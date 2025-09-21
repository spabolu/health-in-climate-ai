"""
Health Check API Endpoints
===========================

System health monitoring and status endpoints for the HeatGuard system.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import psutil
import platform
import time

from ..services.prediction_service import PredictionService
from ..services.batch_service import BatchService
from ..services.compliance_service import ComplianceService
from ..models.model_loader import model_loader
from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Create router
health_bp = APIRouter(prefix="/api/v1", tags=["health"])

# Service instances
prediction_service = PredictionService()
batch_service = BatchService()
compliance_service = ComplianceService()


# Response models
class HealthStatus(BaseModel):
    """Health status response model."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    uptime_seconds: float


class SystemInfo(BaseModel):
    """System information response model."""
    platform: str
    python_version: str
    cpu_count: int
    memory_total_gb: float
    memory_available_gb: float
    cpu_usage_percent: float
    disk_usage_percent: float


class ModelStatus(BaseModel):
    """Model status response model."""
    model_loaded: bool
    model_type: str
    load_time: Optional[str]
    feature_count: int
    target_classes: List[str]
    performance_ok: bool


class ServiceStatus(BaseModel):
    """Individual service status."""
    service_name: str
    status: str
    last_check: str
    details: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    """Complete health check response."""
    overall_status: HealthStatus
    system_info: SystemInfo
    model_status: ModelStatus
    services: List[ServiceStatus]
    configuration: Dict[str, Any]


# Global variables for tracking
_start_time = time.time()
_last_health_check = None
_health_cache_duration = 30  # seconds


@health_bp.get("/health", response_model=HealthCheckResponse,
               summary="Comprehensive system health check")
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for the HeatGuard Predictive Safety System.

    Returns detailed information about:
    - Overall system health status
    - Model loading and performance status
    - Individual service health
    - System resource utilization
    - Configuration status

    This endpoint is used for monitoring, alerting, and ensuring system reliability.
    """
    global _last_health_check

    try:
        current_time = time.time()

        # Check if we have a recent cached result
        if (_last_health_check and
            (current_time - _last_health_check.get('timestamp', 0)) < _health_cache_duration):
            return _last_health_check['result']

        # Perform comprehensive health check
        health_result = await _perform_health_check()

        # Cache the result
        _last_health_check = {
            'timestamp': current_time,
            'result': health_result
        }

        return health_result

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        # Return minimal health status on error
        return HealthCheckResponse(
            overall_status=HealthStatus(
                status="unhealthy",
                timestamp=datetime.now().isoformat(),
                version=settings.VERSION,
                uptime_seconds=time.time() - _start_time
            ),
            system_info=SystemInfo(
                platform="unknown",
                python_version="unknown",
                cpu_count=0,
                memory_total_gb=0.0,
                memory_available_gb=0.0,
                cpu_usage_percent=0.0,
                disk_usage_percent=0.0
            ),
            model_status=ModelStatus(
                model_loaded=False,
                model_type="unknown",
                load_time=None,
                feature_count=0,
                target_classes=[],
                performance_ok=False
            ),
            services=[],
            configuration={"error": str(e)}
        )


@health_bp.get("/health/simple",
               summary="Simple health check")
async def simple_health_check() -> JSONResponse:
    """
    Simple health check endpoint for load balancers and basic monitoring.

    Returns a minimal status indication with HTTP status codes:
    - 200: System is healthy
    - 503: System is unhealthy or degraded
    """
    try:
        # Quick checks only
        model_ok = model_loader.is_model_loaded("default")

        if model_ok:
            return JSONResponse(
                content={
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": settings.VERSION
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "status": "degraded",
                    "timestamp": datetime.now().isoformat(),
                    "reason": "Model not loaded"
                },
                status_code=503
            )

    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            status_code=503
        )


@health_bp.get("/health/model",
               summary="Model-specific health check")
async def model_health_check() -> JSONResponse:
    """
    Detailed health check specifically for the machine learning model.

    Returns information about:
    - Model loading status
    - Model performance metrics
    - Feature availability
    - Prediction capabilities
    """
    try:
        # Get model health from loader
        model_health = model_loader.health_check()

        # Get model info if available
        model_info = {}
        if model_loader.is_model_loaded("default"):
            model = model_loader.get_model("default")
            if model:
                model_info = model.get_model_info()

        return JSONResponse(
            content={
                "model_loader_status": model_health,
                "model_info": model_info,
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )


@health_bp.get("/health/services",
               summary="Service-specific health checks")
async def services_health_check() -> JSONResponse:
    """
    Health check for individual services within the HeatGuard system.

    Checks the status of:
    - Prediction Service
    - Batch Processing Service
    - Compliance Service
    """
    try:
        services_status = []

        # Check Prediction Service
        try:
            pred_health = prediction_service.get_service_health()
            services_status.append({
                "service_name": "PredictionService",
                "status": pred_health.get("status", "unknown"),
                "details": pred_health,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            services_status.append({
                "service_name": "PredictionService",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        # Check Batch Service
        try:
            batch_stats = batch_service.get_service_statistics()
            services_status.append({
                "service_name": "BatchService",
                "status": "healthy",
                "details": batch_stats,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            services_status.append({
                "service_name": "BatchService",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        # Check Compliance Service
        try:
            compliance_status = compliance_service.get_compliance_status()
            services_status.append({
                "service_name": "ComplianceService",
                "status": "healthy" if compliance_status.get("compliance_logging_enabled") else "degraded",
                "details": compliance_status,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            services_status.append({
                "service_name": "ComplianceService",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

        return JSONResponse(
            content={
                "services": services_status,
                "overall_services_status": _determine_overall_services_status(services_status),
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )


@health_bp.get("/health/system",
               summary="System resource health check")
async def system_health_check() -> JSONResponse:
    """
    System resource monitoring and health check.

    Returns information about:
    - CPU usage and availability
    - Memory usage and availability
    - Disk usage
    - System load
    - Platform information
    """
    try:
        # Get system information
        system_info = _get_system_info()

        # Determine system health based on resource usage
        system_status = _determine_system_health(system_info)

        return JSONResponse(
            content={
                "system_status": system_status,
                "system_info": system_info.dict(),
                "thresholds": {
                    "cpu_warning_percent": 80,
                    "cpu_critical_percent": 95,
                    "memory_warning_percent": 80,
                    "memory_critical_percent": 95,
                    "disk_warning_percent": 85,
                    "disk_critical_percent": 95
                },
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=500
        )


@health_bp.get("/readiness",
               summary="Readiness check for container orchestration")
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint for Kubernetes and container orchestration.

    Returns:
    - 200: Service is ready to accept requests
    - 503: Service is not ready (still initializing)
    """
    try:
        # Check if critical components are ready
        model_ready = model_loader.is_model_loaded("default")

        if model_ready:
            return JSONResponse(
                content={
                    "ready": True,
                    "timestamp": datetime.now().isoformat()
                },
                status_code=200
            )
        else:
            return JSONResponse(
                content={
                    "ready": False,
                    "reason": "Model not loaded",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=503
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={
                "ready": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )


@health_bp.get("/liveness",
               summary="Liveness check for container orchestration")
async def liveness_check() -> JSONResponse:
    """
    Liveness check endpoint for Kubernetes and container orchestration.

    Returns:
    - 200: Service is alive and functioning
    - 503: Service is unresponsive (should be restarted)
    """
    try:
        # Basic liveness check - if we can respond, we're alive
        return JSONResponse(
            content={
                "alive": True,
                "uptime_seconds": time.time() - _start_time,
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )

    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return JSONResponse(
            content={
                "alive": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            },
            status_code=503
        )


# Helper functions

async def _perform_health_check() -> HealthCheckResponse:
    """Perform comprehensive health check."""

    # System info
    system_info = _get_system_info()
    system_status = _determine_system_health(system_info)

    # Model status
    model_health = model_loader.health_check()
    model_info = {}
    if model_loader.is_model_loaded("default"):
        model = model_loader.get_model("default")
        if model:
            model_info = model.get_model_info()

    model_status = ModelStatus(
        model_loaded=model_health.get("default_model_loaded", False),
        model_type=model_info.get("model_type", "XGBoost Heat Exposure Predictor"),
        load_time=None,  # Could be added to model info
        feature_count=model_info.get("feature_count", 0),
        target_classes=model_info.get("target_classes", []),
        performance_ok=model_health.get("status") == "healthy"
    )

    # Services status
    services = []

    # Prediction service
    try:
        pred_health = prediction_service.get_service_health()
        services.append(ServiceStatus(
            service_name="PredictionService",
            status=pred_health.get("status", "unknown"),
            last_check=datetime.now().isoformat(),
            details=pred_health
        ))
    except Exception as e:
        services.append(ServiceStatus(
            service_name="PredictionService",
            status="error",
            last_check=datetime.now().isoformat(),
            details={"error": str(e)}
        ))

    # Batch service
    try:
        batch_stats = batch_service.get_service_statistics()
        services.append(ServiceStatus(
            service_name="BatchService",
            status="healthy",
            last_check=datetime.now().isoformat(),
            details=batch_stats
        ))
    except Exception as e:
        services.append(ServiceStatus(
            service_name="BatchService",
            status="error",
            last_check=datetime.now().isoformat(),
            details={"error": str(e)}
        ))

    # Compliance service
    try:
        compliance_status = compliance_service.get_compliance_status()
        services.append(ServiceStatus(
            service_name="ComplianceService",
            status="healthy" if compliance_status.get("compliance_logging_enabled") else "degraded",
            last_check=datetime.now().isoformat(),
            details=compliance_status
        ))
    except Exception as e:
        services.append(ServiceStatus(
            service_name="ComplianceService",
            status="error",
            last_check=datetime.now().isoformat(),
            details={"error": str(e)}
        ))

    # Determine overall status
    overall_status = _determine_overall_status(system_status, model_status.performance_ok, services)

    # Configuration summary
    configuration = {
        "version": settings.VERSION,
        "debug_mode": settings.DEBUG,
        "osha_compliance_enabled": settings.ENABLE_OSHA_LOGGING,
        "max_batch_size": settings.BATCH_SIZE_LIMIT,
        "conservative_bias": settings.CONSERVATIVE_BIAS,
        "cache_enabled": bool(settings.REDIS_URL)
    }

    return HealthCheckResponse(
        overall_status=HealthStatus(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            version=settings.VERSION,
            uptime_seconds=time.time() - _start_time
        ),
        system_info=system_info,
        model_status=model_status,
        services=services,
        configuration=configuration
    )


def _get_system_info() -> SystemInfo:
    """Get current system information."""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return SystemInfo(
            platform=platform.platform(),
            python_version=platform.python_version(),
            cpu_count=psutil.cpu_count(),
            memory_total_gb=round(memory.total / (1024**3), 2),
            memory_available_gb=round(memory.available / (1024**3), 2),
            cpu_usage_percent=round(psutil.cpu_percent(interval=1), 1),
            disk_usage_percent=round(disk.percent, 1)
        )
    except Exception as e:
        logger.warning(f"Could not get complete system info: {e}")
        return SystemInfo(
            platform="unknown",
            python_version=platform.python_version(),
            cpu_count=1,
            memory_total_gb=0.0,
            memory_available_gb=0.0,
            cpu_usage_percent=0.0,
            disk_usage_percent=0.0
        )


def _determine_system_health(system_info: SystemInfo) -> str:
    """Determine system health based on resource usage."""
    if (system_info.cpu_usage_percent > 95 or
        system_info.disk_usage_percent > 95 or
        system_info.memory_available_gb < 0.5):
        return "unhealthy"
    elif (system_info.cpu_usage_percent > 80 or
          system_info.disk_usage_percent > 85 or
          system_info.memory_available_gb < 1.0):
        return "degraded"
    else:
        return "healthy"


def _determine_overall_services_status(services: List[Dict[str, Any]]) -> str:
    """Determine overall status of all services."""
    statuses = [s.get("status", "unknown") for s in services]

    if "error" in statuses or "unhealthy" in statuses:
        return "unhealthy"
    elif "degraded" in statuses:
        return "degraded"
    else:
        return "healthy"


def _determine_overall_status(system_status: str, model_ok: bool, services: List[ServiceStatus]) -> str:
    """Determine overall system health status."""
    service_statuses = [s.status for s in services]

    # Critical: Model must be working
    if not model_ok:
        return "unhealthy"

    # Check for any critical errors
    if system_status == "unhealthy" or "error" in service_statuses:
        return "unhealthy"

    # Check for degraded performance
    if system_status == "degraded" or "degraded" in service_statuses:
        return "degraded"

    return "healthy"