# HeatGuard API Documentation

## Overview

The HeatGuard Predictive Safety System provides a RESTful API for real-time heat exposure prediction and worker safety assessment. This API enables companies to integrate predictive safety capabilities into their existing workforce management systems.

## Base Information

- **Base URL**: `https://api.heatguard.com` (production) / `http://localhost:8000` (development)
- **API Version**: v1
- **Protocol**: HTTPS (production), HTTP (development)
- **Authentication**: API Key (X-API-Key header)
- **Response Format**: JSON
- **Request Format**: JSON

## Authentication

All API requests require authentication using an API key passed in the request header.

```http
X-API-Key: your-api-key-here
```

### Getting an API Key

Contact your system administrator or use the HeatGuard dashboard to generate API keys. Each API key is associated with specific permissions and rate limits.

### Rate Limiting

- **Default Rate Limit**: 1000 requests per minute per API key
- **Burst Limit**: 100 requests per 10 seconds
- **Headers**: Rate limit information is returned in response headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## API Endpoints

### 1. Health Check

Check system health and availability.

```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "HeatGuard Predictive Safety System",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "uptime_seconds": 86400,
  "model_status": "loaded",
  "dependencies": {
    "redis": "connected",
    "model": "ready"
  }
}
```

### 2. Single Worker Prediction

Predict heat exposure risk for a single worker.

```http
POST /api/v1/predict
```

**Request Headers:**
```http
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body:**
```json
{
  "data": {
    "worker_id": "worker_001",
    "Age": 30,
    "Gender": 1,
    "Temperature": 32.5,
    "Humidity": 75.0,
    "hrv_mean_hr": 85.0,
    "hrv_mean_nni": 706.0,
    "hrv_rmssd": 25.5,
    "hrv_sdnn": 45.2
  },
  "options": {
    "use_conservative": true,
    "log_compliance": true
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Range | Description |
|-------|------|----------|-------|-------------|
| `worker_id` | string | No | - | Unique worker identifier |
| `Age` | float | Yes | 16-80 | Worker age in years |
| `Gender` | int | Yes | 0-1 | Gender (0=Female, 1=Male) |
| `Temperature` | float | Yes | -20 to 50 | Temperature in Celsius |
| `Humidity` | float | Yes | 0-100 | Relative humidity percentage |
| `hrv_mean_hr` | float | Yes | 30-220 | Average heart rate (BPM) |
| `hrv_mean_nni` | float | No | 200-2000 | Mean NN interval (ms) |
| `hrv_rmssd` | float | No | 0+ | RMSSD HRV metric |
| `hrv_sdnn` | float | No | 0+ | SDNN HRV metric |

**Response:**
```json
{
  "request_id": "req_1640995200123",
  "worker_id": "worker_001",
  "timestamp": "2024-01-01T12:00:00Z",
  "heat_exposure_risk_score": 0.35,
  "risk_level": "Caution",
  "confidence": 0.87,
  "temperature_celsius": 32.5,
  "temperature_fahrenheit": 90.5,
  "humidity_percent": 75.0,
  "heat_index": 95.2,
  "osha_recommendations": [
    "Increase water intake to 8 oz every 15-20 minutes",
    "Take breaks in shaded or air-conditioned areas",
    "Monitor for early signs of heat exhaustion"
  ],
  "requires_immediate_attention": false,
  "processing_time_ms": 85.3,
  "data_quality_score": 0.95,
  "validation_warnings": []
}
```

### 3. Batch Worker Prediction

Process multiple workers in a single request for efficiency.

```http
POST /api/v1/predict_batch
```

**Request Body:**
```json
{
  "data": [
    {
      "worker_id": "worker_001",
      "Age": 30,
      "Gender": 1,
      "Temperature": 32.5,
      "Humidity": 75.0,
      "hrv_mean_hr": 85.0,
      "hrv_mean_nni": 706.0
    },
    {
      "worker_id": "worker_002",
      "Age": 45,
      "Gender": 0,
      "Temperature": 28.0,
      "Humidity": 65.0,
      "hrv_mean_hr": 78.0,
      "hrv_mean_nni": 750.0
    }
  ],
  "options": {
    "use_conservative": true,
    "log_compliance": true
  },
  "parallel_processing": true
}
```

**Response:**
```json
{
  "request_id": "batch_1640995200456",
  "batch_size": 2,
  "successful_predictions": 2,
  "failed_predictions": 0,
  "processing_time_ms": 150.8,
  "batch_statistics": {
    "average_risk_score": 0.28,
    "high_risk_count": 0,
    "medium_risk_count": 1,
    "low_risk_count": 1,
    "risk_distribution": {
      "Safe": 1,
      "Caution": 1,
      "Warning": 0,
      "Danger": 0
    }
  },
  "predictions": [
    {
      "request_id": "req_1640995200123",
      "worker_id": "worker_001",
      "heat_exposure_risk_score": 0.35,
      "risk_level": "Caution",
      "confidence": 0.87,
      "temperature_celsius": 32.5,
      "humidity_percent": 75.0,
      "osha_recommendations": ["Increase water intake", "Take regular breaks"],
      "requires_immediate_attention": false,
      "processing_time_ms": 75.2
    },
    {
      "request_id": "req_1640995200124",
      "worker_id": "worker_002",
      "heat_exposure_risk_score": 0.21,
      "risk_level": "Safe",
      "confidence": 0.91,
      "temperature_celsius": 28.0,
      "humidity_percent": 65.0,
      "osha_recommendations": ["Continue normal activities", "Stay hydrated"],
      "requires_immediate_attention": false,
      "processing_time_ms": 68.7
    }
  ]
}
```

### 4. Asynchronous Batch Processing

For large datasets (>1000 workers), submit jobs for asynchronous processing.

```http
POST /api/v1/predict_batch_async
```

**Request Body:**
```json
{
  "data": [...],  // Array of up to 10,000 worker records
  "options": {
    "use_conservative": true,
    "log_compliance": true
  },
  "chunk_size": 100,
  "priority": "normal"
}
```

**Response:**
```json
{
  "job_id": "job_abc123def456",
  "status": "submitted",
  "message": "Batch job submitted successfully",
  "batch_size": 5000,
  "estimated_completion_time": "2024-01-01T12:15:00Z"
}
```

### 5. Batch Job Status

Check the status of an asynchronous batch job.

```http
GET /api/v1/batch_status/{job_id}
```

**Response:**
```json
{
  "job_id": "job_abc123def456",
  "status": "processing",
  "progress": {
    "total_workers": 5000,
    "processed_workers": 2500,
    "percent_complete": 50.0
  },
  "estimated_completion": "2024-01-01T12:10:00Z",
  "started_at": "2024-01-01T12:00:00Z",
  "statistics": {
    "successful_predictions": 2450,
    "failed_predictions": 50,
    "average_processing_time_ms": 85.5
  }
}
```

### 6. Batch Job Results

Retrieve results of a completed batch job.

```http
GET /api/v1/batch_results/{job_id}
```

**Response:**
```json
{
  "job_id": "job_abc123def456",
  "status": "completed",
  "completion_time": "2024-01-01T12:12:30Z",
  "total_processing_time_ms": 750000,
  "results": {
    "successful_predictions": 4950,
    "failed_predictions": 50,
    "batch_statistics": {
      "average_risk_score": 0.32,
      "risk_distribution": {
        "Safe": 3200,
        "Caution": 1500,
        "Warning": 200,
        "Danger": 50
      }
    },
    "predictions": [...]  // Array of all prediction results
  }
}
```

### 7. Test Data Generation

Generate test data for development and integration testing.

```http
GET /api/v1/generate_random?count=10&risk_profile=mixed
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `count` | int | 5 | Number of test records (max 100) |
| `risk_profile` | string | "mixed" | Risk profile: "safe", "mixed", "high" |

**Response:**
```json
[
  {
    "worker_id": "test_001",
    "Age": 32,
    "Gender": 1,
    "Temperature": 24.5,
    "Humidity": 60.0,
    "hrv_mean_hr": 75.0,
    "hrv_mean_nni": 800.0,
    "location": "Test Zone A"
  },
  // ... more test records
]
```

### 8. System Information

Get detailed system information and configuration.

```http
GET /api/v1/info
```

**Response:**
```json
{
  "system": {
    "name": "HeatGuard Predictive Safety System",
    "version": "1.0.0",
    "environment": "production",
    "python_version": "3.9+",
    "framework": "FastAPI"
  },
  "model": {
    "name": "XGBoost Heat Exposure Predictor",
    "version": "2.0.1",
    "training_date": "2024-01-01",
    "feature_count": 50,
    "accuracy_score": 0.94
  },
  "configuration": {
    "max_batch_size": 1000,
    "rate_limit_per_minute": 1000,
    "osha_compliance_enabled": true,
    "conservative_bias": true,
    "cache_enabled": true
  }
}
```

## Risk Levels and Safety Recommendations

### Risk Level Classification

| Risk Level | Score Range | Color Code | Immediate Action Required |
|------------|-------------|------------|-------------------------|
| **Safe** | 0.00 - 0.25 | 🟢 Green | No immediate action |
| **Caution** | 0.25 - 0.50 | 🟡 Yellow | Monitor closely |
| **Warning** | 0.50 - 0.75 | 🟠 Orange | Take preventive action |
| **Danger** | 0.75 - 1.00 | 🔴 Red | Immediate intervention |

### OSHA Compliance Recommendations

#### Safe Level (0.00 - 0.25)
- Continue normal work activities
- Maintain regular hydration
- No special precautions required

#### Caution Level (0.25 - 0.50)
- Increase water intake frequency
- Monitor for heat stress symptoms
- Consider lighter workload if temperature rising

#### Warning Level (0.50 - 0.75)
- Take 15-minute breaks in shade every hour
- Drink water every 15 minutes (8 oz)
- Avoid strenuous activities during peak heat
- Consider rotating workers

#### Danger Level (0.75 - 1.00)
- **Stop work immediately**
- Move to air-conditioned area
- Seek medical attention if symptoms present
- Contact supervisor immediately
- Do not return to work until cleared

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error description",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "Temperature",
    "message": "Temperature must be between -20 and 50 degrees Celsius"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_1640995200789"
}
```

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 202 | Accepted | Async job submitted |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Invalid or missing API key |
| 422 | Unprocessable Entity | Data validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | System maintenance |

### Common Error Codes

| Error Code | Description | Resolution |
|------------|-------------|------------|
| `INVALID_API_KEY` | API key is invalid or expired | Check API key configuration |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Wait and retry with backoff |
| `VALIDATION_ERROR` | Input data validation failed | Check required fields and ranges |
| `MODEL_NOT_AVAILABLE` | ML model temporarily unavailable | Retry request or check system status |
| `BATCH_SIZE_EXCEEDED` | Batch size exceeds limit | Reduce batch size or use async processing |

## Integration Examples

### cURL Examples

#### Single Prediction
```bash
curl -X POST "https://api.heatguard.com/api/v1/predict" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "Age": 35,
      "Gender": 1,
      "Temperature": 31.0,
      "Humidity": 70.0,
      "hrv_mean_hr": 82.0,
      "hrv_mean_nni": 732.0
    }
  }'
```

#### Batch Prediction
```bash
curl -X POST "https://api.heatguard.com/api/v1/predict_batch" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"Age": 30, "Gender": 1, "Temperature": 32.0, "Humidity": 75.0, "hrv_mean_hr": 85.0},
      {"Age": 45, "Gender": 0, "Temperature": 28.0, "Humidity": 65.0, "hrv_mean_hr": 78.0}
    ]
  }'
```

### Python Client Example

```python
import requests
import json

class HeatGuardClient:
    def __init__(self, api_key, base_url="https://api.heatguard.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }

    def predict_single(self, worker_data, options=None):
        """Predict heat exposure risk for a single worker."""
        payload = {
            "data": worker_data,
            "options": options or {"use_conservative": True}
        }

        response = requests.post(
            f"{self.base_url}/api/v1/predict",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def predict_batch(self, workers_data, options=None):
        """Predict heat exposure risk for multiple workers."""
        payload = {
            "data": workers_data,
            "options": options or {"use_conservative": True}
        }

        response = requests.post(
            f"{self.base_url}/api/v1/predict_batch",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = HeatGuardClient("your-api-key")

# Single prediction
worker_data = {
    "Age": 30,
    "Gender": 1,
    "Temperature": 32.5,
    "Humidity": 75.0,
    "hrv_mean_hr": 85.0
}

result = client.predict_single(worker_data)
print(f"Risk Level: {result['risk_level']}")
print(f"Risk Score: {result['heat_exposure_risk_score']}")
```

### JavaScript/TypeScript Example

```typescript
interface WorkerData {
  Age: number;
  Gender: 0 | 1;
  Temperature: number;
  Humidity: number;
  hrv_mean_hr: number;
  hrv_mean_nni?: number;
  worker_id?: string;
}

interface PredictionResponse {
  heat_exposure_risk_score: number;
  risk_level: string;
  osha_recommendations: string[];
  requires_immediate_attention: boolean;
}

class HeatGuardAPI {
  constructor(
    private apiKey: string,
    private baseUrl: string = "https://api.heatguard.com"
  ) {}

  async predictSingle(workerData: WorkerData): Promise<PredictionResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/predict`, {
      method: "POST",
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ data: workerData })
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }
}

// Usage
const api = new HeatGuardAPI("your-api-key");

api.predictSingle({
  Age: 30,
  Gender: 1,
  Temperature: 32.5,
  Humidity: 75.0,
  hrv_mean_hr: 85.0
}).then(result => {
  console.log(`Risk Level: ${result.risk_level}`);
  console.log(`Recommendations:`, result.osha_recommendations);
});
```

## Performance Guidelines

### Response Times
- **Single Predictions**: < 200ms (95th percentile)
- **Batch Predictions**: < 500ms for 100 workers
- **Async Jobs**: Status updates within 1 second

### Optimal Usage Patterns

1. **Real-time Monitoring**: Use single predictions for immediate alerts
2. **Periodic Assessments**: Use batch processing for hourly/daily reviews
3. **Large-scale Analysis**: Use async processing for historical analysis
4. **Integration Testing**: Use test data generation endpoints

### Caching Strategies

- Results are cached for 5 minutes for identical input data
- Use `request_id` for result deduplication
- Consider client-side caching for static worker demographics

## Security Best Practices

### API Key Management
- Rotate API keys regularly (recommended: every 90 days)
- Use environment variables for key storage
- Implement key-specific rate limiting
- Monitor key usage for anomalies

### Data Privacy
- Worker data is not permanently stored
- All requests are logged for compliance (configurable retention)
- GDPR/CCPA compliance features available
- Data encryption in transit (TLS 1.2+)

### Network Security
- Use HTTPS in production environments
- Implement IP whitelisting if required
- Configure proper CORS policies
- Monitor for unusual request patterns

## Compliance and Auditing

### OSHA Compliance Features
- Automatic compliance logging for all predictions
- Audit trail with unique request IDs
- Risk assessment documentation
- Safety recommendation tracking
- Incident correlation capabilities

### Regulatory Requirements
- Heat stress assessment per OSHA guidelines
- Documentation for workplace safety programs
- Integration with existing EHS systems
- Customizable alert thresholds

## Support and Resources

### Additional Resources
- [Postman Collection](examples/postman_collection.json)
- [Python SDK](examples/python_client.py)
- [Integration Examples](examples/)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Rate Limit Headers
All responses include rate limit information:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1640995800
X-RateLimit-Burst: 100
```

### Versioning
- Current API version: v1
- Version specified in URL path: `/api/v1/`
- Backward compatibility maintained for major versions
- Deprecation notices provided 6 months in advance

For technical support or integration assistance, please contact the development team or refer to the troubleshooting documentation.