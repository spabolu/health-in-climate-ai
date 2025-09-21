"""
HeatGuard Predictive Safety System - Main Application
=====================================================

Production-grade FastAPI application for heat exposure prediction and worker safety.

This application helps companies with heat-exposed workforces boost productivity by 20%
while keeping employees safe through real-time predictive insights into worker health
and environmental risks.
"""

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uvicorn
from typing import Dict, Any
import logging

# Import application components
from .config.settings import settings
from .utils.logger import setup_logging, get_logger, log_api_request
from .models.model_loader import model_loader
from .middleware.auth import SecurityHeaders
from .api.prediction import prediction_bp
from .api.health import health_bp
from .api.data_generation import data_generation_bp

# Setup logging first
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=settings.LOG_FILE,
    json_format=False
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting HeatGuard Predictive Safety System")
    logger.info(f"Environment: {settings.DEBUG and 'Development' or 'Production'}")
    logger.info(f"Version: {settings.VERSION}")

    try:
        # Pre-load the default model
        logger.info("Pre-loading heat exposure prediction model...")
        model_loader.load_model("default")
        logger.info("Model pre-loading completed successfully")

    except Exception as e:
        logger.error(f"Failed to pre-load model: {e}")
        # Continue startup even if model loading fails
        # The health check will indicate the issue

    logger.info("HeatGuard system startup completed")

    yield

    # Shutdown
    logger.info("Shutting down HeatGuard Predictive Safety System")
    try:
        # Clean up resources
        model_loader.clear_cache()
        logger.info("System shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)


# Add security middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.heatguard.ai"]
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Custom middleware for request logging and security headers
@app.middleware("http")
async def logging_and_security_middleware(request: Request, call_next):
    """Custom middleware for request logging and security headers."""
    start_time = time.time()

    # Log incoming request
    logger.debug(
        f"Incoming request: {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate response time
        process_time = time.time() - start_time

        # Add security headers
        security_headers = SecurityHeaders.get_security_headers()
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value

        # Add custom headers
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-API-Version"] = settings.VERSION

        # Log request completion
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            response_time_ms=round(process_time * 1000, 2)
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time

        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            error=str(e),
            response_time_ms=round(process_time * 1000, 2)
        )

        # Return error response
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": time.time(),
                "request_id": f"req_{int(time.time() * 1000)}"
            }
        )


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": time.time(),
            "request_id": f"req_{int(time.time() * 1000)}"
        }
    )


# Include API routers
app.include_router(prediction_bp)
app.include_router(health_bp)
app.include_router(data_generation_bp)


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with system information.
    """
    return {
        "service": settings.PROJECT_NAME,
        "description": settings.DESCRIPTION,
        "version": settings.VERSION,
        "status": "operational",
        "documentation": "/docs" if settings.DEBUG else "Contact administrator for API documentation",
        "health_check": "/api/v1/health",
        "api_endpoints": {
            "single_prediction": "/api/v1/predict",
            "batch_prediction": "/api/v1/predict_batch",
            "async_batch": "/api/v1/predict_batch_async",
            "health_check": "/api/v1/health",
            "test_data": "/api/v1/generate_random"
        },
        "company_info": {
            "mission": "Helping companies with heat-exposed workforces boost productivity by 20% while keeping employees safe",
            "value_proposition": "Real-time predictive insights into worker health and environmental risks",
            "impact": "Saving businesses millions in lost labor hours and medical costs while addressing a $1B annual healthcare burden"
        },
        "features": {
            "real_time_prediction": "Real-time heat exposure risk assessment from wearable device data",
            "osha_compliance": "Automated OSHA compliance logging and reporting",
            "batch_processing": "Efficient batch processing for large workforces",
            "safety_recommendations": "Evidence-based safety recommendations",
            "environmental_monitoring": "Integration with environmental sensors and IoT devices"
        },
        "timestamp": time.time()
    }


# Additional utility endpoints
@app.get("/api/v1/info", tags=["system"])
async def system_info() -> Dict[str, Any]:
    """Get detailed system information."""
    try:
        model_info = {}
        if model_loader.is_model_loaded("default"):
            model = model_loader.get_model("default")
            if model:
                model_info = model.get_model_info()

        return {
            "system": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": "development" if settings.DEBUG else "production",
                "python_version": "3.8+",
                "framework": "FastAPI"
            },
            "model": model_info,
            "configuration": {
                "max_batch_size": settings.BATCH_SIZE_LIMIT,
                "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
                "osha_compliance_enabled": settings.ENABLE_OSHA_LOGGING,
                "conservative_bias": settings.CONSERVATIVE_BIAS,
                "cache_enabled": bool(settings.REDIS_URL)
            },
            "api_features": {
                "authentication": "API Key based",
                "rate_limiting": "Per API key rate limiting",
                "cors_enabled": bool(settings.BACKEND_CORS_ORIGINS),
                "compression": "Automatic response compression",
                "monitoring": "Built-in health checks and metrics"
            },
            "data_sources": {
                "wearable_devices": [
                    "Heart rate variability (HRV) metrics",
                    "Heart rate monitoring",
                    "Activity and stress indicators"
                ],
                "environmental_sensors": [
                    "Temperature monitoring",
                    "Humidity sensors",
                    "Heat index calculation"
                ],
                "worker_demographics": [
                    "Age and gender factors",
                    "Fitness and heat tolerance profiles"
                ]
            },
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


@app.get("/api/v1/version", tags=["system"])
async def version() -> Dict[str, str]:
    """Get system version information."""
    return {
        "version": settings.VERSION,
        "api_version": "v1",
        "build_date": "2024-01-01",  # Would be set during build process
        "commit_hash": "main",       # Would be set during build process
        "environment": "development" if settings.DEBUG else "production"
    }


# Development-only endpoints
if settings.DEBUG:
    @app.get("/debug/config", tags=["debug"])
    async def debug_config():
        """Debug endpoint to view current configuration."""
        return {
            "warning": "This endpoint is only available in debug mode",
            "settings": {
                "DEBUG": settings.DEBUG,
                "LOG_LEVEL": settings.LOG_LEVEL,
                "HOST": settings.HOST,
                "PORT": settings.PORT,
                "API_V1_STR": settings.API_V1_STR,
                "MODEL_DIR": settings.MODEL_DIR,
                "BATCH_SIZE_LIMIT": settings.BATCH_SIZE_LIMIT,
                "RATE_LIMIT_PER_MINUTE": settings.RATE_LIMIT_PER_MINUTE,
                "OSHA_COMPLIANCE_ENABLED": settings.ENABLE_OSHA_LOGGING
            }
        }

    @app.post("/debug/test_error", tags=["debug"])
    async def test_error():
        """Debug endpoint to test error handling."""
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="This is a test error for debugging purposes"
        )


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    return app


# Run the application
if __name__ == "__main__":
    logger.info(f"Starting HeatGuard API server on {settings.HOST}:{settings.PORT}")

    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        workers=1 if settings.DEBUG else 4
    )