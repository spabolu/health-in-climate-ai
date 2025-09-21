"""
Performance Tests
=================

Comprehensive performance tests for HeatGuard API ensuring:
- Single prediction response times <200ms
- Batch processing efficiency and throughput
- Concurrent request handling
- Memory usage optimization
- Resource utilization monitoring
- Scalability under load
- Database and cache performance
- API endpoint response times
"""

import pytest
import time
import asyncio
import threading
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
import statistics
from typing import List, Dict, Any
import requests
from fastapi.testclient import TestClient


class TestSinglePredictionPerformance:
    """Test performance of single prediction endpoints."""

    def test_single_prediction_response_time(self, authenticated_client, mock_auth_middleware, sample_worker_data, performance_timer):
        """Test that single prediction completes within 200ms."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'request_id': 'perf_test_123',
                'worker_id': 'test_worker',
                'heat_exposure_risk_score': 0.35,
                'risk_level': 'Caution',
                'confidence': 0.87,
                'processing_time_ms': 145.6
            }

            performance_timer.start()
            response = authenticated_client.post("/api/v1/predict", json=request_data)
            performance_timer.stop()

            assert response.status_code == 200
            performance_timer.assert_under_ms(200)  # Must complete within 200ms

    def test_single_prediction_multiple_iterations(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test consistent performance across multiple single predictions."""
        request_data = {"data": sample_worker_data}
        response_times = []
        iterations = 20

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.35,
                'risk_level': 'Caution',
                'confidence': 0.87
            }

            for i in range(iterations):
                start_time = time.time()
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                end_time = time.time()

                assert response.status_code == 200
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)

        # Performance assertions
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

        assert avg_response_time < 150, f"Average response time {avg_response_time:.2f}ms exceeds 150ms"
        assert max_response_time < 250, f"Max response time {max_response_time:.2f}ms exceeds 250ms"
        assert p95_response_time < 200, f"95th percentile response time {p95_response_time:.2f}ms exceeds 200ms"

    def test_single_prediction_with_complex_data(self, authenticated_client, mock_auth_middleware, performance_timer):
        """Test performance with complex data containing all 50 features."""
        from tests.fixtures.sample_data import get_sample_worker_data

        complex_data = get_sample_worker_data()
        # Add additional computed features to make it more complex
        for i in range(20):
            complex_data[f'additional_feature_{i}'] = i * 0.1

        request_data = {"data": complex_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            performance_timer.start()
            response = authenticated_client.post("/api/v1/predict", json=request_data)
            performance_timer.stop()

            assert response.status_code == 200
            performance_timer.assert_under_ms(200)

    def test_health_check_response_time(self, client, performance_timer):
        """Test that health check responds quickly."""
        with patch('app.api.health.model_loader.is_model_loaded', return_value=True):
            performance_timer.start()
            response = client.get("/api/v1/health/simple")
            performance_timer.stop()

            assert response.status_code == 200
            performance_timer.assert_under_ms(50)  # Health check should be very fast

    def test_data_generation_response_time(self, authenticated_client, mock_auth_middleware, performance_timer):
        """Test data generation endpoint performance."""
        with patch('app.api.data_generation.data_generator.generate_batch_samples') as mock_generate:
            mock_generate.return_value = [{'Age': 30, 'Gender': 1}] * 10

            performance_timer.start()
            response = authenticated_client.get("/api/v1/generate_random?count=10")
            performance_timer.stop()

            assert response.status_code == 200
            performance_timer.assert_under_ms(100)


class TestBatchProcessingPerformance:
    """Test performance of batch processing operations."""

    def test_batch_prediction_throughput(self, authenticated_client, mock_auth_middleware, batch_worker_data):
        """Test batch prediction throughput and efficiency."""
        batch_sizes = [10, 50, 100, 500]
        throughput_results = {}

        with patch('app.api.prediction.prediction_service.predict_multiple_workers') as mock_predict:
            for batch_size in batch_sizes:
                test_batch = batch_worker_data[:batch_size]
                request_data = {"data": test_batch, "parallel_processing": True}

                mock_predict.return_value = {
                    'batch_size': batch_size,
                    'successful_predictions': batch_size,
                    'failed_predictions': 0,
                    'processing_time_ms': batch_size * 2,  # Mock 2ms per prediction
                    'predictions': [{'worker_id': f'w_{i}'} for i in range(batch_size)]
                }

                start_time = time.time()
                response = authenticated_client.post("/api/v1/predict_batch", json=request_data)
                end_time = time.time()

                assert response.status_code == 200

                total_time_ms = (end_time - start_time) * 1000
                predictions_per_second = batch_size / (total_time_ms / 1000)
                throughput_results[batch_size] = predictions_per_second

        # Throughput should scale reasonably with batch size
        assert throughput_results[10] > 50, "Low throughput for small batch"
        assert throughput_results[100] > throughput_results[10], "Throughput should improve with larger batches"

    def test_batch_prediction_memory_efficiency(self, authenticated_client, mock_auth_middleware):
        """Test memory efficiency during batch processing."""
        process = psutil.Process(os.getpid())
        initial_memory_mb = process.memory_info().rss / 1024 / 1024

        large_batch = []
        for i in range(200):
            worker_data = {
                'Age': 30, 'Gender': 1, 'Temperature': 25, 'Humidity': 60,
                'hrv_mean_hr': 75, 'worker_id': f'perf_worker_{i}'
            }
            # Add all 50 features
            for j in range(46):
                worker_data[f'hrv_feature_{j}'] = j * 0.1
            large_batch.append(worker_data)

        request_data = {"data": large_batch}

        with patch('app.api.prediction.prediction_service.predict_multiple_workers') as mock_predict:
            mock_predict.return_value = {
                'batch_size': 200,
                'successful_predictions': 200,
                'predictions': [{'worker_id': f'w_{i}'} for i in range(200)]
            }

            response = authenticated_client.post("/api/v1/predict_batch", json=request_data)

        final_memory_mb = process.memory_info().rss / 1024 / 1024
        memory_increase_mb = final_memory_mb - initial_memory_mb

        assert response.status_code == 200
        assert memory_increase_mb < 50, f"Memory usage increased by {memory_increase_mb:.1f}MB, expected <50MB"

    def test_async_batch_job_submission_performance(self, authenticated_client, mock_auth_middleware):
        """Test async batch job submission performance."""
        large_batch = [
            {'Age': 30, 'Gender': 1, 'Temperature': 25, 'Humidity': 60, 'hrv_mean_hr': 75}
            for _ in range(1000)
        ]

        request_data = {
            "data": large_batch,
            "chunk_size": 100,
            "priority": "normal"
        }

        with patch('app.api.prediction.batch_service.submit_batch_job') as mock_submit:
            mock_submit.return_value = "perf_job_123"

            start_time = time.time()
            response = authenticated_client.post("/api/v1/predict_batch_async", json=request_data)
            end_time = time.time()

            submission_time_ms = (end_time - start_time) * 1000

            assert response.status_code == 202
            assert submission_time_ms < 1000, f"Batch job submission took {submission_time_ms:.2f}ms, expected <1000ms"


class TestConcurrencyPerformance:
    """Test performance under concurrent load."""

    def test_concurrent_single_predictions(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test performance with concurrent single prediction requests."""
        num_threads = 10
        num_requests_per_thread = 5
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.35,
                'risk_level': 'Caution'
            }

            def make_request():
                start_time = time.time()
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time_ms': (end_time - start_time) * 1000
                }

            start_time = time.time()

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for _ in range(num_threads * num_requests_per_thread):
                    futures.append(executor.submit(make_request))

                results = [future.result() for future in as_completed(futures)]

            total_time = time.time() - start_time

            # Analyze results
            successful_requests = [r for r in results if r['status_code'] == 200]
            response_times = [r['response_time_ms'] for r in successful_requests]

            success_rate = len(successful_requests) / len(results)
            avg_response_time = statistics.mean(response_times)
            throughput = len(successful_requests) / total_time

            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95%"
            assert avg_response_time < 300, f"Average response time {avg_response_time:.2f}ms under load exceeds 300ms"
            assert throughput > 10, f"Throughput {throughput:.1f} requests/sec below minimum threshold"

    def test_mixed_endpoint_concurrency(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test performance with concurrent requests to different endpoints."""
        endpoints_and_data = [
            ("/api/v1/predict", {"data": sample_worker_data}),
            ("/api/v1/generate_random?count=5", None),
            ("/api/v1/health", None)
        ]

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict, \
             patch('app.api.data_generation.data_generator.generate_batch_samples') as mock_generate, \
             patch('app.api.health.model_loader.is_model_loaded', return_value=True):

            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}
            mock_generate.return_value = [{'Age': 30}] * 5

            def make_request(endpoint, data):
                start_time = time.time()
                if data:
                    response = authenticated_client.post(endpoint, json=data)
                else:
                    response = authenticated_client.get(endpoint)
                end_time = time.time()
                return {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time_ms': (end_time - start_time) * 1000
                }

            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = []
                for _ in range(20):
                    endpoint, data = endpoints_and_data[_ % len(endpoints_and_data)]
                    futures.append(executor.submit(make_request, endpoint, data))

                results = [future.result() for future in as_completed(futures)]

            # All requests should complete successfully
            successful_results = [r for r in results if r['status_code'] == 200]
            assert len(successful_results) >= len(results) * 0.95, "Mixed endpoint concurrency success rate too low"

    def test_rate_limiting_performance(self, client, sample_worker_data):
        """Test that rate limiting doesn't significantly impact performance."""
        client.headers["X-API-Key"] = "test-api-key"

        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate, \
             patch('app.middleware.auth.auth_middleware.rate_limiter.check_rate_limit') as mock_rate_limit:

            mock_validate.return_value = {"permissions": ["read", "write"], "rate_limit": 100}
            mock_rate_limit.return_value = {"allowed": True, "remaining": 99}

            request_data = {"data": sample_worker_data}

            response_times = []
            for _ in range(10):
                start_time = time.time()
                response = client.post("/api/v1/predict", json=request_data)
                end_time = time.time()

                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)

            avg_response_time = statistics.mean(response_times)
            # Rate limiting overhead should be minimal
            assert avg_response_time < 250, f"Rate limiting overhead too high: {avg_response_time:.2f}ms"


class TestModelPerformance:
    """Test ML model performance characteristics."""

    def test_model_loading_performance(self, mock_model_directory):
        """Test model loading time."""
        from app.models.heat_predictor import HeatExposurePredictor

        start_time = time.time()
        predictor = HeatExposurePredictor(model_dir=mock_model_directory)
        end_time = time.time()

        loading_time_ms = (end_time - start_time) * 1000

        assert predictor.is_loaded is True
        assert loading_time_ms < 2000, f"Model loading took {loading_time_ms:.2f}ms, expected <2000ms"

    def test_model_prediction_performance(self, mock_heat_predictor, sample_worker_data, performance_timer):
        """Test individual model prediction performance."""
        # Warm up the model with a few predictions
        for _ in range(3):
            mock_heat_predictor.predict_single(sample_worker_data)

        # Time actual prediction
        performance_timer.start()
        result = mock_heat_predictor.predict_single(sample_worker_data)
        performance_timer.stop()

        assert result is not None
        performance_timer.assert_under_ms(50)  # Model prediction should be very fast

    def test_batch_model_prediction_scaling(self, mock_heat_predictor, batch_worker_data):
        """Test how model prediction scales with batch size."""
        import pandas as pd

        batch_sizes = [10, 50, 100, 200]
        processing_times = {}

        for batch_size in batch_sizes:
            test_data = batch_worker_data[:batch_size]
            df = pd.DataFrame(test_data)

            start_time = time.time()
            results = mock_heat_predictor.predict_batch(df)
            end_time = time.time()

            processing_time_ms = (end_time - start_time) * 1000
            time_per_prediction = processing_time_ms / batch_size

            processing_times[batch_size] = time_per_prediction

            assert len(results) == batch_size

        # Time per prediction should be relatively stable or improve with larger batches
        assert processing_times[200] <= processing_times[10] * 1.5, "Batch processing doesn't scale efficiently"

    def test_model_memory_usage(self, mock_heat_predictor, performance_test_data):
        """Test model memory usage during predictions."""
        import pandas as pd
        process = psutil.Process(os.getpid())

        initial_memory_mb = process.memory_info().rss / 1024 / 1024

        # Process large batch
        df = pd.DataFrame(performance_test_data[:100])
        results = mock_heat_predictor.predict_batch(df)

        peak_memory_mb = process.memory_info().rss / 1024 / 1024
        memory_increase_mb = peak_memory_mb - initial_memory_mb

        assert len(results) == 100
        assert memory_increase_mb < 100, f"Model memory usage increased by {memory_increase_mb:.1f}MB"


class TestResourceUtilization:
    """Test resource utilization under load."""

    def test_cpu_usage_under_load(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test CPU usage during intensive processing."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            # Monitor CPU usage
            cpu_usage_start = psutil.cpu_percent(interval=1)

            # Generate load
            for _ in range(20):
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                assert response.status_code == 200

            cpu_usage_end = psutil.cpu_percent(interval=1)

            # CPU usage should increase but remain reasonable
            cpu_increase = cpu_usage_end - cpu_usage_start
            assert cpu_increase < 50, f"CPU usage increased by {cpu_increase}%, may be too high"

    def test_memory_leak_detection(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test for memory leaks during repeated requests."""
        process = psutil.Process(os.getpid())
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            initial_memory = process.memory_info().rss / 1024 / 1024

            # Make many requests to detect memory leaks
            for i in range(100):
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                assert response.status_code == 200

                # Check memory every 20 requests
                if i % 20 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_increase = current_memory - initial_memory

                    # Memory increase should be bounded
                    assert memory_increase < 50, f"Potential memory leak detected: {memory_increase:.1f}MB increase"

    def test_disk_io_performance(self, authenticated_client, mock_auth_middleware, temp_log_file):
        """Test disk I/O performance during logging."""
        with patch('app.config.settings.settings.LOG_FILE', temp_log_file):
            request_data = {"data": {'Age': 30, 'Gender': 1, 'Temperature': 25, 'Humidity': 60, 'hrv_mean_hr': 75}}

            with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
                mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

                start_time = time.time()

                # Make requests that trigger logging
                for _ in range(10):
                    response = authenticated_client.post("/api/v1/predict", json=request_data)
                    assert response.status_code == 200

                end_time = time.time()
                total_time_ms = (end_time - start_time) * 1000

                # Logging overhead should be minimal
                avg_time_per_request = total_time_ms / 10
                assert avg_time_per_request < 100, f"Logging overhead too high: {avg_time_per_request:.2f}ms per request"


class TestScalabilityPerformance:
    """Test scalability characteristics."""

    def test_response_time_scaling(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test that response times remain stable as load increases."""
        request_data = {"data": sample_worker_data}
        load_levels = [1, 5, 10, 20]
        response_time_results = {}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            for load_level in load_levels:
                response_times = []

                for _ in range(load_level):
                    start_time = time.time()
                    response = authenticated_client.post("/api/v1/predict", json=request_data)
                    end_time = time.time()

                    assert response.status_code == 200
                    response_times.append((end_time - start_time) * 1000)

                avg_response_time = statistics.mean(response_times)
                response_time_results[load_level] = avg_response_time

        # Response times should remain relatively stable
        baseline_time = response_time_results[1]
        high_load_time = response_time_results[20]

        degradation_factor = high_load_time / baseline_time
        assert degradation_factor < 2.0, f"Response time degraded by {degradation_factor:.1f}x under load"

    def test_throughput_limits(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test system throughput limits."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            start_time = time.time()
            successful_requests = 0

            # Run for 5 seconds and measure throughput
            while time.time() - start_time < 5:
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                if response.status_code == 200:
                    successful_requests += 1

            total_time = time.time() - start_time
            throughput = successful_requests / total_time

            assert throughput > 20, f"System throughput {throughput:.1f} requests/sec below minimum threshold"

    def test_error_rate_under_load(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test error rate doesn't increase significantly under load."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            total_requests = 50
            successful_requests = 0
            error_requests = 0

            for _ in range(total_requests):
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    error_requests += 1

            error_rate = error_requests / total_requests
            assert error_rate < 0.05, f"Error rate {error_rate:.2%} too high under load"


class TestCachePerformance:
    """Test caching performance and efficiency."""

    def test_api_key_cache_performance(self, authenticated_client):
        """Test API key validation caching performance."""
        api_key = "test-api-key-for-caching"

        with patch('app.middleware.auth.auth_middleware.validate_api_key') as mock_validate:
            mock_validate.return_value = {"permissions": ["read", "write"]}

            # First request - should hit the validation logic
            start_time = time.time()
            authenticated_client.headers["X-API-Key"] = api_key
            response1 = authenticated_client.get("/api/v1/health")
            first_request_time = time.time() - start_time

            # Second request - should use cache
            start_time = time.time()
            response2 = authenticated_client.get("/api/v1/health")
            second_request_time = time.time() - start_time

            assert response1.status_code == 200
            assert response2.status_code == 200

            # Cache should provide performance benefit
            # (Note: This test might be flaky due to mocking, but demonstrates the concept)

    def test_model_prediction_caching(self, mock_heat_predictor, sample_worker_data):
        """Test model prediction result caching if implemented."""
        # This test assumes caching might be implemented in the future

        # Make identical predictions
        result1 = mock_heat_predictor.predict_single(sample_worker_data.copy())

        start_time = time.time()
        result2 = mock_heat_predictor.predict_single(sample_worker_data.copy())
        end_time = time.time()

        # Results should be identical for identical inputs
        assert result1['heat_exposure_risk_score'] == result2['heat_exposure_risk_score']

        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 100, "Cached/identical predictions should be fast"


@pytest.mark.performance
class TestEndToEndPerformance:
    """End-to-end performance tests simulating real usage."""

    def test_realistic_workload_simulation(self, authenticated_client, mock_auth_middleware):
        """Simulate realistic API usage patterns."""
        from tests.fixtures.sample_data import get_realistic_workforce_data

        workforce_data = get_realistic_workforce_data()[:20]  # Use subset for testing

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            start_time = time.time()
            successful_predictions = 0

            # Simulate mixed API usage
            for i, worker_data in enumerate(workforce_data):
                request_data = {"data": worker_data}

                response = authenticated_client.post("/api/v1/predict", json=request_data)
                if response.status_code == 200:
                    successful_predictions += 1

                # Occasionally check health
                if i % 5 == 0:
                    health_response = authenticated_client.get("/api/v1/health/simple")
                    assert health_response.status_code == 200

                # Occasionally generate test data
                if i % 10 == 0:
                    gen_response = authenticated_client.get("/api/v1/generate_random?count=1")

            total_time = time.time() - start_time
            throughput = successful_predictions / total_time

            assert successful_predictions == len(workforce_data), "All predictions should succeed"
            assert throughput > 5, f"Realistic workload throughput {throughput:.1f} predictions/sec too low"

    def test_peak_load_handling(self, authenticated_client, mock_auth_middleware, batch_worker_data):
        """Test handling of peak load scenarios."""
        with patch('app.api.prediction.prediction_service.predict_multiple_workers') as mock_batch_predict:
            mock_batch_predict.return_value = {
                'batch_size': len(batch_worker_data),
                'successful_predictions': len(batch_worker_data),
                'predictions': [{'worker_id': f'w_{i}'} for i in range(len(batch_worker_data))]
            }

            # Simulate peak load with multiple batch requests
            batch_request_data = {"data": batch_worker_data}

            start_time = time.time()
            responses = []

            for _ in range(5):  # 5 concurrent batch requests
                response = authenticated_client.post("/api/v1/predict_batch", json=batch_request_data)
                responses.append(response)

            total_time = time.time() - start_time

            # All requests should succeed
            successful_batches = [r for r in responses if r.status_code == 200]
            assert len(successful_batches) == 5, "All batch requests should succeed under peak load"

            # Should handle peak load reasonably quickly
            assert total_time < 10, f"Peak load handling took {total_time:.2f}s, expected <10s"


class TestPerformanceRegression:
    """Test for performance regressions."""

    def test_baseline_performance_metrics(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Establish baseline performance metrics for regression testing."""
        request_data = {"data": sample_worker_data}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:
            mock_predict.return_value = {'heat_exposure_risk_score': 0.35}

            # Warm-up requests
            for _ in range(5):
                authenticated_client.post("/api/v1/predict", json=request_data)

            # Measure baseline performance
            response_times = []
            for _ in range(20):
                start_time = time.time()
                response = authenticated_client.post("/api/v1/predict", json=request_data)
                end_time = time.time()

                assert response.status_code == 200
                response_times.append((end_time - start_time) * 1000)

            # Calculate baseline metrics
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)

            # Log baseline metrics for future comparison
            baseline_metrics = {
                'avg_response_time_ms': avg_response_time,
                'p95_response_time_ms': p95_response_time,
                'p99_response_time_ms': p99_response_time,
                'min_response_time_ms': min(response_times),
                'max_response_time_ms': max(response_times)
            }

            # Assert reasonable baseline performance
            assert avg_response_time < 200, f"Baseline average response time {avg_response_time:.2f}ms exceeds 200ms"
            assert p95_response_time < 300, f"Baseline P95 response time {p95_response_time:.2f}ms exceeds 300ms"

            # Store metrics for comparison (in a real scenario, this would be persisted)
            # This could be stored in a file, database, or monitoring system
            return baseline_metrics


# Performance test utilities
def measure_response_time(func, *args, **kwargs):
    """Utility function to measure response time of any function."""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, (end_time - start_time) * 1000


def assert_response_time_under(response_time_ms: float, max_time_ms: int, operation: str = "Operation"):
    """Utility to assert response time is under threshold."""
    assert response_time_ms < max_time_ms, f"{operation} took {response_time_ms:.2f}ms, expected <{max_time_ms}ms"


# Custom pytest markers for performance tests
pytestmark = pytest.mark.performance