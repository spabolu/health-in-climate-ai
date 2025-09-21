"""
API Endpoint Tests
==================

Comprehensive tests for all HeatGuard API endpoints covering:
- Single worker prediction (POST /api/v1/predict)
- Batch worker prediction (POST /api/v1/predict_batch)
- Async batch processing (POST /api/v1/predict_batch_async)
- Health check endpoints (GET /api/v1/health, /health/simple, etc.)
- Data generation endpoints (GET /api/v1/generate_random, etc.)
- System information endpoints

Tests include success cases, error cases, validation, and edge cases.
"""

import pytest
import json
import time
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from fastapi import status


class TestPredictionEndpoints:
    """Test prediction API endpoints."""

    def test_single_prediction_success(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test successful single worker prediction."""
        request_data = {
            "data": sample_worker_data,
            "options": {
                "use_conservative": True,
                "log_compliance": True
            }
        }

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'request_id': 'test_123',
                'worker_id': 'test_worker_001',
                'timestamp': '2024-01-01T12:00:00',
                'heat_exposure_risk_score': 0.35,
                'risk_level': 'Caution',
                'confidence': 0.87,
                'temperature_celsius': 25.5,
                'temperature_fahrenheit': 77.9,
                'humidity_percent': 65.0,
                'heat_index': 79.2,
                'osha_recommendations': ['Increase hydration'],
                'requires_immediate_attention': False,
                'processing_time_ms': 145.6
            }

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert 'heat_exposure_risk_score' in data
            assert 'risk_level' in data
            assert 'confidence' in data
            assert 'osha_recommendations' in data

            # Validate score range
            assert 0 <= data['heat_exposure_risk_score'] <= 1
            assert data['risk_level'] in ['Safe', 'Caution', 'Warning', 'Danger']
            assert 0 <= data['confidence'] <= 1

            # Verify service was called
            mock_predict.assert_called_once()

    def test_single_prediction_missing_auth(self, client, sample_worker_data):
        """Test single prediction without authentication."""
        request_data = {"data": sample_worker_data}

        response = client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 401

    def test_single_prediction_invalid_data(self, authenticated_client, mock_auth_middleware, invalid_worker_data):
        """Test single prediction with invalid data."""
        request_data = {"data": invalid_worker_data}

        response = authenticated_client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 422  # Validation error

    def test_single_prediction_missing_required_fields(self, authenticated_client, mock_auth_middleware):
        """Test single prediction with missing required fields."""
        incomplete_data = {
            "Age": 30,
            "Gender": 1
            # Missing Temperature, Humidity, hrv_mean_hr
        }
        request_data = {"data": incomplete_data}

        response = authenticated_client.post("/api/v1/predict", json=request_data)

        assert response.status_code == 422

    def test_batch_prediction_success(self, authenticated_client, mock_auth_middleware, batch_worker_data):
        """Test successful batch worker prediction."""
        request_data = {
            "data": batch_worker_data,
            "options": {
                "use_conservative": True,
                "log_compliance": True
            },
            "parallel_processing": True
        }

        with patch('app.api.prediction.prediction_service.predict_multiple_workers') as mock_predict:
            mock_predict.return_value = {
                'request_id': 'batch_123',
                'batch_size': len(batch_worker_data),
                'successful_predictions': len(batch_worker_data),
                'failed_predictions': 0,
                'processing_time_ms': 234.5,
                'batch_statistics': {
                    'avg_risk_score': 0.45,
                    'high_risk_count': 2,
                    'risk_distribution': {'Safe': 5, 'Caution': 3, 'Warning': 2}
                },
                'predictions': [
                    {
                        'worker_id': f'worker_{i}',
                        'heat_exposure_risk_score': 0.3 + i * 0.1,
                        'risk_level': 'Caution',
                        'confidence': 0.85
                    } for i in range(len(batch_worker_data))
                ]
            }

            response = authenticated_client.post("/api/v1/predict_batch", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Validate batch response structure
            assert 'batch_size' in data
            assert 'successful_predictions' in data
            assert 'predictions' in data
            assert 'batch_statistics' in data

            assert data['batch_size'] == len(batch_worker_data)
            assert len(data['predictions']) == len(batch_worker_data)

            mock_predict.assert_called_once()

    def test_batch_prediction_size_limit(self, authenticated_client, mock_auth_middleware):
        """Test batch prediction with size exceeding limit."""
        # Create oversized batch (1001 workers)
        large_batch = [{"Age": 30, "Gender": 1, "Temperature": 25, "Humidity": 60, "hrv_mean_hr": 75}] * 1001
        request_data = {"data": large_batch}

        response = authenticated_client.post("/api/v1/predict_batch", json=request_data)

        assert response.status_code == 422  # Should reject oversized batch

    def test_async_batch_prediction_submission(self, authenticated_client, mock_auth_middleware, performance_test_data):
        """Test asynchronous batch job submission."""
        request_data = {
            "data": performance_test_data[:100],  # Use subset for testing
            "options": {
                "use_conservative": True,
                "log_compliance": True
            },
            "chunk_size": 50,
            "priority": "normal"
        }

        with patch('app.api.prediction.batch_service.submit_batch_job') as mock_submit:
            mock_submit.return_value = "job_async_123"

            response = authenticated_client.post("/api/v1/predict_batch_async", json=request_data)

            assert response.status_code == 202  # Accepted
            data = response.json()

            assert 'job_id' in data
            assert 'status' in data
            assert data['status'] == 'submitted'
            assert data['batch_size'] == 100

            mock_submit.assert_called_once()

    def test_batch_status_check(self, authenticated_client, mock_auth_middleware):
        """Test batch job status endpoint."""
        job_id = "test_job_123"

        with patch('app.api.prediction.batch_service.get_job_status') as mock_status:
            mock_status.return_value = {
                'job_id': job_id,
                'status': 'running',
                'progress': 45,
                'estimated_completion': '2024-01-01T13:00:00'
            }

            response = authenticated_client.get(f"/api/v1/batch_status/{job_id}")

            assert response.status_code == 200
            data = response.json()

            assert data['job_id'] == job_id
            assert data['status'] == 'running'

    def test_batch_status_not_found(self, authenticated_client, mock_auth_middleware):
        """Test batch job status for non-existent job."""
        with patch('app.api.prediction.batch_service.get_job_status') as mock_status:
            mock_status.return_value = None

            response = authenticated_client.get("/api/v1/batch_status/nonexistent_job")

            assert response.status_code == 404

    def test_batch_results_retrieval(self, authenticated_client, mock_auth_middleware):
        """Test batch job results endpoint."""
        job_id = "completed_job_123"

        with patch('app.api.prediction.batch_service.get_job_results') as mock_results:
            mock_results.return_value = {
                'job_id': job_id,
                'status': 'completed',
                'results': [{'worker_id': 'w1', 'risk_score': 0.3}],
                'summary': {'total_predictions': 100}
            }

            response = authenticated_client.get(f"/api/v1/batch_results/{job_id}")

            assert response.status_code == 200
            data = response.json()

            assert data['job_id'] == job_id
            assert 'results' in data

    def test_batch_job_cancellation(self, authenticated_client, mock_auth_middleware):
        """Test batch job cancellation."""
        job_id = "running_job_123"

        with patch('app.api.prediction.batch_service.cancel_job') as mock_cancel:
            mock_cancel.return_value = True

            response = authenticated_client.delete(f"/api/v1/batch_job/{job_id}")

            assert response.status_code == 200
            data = response.json()

            assert data['status'] == 'cancelled'

    def test_batch_jobs_listing(self, authenticated_client, mock_auth_middleware):
        """Test batch jobs listing endpoint."""
        with patch('app.api.prediction.batch_service.list_jobs') as mock_list:
            mock_list.return_value = [
                {'job_id': 'job1', 'status': 'running'},
                {'job_id': 'job2', 'status': 'completed'}
            ]

            response = authenticated_client.get("/api/v1/batch_jobs")

            assert response.status_code == 200
            data = response.json()

            assert 'jobs' in data
            assert len(data['jobs']) == 2


class TestHealthEndpoints:
    """Test health check and monitoring endpoints."""

    def test_comprehensive_health_check(self, client):
        """Test comprehensive health check endpoint."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=True), \
             patch('app.api.health.prediction_service.get_service_health', return_value={'status': 'healthy'}), \
             patch('app.api.health.batch_service.get_service_statistics', return_value={'active_jobs': 0}), \
             patch('app.api.health.compliance_service.get_compliance_status', return_value={'compliance_logging_enabled': True}):

            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()

            # Validate health response structure
            assert 'overall_status' in data
            assert 'system_info' in data
            assert 'model_status' in data
            assert 'services' in data
            assert 'configuration' in data

            # Check overall status
            assert data['overall_status']['status'] in ['healthy', 'degraded', 'unhealthy']
            assert 'uptime_seconds' in data['overall_status']

    def test_simple_health_check(self, client):
        """Test simple health check endpoint."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=True):

            response = client.get("/api/v1/health/simple")

            assert response.status_code == 200
            data = response.json()

            assert data['status'] == 'healthy'
            assert 'timestamp' in data

    def test_simple_health_check_degraded(self, client):
        """Test simple health check when model is not loaded."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=False):

            response = client.get("/api/v1/health/simple")

            assert response.status_code == 503
            data = response.json()

            assert data['status'] == 'degraded'

    def test_model_health_check(self, client):
        """Test model-specific health check."""
        with patch('app.api.health.model_loader.health_check', return_value={'status': 'healthy'}), \
             patch('app.api.health.model_loader.is_model_loaded', return_value=True), \
             patch('app.api.health.model_loader.get_model') as mock_get_model:

            mock_model = Mock()
            mock_model.get_model_info.return_value = {
                'model_type': 'XGBoost',
                'feature_count': 50
            }
            mock_get_model.return_value = mock_model

            response = client.get("/api/v1/health/model")

            assert response.status_code == 200
            data = response.json()

            assert 'model_loader_status' in data
            assert 'model_info' in data

    def test_services_health_check(self, client):
        """Test services health check."""
        with patch('app.api.health.prediction_service.get_service_health', return_value={'status': 'healthy'}), \
             patch('app.api.health.batch_service.get_service_statistics', return_value={'active_jobs': 1}), \
             patch('app.api.health.compliance_service.get_compliance_status', return_value={'compliance_logging_enabled': True}):

            response = client.get("/api/v1/health/services")

            assert response.status_code == 200
            data = response.json()

            assert 'services' in data
            assert len(data['services']) >= 3  # At least 3 services

    def test_system_health_check(self, client):
        """Test system resource health check."""
        response = client.get("/api/v1/health/system")

        assert response.status_code == 200
        data = response.json()

        assert 'system_info' in data
        assert 'system_status' in data

    def test_readiness_check(self, client):
        """Test Kubernetes readiness probe."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=True):

            response = client.get("/api/v1/readiness")

            assert response.status_code == 200
            data = response.json()

            assert data['ready'] is True

    def test_readiness_check_not_ready(self, client):
        """Test readiness check when not ready."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=False):

            response = client.get("/api/v1/readiness")

            assert response.status_code == 503
            data = response.json()

            assert data['ready'] is False

    def test_liveness_check(self, client):
        """Test Kubernetes liveness probe."""
        response = client.get("/api/v1/liveness")

        assert response.status_code == 200
        data = response.json()

        assert data['alive'] is True
        assert 'uptime_seconds' in data


class TestDataGenerationEndpoints:
    """Test data generation API endpoints."""

    def test_generate_random_data(self, authenticated_client, mock_auth_middleware):
        """Test random data generation endpoint."""
        with patch('app.api.data_generation.data_generator.generate_batch_samples') as mock_generate:
            mock_generate.return_value = [
                {
                    'Age': 30, 'Gender': 1, 'Temperature': 25,
                    'Humidity': 60, 'hrv_mean_hr': 75,
                    'worker_id': 'generated_001'
                }
            ]

            response = authenticated_client.get("/api/v1/generate_random?count=1")

            assert response.status_code == 200
            data = response.json()

            assert 'data' in data
            assert data['count'] == 1
            assert data['generation_type'] == 'random'

    def test_generate_random_data_with_distribution(self, authenticated_client, mock_auth_middleware):
        """Test random data generation with risk distribution."""
        risk_dist = json.dumps({"safe": 0.5, "caution": 0.3, "warning": 0.2})

        with patch('app.api.data_generation.data_generator.generate_batch_samples') as mock_generate:
            mock_generate.return_value = []

            response = authenticated_client.get(
                f"/api/v1/generate_random?count=10&risk_distribution={risk_dist}"
            )

            assert response.status_code == 200

    def test_generate_random_data_invalid_distribution(self, authenticated_client, mock_auth_middleware):
        """Test random data generation with invalid risk distribution."""
        invalid_dist = json.dumps({"safe": 0.6, "caution": 0.6})  # Sum > 1.0

        response = authenticated_client.get(
            f"/api/v1/generate_random?count=10&risk_distribution={invalid_dist}"
        )

        assert response.status_code == 422

    def test_generate_ramp_up_scenario(self, authenticated_client, mock_auth_middleware):
        """Test escalating risk scenario generation."""
        with patch('app.api.data_generation.data_generator.generate_ramp_up_scenario') as mock_generate:
            mock_generate.return_value = [
                {'Temperature': 25 + i, 'hrv_mean_hr': 70 + i*5}
                for i in range(12)
            ]

            response = authenticated_client.get(
                "/api/v1/generate_ramp_up?duration_minutes=60&interval_minutes=5"
            )

            assert response.status_code == 200
            data = response.json()

            assert data['generation_type'] == 'ramp_up'
            assert data['count'] == 12

    def test_generate_ramp_down_scenario(self, authenticated_client, mock_auth_middleware):
        """Test de-escalating risk scenario generation."""
        with patch('app.api.data_generation.data_generator.generate_ramp_down_scenario') as mock_generate:
            mock_generate.return_value = [
                {'Temperature': 40 - i, 'hrv_mean_hr': 110 - i*5}
                for i in range(12)
            ]

            response = authenticated_client.get(
                "/api/v1/generate_ramp_down?duration_minutes=60&interval_minutes=5"
            )

            assert response.status_code == 200
            data = response.json()

            assert data['generation_type'] == 'ramp_down'
            assert data['count'] == 12

    def test_generate_batch_configured(self, authenticated_client, mock_auth_middleware, batch_worker_data):
        """Test configured batch data generation."""
        request_data = {
            "count": 50,
            "risk_distribution": {
                "safe": 0.4,
                "caution": 0.3,
                "warning": 0.2,
                "danger": 0.1
            },
            "seed": 12345
        }

        with patch('app.api.data_generation.data_generator.generate_batch_samples') as mock_generate:
            mock_generate.return_value = batch_worker_data

            response = authenticated_client.post("/api/v1/generate_batch", json=request_data)

            assert response.status_code == 200
            data = response.json()

            assert data['generation_type'] == 'batch_configured'

    def test_get_generator_info(self, authenticated_client, mock_auth_middleware):
        """Test data generator information endpoint."""
        with patch('app.api.data_generation.data_generator.get_generator_info') as mock_info:
            mock_info.return_value = {
                'generator_version': '1.0.0',
                'total_features': 50,
                'supported_scenarios': ['random', 'ramp_up', 'ramp_down']
            }

            response = authenticated_client.get("/api/v1/generator_info")

            assert response.status_code == 200
            data = response.json()

            assert 'generator_version' in data
            assert 'total_features' in data

    def test_get_feature_template(self, authenticated_client, mock_auth_middleware):
        """Test feature template endpoint."""
        with patch('app.api.data_generation.data_generator.generate_random_sample') as mock_sample:
            mock_sample.return_value = {
                'Age': 30, 'Gender': 1, 'Temperature': 25,
                'Humidity': 60, 'hrv_mean_hr': 75
            }

            response = authenticated_client.get("/api/v1/feature_template")

            assert response.status_code == 200
            data = response.json()

            assert 'feature_template' in data
            assert 'required_features' in data
            assert 'total_features' in data


class TestSystemEndpoints:
    """Test system information and utility endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert 'service' in data
        assert 'version' in data
        assert 'api_endpoints' in data
        assert data['service'] == 'HeatGuard Predictive Safety System'

    def test_system_info_endpoint(self, client):
        """Test system information endpoint."""
        with patch('app.main.model_loader.is_model_loaded', return_value=True), \
             patch('app.main.model_loader.get_model') as mock_get_model:

            mock_model = Mock()
            mock_model.get_model_info.return_value = {
                'model_type': 'XGBoost',
                'feature_count': 50
            }
            mock_get_model.return_value = mock_model

            response = client.get("/api/v1/info")

            assert response.status_code == 200
            data = response.json()

            assert 'system' in data
            assert 'model' in data
            assert 'configuration' in data

    def test_version_endpoint(self, client):
        """Test version information endpoint."""
        response = client.get("/api/v1/version")

        assert response.status_code == 200
        data = response.json()

        assert 'version' in data
        assert 'api_version' in data


class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_validation_errors(self, authenticated_client, mock_auth_middleware):
        """Test various validation errors."""
        # Test with completely empty request
        response = authenticated_client.post("/api/v1/predict", json={})
        assert response.status_code == 422

        # Test with malformed JSON structure
        response = authenticated_client.post("/api/v1/predict", json={"invalid": "structure"})
        assert response.status_code == 422

    def test_server_errors(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test server error handling."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker', side_effect=Exception("Test error")):
            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 500
            data = response.json()
            assert 'error' in data

    def test_not_found_errors(self, authenticated_client, mock_auth_middleware):
        """Test 404 error handling."""
        response = authenticated_client.get("/api/v1/nonexistent_endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, authenticated_client, mock_auth_middleware):
        """Test 405 method not allowed."""
        response = authenticated_client.put("/api/v1/predict")
        assert response.status_code == 405


@pytest.mark.parametrize("endpoint,method,requires_auth", [
    ("/api/v1/predict", "POST", True),
    ("/api/v1/predict_batch", "POST", True),
    ("/api/v1/predict_batch_async", "POST", True),
    ("/api/v1/generate_random", "GET", True),
    ("/api/v1/generate_ramp_up", "GET", True),
    ("/api/v1/generate_ramp_down", "GET", True),
    ("/api/v1/health", "GET", False),
    ("/api/v1/health/simple", "GET", False),
    ("/", "GET", False),
])
def test_endpoint_authentication_requirements(client, authenticated_client, endpoint, method, requires_auth):
    """Test that endpoints properly enforce authentication requirements."""
    test_client = client if not requires_auth else authenticated_client

    # Prepare minimal valid request data for POST endpoints
    request_data = {}
    if method == "POST":
        if "predict" in endpoint and "batch" not in endpoint:
            request_data = {
                "data": {
                    "Age": 30, "Gender": 1, "Temperature": 25,
                    "Humidity": 60, "hrv_mean_hr": 75
                }
            }
        elif "batch" in endpoint:
            request_data = {
                "data": [{
                    "Age": 30, "Gender": 1, "Temperature": 25,
                    "Humidity": 60, "hrv_mean_hr": 75
                }]
            }

    # Mock dependencies to avoid actual processing
    with patch('app.api.prediction.prediction_service'), \
         patch('app.api.data_generation.data_generator'), \
         patch('app.middleware.auth.auth_middleware'):

        if method == "GET":
            response = test_client.get(endpoint)
        elif method == "POST":
            response = test_client.post(endpoint, json=request_data)

        if requires_auth and test_client == client:
            assert response.status_code == 401  # Unauthorized without auth
        else:
            assert response.status_code != 401  # Should not be unauthorized


class TestResponseHeaders:
    """Test security headers and response metadata."""

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/")

        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-Process-Time" in response.headers
        assert "X-API-Version" in response.headers

    def test_cors_headers(self, client):
        """Test CORS headers for preflight requests."""
        headers = {"Origin": "http://localhost:3000"}
        response = client.options("/api/v1/health", headers=headers)

        # Should have CORS headers
        assert response.headers.get("Access-Control-Allow-Origin") is not None


class TestInputValidation:
    """Test comprehensive input validation."""

    @pytest.mark.parametrize("invalid_age", [-1, 150, "invalid", None])
    def test_age_validation(self, authenticated_client, mock_auth_middleware, invalid_age):
        """Test age field validation."""
        data = {
            "Age": invalid_age,
            "Gender": 1,
            "Temperature": 25,
            "Humidity": 60,
            "hrv_mean_hr": 75
        }
        request_data = {"data": data}

        response = authenticated_client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 422

    @pytest.mark.parametrize("invalid_gender", [-1, 2, 1.5, "male"])
    def test_gender_validation(self, authenticated_client, mock_auth_middleware, invalid_gender):
        """Test gender field validation."""
        data = {
            "Age": 30,
            "Gender": invalid_gender,
            "Temperature": 25,
            "Humidity": 60,
            "hrv_mean_hr": 75
        }
        request_data = {"data": data}

        response = authenticated_client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 422

    @pytest.mark.parametrize("invalid_hr", [0, 300, -50, "invalid"])
    def test_heart_rate_validation(self, authenticated_client, mock_auth_middleware, invalid_hr):
        """Test heart rate validation."""
        data = {
            "Age": 30,
            "Gender": 1,
            "Temperature": 25,
            "Humidity": 60,
            "hrv_mean_hr": invalid_hr
        }
        request_data = {"data": data}

        response = authenticated_client.post("/api/v1/predict", json=request_data)
        assert response.status_code == 422