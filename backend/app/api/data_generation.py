"""
Data Generation API Endpoints
==============================

API endpoints for generating test data and simulation scenarios.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

from ..models.data_generator import DataGenerator, WorkerProfile
from ..utils.logger import get_logger, log_api_request
from ..middleware.auth import APIKeyHeader

logger = get_logger(__name__)

# Create router
data_generation_bp = APIRouter(prefix="/api/v1", tags=["data_generation"])

# Data generator instance
data_generator = DataGenerator()


# Request/Response models
class RandomDataRequest(BaseModel):
    """Request model for random data generation."""
    count: int = Field(default=10, ge=1, le=1000, description="Number of samples to generate")
    risk_distribution: Optional[Dict[str, float]] = Field(
        default=None,
        description="Risk level distribution {'safe': 0.4, 'caution': 0.3, 'warning': 0.2, 'danger': 0.1}"
    )
    seed: Optional[int] = Field(default=None, description="Random seed for reproducible results")

    @validator('risk_distribution')
    def validate_risk_distribution(cls, v):
        if v is not None:
            # Check that probabilities sum to approximately 1.0
            total = sum(v.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError("Risk distribution probabilities must sum to 1.0")

            # Check valid risk levels
            valid_levels = {'safe', 'caution', 'warning', 'danger'}
            if not all(level in valid_levels for level in v.keys()):
                raise ValueError(f"Risk levels must be from {valid_levels}")
        return v


class ScenarioRequest(BaseModel):
    """Request model for scenario-based data generation."""
    duration_minutes: int = Field(default=60, ge=5, le=480, description="Scenario duration in minutes")
    interval_minutes: int = Field(default=5, ge=1, le=30, description="Measurement interval in minutes")
    worker_age: Optional[int] = Field(default=None, ge=18, le=65, description="Specific worker age")
    worker_gender: Optional[int] = Field(default=None, ge=0, le=1, description="Worker gender (0=Female, 1=Male)")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducible results")


class GeneratedDataResponse(BaseModel):
    """Response model for generated data."""
    request_id: str
    generation_type: str
    count: int
    generation_time_ms: float
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: str


class DataGeneratorInfo(BaseModel):
    """Information about the data generator."""
    generator_version: str
    total_features: int
    worker_profiles: int
    supported_scenarios: List[str]
    risk_levels: List[str]
    feature_sample: Dict[str, List[float]]


@data_generation_bp.get("/generate_random", response_model=GeneratedDataResponse,
                       summary="Generate random test data")
async def generate_random_data(
    count: int = Field(default=10, ge=1, le=1000),
    risk_distribution: Optional[str] = Field(default=None, description="JSON string of risk distribution"),
    seed: Optional[int] = None,
    api_key: str = Depends(APIKeyHeader)
) -> GeneratedDataResponse:
    """
    Generate random test data for heat exposure prediction testing.

    Creates realistic synthetic data with configurable risk level distribution.
    Perfect for API testing, load testing, and system validation.

    - **Configurable Count**: Generate 1-1000 samples per request
    - **Risk Distribution**: Control the distribution of risk levels
    - **Reproducible**: Use seed parameter for consistent results
    - **Realistic Data**: Based on actual physiological and environmental patterns
    """
    start_time = time.time()
    request_id = f"random_{int(time.time() * 1000)}"

    try:
        logger.info(f"Generating {count} random samples", request_id=request_id)

        # Parse risk distribution if provided
        parsed_risk_dist = None
        if risk_distribution:
            import json
            try:
                parsed_risk_dist = json.loads(risk_distribution)
                # Validate distribution
                total = sum(parsed_risk_dist.values())
                if abs(total - 1.0) > 0.01:
                    raise ValueError("Risk distribution must sum to 1.0")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid risk distribution: {e}"
                )

        # Create data generator with seed
        generator = DataGenerator(seed=seed)

        # Generate data
        generated_data = generator.generate_batch_samples(
            count=count,
            risk_distribution=parsed_risk_dist
        )

        generation_time = time.time() - start_time

        # Create response
        response = GeneratedDataResponse(
            request_id=request_id,
            generation_type="random",
            count=len(generated_data),
            generation_time_ms=round(generation_time * 1000, 2),
            data=generated_data,
            metadata={
                "risk_distribution_used": parsed_risk_dist or "default",
                "seed_used": seed,
                "features_per_sample": len(generator.feature_columns),
                "generator_info": generator.get_generator_info()
            },
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Generated {count} random samples successfully",
                   request_id=request_id, generation_time=generation_time)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating random data: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate random data: {e}"
        )


@data_generation_bp.get("/generate_ramp_up", response_model=GeneratedDataResponse,
                       summary="Generate escalating risk scenario")
async def generate_ramp_up_scenario(
    duration_minutes: int = Field(default=60, ge=5, le=480),
    interval_minutes: int = Field(default=5, ge=1, le=30),
    worker_age: Optional[int] = Field(default=None, ge=18, le=65),
    worker_gender: Optional[int] = Field(default=None, ge=0, le=1),
    seed: Optional[int] = None,
    api_key: str = Depends(APIKeyHeader)
) -> GeneratedDataResponse:
    """
    Generate escalating heat exposure risk scenario (green → red).

    Simulates a worker's physiological response as environmental conditions
    progressively worsen over time. Perfect for testing alert systems and
    monitoring heat stress progression.

    - **Progressive Risk**: Conditions gradually worsen from safe to dangerous
    - **Realistic Timeline**: Configurable duration and measurement intervals
    - **Worker Profiles**: Specify age and gender for realistic responses
    - **Physiological Accuracy**: Heart rate and HRV respond to increasing heat stress
    """
    start_time = time.time()
    request_id = f"rampup_{int(time.time() * 1000)}"

    try:
        logger.info(f"Generating ramp-up scenario: {duration_minutes}min, {interval_minutes}min intervals",
                   request_id=request_id)

        # Create worker profile if specified
        worker_profile = None
        if worker_age is not None or worker_gender is not None:
            # Use defaults if not specified
            age = worker_age or 30
            gender = worker_gender if worker_gender is not None else 1

            worker_profile = WorkerProfile(
                age=age,
                gender=gender,
                fitness_level=0.6,  # Average fitness
                heat_tolerance=0.5,  # Average heat tolerance
                base_heart_rate=70.0,
                base_hrv=35.0
            )

        # Create data generator with seed
        generator = DataGenerator(seed=seed)

        # Generate ramp-up scenario
        generated_data = generator.generate_ramp_up_scenario(
            duration_minutes=duration_minutes,
            interval_minutes=interval_minutes,
            worker_profile=worker_profile
        )

        generation_time = time.time() - start_time

        # Create response
        response = GeneratedDataResponse(
            request_id=request_id,
            generation_type="ramp_up",
            count=len(generated_data),
            generation_time_ms=round(generation_time * 1000, 2),
            data=generated_data,
            metadata={
                "scenario_type": "escalating_risk",
                "duration_minutes": duration_minutes,
                "interval_minutes": interval_minutes,
                "measurements_count": len(generated_data),
                "worker_profile": {
                    "age": worker_profile.age if worker_profile else "random",
                    "gender": worker_profile.gender if worker_profile else "random"
                },
                "seed_used": seed,
                "risk_progression": "safe → danger"
            },
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Generated ramp-up scenario with {len(generated_data)} measurements",
                   request_id=request_id, generation_time=generation_time)

        return response

    except Exception as e:
        logger.error(f"Error generating ramp-up scenario: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ramp-up scenario: {e}"
        )


@data_generation_bp.get("/generate_ramp_down", response_model=GeneratedDataResponse,
                       summary="Generate de-escalating risk scenario")
async def generate_ramp_down_scenario(
    duration_minutes: int = Field(default=60, ge=5, le=480),
    interval_minutes: int = Field(default=5, ge=1, le=30),
    worker_age: Optional[int] = Field(default=None, ge=18, le=65),
    worker_gender: Optional[int] = Field(default=None, ge=0, le=1),
    seed: Optional[int] = None,
    api_key: str = Depends(APIKeyHeader)
) -> GeneratedDataResponse:
    """
    Generate de-escalating heat exposure risk scenario (red → green).

    Simulates a worker's recovery as environmental conditions improve or as
    they move to cooler environments. Useful for testing recovery monitoring
    and cool-down protocols.

    - **Progressive Recovery**: Conditions gradually improve from dangerous to safe
    - **Recovery Patterns**: Realistic physiological recovery responses
    - **Worker Profiles**: Age and gender affect recovery rates
    - **Monitoring Validation**: Test systems that track worker recovery
    """
    start_time = time.time()
    request_id = f"rampdown_{int(time.time() * 1000)}"

    try:
        logger.info(f"Generating ramp-down scenario: {duration_minutes}min, {interval_minutes}min intervals",
                   request_id=request_id)

        # Create worker profile if specified
        worker_profile = None
        if worker_age is not None or worker_gender is not None:
            age = worker_age or 30
            gender = worker_gender if worker_gender is not None else 1

            worker_profile = WorkerProfile(
                age=age,
                gender=gender,
                fitness_level=0.6,
                heat_tolerance=0.5,
                base_heart_rate=70.0,
                base_hrv=35.0
            )

        # Create data generator with seed
        generator = DataGenerator(seed=seed)

        # Generate ramp-down scenario
        generated_data = generator.generate_ramp_down_scenario(
            duration_minutes=duration_minutes,
            interval_minutes=interval_minutes,
            worker_profile=worker_profile
        )

        generation_time = time.time() - start_time

        # Create response
        response = GeneratedDataResponse(
            request_id=request_id,
            generation_type="ramp_down",
            count=len(generated_data),
            generation_time_ms=round(generation_time * 1000, 2),
            data=generated_data,
            metadata={
                "scenario_type": "de-escalating_risk",
                "duration_minutes": duration_minutes,
                "interval_minutes": interval_minutes,
                "measurements_count": len(generated_data),
                "worker_profile": {
                    "age": worker_profile.age if worker_profile else "random",
                    "gender": worker_profile.gender if worker_profile else "random"
                },
                "seed_used": seed,
                "risk_progression": "danger → safe"
            },
            timestamp=datetime.now().isoformat()
        )

        logger.info(f"Generated ramp-down scenario with {len(generated_data)} measurements",
                   request_id=request_id, generation_time=generation_time)

        return response

    except Exception as e:
        logger.error(f"Error generating ramp-down scenario: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate ramp-down scenario: {e}"
        )


@data_generation_bp.post("/generate_batch", response_model=GeneratedDataResponse,
                        summary="Generate data using detailed request")
async def generate_batch_data(
    request: RandomDataRequest,
    api_key: str = Depends(APIKeyHeader)
) -> GeneratedDataResponse:
    """
    Generate batch data with detailed configuration options.

    Provides full control over data generation parameters including
    risk distribution, worker characteristics, and randomization settings.
    """
    start_time = time.time()
    request_id = f"batch_{int(time.time() * 1000)}"

    try:
        logger.info(f"Generating batch data: {request.count} samples",
                   request_id=request_id)

        # Create data generator with seed
        generator = DataGenerator(seed=request.seed)

        # Generate data
        generated_data = generator.generate_batch_samples(
            count=request.count,
            risk_distribution=request.risk_distribution
        )

        generation_time = time.time() - start_time

        # Create response
        response = GeneratedDataResponse(
            request_id=request_id,
            generation_type="batch_configured",
            count=len(generated_data),
            generation_time_ms=round(generation_time * 1000, 2),
            data=generated_data,
            metadata={
                "request_parameters": request.dict(),
                "features_per_sample": len(generator.feature_columns),
                "generator_info": generator.get_generator_info()
            },
            timestamp=datetime.now().isoformat()
        )

        return response

    except Exception as e:
        logger.error(f"Error generating batch data: {e}", request_id=request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch data: {e}"
        )


@data_generation_bp.get("/generator_info", response_model=DataGeneratorInfo,
                       summary="Get data generator information")
async def get_generator_info(
    api_key: str = Depends(APIKeyHeader)
) -> DataGeneratorInfo:
    """
    Get detailed information about the data generator capabilities.

    Returns information about supported features, scenarios, and configuration options
    for the synthetic data generation system.
    """
    try:
        generator_info = data_generator.get_generator_info()

        return DataGeneratorInfo(
            generator_version=generator_info["generator_version"],
            total_features=generator_info["total_features"],
            worker_profiles=generator_info["worker_profiles"],
            supported_scenarios=generator_info["supported_scenarios"],
            risk_levels=generator_info["risk_levels"],
            feature_sample=generator_info["feature_ranges"]
        )

    except Exception as e:
        logger.error(f"Error getting generator info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generator info: {e}"
        )


@data_generation_bp.get("/feature_template",
                       summary="Get feature template for data structure")
async def get_feature_template(
    api_key: str = Depends(APIKeyHeader)
) -> JSONResponse:
    """
    Get a template showing the expected data structure for predictions.

    Returns a sample data structure with all required and optional features
    that can be used as a template for API requests.
    """
    try:
        # Generate a single sample to show structure
        sample = data_generator.generate_random_sample()

        # Remove generated fields to show clean template
        template = {k: v for k, v in sample.items()
                   if not k.startswith('sample_') and k != 'worker_id'}

        return JSONResponse(
            content={
                "feature_template": template,
                "required_features": [
                    "Age", "Gender", "Temperature", "Humidity",
                    "hrv_mean_hr", "hrv_mean_nni"
                ],
                "feature_descriptions": {
                    "Age": "Worker age in years (18-65)",
                    "Gender": "Worker gender (0=Female, 1=Male)",
                    "Temperature": "Environmental temperature in Celsius",
                    "Humidity": "Relative humidity as percentage (0-100)",
                    "hrv_mean_hr": "Average heart rate in beats per minute",
                    "hrv_mean_nni": "Mean NN interval in milliseconds"
                },
                "total_features": len(template),
                "data_types": {
                    "demographics": ["Age", "Gender"],
                    "environmental": ["Temperature", "Humidity"],
                    "physiological": [k for k in template.keys() if k.startswith("hrv_")]
                }
            }
        )

    except Exception as e:
        logger.error(f"Error getting feature template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feature template: {e}"
        )