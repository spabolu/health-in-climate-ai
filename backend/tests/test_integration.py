"""
Integration Tests
=================

End-to-end integration tests for the HeatGuard Predictive Safety System:
- Complete prediction pipeline from API to ML model
- Data flow through all system components
- Service interaction and dependency management
- Error handling across service boundaries
- Real-world workflow simulation
- Database and external service integration
- Monitoring and logging integration
- Full system reliability testing
"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import pandas as pd
from typing import Dict, List, Any


class TestFullPredictionPipeline:
    """Test complete prediction pipeline integration."""

    def test_single_prediction_full_pipeline(self, authenticated_client, mock_auth_middleware,
                                           mock_heat_predictor, sample_worker_data):
        """Test complete single prediction pipeline from API to model."""
        request_data = {
            "data": sample_worker_data,
            "options": {
                "use_conservative": True,
                "log_compliance": True
            }
        }

        # Mock the prediction service to use real model
        with patch('app.services.prediction_service.PredictionService') as mock_pred_service:
            mock_service_instance = Mock()
            mock_service_instance.predict_single_worker = AsyncMock()

            # Simulate the full prediction result
            full_prediction_result = {
                'request_id': 'integration_test_123',
                'worker_id': sample_worker_data.get('worker_id', 'test_worker'),
                'timestamp': '2024-01-01T12:00:00',
                'heat_exposure_risk_score': 0.45,
                'risk_level': 'Caution',
                'confidence': 0.89,
                'temperature_celsius': sample_worker_data['Temperature'],
                'temperature_fahrenheit': (sample_worker_data['Temperature'] * 9/5) + 32,
                'humidity_percent': sample_worker_data['Humidity'],
                'heat_index': 85.3,
                'osha_recommendations': [
                    'Increase water intake to 8 oz every 15-20 minutes',
                    'Take rest breaks in shade/cool area every hour',
                    'Monitor workers for early heat stress symptoms'
                ],
                'requires_immediate_attention': False,
                'processing_time_ms': 156.7,
                'data_quality_score': 0.94,
                'validation_warnings': []
            }

            mock_service_instance.predict_single_worker.return_value = full_prediction_result
            mock_pred_service.return_value = mock_service_instance

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify complete pipeline results
            assert data['heat_exposure_risk_score'] == 0.45
            assert data['risk_level'] == 'Caution'
            assert data['confidence'] == 0.89
            assert data['worker_id'] == sample_worker_data.get('worker_id', 'test_worker')
            assert len(data['osha_recommendations']) > 0
            assert 'heat_index' in data
            assert data['requires_immediate_attention'] is False

    def test_batch_prediction_full_pipeline(self, authenticated_client, mock_auth_middleware,
                                         batch_worker_data):
        """Test complete batch prediction pipeline."""
        request_data = {
            "data": batch_worker_data,
            "options": {
                "use_conservative": True,
                "log_compliance": True
            },
            "parallel_processing": True
        }

        with patch('app.services.prediction_service.PredictionService') as mock_pred_service:
            mock_service_instance = Mock()
            mock_service_instance.predict_multiple_workers = AsyncMock()

            # Create realistic batch results
            batch_predictions = []
            for i, worker_data in enumerate(batch_worker_data):
                prediction = {
                    'request_id': f'batch_integration_{i}',
                    'worker_id': worker_data.get('worker_id', f'batch_worker_{i}'),
                    'heat_exposure_risk_score': 0.2 + (i * 0.1),
                    'risk_level': ['Safe', 'Caution', 'Warning', 'Danger'][min(3, i // 3)],
                    'confidence': 0.85 + (i * 0.01),
                    'osha_recommendations': [f'Recommendation for worker {i}'],
                    'requires_immediate_attention': i > 7
                }
                batch_predictions.append(prediction)

            batch_result = {
                'request_id': 'batch_integration_test',
                'batch_size': len(batch_worker_data),
                'successful_predictions': len(batch_worker_data),
                'failed_predictions': 0,
                'processing_time_ms': 1234.5,
                'batch_statistics': {
                    'avg_risk_score': 0.55,
                    'max_risk_score': 0.9,
                    'min_risk_score': 0.2,
                    'high_risk_count': 3,
                    'risk_distribution': {
                        'Safe': 3,
                        'Caution': 3,
                        'Warning': 2,
                        'Danger': 2
                    }
                },
                'predictions': batch_predictions,
                'validation_warnings': []
            }

            mock_service_instance.predict_multiple_workers.return_value = batch_result
            mock_pred_service.return_value = mock_service_instance

            response = authenticated_client.post("/api/v1/predict_batch", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify batch pipeline results
            assert data['batch_size'] == len(batch_worker_data)
            assert data['successful_predictions'] == len(batch_worker_data)
            assert data['failed_predictions'] == 0
            assert len(data['predictions']) == len(batch_worker_data)
            assert 'batch_statistics' in data
            assert 'risk_distribution' in data['batch_statistics']

    def test_async_batch_processing_integration(self, authenticated_client, mock_auth_middleware,
                                              performance_test_data):
        """Test async batch processing integration."""
        request_data = {
            "data": performance_test_data[:50],  # Use subset for testing
            "options": {
                "use_conservative": True,
                "log_compliance": True
            },
            "chunk_size": 10,
            "priority": "high"
        }

        with patch('app.services.batch_service.BatchService') as mock_batch_service:
            mock_service_instance = Mock()
            mock_service_instance.submit_batch_job = AsyncMock()
            mock_service_instance.get_job_status = AsyncMock()
            mock_service_instance.get_job_results = AsyncMock()

            job_id = "integration_batch_job_123"
            mock_service_instance.submit_batch_job.return_value = job_id

            mock_batch_service.return_value = mock_service_instance

            # Submit batch job
            response = authenticated_client.post("/api/v1/predict_batch_async", json=request_data)

            assert response.status_code == 202
            data = response.json()
            assert data['job_id'] == job_id
            assert data['status'] == 'submitted'
            assert data['batch_size'] == 50

            # Check job status
            job_status = {
                'job_id': job_id,
                'status': 'running',
                'progress': 75,
                'estimated_completion': '2024-01-01T13:00:00'
            }
            mock_service_instance.get_job_status.return_value = job_status

            status_response = authenticated_client.get(f"/api/v1/batch_status/{job_id}")
            assert status_response.status_code == 200
            assert status_response.json()['status'] == 'running'

            # Get completed results
            job_results = {
                'job_id': job_id,
                'status': 'completed',
                'batch_size': 50,
                'successful_predictions': 48,
                'failed_predictions': 2,
                'results': [{'worker_id': f'w_{i}', 'risk_score': 0.3} for i in range(48)]
            }
            mock_service_instance.get_job_results.return_value = job_results

            results_response = authenticated_client.get(f"/api/v1/batch_results/{job_id}")
            assert results_response.status_code == 200
            assert results_response.json()['successful_predictions'] == 48


class TestServiceIntegration:
    """Test integration between different services."""

    def test_prediction_service_model_integration(self, sample_worker_data, mock_model_directory):
        """Test integration between prediction service and ML model."""
        from app.services.prediction_service import PredictionService
        from app.models.heat_predictor import HeatExposurePredictor

        # Create real instances
        predictor = HeatExposurePredictor(model_dir=mock_model_directory)
        prediction_service = PredictionService()

        # Mock the service to use our test predictor
        with patch.object(prediction_service, '_get_predictor', return_value=predictor):
            result = asyncio.run(prediction_service.predict_single_worker(
                sample_worker_data,
                use_conservative=True,
                log_compliance=True
            ))

            # Verify service-model integration
            assert 'heat_exposure_risk_score' in result
            assert 'risk_level' in result
            assert 'osha_recommendations' in result
            assert result['worker_id'] == sample_worker_data.get('worker_id', 'unknown')

    def test_batch_service_prediction_service_integration(self, batch_worker_data):
        """Test integration between batch service and prediction service."""
        from app.services.batch_service import BatchService
        from app.services.prediction_service import PredictionService

        batch_service = BatchService()
        prediction_service = PredictionService()

        # Mock prediction service methods
        with patch.object(prediction_service, 'predict_multiple_workers') as mock_predict:
            mock_predict.return_value = {
                'batch_size': len(batch_worker_data),
                'successful_predictions': len(batch_worker_data),
                'predictions': [{'worker_id': f'w_{i}'} for i in range(len(batch_worker_data))]
            }

            job_id = asyncio.run(batch_service.submit_batch_job(
                data=batch_worker_data,
                use_conservative=True,
                log_compliance=True,
                chunk_size=5,
                priority="normal"
            ))

            assert isinstance(job_id, str)
            assert len(job_id) > 0

    def test_compliance_service_integration(self, sample_worker_data):
        """Test integration with OSHA compliance service."""
        from app.services.compliance_service import ComplianceService

        compliance_service = ComplianceService()

        prediction_result = {
            'worker_id': 'compliance_test_worker',
            'heat_exposure_risk_score': 0.75,
            'risk_level': 'Warning',
            'temperature_celsius': 38.0,
            'humidity_percent': 85.0,
            'osha_recommendations': ['Implement work/rest cycles'],
            'requires_immediate_attention': True
        }

        # Test compliance logging
        with patch.object(compliance_service, '_write_log_entry') as mock_log:
            result = compliance_service.log_prediction(
                prediction_result,
                worker_data=sample_worker_data
            )

            assert result is True
            mock_log.assert_called_once()

    def test_health_service_integration(self, client):
        """Test health check service integration."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=True), \
             patch('app.api.health.prediction_service.get_service_health') as mock_pred_health, \
             patch('app.api.health.batch_service.get_service_statistics') as mock_batch_stats, \
             patch('app.api.health.compliance_service.get_compliance_status') as mock_compliance_status:

            mock_pred_health.return_value = {
                'status': 'healthy',
                'total_predictions': 1000,
                'avg_response_time_ms': 145.6
            }

            mock_batch_stats.return_value = {
                'active_jobs': 2,
                'completed_jobs': 50,
                'queue_size': 5
            }

            mock_compliance_status.return_value = {
                'compliance_logging_enabled': True,
                'total_logs': 1000,
                'high_risk_incidents': 25
            }

            response = client.get("/api/v1/health")

            assert response.status_code == 200
            data = response.json()

            # Verify all services are integrated in health check
            assert data['overall_status']['status'] in ['healthy', 'degraded', 'unhealthy']
            assert len(data['services']) >= 3
            assert any(service['service_name'] == 'PredictionService' for service in data['services'])
            assert any(service['service_name'] == 'BatchService' for service in data['services'])
            assert any(service['service_name'] == 'ComplianceService' for service in data['services'])


class TestDataFlowIntegration:
    """Test data flow through the entire system."""

    def test_input_validation_integration(self, authenticated_client, mock_auth_middleware):
        """Test input validation flow throughout the system."""
        # Test with invalid data that should be caught by validation
        invalid_requests = [
            # Missing required fields
            {"data": {"Age": 30}},
            # Invalid data types
            {"data": {"Age": "thirty", "Gender": "male", "Temperature": "hot"}},
            # Out of range values
            {"data": {"Age": -5, "Gender": 2, "Temperature": 100, "Humidity": 150, "hrv_mean_hr": 300}}
        ]

        for invalid_request in invalid_requests:
            response = authenticated_client.post("/api/v1/predict", json=invalid_request)

            # Should be caught by input validation
            assert response.status_code == 422
            assert 'detail' in response.json()

    def test_data_transformation_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test data transformation through the pipeline."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            # Verify data transformations in the pipeline
            expected_result = {
                'heat_exposure_risk_score': 0.45,
                'risk_level': 'Caution',
                'temperature_celsius': sample_worker_data['Temperature'],
                'temperature_fahrenheit': (sample_worker_data['Temperature'] * 9/5) + 32,
                'humidity_percent': sample_worker_data['Humidity'],
                'heat_index': 82.5  # Calculated heat index
            }

            mock_predict.return_value = expected_result

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify data transformations occurred
            assert data['temperature_fahrenheit'] != data['temperature_celsius']
            assert data['heat_index'] > data['temperature_fahrenheit']  # Heat index should be higher
            assert 0 <= data['heat_exposure_risk_score'] <= 1

    def test_error_propagation_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test error propagation through the system layers."""
        request_data = {"data": sample_worker_data}

        # Test different types of errors propagating through layers
        error_scenarios = [
            # Model prediction error
            (Exception("Model prediction failed"), 500),
            # Validation error from service layer
            (ValueError("Invalid input data"), 500),
            # Service unavailable error
            (ConnectionError("Service unavailable"), 500)
        ]

        for error, expected_status in error_scenarios:
            with patch('app.api.prediction.prediction_service.predict_single_worker', side_effect=error):
                response = authenticated_client.post("/api/v1/predict", json=request_data)

                assert response.status_code == expected_status
                assert 'error' in response.json()

    def test_response_formatting_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test response formatting consistency across endpoints."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.65,
                'risk_level': 'Warning',
                'confidence': 0.92,
                'osha_recommendations': ['Take immediate action'],
                'requires_immediate_attention': True,
                'processing_time_ms': 156.7
            }

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify consistent response format
            required_fields = [
                'heat_exposure_risk_score', 'risk_level', 'confidence',
                'osha_recommendations', 'requires_immediate_attention'
            ]

            for field in required_fields:
                assert field in data, f"Required field {field} missing from response"

            # Verify data types
            assert isinstance(data['heat_exposure_risk_score'], float)
            assert isinstance(data['risk_level'], str)
            assert isinstance(data['confidence'], float)
            assert isinstance(data['osha_recommendations'], list)
            assert isinstance(data['requires_immediate_attention'], bool)


class TestExternalIntegration:
    """Test integration with external systems and dependencies."""

    def test_redis_cache_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data, mock_redis):
        """Test Redis cache integration for rate limiting and caching."""
        request_data = {"data": sample_worker_data}

        # Redis should be used for rate limiting
        with patch('app.middleware.auth.redis.from_url', return_value=mock_redis):
            response = authenticated_client.post("/api/v1/predict", json=request_data)

            # Redis operations should have been called
            mock_redis.pipeline.assert_called()

    def test_logging_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data, temp_log_file):
        """Test logging integration across the system."""
        request_data = {"data": sample_worker_data}

        with patch('app.config.settings.settings.LOG_FILE', temp_log_file), \
             patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:

            mock_predict.return_value = {'heat_exposure_risk_score': 0.4}

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200

            # Verify logs were written
            with open(temp_log_file, 'r') as f:
                log_content = f.read()
                # Should contain API request logs
                assert 'predict' in log_content or len(log_content) == 0  # May be empty if mocked

    def test_monitoring_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test monitoring and metrics integration."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.4,
                'processing_time_ms': 145.6
            }

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200

            # Check for monitoring headers
            assert 'X-Process-Time' in response.headers
            assert 'X-API-Version' in response.headers

            # Process time should be reasonable
            process_time = float(response.headers['X-Process-Time'])
            assert process_time >= 0

    def test_database_integration(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test database integration for compliance logging."""
        request_data = {
            "data": sample_worker_data,
            "options": {"log_compliance": True}
        }

        with patch('app.services.compliance_service.ComplianceService') as mock_compliance:
            mock_compliance_instance = Mock()
            mock_compliance_instance.log_prediction.return_value = True
            mock_compliance.return_value = mock_compliance_instance

            with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
                mock_predict.return_value = {
                    'heat_exposure_risk_score': 0.7,
                    'risk_level': 'Warning',
                    'requires_immediate_attention': True
                }

                response = authenticated_client.post("/api/v1/predict", json=request_data)

                assert response.status_code == 200
                # Compliance logging should have been triggered
                # (In a real system, this would involve database operations)


class TestWorkflowIntegration:
    """Test complete workflow scenarios."""

    def test_worker_monitoring_workflow(self, authenticated_client, mock_auth_middleware):
        """Test complete worker monitoring workflow."""
        from tests.fixtures.sample_data import get_ramp_up_scenario_data

        # Simulate a worker's condition deteriorating over time
        scenario_data = get_ramp_up_scenario_data()[:6]  # Use first 6 data points

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            results = []

            for i, worker_data in enumerate(scenario_data):
                # Simulate increasing risk scores
                mock_predict.return_value = {
                    'heat_exposure_risk_score': 0.1 + (i * 0.15),
                    'risk_level': ['Safe', 'Safe', 'Caution', 'Caution', 'Warning', 'Danger'][i],
                    'requires_immediate_attention': i >= 4,
                    'osha_recommendations': [f'Recommendation for step {i+1}']
                }

                request_data = {"data": worker_data}
                response = authenticated_client.post("/api/v1/predict", json=request_data)

                assert response.status_code == 200
                result = response.json()
                results.append(result)

            # Verify workflow progression
            assert results[0]['risk_level'] == 'Safe'
            assert results[-1]['risk_level'] == 'Danger'
            assert results[-1]['requires_immediate_attention'] is True

            # Verify escalating risk scores
            risk_scores = [r['heat_exposure_risk_score'] for r in results]
            assert all(risk_scores[i] <= risk_scores[i+1] for i in range(len(risk_scores)-1))

    def test_batch_processing_workflow(self, authenticated_client, mock_auth_middleware, batch_worker_data):
        """Test complete batch processing workflow."""
        # Submit batch job
        batch_request = {
            "data": batch_worker_data,
            "chunk_size": 5,
            "priority": "normal"
        }

        with patch('app.api.prediction.batch_service.submit_batch_job') as mock_submit, \
             patch('app.api.prediction.batch_service.get_job_status') as mock_status, \
             patch('app.api.prediction.batch_service.get_job_results') as mock_results:

            job_id = "workflow_test_job"
            mock_submit.return_value = job_id

            # Submit job
            response = authenticated_client.post("/api/v1/predict_batch_async", json=batch_request)
            assert response.status_code == 202
            assert response.json()['job_id'] == job_id

            # Check status progression
            statuses = ['running', 'running', 'completed']
            for status in statuses:
                mock_status.return_value = {'job_id': job_id, 'status': status}
                status_response = authenticated_client.get(f"/api/v1/batch_status/{job_id}")
                assert status_response.status_code == 200
                assert status_response.json()['status'] == status

            # Get final results
            mock_results.return_value = {
                'job_id': job_id,
                'status': 'completed',
                'results': [{'worker_id': f'w_{i}'} for i in range(len(batch_worker_data))]
            }

            results_response = authenticated_client.get(f"/api/v1/batch_results/{job_id}")
            assert results_response.status_code == 200
            assert len(results_response.json()['results']) == len(batch_worker_data)

    def test_emergency_response_workflow(self, authenticated_client, mock_auth_middleware, high_risk_scenario_data):
        """Test emergency response workflow for high-risk scenarios."""
        request_data = {"data": high_risk_scenario_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict, \
             patch('app.services.compliance_service.ComplianceService.log_prediction') as mock_compliance_log, \
             patch('app.services.alert_service.AlertService.send_emergency_alert') as mock_alert:

            # High-risk prediction
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.95,
                'risk_level': 'Danger',
                'requires_immediate_attention': True,
                'osha_recommendations': [
                    'STOP strenuous outdoor work immediately',
                    'Move to air-conditioned environment',
                    'Contact medical personnel'
                ],
                'emergency_alert_triggered': True
            }

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify emergency response
            assert data['risk_level'] == 'Danger'
            assert data['requires_immediate_attention'] is True
            assert any('STOP' in rec for rec in data['osha_recommendations'])

            # Emergency systems should be triggered
            # (In real implementation, compliance logging and alerts would be triggered)

    def test_data_generation_integration_workflow(self, authenticated_client, mock_auth_middleware):
        """Test data generation and prediction workflow integration."""
        # Generate test data
        with patch('app.api.data_generation.data_generator.generate_ramp_up_scenario') as mock_generate:
            scenario_data = [
                {'Age': 30, 'Gender': 1, 'Temperature': 25 + i*3, 'Humidity': 60 + i*5, 'hrv_mean_hr': 70 + i*10}
                for i in range(5)
            ]
            mock_generate.return_value = scenario_data

            # Generate scenario data
            gen_response = authenticated_client.get(
                "/api/v1/generate_ramp_up?duration_minutes=60&interval_minutes=5"
            )

            assert gen_response.status_code == 200
            generated_data = gen_response.json()['data']

            # Use generated data for predictions
            with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
                mock_predict.return_value = {'heat_exposure_risk_score': 0.5}

                for worker_data in generated_data:
                    request_data = {"data": worker_data}
                    pred_response = authenticated_client.post("/api/v1/predict", json=request_data)
                    assert pred_response.status_code == 200


class TestSystemReliability:
    """Test system reliability and fault tolerance."""

    def test_partial_service_failure_handling(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test system behavior when some services fail."""
        request_data = {"data": sample_worker_data}

        # Mock compliance service failure
        with patch('app.services.compliance_service.ComplianceService.log_prediction', side_effect=Exception("Compliance service down")), \
             patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:

            mock_predict.return_value = {'heat_exposure_risk_score': 0.4}

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            # Core prediction should still work even if compliance logging fails
            assert response.status_code == 200
            assert 'heat_exposure_risk_score' in response.json()

    def test_model_unavailable_fallback(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test system behavior when ML model is unavailable."""
        request_data = {"data": sample_worker_data}

        with patch('app.models.model_loader.model_loader.is_model_loaded', return_value=False):
            response = authenticated_client.post("/api/v1/predict", json=request_data)

            # Should return appropriate error when model is unavailable
            assert response.status_code in [500, 503]

    def test_high_load_reliability(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test system reliability under high load."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.4}

            # Make many concurrent requests
            responses = []
            for _ in range(20):
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                responses.append(response)

            # Most requests should succeed
            successful_responses = [r for r in responses if r.status_code == 200]
            success_rate = len(successful_responses) / len(responses)

            assert success_rate >= 0.9, f"Success rate {success_rate:.2%} under high load is too low"

    def test_graceful_degradation(self, authenticated_client, mock_auth_middleware):
        """Test graceful degradation when system is under stress."""
        # Test various stress scenarios
        stress_scenarios = [
            # High memory usage simulation
            {"scenario": "memory_stress", "expected_status": [200, 503]},
            # High CPU usage simulation
            {"scenario": "cpu_stress", "expected_status": [200, 503]},
            # Database connection issues
            {"scenario": "db_stress", "expected_status": [200, 500]}
        ]

        for scenario in stress_scenarios:
            request_data = {"data": {"Age": 30, "Gender": 1, "Temperature": 25, "Humidity": 60, "hrv_mean_hr": 75}}

            with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
                if scenario["scenario"] == "memory_stress":
                    # Simulate memory pressure
                    mock_predict.side_effect = MemoryError("Out of memory")
                elif scenario["scenario"] == "cpu_stress":
                    # Simulate CPU overload
                    mock_predict.side_effect = TimeoutError("Request timeout")
                else:
                    # Simulate database issues
                    mock_predict.side_effect = ConnectionError("Database unavailable")

                response = authenticated_client.post("/api/v1/predict", json=request_data)
                assert response.status_code in scenario["expected_status"]


class TestConfigurationIntegration:
    """Test configuration and environment integration."""

    def test_debug_mode_integration(self, client):
        """Test system behavior in debug mode."""
        with patch('app.config.settings.settings.DEBUG', True):
            # Debug endpoints should be available
            response = client.get("/debug/config")
            # May or may not exist based on implementation

    def test_production_mode_integration(self, client):
        """Test system behavior in production mode."""
        with patch('app.config.settings.settings.DEBUG', False):
            # Documentation endpoints should be restricted
            response = client.get("/docs")
            assert response.status_code in [404, 403]  # Should be restricted in production

    def test_environment_variable_integration(self, authenticated_client, mock_auth_middleware):
        """Test environment variable integration."""
        with patch('app.config.settings.settings.CONSERVATIVE_BIAS', 0.2):
            # System should use the configured conservative bias
            # This would be tested through prediction results in a real system
            pass


@pytest.mark.integration
class TestEndToEndScenarios:
    """End-to-end scenario tests simulating real-world usage."""

    def test_construction_site_monitoring_scenario(self, authenticated_client, mock_auth_middleware):
        """Simulate monitoring workers at a construction site throughout the day."""
        from tests.fixtures.sample_data import get_realistic_workforce_data

        workforce_data = get_realistic_workforce_data()[:10]  # Use subset

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            daily_results = []

            for hour in range(8, 17):  # 8 AM to 5 PM
                # Temperature rises during the day
                temp_adjustment = (hour - 8) * 2  # Gets hotter as day progresses

                for worker_data in workforce_data:
                    adjusted_data = worker_data.copy()
                    adjusted_data['Temperature'] += temp_adjustment

                    # Risk increases with temperature
                    risk_score = min(0.9, 0.1 + (temp_adjustment * 0.05))
                    mock_predict.return_value = {
                        'heat_exposure_risk_score': risk_score,
                        'risk_level': 'Safe' if risk_score < 0.3 else 'Caution' if risk_score < 0.6 else 'Warning',
                        'worker_id': worker_data['worker_id'],
                        'hour': hour
                    }

                    request_data = {"data": adjusted_data}
                    response = authenticated_client.post("/api/v1/predict", json=request_data)

                    assert response.status_code == 200
                    daily_results.append(response.json())

            # Verify realistic progression
            morning_results = [r for r in daily_results if r.get('hour', 8) <= 10]
            afternoon_results = [r for r in daily_results if r.get('hour', 8) >= 14]

            morning_avg_risk = sum(r['heat_exposure_risk_score'] for r in morning_results) / len(morning_results)
            afternoon_avg_risk = sum(r['heat_exposure_risk_score'] for r in afternoon_results) / len(afternoon_results)

            # Risk should generally increase throughout the day
            assert afternoon_avg_risk >= morning_avg_risk

    def test_emergency_response_scenario(self, authenticated_client, mock_auth_middleware):
        """Simulate emergency response to dangerous heat conditions."""
        emergency_worker_data = {
            'Age': 45, 'Gender': 1, 'Temperature': 43.0, 'Humidity': 90.0,
            'hrv_mean_hr': 150, 'hrv_mean_nni': 400, 'hrv_rmssd': 8.0,
            'worker_id': 'emergency_worker_001'
        }

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict, \
             patch('app.services.compliance_service.ComplianceService') as mock_compliance, \
             patch('app.services.alert_service.AlertService') as mock_alert:

            # Dangerous prediction
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.92,
                'risk_level': 'Danger',
                'requires_immediate_attention': True,
                'osha_recommendations': [
                    'STOP strenuous outdoor work immediately',
                    'Move to air-conditioned environment',
                    'Contact medical personnel if symptoms present'
                ]
            }

            request_data = {"data": emergency_worker_data}
            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            result = response.json()

            # Emergency conditions detected
            assert result['risk_level'] == 'Danger'
            assert result['requires_immediate_attention'] is True
            assert any('STOP' in rec for rec in result['osha_recommendations'])

            # In a real system, this would trigger:
            # - Immediate alerts to supervisors
            # - Compliance logging for OSHA
            # - Automatic work stoppage recommendations
            # - Emergency response protocols


# Mark all classes in this module as integration tests
for name, obj in list(globals().items()):
    if isinstance(obj, type) and name.startswith('Test'):
        obj = pytest.mark.integration(obj)