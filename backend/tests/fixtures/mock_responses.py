"""
Mock API Responses
==================

Mock response data for testing HeatGuard API endpoints and services.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union
import uuid


def get_mock_prediction_response() -> Dict[str, Any]:
    """Mock single prediction response."""
    return {
        'request_id': f'req_{int(time.time() * 1000)}',
        'worker_id': 'test_worker_001',
        'timestamp': datetime.now().isoformat(),
        'heat_exposure_risk_score': 0.35,
        'risk_level': 'Caution',
        'confidence': 0.87,
        'temperature_celsius': 25.5,
        'temperature_fahrenheit': 77.9,
        'humidity_percent': 65.0,
        'heat_index': 79.2,
        'osha_recommendations': [
            'Increase water intake to 8 oz every 15-20 minutes',
            'Take rest breaks in shade/cool area every hour',
            'Monitor workers for early heat stress symptoms'
        ],
        'requires_immediate_attention': False,
        'processing_time_ms': 45.6,
        'data_quality_score': 0.92,
        'validation_warnings': []
    }


def get_mock_batch_prediction_response() -> Dict[str, Any]:
    """Mock batch prediction response."""
    predictions = []
    for i in range(10):
        pred = get_mock_prediction_response()
        pred['worker_id'] = f'batch_worker_{i+1:03d}'
        pred['heat_exposure_risk_score'] = 0.2 + (i * 0.08)  # Varying risk scores
        pred['risk_level'] = ['Safe', 'Caution', 'Warning', 'Danger'][min(3, i // 3)]
        predictions.append(pred)

    return {
        'request_id': f'batch_{int(time.time() * 1000)}',
        'batch_size': 10,
        'successful_predictions': 10,
        'failed_predictions': 0,
        'processing_time_ms': 234.5,
        'batch_statistics': {
            'avg_risk_score': 0.56,
            'max_risk_score': 0.92,
            'min_risk_score': 0.20,
            'high_risk_count': 3,
            'low_risk_count': 2,
            'risk_distribution': {
                'Safe': 2,
                'Caution': 3,
                'Warning': 3,
                'Danger': 2
            }
        },
        'predictions': predictions,
        'validation_warnings': []
    }


def get_mock_batch_job_results() -> Dict[str, Any]:
    """Mock async batch job results."""
    return {
        'job_id': 'job_12345',
        'status': 'completed',
        'batch_size': 1000,
        'successful_predictions': 995,
        'failed_predictions': 5,
        'processing_time_ms': 15678.9,
        'completion_time': datetime.now().isoformat(),
        'batch_statistics': {
            'avg_risk_score': 0.42,
            'max_risk_score': 0.98,
            'min_risk_score': 0.05,
            'high_risk_count': 156,
            'medium_risk_count': 432,
            'low_risk_count': 407,
            'risk_distribution': {
                'Safe': 407,
                'Caution': 276,
                'Warning': 156,
                'Danger': 156
            }
        },
        'results_summary': {
            'total_processing_time_seconds': 15.68,
            'average_prediction_time_ms': 15.7,
            'predictions_per_second': 63.4,
            'memory_usage_mb': 128.5
        },
        'download_url': '/api/v1/batch_results/job_12345/download',
        'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
    }


def get_mock_job_list() -> List[Dict[str, Any]]:
    """Mock job list for batch processing."""
    jobs = []
    statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']

    for i in range(10):
        job = {
            'job_id': f'job_{12345 + i}',
            'status': statuses[i % len(statuses)],
            'batch_size': 100 * (i + 1),
            'created_at': (datetime.now() - timedelta(hours=i)).isoformat(),
            'updated_at': (datetime.now() - timedelta(minutes=i * 10)).isoformat(),
            'priority': ['low', 'normal', 'high'][i % 3],
            'progress_percent': min(100, i * 11) if statuses[i % len(statuses)] in ['running', 'completed'] else 0
        }

        if job['status'] == 'completed':
            job['completed_at'] = job['updated_at']
            job['results_available'] = True
        elif job['status'] == 'failed':
            job['error_message'] = f'Processing error in job {job["job_id"]}'

        jobs.append(job)

    return jobs


def get_mock_health_check_response() -> Dict[str, Any]:
    """Mock comprehensive health check response."""
    return {
        'overall_status': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'uptime_seconds': 3600.5
        },
        'system_info': {
            'platform': 'Darwin-21.6.0-x86_64-i386-64bit',
            'python_version': '3.9.12',
            'cpu_count': 8,
            'memory_total_gb': 16.0,
            'memory_available_gb': 8.5,
            'cpu_usage_percent': 25.3,
            'disk_usage_percent': 45.8
        },
        'model_status': {
            'model_loaded': True,
            'model_type': 'XGBoost Heat Exposure Predictor',
            'load_time': '2024-01-01T10:00:00Z',
            'feature_count': 50,
            'target_classes': ['neutral', 'slightly_warm', 'warm', 'hot'],
            'performance_ok': True
        },
        'services': [
            {
                'service_name': 'PredictionService',
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'details': {
                    'total_predictions': 15234,
                    'avg_response_time_ms': 156.7,
                    'error_rate_percent': 0.12
                }
            },
            {
                'service_name': 'BatchService',
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'details': {
                    'active_jobs': 2,
                    'completed_jobs': 45,
                    'queue_size': 0
                }
            },
            {
                'service_name': 'ComplianceService',
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'details': {
                    'compliance_logging_enabled': True,
                    'logs_written': 12453,
                    'osha_reports_generated': 8
                }
            }
        ],
        'configuration': {
            'version': '1.0.0',
            'debug_mode': False,
            'osha_compliance_enabled': True,
            'max_batch_size': 1000,
            'conservative_bias': 0.15,
            'cache_enabled': True
        }
    }


def get_mock_data_generation_response() -> Dict[str, Any]:
    """Mock data generation response."""
    from .sample_data import get_batch_worker_data

    generated_data = get_batch_worker_data(count=10)

    return {
        'request_id': f'gen_{int(time.time() * 1000)}',
        'generation_type': 'random',
        'count': len(generated_data),
        'generation_time_ms': 23.4,
        'data': generated_data,
        'metadata': {
            'risk_distribution_used': 'default',
            'seed_used': None,
            'features_per_sample': 50,
            'generator_info': get_mock_generator_info()
        },
        'timestamp': datetime.now().isoformat()
    }


def get_mock_generator_info() -> Dict[str, Any]:
    """Mock data generator information."""
    return {
        'generator_version': '1.0.0',
        'total_features': 50,
        'worker_profiles': 5,
        'supported_scenarios': ['random', 'ramp_up', 'ramp_down', 'batch_configured'],
        'risk_levels': ['safe', 'caution', 'warning', 'danger'],
        'feature_ranges': {
            'Age': [18, 65],
            'Temperature': [-10, 50],
            'Humidity': [0, 100],
            'hrv_mean_hr': [40, 200],
            'hrv_rmssd': [1, 150]
        }
    }


def get_mock_osha_report() -> Dict[str, Any]:
    """Mock OSHA compliance report."""
    return {
        'report_id': f'osha_{int(time.time())}',
        'generated_at': datetime.now().isoformat(),
        'report_period': {
            'start_date': (datetime.now() - timedelta(days=30)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'duration_days': 30
        },
        'summary': {
            'total_assessments': 5234,
            'high_risk_incidents': 234,
            'workers_monitored': 156,
            'compliance_rate_percent': 98.5
        },
        'risk_breakdown': {
            'safe_assessments': 3456,
            'caution_assessments': 1234,
            'warning_assessments': 345,
            'danger_assessments': 199
        },
        'intervention_metrics': {
            'automatic_alerts_sent': 234,
            'work_stoppages_recommended': 45,
            'cooling_breaks_suggested': 567,
            'medical_referrals': 12
        },
        'environmental_data': {
            'avg_temperature_celsius': 28.5,
            'max_temperature_celsius': 42.1,
            'avg_humidity_percent': 68.2,
            'max_heat_index': 98.7
        },
        'recommendations': [
            'Increase cooling stations in high-risk areas',
            'Implement additional training for workers in extreme conditions',
            'Consider adjusting work schedules during peak heat hours'
        ],
        'compliance_status': 'COMPLIANT'
    }


def get_mock_error_responses() -> Dict[str, Dict[str, Any]]:
    """Mock error responses for testing."""
    return {
        'validation_error': {
            'error': 'Input validation failed',
            'detail': 'Missing required field: hrv_mean_hr',
            'status_code': 422,
            'timestamp': datetime.now().isoformat()
        },
        'authentication_error': {
            'error': 'Invalid API key',
            'detail': 'The provided API key is not valid',
            'status_code': 401,
            'timestamp': datetime.now().isoformat()
        },
        'rate_limit_error': {
            'error': 'Rate limit exceeded',
            'detail': 'Rate limit exceeded. Limit: 100 requests per minute',
            'status_code': 429,
            'timestamp': datetime.now().isoformat(),
            'retry_after': 60
        },
        'server_error': {
            'error': 'Internal server error',
            'detail': 'An unexpected error occurred',
            'status_code': 500,
            'timestamp': datetime.now().isoformat(),
            'request_id': f'req_{int(time.time() * 1000)}'
        },
        'model_error': {
            'error': 'Model prediction failed',
            'detail': 'The machine learning model encountered an error',
            'status_code': 503,
            'timestamp': datetime.now().isoformat()
        }
    }


def get_mock_performance_metrics() -> Dict[str, Any]:
    """Mock performance metrics for testing."""
    return {
        'response_times': {
            'single_prediction_ms': 145.6,
            'batch_prediction_ms': 2345.7,
            'health_check_ms': 12.3,
            'data_generation_ms': 34.5
        },
        'throughput': {
            'predictions_per_second': 45.2,
            'batch_processing_rate': 156.7,
            'concurrent_requests': 12
        },
        'resource_usage': {
            'cpu_usage_percent': 25.8,
            'memory_usage_mb': 256.4,
            'disk_io_mb_per_sec': 5.2
        },
        'cache_metrics': {
            'hit_rate_percent': 87.3,
            'miss_rate_percent': 12.7,
            'cache_size_mb': 45.6
        },
        'model_metrics': {
            'model_load_time_ms': 1234.5,
            'prediction_accuracy': 0.94,
            'feature_processing_time_ms': 23.4
        }
    }


def get_mock_security_audit() -> Dict[str, Any]:
    """Mock security audit data."""
    return {
        'audit_id': f'audit_{int(time.time())}',
        'timestamp': datetime.now().isoformat(),
        'period': {
            'start': (datetime.now() - timedelta(hours=24)).isoformat(),
            'end': datetime.now().isoformat()
        },
        'authentication_events': {
            'successful_logins': 1234,
            'failed_logins': 23,
            'api_key_validations': 15234,
            'rate_limit_violations': 45
        },
        'security_headers': {
            'x_content_type_options': 'present',
            'x_frame_options': 'present',
            'strict_transport_security': 'present',
            'cache_control': 'present'
        },
        'vulnerability_scan': {
            'last_scan': datetime.now().isoformat(),
            'high_risk_issues': 0,
            'medium_risk_issues': 2,
            'low_risk_issues': 5,
            'status': 'PASS'
        },
        'access_patterns': {
            'unique_api_keys': 12,
            'top_endpoints': [
                '/api/v1/predict',
                '/api/v1/health',
                '/api/v1/generate_random'
            ],
            'suspicious_activity': False
        }
    }


def get_mock_load_test_results() -> Dict[str, Any]:
    """Mock load testing results."""
    return {
        'test_id': f'load_test_{int(time.time())}',
        'timestamp': datetime.now().isoformat(),
        'test_configuration': {
            'duration_seconds': 300,
            'concurrent_users': 50,
            'requests_per_second': 100,
            'test_scenarios': ['single_prediction', 'batch_prediction', 'health_check']
        },
        'results': {
            'total_requests': 30000,
            'successful_requests': 29876,
            'failed_requests': 124,
            'success_rate_percent': 99.59,
            'average_response_time_ms': 156.7,
            'p95_response_time_ms': 234.5,
            'p99_response_time_ms': 345.6,
            'max_response_time_ms': 567.8,
            'requests_per_second_achieved': 99.6
        },
        'performance_breakdown': {
            'single_prediction': {
                'count': 15000,
                'avg_response_ms': 145.6,
                'success_rate': 99.8
            },
            'batch_prediction': {
                'count': 3000,
                'avg_response_ms': 1234.5,
                'success_rate': 99.2
            },
            'health_check': {
                'count': 12000,
                'avg_response_ms': 23.4,
                'success_rate': 100.0
            }
        },
        'resource_utilization': {
            'peak_cpu_percent': 78.5,
            'peak_memory_mb': 512.3,
            'peak_disk_io_mb_per_sec': 15.6
        },
        'errors': [
            {'type': 'timeout', 'count': 45, 'percentage': 0.15},
            {'type': 'rate_limit', 'count': 23, 'percentage': 0.08},
            {'type': 'server_error', 'count': 56, 'percentage': 0.19}
        ]
    }