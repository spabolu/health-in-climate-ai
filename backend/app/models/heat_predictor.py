"""
Heat Exposure Predictor
======================

Core machine learning model for predicting heat exposure risk from wearable device data.
Transforms thermal comfort predictions into heat exposure risk assessments for worker safety.
"""

import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import logging

from ..config.model_config import MODEL_CONFIG, RISK_ASSESSMENT_MAPPING, HEAT_INDEX_CONFIG, OSHA_STANDARDS
from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HeatExposurePredictor:
    """
    A production-grade class for predicting heat exposure risk from wearable device data.

    This class transforms thermal comfort predictions into heat exposure risk assessments
    following OSHA guidelines for workplace safety.
    """

    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialize the heat exposure predictor.

        Args:
            model_dir: Directory containing the trained model files
        """
        self.model_dir = model_dir or settings.MODEL_DIR
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        self.conservative_bias = MODEL_CONFIG.conservative_bias
        self.is_loaded = False

        self._load_model()

    def _load_model(self) -> None:
        """Load all model components from saved files."""
        try:
            logger.info(f"Loading heat exposure model from {self.model_dir}")

            # Load model components
            self.model = joblib.load(os.path.join(self.model_dir, "xgboost_model.joblib"))
            self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.joblib"))
            self.label_encoder = joblib.load(os.path.join(self.model_dir, "label_encoder.joblib"))
            self.feature_columns = joblib.load(os.path.join(self.model_dir, "feature_columns.joblib"))

            self.is_loaded = True

            logger.info("Heat exposure model loaded successfully")
            logger.info(f"Model directory: {self.model_dir}")
            logger.info(f"Target classes: {list(self.label_encoder.classes_)}")
            logger.info(f"Features: {len(self.feature_columns)} wearable device metrics")

        except FileNotFoundError as e:
            logger.error(f"Error loading model: {e}")
            logger.error(f"Ensure model directory '{self.model_dir}' exists with all required files")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading model: {e}")
            raise

    def calculate_heat_index(self, temperature_f: float, humidity: float) -> float:
        """
        Calculate heat index using NOAA formula.

        Args:
            temperature_f: Temperature in Fahrenheit
            humidity: Relative humidity as percentage (0-100)

        Returns:
            Heat index in Fahrenheit
        """
        if temperature_f < 80:
            return temperature_f

        # NOAA Heat Index Formula coefficients
        c = HEAT_INDEX_CONFIG['coefficients']

        hi = (c['c1'] +
              c['c2'] * temperature_f +
              c['c3'] * humidity +
              c['c4'] * temperature_f * humidity +
              c['c5'] * temperature_f**2 +
              c['c6'] * humidity**2 +
              c['c7'] * temperature_f**2 * humidity +
              c['c8'] * temperature_f * humidity**2 +
              c['c9'] * temperature_f**2 * humidity**2)

        # Apply adjustments for extreme conditions
        adj = HEAT_INDEX_CONFIG['adjustments']
        if humidity < adj['low_rh_threshold'] and adj['temp_threshold_low'] <= temperature_f <= adj['temp_threshold_high']:
            hi -= ((13 - humidity) / 4) * np.sqrt((17 - abs(temperature_f - 95)) / 17)
        elif humidity > adj['high_rh_threshold'] and adj['temp_threshold_low'] <= temperature_f <= adj['temp_threshold_high']:
            hi += ((humidity - 85) / 10) * ((87 - temperature_f) / 5)

        return hi

    def _transform_thermal_to_heat_exposure(self, thermal_comfort_score: float) -> float:
        """
        Transform thermal comfort score to heat exposure risk score.

        Args:
            thermal_comfort_score: Original thermal comfort score (0-1)

        Returns:
            Heat exposure risk score (0=safe, 1=dangerous)
        """
        # Apply transformation: thermal comfort discomfort becomes heat exposure risk
        # Higher discomfort = higher heat exposure risk
        heat_exposure_risk = thermal_comfort_score

        # Apply additional bias for safety margin
        heat_exposure_risk = min(1.0, heat_exposure_risk + self.conservative_bias)

        return heat_exposure_risk

    def _create_heat_exposure_score(self, predictions: np.ndarray, probabilities: np.ndarray) -> Tuple[List[float], List[float], Dict[str, float]]:
        """
        Convert thermal comfort predictions to heat exposure risk scores.

        Args:
            predictions: Array of predicted classes
            probabilities: Array of class probabilities

        Returns:
            Tuple of (standard_scores, conservative_scores, class_mapping)
        """
        # Get class names from label encoder
        class_names = self.label_encoder.classes_

        # Map thermal comfort classes to heat exposure risk scores
        class_to_risk_score = {}
        mapping = RISK_ASSESSMENT_MAPPING['thermal_comfort_to_heat_exposure']

        for class_name in class_names:
            class_name_lower = class_name.lower()
            if 'neutral' in class_name_lower:
                class_to_risk_score[class_name] = mapping['neutral']
            elif 'slightly' in class_name_lower and 'warm' in class_name_lower:
                class_to_risk_score[class_name] = mapping['slightly_warm']
            elif 'warm' in class_name_lower and 'slightly' not in class_name_lower:
                class_to_risk_score[class_name] = mapping['warm']
            elif 'hot' in class_name_lower:
                class_to_risk_score[class_name] = mapping['hot']
            else:
                # Default mapping based on class index
                class_idx = list(class_names).index(class_name)
                class_to_risk_score[class_name] = class_idx / (len(class_names) - 1)

        # Calculate weighted risk scores
        standard_scores = []
        for prob_dist in probabilities:
            weighted_score = sum(prob * class_to_risk_score[class_names[j]]
                               for j, prob in enumerate(prob_dist))
            standard_scores.append(weighted_score)

        # Apply conservative bias for safety
        conservative_scores = [
            min(1.0, score + self.conservative_bias)
            for score in standard_scores
        ]

        return standard_scores, conservative_scores, class_to_risk_score

    def _assess_heat_exposure_risk(self, risk_score: float) -> str:
        """
        Assess heat exposure risk level based on score.

        Args:
            risk_score: Heat exposure risk score (0-1)

        Returns:
            Risk level string
        """
        thresholds = MODEL_CONFIG.risk_thresholds

        if risk_score < thresholds['safe']:
            return "Safe"
        elif risk_score < thresholds['caution']:
            return "Caution"
        elif risk_score < thresholds['warning']:
            return "Warning"
        else:
            return "Danger"

    def _get_osha_recommendations(self, risk_score: float, temperature_c: float, humidity: float) -> List[str]:
        """
        Get OSHA-compliant safety recommendations based on heat exposure risk.

        Args:
            risk_score: Heat exposure risk score (0-1)
            temperature_c: Temperature in Celsius
            humidity: Relative humidity percentage

        Returns:
            List of safety recommendations
        """
        # Convert temperature to Fahrenheit for heat index calculation
        temperature_f = (temperature_c * 9/5) + 32
        heat_index = self.calculate_heat_index(temperature_f, humidity)

        recommendations = []

        # Risk-based recommendations
        if risk_score < 0.25:  # Safe
            recommendations.extend([
                "Continue current activity with normal precautions",
                "Maintain regular hydration schedule",
                "Monitor for any changes in conditions"
            ])
        elif risk_score < 0.5:  # Caution
            recommendations.extend([
                "Increase water intake to 8 oz every 15-20 minutes",
                "Take rest breaks in shade/cool area every hour",
                "Monitor workers for early heat stress symptoms",
                "Consider lighter colored, loose-fitting clothing"
            ])
        elif risk_score < 0.75:  # Warning
            recommendations.extend([
                "Implement work/rest cycles: 15 minutes work, 15 minutes rest",
                "Mandatory water intake: 8 oz every 15 minutes",
                "Move to air-conditioned area if possible",
                "Remove unnecessary clothing layers",
                "Assign heat stress buddy system"
            ])
        else:  # Danger
            recommendations.extend([
                "STOP strenuous outdoor work immediately",
                "Move to air-conditioned environment",
                "Continuous medical monitoring required",
                "Implement emergency cooling procedures",
                "Contact medical personnel if heat illness symptoms present"
            ])

        # Heat index specific recommendations
        if heat_index >= 130:  # Extreme Danger
            recommendations.append("EXTREME DANGER: Cease all outdoor work activities")
        elif heat_index >= 105:  # Danger
            recommendations.append("Postpone non-essential outdoor work")
        elif heat_index >= 90:  # Extreme Caution
            recommendations.append("Extreme caution required for outdoor work")

        return recommendations

    def predict_single(self, features_dict: Dict[str, Union[int, float]],
                      use_conservative: bool = True) -> Dict[str, Any]:
        """
        Predict heat exposure risk for a single worker.

        Args:
            features_dict: Dictionary with feature names as keys and values
            use_conservative: Whether to apply conservative bias for safety

        Returns:
            Comprehensive heat exposure risk assessment
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call _load_model() first.")

        # Validate input features
        missing_features = [f for f in self.feature_columns if f not in features_dict]
        if missing_features:
            logger.warning(f"Missing features: {missing_features}")
            # Fill missing features with default values
            for feature in missing_features:
                features_dict[feature] = 0.0

        # Prepare features
        features_df = pd.DataFrame([features_dict])
        features_df = features_df[self.feature_columns]  # Ensure correct order

        # Handle missing values
        features_df = features_df.fillna(0.0)

        # Scale features
        features_scaled = self.scaler.transform(features_df)

        # Make predictions
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]

        # Calculate heat exposure risk scores
        standard_scores, conservative_scores, class_mapping = self._create_heat_exposure_score(
            np.array([prediction]), np.array([probabilities])
        )

        # Select final score based on conservative setting
        final_score = conservative_scores[0] if use_conservative else standard_scores[0]

        # Generate assessments and recommendations
        predicted_class = self.label_encoder.classes_[prediction]
        confidence = float(probabilities.max())
        risk_level = self._assess_heat_exposure_risk(final_score)

        # Get environmental data for heat index calculation
        temp_c = features_dict.get('Temperature', 25.0)
        humidity = features_dict.get('Humidity', 50.0)
        temp_f = (temp_c * 9/5) + 32
        heat_index = self.calculate_heat_index(temp_f, humidity)

        recommendations = self._get_osha_recommendations(final_score, temp_c, humidity)

        # Prepare comprehensive result
        result = {
            'timestamp': datetime.now().isoformat(),
            'worker_id': features_dict.get('worker_id', 'unknown'),

            # Core predictions
            'heat_exposure_risk_score': round(float(final_score), 4),
            'risk_level': risk_level,
            'confidence': round(confidence, 3),

            # Environmental assessment
            'temperature_celsius': temp_c,
            'temperature_fahrenheit': round(temp_f, 1),
            'humidity_percent': humidity,
            'heat_index': round(heat_index, 1),

            # Detailed scores
            'risk_score_standard': round(float(standard_scores[0]), 4),
            'risk_score_conservative': round(float(conservative_scores[0]), 4),
            'conservative_bias_applied': use_conservative,
            'conservative_bias_value': self.conservative_bias,

            # ML model details
            'predicted_thermal_class': str(predicted_class),
            'class_probabilities': {
                class_name: round(float(prob), 3)
                for class_name, prob in zip(self.label_encoder.classes_, probabilities)
            },

            # Safety recommendations
            'osha_recommendations': recommendations,
            'requires_immediate_attention': final_score > MODEL_CONFIG.risk_thresholds['warning'],

            # Biometric summary
            'heart_rate_avg': features_dict.get('hrv_mean_hr', 0.0),
            'hrv_rmssd': features_dict.get('hrv_rmssd', 0.0),

            # System metadata
            'model_version': '1.0.0',
            'prediction_method': 'xgboost_heat_exposure'
        }

        logger.info(f"Heat exposure prediction completed - Risk Level: {risk_level}, Score: {final_score:.3f}")

        return result

    def predict_batch(self, features_df: pd.DataFrame,
                     use_conservative: bool = True) -> List[Dict[str, Any]]:
        """
        Predict heat exposure risk for multiple workers.

        Args:
            features_df: DataFrame with features for multiple samples
            use_conservative: Whether to apply conservative bias

        Returns:
            List of heat exposure risk assessments
        """
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call _load_model() first.")

        logger.info(f"Starting batch prediction for {len(features_df)} samples")

        results = []
        for idx, row in features_df.iterrows():
            try:
                # Add sample identifier if not present
                row_dict = row.to_dict()
                if 'worker_id' not in row_dict:
                    row_dict['worker_id'] = f"worker_{idx}"

                result = self.predict_single(row_dict, use_conservative)
                result['batch_index'] = idx
                results.append(result)

            except Exception as e:
                logger.error(f"Error predicting sample {idx}: {e}")
                # Create error result
                error_result = {
                    'timestamp': datetime.now().isoformat(),
                    'worker_id': f"worker_{idx}",
                    'batch_index': idx,
                    'error': str(e),
                    'heat_exposure_risk_score': None,
                    'risk_level': 'Error',
                    'prediction_successful': False
                }
                results.append(error_result)

        successful_predictions = len([r for r in results if 'error' not in r])
        logger.info(f"Batch prediction completed: {successful_predictions}/{len(features_df)} successful")

        return results

    def get_feature_template(self) -> Dict[str, Union[int, float]]:
        """
        Get a template dictionary with all required features and example values.

        Returns:
            Template dictionary for model input
        """
        template = {}
        for feature in self.feature_columns:
            if feature == 'Gender':
                template[feature] = 1  # 1 for Male, 0 for Female
            elif feature == 'Age':
                template[feature] = 30  # Example age
            elif feature == 'Temperature':
                template[feature] = 25.0  # Example temperature in Celsius
            elif feature == 'Humidity':
                template[feature] = 60.0  # Example humidity percentage
            elif feature.startswith('hrv_'):
                # Provide realistic default values for HRV features
                if 'hr' in feature:
                    template[feature] = 75.0  # Heart rate related
                elif 'nni' in feature:
                    template[feature] = 800.0  # NN interval related
                else:
                    template[feature] = 0.0  # Other HRV metrics
            else:
                template[feature] = 0.0

        return template

    def validate_input(self, features_dict: Dict[str, Union[int, float]]) -> List[str]:
        """
        Validate input features for prediction.

        Args:
            features_dict: Input features dictionary

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for required features
        missing_features = [f for f in self.feature_columns if f not in features_dict]
        if missing_features:
            errors.append(f"Missing required features: {missing_features}")

        # Validate feature ranges
        for feature, value in features_dict.items():
            if feature in self.feature_columns:
                try:
                    float(value)  # Ensure numeric
                except (ValueError, TypeError):
                    errors.append(f"Feature '{feature}' must be numeric, got {type(value)}")

        return errors

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            'model_loaded': self.is_loaded,
            'model_type': 'XGBoost Heat Exposure Predictor',
            'model_directory': self.model_dir,
            'feature_count': len(self.feature_columns) if self.feature_columns else 0,
            'target_classes': list(self.label_encoder.classes_) if self.label_encoder else [],
            'conservative_bias': self.conservative_bias,
            'version': '1.0.0'
        }