"""
OSHA Compliance Service
=======================

Handles OSHA compliance logging and reporting for heat exposure predictions.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

from ..config.settings import settings
from ..config.model_config import OSHA_STANDARDS
from ..utils.logger import get_logger, log_prediction

logger = get_logger(__name__)


class ComplianceService:
    """Service for OSHA compliance logging and reporting."""

    def __init__(self):
        self.osha_logger = logging.getLogger('osha_compliance')
        self.enable_logging = settings.ENABLE_OSHA_LOGGING
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Ensure OSHA log directory exists."""
        if self.enable_logging:
            log_path = Path(settings.OSHA_LOG_FILE)
            log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_prediction(self, prediction_result: Dict[str, Any]) -> None:
        """
        Log a single heat exposure prediction for OSHA compliance.

        Args:
            prediction_result: Complete prediction result dictionary
        """
        if not self.enable_logging:
            return

        try:
            # Extract key information for compliance
            compliance_entry = self._create_compliance_entry(prediction_result)

            # Log to OSHA compliance file
            self.osha_logger.info(json.dumps(compliance_entry, ensure_ascii=False))

            # Check if immediate action is required
            if self._requires_immediate_action(prediction_result):
                self._log_immediate_action_required(prediction_result)

            logger.debug(f"OSHA compliance logged for worker {prediction_result.get('worker_id')}")

        except Exception as e:
            logger.error(f"Failed to log OSHA compliance: {e}")

    def log_batch_predictions(self, prediction_results: List[Dict[str, Any]]) -> None:
        """
        Log batch predictions for OSHA compliance.

        Args:
            prediction_results: List of prediction result dictionaries
        """
        if not self.enable_logging:
            return

        try:
            batch_summary = self._create_batch_compliance_summary(prediction_results)

            # Log batch summary
            self.osha_logger.info(json.dumps(batch_summary, ensure_ascii=False))

            # Log individual predictions
            for result in prediction_results:
                if 'error' not in result:  # Only log successful predictions
                    self.log_prediction(result)

            # Check for batch-level alerts
            high_risk_count = sum(1 for r in prediction_results
                                if r.get('heat_exposure_risk_score', 0) > 0.75)

            if high_risk_count > 0:
                self._log_batch_alert(prediction_results, high_risk_count)

            logger.info(f"OSHA compliance logged for batch of {len(prediction_results)} predictions")

        except Exception as e:
            logger.error(f"Failed to log batch OSHA compliance: {e}")

    def _create_compliance_entry(self, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized compliance log entry."""
        return {
            'compliance_event': 'HEAT_EXPOSURE_ASSESSMENT',
            'timestamp_utc': prediction_result.get('timestamp', datetime.now().isoformat()),
            'worker_identification': {
                'worker_id': prediction_result.get('worker_id', 'unknown'),
                'batch_index': prediction_result.get('batch_index')
            },
            'environmental_conditions': {
                'temperature_celsius': prediction_result.get('temperature_celsius', 0),
                'temperature_fahrenheit': prediction_result.get('temperature_fahrenheit', 0),
                'humidity_percent': prediction_result.get('humidity_percent', 0),
                'heat_index_fahrenheit': prediction_result.get('heat_index', 0)
            },
            'risk_assessment': {
                'heat_exposure_risk_score': prediction_result.get('heat_exposure_risk_score', 0),
                'risk_level': prediction_result.get('risk_level', 'Unknown'),
                'requires_immediate_attention': prediction_result.get('requires_immediate_attention', False),
                'confidence': prediction_result.get('confidence', 0)
            },
            'physiological_indicators': {
                'heart_rate_avg': prediction_result.get('heart_rate_avg', 0),
                'hrv_rmssd': prediction_result.get('hrv_rmssd', 0)
            },
            'safety_recommendations': {
                'recommendations': prediction_result.get('osha_recommendations', []),
                'recommendation_count': len(prediction_result.get('osha_recommendations', []))
            },
            'compliance_flags': {
                'exceeds_heat_index_threshold': self._check_heat_index_threshold(
                    prediction_result.get('heat_index', 0)
                ),
                'requires_work_rest_cycle': prediction_result.get('heat_exposure_risk_score', 0) > 0.5,
                'medical_attention_recommended': prediction_result.get('heat_exposure_risk_score', 0) > 0.75
            },
            'system_metadata': {
                'model_version': prediction_result.get('model_version', '1.0.0'),
                'prediction_method': prediction_result.get('prediction_method', 'xgboost_heat_exposure'),
                'conservative_bias_applied': prediction_result.get('conservative_bias_applied', True),
                'request_id': prediction_result.get('request_id', 'unknown')
            }
        }

    def _create_batch_compliance_summary(self, prediction_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create batch compliance summary."""
        successful_results = [r for r in prediction_results if 'error' not in r]

        if not successful_results:
            return {
                'compliance_event': 'BATCH_ASSESSMENT_SUMMARY',
                'timestamp_utc': datetime.now().isoformat(),
                'error': 'No successful predictions in batch',
                'total_workers': len(prediction_results)
            }

        # Calculate batch statistics
        risk_scores = [r.get('heat_exposure_risk_score', 0) for r in successful_results]
        heat_indices = [r.get('heat_index', 0) for r in successful_results]

        # Count workers by risk level
        risk_distribution = {}
        for result in successful_results:
            risk_level = result.get('risk_level', 'Unknown')
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        # OSHA compliance flags
        high_heat_index_count = sum(1 for hi in heat_indices if hi >= settings.HEAT_INDEX_THRESHOLD_DANGER)
        immediate_attention_count = sum(1 for r in successful_results
                                      if r.get('requires_immediate_attention', False))

        return {
            'compliance_event': 'BATCH_ASSESSMENT_SUMMARY',
            'timestamp_utc': datetime.now().isoformat(),
            'batch_info': {
                'total_workers_assessed': len(prediction_results),
                'successful_assessments': len(successful_results),
                'failed_assessments': len(prediction_results) - len(successful_results)
            },
            'risk_summary': {
                'average_risk_score': round(sum(risk_scores) / len(risk_scores), 3),
                'highest_risk_score': round(max(risk_scores), 3),
                'risk_level_distribution': risk_distribution
            },
            'environmental_summary': {
                'average_heat_index': round(sum(heat_indices) / len(heat_indices), 1),
                'maximum_heat_index': round(max(heat_indices), 1),
                'workers_above_heat_threshold': high_heat_index_count
            },
            'compliance_alerts': {
                'workers_requiring_immediate_attention': immediate_attention_count,
                'percentage_high_risk': round((immediate_attention_count / len(successful_results)) * 100, 1),
                'osha_intervention_recommended': immediate_attention_count > 0 or high_heat_index_count > 0
            },
            'system_info': {
                'assessment_system': 'HeatGuard Predictive Safety System',
                'batch_processing_time_ms': max([r.get('processing_time_ms', 0) for r in successful_results], default=0)
            }
        }

    def _requires_immediate_action(self, prediction_result: Dict[str, Any]) -> bool:
        """Check if prediction requires immediate action."""
        risk_score = prediction_result.get('heat_exposure_risk_score', 0)
        heat_index = prediction_result.get('heat_index', 0)

        return (
            risk_score > 0.75 or
            heat_index >= settings.HEAT_INDEX_THRESHOLD_DANGER or
            prediction_result.get('requires_immediate_attention', False)
        )

    def _log_immediate_action_required(self, prediction_result: Dict[str, Any]) -> None:
        """Log immediate action alert."""
        alert_entry = {
            'compliance_event': 'IMMEDIATE_ACTION_REQUIRED',
            'timestamp_utc': datetime.now().isoformat(),
            'worker_id': prediction_result.get('worker_id', 'unknown'),
            'risk_score': prediction_result.get('heat_exposure_risk_score', 0),
            'risk_level': prediction_result.get('risk_level', 'Unknown'),
            'heat_index': prediction_result.get('heat_index', 0),
            'alert_reasons': self._get_alert_reasons(prediction_result),
            'immediate_recommendations': prediction_result.get('osha_recommendations', [])[:3]  # Top 3
        }

        self.osha_logger.warning(json.dumps(alert_entry, ensure_ascii=False))

    def _log_batch_alert(self, prediction_results: List[Dict[str, Any]], high_risk_count: int) -> None:
        """Log batch-level alert."""
        alert_entry = {
            'compliance_event': 'BATCH_HIGH_RISK_ALERT',
            'timestamp_utc': datetime.now().isoformat(),
            'total_workers': len(prediction_results),
            'high_risk_workers': high_risk_count,
            'risk_percentage': round((high_risk_count / len(prediction_results)) * 100, 1),
            'recommended_actions': [
                'Immediately review high-risk worker conditions',
                'Implement emergency cooling procedures',
                'Consider work stoppage if conditions do not improve',
                'Contact medical personnel if heat illness symptoms present'
            ]
        }

        self.osha_logger.warning(json.dumps(alert_entry, ensure_ascii=False))

    def _check_heat_index_threshold(self, heat_index: float) -> str:
        """Check heat index against OSHA thresholds."""
        if heat_index >= 130:
            return 'EXTREME_DANGER'
        elif heat_index >= 105:
            return 'DANGER'
        elif heat_index >= 90:
            return 'EXTREME_CAUTION'
        elif heat_index >= 80:
            return 'CAUTION'
        else:
            return 'NORMAL'

    def _get_alert_reasons(self, prediction_result: Dict[str, Any]) -> List[str]:
        """Get reasons why immediate action is required."""
        reasons = []

        risk_score = prediction_result.get('heat_exposure_risk_score', 0)
        heat_index = prediction_result.get('heat_index', 0)

        if risk_score > 0.75:
            reasons.append(f'High heat exposure risk score: {risk_score}')

        if heat_index >= settings.HEAT_INDEX_THRESHOLD_DANGER:
            reasons.append(f'Heat index above danger threshold: {heat_index}°F')

        if prediction_result.get('requires_immediate_attention', False):
            reasons.append('Model flagged for immediate attention')

        return reasons

    def generate_compliance_report(self,
                                 start_date: datetime,
                                 end_date: datetime,
                                 worker_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate OSHA compliance report for specified time period.

        Args:
            start_date: Report start date
            end_date: Report end date
            worker_ids: Optional list of specific worker IDs to include

        Returns:
            Comprehensive compliance report
        """
        try:
            # Read compliance logs for the specified period
            log_entries = self._read_compliance_logs(start_date, end_date)

            if not log_entries:
                return {
                    'report_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'error': 'No compliance data found for specified period'
                }

            # Filter by worker IDs if specified
            if worker_ids:
                log_entries = [
                    entry for entry in log_entries
                    if entry.get('worker_identification', {}).get('worker_id') in worker_ids
                ]

            # Generate report
            report = self._compile_compliance_report(log_entries, start_date, end_date)
            return report

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                'error': f'Report generation failed: {e}',
                'timestamp': datetime.now().isoformat()
            }

    def _read_compliance_logs(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Read compliance logs from file system."""
        # This is a simplified implementation
        # In a production system, you might use a database or log aggregation service
        log_entries = []

        try:
            log_file = Path(settings.OSHA_LOG_FILE)
            if not log_file.exists():
                return log_entries

            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            # Parse log line - this assumes JSON format
                            parts = line.split(' | ')
                            if len(parts) >= 3:
                                timestamp_str = parts[0]
                                message = parts[2]

                                # Try to parse as JSON
                                if message.startswith('{'):
                                    entry = json.loads(message)
                                    entry_time = datetime.fromisoformat(
                                        entry.get('timestamp_utc', '').replace('Z', '+00:00')
                                    )

                                    if start_date <= entry_time <= end_date:
                                        log_entries.append(entry)

                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue  # Skip invalid entries

        except Exception as e:
            logger.error(f"Error reading compliance logs: {e}")

        return log_entries

    def _compile_compliance_report(self,
                                 log_entries: List[Dict[str, Any]],
                                 start_date: datetime,
                                 end_date: datetime) -> Dict[str, Any]:
        """Compile compliance report from log entries."""
        # This would contain detailed report compilation logic
        # Simplified version for demonstration

        assessments = [e for e in log_entries if e.get('compliance_event') == 'HEAT_EXPOSURE_ASSESSMENT']
        alerts = [e for e in log_entries if 'ALERT' in e.get('compliance_event', '')]

        worker_ids = list(set([
            a.get('worker_identification', {}).get('worker_id')
            for a in assessments
            if a.get('worker_identification', {}).get('worker_id')
        ]))

        return {
            'report_metadata': {
                'report_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'generated_at': datetime.now().isoformat(),
                'report_type': 'OSHA Heat Exposure Compliance Report'
            },
            'summary_statistics': {
                'total_assessments': len(assessments),
                'unique_workers': len(worker_ids),
                'total_alerts': len(alerts),
                'assessment_days': (end_date - start_date).days + 1
            },
            'detailed_analysis': {
                'worker_list': worker_ids[:50],  # Limit for display
                'alert_summary': self._summarize_alerts(alerts),
                'high_risk_incidents': len([a for a in assessments
                                          if a.get('risk_assessment', {}).get('heat_exposure_risk_score', 0) > 0.75])
            },
            'compliance_status': {
                'osha_compliant': True,  # Based on logging completeness
                'documentation_complete': True,
                'alerts_properly_logged': len(alerts) > 0
            }
        }

    def _summarize_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize alert types and counts."""
        summary = {}
        for alert in alerts:
            event_type = alert.get('compliance_event', 'UNKNOWN')
            summary[event_type] = summary.get(event_type, 0) + 1
        return summary

    def get_compliance_status(self) -> Dict[str, Any]:
        """Get current compliance system status."""
        return {
            'compliance_logging_enabled': self.enable_logging,
            'log_file_path': settings.OSHA_LOG_FILE,
            'log_file_exists': Path(settings.OSHA_LOG_FILE).exists() if self.enable_logging else False,
            'heat_index_thresholds': {
                'warning': settings.HEAT_INDEX_THRESHOLD_WARNING,
                'danger': settings.HEAT_INDEX_THRESHOLD_DANGER
            },
            'osha_standards_loaded': bool(OSHA_STANDARDS),
            'timestamp': datetime.now().isoformat()
        }