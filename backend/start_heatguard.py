#!/usr/bin/env python3
"""
HeatGuard Predictive Safety System Startup Script
=================================================

Production-ready startup script for the HeatGuard API server.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    import uvicorn
    from app.main import app
    from app.config.settings import settings
    from app.utils.logger import setup_logging
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install required dependencies: pip install -r requirements.txt")
    sys.exit(1)


def setup_environment():
    """Setup environment variables and configuration."""
    # Set default environment if not specified
    if "ENVIRONMENT" not in os.environ:
        os.environ["ENVIRONMENT"] = "development"

    # Create necessary directories
    directories = [
        "logs",
        "data",
        "thermal_comfort_model"  # Ensure model directory exists
    ]

    for directory in directories:
        dir_path = backend_dir / directory
        dir_path.mkdir(exist_ok=True)

    print(f"✅ Environment setup completed")
    print(f"   - Working directory: {backend_dir}")
    print(f"   - Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    print(f"   - Log level: {settings.LOG_LEVEL}")


def check_model_availability():
    """Check if the thermal comfort model is available."""
    model_dir = backend_dir / settings.MODEL_DIR
    required_files = [
        "xgboost_model.joblib",
        "scaler.joblib",
        "label_encoder.joblib",
        "feature_columns.joblib"
    ]

    missing_files = []
    for file_name in required_files:
        file_path = model_dir / file_name
        if not file_path.exists():
            missing_files.append(file_name)

    if missing_files:
        print(f"⚠️  Warning: Missing model files in {model_dir}:")
        for file_name in missing_files:
            print(f"   - {file_name}")
        print(f"   The system will start but predictions will fail until models are available.")
        return False
    else:
        print(f"✅ All required model files found in {model_dir}")
        return True


def check_dependencies():
    """Check if all required dependencies are installed."""
    try:
        import fastapi
        import xgboost
        import pandas
        import numpy
        import pydantic
        import redis
        print("✅ Core dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing required dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False


def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description="HeatGuard Predictive Safety System")

    parser.add_argument(
        "--host",
        default=settings.HOST,
        help=f"Host to bind (default: {settings.HOST})"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"Port to bind (default: {settings.PORT})"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.RELOAD,
        help="Enable auto-reload for development"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1 if settings.DEBUG else 4,
        help="Number of worker processes"
    )

    parser.add_argument(
        "--log-level",
        default=settings.LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Log level (default: {settings.LOG_LEVEL})"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only run system checks without starting server"
    )

    args = parser.parse_args()

    print("🔥 HeatGuard Predictive Safety System")
    print("=" * 50)
    print(f"Version: {settings.VERSION}")
    print(f"Description: {settings.DESCRIPTION}")
    print()

    # Setup environment
    setup_environment()

    # Run system checks
    print("\n🔍 Running system checks...")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check model availability
    model_available = check_model_availability()

    # Check Redis connection (optional)
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("   Caching and rate limiting will use in-memory storage")

    print("\n✅ System checks completed")

    if args.check_only:
        print("\n🏁 Check-only mode - exiting without starting server")
        return

    if not model_available:
        response = input("\n⚠️  Model files are missing. Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting...")
            sys.exit(1)

    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_file=settings.LOG_FILE if not settings.DEBUG else None
    )

    # Start server
    print(f"\n🚀 Starting HeatGuard API server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Workers: {args.workers}")
    print(f"   Reload: {args.reload}")
    print(f"   Log level: {args.log_level}")
    print()

    if settings.DEBUG:
        print("🔧 Development mode - API docs available at:")
        print(f"   - Swagger UI: http://{args.host}:{args.port}/docs")
        print(f"   - ReDoc: http://{args.host}:{args.port}/redoc")
        print()

    print("📊 API endpoints:")
    print(f"   - Health check: http://{args.host}:{args.port}/api/v1/health")
    print(f"   - Single prediction: POST http://{args.host}:{args.port}/api/v1/predict")
    print(f"   - Batch prediction: POST http://{args.host}:{args.port}/api/v1/predict_batch")
    print(f"   - Test data: GET http://{args.host}:{args.port}/api/v1/generate_random")
    print()

    print("🔑 Authentication:")
    print("   API key required in header: X-API-Key")
    print("   Demo key: heatguard-api-key-demo-12345")
    print()

    try:
        # Configure uvicorn
        config = uvicorn.Config(
            app=app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
            access_log=True,
            loop="asyncio",
            http="httptools",
            lifespan="on"
        )

        # Create server
        server = uvicorn.Server(config)

        # Run server
        server.run()

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down HeatGuard system...")
    except Exception as e:
        print(f"\n❌ Server startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()