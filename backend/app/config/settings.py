"""
Application Configuration
========================

Central configuration management for the HeatGuard system.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "HeatGuard Predictive Safety System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Real-time heat exposure prediction API for workforce safety"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    RELOAD: bool = False

    # Security Configuration
    SECRET_KEY: str = "heatguard-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    API_KEY_HEADER: str = "X-API-Key"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://localhost:3000",
        "https://localhost:8080",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Configuration (for future use)
    DATABASE_URL: Optional[str] = None

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL: int = 300  # 5 minutes

    # Model Configuration
    MODEL_DIR: str = "thermal_comfort_model"
    MODEL_CACHE_SIZE: int = 10
    PREDICTION_TIMEOUT: int = 30  # seconds

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None

    # OSHA Compliance Configuration
    ENABLE_OSHA_LOGGING: bool = True
    OSHA_LOG_FILE: str = "logs/osha_compliance.log"
    HEAT_INDEX_THRESHOLD_WARNING: float = 80.0  # °F
    HEAT_INDEX_THRESHOLD_DANGER: float = 90.0   # °F

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    BATCH_SIZE_LIMIT: int = 1000

    # Monitoring and Health Checks
    HEALTH_CHECK_TIMEOUT: int = 5
    METRICS_ENABLED: bool = True

    # Feature Engineering
    CONSERVATIVE_BIAS: float = 0.15
    ENABLE_FEATURE_SCALING: bool = True
    HANDLE_MISSING_VALUES: bool = True

    # Wearable Device Integration
    DEVICE_DATA_TIMEOUT: int = 10  # seconds
    ENABLE_REAL_TIME_STREAMING: bool = True
    MAX_CONCURRENT_PREDICTIONS: int = 100

    # Environment-specific overrides
    @validator("SECRET_KEY", pre=True)
    def validate_secret_key(cls, v):
        if v == "heatguard-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "Using default secret key. Change this in production!",
                UserWarning
            )
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    RELOAD: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    RELOAD: bool = False
    LOG_LEVEL: str = "WARNING"
    SECRET_KEY: str = os.getenv("SECRET_KEY", settings.SECRET_KEY)


class TestingSettings(Settings):
    """Testing environment settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6380"  # Different Redis instance for testing


def get_settings() -> Settings:
    """Get settings based on environment."""
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


# Use environment-specific settings
settings = get_settings()