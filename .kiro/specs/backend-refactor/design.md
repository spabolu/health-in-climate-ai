# Design Document

## Overview

The refactored backend will be a streamlined FastAPI application focused solely on thermal comfort prediction. The design eliminates redundancy from the current multi-file Flask implementation and provides a single, well-defined prediction endpoint that returns risk scores.

## Architecture

### High-Level Architecture

```
Client Request → FastAPI App → Model Service → XGBoost Model → Risk Score Response
```

The architecture follows a simple layered approach:
- **API Layer**: FastAPI application handling HTTP requests/responses
- **Service Layer**: Thermal comfort prediction service encapsulating model logic
- **Model Layer**: Pre-trained XGBoost model with preprocessing components

### File Structure

The refactored backend will have this minimal structure:

```
backend/
├── main.py                    # FastAPI application entry point
├── models/
│   └── predictor.py          # Thermal comfort prediction service
├── schemas/
│   └── prediction.py         # Pydantic models for request/response
├── thermal_comfort_model/    # Existing model artifacts (preserved)
│   ├── xgboost_model.joblib
│   ├── scaler.joblib
│   ├── label_encoder.joblib
│   ├── feature_columns.joblib
│   └── model_metadata.txt
└── requirements.txt          # Updated dependencies
```

## Components and Interfaces

### 1. FastAPI Application (main.py)

**Responsibilities:**
- Initialize FastAPI app with automatic documentation
- Define the single prediction endpoint
- Handle application startup/shutdown events
- Configure CORS if needed

**Key Features:**
- Automatic OpenAPI/Swagger documentation
- Request/response validation via Pydantic
- Proper HTTP status codes and error handling

### 2. Prediction Service (models/predictor.py)

**Responsibilities:**
- Load and manage the trained XGBoost model
- Handle feature preprocessing and scaling
- Calculate thermal comfort risk scores
- Apply conservative bias for safety

**Key Methods:**
```python
class ThermalComfortPredictor:
    def __init__(self, model_dir: str)
    def load_model(self) -> None
    def predict_risk_score(self, features: dict) -> PredictionResult
    def _preprocess_features(self, features: dict) -> np.ndarray
    def _calculate_risk_score(self, prediction: int, probabilities: np.ndarray) -> float
```

### 3. Data Schemas (schemas/prediction.py)

**Request Schema:**
```python
class PredictionRequest(BaseModel):
    # Demographics
    gender: int = Field(..., ge=0, le=1, description="0 for Female, 1 for Male")
    age: int = Field(..., ge=0, le=120, description="Age in years")
    
    # Environmental
    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    
    # HRV Features (all required based on model training)
    hrv_mean_hr: float
    hrv_mean_nni: float
    # ... (all other HRV features as required by the model)
    
    # Optional parameters
    conservative_bias: Optional[float] = Field(0.15, ge=0, le=0.5)
```

**Response Schema:**
```python
class PredictionResponse(BaseModel):
    success: bool
    risk_score: float = Field(..., ge=0, le=1, description="Risk score from 0 (comfortable) to 1 (critical)")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence")
    risk_level: str = Field(..., description="Human-readable risk level")
    predicted_class: str = Field(..., description="Original thermal sensation class")
    conservative_bias: float = Field(..., description="Applied conservative bias")
    timestamp: str = Field(..., description="Prediction timestamp")
```

## Data Models

### Input Features

The system will accept the same feature set as the original model:

**Demographics (2 features):**
- Gender (0/1)
- Age (years)

**Environmental (2 features):**
- Temperature (°C)
- Humidity (%)

**Heart Rate Variability (50+ features):**
- All HRV metrics from the original training (hrv_mean_hr, hrv_mean_nni, etc.)

### Risk Score Calculation

The risk score calculation will preserve the original logic:

1. **Base Score Calculation:**
   ```
   Base_Score = Σ(P(class_i) × Score(class_i))
   ```

2. **Conservative Adjustment:**
   ```
   Risk_Score = min(1.0, Base_Score + Conservative_Bias)
   ```

3. **Class-to-Score Mapping:**
   - neutral: 0.0
   - slightly warm: 0.33
   - warm: 0.67
   - hot: 1.0

## Error Handling

### Error Types and Responses

1. **Model Loading Errors (500):**
   ```json
   {
     "success": false,
     "error": "Model failed to load",
     "detail": "Missing model file: xgboost_model.joblib"
   }
   ```

2. **Validation Errors (422):**
   ```json
   {
     "success": false,
     "error": "Validation failed",
     "detail": [
       {
         "field": "temperature",
         "message": "field required"
       }
     ]
   }
   ```

3. **Prediction Errors (500):**
   ```json
   {
     "success": false,
     "error": "Prediction failed",
     "detail": "Internal model error during prediction"
   }
   ```

### Error Handling Strategy

- Use FastAPI's built-in exception handling
- Custom exception classes for model-specific errors
- Proper HTTP status codes
- Detailed error messages for debugging
- Graceful degradation when possible

## Testing Strategy

### Unit Tests

1. **Model Loading Tests:**
   - Test successful model loading
   - Test handling of missing model files
   - Test model component validation

2. **Prediction Logic Tests:**
   - Test feature preprocessing
   - Test risk score calculation
   - Test conservative bias application
   - Test edge cases (extreme values)

3. **API Endpoint Tests:**
   - Test successful prediction requests
   - Test validation error handling
   - Test response format compliance

### Integration Tests

1. **End-to-End Prediction Tests:**
   - Test complete prediction workflow
   - Test with real feature data
   - Verify response format and values

2. **Model Compatibility Tests:**
   - Ensure compatibility with existing model artifacts
   - Verify prediction consistency with original implementation

### Performance Tests

1. **Load Testing:**
   - Test concurrent prediction requests
   - Measure response times
   - Test memory usage under load

## API Endpoint Specification

### POST /predict

**Description:** Predict thermal comfort risk score from input features

**Request:**
```json
{
  "gender": 1,
  "age": 30,
  "temperature": 28.5,
  "humidity": 65,
  "hrv_mean_hr": 75,
  "hrv_mean_nni": 800,
  // ... all other required HRV features
  "conservative_bias": 0.15
}
```

**Response (200):**
```json
{
  "success": true,
  "risk_score": 0.42,
  "confidence": 0.87,
  "risk_level": "Moderate Risk",
  "predicted_class": "slightly warm",
  "conservative_bias": 0.15,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Response (422 - Validation Error):**
```json
{
  "success": false,
  "error": "Validation failed",
  "detail": [
    {
      "field": "temperature",
      "message": "field required"
    }
  ]
}
```

## Migration Strategy

### Files to Remove

The following files will be removed as they are redundant or not needed:

- `flask_app.py` (replaced by FastAPI)
- `simple_api.py` (redundant Flask implementation)
- `run_api.py` (replaced by FastAPI startup)
- `test_api.py` (will be replaced with new tests)
- `example_usage.py` (not needed for core functionality)
- `predict_thermal_comfort.py` (logic moved to predictor service)

### Files to Preserve

- `thermal_comfort_model/` directory (all model artifacts)
- `Train2021.csv` and `Test Data.csv` (for reference/retraining)
- `main.py` (will be completely rewritten for FastAPI)

### Dependencies Update

Update `requirements.txt` to replace Flask with FastAPI:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
xgboost==1.7.6
joblib==1.3.2
pydantic==2.5.0
```

## Deployment Considerations

### Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Health Check

The API will include a simple health check endpoint:

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

This design provides a clean, focused, and maintainable solution that meets all the requirements while preserving the core prediction functionality.