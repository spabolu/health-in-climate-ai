"""
HeatGuard Predictive Safety System
==================================

A production-grade heat exposure prediction API that helps companies with
heat-exposed workforces boost productivity by 20% while keeping employees safe.

The system provides real-time predictive insights into worker health and
environmental risks, saving businesses millions in lost labor hours and
medical costs while addressing a $1B annual healthcare burden.
"""

__version__ = "1.0.0"
__author__ = "HeatGuard Team"

from .models.heat_predictor import HeatExposurePredictor
from .config.settings import settings

__all__ = [
    "HeatExposurePredictor",
    "settings",
]