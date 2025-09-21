# HeatGuard Predictive Safety System - Backend

## Overview

The HeatGuard Predictive Safety System is a production-grade API that transforms thermal comfort predictions into heat exposure risk assessments for worker safety. Built with FastAPI and XGBoost, it helps companies with heat-exposed workforces boost productivity by 20% while keeping employees safe.

## Features

### 🔥 Core Capabilities
- **Real-time Heat Exposure Prediction**: XGBoost-based ML model for accurate risk assessment
- **OSHA Compliance**: Automated logging and reporting for workplace safety compliance
- **Wearable Device Integration**: Processes HRV and biometric data from worker devices
- **Environmental Monitoring**: Temperature, humidity, and heat index calculations
- **Batch Processing**: Efficient processing of multiple workers simultaneously

### 🛡️ Safety & Security
- **API Key Authentication**: Secure access control with rate limiting
- **Conservative Risk Bias**: Built-in safety margin for worker protection
- **Structured Logging**: Comprehensive audit trails and monitoring
- **Error Handling**: Robust error handling and graceful degradation

### 📊 Data Processing
- **Smart Validation**: Comprehensive input validation with business rule checks
- **Missing Value Handling**: Intelligent imputation based on worker profiles
- **Feature Engineering**: Automatic calculation of derived health metrics
- **Data Quality Scoring**: Assessment of prediction reliability

## Architecture

```
backend/app/
├── models/              # ML models and data generation
│   ├── heat_predictor.py     # Core XGBoost heat exposure model
│   ├── model_loader.py       # Model caching and lifecycle management
│   └── data_generator.py     # Synthetic data generation for testing
├── api/                 # REST API endpoints
│   ├── prediction.py         # Prediction endpoints (/predict, /predict_batch)
│   ├── health.py            # Health check endpoints (/health)
│   └── data_generation.py   # Test data generation endpoints
├── services/            # Business logic layer
│   ├── prediction_service.py # Core prediction business logic
│   ├── batch_service.py      # Async batch processing
│   └── compliance_service.py # OSHA compliance logging
├── utils/               # Utilities and helpers
│   ├── validators.py         # Input validation and sanitization
│   ├── data_preprocessor.py  # Data preprocessing and feature engineering
│   └── logger.py            # Structured logging utilities
├── config/              # Configuration management
│   ├── settings.py          # Application settings
│   └── model_config.py      # ML model configuration
└── middleware/          # HTTP middleware
    └── auth.py              # Authentication and security middleware
```

## Quick Start

### 1. Installation

```bash
# Clone repository (if not already done)
cd backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Model Setup

Ensure the thermal comfort model files are available in the `thermal_comfort_model/` directory:
- `xgboost_model.joblib`
- `scaler.joblib`
- `label_encoder.joblib`
- `feature_columns.joblib`

### 3. Start the Server

```bash
# Using the startup script (recommended)
python start_heatguard.py

# Or directly with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Generate test data
curl -H "X-API-Key: heatguard-api-key-demo-12345" \
     http://localhost:8000/api/v1/generate_random?count=1

# Make a prediction
curl -X POST http://localhost:8000/api/v1/predict \
     -H "Content-Type: application/json" \
     -H "X-API-Key: heatguard-api-key-demo-12345" \
     -d '{
       "data": {
         "Age": 30,
         "Gender": 1,
         "Temperature": 32.5,
         "Humidity": 75.0,
         "hrv_mean_hr": 85.0,
         "hrv_mean_nni": 706.0
       }
     }'
```

## API Endpoints

### Core Prediction Endpoints
- `POST /api/v1/predict` - Single worker heat exposure prediction
- `POST /api/v1/predict_batch` - Multiple worker predictions
- `POST /api/v1/predict_batch_async` - Large batch async processing
- `GET /api/v1/batch_status/{job_id}` - Async job status
- `GET /api/v1/batch_results/{job_id}` - Async job results

### Test Data Generation
- `GET /api/v1/generate_random` - Random test data
- `GET /api/v1/generate_ramp_up` - Escalating risk scenario (green→red)
- `GET /api/v1/generate_ramp_down` - De-escalating risk scenario (red→green)
- `GET /api/v1/feature_template` - Data structure template

### System Health & Monitoring
- `GET /api/v1/health` - Comprehensive system health check
- `GET /api/v1/health/simple` - Simple health status (for load balancers)
- `GET /api/v1/health/model` - ML model specific health
- `GET /api/v1/health/services` - Individual service health
- `GET /api/v1/readiness` - Kubernetes readiness probe
- `GET /api/v1/liveness` - Kubernetes liveness probe

### System Information
- `GET /` - Root endpoint with system overview
- `GET /api/v1/info` - Detailed system information
- `GET /api/v1/version` - Version information

## Configuration

### Environment Variables

```bash
# Application Settings
ENVIRONMENT=development          # development, production, testing
DEBUG=true                      # Enable debug mode
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Server Configuration
HOST=0.0.0.0                    # Server host
PORT=8000                       # Server port

# Security
SECRET_KEY=your-secret-key      # JWT secret key
API_KEY_HEADER=X-API-Key       # API key header name

# Model Configuration
MODEL_DIR=thermal_comfort_model # Model files directory
CONSERVATIVE_BIAS=0.15          # Safety bias for predictions

# OSHA Compliance
ENABLE_OSHA_LOGGING=true        # Enable compliance logging
OSHA_LOG_FILE=logs/osha_compliance.log

# Rate Limiting & Caching
REDIS_URL=redis://localhost:6379  # Redis connection (optional)
RATE_LIMIT_PER_MINUTE=100       # Default rate limit
BATCH_SIZE_LIMIT=1000           # Maximum batch size

# Thresholds
HEAT_INDEX_THRESHOLD_WARNING=80.0  # °F
HEAT_INDEX_THRESHOLD_DANGER=90.0   # °F
```

### API Keys

Demo API keys for testing:
- `heatguard-api-key-demo-12345` - Full access (read/write/admin)
- `heatguard-readonly-key-67890` - Read-only access

## Data Requirements

### Required Features
- `Age`: Worker age (18-80 years)
- `Gender`: 0=Female, 1=Male
- `Temperature`: Environmental temperature (°C)
- `Humidity`: Relative humidity (0-100%)
- `hrv_mean_hr`: Average heart rate (BPM)

### Optional HRV Features
The system supports 50+ heart rate variability features from wearable devices:
- Time domain: `hrv_rmssd`, `hrv_sdnn`, `hrv_mean_nni`
- Frequency domain: `hrv_lf`, `hrv_hf`, `hrv_lf_hf_ratio`
- Geometric: `hrv_SD1`, `hrv_SD2`
- Statistical: `hrv_entropy`, `hrv_kurtosis`

## Response Format

### Prediction Response
```json
{
  "request_id": "single_1640995200000",
  "worker_id": "worker_001",
  "timestamp": "2024-01-01T12:00:00",
  "heat_exposure_risk_score": 0.65,
  "risk_level": "Warning",
  "confidence": 0.87,
  "temperature_celsius": 32.5,
  "temperature_fahrenheit": 90.5,
  "humidity_percent": 75.0,
  "heat_index": 105.2,
  "osha_recommendations": [
    "Implement work/rest cycles: 15 minutes work, 15 minutes rest",
    "Mandatory water intake: 8 oz every 15 minutes",
    "Move to air-conditioned area if possible"
  ],
  "requires_immediate_attention": false,
  "processing_time_ms": 45.2
}
```

### Risk Levels
- **Safe** (0.0-0.25): Normal working conditions
- **Caution** (0.25-0.50): Increased monitoring recommended
- **Warning** (0.50-0.75): Work/rest cycles required
- **Danger** (0.75-1.0): Immediate intervention needed

## Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "start_heatguard.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Kubernetes Health Checks
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/liveness
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/readiness
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Performance Considerations
- **Caching**: Redis recommended for production (rate limiting, model caching)
- **Load Balancing**: Supports multiple worker processes
- **Monitoring**: Built-in health checks and structured logging
- **Rate Limiting**: Per-API-key rate limiting with Redis or in-memory fallback

## Compliance & Logging

### OSHA Compliance
- Automatic logging of all predictions
- Heat index threshold monitoring
- Safety recommendation tracking
- Audit trail for regulatory compliance

### Log Files
- `logs/app.log` - Application logs
- `logs/osha_compliance.log` - OSHA compliance logs
- Structured JSON logging available

## Development

### Testing
```bash
# Run tests
pytest

# Generate test data
curl -H "X-API-Key: heatguard-api-key-demo-12345" \
     "http://localhost:8000/api/v1/generate_random?count=10"

# Test different risk scenarios
curl -H "X-API-Key: heatguard-api-key-demo-12345" \
     "http://localhost:8000/api/v1/generate_ramp_up?duration_minutes=30"
```

### Debug Mode
```bash
# Start in debug mode
ENVIRONMENT=development DEBUG=true python start_heatguard.py

# View configuration (debug only)
curl http://localhost:8000/debug/config
```

## Support

For issues, questions, or feature requests:
- System health: `GET /api/v1/health`
- API documentation: `GET /docs` (debug mode only)
- Logs: Check `logs/` directory for detailed information

## License

Copyright (c) 2024 HeatGuard Predictive Safety System. All rights reserved.