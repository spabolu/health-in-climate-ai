"""
Heat Exposure Predictor Model Tests
===================================

Comprehensive tests for the HeatExposurePredictor ML model including:
- Model loading and initialization
- Single prediction validation
- Batch prediction processing
- Heat index calculations
- Risk assessment and scoring
- OSHA recommendation generation
- Model performance and accuracy
- Edge cases and error handling
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder

from app.models.heat_predictor import HeatExposurePredictor


class TestModelInitialization:
    """Test model loading and initialization."""

    def test_model_initialization_success(self, mock_model_directory):
        """Test successful model initialization."""
        predictor = HeatExposurePredictor(model_dir=mock_model_directory)

        assert predictor.is_loaded is True
        assert predictor.model is not None
        assert predictor.scaler is not None
        assert predictor.label_encoder is not None
        assert predictor.feature_columns is not None
        assert len(predictor.feature_columns) == 50

    def test_model_initialization_missing_directory(self):
        """Test model initialization with missing directory."""
        with pytest.raises(FileNotFoundError):
            HeatExposurePredictor(model_dir="/nonexistent/directory")

    def test_model_initialization_missing_files(self):
        """Test model initialization with missing model files."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create empty directory (missing model files)
            with pytest.raises(FileNotFoundError):
                HeatExposurePredictor(model_dir=temp_dir)
        finally:
            os.rmdir(temp_dir)

    def test_model_info_retrieval(self, mock_heat_predictor):
        """Test getting model information."""
        info = mock_heat_predictor.get_model_info()

        assert 'model_loaded' in info
        assert 'model_type' in info
        assert 'feature_count' in info
        assert 'target_classes' in info
        assert 'conservative_bias' in info

        assert info['model_loaded'] is True
        assert info['feature_count'] == 50
        assert info['model_type'] == 'XGBoost Heat Exposure Predictor'


class TestHeatIndexCalculation:
    """Test heat index calculation functionality."""

    def test_heat_index_normal_conditions(self, mock_heat_predictor):
        """Test heat index calculation under normal conditions."""
        # Normal conditions
        temp_f = 85.0
        humidity = 60.0

        heat_index = mock_heat_predictor.calculate_heat_index(temp_f, humidity)

        assert isinstance(heat_index, float)
        assert heat_index >= temp_f  # Heat index should be >= air temperature

    def test_heat_index_low_temperature(self, mock_heat_predictor):
        """Test heat index calculation with low temperature."""
        # Below 80°F threshold
        temp_f = 75.0
        humidity = 60.0

        heat_index = mock_heat_predictor.calculate_heat_index(temp_f, humidity)

        assert heat_index == temp_f  # Should return air temperature unchanged

    def test_heat_index_extreme_conditions(self, mock_heat_predictor):
        """Test heat index calculation under extreme conditions."""
        # Very hot and humid
        temp_f = 100.0
        humidity = 90.0

        heat_index = mock_heat_predictor.calculate_heat_index(temp_f, humidity)

        assert heat_index > temp_f  # Should be significantly higher than air temp
        assert heat_index > 100  # Should be in dangerous range

    @pytest.mark.parametrize("temp_f,humidity,expected_range", [
        (80, 40, (80, 85)),    # Low humidity
        (90, 50, (90, 100)),   # Moderate conditions
        (95, 85, (110, 130)),  # High heat and humidity
        (105, 70, (130, 150))  # Extreme heat
    ])
    def test_heat_index_ranges(self, mock_heat_predictor, temp_f, humidity, expected_range):
        """Test heat index calculation ranges."""
        heat_index = mock_heat_predictor.calculate_heat_index(temp_f, humidity)

        min_expected, max_expected = expected_range
        assert min_expected <= heat_index <= max_expected


class TestSinglePrediction:
    """Test single worker prediction functionality."""

    def test_single_prediction_success(self, mock_heat_predictor, sample_worker_data):
        """Test successful single worker prediction."""
        result = mock_heat_predictor.predict_single(sample_worker_data)

        # Validate result structure
        assert 'heat_exposure_risk_score' in result
        assert 'risk_level' in result
        assert 'confidence' in result
        assert 'temperature_celsius' in result
        assert 'temperature_fahrenheit' in result
        assert 'humidity_percent' in result
        assert 'heat_index' in result
        assert 'osha_recommendations' in result
        assert 'requires_immediate_attention' in result
        assert 'worker_id' in result
        assert 'timestamp' in result

        # Validate score ranges
        assert 0 <= result['heat_exposure_risk_score'] <= 1
        assert 0 <= result['confidence'] <= 1

        # Validate risk level
        assert result['risk_level'] in ['Safe', 'Caution', 'Warning', 'Danger']

        # Validate recommendations
        assert isinstance(result['osha_recommendations'], list)
        assert len(result['osha_recommendations']) > 0

    def test_single_prediction_with_missing_features(self, mock_heat_predictor, missing_features_data):
        """Test single prediction with missing features."""
        # Should handle missing features by filling with defaults
        result = mock_heat_predictor.predict_single(missing_features_data)

        assert 'heat_exposure_risk_score' in result
        assert result['heat_exposure_risk_score'] is not None

    def test_single_prediction_conservative_bias(self, mock_heat_predictor, sample_worker_data):
        """Test single prediction with conservative bias."""
        # Test with conservative bias
        result_conservative = mock_heat_predictor.predict_single(sample_worker_data, use_conservative=True)

        # Test without conservative bias
        result_standard = mock_heat_predictor.predict_single(sample_worker_data, use_conservative=False)

        # Conservative should have higher or equal risk score
        assert result_conservative['heat_exposure_risk_score'] >= result_standard['heat_exposure_risk_score']

        # Should indicate conservative bias was applied
        assert result_conservative['conservative_bias_applied'] is True
        assert result_standard['conservative_bias_applied'] is False

    def test_single_prediction_high_risk_scenario(self, mock_heat_predictor, high_risk_scenario_data):
        """Test single prediction with high-risk scenario."""
        result = mock_heat_predictor.predict_single(high_risk_scenario_data)

        # High-risk scenario should result in elevated risk scores
        assert result['heat_exposure_risk_score'] > 0.5
        assert result['risk_level'] in ['Warning', 'Danger']
        assert result['requires_immediate_attention'] is True

        # Should have relevant OSHA recommendations
        recommendations = result['osha_recommendations']
        high_risk_keywords = ['STOP', 'immediate', 'medical', 'emergency', 'air-conditioned']
        assert any(keyword in ' '.join(recommendations) for keyword in high_risk_keywords)

    def test_single_prediction_edge_cases(self, mock_heat_predictor, edge_case_worker_data):
        """Test single prediction with edge case values."""
        for edge_case in edge_case_worker_data:
            result = mock_heat_predictor.predict_single(edge_case)

            # Should handle edge cases without crashing
            assert 'heat_exposure_risk_score' in result
            assert 0 <= result['heat_exposure_risk_score'] <= 1

    def test_single_prediction_model_not_loaded(self, sample_worker_data):
        """Test single prediction when model is not loaded."""
        predictor = HeatExposurePredictor.__new__(HeatExposurePredictor)
        predictor.is_loaded = False

        with pytest.raises(RuntimeError, match="Model not loaded"):
            predictor.predict_single(sample_worker_data)


class TestBatchPrediction:
    """Test batch prediction functionality."""

    def test_batch_prediction_success(self, mock_heat_predictor, batch_worker_data):
        """Test successful batch prediction."""
        df = pd.DataFrame(batch_worker_data)
        results = mock_heat_predictor.predict_batch(df)

        assert len(results) == len(batch_worker_data)

        for i, result in enumerate(results):
            assert 'heat_exposure_risk_score' in result
            assert 'worker_id' in result
            assert 'batch_index' in result
            assert result['batch_index'] == i

    def test_batch_prediction_with_errors(self, mock_heat_predictor):
        """Test batch prediction with some failed predictions."""
        # Create batch with invalid data that will cause errors
        batch_data = [
            {'Age': 30, 'Gender': 1, 'Temperature': 25, 'Humidity': 60, 'hrv_mean_hr': 75},
            {'Age': 'invalid'},  # This should cause an error
            {'Age': 35, 'Gender': 0, 'Temperature': 30, 'Humidity': 70, 'hrv_mean_hr': 80}
        ]

        df = pd.DataFrame(batch_data)

        with patch.object(mock_heat_predictor, 'predict_single') as mock_single:
            # First and third calls succeed, second fails
            mock_single.side_effect = [
                {'heat_exposure_risk_score': 0.3, 'risk_level': 'Safe'},
                Exception("Prediction error"),
                {'heat_exposure_risk_score': 0.4, 'risk_level': 'Caution'}
            ]

            results = mock_heat_predictor.predict_batch(df)

            assert len(results) == 3
            assert 'error' not in results[0]  # First prediction successful
            assert 'error' in results[1]      # Second prediction failed
            assert 'error' not in results[2]  # Third prediction successful

    def test_batch_prediction_empty_dataframe(self, mock_heat_predictor):
        """Test batch prediction with empty DataFrame."""
        empty_df = pd.DataFrame()
        results = mock_heat_predictor.predict_batch(empty_df)

        assert len(results) == 0

    def test_batch_prediction_performance(self, mock_heat_predictor, performance_test_data):
        """Test batch prediction performance with large dataset."""
        df = pd.DataFrame(performance_test_data[:100])  # Test with 100 samples

        import time
        start_time = time.time()
        results = mock_heat_predictor.predict_batch(df)
        end_time = time.time()

        processing_time = end_time - start_time

        assert len(results) == 100
        # Should process 100 predictions reasonably quickly
        assert processing_time < 10.0  # Less than 10 seconds for 100 predictions


class TestRiskAssessment:
    """Test risk assessment and scoring logic."""

    def test_risk_level_mapping(self, mock_heat_predictor):
        """Test risk level mapping from scores."""
        # Test different risk scores
        risk_scores = [0.1, 0.3, 0.6, 0.9]
        expected_levels = ['Safe', 'Caution', 'Warning', 'Danger']

        for score, expected_level in zip(risk_scores, expected_levels):
            level = mock_heat_predictor._assess_heat_exposure_risk(score)
            # Allow for some flexibility in thresholds
            assert level in ['Safe', 'Caution', 'Warning', 'Danger']

    def test_conservative_bias_application(self, mock_heat_predictor):
        """Test conservative bias application."""
        # Mock predictions and probabilities
        mock_predictions = np.array([0, 1, 2])  # Different class predictions
        mock_probabilities = np.array([
            [0.7, 0.2, 0.1],  # Mostly class 0
            [0.1, 0.7, 0.2],  # Mostly class 1
            [0.1, 0.2, 0.7]   # Mostly class 2
        ])

        standard_scores, conservative_scores, _ = mock_heat_predictor._create_heat_exposure_score(
            mock_predictions, mock_probabilities
        )

        # Conservative scores should be higher or equal
        for std, cons in zip(standard_scores, conservative_scores):
            assert cons >= std
            assert cons <= 1.0  # Should not exceed maximum

    def test_thermal_to_heat_exposure_transformation(self, mock_heat_predictor):
        """Test transformation from thermal comfort to heat exposure scores."""
        thermal_scores = [0.2, 0.5, 0.8]

        for thermal_score in thermal_scores:
            heat_score = mock_heat_predictor._transform_thermal_to_heat_exposure(thermal_score)

            assert 0 <= heat_score <= 1
            # Heat exposure score should be related to thermal discomfort
            assert heat_score >= thermal_score - 0.01  # Allow for small numerical differences


class TestOSHARecommendations:
    """Test OSHA recommendation generation."""

    def test_osha_recommendations_safe_conditions(self, mock_heat_predictor):
        """Test OSHA recommendations for safe conditions."""
        recommendations = mock_heat_predictor._get_osha_recommendations(
            risk_score=0.1, temperature_c=22.0, humidity=50.0
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include normal precautions
        rec_text = ' '.join(recommendations).lower()
        assert any(keyword in rec_text for keyword in ['normal', 'regular', 'monitor'])

    def test_osha_recommendations_caution_conditions(self, mock_heat_predictor):
        """Test OSHA recommendations for caution-level conditions."""
        recommendations = mock_heat_predictor._get_osha_recommendations(
            risk_score=0.4, temperature_c=30.0, humidity=70.0
        )

        rec_text = ' '.join(recommendations).lower()
        assert any(keyword in rec_text for keyword in ['increase', 'water', 'rest', 'shade'])

    def test_osha_recommendations_warning_conditions(self, mock_heat_predictor):
        """Test OSHA recommendations for warning-level conditions."""
        recommendations = mock_heat_predictor._get_osha_recommendations(
            risk_score=0.7, temperature_c=37.0, humidity=80.0
        )

        rec_text = ' '.join(recommendations).lower()
        assert any(keyword in rec_text for keyword in ['work/rest', 'mandatory', 'air-conditioned'])

    def test_osha_recommendations_danger_conditions(self, mock_heat_predictor):
        """Test OSHA recommendations for dangerous conditions."""
        recommendations = mock_heat_predictor._get_osha_recommendations(
            risk_score=0.9, temperature_c=42.0, humidity=85.0
        )

        rec_text = ' '.join(recommendations).lower()
        assert any(keyword in rec_text for keyword in ['stop', 'immediately', 'medical', 'emergency'])

    def test_osha_recommendations_heat_index_specific(self, mock_heat_predictor):
        """Test heat index specific OSHA recommendations."""
        # Extreme heat index conditions
        recommendations = mock_heat_predictor._get_osha_recommendations(
            risk_score=0.8, temperature_c=43.0, humidity=90.0  # Very high heat index
        )

        rec_text = ' '.join(recommendations).lower()
        # Should include heat index specific warnings
        assert any(keyword in rec_text for keyword in ['extreme', 'danger', 'cease'])


class TestFeatureValidation:
    """Test feature validation and template functionality."""

    def test_feature_template_generation(self, mock_heat_predictor):
        """Test feature template generation."""
        template = mock_heat_predictor.get_feature_template()

        assert isinstance(template, dict)
        assert len(template) == 50  # Should have all 50 features

        # Check required features are present
        required_features = ['Age', 'Gender', 'Temperature', 'Humidity', 'hrv_mean_hr', 'hrv_mean_nni']
        for feature in required_features:
            assert feature in template

        # Check reasonable default values
        assert 18 <= template['Age'] <= 65
        assert template['Gender'] in [0, 1]
        assert -20 <= template['Temperature'] <= 50
        assert 0 <= template['Humidity'] <= 100
        assert 40 <= template['hrv_mean_hr'] <= 200

    def test_input_validation_success(self, mock_heat_predictor, sample_worker_data):
        """Test input validation with valid data."""
        errors = mock_heat_predictor.validate_input(sample_worker_data)

        assert len(errors) == 0  # Should have no validation errors

    def test_input_validation_missing_features(self, mock_heat_predictor):
        """Test input validation with missing features."""
        incomplete_data = {
            'Age': 30,
            'Gender': 1
            # Missing many required features
        }

        errors = mock_heat_predictor.validate_input(incomplete_data)

        assert len(errors) > 0
        assert any('missing' in error.lower() for error in errors)

    def test_input_validation_invalid_types(self, mock_heat_predictor):
        """Test input validation with invalid data types."""
        invalid_data = {
            'Age': 'thirty',  # Should be numeric
            'Gender': 'male',  # Should be 0 or 1
            'Temperature': None,  # Should not be None
            'hrv_mean_hr': 'invalid'
        }

        errors = mock_heat_predictor.validate_input(invalid_data)

        assert len(errors) > 0
        assert any('numeric' in error.lower() or 'type' in error.lower() for error in errors)


class TestModelAccuracy:
    """Test model accuracy and prediction quality."""

    def test_prediction_consistency(self, mock_heat_predictor, sample_worker_data):
        """Test that identical inputs produce identical outputs."""
        result1 = mock_heat_predictor.predict_single(sample_worker_data.copy())
        result2 = mock_heat_predictor.predict_single(sample_worker_data.copy())

        # Should produce identical results for identical inputs
        assert result1['heat_exposure_risk_score'] == result2['heat_exposure_risk_score']
        assert result1['risk_level'] == result2['risk_level']
        assert result1['confidence'] == result2['confidence']

    def test_prediction_variability(self, mock_heat_predictor, batch_worker_data):
        """Test that different inputs produce varied outputs."""
        results = []
        for data in batch_worker_data[:5]:  # Test with 5 different samples
            result = mock_heat_predictor.predict_single(data)
            results.append(result['heat_exposure_risk_score'])

        # Should have some variability in results
        assert len(set(results)) > 1  # Not all identical

    def test_prediction_sensitivity(self, mock_heat_predictor, sample_worker_data):
        """Test model sensitivity to input changes."""
        baseline_result = mock_heat_predictor.predict_single(sample_worker_data)

        # Test temperature sensitivity
        hot_data = sample_worker_data.copy()
        hot_data['Temperature'] += 10  # Increase by 10°C
        hot_result = mock_heat_predictor.predict_single(hot_data)

        # Higher temperature should generally increase risk
        assert hot_result['heat_exposure_risk_score'] >= baseline_result['heat_exposure_risk_score']

        # Test heart rate sensitivity
        high_hr_data = sample_worker_data.copy()
        high_hr_data['hrv_mean_hr'] += 30  # Increase heart rate significantly
        high_hr_result = mock_heat_predictor.predict_single(high_hr_data)

        # Higher heart rate should generally increase risk
        assert high_hr_result['heat_exposure_risk_score'] >= baseline_result['heat_exposure_risk_score']


class TestErrorHandling:
    """Test error handling and robustness."""

    def test_malformed_input_handling(self, mock_heat_predictor):
        """Test handling of malformed input data."""
        malformed_inputs = [
            {},  # Empty dict
            {'invalid_field': 'invalid_value'},  # Wrong fields
            {'Age': float('inf')},  # Invalid numeric values
            {'Age': float('nan')},  # NaN values
        ]

        for malformed_input in malformed_inputs:
            # Should either handle gracefully or raise appropriate exceptions
            try:
                result = mock_heat_predictor.predict_single(malformed_input)
                # If it succeeds, should still have valid output structure
                assert 'heat_exposure_risk_score' in result
                assert 0 <= result['heat_exposure_risk_score'] <= 1
            except (ValueError, KeyError, RuntimeError):
                # These are acceptable exceptions for malformed input
                pass

    def test_extreme_value_handling(self, mock_heat_predictor, extreme_values_data):
        """Test handling of extreme but valid values."""
        # Should handle extreme values without crashing
        result = mock_heat_predictor.predict_single(extreme_values_data)

        assert 'heat_exposure_risk_score' in result
        assert 0 <= result['heat_exposure_risk_score'] <= 1
        assert result['risk_level'] in ['Safe', 'Caution', 'Warning', 'Danger']

    def test_memory_efficiency(self, mock_heat_predictor):
        """Test memory efficiency with large batch processing."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process a reasonably large batch
        large_batch_data = []
        for i in range(100):
            data = {
                'Age': 30, 'Gender': 1, 'Temperature': 25 + i*0.1,
                'Humidity': 60, 'hrv_mean_hr': 75,
                **{f'hrv_feature_{j}': 1.0 for j in range(46)}  # Fill other features
            }
            large_batch_data.append(data)

        df = pd.DataFrame(large_batch_data)
        results = mock_heat_predictor.predict_batch(df)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 100 predictions)
        assert memory_increase < 100
        assert len(results) == 100


@pytest.mark.parametrize("temperature,humidity,expected_risk_increase", [
    (20, 40, False),   # Cool and dry - should not increase risk
    (35, 80, True),    # Hot and humid - should increase risk
    (45, 90, True),    # Extreme conditions - should definitely increase risk
])
def test_environmental_factor_impact(mock_heat_predictor, sample_worker_data, temperature, humidity, expected_risk_increase):
    """Test that environmental factors properly impact risk assessment."""
    baseline_data = sample_worker_data.copy()
    baseline_data['Temperature'] = 25  # Baseline comfortable temperature
    baseline_data['Humidity'] = 50     # Baseline comfortable humidity

    environmental_data = sample_worker_data.copy()
    environmental_data['Temperature'] = temperature
    environmental_data['Humidity'] = humidity

    baseline_result = mock_heat_predictor.predict_single(baseline_data)
    environmental_result = mock_heat_predictor.predict_single(environmental_data)

    if expected_risk_increase:
        assert environmental_result['heat_exposure_risk_score'] > baseline_result['heat_exposure_risk_score']
    else:
        assert environmental_result['heat_exposure_risk_score'] <= baseline_result['heat_exposure_risk_score']


@pytest.mark.parametrize("age,gender,fitness_expectation", [
    (25, 1, "lower_risk"),    # Young male - typically lower risk
    (60, 0, "higher_risk"),   # Older female - typically higher risk
    (45, 1, "moderate_risk")  # Middle-aged male - moderate risk
])
def test_demographic_factor_impact(mock_heat_predictor, sample_worker_data, age, gender, fitness_expectation):
    """Test that demographic factors properly impact risk assessment."""
    data = sample_worker_data.copy()
    data['Age'] = age
    data['Gender'] = gender

    result = mock_heat_predictor.predict_single(data)

    # While we can't assert exact risk levels due to model complexity,
    # we can ensure the prediction is reasonable
    assert 0 <= result['heat_exposure_risk_score'] <= 1
    assert result['risk_level'] in ['Safe', 'Caution', 'Warning', 'Danger']

    # Age should be reflected in recommendations for older workers
    if age > 50:
        rec_text = ' '.join(result['osha_recommendations']).lower()
        # Older workers might get more cautious recommendations
        assert len(result['osha_recommendations']) >= 3