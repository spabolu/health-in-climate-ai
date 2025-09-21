"""
Pytest Configuration and Fixtures
=================================

Global pytest configuration and fixtures for the HeatGuard test suite.
Provides common test data, mock objects, and test environment setup.
"""

import pytest
import asyncio
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Generator
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from fastapi import FastAPI
import redis
import json
import time
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import create_app
from app.config.settings import TestingSettings
from app.models.heat_predictor import HeatExposurePredictor
from app.models.model_loader import model_loader
from app.middleware.auth import auth_middleware
from tests.fixtures.sample_data import *
from tests.fixtures.mock_responses import *


# Test configuration
TEST_API_KEY = "test-api-key-12345"
ADMIN_API_KEY = "admin-api-key-67890"
READONLY_API_KEY = "readonly-api-key-99999"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test application settings."""
    settings = TestingSettings()
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
    settings.REDIS_URL = "redis://localhost:6380"  # Test Redis instance
    settings.MODEL_DIR = "thermal_comfort_model"
    settings.ENABLE_OSHA_LOGGING = True
    settings.CONSERVATIVE_BIAS = 0.15
    return settings


@pytest.fixture(scope="session")
def test_app(test_settings):
    """Create FastAPI test application."""
    with patch('app.config.settings.settings', test_settings):
        app = create_app()
        yield app


@pytest.fixture(scope="session")
def client(test_app):
    """FastAPI test client."""
    return TestClient(test_app)


@pytest.fixture(scope="session")
def authenticated_client(test_app):
    """FastAPI test client with authentication headers."""
    client = TestClient(test_app)
    client.headers.update({"X-API-Key": TEST_API_KEY})
    return client


@pytest.fixture(scope="session")
def admin_client(test_app):
    """FastAPI test client with admin authentication."""
    client = TestClient(test_app)
    client.headers.update({"X-API-Key": ADMIN_API_KEY})
    return client


@pytest.fixture(scope="session")
def readonly_client(test_app):
    """FastAPI test client with readonly authentication."""
    client = TestClient(test_app)
    client.headers.update({"X-API-Key": READONLY_API_KEY})
    return client


@pytest.fixture(scope="function")
def mock_auth_middleware():
    """Mock authentication middleware for testing."""
    mock_auth = Mock()
    mock_auth.validate_api_key.return_value = {
        "name": "Test API Key",
        "permissions": ["read", "write", "admin"],
        "rate_limit": 1000,
        "active": True
    }
    mock_auth.check_permissions.return_value = True
    mock_auth.get_rate_limit.return_value = 1000
    mock_auth.rate_limiter.check_rate_limit.return_value = {
        "allowed": True,
        "limit": 1000,
        "remaining": 999,
        "reset_time": int(time.time() + 60),
        "current_count": 1
    }

    with patch('app.middleware.auth.auth_middleware', mock_auth):
        yield mock_auth


@pytest.fixture(scope="session")
def mock_model_directory():
    """Create a temporary directory with mock model files."""
    temp_dir = tempfile.mkdtemp()

    try:
        # Create mock model files
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler, LabelEncoder

        # Mock XGBoost model (using RandomForest as substitute)
        mock_model = RandomForestClassifier(n_estimators=10, random_state=42)
        mock_features = np.random.random((100, 50))  # 50 features
        mock_labels = np.random.randint(0, 4, 100)
        mock_model.fit(mock_features, mock_labels)

        # Mock scaler
        mock_scaler = StandardScaler()
        mock_scaler.fit(mock_features)

        # Mock label encoder
        mock_encoder = LabelEncoder()
        mock_encoder.fit(['neutral', 'slightly_warm', 'warm', 'hot'])

        # Mock feature columns
        feature_columns = get_all_feature_columns()

        # Save mock files
        joblib.dump(mock_model, os.path.join(temp_dir, "xgboost_model.joblib"))
        joblib.dump(mock_scaler, os.path.join(temp_dir, "scaler.joblib"))
        joblib.dump(mock_encoder, os.path.join(temp_dir, "label_encoder.joblib"))
        joblib.dump(feature_columns, os.path.join(temp_dir, "feature_columns.joblib"))

        yield temp_dir

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def mock_heat_predictor(mock_model_directory):
    """Mock HeatExposurePredictor for testing."""
    with patch('app.config.settings.settings.MODEL_DIR', mock_model_directory):
        predictor = HeatExposurePredictor(model_dir=mock_model_directory)
        yield predictor


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.ping.return_value = True
    mock_redis.pipeline.return_value = mock_redis
    mock_redis.zremrangebyscore.return_value = None
    mock_redis.zcard.return_value = 5
    mock_redis.zadd.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.execute.return_value = [None, 5, 1, True]
    mock_redis.zrange.return_value = [(b'123456789', 1234567890)]

    with patch('redis.from_url', return_value=mock_redis):
        yield mock_redis


@pytest.fixture(scope="function")
def sample_worker_data():
    """Sample worker data with all 50 features."""
    return get_sample_worker_data()


@pytest.fixture(scope="function")
def batch_worker_data():
    """Batch of worker data for testing."""
    return get_batch_worker_data(count=10)


@pytest.fixture(scope="function")
def invalid_worker_data():
    """Invalid worker data for negative testing."""
    return get_invalid_worker_data()


@pytest.fixture(scope="function")
def edge_case_worker_data():
    """Edge case worker data for boundary testing."""
    return get_edge_case_worker_data()


@pytest.fixture(scope="function")
def high_risk_scenario_data():
    """High risk scenario data for safety testing."""
    return get_high_risk_scenario_data()


@pytest.fixture(scope="function")
def performance_test_data():
    """Large dataset for performance testing."""
    return get_performance_test_data(count=1000)


@pytest.fixture(scope="function")
def mock_prediction_service():
    """Mock prediction service for testing."""
    mock_service = AsyncMock()
    mock_service.predict_single_worker.return_value = get_mock_prediction_response()
    mock_service.predict_multiple_workers.return_value = get_mock_batch_prediction_response()
    mock_service.get_service_health.return_value = {"status": "healthy", "predictions_count": 100}
    return mock_service


@pytest.fixture(scope="function")
def mock_batch_service():
    """Mock batch service for testing."""
    mock_service = AsyncMock()
    mock_service.submit_batch_job.return_value = "job_12345"
    mock_service.get_job_status.return_value = {
        "job_id": "job_12345",
        "status": "completed",
        "progress": 100,
        "results_available": True
    }
    mock_service.get_job_results.return_value = get_mock_batch_job_results()
    mock_service.cancel_job.return_value = True
    mock_service.list_jobs.return_value = get_mock_job_list()
    mock_service.get_service_statistics.return_value = {
        "active_jobs": 2,
        "completed_jobs": 50,
        "failed_jobs": 1
    }
    return mock_service


@pytest.fixture(scope="function")
def mock_compliance_service():
    """Mock compliance service for OSHA testing."""
    mock_service = Mock()
    mock_service.log_prediction.return_value = True
    mock_service.get_compliance_status.return_value = {
        "compliance_logging_enabled": True,
        "total_logs": 1000,
        "high_risk_incidents": 25,
        "osha_reports_generated": 12
    }
    mock_service.generate_osha_report.return_value = get_mock_osha_report()
    return mock_service


@pytest.fixture(scope="function")
def mock_data_generator():
    """Mock data generator for testing."""
    mock_generator = Mock()
    mock_generator.generate_random_sample.return_value = get_sample_worker_data()
    mock_generator.generate_batch_samples.return_value = get_batch_worker_data(count=10)
    mock_generator.generate_ramp_up_scenario.return_value = get_ramp_up_scenario_data()
    mock_generator.generate_ramp_down_scenario.return_value = get_ramp_down_scenario_data()
    mock_generator.get_generator_info.return_value = get_mock_generator_info()
    mock_generator.feature_columns = get_all_feature_columns()
    return mock_generator


# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance testing."""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None

        def assert_under_ms(self, max_ms: int):
            assert self.elapsed_ms is not None, "Timer not properly used"
            assert self.elapsed_ms < max_ms, f"Operation took {self.elapsed_ms:.2f}ms, expected < {max_ms}ms"

    return Timer()


# Database and storage fixtures
@pytest.fixture(scope="function")
def temp_log_file():
    """Temporary log file for testing."""
    fd, path = tempfile.mkstemp(suffix='.log')
    try:
        os.close(fd)
        yield path
    finally:
        if os.path.exists(path):
            os.unlink(path)


@pytest.fixture(scope="function")
def mock_file_system():
    """Mock file system operations."""
    with patch('builtins.open'), \
         patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('shutil.copy2'):
        yield


# Test utilities
def assert_valid_prediction_response(response_data: Dict[str, Any]):
    """Assert that prediction response has all required fields."""
    required_fields = [
        'heat_exposure_risk_score', 'risk_level', 'confidence',
        'temperature_celsius', 'temperature_fahrenheit', 'humidity_percent',
        'heat_index', 'osha_recommendations', 'requires_immediate_attention'
    ]

    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"

    # Validate score range
    score = response_data['heat_exposure_risk_score']
    assert 0 <= score <= 1, f"Risk score {score} not in valid range [0, 1]"

    # Validate risk level
    valid_risk_levels = ['Safe', 'Caution', 'Warning', 'Danger']
    assert response_data['risk_level'] in valid_risk_levels

    # Validate confidence
    confidence = response_data['confidence']
    assert 0 <= confidence <= 1, f"Confidence {confidence} not in valid range [0, 1]"


def assert_response_time_under_ms(response_time_ms: float, max_ms: int = 200):
    """Assert that response time is under specified milliseconds."""
    assert response_time_ms < max_ms, f"Response time {response_time_ms:.2f}ms exceeds {max_ms}ms limit"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "compliance: OSHA compliance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file names
        if "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        if "test_auth" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        if "test_compliance" in str(item.fspath):
            item.add_marker(pytest.mark.compliance)
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        else:
            item.add_marker(pytest.mark.unit)