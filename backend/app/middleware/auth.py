"""
Authentication and Security Middleware
======================================

Handles API key authentication, rate limiting, and security for the HeatGuard system.
"""

import time
import hashlib
import hmac
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
import redis
from collections import defaultdict
import threading

from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class APIKeyError(Exception):
    """Custom exception for API key authentication errors."""
    pass


class RateLimitError(Exception):
    """Custom exception for rate limiting errors."""
    pass


# API Key security scheme
APIKeyHeader = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

# Bearer token security scheme
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Authentication and authorization middleware."""

    def __init__(self):
        self.valid_api_keys = self._load_api_keys()
        self.rate_limiter = RateLimiter()
        self.api_key_cache = {}
        self.cache_ttl = 300  # 5 minutes

    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        Load valid API keys and their metadata.
        In production, this would load from a secure database.
        """
        # For demonstration - in production, load from secure storage
        api_keys = {
            "heatguard-api-key-demo-12345": {
                "name": "Demo API Key",
                "permissions": ["read", "write", "admin"],
                "rate_limit": 1000,  # requests per minute
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": None,  # Never expires
                "active": True
            },
            "heatguard-readonly-key-67890": {
                "name": "Read-Only API Key",
                "permissions": ["read"],
                "rate_limit": 500,
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": None,
                "active": True
            }
        }

        logger.info(f"Loaded {len(api_keys)} API keys")
        return api_keys

    def validate_api_key(self, api_key: Optional[str]) -> Dict[str, Any]:
        """
        Validate API key and return key metadata.

        Args:
            api_key: API key to validate

        Returns:
            API key metadata

        Raises:
            APIKeyError: If API key is invalid
        """
        if not api_key:
            raise APIKeyError("API key is required")

        # Check cache first
        cache_key = hashlib.sha256(api_key.encode()).hexdigest()
        if cache_key in self.api_key_cache:
            cached_result, cached_time = self.api_key_cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                if cached_result is None:
                    raise APIKeyError("Invalid API key")
                return cached_result

        # Validate API key
        key_info = self.valid_api_keys.get(api_key)

        if not key_info:
            # Cache negative result
            self.api_key_cache[cache_key] = (None, time.time())
            raise APIKeyError("Invalid API key")

        if not key_info.get("active", False):
            raise APIKeyError("API key is deactivated")

        # Check expiration
        expires_at = key_info.get("expires_at")
        if expires_at:
            expire_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now().replace(tzinfo=expire_time.tzinfo) > expire_time:
                raise APIKeyError("API key has expired")

        # Cache positive result
        self.api_key_cache[cache_key] = (key_info, time.time())

        logger.debug(f"API key validated: {key_info.get('name', 'Unknown')}")
        return key_info

    def check_permissions(self, key_info: Dict[str, Any], required_permission: str) -> bool:
        """
        Check if API key has required permission.

        Args:
            key_info: API key metadata
            required_permission: Required permission level

        Returns:
            True if permission is granted
        """
        permissions = key_info.get("permissions", [])
        return required_permission in permissions or "admin" in permissions

    def get_rate_limit(self, key_info: Dict[str, Any]) -> int:
        """Get rate limit for API key."""
        return key_info.get("rate_limit", settings.RATE_LIMIT_PER_MINUTE)


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self):
        self.redis_client = self._get_redis_client()
        self.in_memory_store = defaultdict(list)
        self.lock = threading.Lock()

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client if available."""
        try:
            if settings.REDIS_URL:
                client = redis.from_url(settings.REDIS_URL)
                client.ping()  # Test connection
                return client
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
        return None

    def check_rate_limit(self, identifier: str, limit: int, window_minutes: int = 1) -> Dict[str, Any]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (API key hash, IP, etc.)
            limit: Maximum requests allowed
            window_minutes: Time window in minutes

        Returns:
            Dictionary with rate limit status

        Raises:
            RateLimitError: If rate limit is exceeded
        """
        now = time.time()
        window_start = now - (window_minutes * 60)

        if self.redis_client:
            return self._check_rate_limit_redis(identifier, limit, window_start, now)
        else:
            return self._check_rate_limit_memory(identifier, limit, window_start, now)

    def _check_rate_limit_redis(self, identifier: str, limit: int, window_start: float, now: float) -> Dict[str, Any]:
        """Redis-based rate limiting."""
        try:
            pipe = self.redis_client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(f"rate_limit:{identifier}", 0, window_start)

            # Count current requests
            pipe.zcard(f"rate_limit:{identifier}")

            # Add current request
            pipe.zadd(f"rate_limit:{identifier}", {str(now): now})

            # Set expiration
            pipe.expire(f"rate_limit:{identifier}", 3600)  # 1 hour

            results = pipe.execute()
            current_count = results[1]

            if current_count >= limit:
                # Get time until reset
                oldest_request = self.redis_client.zrange(f"rate_limit:{identifier}", 0, 0, withscores=True)
                if oldest_request:
                    reset_time = int(oldest_request[0][1] + 60)  # 1 minute window
                else:
                    reset_time = int(now + 60)

                raise RateLimitError(
                    f"Rate limit exceeded. Limit: {limit} requests per minute. "
                    f"Current: {current_count}. Reset at: {reset_time}"
                )

            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset_time": int(now + 60),
                "current_count": current_count + 1
            }

        except redis.RedisError as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to memory-based rate limiting
            return self._check_rate_limit_memory(identifier, limit, window_start, now)

    def _check_rate_limit_memory(self, identifier: str, limit: int, window_start: float, now: float) -> Dict[str, Any]:
        """In-memory rate limiting."""
        with self.lock:
            # Clean old entries
            self.in_memory_store[identifier] = [
                timestamp for timestamp in self.in_memory_store[identifier]
                if timestamp > window_start
            ]

            current_count = len(self.in_memory_store[identifier])

            if current_count >= limit:
                oldest_timestamp = min(self.in_memory_store[identifier]) if self.in_memory_store[identifier] else now
                reset_time = int(oldest_timestamp + 60)

                raise RateLimitError(
                    f"Rate limit exceeded. Limit: {limit} requests per minute. "
                    f"Current: {current_count}. Reset at: {reset_time}"
                )

            # Add current request
            self.in_memory_store[identifier].append(now)

            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset_time": int(now + 60),
                "current_count": current_count + 1
            }


# Global instances
auth_middleware = AuthMiddleware()


# Dependency functions
async def get_api_key(api_key: Optional[str] = Depends(APIKeyHeader)) -> str:
    """
    Extract and validate API key from request headers.

    Args:
        api_key: API key from header

    Returns:
        Valid API key

    Raises:
        HTTPException: If API key is invalid
    """
    try:
        key_info = auth_middleware.validate_api_key(api_key)

        # Check rate limit
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        rate_limit = auth_middleware.get_rate_limit(key_info)

        try:
            rate_limit_status = auth_middleware.rate_limiter.check_rate_limit(
                identifier=key_hash,
                limit=rate_limit
            )
            logger.debug(f"Rate limit check passed", **rate_limit_status)

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded for API key", api_key_name=key_info.get('name'))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
                headers={
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + 60))
                }
            )

        return api_key

    except APIKeyError as e:
        logger.warning(f"API key validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "ApiKey"}
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user(api_key: str = Depends(get_api_key)) -> Dict[str, Any]:
    """
    Get current user information from validated API key.

    Args:
        api_key: Validated API key

    Returns:
        User information dictionary
    """
    try:
        key_info = auth_middleware.validate_api_key(api_key)
        return {
            "api_key_name": key_info.get("name", "Unknown"),
            "permissions": key_info.get("permissions", []),
            "rate_limit": key_info.get("rate_limit", settings.RATE_LIMIT_PER_MINUTE),
            "authenticated": True
        }
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to get user information"
        )


async def require_permission(permission: str):
    """
    Dependency factory for requiring specific permissions.

    Args:
        permission: Required permission level

    Returns:
        Dependency function
    """
    async def permission_checker(api_key: str = Depends(get_api_key)) -> bool:
        try:
            key_info = auth_middleware.validate_api_key(api_key)

            if not auth_middleware.check_permissions(key_info, permission):
                logger.warning(
                    f"Permission denied: {permission}",
                    api_key_name=key_info.get('name'),
                    permissions=key_info.get('permissions')
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )

            return True

        except APIKeyError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    return permission_checker


# Convenience dependencies for different permission levels
async def require_read_permission(api_key: str = Depends(get_api_key)) -> bool:
    """Require read permission."""
    return await require_permission("read")(api_key)


async def require_write_permission(api_key: str = Depends(get_api_key)) -> bool:
    """Require write permission."""
    return await require_permission("write")(api_key)


async def require_admin_permission(api_key: str = Depends(get_api_key)) -> bool:
    """Require admin permission."""
    return await require_permission("admin")(api_key)


# JWT token support (for future use)
class JWTManager:
    """JWT token management for advanced authentication."""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            raise APIKeyError("Invalid token")


# Global JWT manager
jwt_manager = JWTManager()


# Security utility functions
def hash_api_key(api_key: str) -> str:
    """Create a secure hash of an API key."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new API key."""
    import secrets
    return f"heatguard-{secrets.token_urlsafe(32)}"


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify HMAC signature for webhook security."""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


# Security headers middleware
class SecurityHeaders:
    """Security headers for API responses."""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }


def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


# Audit logging
def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "info") -> None:
    """Log security-related events."""
    security_logger = get_logger("security")

    log_entry = {
        "event_type": event_type,
        "severity": severity,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }

    if severity == "critical":
        security_logger.critical(f"Security event: {event_type}", **log_entry)
    elif severity == "error":
        security_logger.error(f"Security event: {event_type}", **log_entry)
    elif severity == "warning":
        security_logger.warning(f"Security event: {event_type}", **log_entry)
    else:
        security_logger.info(f"Security event: {event_type}", **log_entry)