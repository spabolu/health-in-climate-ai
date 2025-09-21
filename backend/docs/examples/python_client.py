"""
HeatGuard Python Client Library
==============================

Comprehensive Python client for the HeatGuard Predictive Safety System API.
Provides easy-to-use methods for all API endpoints with proper error handling,
authentication, rate limiting, and best practices.

Example Usage:
    from heatguard_client import HeatGuardClient

    client = HeatGuardClient(api_key="your-api-key")

    # Single prediction
    result = client.predict_single({
        "Age": 30,
        "Gender": 1,
        "Temperature": 32.5,
        "Humidity": 75.0,
        "hrv_mean_hr": 85.0
    })

    print(f"Risk Level: {result['risk_level']}")
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin

import aiohttp
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HeatGuardConfig:
    """Configuration class for HeatGuard client."""
    api_key: str
    base_url: str = "https://api.heatguard.com"
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.3
    rate_limit_delay: float = 0.1
    enable_logging: bool = True


class HeatGuardError(Exception):
    """Base exception for HeatGuard API errors."""
    pass


class AuthenticationError(HeatGuardError):
    """Raised when API key is invalid or missing."""
    pass


class ValidationError(HeatGuardError):
    """Raised when input data validation fails."""
    pass


class RateLimitError(HeatGuardError):
    """Raised when rate limit is exceeded."""
    pass


class APIError(HeatGuardError):
    """Raised when API returns an error response."""

    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class HeatGuardClient:
    """
    Synchronous client for HeatGuard Predictive Safety System API.

    This client provides methods for all API endpoints with automatic retries,
    rate limiting, and comprehensive error handling.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.heatguard.com", **kwargs):
        """
        Initialize the HeatGuard client.

        Args:
            api_key: Your HeatGuard API key
            base_url: API base URL (default: production)
            **kwargs: Additional configuration options
        """
        self.config = HeatGuardConfig(api_key=api_key, base_url=base_url, **kwargs)
        self.session = self._create_session()

        if self.config.enable_logging:
            logger.info(f"HeatGuard client initialized for {self.config.base_url}")

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update({
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json",
            "User-Agent": "HeatGuard-Python-Client/1.0.0"
        })

        return session

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make an HTTP request to the API with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for the request

        Returns:
            Dict containing the response data

        Raises:
            AuthenticationError: If API key is invalid
            ValidationError: If input data is invalid
            RateLimitError: If rate limit is exceeded
            APIError: For other API errors
        """
        url = urljoin(self.config.base_url, endpoint)

        # Add rate limiting
        time.sleep(self.config.rate_limit_delay)

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.config.timeout,
                **kwargs
            )

            # Handle different HTTP status codes
            if response.status_code == 401:
                raise AuthenticationError("Invalid or missing API key")
            elif response.status_code == 422:
                error_data = response.json() if response.content else {}
                raise ValidationError(f"Validation error: {error_data.get('detail', 'Invalid input data')}")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please wait before making more requests.")
            elif response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    f"API error: {error_data.get('detail', 'Unknown error')}",
                    status_code=response.status_code,
                    response_data=error_data
                )

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            if isinstance(e, (Timeout, ConnectionError)):
                raise APIError(f"Connection error: {str(e)}")
            raise APIError(f"Request failed: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status.

        Returns:
            Dict containing health status information
        """
        return self._make_request("GET", "/api/v1/health")

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get detailed system information.

        Returns:
            Dict containing system configuration and status
        """
        return self._make_request("GET", "/api/v1/info")

    def predict_single(
        self,
        worker_data: Dict[str, Any],
        use_conservative: bool = True,
        log_compliance: bool = True
    ) -> Dict[str, Any]:
        """
        Predict heat exposure risk for a single worker.

        Args:
            worker_data: Dictionary containing worker biometric and environmental data
            use_conservative: Apply conservative bias for safety
            log_compliance: Log prediction for OSHA compliance

        Returns:
            Dict containing prediction results

        Example:
            >>> result = client.predict_single({
            ...     "Age": 30,
            ...     "Gender": 1,
            ...     "Temperature": 32.5,
            ...     "Humidity": 75.0,
            ...     "hrv_mean_hr": 85.0
            ... })
            >>> print(result['risk_level'])
        """
        payload = {
            "data": worker_data,
            "options": {
                "use_conservative": use_conservative,
                "log_compliance": log_compliance
            }
        }

        return self._make_request("POST", "/api/v1/predict", json=payload)

    def predict_batch(
        self,
        workers_data: List[Dict[str, Any]],
        use_conservative: bool = True,
        log_compliance: bool = True,
        parallel_processing: bool = True
    ) -> Dict[str, Any]:
        """
        Predict heat exposure risk for multiple workers.

        Args:
            workers_data: List of worker data dictionaries
            use_conservative: Apply conservative bias for safety
            log_compliance: Log predictions for OSHA compliance
            parallel_processing: Process predictions in parallel

        Returns:
            Dict containing batch prediction results

        Example:
            >>> results = client.predict_batch([
            ...     {"Age": 30, "Gender": 1, "Temperature": 32.0, "Humidity": 75.0, "hrv_mean_hr": 85.0},
            ...     {"Age": 45, "Gender": 0, "Temperature": 28.0, "Humidity": 65.0, "hrv_mean_hr": 78.0}
            ... ])
        """
        payload = {
            "data": workers_data,
            "options": {
                "use_conservative": use_conservative,
                "log_compliance": log_compliance
            },
            "parallel_processing": parallel_processing
        }

        return self._make_request("POST", "/api/v1/predict_batch", json=payload)

    def submit_async_batch(
        self,
        workers_data: List[Dict[str, Any]],
        chunk_size: int = 100,
        priority: str = "normal",
        use_conservative: bool = True,
        log_compliance: bool = True
    ) -> Dict[str, Any]:
        """
        Submit a large batch for asynchronous processing.

        Args:
            workers_data: List of worker data dictionaries
            chunk_size: Processing chunk size (10-1000)
            priority: Job priority ('low', 'normal', 'high')
            use_conservative: Apply conservative bias
            log_compliance: Log for compliance

        Returns:
            Dict containing job submission details
        """
        payload = {
            "data": workers_data,
            "options": {
                "use_conservative": use_conservative,
                "log_compliance": log_compliance
            },
            "chunk_size": chunk_size,
            "priority": priority
        }

        return self._make_request("POST", "/api/v1/predict_batch_async", json=payload)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of an asynchronous batch job.

        Args:
            job_id: Job identifier returned from async batch submission

        Returns:
            Dict containing job status and progress information
        """
        return self._make_request("GET", f"/api/v1/batch_status/{job_id}")

    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get results of a completed batch job.

        Args:
            job_id: Job identifier

        Returns:
            Dict containing job results and predictions
        """
        return self._make_request("GET", f"/api/v1/batch_results/{job_id}")

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel an active batch job.

        Args:
            job_id: Job identifier

        Returns:
            Dict containing cancellation status
        """
        return self._make_request("DELETE", f"/api/v1/batch_job/{job_id}")

    def list_jobs(self, status_filter: str = None, limit: int = 50) -> Dict[str, Any]:
        """
        List batch processing jobs.

        Args:
            status_filter: Filter by job status ('pending', 'processing', 'completed', 'failed')
            limit: Maximum number of jobs to return (1-200)

        Returns:
            Dict containing list of jobs
        """
        params = {"limit": limit}
        if status_filter:
            params["status_filter"] = status_filter

        return self._make_request("GET", "/api/v1/batch_jobs", params=params)

    def generate_test_data(
        self,
        count: int = 10,
        risk_profile: str = "mixed"
    ) -> List[Dict[str, Any]]:
        """
        Generate test data for development and testing.

        Args:
            count: Number of test records (1-100)
            risk_profile: Risk profile ('safe', 'mixed', 'high')

        Returns:
            List of generated worker data records
        """
        params = {
            "count": count,
            "risk_profile": risk_profile
        }

        return self._make_request("GET", "/api/v1/generate_random", params=params)

    def wait_for_job_completion(
        self,
        job_id: str,
        check_interval: int = 5,
        max_wait_time: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for an asynchronous job to complete.

        Args:
            job_id: Job identifier
            check_interval: Time between status checks (seconds)
            max_wait_time: Maximum time to wait (seconds)

        Returns:
            Dict containing final job results

        Raises:
            TimeoutError: If job doesn't complete within max_wait_time
            APIError: If job fails
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            status = self.get_job_status(job_id)

            if status["status"] == "completed":
                return self.get_job_results(job_id)
            elif status["status"] == "failed":
                raise APIError(f"Job {job_id} failed: {status.get('error', 'Unknown error')}")

            if self.config.enable_logging:
                progress = status.get("progress", {}).get("percent_complete", 0)
                logger.info(f"Job {job_id} progress: {progress}%")

            time.sleep(check_interval)

        raise TimeoutError(f"Job {job_id} did not complete within {max_wait_time} seconds")


class AsyncHeatGuardClient:
    """
    Asynchronous client for HeatGuard API using aiohttp.

    This client provides the same functionality as the synchronous client
    but with async/await support for better performance in async applications.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.heatguard.com", **kwargs):
        """Initialize the async HeatGuard client."""
        self.config = HeatGuardConfig(api_key=api_key, base_url=base_url, **kwargs)
        self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={
                "X-API-Key": self.config.api_key,
                "Content-Type": "application/json",
                "User-Agent": "HeatGuard-Python-AsyncClient/1.0.0"
            },
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an async HTTP request."""
        if not self.session:
            raise RuntimeError("Client must be used as async context manager")

        url = urljoin(self.config.base_url, endpoint)

        # Add rate limiting
        await asyncio.sleep(self.config.rate_limit_delay)

        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid or missing API key")
                elif response.status == 422:
                    error_data = await response.json()
                    raise ValidationError(f"Validation error: {error_data.get('detail', 'Invalid input')}")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_data = await response.json() if response.content_length else {}
                    raise APIError(
                        f"API error: {error_data.get('detail', 'Unknown error')}",
                        status_code=response.status,
                        response_data=error_data
                    )

                return await response.json()

        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {str(e)}")

    async def predict_single(
        self,
        worker_data: Dict[str, Any],
        use_conservative: bool = True,
        log_compliance: bool = True
    ) -> Dict[str, Any]:
        """Async version of predict_single."""
        payload = {
            "data": worker_data,
            "options": {
                "use_conservative": use_conservative,
                "log_compliance": log_compliance
            }
        }

        return await self._make_request("POST", "/api/v1/predict", json=payload)

    async def predict_batch(
        self,
        workers_data: List[Dict[str, Any]],
        use_conservative: bool = True,
        log_compliance: bool = True,
        parallel_processing: bool = True
    ) -> Dict[str, Any]:
        """Async version of predict_batch."""
        payload = {
            "data": workers_data,
            "options": {
                "use_conservative": use_conservative,
                "log_compliance": log_compliance
            },
            "parallel_processing": parallel_processing
        }

        return await self._make_request("POST", "/api/v1/predict_batch", json=payload)


class HeatGuardMonitor:
    """
    Monitoring and alerting helper for HeatGuard predictions.

    Provides utilities for monitoring prediction results, generating alerts,
    and tracking safety metrics over time.
    """

    def __init__(self, client: HeatGuardClient):
        """Initialize monitor with a HeatGuard client."""
        self.client = client
        self.alert_thresholds = {
            "high_risk_percentage": 10.0,  # Alert if >10% predictions are high risk
            "response_time_ms": 1000,      # Alert if response time >1s
            "error_rate": 5.0              # Alert if error rate >5%
        }

    def analyze_batch_results(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze batch prediction results for safety insights.

        Args:
            batch_results: Results from predict_batch call

        Returns:
            Dict containing analysis and recommendations
        """
        predictions = batch_results.get("predictions", [])
        total_predictions = len(predictions)

        if total_predictions == 0:
            return {"error": "No predictions to analyze"}

        # Count risk levels
        risk_counts = {"Safe": 0, "Caution": 0, "Warning": 0, "Danger": 0}
        immediate_attention_count = 0
        total_response_time = 0

        for prediction in predictions:
            risk_level = prediction.get("risk_level", "Unknown")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

            if prediction.get("requires_immediate_attention", False):
                immediate_attention_count += 1

            total_response_time += prediction.get("processing_time_ms", 0)

        # Calculate metrics
        high_risk_count = risk_counts["Warning"] + risk_counts["Danger"]
        high_risk_percentage = (high_risk_count / total_predictions) * 100
        avg_response_time = total_response_time / total_predictions

        analysis = {
            "total_predictions": total_predictions,
            "risk_distribution": risk_counts,
            "high_risk_count": high_risk_count,
            "high_risk_percentage": high_risk_percentage,
            "immediate_attention_count": immediate_attention_count,
            "avg_response_time_ms": avg_response_time,
            "recommendations": []
        }

        # Generate recommendations
        if high_risk_percentage > self.alert_thresholds["high_risk_percentage"]:
            analysis["recommendations"].append(
                f"HIGH ALERT: {high_risk_percentage:.1f}% of workers are at high risk. "
                "Consider implementing immediate safety measures."
            )

        if immediate_attention_count > 0:
            analysis["recommendations"].append(
                f"IMMEDIATE ACTION REQUIRED: {immediate_attention_count} workers need immediate attention."
            )

        if avg_response_time > self.alert_thresholds["response_time_ms"]:
            analysis["recommendations"].append(
                f"Performance warning: Average response time is {avg_response_time:.0f}ms. "
                "Consider optimizing your request patterns."
            )

        return analysis

    def generate_safety_report(self, predictions: List[Dict[str, Any]]) -> str:
        """
        Generate a formatted safety report.

        Args:
            predictions: List of prediction results

        Returns:
            Formatted string report
        """
        if not predictions:
            return "No predictions available for report."

        analysis = self.analyze_batch_results({"predictions": predictions})

        report = f"""
HeatGuard Safety Report
=======================
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

Summary:
--------
Total Workers Assessed: {analysis['total_predictions']}
High-Risk Workers: {analysis['high_risk_count']} ({analysis['high_risk_percentage']:.1f}%)
Immediate Attention Required: {analysis['immediate_attention_count']}

Risk Distribution:
------------------
Safe: {analysis['risk_distribution']['Safe']} workers
Caution: {analysis['risk_distribution']['Caution']} workers
Warning: {analysis['risk_distribution']['Warning']} workers
Danger: {analysis['risk_distribution']['Danger']} workers

Performance:
------------
Average Processing Time: {analysis['avg_response_time_ms']:.0f}ms

Recommendations:
----------------
"""

        for i, recommendation in enumerate(analysis['recommendations'], 1):
            report += f"{i}. {recommendation}\n"

        if not analysis['recommendations']:
            report += "No immediate actions required. Continue monitoring.\n"

        return report


# Example usage and integration patterns
if __name__ == "__main__":
    # Example 1: Basic single prediction
    print("=== Example 1: Single Prediction ===")
    client = HeatGuardClient(api_key="your-api-key-here", base_url="http://localhost:8000")

    try:
        # Check API health first
        health = client.health_check()
        print(f"API Status: {health['status']}")

        # Make a single prediction
        worker_data = {
            "Age": 30,
            "Gender": 1,
            "Temperature": 32.5,
            "Humidity": 75.0,
            "hrv_mean_hr": 85.0,
            "hrv_mean_nni": 706.0
        }

        result = client.predict_single(worker_data)
        print(f"Risk Level: {result['risk_level']}")
        print(f"Risk Score: {result['heat_exposure_risk_score']:.3f}")
        print(f"Recommendations: {result['osha_recommendations']}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Batch prediction with monitoring
    print("\n=== Example 2: Batch Prediction with Monitoring ===")
    try:
        # Generate test data
        test_data = client.generate_test_data(count=5, risk_profile="mixed")

        # Make batch prediction
        batch_results = client.predict_batch(test_data)

        # Analyze results with monitor
        monitor = HeatGuardMonitor(client)
        analysis = monitor.analyze_batch_results(batch_results)

        print(f"Total predictions: {analysis['total_predictions']}")
        print(f"High-risk percentage: {analysis['high_risk_percentage']:.1f}%")

        # Generate safety report
        safety_report = monitor.generate_safety_report(batch_results['predictions'])
        print(safety_report)

    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Async batch processing
    print("\n=== Example 3: Async Processing ===")
    async def async_example():
        async with AsyncHeatGuardClient(api_key="your-api-key-here", base_url="http://localhost:8000") as async_client:
            try:
                # Async single prediction
                result = await async_client.predict_single({
                    "Age": 35,
                    "Gender": 0,
                    "Temperature": 29.0,
                    "Humidity": 70.0,
                    "hrv_mean_hr": 80.0
                })
                print(f"Async prediction result: {result['risk_level']}")

            except Exception as e:
                print(f"Async error: {e}")

    # Run async example
    asyncio.run(async_example())