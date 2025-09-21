"""
Data Generator
==============

Generates realistic test data for heat exposure prediction testing and simulation.
"""

import random
import math
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

from ..config.model_config import MODEL_CONFIG, FEATURE_ENGINEERING
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class WorkerProfile:
    """Represents a worker profile for data generation."""
    age: int
    gender: int  # 0 = Female, 1 = Male
    fitness_level: float  # 0-1 scale
    heat_tolerance: float  # 0-1 scale
    base_heart_rate: float
    base_hrv: float


class DataGenerator:
    """Generates synthetic data for heat exposure prediction testing."""

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the data generator.

        Args:
            seed: Random seed for reproducible results
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        self.feature_columns = MODEL_CONFIG.feature_columns
        self.rng = np.random.RandomState(seed)

        # Define realistic ranges for features
        self.feature_ranges = self._define_feature_ranges()
        self.worker_profiles = self._create_worker_profiles()

    def _define_feature_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Define realistic ranges for all features."""
        return {
            # Demographics
            'Age': (18, 65),
            'Gender': (0, 1),  # Discrete: 0=Female, 1=Male

            # Environmental
            'Temperature': (15, 45),  # Celsius
            'Humidity': (20, 95),     # Percentage

            # Heart Rate Variability - Time Domain
            'hrv_mean_nni': (600, 1200),    # NN intervals in ms
            'hrv_median_nni': (600, 1200),
            'hrv_range_nni': (100, 800),
            'hrv_sdsd': (10, 100),
            'hrv_rmssd': (15, 120),
            'hrv_nni_50': (5, 300),
            'hrv_pnni_50': (2, 50),
            'hrv_nni_20': (10, 400),
            'hrv_pnni_20': (5, 80),
            'hrv_cvsd': (0.02, 0.15),
            'hrv_sdnn': (20, 150),
            'hrv_cvnni': (0.02, 0.12),

            # Heart Rate Features
            'hrv_mean_hr': (50, 120),
            'hrv_min_hr': (45, 100),
            'hrv_max_hr': (70, 180),
            'hrv_std_hr': (5, 30),

            # Frequency Domain
            'hrv_total_power': (500, 8000),
            'hrv_vlf': (100, 3000),
            'hrv_lf': (200, 2000),
            'hrv_hf': (150, 1500),
            'hrv_lf_hf_ratio': (0.5, 5.0),
            'hrv_lfnu': (20, 80),
            'hrv_hfnu': (20, 80),

            # Geometric Features
            'hrv_SD1': (10, 80),
            'hrv_SD2': (30, 200),
            'hrv_SD2SD1': (1.2, 4.0),
            'hrv_CSI': (2, 10),
            'hrv_CVI': (2, 8),
            'hrv_CSI_Modified': (3, 15),

            # Statistical Features
            'hrv_mean': (600, 1200),
            'hrv_std': (20, 150),
            'hrv_min': (400, 1000),
            'hrv_max': (700, 1400),
            'hrv_ptp': (100, 800),
            'hrv_sum': (30000, 120000),
            'hrv_energy': (1e8, 1e12),
            'hrv_skewness': (-2, 2),
            'hrv_kurtosis': (0, 10),
            'hrv_peaks': (50, 200),
            'hrv_rms': (600, 1200),
            'hrv_lineintegral': (30000, 120000),
            'hrv_n_above_mean': (25, 75),
            'hrv_n_below_mean': (25, 75),
            'hrv_n_sign_changes': (20, 80),
            'hrv_iqr': (50, 300),
            'hrv_iqr_5_95': (200, 800),
            'hrv_pct_5': (500, 1000),
            'hrv_pct_95': (800, 1300),
            'hrv_entropy': (0.5, 1.5),
            'hrv_perm_entropy': (0.3, 1.0),
            'hrv_svd_entropy': (0.4, 1.2)
        }

    def _create_worker_profiles(self) -> List[WorkerProfile]:
        """Create diverse worker profiles for realistic data generation."""
        profiles = []

        # Create various worker archetypes
        archetypes = [
            # Young, fit male worker
            {'age': 25, 'gender': 1, 'fitness': 0.8, 'heat_tolerance': 0.7, 'base_hr': 65, 'base_hrv': 45},
            # Middle-aged female worker
            {'age': 40, 'gender': 0, 'fitness': 0.6, 'heat_tolerance': 0.6, 'base_hr': 75, 'base_hrv': 35},
            # Older male worker
            {'age': 55, 'gender': 1, 'fitness': 0.4, 'heat_tolerance': 0.4, 'base_hr': 80, 'base_hrv': 25},
            # Young female worker
            {'age': 22, 'gender': 0, 'fitness': 0.7, 'heat_tolerance': 0.6, 'base_hr': 70, 'base_hrv': 40},
            # Average male worker
            {'age': 35, 'gender': 1, 'fitness': 0.5, 'heat_tolerance': 0.5, 'base_hr': 75, 'base_hrv': 35},
            # Fit older female worker
            {'age': 50, 'gender': 0, 'fitness': 0.7, 'heat_tolerance': 0.6, 'base_hr': 72, 'base_hrv': 38}
        ]

        for archetype in archetypes:
            profile = WorkerProfile(
                age=archetype['age'],
                gender=archetype['gender'],
                fitness_level=archetype['fitness'],
                heat_tolerance=archetype['heat_tolerance'],
                base_heart_rate=archetype['base_hr'],
                base_hrv=archetype['base_hrv']
            )
            profiles.append(profile)

        return profiles

    def generate_random_sample(self,
                              risk_level: Optional[str] = None,
                              worker_profile: Optional[WorkerProfile] = None) -> Dict[str, Any]:
        """
        Generate a single random data sample.

        Args:
            risk_level: Target risk level ('safe', 'caution', 'warning', 'danger')
            worker_profile: Specific worker profile to use

        Returns:
            Dictionary with generated feature values
        """
        # Select worker profile
        if worker_profile is None:
            worker_profile = self.rng.choice(self.worker_profiles)

        # Generate base data
        data = {
            'worker_id': f'worker_{self.rng.randint(1000, 9999)}',
            'Age': worker_profile.age,
            'Gender': worker_profile.gender
        }

        # Generate environmental conditions based on target risk level
        if risk_level:
            temp, humidity = self._generate_environmental_conditions(risk_level)
        else:
            temp = self.rng.uniform(*self.feature_ranges['Temperature'])
            humidity = self.rng.uniform(*self.feature_ranges['Humidity'])

        data['Temperature'] = temp
        data['Humidity'] = humidity

        # Generate physiological data based on environmental stress and worker profile
        stress_factor = self._calculate_stress_factor(temp, humidity, worker_profile)
        hrv_data = self._generate_hrv_features(worker_profile, stress_factor)
        data.update(hrv_data)

        return data

    def generate_batch_samples(self,
                              count: int,
                              risk_distribution: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple random data samples.

        Args:
            count: Number of samples to generate
            risk_distribution: Distribution of risk levels {'safe': 0.4, 'caution': 0.3, ...}

        Returns:
            List of generated data samples
        """
        if risk_distribution is None:
            risk_distribution = {
                'safe': 0.4,
                'caution': 0.3,
                'warning': 0.2,
                'danger': 0.1
            }

        samples = []
        risk_levels = list(risk_distribution.keys())
        risk_weights = list(risk_distribution.values())

        for i in range(count):
            # Select risk level based on distribution
            risk_level = self.rng.choice(risk_levels, p=risk_weights)

            # Generate sample
            sample = self.generate_random_sample(risk_level=risk_level)
            sample['sample_index'] = i
            samples.append(sample)

        logger.info(f"Generated {count} random samples with risk distribution: {risk_distribution}")
        return samples

    def generate_ramp_up_scenario(self,
                                 duration_minutes: int = 60,
                                 interval_minutes: int = 5,
                                 worker_profile: Optional[WorkerProfile] = None) -> List[Dict[str, Any]]:
        """
        Generate escalating risk scenario (green → red).

        Args:
            duration_minutes: Total duration of the scenario
            interval_minutes: Time interval between measurements
            worker_profile: Specific worker profile to use

        Returns:
            List of samples showing escalating heat exposure risk
        """
        if worker_profile is None:
            worker_profile = self.rng.choice(self.worker_profiles)

        samples = []
        num_samples = duration_minutes // interval_minutes

        for i in range(num_samples):
            # Calculate progression from safe to dangerous
            progress = i / (num_samples - 1)  # 0 to 1

            # Environmental escalation
            temp_start = 22  # Comfortable start temperature
            temp_end = 42    # Dangerous end temperature
            temp = temp_start + (temp_end - temp_start) * progress

            humidity_start = 45  # Moderate humidity
            humidity_end = 85    # High humidity
            humidity = humidity_start + (humidity_end - humidity_start) * progress

            # Generate sample
            data = {
                'worker_id': f'rampup_worker_{worker_profile.age}_{worker_profile.gender}',
                'scenario_type': 'ramp_up',
                'time_minutes': i * interval_minutes,
                'scenario_progress': progress,
                'Age': worker_profile.age,
                'Gender': worker_profile.gender,
                'Temperature': temp,
                'Humidity': humidity
            }

            # Generate physiological response
            stress_factor = self._calculate_stress_factor(temp, humidity, worker_profile, progress)
            hrv_data = self._generate_hrv_features(worker_profile, stress_factor)
            data.update(hrv_data)

            samples.append(data)

        logger.info(f"Generated ramp-up scenario with {len(samples)} samples over {duration_minutes} minutes")
        return samples

    def generate_ramp_down_scenario(self,
                                   duration_minutes: int = 60,
                                   interval_minutes: int = 5,
                                   worker_profile: Optional[WorkerProfile] = None) -> List[Dict[str, Any]]:
        """
        Generate de-escalating risk scenario (red → green).

        Args:
            duration_minutes: Total duration of the scenario
            interval_minutes: Time interval between measurements
            worker_profile: Specific worker profile to use

        Returns:
            List of samples showing decreasing heat exposure risk
        """
        if worker_profile is None:
            worker_profile = self.rng.choice(self.worker_profiles)

        samples = []
        num_samples = duration_minutes // interval_minutes

        for i in range(num_samples):
            # Calculate progression from dangerous to safe
            progress = 1 - (i / (num_samples - 1))  # 1 to 0

            # Environmental de-escalation
            temp_start = 42  # Dangerous start temperature
            temp_end = 22    # Comfortable end temperature
            temp = temp_start + (temp_end - temp_start) * (1 - progress)

            humidity_start = 85  # High humidity
            humidity_end = 45    # Moderate humidity
            humidity = humidity_start + (humidity_end - humidity_start) * (1 - progress)

            # Generate sample
            data = {
                'worker_id': f'rampdown_worker_{worker_profile.age}_{worker_profile.gender}',
                'scenario_type': 'ramp_down',
                'time_minutes': i * interval_minutes,
                'scenario_progress': 1 - progress,  # 0 to 1 for recovery
                'Age': worker_profile.age,
                'Gender': worker_profile.gender,
                'Temperature': temp,
                'Humidity': humidity
            }

            # Generate physiological response (recovery)
            stress_factor = self._calculate_stress_factor(temp, humidity, worker_profile, progress * 0.7)  # Slower recovery
            hrv_data = self._generate_hrv_features(worker_profile, stress_factor)
            data.update(hrv_data)

            samples.append(data)

        logger.info(f"Generated ramp-down scenario with {len(samples)} samples over {duration_minutes} minutes")
        return samples

    def _generate_environmental_conditions(self, risk_level: str) -> Tuple[float, float]:
        """Generate environmental conditions for specific risk level."""
        if risk_level == 'safe':
            temp = self.rng.uniform(18, 26)
            humidity = self.rng.uniform(30, 60)
        elif risk_level == 'caution':
            temp = self.rng.uniform(26, 32)
            humidity = self.rng.uniform(50, 75)
        elif risk_level == 'warning':
            temp = self.rng.uniform(32, 38)
            humidity = self.rng.uniform(65, 85)
        else:  # danger
            temp = self.rng.uniform(38, 45)
            humidity = self.rng.uniform(70, 95)

        return temp, humidity

    def _calculate_stress_factor(self,
                               temp: float,
                               humidity: float,
                               worker_profile: WorkerProfile,
                               time_progress: float = 0) -> float:
        """Calculate physiological stress factor based on conditions and worker profile."""
        # Base stress from temperature
        temp_stress = max(0, (temp - 25) / 20)  # Normalized temperature stress

        # Humidity multiplier
        humidity_multiplier = 1 + (humidity - 50) / 100

        # Environmental stress
        env_stress = temp_stress * humidity_multiplier

        # Worker-specific factors
        age_factor = 1 + (worker_profile.age - 30) / 100  # Older workers more susceptible
        fitness_factor = 1 - (worker_profile.fitness_level * 0.3)  # Fit workers more resilient
        tolerance_factor = 1 - (worker_profile.heat_tolerance * 0.4)  # Heat tolerance helps

        # Time-based accumulation (for scenarios)
        time_factor = 1 + time_progress * 0.5  # Stress accumulates over time

        # Combined stress factor
        stress_factor = env_stress * age_factor * fitness_factor * tolerance_factor * time_factor

        return min(2.0, max(0.1, stress_factor))  # Clamp between 0.1 and 2.0

    def _generate_hrv_features(self,
                             worker_profile: WorkerProfile,
                             stress_factor: float) -> Dict[str, float]:
        """Generate realistic HRV features based on worker profile and stress."""
        hrv_data = {}

        # Base heart rate adjusted for stress
        base_hr = worker_profile.base_heart_rate
        stressed_hr = base_hr * (1 + stress_factor * 0.4)  # HR increases with stress
        stressed_hr = min(180, max(50, stressed_hr))  # Physiological limits

        hrv_data['hrv_mean_hr'] = stressed_hr
        hrv_data['hrv_min_hr'] = stressed_hr * 0.85
        hrv_data['hrv_max_hr'] = stressed_hr * 1.25
        hrv_data['hrv_std_hr'] = stressed_hr * 0.15

        # HRV decreases with stress
        base_hrv = worker_profile.base_hrv
        stressed_rmssd = base_hrv * (1 - stress_factor * 0.6)  # HRV decreases with stress
        stressed_rmssd = max(10, stressed_rmssd)  # Minimum HRV

        # Time domain features
        mean_nni = 60000 / stressed_hr  # Convert HR to NN intervals
        hrv_data['hrv_mean_nni'] = mean_nni
        hrv_data['hrv_median_nni'] = mean_nni * self.rng.uniform(0.95, 1.05)
        hrv_data['hrv_rmssd'] = stressed_rmssd
        hrv_data['hrv_sdnn'] = stressed_rmssd * self.rng.uniform(1.5, 2.5)
        hrv_data['hrv_sdsd'] = stressed_rmssd * self.rng.uniform(0.8, 1.2)

        # Generate other features with realistic correlations
        for feature in self.feature_columns:
            if feature.startswith('hrv_') and feature not in hrv_data:
                if feature in self.feature_ranges:
                    min_val, max_val = self.feature_ranges[feature]

                    # Apply stress-related modifications
                    if 'power' in feature or 'energy' in feature:
                        # Power features decrease with stress
                        base_val = self.rng.uniform(min_val, max_val)
                        stressed_val = base_val * (1 - stress_factor * 0.3)
                        hrv_data[feature] = max(min_val * 0.1, stressed_val)
                    elif 'ratio' in feature:
                        # Ratio features change with stress
                        hrv_data[feature] = self.rng.uniform(min_val, max_val) * (1 + stress_factor * 0.2)
                    else:
                        # Default generation with stress influence
                        base_val = self.rng.uniform(min_val, max_val)
                        stress_influence = self.rng.uniform(-0.2, 0.2) * stress_factor
                        hrv_data[feature] = base_val * (1 + stress_influence)
                        hrv_data[feature] = max(min_val, min(max_val, hrv_data[feature]))

        return hrv_data

    def generate_dataframe(self,
                          count: int,
                          scenario_type: str = 'random',
                          **kwargs) -> pd.DataFrame:
        """
        Generate data as a pandas DataFrame.

        Args:
            count: Number of samples
            scenario_type: Type of scenario ('random', 'ramp_up', 'ramp_down')
            **kwargs: Additional arguments passed to generation methods

        Returns:
            DataFrame with generated data
        """
        if scenario_type == 'random':
            samples = self.generate_batch_samples(count, **kwargs)
        elif scenario_type == 'ramp_up':
            samples = self.generate_ramp_up_scenario(**kwargs)
        elif scenario_type == 'ramp_down':
            samples = self.generate_ramp_down_scenario(**kwargs)
        else:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        df = pd.DataFrame(samples)

        # Ensure all required features are present
        for feature in self.feature_columns:
            if feature not in df.columns:
                if feature in self.feature_ranges:
                    min_val, max_val = self.feature_ranges[feature]
                    df[feature] = self.rng.uniform(min_val, max_val, len(df))
                else:
                    df[feature] = 0.0

        return df

    def get_generator_info(self) -> Dict[str, Any]:
        """Get information about the data generator."""
        return {
            'generator_version': '1.0.0',
            'total_features': len(self.feature_columns),
            'worker_profiles': len(self.worker_profiles),
            'supported_scenarios': ['random', 'ramp_up', 'ramp_down'],
            'risk_levels': ['safe', 'caution', 'warning', 'danger'],
            'feature_ranges': {k: list(v) for k, v in list(self.feature_ranges.items())[:10]}  # Sample
        }