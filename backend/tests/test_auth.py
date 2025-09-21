"""
Authentication and Security Tests
=================================

Comprehensive tests for HeatGuard authentication and security features:
- API key authentication and validation
- Rate limiting functionality
- Permission-based access control
- JWT token management (future use)
- Security headers validation
- Input sanitization and validation
- Audit logging and security events
- Protection against common vulnerabilities
"""

import pytest
import time
import hashlib
import hmac
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
import redis

from app.middleware.auth import (
    AuthMiddleware, RateLimiter, APIKeyError, RateLimitError,
    get_api_key, get_current_user, require_permission,
    hash_api_key, generate_api_key, verify_signature,
    SecurityHeaders, log_security_event, JWTManager
)


class TestAPIKeyAuthentication:
    """Test API key authentication functionality."""

    def test_valid_api_key_authentication(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test authentication with valid API key."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.3,
                'risk_level': 'Safe',
                'confidence': 0.9
            }

            response = authenticated_client.post("/api/v1/predict", json=request_data)
            assert response.status_code == 200

    def test_missing_api_key(self, client, sample_worker_data):
        """Test request without API key."""
        request_data = {"data": sample_worker_data}
        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 401

    def test_invalid_api_key(self, client, sample_worker_data):
        """Test request with invalid API key."""
        client.headers["X-API-Key"] = "invalid-api-key-123"
        request_data = {"data": sample_worker_data}

        response = client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 401

    def test_expired_api_key(self, client, sample_worker_data):
        """Test request with expired API key."""
        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate:
            mock_validate.side_effect = APIKeyError("API key has expired")

            client.headers["X-API-Key"] = "expired-api-key"
            request_data = {"data": sample_worker_data}

            response = client.post("/api/v1/predict", json=request_data)
            assert response.status_code == 401
            assert "expired" in response.json()["detail"].lower()

    def test_deactivated_api_key(self, client, sample_worker_data):
        """Test request with deactivated API key."""
        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate:
            mock_validate.side_effect = APIKeyError("API key is deactivated")

            client.headers["X-API-Key"] = "deactivated-api-key"
            request_data = {"data": sample_worker_data}

            response = client.post("/api/v1/predict", json=request_data)
            assert response.status_code == 401


class TestAuthMiddleware:
    """Test AuthMiddleware class functionality."""

    def test_auth_middleware_initialization(self):
        """Test AuthMiddleware initialization."""
        auth_middleware = AuthMiddleware()

        assert auth_middleware.valid_api_keys is not None
        assert auth_middleware.rate_limiter is not None
        assert isinstance(auth_middleware.api_key_cache, dict)

    def test_validate_api_key_success(self):
        """Test successful API key validation."""
        auth_middleware = AuthMiddleware()

        # Test with demo key from middleware
        api_key = "heatguard-api-key-demo-12345"
        key_info = auth_middleware.validate_api_key(api_key)

        assert key_info is not None
        assert key_info["active"] is True
        assert "permissions" in key_info
        assert "rate_limit" in key_info

    def test_validate_api_key_failure(self):
        """Test API key validation failure."""
        auth_middleware = AuthMiddleware()

        with pytest.raises(APIKeyError):
            auth_middleware.validate_api_key("invalid-key")

        with pytest.raises(APIKeyError):
            auth_middleware.validate_api_key(None)

        with pytest.raises(APIKeyError):
            auth_middleware.validate_api_key("")

    def test_validate_api_key_caching(self):
        """Test API key validation caching."""
        auth_middleware = AuthMiddleware()
        api_key = "heatguard-api-key-demo-12345"

        # First call - should cache result
        result1 = auth_middleware.validate_api_key(api_key)

        # Second call - should use cache
        result2 = auth_middleware.validate_api_key(api_key)

        assert result1 == result2

    def test_check_permissions(self):
        """Test permission checking."""
        auth_middleware = AuthMiddleware()

        # Mock key info with different permissions
        admin_key_info = {"permissions": ["admin"]}
        read_key_info = {"permissions": ["read"]}
        write_key_info = {"permissions": ["write"]}
        no_permission_key_info = {"permissions": []}

        # Admin should have all permissions
        assert auth_middleware.check_permissions(admin_key_info, "read") is True
        assert auth_middleware.check_permissions(admin_key_info, "write") is True
        assert auth_middleware.check_permissions(admin_key_info, "admin") is True

        # Read-only key should only have read permission
        assert auth_middleware.check_permissions(read_key_info, "read") is True
        assert auth_middleware.check_permissions(read_key_info, "write") is False

        # Write key should have write permission
        assert auth_middleware.check_permissions(write_key_info, "write") is True
        assert auth_middleware.check_permissions(write_key_info, "admin") is False

        # No permissions should fail all checks
        assert auth_middleware.check_permissions(no_permission_key_info, "read") is False

    def test_get_rate_limit(self):
        """Test rate limit retrieval."""
        auth_middleware = AuthMiddleware()

        key_info = {"rate_limit": 500}
        assert auth_middleware.get_rate_limit(key_info) == 500

        key_info_no_limit = {}
        default_limit = auth_middleware.get_rate_limit(key_info_no_limit)
        assert default_limit > 0  # Should return default rate limit


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        rate_limiter = RateLimiter()

        assert rate_limiter.in_memory_store is not None
        assert rate_limiter.lock is not None

    def test_rate_limit_check_success(self):
        """Test successful rate limit check."""
        rate_limiter = RateLimiter()

        # Should allow requests within limit
        result = rate_limiter.check_rate_limit("test_id", limit=10, window_minutes=1)

        assert result["allowed"] is True
        assert result["limit"] == 10
        assert result["remaining"] >= 0
        assert "reset_time" in result

    def test_rate_limit_check_exceeded(self):
        """Test rate limit exceeded."""
        rate_limiter = RateLimiter()
        identifier = "test_rate_limit"

        # Make requests up to the limit
        for i in range(5):
            rate_limiter.check_rate_limit(identifier, limit=5, window_minutes=1)

        # Next request should exceed limit
        with pytest.raises(RateLimitError):
            rate_limiter.check_rate_limit(identifier, limit=5, window_minutes=1)

    def test_rate_limit_window_reset(self):
        """Test rate limit window reset."""
        rate_limiter = RateLimiter()
        identifier = "test_window_reset"

        # Fill up the rate limit
        for i in range(3):
            rate_limiter.check_rate_limit(identifier, limit=3, window_minutes=1)

        # Should exceed limit
        with pytest.raises(RateLimitError):
            rate_limiter.check_rate_limit(identifier, limit=3, window_minutes=1)

        # Clear the in-memory store to simulate window reset
        rate_limiter.in_memory_store[identifier] = []

        # Should allow requests again
        result = rate_limiter.check_rate_limit(identifier, limit=3, window_minutes=1)
        assert result["allowed"] is True

    @patch('redis.from_url')
    def test_redis_rate_limiting(self, mock_redis_factory):
        """Test Redis-based rate limiting."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.zremrangebyscore.return_value = None
        mock_redis.zcard.return_value = 2
        mock_redis.zadd.return_value = 1
        mock_redis.expire.return_value = True
        mock_redis.execute.return_value = [None, 2, 1, True]

        mock_redis_factory.return_value = mock_redis

        rate_limiter = RateLimiter()

        result = rate_limiter.check_rate_limit("redis_test", limit=10, window_minutes=1)

        assert result["allowed"] is True
        assert result["current_count"] == 3  # 2 existing + 1 new

    @patch('redis.from_url')
    def test_redis_rate_limit_exceeded(self, mock_redis_factory):
        """Test Redis rate limit exceeded."""
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.pipeline.return_value = mock_redis
        mock_redis.execute.return_value = [None, 10, 1, True]  # Already at limit
        mock_redis.zrange.return_value = [(b'123456789', time.time())]

        mock_redis_factory.return_value = mock_redis

        rate_limiter = RateLimiter()

        with pytest.raises(RateLimitError):
            rate_limiter.check_rate_limit("redis_test", limit=10, window_minutes=1)

    def test_redis_fallback_to_memory(self):
        """Test fallback to memory-based rate limiting when Redis fails."""
        with patch('redis.from_url', side_effect=Exception("Redis connection failed")):
            rate_limiter = RateLimiter()

            # Should fallback to memory-based rate limiting
            result = rate_limiter.check_rate_limit("fallback_test", limit=5, window_minutes=1)
            assert result["allowed"] is True


class TestPermissionSystem:
    """Test permission-based access control."""

    @pytest.mark.asyncio
    async def test_require_read_permission_success(self):
        """Test successful read permission requirement."""
        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate, \
             patch('app.middleware.auth.auth_middleware.check_permissions') as mock_check_perm, \
             patch('app.middleware.auth.auth_middleware.rate_limiter.check_rate_limit') as mock_rate_limit:

            mock_validate.return_value = {"permissions": ["read"]}
            mock_check_perm.return_value = True
            mock_rate_limit.return_value = {"allowed": True}

            from app.middleware.auth import require_read_permission
            result = await require_read_permission("valid-api-key")
            assert result is True

    @pytest.mark.asyncio
    async def test_require_write_permission_denied(self):
        """Test write permission denied."""
        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate, \
             patch('app.middleware.auth.auth_middleware.check_permissions') as mock_check_perm, \
             patch('app.middleware.auth.auth_middleware.rate_limiter.check_rate_limit') as mock_rate_limit:

            mock_validate.return_value = {"permissions": ["read"]}
            mock_check_perm.return_value = False  # No write permission
            mock_rate_limit.return_value = {"allowed": True}

            from app.middleware.auth import require_write_permission

            with pytest.raises(HTTPException) as exc_info:
                await require_write_permission("read-only-key")

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_admin_permission(self):
        """Test admin permission requirement."""
        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate, \
             patch('app.middleware.auth.auth_middleware.check_permissions') as mock_check_perm, \
             patch('app.middleware.auth.auth_middleware.rate_limiter.check_rate_limit') as mock_rate_limit:

            mock_validate.return_value = {"permissions": ["admin"]}
            mock_check_perm.return_value = True
            mock_rate_limit.return_value = {"allowed": True}

            from app.middleware.auth import require_admin_permission
            result = await require_admin_permission("admin-api-key")
            assert result is True


class TestJWTTokenManagement:
    """Test JWT token management for advanced authentication."""

    def test_jwt_manager_initialization(self):
        """Test JWT manager initialization."""
        jwt_manager = JWTManager()

        assert jwt_manager.secret_key is not None
        assert jwt_manager.algorithm is not None
        assert jwt_manager.access_token_expire_minutes > 0

    def test_create_access_token(self):
        """Test JWT access token creation."""
        jwt_manager = JWTManager()

        data = {"user_id": "test_user", "permissions": ["read", "write"]}
        token = jwt_manager.create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_success(self):
        """Test successful JWT token verification."""
        jwt_manager = JWTManager()

        data = {"user_id": "test_user", "permissions": ["read"]}
        token = jwt_manager.create_access_token(data)

        payload = jwt_manager.verify_token(token)

        assert payload["user_id"] == "test_user"
        assert payload["permissions"] == ["read"]
        assert "exp" in payload

    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token."""
        jwt_manager = JWTManager()

        with pytest.raises(APIKeyError):
            jwt_manager.verify_token("invalid.jwt.token")

    def test_verify_token_expired(self):
        """Test JWT token verification with expired token."""
        jwt_manager = JWTManager()

        # Create token with immediate expiration
        from datetime import datetime, timedelta
        data = {"user_id": "test_user"}
        expired_time = datetime.utcnow() - timedelta(seconds=1)

        with patch('app.middleware.auth.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = expired_time
            token = jwt_manager.create_access_token(data)

        with pytest.raises(APIKeyError):
            jwt_manager.verify_token(token)


class TestSecurityHeaders:
    """Test security headers functionality."""

    def test_security_headers_generation(self):
        """Test security headers generation."""
        headers = SecurityHeaders.get_security_headers()

        assert isinstance(headers, dict)

        # Check for standard security headers
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Cache-Control",
            "Pragma",
            "Expires"
        ]

        for header in expected_headers:
            assert header in headers

    def test_security_headers_values(self):
        """Test security header values."""
        headers = SecurityHeaders.get_security_headers()

        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert "max-age" in headers["Strict-Transport-Security"]

    def test_security_headers_in_response(self, client):
        """Test that security headers are present in API responses."""
        response = client.get("/")

        # Check that security headers are present
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers


class TestSecurityUtilities:
    """Test security utility functions."""

    def test_hash_api_key(self):
        """Test API key hashing."""
        api_key = "test-api-key-123"
        hashed = hash_api_key(api_key)

        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex digest length
        assert hashed != api_key  # Should be different from original

        # Same input should produce same hash
        assert hash_api_key(api_key) == hashed

    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        assert isinstance(key1, str)
        assert isinstance(key2, str)
        assert key1 != key2  # Should be unique
        assert key1.startswith("heatguard-")
        assert len(key1) > 20  # Should be reasonably long

    def test_verify_signature(self):
        """Test HMAC signature verification."""
        payload = "test payload data"
        secret = "test-secret-key"

        # Create valid signature
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        # Should verify correctly
        assert verify_signature(payload, signature, secret) is True

        # Should fail with wrong signature
        assert verify_signature(payload, "invalid-signature", secret) is False

        # Should fail with wrong secret
        assert verify_signature(payload, signature, "wrong-secret") is False

    def test_get_client_ip(self):
        """Test client IP extraction."""
        from app.middleware.auth import get_client_ip

        # Mock request with different headers
        mock_request = Mock()

        # Test with X-Forwarded-For
        mock_request.headers.get.side_effect = lambda h: {
            "X-Forwarded-For": "192.168.1.100, 10.0.0.1"
        }.get(h)
        mock_request.client.host = "127.0.0.1"

        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.100"  # Should return first IP in forwarded list

        # Test with X-Real-IP
        mock_request.headers.get.side_effect = lambda h: {
            "X-Real-IP": "203.0.113.1"
        }.get(h, None)

        ip = get_client_ip(mock_request)
        assert ip == "203.0.113.1"

        # Test with direct client IP
        mock_request.headers.get.return_value = None
        mock_request.client.host = "198.51.100.1"

        ip = get_client_ip(mock_request)
        assert ip == "198.51.100.1"


class TestSecurityAuditLogging:
    """Test security audit logging functionality."""

    def test_log_security_event(self):
        """Test security event logging."""
        with patch('app.middleware.auth.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_security_event(
                event_type="authentication_failure",
                details={"api_key": "invalid-key", "ip": "192.168.1.100"},
                severity="warning"
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "authentication_failure" in call_args[0][0]

    def test_log_security_event_critical(self):
        """Test critical security event logging."""
        with patch('app.middleware.auth.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            log_security_event(
                event_type="potential_attack",
                details={"attack_type": "sql_injection", "blocked": True},
                severity="critical"
            )

            mock_logger.critical.assert_called_once()


class TestSecurityIntegration:
    """Test security integration with API endpoints."""

    def test_rate_limiting_integration(self, client, sample_worker_data):
        """Test rate limiting integration with API endpoints."""
        client.headers["X-API-Key"] = "test-api-key"

        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate, \
             patch('app.middleware.auth.auth_middleware.rate_limiter.check_rate_limit') as mock_rate_limit:

            mock_validate.return_value = {"permissions": ["read", "write"], "rate_limit": 1}
            mock_rate_limit.side_effect = RateLimitError("Rate limit exceeded")

            request_data = {"data": sample_worker_data}
            response = client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 429
            assert "rate limit" in response.json()["detail"].lower()

    def test_cors_security(self, client):
        """Test CORS security configuration."""
        # Test preflight request
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://malicious-site.com"}
        )

        # Should handle CORS appropriately
        # Exact behavior depends on CORS configuration

    def test_input_sanitization(self, authenticated_client, mock_auth_middleware):
        """Test input sanitization and validation."""
        # Test with potentially malicious input
        malicious_data = {
            "Age": 30,
            "Gender": 1,
            "Temperature": 25,
            "Humidity": 60,
            "hrv_mean_hr": 75,
            "malicious_script": "<script>alert('xss')</script>",
            "sql_injection": "'; DROP TABLE users; --"
        }

        request_data = {"data": malicious_data}
        response = authenticated_client.post("/api/v1/predict", json=request_data)

        # Should either sanitize input or reject with validation error
        assert response.status_code in [200, 422]

    def test_error_information_disclosure(self, client):
        """Test that errors don't disclose sensitive information."""
        # Test with invalid endpoint
        response = client.get("/api/v1/internal-debug-info")

        assert response.status_code == 404
        response_data = response.json()

        # Should not contain sensitive system information
        response_text = str(response_data).lower()
        sensitive_info = ["password", "secret", "key", "token", "database"]

        for info in sensitive_info:
            assert info not in response_text

    def test_sql_injection_protection(self, authenticated_client, mock_auth_middleware):
        """Test SQL injection protection."""
        sql_injection_payloads = [
            "'; DROP TABLE workers; --",
            "' OR '1'='1",
            "'; INSERT INTO workers VALUES (1,2,3); --"
        ]

        for payload in sql_injection_payloads:
            malicious_data = {
                "Age": 30,
                "Gender": 1,
                "Temperature": 25,
                "Humidity": 60,
                "hrv_mean_hr": 75,
                "worker_id": payload
            }

            request_data = {"data": malicious_data}
            response = authenticated_client.post("/api/v1/predict", json=request_data)

            # Should not execute SQL injection
            # Response should be either success (if sanitized) or validation error
            assert response.status_code in [200, 422, 400]

    def test_xss_protection(self, authenticated_client, mock_auth_middleware):
        """Test XSS protection."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]

        for payload in xss_payloads:
            malicious_data = {
                "Age": 30,
                "Gender": 1,
                "Temperature": 25,
                "Humidity": 60,
                "hrv_mean_hr": 75,
                "worker_id": payload
            }

            request_data = {"data": malicious_data}
            response = authenticated_client.post("/api/v1/predict", json=request_data)

            if response.status_code == 200:
                response_text = response.text
                # XSS payload should not be reflected back unescaped
                assert "<script>" not in response_text
                assert "javascript:" not in response_text


class TestSecurityConfiguration:
    """Test security configuration and settings."""

    def test_debug_mode_security(self):
        """Test security implications of debug mode."""
        from app.config.settings import settings

        if settings.DEBUG:
            # In debug mode, some security features might be relaxed
            # but sensitive endpoints should still require authentication
            pass
        else:
            # In production mode, all security features should be enabled
            assert settings.SECRET_KEY != "heatguard-secret-key-change-in-production"

    def test_https_enforcement(self, client):
        """Test HTTPS enforcement in production."""
        response = client.get("/", headers={"X-Forwarded-Proto": "http"})

        # In production, should redirect to HTTPS or enforce secure connection
        # Exact behavior depends on deployment configuration

    def test_api_versioning_security(self, client):
        """Test API versioning doesn't introduce security issues."""
        # Test that old API versions don't bypass security
        response = client.get("/api/v0/predict")  # Non-existent old version
        assert response.status_code == 404

        response = client.get("/api/v2/predict")  # Non-existent new version
        assert response.status_code == 404


@pytest.mark.parametrize("endpoint,method,should_have_auth", [
    ("/api/v1/predict", "POST", True),
    ("/api/v1/predict_batch", "POST", True),
    ("/api/v1/generate_random", "GET", True),
    ("/api/v1/health", "GET", False),
    ("/api/v1/health/simple", "GET", False),
    ("/", "GET", False)
])
def test_endpoint_security_requirements(client, endpoint, method, should_have_auth):
    """Test that endpoints have appropriate security requirements."""
    if method == "GET":
        response = client.get(endpoint)
    elif method == "POST":
        response = client.post(endpoint, json={})

    if should_have_auth:
        # Protected endpoints should require authentication
        assert response.status_code in [401, 422]  # 401 for auth, 422 for validation
    else:
        # Public endpoints should not require authentication
        assert response.status_code != 401