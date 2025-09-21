"""
Input Validation Utilities
===========================

Comprehensive validation for heat exposure prediction inputs.
"""

import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from ..config.model_config import MODEL_CONFIG, VALIDATION_RULES
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class InputValidator:
    """Validates input data for heat exposure predictions."""

    def __init__(self):
        self.required_features = VALIDATION_RULES['required_features']
        self.optional_features = VALIDATION_RULES['optional_features']
        self.all_features = MODEL_CONFIG.feature_columns
        self.value_ranges = VALIDATION_RULES['value_ranges']

    def validate_single_prediction(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Validate input data for single prediction.

        Args:
            data: Input data dictionary

        Returns:
            Tuple of (cleaned_data, warnings)

        Raises:
            ValidationError: If validation fails
        """
        errors = []
        warnings = []
        cleaned_data = {}

        # Check data type
        if not isinstance(data, dict):
            raise ValidationError(f"Input must be a dictionary, got {type(data)}")

        # Validate worker ID
        worker_id = data.get('worker_id')
        if worker_id is not None:
            cleaned_data['worker_id'] = str(worker_id)
        else:
            cleaned_data['worker_id'] = f"worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            warnings.append("No worker_id provided, generated automatically")

        # Validate required features
        missing_required = []
        for feature in self.required_features:
            if feature not in data or data[feature] is None:
                missing_required.append(feature)

        if missing_required:
            errors.append(f"Missing required features: {missing_required}")

        # Validate and clean feature values
        for feature in self.all_features:
            if feature in data:
                try:
                    value = self._validate_feature_value(feature, data[feature])
                    cleaned_data[feature] = value
                except ValidationError as e:
                    errors.append(f"Feature '{feature}': {e}")
            elif feature in self.required_features:
                # Already handled in missing_required check
                continue
            else:
                # Optional feature - use default value
                cleaned_data[feature] = self._get_default_value(feature)
                warnings.append(f"Using default value for optional feature '{feature}'")

        # Additional business logic validation
        try:
            self._validate_business_rules(cleaned_data)
        except ValidationError as e:
            errors.append(f"Business rule validation: {e}")

        if errors:
            raise ValidationError(f"Validation failed: {'; '.join(errors)}")

        return cleaned_data, warnings

    def validate_batch_prediction(self, data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Validate input data for batch prediction.

        Args:
            data: List of input data dictionaries

        Returns:
            Tuple of (cleaned_data_list, warnings)

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, list):
            raise ValidationError(f"Batch input must be a list, got {type(data)}")

        if len(data) == 0:
            raise ValidationError("Batch input cannot be empty")

        if len(data) > 1000:  # Configurable limit
            raise ValidationError(f"Batch size {len(data)} exceeds maximum limit of 1000")

        cleaned_data_list = []
        all_warnings = []
        failed_indices = []

        for i, item in enumerate(data):
            try:
                cleaned_item, warnings = self.validate_single_prediction(item)
                cleaned_item['batch_index'] = i
                cleaned_data_list.append(cleaned_item)
                if warnings:
                    all_warnings.extend([f"Item {i}: {w}" for w in warnings])
            except ValidationError as e:
                failed_indices.append(i)
                all_warnings.append(f"Item {i} validation failed: {e}")

        if failed_indices:
            if len(failed_indices) == len(data):
                raise ValidationError("All items in batch failed validation")
            else:
                all_warnings.append(f"Items {failed_indices} failed validation and were skipped")

        return cleaned_data_list, all_warnings

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate pandas DataFrame for batch prediction.

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (cleaned_df, warnings)

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(df, pd.DataFrame):
            raise ValidationError(f"Input must be a pandas DataFrame, got {type(df)}")

        if df.empty:
            raise ValidationError("DataFrame cannot be empty")

        if len(df) > 1000:  # Configurable limit
            raise ValidationError(f"DataFrame size {len(df)} exceeds maximum limit of 1000")

        warnings = []
        cleaned_df = df.copy()

        # Add worker_id column if missing
        if 'worker_id' not in cleaned_df.columns:
            cleaned_df['worker_id'] = [f"worker_{i}" for i in range(len(cleaned_df))]
            warnings.append("Added auto-generated worker_id column")

        # Check for required features
        missing_features = [f for f in self.required_features if f not in cleaned_df.columns]
        if missing_features:
            raise ValidationError(f"Missing required columns: {missing_features}")

        # Add missing optional features with default values
        for feature in self.all_features:
            if feature not in cleaned_df.columns:
                cleaned_df[feature] = self._get_default_value(feature)
                warnings.append(f"Added default values for missing column '{feature}'")

        # Validate and clean values
        for feature in self.all_features:
            if feature in cleaned_df.columns:
                try:
                    cleaned_df[feature] = cleaned_df[feature].apply(
                        lambda x: self._validate_feature_value(feature, x)
                    )
                except Exception as e:
                    raise ValidationError(f"Error validating column '{feature}': {e}")

        # Check for and handle missing values
        missing_counts = cleaned_df[self.all_features].isnull().sum()
        if missing_counts.sum() > 0:
            features_with_missing = missing_counts[missing_counts > 0].index.tolist()
            warnings.append(f"Found missing values in columns: {features_with_missing}")
            # Fill with defaults
            for feature in features_with_missing:
                cleaned_df[feature].fillna(self._get_default_value(feature), inplace=True)

        return cleaned_df, warnings

    def _validate_feature_value(self, feature: str, value: Any) -> float:
        """
        Validate and convert a single feature value.

        Args:
            feature: Feature name
            value: Feature value

        Returns:
            Validated and converted value

        Raises:
            ValidationError: If validation fails
        """
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return self._get_default_value(feature)

        # Convert to numeric
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Cannot convert '{value}' to numeric")

        # Check for invalid numeric values
        if np.isnan(numeric_value) or np.isinf(numeric_value):
            return self._get_default_value(feature)

        # Validate ranges
        if feature in self.value_ranges:
            min_val, max_val = self.value_ranges[feature]
            if not (min_val <= numeric_value <= max_val):
                logger.warning(f"Feature '{feature}' value {numeric_value} outside expected range [{min_val}, {max_val}]")
                # Clamp to valid range
                numeric_value = max(min_val, min(max_val, numeric_value))

        return numeric_value

    def _get_default_value(self, feature: str) -> float:
        """
        Get default value for a feature.

        Args:
            feature: Feature name

        Returns:
            Default value
        """
        if feature == 'Gender':
            return 1.0  # Default to Male
        elif feature == 'Age':
            return 30.0  # Default age
        elif feature == 'Temperature':
            return 25.0  # Comfortable temperature in Celsius
        elif feature == 'Humidity':
            return 50.0  # Moderate humidity
        elif 'hr' in feature.lower() and 'mean' in feature:
            return 75.0  # Default heart rate
        elif 'nni' in feature.lower() and 'mean' in feature:
            return 800.0  # Default NN interval
        elif feature.startswith('hrv_'):
            return 0.0  # Default for other HRV features
        else:
            return 0.0

    def _validate_business_rules(self, data: Dict[str, Any]) -> None:
        """
        Validate business-specific rules.

        Args:
            data: Validated feature data

        Raises:
            ValidationError: If business rules fail
        """
        # Age validation
        age = data.get('Age', 0)
        if age < 16:
            raise ValidationError("Worker age must be at least 16 years")
        if age > 80:
            logger.warning(f"Unusual age value: {age} years")

        # Temperature validation
        temp = data.get('Temperature', 25)
        if temp < -20:
            raise ValidationError("Temperature too low for outdoor work")
        if temp > 50:
            logger.warning(f"Extremely high temperature: {temp}°C")

        # Heart rate validation
        hr = data.get('hrv_mean_hr', 75)
        if hr < 30:
            logger.warning(f"Unusually low heart rate: {hr} BPM")
        if hr > 220:
            logger.warning(f"Unusually high heart rate: {hr} BPM")

        # Humidity validation
        humidity = data.get('Humidity', 50)
        if humidity < 0 or humidity > 100:
            raise ValidationError(f"Humidity must be between 0-100%, got {humidity}%")

    def validate_api_key(self, api_key: Optional[str]) -> bool:
        """
        Validate API key format and structure.

        Args:
            api_key: API key to validate

        Returns:
            True if valid, False otherwise
        """
        if not api_key:
            return False

        # Basic format validation - adjust based on your API key format
        if len(api_key) < 20:
            return False

        # Check for valid characters (alphanumeric + some special chars)
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key):
            return False

        return True

    def validate_worker_id(self, worker_id: str) -> str:
        """
        Validate and normalize worker ID.

        Args:
            worker_id: Worker identifier

        Returns:
            Normalized worker ID

        Raises:
            ValidationError: If worker ID is invalid
        """
        if not worker_id or not isinstance(worker_id, str):
            raise ValidationError("Worker ID must be a non-empty string")

        # Remove extra whitespace
        worker_id = worker_id.strip()

        if len(worker_id) == 0:
            raise ValidationError("Worker ID cannot be empty")

        if len(worker_id) > 100:
            raise ValidationError("Worker ID too long (max 100 characters)")

        # Basic sanitization - allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', worker_id):
            raise ValidationError("Worker ID contains invalid characters")

        return worker_id

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get summary of validation rules and requirements.

        Returns:
            Dictionary with validation information
        """
        return {
            'required_features': self.required_features,
            'optional_features': self.optional_features[:10],  # Show first 10
            'total_features': len(self.all_features),
            'value_ranges': self.value_ranges,
            'max_batch_size': 1000,
            'supported_formats': ['dict', 'list_of_dicts', 'pandas_dataframe']
        }