"""
API Package
===========

Contains all REST API endpoints for the HeatGuard system.
"""

from .prediction import prediction_bp
from .health import health_bp
from .data_generation import data_generation_bp

__all__ = [
    "prediction_bp",
    "health_bp",
    "data_generation_bp",
]