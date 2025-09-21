"""
Prediction API Endpoints
=========================

REST API endpoints for heat exposure predictions.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import time
import uuid
from datetime import datetime

from ..services.prediction_service import PredictionService
from ..services.batch_service import BatchService
from ..utils.validators import ValidationError
from ..utils.logger import get_logger, log_api_request
from ..config.settings import settings
from ..middleware.auth import get_current_user, APIKeyHeader

logger = get_logger(__name__)

# Create router
prediction_bp = APIRouter(prefix="/api/v1", tags=["predictions"])

# Service instances
prediction_service = PredictionService()
batch_service = BatchService()


# Pydantic models for request/response
class WorkerData(BaseModel):
    """Worker biometric and environmental data."""
    worker_id: Optional[str] = Field(None, description="Worker identifier")
    Age: float = Field(..., ge=16, le=80, description="Worker age in years")
    Gender: int = Field(..., ge=0, le=1, description="Gender (0=Female, 1=Male)")
    Temperature: float = Field(..., ge=-20, le=50, description="Temperature in Celsius")
    Humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")

    # Heart rate features (required)
    hrv_mean_hr: float = Field(..., ge=30, le=220, description="Average heart rate (BPM)")
    hrv_mean_nni: Optional[float] = Field(None, ge=200, le=2000, description="Mean NN interval (ms)")

    # Optional HRV features
    hrv_rmssd: Optional[float] = Field(None, ge=0, description="RMSSD HRV metric")
    hrv_sdnn: Optional[float] = Field(None, ge=0, description="SDNN HRV metric")
    hrv_total_power: Optional[float] = Field(None, ge=0, description="Total HRV power")
    hrv_lf: Optional[float] = Field(None, ge=0, description="Low frequency power")
    hrv_hf: Optional[float] = Field(None, ge=0, description="High frequency power")
    hrv_lf_hf_ratio: Optional[float] = Field(None, ge=0, description="LF/HF ratio")

    # Additional optional features can be included
    class Config:
        extra = "allow"  # Allow additional HRV features
        schema_extra = {
            "example": {
                "worker_id": "worker_001",
                "Age": 30,
                "Gender": 1,
                "Temperature": 32.5,
                "Humidity": 75.0,
                "hrv_mean_hr": 85.0,
                "hrv_mean_nni": 706.0,
                "hrv_rmssd": 25.5,
                "hrv_sdnn": 45.2
            }
        }

    @validator('worker_id', pre=True, always=True)
    def generate_worker_id(cls, v):
        """Generate worker ID if not provided."""
        if not v:
            return f"worker_{int(time.time() * 1000)}"
        return v


class PredictionOptions(BaseModel):
    """Options for prediction requests."""
    use_conservative: bool = Field(True, description="Apply conservative bias for safety")
    log_compliance: bool = Field(True, description="Log prediction for OSHA compliance")


class SinglePredictionRequest(BaseModel):
    """Request model for single worker prediction."""
    data: WorkerData
    options: Optional[PredictionOptions] = PredictionOptions()


class BatchPredictionRequest(BaseModel):
    """Request model for batch worker predictions."""
    data: List[WorkerData] = Field(..., min_items=1, max_items=1000)
    options: Optional[PredictionOptions] = PredictionOptions()
    parallel_processing: bool = Field(True, description="Process predictions in parallel")


class PredictionResponse(BaseModel):
    """Response model for single prediction."""
    request_id: str
    worker_id: str
    timestamp: str
    heat_exposure_risk_score: float = Field(..., ge=0, le=1)
    risk_level: str
    confidence: float = Field(..., ge=0, le=1)

    # Environmental data
    temperature_celsius: float
    temperature_fahrenheit: float
    humidity_percent: float
    heat_index: float

    # Safety information
    osha_recommendations: List[str]
    requires_immediate_attention: bool

    # Processing metadata
    processing_time_ms: float
    data_quality_score: Optional[float]
    validation_warnings: Optional[List[str]]


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions."""
    request_id: str
    batch_size: int
    successful_predictions: int
    failed_predictions: int
    processing_time_ms: float
    batch_statistics: Dict[str, Any]
    predictions: List[PredictionResponse]
    validation_warnings: Optional[List[str]]


# API Endpoints

@prediction_bp.post("/predict", response_model=PredictionResponse,
                   summary="Predict heat exposure risk for single worker")
async def predict_single_worker(
    request: SinglePredictionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(APIKeyHeader)
) -> PredictionResponse:
    """
    Predict heat exposure risk for a single worker based on biometric and environmental data.

    This endpoint analyzes real-time wearable device data and environmental conditions to
    assess heat exposure risk and provide OSHA-compliant safety recommendations.

    - **Worker Data**: Biometric data from wearable devices and environmental sensors
    - **Risk Assessment**: Returns risk score (0-1) and categorical risk level
    - **Safety Recommendations**: OSHA-compliant recommendations based on risk level
    - **OSHA Compliance**: Automatically logs predictions for compliance reporting
    """
    start_time = time.time()

    try:
        # Convert Pydantic model to dict
        worker_data = request.data.dict()
        options = request.options.dict() if request.options else {}

        # Make prediction
        result = await prediction_service.predict_single_worker(
            worker_data,
            use_conservative=options.get('use_conservative', True),
            log_compliance=options.get('log_compliance', True)
        )

        # Log API request
        response_time = time.time() - start_time
        background_tasks.add_task(
            log_api_request,
            endpoint="/api/v1/predict",
            method="POST",
            status_code=200,
            response_time=response_time,
            user_id=None,  # Could extract from API key
            request_id=result.get('request_id')
        )

        return PredictionResponse(**result)

    except ValidationError as e:
        logger.error(f"Validation error in single prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Input validation failed: {e}"
        )
    except Exception as e:
        logger.error(f"Error in single prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during prediction"
        )


@prediction_bp.post("/predict_batch", response_model=BatchPredictionResponse,
                   summary="Predict heat exposure risk for multiple workers")
async def predict_batch_workers(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(APIKeyHeader)
) -> BatchPredictionResponse:
    """
    Predict heat exposure risk for multiple workers in a single request.

    Efficiently processes multiple worker assessments with batch optimization and
    parallel processing capabilities.

    - **Batch Processing**: Handle up to 1000 workers per request
    - **Parallel Processing**: Optional parallel processing for faster results
    - **Batch Statistics**: Aggregated risk analysis across all workers
    - **OSHA Compliance**: Batch compliance logging for all predictions
    """
    start_time = time.time()

    try:
        # Convert Pydantic models to dicts
        worker_data_list = [worker.dict() for worker in request.data]
        options = request.options.dict() if request.options else {}

        # Make batch prediction
        result = await prediction_service.predict_multiple_workers(
            worker_data_list,
            use_conservative=options.get('use_conservative', True),
            log_compliance=options.get('log_compliance', True),
            parallel=request.parallel_processing
        )

        # Log API request
        response_time = time.time() - start_time
        background_tasks.add_task(
            log_api_request,
            endpoint="/api/v1/predict_batch",
            method="POST",
            status_code=200,
            response_time=response_time,
            user_id=None,
            request_id=result.get('request_id')
        )

        return BatchPredictionResponse(**result)

    except ValidationError as e:
        logger.error(f"Validation error in batch prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Batch validation failed: {e}"
        )
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during batch prediction"
        )


# Async Batch Processing Endpoints

class AsyncBatchRequest(BaseModel):
    """Request model for asynchronous batch processing."""
    data: List[WorkerData] = Field(..., min_items=1, max_items=10000)
    options: Optional[PredictionOptions] = PredictionOptions()
    chunk_size: int = Field(100, ge=10, le=1000, description="Processing chunk size")
    priority: str = Field("normal", regex="^(low|normal|high)$")


class AsyncBatchResponse(BaseModel):
    """Response model for async batch job submission."""
    job_id: str
    status: str
    message: str
    batch_size: int
    estimated_completion_time: Optional[str]


@prediction_bp.post("/predict_batch_async", response_model=AsyncBatchResponse,
                   summary="Submit large batch for asynchronous processing")
async def submit_async_batch_prediction(
    request: AsyncBatchRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(APIKeyHeader)
) -> AsyncBatchResponse:
    """
    Submit a large batch of workers for asynchronous processing.

    For large datasets (>1000 workers), this endpoint provides asynchronous processing
    with job tracking and status monitoring capabilities.

    - **Large Batches**: Handle up to 10,000 workers per job
    - **Job Tracking**: Returns job ID for monitoring progress
    - **Chunk Processing**: Configurable chunk size for optimal performance
    - **Priority Queuing**: Set job priority for processing order
    """
    start_time = time.time()

    try:
        # Convert Pydantic models to dicts
        worker_data_list = [worker.dict() for worker in request.data]

        # Submit batch job
        job_id = await batch_service.submit_batch_job(
            data=worker_data_list,
            use_conservative=request.options.use_conservative,
            log_compliance=request.options.log_compliance,
            chunk_size=request.chunk_size,
            priority=request.priority
        )

        # Estimate completion time (rough calculation)
        batch_size = len(worker_data_list)
        estimated_seconds = (batch_size / 100) * 30  # Rough estimate
        estimated_completion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log API request
        response_time = time.time() - start_time
        background_tasks.add_task(
            log_api_request,
            endpoint="/api/v1/predict_batch_async",
            method="POST",
            status_code=202,
            response_time=response_time,
            user_id=None,
            request_id=job_id
        )

        return AsyncBatchResponse(
            job_id=job_id,
            status="submitted",
            message="Batch job submitted successfully",
            batch_size=batch_size,
            estimated_completion_time=estimated_completion
        )

    except Exception as e:
        logger.error(f"Error submitting async batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit batch job"
        )


@prediction_bp.get("/batch_status/{job_id}",
                  summary="Get status of asynchronous batch job")
async def get_batch_job_status(
    job_id: str,
    api_key: str = Depends(APIKeyHeader)
) -> JSONResponse:
    """
    Get the current status of an asynchronous batch processing job.

    Returns detailed information about job progress, completion status,
    and any errors encountered during processing.
    """
    try:
        status_info = await batch_service.get_job_status(job_id)

        if status_info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        return JSONResponse(content=status_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job status"
        )


@prediction_bp.get("/batch_results/{job_id}",
                  summary="Get results of completed batch job")
async def get_batch_job_results(
    job_id: str,
    api_key: str = Depends(APIKeyHeader)
) -> JSONResponse:
    """
    Get the results of a completed asynchronous batch processing job.

    Returns all prediction results and processing statistics for the batch job.
    """
    try:
        results = await batch_service.get_job_results(job_id)

        if results is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        return JSONResponse(content=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving job results"
        )


@prediction_bp.delete("/batch_job/{job_id}",
                     summary="Cancel asynchronous batch job")
async def cancel_batch_job(
    job_id: str,
    api_key: str = Depends(APIKeyHeader)
) -> JSONResponse:
    """
    Cancel an active asynchronous batch processing job.

    Stops processing of the specified job if it's still running or pending.
    """
    try:
        cancelled = await batch_service.cancel_job(job_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or cannot be cancelled"
            )

        return JSONResponse(
            content={
                "job_id": job_id,
                "status": "cancelled",
                "message": "Job cancelled successfully"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error cancelling job"
        )


@prediction_bp.get("/batch_jobs",
                  summary="List batch jobs")
async def list_batch_jobs(
    status_filter: Optional[str] = None,
    limit: int = Field(50, ge=1, le=200),
    api_key: str = Depends(APIKeyHeader)
) -> JSONResponse:
    """
    List batch processing jobs with optional status filtering.

    Returns a list of batch jobs with their current status and metadata.
    """
    try:
        jobs = await batch_service.list_jobs(status_filter, limit)

        return JSONResponse(
            content={
                "jobs": jobs,
                "total_count": len(jobs),
                "status_filter": status_filter,
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing batch jobs"
        )