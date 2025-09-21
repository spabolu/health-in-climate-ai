"""
Data Preprocessing Utilities
=============================

Handles data preprocessing, feature engineering, and transformation
for heat exposure prediction.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import warnings

from ..config.model_config import MODEL_CONFIG, FEATURE_ENGINEERING
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataPreprocessor:
    """Handles data preprocessing for heat exposure prediction."""

    def __init__(self):
        self.feature_columns = MODEL_CONFIG.feature_columns
        self.normalization_ranges = FEATURE_ENGINEERING['normalization_ranges']
        self.hrv_feature_groups = FEATURE_ENGINEERING['hrv_feature_groups']

    def preprocess_single(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Preprocess data for a single worker prediction.

        Args:
            data: Input data dictionary

        Returns:
            Preprocessed data dictionary
        """
        processed_data = data.copy()

        # Handle missing values
        processed_data = self._handle_missing_values(processed_data)

        # Feature engineering
        processed_data = self._engineer_features(processed_data)

        # Normalize features
        if MODEL_CONFIG.enable_scaling:
            processed_data = self._normalize_features(processed_data)

        # Ensure all required features are present
        for feature in self.feature_columns:
            if feature not in processed_data:
                processed_data[feature] = 0.0

        logger.debug(f"Preprocessed single sample with {len(processed_data)} features")
        return processed_data

    def preprocess_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """
        Preprocess data for batch prediction.

        Args:
            data_list: List of input data dictionaries

        Returns:
            List of preprocessed data dictionaries
        """
        processed_list = []

        for i, data in enumerate(data_list):
            try:
                processed_data = self.preprocess_single(data)
                processed_data['batch_index'] = i
                processed_list.append(processed_data)
            except Exception as e:
                logger.error(f"Error preprocessing batch item {i}: {e}")
                continue

        logger.info(f"Preprocessed batch of {len(processed_list)}/{len(data_list)} samples")
        return processed_list

    def preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess pandas DataFrame for batch prediction.

        Args:
            df: Input DataFrame

        Returns:
            Preprocessed DataFrame
        """
        processed_df = df.copy()

        # Handle missing values
        processed_df = self._handle_missing_values_df(processed_df)

        # Feature engineering
        processed_df = self._engineer_features_df(processed_df)

        # Normalize features
        if MODEL_CONFIG.enable_scaling:
            processed_df = self._normalize_features_df(processed_df)

        # Ensure all required features are present
        for feature in self.feature_columns:
            if feature not in processed_df.columns:
                processed_df[feature] = 0.0

        # Reorder columns to match model expectations
        feature_cols = [col for col in self.feature_columns if col in processed_df.columns]
        other_cols = [col for col in processed_df.columns if col not in self.feature_columns]
        processed_df = processed_df[feature_cols + other_cols]

        logger.info(f"Preprocessed DataFrame with {len(processed_df)} rows and {len(feature_cols)} features")
        return processed_df

    def _handle_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle missing values in single data sample.

        Args:
            data: Input data dictionary

        Returns:
            Data with missing values handled
        """
        processed_data = data.copy()

        for feature in self.feature_columns:
            if feature not in processed_data or processed_data[feature] is None:
                processed_data[feature] = self._get_imputed_value(feature, processed_data)
            elif isinstance(processed_data[feature], str) and processed_data[feature].strip() == "":
                processed_data[feature] = self._get_imputed_value(feature, processed_data)

        return processed_data

    def _handle_missing_values_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with missing values handled
        """
        processed_df = df.copy()

        for feature in self.feature_columns:
            if feature in processed_df.columns:
                # Get missing value mask
                missing_mask = processed_df[feature].isnull()

                if missing_mask.sum() > 0:
                    # Use group-based imputation where possible
                    imputed_values = processed_df.apply(
                        lambda row: self._get_imputed_value(feature, row.to_dict())
                        if pd.isnull(row[feature]) else row[feature],
                        axis=1
                    )
                    processed_df[feature] = imputed_values

        return processed_df

    def _get_imputed_value(self, feature: str, context_data: Dict[str, Any]) -> float:
        """
        Get imputed value for missing feature based on context.

        Args:
            feature: Feature name
            context_data: Available context data

        Returns:
            Imputed value
        """
        # Demographics-based imputation
        if feature == 'Age':
            return 30.0  # Default working age

        if feature == 'Gender':
            return 1.0  # Default to Male

        # Environmental imputation
        if feature == 'Temperature':
            return 25.0  # Comfortable room temperature

        if feature == 'Humidity':
            return 50.0  # Moderate humidity

        # HRV feature imputation based on age and gender
        age = context_data.get('Age', 30)
        gender = context_data.get('Gender', 1)

        if feature == 'hrv_mean_hr':
            # Age-adjusted resting heart rate
            base_hr = 75 - (age - 30) * 0.5  # Decreases with age
            return max(50, min(100, base_hr))

        if feature == 'hrv_mean_nni':
            # Inverse relationship with heart rate
            hr = context_data.get('hrv_mean_hr', 75)
            return 60000 / hr if hr > 0 else 800

        if feature == 'hrv_rmssd':
            # Age and gender dependent
            base_rmssd = 40 - (age - 30) * 0.5
            if gender == 0:  # Female
                base_rmssd += 5
            return max(10, base_rmssd)

        if feature == 'hrv_sdnn':
            # Related to overall HRV
            base_sdnn = 50 - (age - 30) * 0.3
            return max(20, base_sdnn)

        # Default for other HRV features
        if feature.startswith('hrv_'):
            return 0.0

        return 0.0

    def _engineer_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create engineered features from raw data.

        Args:
            data: Input data dictionary

        Returns:
            Data with engineered features
        """
        engineered_data = data.copy()

        # Calculate derived HRV features if missing
        if 'hrv_mean_hr' in engineered_data and 'hrv_mean_nni' not in engineered_data:
            hr = engineered_data['hrv_mean_hr']
            if hr > 0:
                engineered_data['hrv_mean_nni'] = 60000 / hr

        if 'hrv_mean_nni' in engineered_data and 'hrv_mean_hr' not in engineered_data:
            nni = engineered_data['hrv_mean_nni']
            if nni > 0:
                engineered_data['hrv_mean_hr'] = 60000 / nni

        # Calculate heat stress indicators
        temp = engineered_data.get('Temperature', 25)
        humidity = engineered_data.get('Humidity', 50)

        # Heat index approximation (if not already calculated elsewhere)
        if temp > 26:  # Above comfortable temperature
            heat_factor = 1 + (temp - 26) * 0.05 + (humidity - 50) * 0.01
            engineered_data['heat_stress_factor'] = min(2.0, heat_factor)
        else:
            engineered_data['heat_stress_factor'] = 1.0

        # Age-adjusted physiological indicators
        age = engineered_data.get('Age', 30)
        age_factor = 1 + max(0, (age - 40) * 0.01)  # Increased risk after 40
        engineered_data['age_risk_factor'] = age_factor

        # HRV-based stress indicators
        rmssd = engineered_data.get('hrv_rmssd', 0)
        if rmssd > 0:
            # Lower RMSSD indicates higher stress
            stress_indicator = max(0, (50 - rmssd) / 50)
            engineered_data['stress_indicator'] = stress_indicator

        return engineered_data

    def _engineer_features_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create engineered features for DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with engineered features
        """
        engineered_df = df.copy()

        # Vectorized feature engineering
        if 'hrv_mean_hr' in engineered_df.columns and 'hrv_mean_nni' not in engineered_df.columns:
            engineered_df['hrv_mean_nni'] = 60000 / engineered_df['hrv_mean_hr'].replace(0, np.nan)

        if 'hrv_mean_nni' in engineered_df.columns and 'hrv_mean_hr' not in engineered_df.columns:
            engineered_df['hrv_mean_hr'] = 60000 / engineered_df['hrv_mean_nni'].replace(0, np.nan)

        # Heat stress factor
        if 'Temperature' in engineered_df.columns and 'Humidity' in engineered_df.columns:
            temp = engineered_df['Temperature']
            humidity = engineered_df['Humidity']
            heat_factor = 1 + np.maximum(0, temp - 26) * 0.05 + (humidity - 50) * 0.01
            engineered_df['heat_stress_factor'] = np.minimum(2.0, heat_factor)

        # Age risk factor
        if 'Age' in engineered_df.columns:
            age_factor = 1 + np.maximum(0, (engineered_df['Age'] - 40) * 0.01)
            engineered_df['age_risk_factor'] = age_factor

        # HRV stress indicator
        if 'hrv_rmssd' in engineered_df.columns:
            rmssd = engineered_df['hrv_rmssd']
            stress_indicator = np.maximum(0, (50 - rmssd) / 50)
            engineered_df['stress_indicator'] = stress_indicator.fillna(0)

        return engineered_df

    def _normalize_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize features to standard ranges.

        Args:
            data: Input data dictionary

        Returns:
            Data with normalized features
        """
        normalized_data = data.copy()

        for feature, value in normalized_data.items():
            if feature in self.normalization_ranges:
                min_val, max_val = self.normalization_ranges[feature]
                if max_val > min_val:
                    # Min-max normalization to [0, 1]
                    normalized_value = (value - min_val) / (max_val - min_val)
                    normalized_data[feature] = np.clip(normalized_value, 0, 1)

        return normalized_data

    def _normalize_features_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize features in DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with normalized features
        """
        normalized_df = df.copy()

        for feature in self.normalization_ranges:
            if feature in normalized_df.columns:
                min_val, max_val = self.normalization_ranges[feature]
                if max_val > min_val:
                    # Min-max normalization to [0, 1]
                    normalized_values = (normalized_df[feature] - min_val) / (max_val - min_val)
                    normalized_df[feature] = np.clip(normalized_values, 0, 1)

        return normalized_df

    def create_feature_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of feature values and their interpretations.

        Args:
            data: Processed data dictionary

        Returns:
            Feature summary dictionary
        """
        summary = {
            'demographics': {
                'age': data.get('Age', 'N/A'),
                'gender': 'Male' if data.get('Gender', 1) == 1 else 'Female'
            },
            'environmental': {
                'temperature_celsius': data.get('Temperature', 'N/A'),
                'humidity_percent': data.get('Humidity', 'N/A'),
                'heat_stress_factor': round(data.get('heat_stress_factor', 1.0), 2)
            },
            'cardiovascular': {
                'heart_rate_avg': data.get('hrv_mean_hr', 'N/A'),
                'heart_rate_variability_rmssd': data.get('hrv_rmssd', 'N/A'),
                'nn_interval_avg': data.get('hrv_mean_nni', 'N/A')
            },
            'stress_indicators': {
                'age_risk_factor': round(data.get('age_risk_factor', 1.0), 2),
                'stress_indicator': round(data.get('stress_indicator', 0.0), 2)
            }
        }

        # Add feature completeness
        total_features = len(self.feature_columns)
        available_features = sum(1 for f in self.feature_columns if f in data and data[f] is not None)
        summary['data_quality'] = {
            'feature_completeness': f"{available_features}/{total_features}",
            'completeness_percent': round((available_features / total_features) * 100, 1)
        }

        return summary

    def validate_preprocessed_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate preprocessed data before prediction.

        Args:
            data: Preprocessed data dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check for required features
        missing_features = [f for f in self.feature_columns if f not in data]
        if missing_features:
            errors.append(f"Missing features after preprocessing: {missing_features}")

        # Check for invalid values
        for feature in self.feature_columns:
            if feature in data:
                value = data[feature]
                if not isinstance(value, (int, float)):
                    errors.append(f"Feature {feature} has non-numeric value: {value}")
                elif np.isnan(value) or np.isinf(value):
                    errors.append(f"Feature {feature} has invalid numeric value: {value}")

        return len(errors) == 0, errors