"""
Model Configuration
===================

Configuration for machine learning models and feature engineering.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class ModelConfiguration:
    """Configuration for heat exposure prediction models."""

    # XGBoost Model Parameters
    xgboost_params: Dict[str, Any] = None

    # Feature Configuration
    feature_columns: List[str] = None

    # Prediction Thresholds
    risk_thresholds: Dict[str, float] = None

    # Data Processing
    conservative_bias: float = 0.15
    enable_scaling: bool = True
    fill_missing_values: bool = True

    def __post_init__(self):
        if self.xgboost_params is None:
            self.xgboost_params = {
                'objective': 'multi:softprob',
                'num_class': 4,
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42,
                'n_jobs': -1
            }

        if self.feature_columns is None:
            self.feature_columns = [
                # Demographics
                "Gender", "Age",

                # Heart Rate Variability (HRV) Features from Wearable Devices
                "hrv_mean_nni", "hrv_median_nni", "hrv_range_nni",
                "hrv_sdsd", "hrv_rmssd", "hrv_nni_50", "hrv_pnni_50",
                "hrv_nni_20", "hrv_pnni_20", "hrv_cvsd", "hrv_sdnn",
                "hrv_cvnni", "hrv_mean_hr", "hrv_min_hr", "hrv_max_hr",
                "hrv_std_hr", "hrv_total_power", "hrv_vlf", "hrv_lf",
                "hrv_hf", "hrv_lf_hf_ratio", "hrv_lfnu", "hrv_hfnu",
                "hrv_SD1", "hrv_SD2", "hrv_SD2SD1", "hrv_CSI",
                "hrv_CVI", "hrv_CSI_Modified", "hrv_mean", "hrv_std",
                "hrv_min", "hrv_max", "hrv_ptp", "hrv_sum", "hrv_energy",
                "hrv_skewness", "hrv_kurtosis", "hrv_peaks", "hrv_rms",
                "hrv_lineintegral", "hrv_n_above_mean", "hrv_n_below_mean",
                "hrv_n_sign_changes", "hrv_iqr", "hrv_iqr_5_95",
                "hrv_pct_5", "hrv_pct_95", "hrv_entropy",
                "hrv_perm_entropy", "hrv_svd_entropy",

                # Environmental Data (from IoT sensors)
                "Temperature", "Humidity"
            ]

        if self.risk_thresholds is None:
            self.risk_thresholds = {
                'safe': 0.25,           # 0.0 - 0.25: Safe conditions
                'caution': 0.50,        # 0.25 - 0.50: Caution needed
                'warning': 0.75,        # 0.50 - 0.75: Warning level
                'danger': 1.0           # 0.75 - 1.0: Dangerous conditions
            }


# Heat Index Calculation Parameters
HEAT_INDEX_CONFIG = {
    'coefficients': {
        'c1': -42.379,
        'c2': 2.04901523,
        'c3': 10.14333127,
        'c4': -0.22475541,
        'c5': -6.83783e-3,
        'c6': -5.481717e-2,
        'c7': 1.22874e-3,
        'c8': 8.5282e-4,
        'c9': -1.99e-6
    },
    'adjustments': {
        'low_rh_threshold': 13,
        'high_rh_threshold': 85,
        'temp_threshold_low': 80,
        'temp_threshold_high': 87
    }
}

# OSHA Heat Safety Standards
OSHA_STANDARDS = {
    'heat_index_categories': {
        'caution': (80, 90),      # 80-90°F: Caution
        'extreme_caution': (90, 105),  # 90-105°F: Extreme Caution
        'danger': (105, 130),     # 105-130°F: Danger
        'extreme_danger': (130, float('inf'))  # 130°F+: Extreme Danger
    },
    'work_rest_ratios': {
        'light_work': {
            'caution': {'work': 45, 'rest': 15},
            'extreme_caution': {'work': 30, 'rest': 30},
            'danger': {'work': 15, 'rest': 45},
            'extreme_danger': {'work': 0, 'rest': 60}
        },
        'moderate_work': {
            'caution': {'work': 30, 'rest': 30},
            'extreme_caution': {'work': 15, 'rest': 45},
            'danger': {'work': 0, 'rest': 60},
            'extreme_danger': {'work': 0, 'rest': 60}
        },
        'heavy_work': {
            'caution': {'work': 15, 'rest': 45},
            'extreme_caution': {'work': 0, 'rest': 60},
            'danger': {'work': 0, 'rest': 60},
            'extreme_danger': {'work': 0, 'rest': 60}
        }
    }
}

# Risk Assessment Mapping
RISK_ASSESSMENT_MAPPING = {
    'thermal_comfort_to_heat_exposure': {
        'neutral': 0.0,          # Comfortable -> Safe
        'slightly_warm': 0.3,    # Slightly uncomfortable -> Caution
        'warm': 0.6,            # Uncomfortable -> Warning
        'hot': 0.9              # Very uncomfortable -> Danger
    }
}

# Feature Engineering Configuration
FEATURE_ENGINEERING = {
    'hrv_feature_groups': {
        'time_domain': [
            'hrv_mean_nni', 'hrv_median_nni', 'hrv_range_nni',
            'hrv_sdsd', 'hrv_rmssd', 'hrv_sdnn', 'hrv_cvnni'
        ],
        'frequency_domain': [
            'hrv_total_power', 'hrv_vlf', 'hrv_lf', 'hrv_hf',
            'hrv_lf_hf_ratio', 'hrv_lfnu', 'hrv_hfnu'
        ],
        'geometric': [
            'hrv_SD1', 'hrv_SD2', 'hrv_SD2SD1', 'hrv_CSI',
            'hrv_CVI', 'hrv_CSI_Modified'
        ],
        'statistical': [
            'hrv_mean', 'hrv_std', 'hrv_min', 'hrv_max',
            'hrv_skewness', 'hrv_kurtosis', 'hrv_entropy'
        ]
    },
    'normalization_ranges': {
        'Age': (18, 65),
        'Temperature': (-10, 50),  # Celsius
        'Humidity': (0, 100),      # Percentage
        'hrv_mean_hr': (40, 200),  # BPM
        'hrv_mean_nni': (300, 1500)  # milliseconds
    }
}

# Data Validation Rules
VALIDATION_RULES = {
    'required_features': [
        'Gender', 'Age', 'Temperature', 'Humidity',
        'hrv_mean_hr', 'hrv_mean_nni'
    ],
    'optional_features': [
        f for f in ModelConfiguration().feature_columns
        if f not in ['Gender', 'Age', 'Temperature', 'Humidity', 'hrv_mean_hr', 'hrv_mean_nni']
    ],
    'value_ranges': {
        'Gender': (0, 1),
        'Age': (16, 80),
        'Temperature': (-50, 70),  # Celsius, extended range for validation
        'Humidity': (0, 100),
        'hrv_mean_hr': (30, 220),
        'hrv_mean_nni': (200, 2000)
    }
}

# Model Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    'accuracy_minimum': 0.85,
    'precision_minimum': 0.80,
    'recall_minimum': 0.80,
    'f1_minimum': 0.80,
    'prediction_time_maximum': 0.1,  # seconds
    'model_load_time_maximum': 5.0   # seconds
}

# Global model configuration instance
MODEL_CONFIG = ModelConfiguration()