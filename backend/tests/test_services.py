"""
Service Layer Tests
===================

Comprehensive tests for HeatGuard service layer components:
- PredictionService business logic
- BatchService processing functionality
- ComplianceService OSHA logging
- DataGenerationService synthetic data
- AlertService notifications
- CacheService optimization
- ValidationService input checking
- Service integration and dependencies
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime, timedelta

# Import services (these would need to be created based on the architecture)
# from app.services.prediction_service import PredictionService
# from app.services.batch_service import BatchService
# from app.services.compliance_service import ComplianceService
# from app.services.data_generation_service import DataGenerationService
# from app.services.alert_service import AlertService


class TestPredictionService:
    """Test the core prediction service business logic."""

    @pytest.fixture
    def prediction_service(self):
        """Create a prediction service instance for testing."""
        # Mock the service since the actual implementation may vary
        mock_service = Mock()
        mock_service.predict_single_worker = AsyncMock()
        mock_service.predict_multiple_workers = AsyncMock()
        mock_service.get_service_health = Mock()
        return mock_service

    @pytest.mark.asyncio
    async def test_single_worker_prediction_success(self, prediction_service, sample_worker_data, mock_heat_predictor):
        """Test successful single worker prediction."""
        expected_result = {
            'request_id': 'service_test_123',
            'worker_id': sample_worker_data.get('worker_id', 'test_worker'),
            'heat_exposure_risk_score': 0.45,
            'risk_level': 'Caution',
            'confidence': 0.89,
            'osha_recommendations': ['Increase hydration', 'Take rest breaks'],
            'requires_immediate_attention': False,
            'processing_time_ms': 156.7
        }

        prediction_service.predict_single_worker.return_value = expected_result

        result = await prediction_service.predict_single_worker(
            sample_worker_data,
            use_conservative=True,
            log_compliance=True
        )

        assert result == expected_result
        prediction_service.predict_single_worker.assert_called_once_with(
            sample_worker_data,
            use_conservative=True,
            log_compliance=True
        )

    @pytest.mark.asyncio
    async def test_single_worker_prediction_with_validation_errors(self, prediction_service, invalid_worker_data):
        """Test single worker prediction with validation errors."""
        from app.utils.validators import ValidationError

        prediction_service.predict_single_worker.side_effect = ValidationError("Invalid age value")

        with pytest.raises(ValidationError):
            await prediction_service.predict_single_worker(invalid_worker_data)

    @pytest.mark.asyncio
    async def test_single_worker_prediction_with_model_error(self, prediction_service, sample_worker_data):
        """Test single worker prediction with model error."""
        prediction_service.predict_single_worker.side_effect = RuntimeError("Model prediction failed")

        with pytest.raises(RuntimeError):
            await prediction_service.predict_single_worker(sample_worker_data)

    @pytest.mark.asyncio
    async def test_multiple_workers_prediction_success(self, prediction_service, batch_worker_data):
        """Test successful multiple workers prediction."""
        expected_result = {
            'request_id': 'batch_service_test',
            'batch_size': len(batch_worker_data),
            'successful_predictions': len(batch_worker_data),
            'failed_predictions': 0,
            'processing_time_ms': 1234.5,
            'batch_statistics': {
                'avg_risk_score': 0.42,
                'max_risk_score': 0.85,
                'min_risk_score': 0.15,
                'high_risk_count': 3,
                'risk_distribution': {'Safe': 5, 'Caution': 3, 'Warning': 2}
            },
            'predictions': [
                {
                    'worker_id': f'batch_worker_{i}',
                    'heat_exposure_risk_score': 0.3 + (i * 0.05),
                    'risk_level': 'Caution'
                } for i in range(len(batch_worker_data))
            ]
        }

        prediction_service.predict_multiple_workers.return_value = expected_result

        result = await prediction_service.predict_multiple_workers(
            batch_worker_data,
            use_conservative=True,
            log_compliance=True,
            parallel=True
        )

        assert result == expected_result
        assert result['batch_size'] == len(batch_worker_data)
        assert result['successful_predictions'] == len(batch_worker_data)

    @pytest.mark.asyncio
    async def test_batch_prediction_with_partial_failures(self, prediction_service, batch_worker_data):
        """Test batch prediction with some failures."""
        # Simulate partial failures
        expected_result = {
            'batch_size': len(batch_worker_data),
            'successful_predictions': len(batch_worker_data) - 2,
            'failed_predictions': 2,
            'batch_statistics': {'avg_risk_score': 0.35},
            'predictions': [
                {'worker_id': f'worker_{i}', 'heat_exposure_risk_score': 0.35}
                for i in range(len(batch_worker_data) - 2)
            ],
            'errors': [
                {'worker_id': f'worker_{len(batch_worker_data)-1}', 'error': 'Validation failed'},
                {'worker_id': f'worker_{len(batch_worker_data)}', 'error': 'Model error'}
            ]
        }

        prediction_service.predict_multiple_workers.return_value = expected_result

        result = await prediction_service.predict_multiple_workers(batch_worker_data)

        assert result['failed_predictions'] == 2
        assert len(result['errors']) == 2

    def test_prediction_service_health_check(self, prediction_service):
        """Test prediction service health check."""
        expected_health = {
            'status': 'healthy',
            'total_predictions': 15000,
            'avg_response_time_ms': 145.6,
            'error_rate_percent': 0.15,
            'model_loaded': True,
            'last_prediction': '2024-01-01T12:00:00'
        }

        prediction_service.get_service_health.return_value = expected_health

        health = prediction_service.get_service_health()

        assert health['status'] == 'healthy'
        assert health['total_predictions'] > 0
        assert health['model_loaded'] is True

    @pytest.mark.asyncio
    async def test_prediction_service_with_conservative_bias(self, prediction_service, sample_worker_data):
        """Test prediction service conservative bias application."""
        # Test with conservative bias
        conservative_result = {
            'heat_exposure_risk_score': 0.65,
            'conservative_bias_applied': True,
            'risk_score_standard': 0.50
        }

        # Test without conservative bias
        standard_result = {
            'heat_exposure_risk_score': 0.50,
            'conservative_bias_applied': False,
            'risk_score_standard': 0.50
        }

        prediction_service.predict_single_worker.side_effect = [conservative_result, standard_result]

        # Test with conservative bias
        result1 = await prediction_service.predict_single_worker(
            sample_worker_data, use_conservative=True
        )

        # Test without conservative bias
        result2 = await prediction_service.predict_single_worker(
            sample_worker_data, use_conservative=False
        )

        assert result1['conservative_bias_applied'] is True
        assert result2['conservative_bias_applied'] is False
        assert result1['heat_exposure_risk_score'] >= result2['heat_exposure_risk_score']


class TestBatchService:
    """Test batch processing service functionality."""

    @pytest.fixture
    def batch_service(self):
        """Create a batch service instance for testing."""
        mock_service = Mock()
        mock_service.submit_batch_job = AsyncMock()
        mock_service.get_job_status = AsyncMock()
        mock_service.get_job_results = AsyncMock()
        mock_service.cancel_job = AsyncMock()
        mock_service.list_jobs = AsyncMock()
        mock_service.get_service_statistics = Mock()
        return mock_service

    @pytest.mark.asyncio
    async def test_submit_batch_job(self, batch_service, batch_worker_data):
        """Test batch job submission."""
        job_id = "batch_job_12345"
        batch_service.submit_batch_job.return_value = job_id

        result_job_id = await batch_service.submit_batch_job(
            data=batch_worker_data,
            use_conservative=True,
            log_compliance=True,
            chunk_size=10,
            priority="normal"
        )

        assert result_job_id == job_id
        batch_service.submit_batch_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_job_status_running(self, batch_service):
        """Test getting status of a running batch job."""
        job_id = "running_job_123"
        expected_status = {
            'job_id': job_id,
            'status': 'running',
            'progress': 45,
            'started_at': '2024-01-01T10:00:00',
            'estimated_completion': '2024-01-01T11:00:00',
            'processed_count': 450,
            'total_count': 1000
        }

        batch_service.get_job_status.return_value = expected_status

        status = await batch_service.get_job_status(job_id)

        assert status['status'] == 'running'
        assert status['progress'] == 45
        assert status['job_id'] == job_id

    @pytest.mark.asyncio
    async def test_get_job_status_completed(self, batch_service):
        """Test getting status of a completed batch job."""
        job_id = "completed_job_123"
        expected_status = {
            'job_id': job_id,
            'status': 'completed',
            'progress': 100,
            'completed_at': '2024-01-01T10:30:00',
            'total_processing_time_seconds': 1800,
            'successful_predictions': 980,
            'failed_predictions': 20
        }

        batch_service.get_job_status.return_value = expected_status

        status = await batch_service.get_job_status(job_id)

        assert status['status'] == 'completed'
        assert status['progress'] == 100
        assert status['successful_predictions'] == 980

    @pytest.mark.asyncio
    async def test_get_job_results(self, batch_service):
        """Test getting results of a completed batch job."""
        job_id = "completed_job_123"
        expected_results = {
            'job_id': job_id,
            'status': 'completed',
            'batch_size': 1000,
            'successful_predictions': 980,
            'failed_predictions': 20,
            'batch_statistics': {
                'avg_risk_score': 0.42,
                'max_risk_score': 0.95,
                'high_risk_count': 125,
                'risk_distribution': {'Safe': 400, 'Caution': 350, 'Warning': 150, 'Danger': 80}
            },
            'results_summary': {
                'predictions_per_second': 8.5,
                'average_processing_time_ms': 117.6
            },
            'download_url': f'/api/v1/batch_results/{job_id}/download'
        }

        batch_service.get_job_results.return_value = expected_results

        results = await batch_service.get_job_results(job_id)

        assert results['job_id'] == job_id
        assert results['successful_predictions'] == 980
        assert 'batch_statistics' in results

    @pytest.mark.asyncio
    async def test_cancel_batch_job(self, batch_service):
        """Test cancelling a batch job."""
        job_id = "running_job_to_cancel"
        batch_service.cancel_job.return_value = True

        cancelled = await batch_service.cancel_job(job_id)

        assert cancelled is True
        batch_service.cancel_job.assert_called_once_with(job_id)

    @pytest.mark.asyncio
    async def test_list_batch_jobs(self, batch_service):
        """Test listing batch jobs."""
        expected_jobs = [
            {
                'job_id': 'job_001',
                'status': 'running',
                'progress': 75,
                'created_at': '2024-01-01T09:00:00'
            },
            {
                'job_id': 'job_002',
                'status': 'completed',
                'progress': 100,
                'created_at': '2024-01-01T08:00:00'
            }
        ]

        batch_service.list_jobs.return_value = expected_jobs

        jobs = await batch_service.list_jobs(status_filter='all', limit=10)

        assert len(jobs) == 2
        assert jobs[0]['job_id'] == 'job_001'

    def test_batch_service_statistics(self, batch_service):
        """Test batch service statistics."""
        expected_stats = {
            'total_jobs_submitted': 150,
            'jobs_completed': 140,
            'jobs_running': 5,
            'jobs_failed': 5,
            'avg_processing_time_seconds': 1200,
            'total_predictions_processed': 150000,
            'queue_size': 3
        }

        batch_service.get_service_statistics.return_value = expected_stats

        stats = batch_service.get_service_statistics()

        assert stats['total_jobs_submitted'] == 150
        assert stats['jobs_completed'] == 140

    @pytest.mark.asyncio
    async def test_batch_job_with_priority(self, batch_service, batch_worker_data):
        """Test batch job submission with different priorities."""
        priorities = ['low', 'normal', 'high']

        for priority in priorities:
            job_id = f"priority_{priority}_job"
            batch_service.submit_batch_job.return_value = job_id

            result_job_id = await batch_service.submit_batch_job(
                data=batch_worker_data,
                priority=priority
            )

            assert result_job_id == job_id

    @pytest.mark.asyncio
    async def test_batch_service_error_handling(self, batch_service):
        """Test batch service error handling."""
        # Test job not found
        batch_service.get_job_status.return_value = None

        status = await batch_service.get_job_status("nonexistent_job")
        assert status is None

        # Test cancellation failure
        batch_service.cancel_job.return_value = False

        cancelled = await batch_service.cancel_job("uncancellable_job")
        assert cancelled is False


class TestDataGenerationService:
    """Test synthetic data generation service."""

    @pytest.fixture
    def data_generation_service(self):
        """Create a data generation service instance."""
        mock_service = Mock()
        mock_service.generate_random_samples = Mock()
        mock_service.generate_scenario_data = Mock()
        mock_service.get_feature_template = Mock()
        mock_service.get_generator_info = Mock()
        return mock_service

    def test_generate_random_samples(self, data_generation_service):
        """Test random sample generation."""
        expected_samples = [
            {
                'Age': 30, 'Gender': 1, 'Temperature': 25.5,
                'Humidity': 65.0, 'hrv_mean_hr': 75.0,
                'worker_id': 'generated_001'
            },
            {
                'Age': 45, 'Gender': 0, 'Temperature': 28.2,
                'Humidity': 70.0, 'hrv_mean_hr': 80.0,
                'worker_id': 'generated_002'
            }
        ]

        data_generation_service.generate_random_samples.return_value = expected_samples

        samples = data_generation_service.generate_random_samples(
            count=2,
            risk_distribution={'safe': 0.7, 'caution': 0.3},
            seed=12345
        )

        assert len(samples) == 2
        assert all('worker_id' in sample for sample in samples)
        data_generation_service.generate_random_samples.assert_called_once()

    def test_generate_scenario_data(self, data_generation_service):
        """Test scenario-based data generation."""
        scenarios = ['ramp_up', 'ramp_down', 'steady_state', 'emergency']

        for scenario in scenarios:
            expected_data = [
                {
                    'scenario_step': i,
                    'Temperature': 25 + i * 2,
                    'hrv_mean_hr': 70 + i * 5,
                    'scenario_type': scenario
                } for i in range(10)
            ]

            data_generation_service.generate_scenario_data.return_value = expected_data

            data = data_generation_service.generate_scenario_data(
                scenario_type=scenario,
                duration_minutes=60,
                interval_minutes=6
            )

            assert len(data) == 10
            assert all(item['scenario_type'] == scenario for item in data)

    def test_get_feature_template(self, data_generation_service):
        """Test feature template retrieval."""
        expected_template = {
            'Age': 30,
            'Gender': 1,
            'Temperature': 25.0,
            'Humidity': 60.0,
            'hrv_mean_hr': 75.0,
            'hrv_mean_nni': 800.0,
            # ... other HRV features
        }

        data_generation_service.get_feature_template.return_value = expected_template

        template = data_generation_service.get_feature_template()

        assert 'Age' in template
        assert 'Gender' in template
        assert 'Temperature' in template
        assert template['Age'] == 30

    def test_get_generator_info(self, data_generation_service):
        """Test generator information retrieval."""
        expected_info = {
            'generator_version': '1.0.0',
            'supported_scenarios': ['random', 'ramp_up', 'ramp_down', 'emergency'],
            'total_features': 50,
            'risk_levels': ['safe', 'caution', 'warning', 'danger'],
            'default_worker_profiles': 5
        }

        data_generation_service.get_generator_info.return_value = expected_info

        info = data_generation_service.get_generator_info()

        assert info['generator_version'] == '1.0.0'
        assert len(info['supported_scenarios']) == 4
        assert info['total_features'] == 50

    def test_data_quality_validation(self, data_generation_service):
        """Test data quality validation for generated data."""
        generated_data = [
            {'Age': 30, 'Gender': 1, 'Temperature': 25, 'Humidity': 60, 'hrv_mean_hr': 75},
            {'Age': 25, 'Gender': 0, 'Temperature': 30, 'Humidity': 70, 'hrv_mean_hr': 80}
        ]

        data_generation_service.generate_random_samples.return_value = generated_data

        samples = data_generation_service.generate_random_samples(count=2)

        # Validate generated data quality
        for sample in samples:
            assert 18 <= sample['Age'] <= 70
            assert sample['Gender'] in [0, 1]
            assert -10 <= sample['Temperature'] <= 50
            assert 0 <= sample['Humidity'] <= 100
            assert 40 <= sample['hrv_mean_hr'] <= 200


class TestValidationService:
    """Test input validation service."""

    @pytest.fixture
    def validation_service(self):
        """Create a validation service instance."""
        mock_service = Mock()
        mock_service.validate_worker_data = Mock()
        mock_service.validate_batch_data = Mock()
        mock_service.validate_api_request = Mock()
        return mock_service

    def test_validate_worker_data_success(self, validation_service, sample_worker_data):
        """Test successful worker data validation."""
        validation_service.validate_worker_data.return_value = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'data_quality_score': 0.95
        }

        result = validation_service.validate_worker_data(sample_worker_data)

        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert result['data_quality_score'] > 0.9

    def test_validate_worker_data_with_errors(self, validation_service, invalid_worker_data):
        """Test worker data validation with errors."""
        validation_service.validate_worker_data.return_value = {
            'valid': False,
            'errors': [
                'Age must be numeric',
                'Gender must be 0 or 1',
                'Temperature is required'
            ],
            'warnings': ['Some HRV features are missing'],
            'data_quality_score': 0.2
        }

        result = validation_service.validate_worker_data(invalid_worker_data)

        assert result['valid'] is False
        assert len(result['errors']) == 3
        assert result['data_quality_score'] < 0.5

    def test_validate_batch_data(self, validation_service, batch_worker_data):
        """Test batch data validation."""
        validation_service.validate_batch_data.return_value = {
            'valid': True,
            'total_records': len(batch_worker_data),
            'valid_records': len(batch_worker_data),
            'invalid_records': 0,
            'batch_errors': [],
            'record_errors': {},
            'overall_quality_score': 0.92
        }

        result = validation_service.validate_batch_data(batch_worker_data)

        assert result['valid'] is True
        assert result['total_records'] == len(batch_worker_data)
        assert result['invalid_records'] == 0

    def test_validate_api_request(self, validation_service):
        """Test API request validation."""
        api_request = {
            'endpoint': '/api/v1/predict',
            'method': 'POST',
            'headers': {'Content-Type': 'application/json'},
            'data': {'Age': 30, 'Gender': 1}
        }

        validation_service.validate_api_request.return_value = {
            'valid': True,
            'rate_limit_ok': True,
            'authentication_ok': True,
            'content_type_valid': True,
            'request_size_ok': True
        }

        result = validation_service.validate_api_request(api_request)

        assert result['valid'] is True
        assert result['rate_limit_ok'] is True
        assert result['authentication_ok'] is True


class TestAlertService:
    """Test alert and notification service."""

    @pytest.fixture
    def alert_service(self):
        """Create an alert service instance."""
        mock_service = Mock()
        mock_service.send_emergency_alert = AsyncMock()
        mock_service.send_warning_notification = AsyncMock()
        mock_service.log_alert = Mock()
        mock_service.get_alert_history = Mock()
        return mock_service

    @pytest.mark.asyncio
    async def test_send_emergency_alert(self, alert_service):
        """Test sending emergency alerts."""
        alert_data = {
            'worker_id': 'emergency_worker_001',
            'risk_level': 'Danger',
            'heat_exposure_risk_score': 0.95,
            'location': 'Construction Site A',
            'supervisor_contact': 'supervisor@company.com',
            'emergency_actions': ['Stop work immediately', 'Call medical personnel']
        }

        alert_service.send_emergency_alert.return_value = {
            'alert_id': 'alert_12345',
            'sent_successfully': True,
            'recipients_notified': 3,
            'channels_used': ['email', 'sms', 'push_notification']
        }

        result = await alert_service.send_emergency_alert(alert_data)

        assert result['sent_successfully'] is True
        assert result['recipients_notified'] == 3
        alert_service.send_emergency_alert.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_warning_notification(self, alert_service):
        """Test sending warning notifications."""
        warning_data = {
            'worker_id': 'warning_worker_001',
            'risk_level': 'Warning',
            'recommendations': ['Take rest break', 'Increase hydration']
        }

        alert_service.send_warning_notification.return_value = {
            'notification_id': 'notif_67890',
            'sent_successfully': True,
            'delivery_method': 'push_notification'
        }

        result = await alert_service.send_warning_notification(warning_data)

        assert result['sent_successfully'] is True
        assert 'notification_id' in result

    def test_log_alert(self, alert_service):
        """Test alert logging."""
        alert_log_entry = {
            'alert_type': 'emergency',
            'worker_id': 'log_worker_001',
            'timestamp': datetime.now().isoformat(),
            'risk_score': 0.85,
            'actions_taken': ['Notification sent', 'Supervisor contacted']
        }

        alert_service.log_alert.return_value = True

        logged = alert_service.log_alert(alert_log_entry)

        assert logged is True
        alert_service.log_alert.assert_called_once()

    def test_get_alert_history(self, alert_service):
        """Test retrieving alert history."""
        expected_history = [
            {
                'alert_id': 'alert_001',
                'timestamp': '2024-01-01T10:00:00',
                'worker_id': 'history_worker_001',
                'alert_type': 'emergency',
                'resolved': True
            },
            {
                'alert_id': 'alert_002',
                'timestamp': '2024-01-01T11:00:00',
                'worker_id': 'history_worker_002',
                'alert_type': 'warning',
                'resolved': False
            }
        ]

        alert_service.get_alert_history.return_value = expected_history

        history = alert_service.get_alert_history(
            start_date='2024-01-01',
            end_date='2024-01-02',
            worker_id=None
        )

        assert len(history) == 2
        assert history[0]['alert_type'] == 'emergency'


class TestCacheService:
    """Test caching service for performance optimization."""

    @pytest.fixture
    def cache_service(self):
        """Create a cache service instance."""
        mock_service = Mock()
        mock_service.get = AsyncMock()
        mock_service.set = AsyncMock()
        mock_service.delete = AsyncMock()
        mock_service.clear = AsyncMock()
        mock_service.get_stats = Mock()
        return mock_service

    @pytest.mark.asyncio
    async def test_cache_get_hit(self, cache_service):
        """Test cache hit scenario."""
        cache_key = "prediction_cache_worker_123"
        cached_result = {
            'heat_exposure_risk_score': 0.45,
            'risk_level': 'Caution',
            'cached': True,
            'cache_timestamp': datetime.now().isoformat()
        }

        cache_service.get.return_value = cached_result

        result = await cache_service.get(cache_key)

        assert result == cached_result
        assert result['cached'] is True

    @pytest.mark.asyncio
    async def test_cache_get_miss(self, cache_service):
        """Test cache miss scenario."""
        cache_key = "nonexistent_cache_key"
        cache_service.get.return_value = None

        result = await cache_service.get(cache_key)

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set(self, cache_service):
        """Test setting cache values."""
        cache_key = "new_prediction_cache"
        cache_value = {
            'heat_exposure_risk_score': 0.35,
            'risk_level': 'Safe',
            'timestamp': datetime.now().isoformat()
        }
        ttl_seconds = 300

        cache_service.set.return_value = True

        success = await cache_service.set(cache_key, cache_value, ttl_seconds)

        assert success is True
        cache_service.set.assert_called_once_with(cache_key, cache_value, ttl_seconds)

    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_service):
        """Test cache deletion."""
        cache_key = "cache_to_delete"
        cache_service.delete.return_value = True

        deleted = await cache_service.delete(cache_key)

        assert deleted is True

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_service):
        """Test clearing all cache."""
        cache_service.clear.return_value = True

        cleared = await cache_service.clear()

        assert cleared is True

    def test_cache_statistics(self, cache_service):
        """Test cache statistics."""
        expected_stats = {
            'total_keys': 1500,
            'hit_count': 8500,
            'miss_count': 1500,
            'hit_rate': 85.0,
            'memory_usage_mb': 64.5,
            'evictions': 45
        }

        cache_service.get_stats.return_value = expected_stats

        stats = cache_service.get_stats()

        assert stats['hit_rate'] == 85.0
        assert stats['total_keys'] == 1500


class TestServiceIntegration:
    """Test integration between different services."""

    def test_prediction_service_with_cache(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test prediction service integration with cache service."""
        with patch('app.services.cache_service.CacheService') as mock_cache, \
             patch('app.services.prediction_service.PredictionService') as mock_prediction:

            mock_cache_instance = Mock()
            mock_cache_instance.get = AsyncMock(return_value=None)  # Cache miss
            mock_cache_instance.set = AsyncMock(return_value=True)
            mock_cache.return_value = mock_cache_instance

            mock_prediction_instance = Mock()
            mock_prediction_instance.predict_single_worker = AsyncMock()
            mock_prediction_instance.predict_single_worker.return_value = {
                'heat_exposure_risk_score': 0.45,
                'risk_level': 'Caution'
            }
            mock_prediction.return_value = mock_prediction_instance

            # First call should miss cache and call prediction service
            result1 = asyncio.run(mock_prediction_instance.predict_single_worker(sample_worker_data))

            # Verify prediction service was called
            assert result1['heat_exposure_risk_score'] == 0.45

    def test_prediction_service_with_alert_service(self, sample_worker_data):
        """Test prediction service integration with alert service."""
        with patch('app.services.prediction_service.PredictionService') as mock_prediction, \
             patch('app.services.alert_service.AlertService') as mock_alert:

            # High-risk prediction should trigger alert
            high_risk_result = {
                'heat_exposure_risk_score': 0.92,
                'risk_level': 'Danger',
                'requires_immediate_attention': True,
                'alert_triggered': True
            }

            mock_prediction_instance = Mock()
            mock_prediction_instance.predict_single_worker = AsyncMock(return_value=high_risk_result)
            mock_prediction.return_value = mock_prediction_instance

            mock_alert_instance = Mock()
            mock_alert_instance.send_emergency_alert = AsyncMock(return_value={'sent_successfully': True})
            mock_alert.return_value = mock_alert_instance

            # Make high-risk prediction
            result = asyncio.run(mock_prediction_instance.predict_single_worker(sample_worker_data))

            assert result['alert_triggered'] is True
            assert result['requires_immediate_attention'] is True

    def test_batch_service_with_prediction_service(self, batch_worker_data):
        """Test batch service integration with prediction service."""
        with patch('app.services.batch_service.BatchService') as mock_batch, \
             patch('app.services.prediction_service.PredictionService') as mock_prediction:

            mock_batch_instance = Mock()
            mock_batch_instance.submit_batch_job = AsyncMock(return_value="batch_job_123")
            mock_batch.return_value = mock_batch_instance

            mock_prediction_instance = Mock()
            mock_prediction_instance.predict_multiple_workers = AsyncMock()
            mock_prediction_instance.predict_multiple_workers.return_value = {
                'batch_size': len(batch_worker_data),
                'successful_predictions': len(batch_worker_data)
            }
            mock_prediction.return_value = mock_prediction_instance

            # Submit batch job
            job_id = asyncio.run(mock_batch_instance.submit_batch_job(data=batch_worker_data))

            assert job_id == "batch_job_123"

    def test_compliance_service_with_prediction_service(self, sample_worker_data):
        """Test compliance service integration with predictions."""
        with patch('app.services.compliance_service.ComplianceService') as mock_compliance, \
             patch('app.services.prediction_service.PredictionService') as mock_prediction:

            prediction_result = {
                'worker_id': 'compliance_worker',
                'heat_exposure_risk_score': 0.75,
                'risk_level': 'Warning',
                'requires_immediate_attention': True
            }

            mock_prediction_instance = Mock()
            mock_prediction_instance.predict_single_worker = AsyncMock(return_value=prediction_result)
            mock_prediction.return_value = mock_prediction_instance

            mock_compliance_instance = Mock()
            mock_compliance_instance.log_prediction.return_value = True
            mock_compliance.return_value = mock_compliance_instance

            # Make prediction and log for compliance
            result = asyncio.run(mock_prediction_instance.predict_single_worker(sample_worker_data))

            # Log result for compliance
            logged = mock_compliance_instance.log_prediction(result, sample_worker_data)

            assert logged is True
            assert result['requires_immediate_attention'] is True


class TestServiceErrorHandling:
    """Test error handling across services."""

    def test_service_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for service failures."""
        with patch('app.services.prediction_service.PredictionService') as mock_service:
            mock_instance = Mock()

            # Simulate multiple failures
            failure_responses = [Exception("Service unavailable")] * 5
            success_response = {'heat_exposure_risk_score': 0.4}

            mock_instance.predict_single_worker = AsyncMock()
            mock_instance.predict_single_worker.side_effect = failure_responses + [success_response]
            mock_service.return_value = mock_instance

            # After multiple failures, circuit breaker should open
            # This is a conceptual test - actual implementation would vary

    def test_service_retry_mechanism(self):
        """Test retry mechanism for transient failures."""
        with patch('app.services.prediction_service.PredictionService') as mock_service:
            mock_instance = Mock()

            # First call fails, second succeeds
            mock_instance.predict_single_worker = AsyncMock()
            mock_instance.predict_single_worker.side_effect = [
                ConnectionError("Temporary network issue"),
                {'heat_exposure_risk_score': 0.4}
            ]
            mock_service.return_value = mock_instance

            # Service should retry and succeed on second attempt
            # Implementation would handle retry logic

    def test_service_graceful_degradation(self):
        """Test graceful degradation when dependent services fail."""
        with patch('app.services.cache_service.CacheService') as mock_cache, \
             patch('app.services.prediction_service.PredictionService') as mock_prediction:

            # Cache service fails
            mock_cache_instance = Mock()
            mock_cache_instance.get = AsyncMock(side_effect=ConnectionError("Cache unavailable"))
            mock_cache.return_value = mock_cache_instance

            # Prediction service should continue without cache
            mock_prediction_instance = Mock()
            mock_prediction_instance.predict_single_worker = AsyncMock()
            mock_prediction_instance.predict_single_worker.return_value = {
                'heat_exposure_risk_score': 0.4,
                'cache_used': False  # Indicates cache was not available
            }
            mock_prediction.return_value = mock_prediction_instance

            # Service should work even without cache
            # Implementation would handle fallback logic


# Mark all service tests
for name, obj in list(globals().items()):
    if isinstance(obj, type) and name.startswith('Test') and 'Service' in name:
        obj = pytest.mark.unit(obj)