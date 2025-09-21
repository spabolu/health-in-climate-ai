"""
Sample Test Data
================

Comprehensive test data fixtures with all 50 HRV features for HeatGuard testing.
Includes realistic scenarios covering safe to dangerous heat exposure conditions.
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Union
import numpy as np


def get_all_feature_columns() -> List[str]:
    """Get all 50 feature columns used by the HeatGuard model."""
    return [
        # Demographics (2 features)
        'Age', 'Gender',

        # Environmental (2 features)
        'Temperature', 'Humidity',

        # Core HRV features (46 features)
        'hrv_mean_nni', 'hrv_median_nni', 'hrv_mode_nni', 'hrv_range_nni',
        'hrv_std_nni', 'hrv_cv_nni', 'hrv_mean_hr', 'hrv_median_hr',
        'hrv_mode_hr', 'hrv_range_hr', 'hrv_std_hr', 'hrv_cv_hr',
        'hrv_rmssd', 'hrv_sdnn', 'hrv_sdsd', 'hrv_nn50', 'hrv_pnn50',
        'hrv_nn20', 'hrv_pnn20', 'hrv_cvnn', 'hrv_cvsd', 'hrv_median_mad',
        'hrv_mean_mad', 'hrv_iqr_nni', 'hrv_total_power', 'hrv_vlf',
        'hrv_lf', 'hrv_hf', 'hrv_lf_hf_ratio', 'hrv_lf_peak',
        'hrv_hf_peak', 'hrv_vlf_percent', 'hrv_lf_percent', 'hrv_hf_percent',
        'hrv_lf_nu', 'hrv_hf_nu', 'hrv_csi', 'hrv_cvi', 'hrv_modified_csi',
        'hrv_tinn', 'hrv_triangular_index', 'hrv_alpha1', 'hrv_alpha2',
        'hrv_sd1', 'hrv_sd2', 'hrv_sd1_sd2_ratio'
    ]


def get_sample_worker_data() -> Dict[str, Union[int, float]]:
    """Generate a complete sample worker data with all 50 features."""
    return {
        # Demographics
        'Age': 30.0,
        'Gender': 1,  # 1=Male, 0=Female

        # Environmental
        'Temperature': 25.5,  # Celsius
        'Humidity': 65.0,     # Percentage

        # Core HRV time domain features
        'hrv_mean_nni': 800.0,    # Mean NN interval (ms)
        'hrv_median_nni': 795.0,  # Median NN interval
        'hrv_mode_nni': 790.0,    # Mode NN interval
        'hrv_range_nni': 450.0,   # Range of NN intervals
        'hrv_std_nni': 45.0,      # Standard deviation of NN intervals
        'hrv_cv_nni': 5.6,        # Coefficient of variation

        # Heart rate features
        'hrv_mean_hr': 75.0,      # Average heart rate (BPM)
        'hrv_median_hr': 75.5,    # Median heart rate
        'hrv_mode_hr': 76.0,      # Mode heart rate
        'hrv_range_hr': 35.0,     # Heart rate range
        'hrv_std_hr': 8.5,        # Heart rate standard deviation
        'hrv_cv_hr': 11.3,        # Heart rate coefficient of variation

        # HRV statistical measures
        'hrv_rmssd': 35.5,        # Root mean square of successive differences
        'hrv_sdnn': 48.2,         # Standard deviation of NN intervals
        'hrv_sdsd': 35.1,         # Standard deviation of successive differences
        'hrv_nn50': 125,          # Number of successive NN intervals > 50ms
        'hrv_pnn50': 15.6,        # Percentage of NN intervals > 50ms
        'hrv_nn20': 245,          # Number of successive NN intervals > 20ms
        'hrv_pnn20': 45.8,        # Percentage of NN intervals > 20ms
        'hrv_cvnn': 5.8,          # Coefficient of variation of NN intervals
        'hrv_cvsd': 0.044,        # Coefficient of variation of successive differences
        'hrv_median_mad': 22.5,   # Median absolute deviation
        'hrv_mean_mad': 28.3,     # Mean absolute deviation
        'hrv_iqr_nni': 62.0,      # Interquartile range of NN intervals

        # Frequency domain features
        'hrv_total_power': 2850.0,  # Total spectral power
        'hrv_vlf': 1200.0,          # Very low frequency power
        'hrv_lf': 980.0,            # Low frequency power
        'hrv_hf': 670.0,            # High frequency power
        'hrv_lf_hf_ratio': 1.46,    # LF/HF ratio
        'hrv_lf_peak': 0.08,        # LF peak frequency
        'hrv_hf_peak': 0.25,        # HF peak frequency
        'hrv_vlf_percent': 42.1,    # VLF percentage
        'hrv_lf_percent': 34.4,     # LF percentage
        'hrv_hf_percent': 23.5,     # HF percentage
        'hrv_lf_nu': 59.4,          # LF normalized units
        'hrv_hf_nu': 40.6,          # HF normalized units

        # Stress indices
        'hrv_csi': 3.2,             # Cardiac stress index
        'hrv_cvi': 2.8,             # Cardiac vagal index
        'hrv_modified_csi': 5.1,    # Modified cardiac stress index

        # Geometric measures
        'hrv_tinn': 225.0,          # Triangular interpolation
        'hrv_triangular_index': 12.8, # Triangular index

        # Non-linear measures
        'hrv_alpha1': 1.15,         # Short-term detrended fluctuation analysis
        'hrv_alpha2': 0.98,         # Long-term detrended fluctuation analysis

        # Poincaré plot measures
        'hrv_sd1': 25.1,            # Standard deviation perpendicular to line of identity
        'hrv_sd2': 68.3,            # Standard deviation along line of identity
        'hrv_sd1_sd2_ratio': 0.37,  # SD1/SD2 ratio

        # Additional metadata
        'worker_id': 'test_worker_001'
    }


def get_batch_worker_data(count: int = 10) -> List[Dict[str, Union[int, float]]]:
    """Generate batch worker data with variations."""
    batch_data = []

    for i in range(count):
        base_data = get_sample_worker_data()

        # Add variations
        base_data['worker_id'] = f'test_worker_{i+1:03d}'
        base_data['Age'] = random.uniform(20, 60)
        base_data['Gender'] = random.choice([0, 1])
        base_data['Temperature'] = random.uniform(18, 40)
        base_data['Humidity'] = random.uniform(30, 90)

        # Vary HRV metrics realistically
        base_data['hrv_mean_hr'] = random.uniform(60, 100)
        base_data['hrv_mean_nni'] = 60000 / base_data['hrv_mean_hr']  # Convert from HR
        base_data['hrv_rmssd'] = random.uniform(15, 80)
        base_data['hrv_sdnn'] = random.uniform(20, 120)
        base_data['hrv_lf_hf_ratio'] = random.uniform(0.5, 3.0)

        batch_data.append(base_data)

    return batch_data


def get_invalid_worker_data() -> Dict[str, Any]:
    """Generate invalid worker data for negative testing."""
    return {
        'Age': 'invalid_age',  # Should be numeric
        'Gender': 5,           # Should be 0 or 1
        'Temperature': None,   # Should not be None
        'Humidity': -10,       # Should be >= 0
        'hrv_mean_hr': 300,    # Unrealistic heart rate
        'hrv_mean_nni': 'invalid', # Should be numeric
        'missing_required_field': True  # Extra field, missing required ones
    }


def get_edge_case_worker_data() -> List[Dict[str, Union[int, float]]]:
    """Generate edge case worker data for boundary testing."""
    edge_cases = []

    # Minimum values
    min_case = get_sample_worker_data()
    min_case.update({
        'Age': 18.0,
        'Temperature': -10.0,
        'Humidity': 0.0,
        'hrv_mean_hr': 40.0,
        'hrv_mean_nni': 300.0,
        'hrv_rmssd': 1.0,
        'hrv_sdnn': 5.0
    })
    edge_cases.append(min_case)

    # Maximum values
    max_case = get_sample_worker_data()
    max_case.update({
        'Age': 80.0,
        'Temperature': 50.0,
        'Humidity': 100.0,
        'hrv_mean_hr': 200.0,
        'hrv_mean_nni': 1500.0,
        'hrv_rmssd': 150.0,
        'hrv_sdnn': 300.0
    })
    edge_cases.append(max_case)

    # Zero/near-zero values
    zero_case = get_sample_worker_data()
    zero_case.update({
        'hrv_rmssd': 0.1,
        'hrv_sdnn': 0.1,
        'hrv_total_power': 10.0,
        'hrv_lf': 1.0,
        'hrv_hf': 1.0
    })
    edge_cases.append(zero_case)

    return edge_cases


def get_high_risk_scenario_data() -> Dict[str, Union[int, float]]:
    """Generate high-risk heat exposure scenario data."""
    high_risk_data = get_sample_worker_data()
    high_risk_data.update({
        # High temperature and humidity
        'Temperature': 42.0,  # Very hot
        'Humidity': 85.0,     # Very humid

        # Stressed physiological indicators
        'hrv_mean_hr': 120.0,     # Elevated heart rate
        'hrv_mean_nni': 500.0,    # Shorter intervals
        'hrv_rmssd': 12.0,        # Low HRV (stress indicator)
        'hrv_sdnn': 18.0,         # Low variability
        'hrv_lf_hf_ratio': 4.5,   # High stress ratio
        'hrv_csi': 8.2,           # High cardiac stress index

        # Older worker (higher risk)
        'Age': 55.0,
        'worker_id': 'high_risk_worker'
    })

    return high_risk_data


def get_performance_test_data(count: int = 1000) -> List[Dict[str, Union[int, float]]]:
    """Generate large dataset for performance testing."""
    return get_batch_worker_data(count)


def get_ramp_up_scenario_data() -> List[Dict[str, Union[int, float]]]:
    """Generate escalating risk scenario data (safe -> dangerous)."""
    scenario_data = []
    steps = 12  # 1-hour scenario with 5-minute intervals

    base_temp = 25.0
    base_hr = 70.0
    base_rmssd = 45.0

    for i in range(steps):
        progress = i / (steps - 1)  # 0 to 1

        sample = get_sample_worker_data()
        sample.update({
            'Temperature': base_temp + (progress * 15),  # 25°C to 40°C
            'Humidity': 60.0 + (progress * 25),          # 60% to 85%
            'hrv_mean_hr': base_hr + (progress * 40),    # 70 to 110 BPM
            'hrv_rmssd': base_rmssd - (progress * 30),   # 45 to 15 (decreasing)
            'hrv_sdnn': 50.0 - (progress * 25),          # 50 to 25
            'hrv_lf_hf_ratio': 1.0 + (progress * 3),     # 1.0 to 4.0
            'worker_id': f'ramp_up_step_{i+1:02d}',
            'scenario_step': i + 1,
            'scenario_time_minutes': i * 5
        })
        scenario_data.append(sample)

    return scenario_data


def get_ramp_down_scenario_data() -> List[Dict[str, Union[int, float]]]:
    """Generate de-escalating risk scenario data (dangerous -> safe)."""
    scenario_data = []
    steps = 12

    base_temp = 40.0
    base_hr = 110.0
    base_rmssd = 15.0

    for i in range(steps):
        progress = i / (steps - 1)  # 0 to 1

        sample = get_sample_worker_data()
        sample.update({
            'Temperature': base_temp - (progress * 15),  # 40°C to 25°C
            'Humidity': 85.0 - (progress * 25),          # 85% to 60%
            'hrv_mean_hr': base_hr - (progress * 40),    # 110 to 70 BPM
            'hrv_rmssd': base_rmssd + (progress * 30),   # 15 to 45 (increasing)
            'hrv_sdnn': 25.0 + (progress * 25),          # 25 to 50
            'hrv_lf_hf_ratio': 4.0 - (progress * 3),     # 4.0 to 1.0
            'worker_id': f'ramp_down_step_{i+1:02d}',
            'scenario_step': i + 1,
            'scenario_time_minutes': i * 5
        })
        scenario_data.append(sample)

    return scenario_data


def get_missing_features_data() -> Dict[str, Any]:
    """Generate data with missing features for robustness testing."""
    data = {
        'Age': 35.0,
        'Gender': 1,
        'Temperature': 30.0,
        'Humidity': 70.0,
        'hrv_mean_hr': 80.0,
        # Deliberately missing many HRV features
        'worker_id': 'missing_features_worker'
    }
    return data


def get_extreme_values_data() -> Dict[str, Union[int, float]]:
    """Generate data with extreme but valid values."""
    return {
        # Demographics
        'Age': 18.0,     # Minimum working age
        'Gender': 0,     # Female

        # Extreme environmental conditions
        'Temperature': 48.0,  # Extreme heat
        'Humidity': 95.0,     # Very high humidity

        # Extreme physiological values (but still physiologically possible)
        'hrv_mean_hr': 180.0,     # Very high heart rate
        'hrv_mean_nni': 333.0,    # Corresponding short interval
        'hrv_rmssd': 5.0,         # Very low HRV (severe stress)
        'hrv_sdnn': 8.0,          # Very low variability
        'hrv_lf_hf_ratio': 8.0,   # Very high stress ratio
        'hrv_csi': 15.0,          # Very high cardiac stress

        # Fill remaining features with extreme but valid values
        **{col: 0.1 if 'percent' in col or 'ratio' in col else 1.0
           for col in get_all_feature_columns()[6:]
           if col not in ['hrv_mean_hr', 'hrv_mean_nni', 'hrv_rmssd', 'hrv_sdnn',
                         'hrv_lf_hf_ratio', 'hrv_csi']},

        'worker_id': 'extreme_values_worker'
    }


def get_realistic_workforce_data() -> List[Dict[str, Union[int, float]]]:
    """Generate realistic workforce data with diverse demographics and conditions."""
    workforce = []

    # Different worker profiles
    profiles = [
        {"age_range": (22, 35), "fitness": "high", "experience": "new"},
        {"age_range": (35, 50), "fitness": "medium", "experience": "experienced"},
        {"age_range": (50, 65), "fitness": "low", "experience": "veteran"}
    ]

    # Different environmental conditions
    environments = [
        {"temp": 22, "humidity": 45, "description": "comfortable"},
        {"temp": 28, "humidity": 65, "description": "warm"},
        {"temp": 35, "humidity": 75, "description": "hot"},
        {"temp": 42, "humidity": 85, "description": "dangerous"}
    ]

    worker_id = 1
    for profile in profiles:
        for env in environments:
            for gender in [0, 1]:  # Both genders
                for _ in range(3):  # 3 workers per combination
                    worker_data = get_sample_worker_data()

                    # Apply profile
                    age = random.uniform(*profile["age_range"])
                    worker_data['Age'] = age
                    worker_data['Gender'] = gender

                    # Apply environment
                    worker_data['Temperature'] = env["temp"] + random.uniform(-2, 2)
                    worker_data['Humidity'] = env["humidity"] + random.uniform(-10, 10)

                    # Adjust physiology based on profile and environment
                    fitness_multiplier = {"high": 0.8, "medium": 1.0, "low": 1.2}[profile["fitness"]]
                    age_factor = 1 + (age - 30) * 0.01  # Older workers slightly higher HR
                    temp_stress = max(0, (env["temp"] - 25) * 0.05)  # Temperature stress

                    base_hr = 70 * fitness_multiplier * age_factor * (1 + temp_stress)
                    worker_data['hrv_mean_hr'] = base_hr + random.uniform(-5, 5)
                    worker_data['hrv_mean_nni'] = 60000 / worker_data['hrv_mean_hr']

                    # Adjust HRV based on stress level
                    stress_level = temp_stress + (age - 30) * 0.01
                    worker_data['hrv_rmssd'] = max(10, 45 - stress_level * 20 + random.uniform(-5, 5))
                    worker_data['hrv_sdnn'] = max(15, 50 - stress_level * 15 + random.uniform(-5, 5))
                    worker_data['hrv_lf_hf_ratio'] = 1.0 + stress_level * 2 + random.uniform(-0.2, 0.2)

                    worker_data['worker_id'] = f'workforce_worker_{worker_id:03d}'
                    worker_data['profile'] = profile["description"]
                    worker_data['environment'] = env["description"]

                    workforce.append(worker_data)
                    worker_id += 1

    return workforce