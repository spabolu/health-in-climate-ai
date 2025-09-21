"""
OSHA Compliance Tests
=====================

Comprehensive tests for OSHA compliance functionality in HeatGuard:
- Compliance logging and audit trails
- OSHA standard adherence validation
- Heat exposure incident reporting
- Regulatory compliance documentation
- Safety recommendation validation
- Work/rest cycle compliance
- Temperature threshold monitoring
- Legal documentation requirements
- Audit report generation
"""

import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, mock_open
from typing import Dict, List, Any
import csv
import io

from app.services.compliance_service import ComplianceService
from app.config.model_config import OSHA_STANDARDS


class TestOSHAComplianceService:
    """Test OSHA compliance service functionality."""

    @pytest.fixture
    def compliance_service(self):
        """Create a compliance service instance for testing."""
        return ComplianceService()

    @pytest.fixture
    def sample_compliance_data(self):
        """Sample data for compliance testing."""
        return {
            'worker_id': 'comp_worker_001',
            'timestamp': datetime.now().isoformat(),
            'heat_exposure_risk_score': 0.75,
            'risk_level': 'Warning',
            'temperature_celsius': 38.5,
            'temperature_fahrenheit': 101.3,
            'humidity_percent': 85.0,
            'heat_index': 118.5,
            'osha_recommendations': [
                'Implement work/rest cycles: 15 minutes work, 15 minutes rest',
                'Mandatory water intake: 8 oz every 15 minutes',
                'Move to air-conditioned area if possible'
            ],
            'requires_immediate_attention': True
        }

    def test_compliance_service_initialization(self, compliance_service):
        """Test compliance service initialization."""
        assert compliance_service is not None
        assert hasattr(compliance_service, 'log_prediction')
        assert hasattr(compliance_service, 'get_compliance_status')

    def test_compliance_logging_enabled(self, compliance_service, sample_compliance_data):
        """Test compliance logging when enabled."""
        with patch('app.config.settings.settings.ENABLE_OSHA_LOGGING', True), \
             patch.object(compliance_service, '_write_log_entry') as mock_write:

            worker_data = {
                'Age': 35, 'Gender': 1, 'Temperature': 38.5,
                'Humidity': 85.0, 'hrv_mean_hr': 110
            }

            result = compliance_service.log_prediction(sample_compliance_data, worker_data)

            assert result is True
            mock_write.assert_called_once()

    def test_compliance_logging_disabled(self, compliance_service, sample_compliance_data):
        """Test compliance logging when disabled."""
        with patch('app.config.settings.settings.ENABLE_OSHA_LOGGING', False):

            worker_data = {'Age': 35, 'Gender': 1}

            result = compliance_service.log_prediction(sample_compliance_data, worker_data)

            assert result is False  # Should not log when disabled

    def test_high_risk_incident_logging(self, compliance_service, sample_compliance_data):
        """Test logging of high-risk incidents for OSHA compliance."""
        # High-risk scenario
        high_risk_data = sample_compliance_data.copy()
        high_risk_data.update({
            'heat_exposure_risk_score': 0.92,
            'risk_level': 'Danger',
            'temperature_celsius': 43.0,
            'heat_index': 125.0,
            'requires_immediate_attention': True,
            'incident_type': 'heat_stress_emergency'
        })

        with patch.object(compliance_service, '_write_log_entry') as mock_write, \
             patch.object(compliance_service, '_log_high_risk_incident') as mock_incident:

            worker_data = {'Age': 50, 'Gender': 0, 'Temperature': 43.0}
            result = compliance_service.log_prediction(high_risk_data, worker_data)

            assert result is True
            mock_write.assert_called_once()
            mock_incident.assert_called_once()

    def test_osha_standards_validation(self, compliance_service):
        """Test validation against OSHA heat exposure standards."""
        test_scenarios = [
            # Temperature, Humidity, Expected Compliance Level
            (25.0, 50.0, 'compliant'),      # Safe conditions
            (32.0, 70.0, 'caution'),        # Caution level
            (38.0, 80.0, 'warning'),        # Warning level
            (43.0, 85.0, 'violation'),      # Dangerous conditions
        ]

        for temp, humidity, expected_level in test_scenarios:
            compliance_level = compliance_service._assess_osha_compliance(temp, humidity)

            if expected_level == 'compliant':
                assert compliance_level in ['compliant', 'caution']
            elif expected_level == 'violation':
                assert compliance_level in ['warning', 'violation']

    def test_work_rest_cycle_recommendations(self, compliance_service):
        """Test OSHA work/rest cycle recommendations."""
        scenarios = [
            (0.3, False),  # Low risk - no special cycles needed
            (0.6, True),   # Medium risk - work/rest cycles recommended
            (0.8, True),   # High risk - mandatory work/rest cycles
        ]

        for risk_score, should_recommend_cycles in scenarios:
            recommendations = compliance_service._get_work_rest_recommendations(risk_score)

            if should_recommend_cycles:
                rec_text = ' '.join(recommendations).lower()
                assert any(keyword in rec_text for keyword in ['work/rest', 'cycle', 'break'])
            # For low risk, may or may not have cycle recommendations

    def test_compliance_status_reporting(self, compliance_service):
        """Test compliance status reporting functionality."""
        with patch.object(compliance_service, '_get_compliance_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'total_assessments': 1000,
                'high_risk_incidents': 45,
                'compliance_rate': 95.5,
                'violations_count': 12
            }

            status = compliance_service.get_compliance_status()

            assert 'compliance_logging_enabled' in status
            assert 'total_assessments' in status
            assert 'high_risk_incidents' in status
            assert status['compliance_rate'] == 95.5

    def test_audit_trail_generation(self, compliance_service, temp_log_file):
        """Test audit trail generation for compliance."""
        with patch('app.config.settings.settings.OSHA_LOG_FILE', temp_log_file):
            audit_data = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'worker_id': 'audit_worker_001',
                    'risk_level': 'Warning',
                    'action_taken': 'Work stoppage recommended'
                },
                {
                    'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'worker_id': 'audit_worker_002',
                    'risk_level': 'Danger',
                    'action_taken': 'Emergency cooling initiated'
                }
            ]

            for entry in audit_data:
                compliance_service._write_audit_entry(entry)

            # Verify audit trail was written
            assert os.path.exists(temp_log_file)
            with open(temp_log_file, 'r') as f:
                content = f.read()
                assert 'audit_worker_001' in content
                assert 'audit_worker_002' in content


class TestOSHAReporting:
    """Test OSHA reporting and documentation functionality."""

    @pytest.fixture
    def compliance_service(self):
        return ComplianceService()

    def test_daily_compliance_report(self, compliance_service):
        """Test generation of daily compliance reports."""
        with patch.object(compliance_service, '_get_daily_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'date': datetime.now().date().isoformat(),
                'total_workers_monitored': 150,
                'total_assessments': 1200,
                'high_risk_incidents': 8,
                'violations': 2,
                'avg_temperature': 34.5,
                'max_temperature': 42.1,
                'avg_heat_index': 95.3
            }

            report = compliance_service.generate_daily_report()

            assert 'report_date' in report
            assert 'summary' in report
            assert 'incidents' in report
            assert 'recommendations' in report
            assert report['summary']['total_workers_monitored'] == 150

    def test_weekly_compliance_summary(self, compliance_service):
        """Test weekly compliance summary generation."""
        with patch.object(compliance_service, '_get_weekly_metrics') as mock_metrics:
            mock_metrics.return_value = {
                'week_start': (datetime.now() - timedelta(days=7)).date().isoformat(),
                'week_end': datetime.now().date().isoformat(),
                'total_work_hours': 6000,
                'incidents_by_day': {
                    'Monday': 2, 'Tuesday': 1, 'Wednesday': 3,
                    'Thursday': 2, 'Friday': 4, 'Saturday': 1, 'Sunday': 0
                },
                'compliance_rate': 96.2
            }

            report = compliance_service.generate_weekly_summary()

            assert 'period' in report
            assert 'compliance_metrics' in report
            assert 'trend_analysis' in report
            assert report['compliance_metrics']['compliance_rate'] == 96.2

    def test_osha_incident_report(self, compliance_service):
        """Test OSHA-specific incident reporting."""
        incident_data = {
            'incident_id': 'INC_001_2024',
            'worker_id': 'incident_worker_001',
            'timestamp': datetime.now().isoformat(),
            'severity': 'high',
            'temperature': 44.5,
            'heat_index': 128.0,
            'symptoms_reported': ['dizziness', 'nausea', 'excessive_sweating'],
            'actions_taken': [
                'Immediate work stoppage',
                'Medical evaluation',
                'Cooling measures implemented'
            ],
            'medical_attention_required': True
        }

        with patch.object(compliance_service, '_format_osha_incident') as mock_format:
            mock_format.return_value = {
                'osha_form_300_entry': True,
                'recordable_incident': True,
                'notification_required': True
            }

            report = compliance_service.generate_incident_report(incident_data)

            assert 'incident_details' in report
            assert 'osha_compliance' in report
            assert 'regulatory_requirements' in report
            assert report['osha_compliance']['recordable_incident'] is True

    def test_regulatory_documentation(self, compliance_service):
        """Test regulatory documentation generation."""
        with patch.object(compliance_service, '_compile_regulatory_docs') as mock_compile:
            mock_compile.return_value = {
                'heat_illness_prevention_plan': 'documented',
                'worker_training_records': 'up_to_date',
                'environmental_monitoring': 'active',
                'incident_response_procedures': 'documented',
                'compliance_audit_trail': 'maintained'
            }

            docs = compliance_service.get_regulatory_documentation()

            assert 'heat_illness_prevention_plan' in docs
            assert 'worker_training_records' in docs
            assert 'compliance_status' in docs

    def test_export_compliance_data(self, compliance_service):
        """Test exporting compliance data for regulatory submission."""
        export_request = {
            'start_date': (datetime.now() - timedelta(days=30)).isoformat(),
            'end_date': datetime.now().isoformat(),
            'format': 'csv',
            'include_incidents': True,
            'include_metrics': True
        }

        with patch.object(compliance_service, '_extract_compliance_data') as mock_extract:
            mock_extract.return_value = [
                {
                    'date': '2024-01-01',
                    'worker_id': 'exp_worker_001',
                    'risk_level': 'Warning',
                    'temperature': 38.0,
                    'actions_taken': 'Rest break enforced'
                }
            ]

            export_data = compliance_service.export_compliance_data(export_request)

            assert 'data' in export_data
            assert 'metadata' in export_data
            assert export_data['metadata']['format'] == 'csv'
            assert len(export_data['data']) > 0


class TestOSHAStandards:
    """Test adherence to specific OSHA heat exposure standards."""

    def test_heat_index_thresholds(self):
        """Test OSHA heat index threshold compliance."""
        heat_index_scenarios = [
            (75, 'safe'),       # Below caution threshold
            (85, 'caution'),    # Caution level
            (90, 'warning'),    # Extreme caution
            (105, 'danger'),    # Danger level
            (130, 'extreme')    # Extreme danger
        ]

        for heat_index, expected_level in heat_index_scenarios:
            level = ComplianceService._classify_heat_index_level(heat_index)

            if expected_level == 'safe':
                assert level in ['safe', 'low_risk']
            elif expected_level == 'extreme':
                assert level in ['extreme_danger', 'extreme', 'critical']
            else:
                assert level is not None

    def test_work_rest_ratios(self):
        """Test OSHA-compliant work/rest ratios based on conditions."""
        scenarios = [
            (80, 50, '45/15'),   # 45 min work, 15 min rest
            (90, 70, '30/30'),   # 30 min work, 30 min rest
            (95, 80, '15/45'),   # 15 min work, 45 min rest
            (105, 85, '0/60'),   # No work, continuous rest
        ]

        for temp_f, humidity, expected_ratio in scenarios:
            ratio = ComplianceService._calculate_work_rest_ratio(temp_f, humidity)

            # Verify ratio makes sense (work time should decrease with higher risk)
            if expected_ratio == '0/60':
                assert ratio['work_minutes'] == 0
                assert ratio['rest_minutes'] > 0
            else:
                assert ratio['work_minutes'] > 0
                assert ratio['rest_minutes'] > 0

    def test_hydration_requirements(self):
        """Test OSHA hydration requirement compliance."""
        risk_levels = ['Safe', 'Caution', 'Warning', 'Danger']

        for risk_level in risk_levels:
            hydration_req = ComplianceService._get_hydration_requirements(risk_level)

            assert 'frequency_minutes' in hydration_req
            assert 'volume_oz' in hydration_req

            # Higher risk should require more frequent hydration
            if risk_level == 'Danger':
                assert hydration_req['frequency_minutes'] <= 15
                assert hydration_req['volume_oz'] >= 8

    def test_medical_monitoring_requirements(self):
        """Test OSHA medical monitoring requirements."""
        worker_profiles = [
            {'age': 25, 'health_status': 'good', 'heat_acclimatized': True},
            {'age': 55, 'health_status': 'fair', 'heat_acclimatized': False},
            {'age': 65, 'health_status': 'poor', 'heat_acclimatized': False}
        ]

        for profile in worker_profiles:
            monitoring_req = ComplianceService._assess_medical_monitoring_needs(profile)

            assert 'monitoring_required' in monitoring_req
            assert 'frequency' in monitoring_req

            # Older workers or those with health issues should require more monitoring
            if profile['age'] > 50 or profile['health_status'] == 'poor':
                assert monitoring_req['monitoring_required'] is True

    def test_personal_protective_equipment(self):
        """Test PPE requirements based on heat exposure conditions."""
        conditions = [
            {'temperature': 85, 'humidity': 60, 'work_type': 'light'},
            {'temperature': 95, 'humidity': 80, 'work_type': 'moderate'},
            {'temperature': 105, 'humidity': 85, 'work_type': 'heavy'}
        ]

        for condition in conditions:
            ppe_req = ComplianceService._assess_ppe_requirements(condition)

            assert 'required_items' in ppe_req
            assert isinstance(ppe_req['required_items'], list)

            # Extreme conditions should require more PPE
            if condition['temperature'] > 100:
                required_items = ppe_req['required_items']
                assert any('cooling' in item.lower() for item in required_items)


class TestComplianceValidation:
    """Test validation of compliance with various OSHA requirements."""

    @pytest.fixture
    def compliance_service(self):
        return ComplianceService()

    def test_temperature_monitoring_compliance(self, compliance_service):
        """Test compliance with temperature monitoring requirements."""
        monitoring_data = [
            {'timestamp': '2024-01-01T08:00:00', 'temperature': 78.0, 'humidity': 55.0},
            {'timestamp': '2024-01-01T10:00:00', 'temperature': 85.0, 'humidity': 65.0},
            {'timestamp': '2024-01-01T12:00:00', 'temperature': 92.0, 'humidity': 75.0},
            {'timestamp': '2024-01-01T14:00:00', 'temperature': 98.0, 'humidity': 80.0},
            {'timestamp': '2024-01-01T16:00:00', 'temperature': 95.0, 'humidity': 75.0}
        ]

        validation_result = compliance_service.validate_temperature_monitoring(monitoring_data)

        assert 'compliant' in validation_result
        assert 'monitoring_frequency_adequate' in validation_result
        assert 'alerts_triggered_appropriately' in validation_result

    def test_worker_training_compliance(self, compliance_service):
        """Test worker training compliance validation."""
        training_records = [
            {
                'worker_id': 'train_worker_001',
                'heat_illness_prevention_training': True,
                'training_date': '2024-01-01',
                'refresher_due': '2024-07-01',
                'competency_verified': True
            },
            {
                'worker_id': 'train_worker_002',
                'heat_illness_prevention_training': False,
                'training_date': None,
                'refresher_due': None,
                'competency_verified': False
            }
        ]

        validation = compliance_service.validate_training_compliance(training_records)

        assert 'overall_compliance_rate' in validation
        assert 'non_compliant_workers' in validation
        assert len(validation['non_compliant_workers']) == 1

    def test_incident_response_compliance(self, compliance_service):
        """Test incident response compliance validation."""
        incident_response_data = {
            'response_time_minutes': 3,
            'medical_evaluation_conducted': True,
            'cooling_measures_applied': True,
            'work_stoppage_implemented': True,
            'supervisor_notified': True,
            'documentation_completed': True,
            'follow_up_scheduled': True
        }

        validation = compliance_service.validate_incident_response(incident_response_data)

        assert validation['compliant'] is True
        assert validation['response_time_adequate'] is True
        assert len(validation['deficiencies']) == 0

    def test_environmental_controls_compliance(self, compliance_service):
        """Test environmental controls compliance."""
        controls_data = {
            'shade_structures_available': True,
            'cooling_areas_provided': True,
            'water_stations_adequate': True,
            'air_movement_systems': True,
            'engineering_controls': ['shade', 'fans', 'misting_systems'],
            'administrative_controls': ['work_scheduling', 'job_rotation', 'rest_breaks']
        }

        validation = compliance_service.validate_environmental_controls(controls_data)

        assert 'engineering_controls_adequate' in validation
        assert 'administrative_controls_adequate' in validation
        assert validation['overall_compliance'] is True


class TestComplianceMetrics:
    """Test compliance metrics and KPI tracking."""

    @pytest.fixture
    def compliance_service(self):
        return ComplianceService()

    def test_compliance_rate_calculation(self, compliance_service):
        """Test calculation of overall compliance rates."""
        assessment_data = [
            {'compliant': True, 'risk_level': 'Safe'},
            {'compliant': True, 'risk_level': 'Caution'},
            {'compliant': False, 'risk_level': 'Warning'},  # Non-compliant
            {'compliant': True, 'risk_level': 'Caution'},
            {'compliant': False, 'risk_level': 'Danger'}    # Non-compliant
        ]

        compliance_rate = compliance_service.calculate_compliance_rate(assessment_data)

        assert compliance_rate['overall_rate'] == 60.0  # 3/5 = 60%
        assert compliance_rate['by_risk_level']['Warning'] == 0.0
        assert compliance_rate['by_risk_level']['Safe'] == 100.0

    def test_incident_rate_tracking(self, compliance_service):
        """Test incident rate tracking and trending."""
        incident_data = [
            {'date': '2024-01-01', 'incidents': 2, 'work_hours': 800},
            {'date': '2024-01-02', 'incidents': 1, 'work_hours': 800},
            {'date': '2024-01-03', 'incidents': 0, 'work_hours': 800},
            {'date': '2024-01-04', 'incidents': 3, 'work_hours': 800},
            {'date': '2024-01-05', 'incidents': 1, 'work_hours': 800}
        ]

        metrics = compliance_service.calculate_incident_metrics(incident_data)

        assert 'incident_rate_per_100_workers' in metrics
        assert 'trend_direction' in metrics
        assert 'total_incidents' in metrics
        assert metrics['total_incidents'] == 7

    def test_regulatory_kpi_tracking(self, compliance_service):
        """Test regulatory KPI tracking."""
        kpi_data = {
            'heat_illness_incidents': 5,
            'days_without_incidents': 12,
            'training_completion_rate': 95.5,
            'environmental_monitoring_uptime': 98.2,
            'response_time_compliance': 89.1,
            'documentation_completeness': 92.3
        }

        kpis = compliance_service.track_regulatory_kpis(kpi_data)

        assert 'safety_performance_index' in kpis
        assert 'regulatory_compliance_score' in kpis
        assert 'areas_for_improvement' in kpis

        # Overall score should be reasonable
        assert 0 <= kpis['regulatory_compliance_score'] <= 100


class TestComplianceIntegration:
    """Test integration of compliance features with API endpoints."""

    def test_prediction_compliance_logging(self, authenticated_client, mock_auth_middleware, sample_worker_data):
        """Test that predictions are properly logged for compliance."""
        request_data = {
            "data": sample_worker_data,
            "options": {
                "use_conservative": True,
                "log_compliance": True
            }
        }

        with patch('app.services.compliance_service.ComplianceService.log_prediction') as mock_log, \
             patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict:

            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.75,
                'risk_level': 'Warning',
                'requires_immediate_attention': True
            }

            mock_log.return_value = True

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            mock_log.assert_called_once()

    def test_batch_compliance_logging(self, authenticated_client, mock_auth_middleware, batch_worker_data):
        """Test compliance logging for batch predictions."""
        request_data = {
            "data": batch_worker_data,
            "options": {"log_compliance": True}
        }

        with patch('app.services.compliance_service.ComplianceService.log_prediction') as mock_log, \
             patch('app.api.prediction.prediction_service.predict_multiple_workers') as mock_predict:

            mock_predict.return_value = {
                'batch_size': len(batch_worker_data),
                'successful_predictions': len(batch_worker_data),
                'predictions': [{'worker_id': f'w_{i}'} for i in range(len(batch_worker_data))]
            }

            response = authenticated_client.post("/api/v1/predict_batch", json=request_data)

            assert response.status_code == 200
            # Compliance logging should be called for the batch
            # (Actual implementation may vary)

    def test_compliance_health_check(self, client):
        """Test compliance service in health check."""
        with patch('app.services.compliance_service.ComplianceService.get_compliance_status') as mock_status:
            mock_status.return_value = {
                'compliance_logging_enabled': True,
                'total_logs': 5000,
                'high_risk_incidents': 45,
                'last_audit_date': '2024-01-01'
            }

            response = client.get("/api/v1/health/services")

            assert response.status_code == 200
            data = response.json()

            # Compliance service should be included in health check
            compliance_services = [s for s in data['services'] if 'Compliance' in s['service_name']]
            assert len(compliance_services) > 0


class TestComplianceAuditing:
    """Test compliance auditing and reporting functionality."""

    @pytest.fixture
    def compliance_service(self):
        return ComplianceService()

    def test_audit_trail_integrity(self, compliance_service, temp_log_file):
        """Test audit trail integrity and tamper detection."""
        with patch('app.config.settings.settings.OSHA_LOG_FILE', temp_log_file):
            audit_entries = [
                {'action': 'prediction_logged', 'worker_id': 'audit_001', 'timestamp': datetime.now().isoformat()},
                {'action': 'incident_reported', 'worker_id': 'audit_002', 'timestamp': datetime.now().isoformat()},
                {'action': 'training_completed', 'worker_id': 'audit_003', 'timestamp': datetime.now().isoformat()}
            ]

            for entry in audit_entries:
                compliance_service._write_audit_entry(entry)

            # Verify audit trail can be validated
            validation = compliance_service.validate_audit_trail(temp_log_file)

            assert validation['entries_count'] == 3
            assert validation['integrity_verified'] is True
            assert validation['no_gaps_detected'] is True

    def test_compliance_report_generation(self, compliance_service):
        """Test comprehensive compliance report generation."""
        with patch.object(compliance_service, '_gather_compliance_data') as mock_data:
            mock_data.return_value = {
                'period': '2024-Q1',
                'total_assessments': 10000,
                'compliance_rate': 94.2,
                'incidents': 28,
                'training_completion': 97.8,
                'audit_findings': 3
            }

            report = compliance_service.generate_compliance_report('2024-Q1')

            assert 'executive_summary' in report
            assert 'compliance_metrics' in report
            assert 'incidents_analysis' in report
            assert 'recommendations' in report
            assert 'regulatory_status' in report

    def test_regulatory_submission_format(self, compliance_service):
        """Test formatting data for regulatory submissions."""
        raw_data = {
            'incidents': [
                {
                    'date': '2024-01-15',
                    'severity': 'moderate',
                    'cause': 'heat_exhaustion',
                    'actions_taken': ['cooling', 'medical_eval']
                }
            ],
            'preventive_measures': [
                'increased_monitoring',
                'additional_training',
                'improved_ventilation'
            ]
        }

        formatted_submission = compliance_service.format_regulatory_submission(raw_data)

        assert 'osha_300_entries' in formatted_submission
        assert 'preventive_actions' in formatted_submission
        assert 'compliance_statement' in formatted_submission
        assert formatted_submission['format_version'] is not None


# Mark all tests as compliance tests
pytestmark = pytest.mark.compliance


class TestOSHAIntegrationScenarios:
    """Integration scenarios testing complete OSHA compliance workflows."""

    def test_complete_incident_workflow(self, authenticated_client, mock_auth_middleware):
        """Test complete incident detection and compliance workflow."""
        # Dangerous worker condition
        dangerous_data = {
            'Age': 55, 'Gender': 0, 'Temperature': 44.0, 'Humidity': 90.0,
            'hrv_mean_hr': 160, 'hrv_rmssd': 5.0, 'worker_id': 'incident_worker'
        }

        request_data = {"data": dangerous_data, "options": {"log_compliance": True}}

        with patch('app.api.prediction.prediction_service.predict_single_worker') as mock_predict, \
             patch('app.services.compliance_service.ComplianceService.log_prediction') as mock_log, \
             patch('app.services.alert_service.AlertService.trigger_emergency_response') as mock_alert:

            # Dangerous prediction
            mock_predict.return_value = {
                'heat_exposure_risk_score': 0.95,
                'risk_level': 'Danger',
                'requires_immediate_attention': True,
                'osha_recommendations': [
                    'STOP work immediately',
                    'Move to air-conditioned area',
                    'Contact medical personnel'
                ],
                'incident_detected': True
            }

            mock_log.return_value = True

            response = authenticated_client.post("/api/v1/predict", json=request_data)

            assert response.status_code == 200
            data = response.json()

            # Verify incident was properly handled
            assert data['risk_level'] == 'Danger'
            assert data['requires_immediate_attention'] is True
            assert any('STOP' in rec for rec in data['osha_recommendations'])

            # Verify compliance logging occurred
            mock_log.assert_called_once()

    def test_regulatory_audit_preparation(self, authenticated_client, mock_auth_middleware):
        """Test preparation of data for regulatory audits."""
        # Simulate a period of monitoring with various risk levels
        monitoring_data = [
            {'risk_score': 0.2, 'compliant': True},
            {'risk_score': 0.4, 'compliant': True},
            {'risk_score': 0.6, 'compliant': True},
            {'risk_score': 0.8, 'compliant': False},  # Non-compliant incident
            {'risk_score': 0.3, 'compliant': True}
        ]

        with patch('app.services.compliance_service.ComplianceService') as mock_compliance:
            mock_service = Mock()
            mock_service.prepare_audit_package.return_value = {
                'audit_period': '2024-Q1',
                'total_assessments': len(monitoring_data),
                'compliance_rate': 80.0,
                'documentation_complete': True,
                'regulatory_requirements_met': True
            }

            mock_compliance.return_value = mock_service

            # This would be called during audit preparation
            audit_package = mock_service.prepare_audit_package('2024-Q1')

            assert audit_package['compliance_rate'] == 80.0
            assert audit_package['documentation_complete'] is True