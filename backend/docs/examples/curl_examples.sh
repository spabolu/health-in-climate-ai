#!/bin/bash
# HeatGuard API - cURL Examples
# Comprehensive examples for all API endpoints with authentication and error handling

# Configuration
API_BASE_URL="https://api.heatguard.com"
DEV_API_BASE_URL="http://localhost:8000"
API_KEY="your-api-key-here"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to print colored output
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if API key is set
if [ "$API_KEY" = "your-api-key-here" ]; then
    print_error "Please set your API key in the API_KEY variable"
    exit 1
fi

# Use development URL if running locally
if [ "$1" = "dev" ]; then
    API_BASE_URL=$DEV_API_BASE_URL
    print_info "Using development API: $API_BASE_URL"
fi

# Common headers
COMMON_HEADERS=(-H "X-API-Key: $API_KEY" -H "Content-Type: application/json")

print_header "HeatGuard API Examples"

# =============================================================================
# 1. Health Check
# =============================================================================
print_header "1. Health Check"
print_info "Checking API health status..."

curl -s -w "\nHTTP Status: %{http_code}\nResponse Time: %{time_total}s\n" \
  "$API_BASE_URL/api/v1/health" \
  | jq '.'

echo ""

# =============================================================================
# 2. System Information
# =============================================================================
print_header "2. System Information"
print_info "Retrieving system information..."

curl -s "${COMMON_HEADERS[@]}" \
  "$API_BASE_URL/api/v1/info" \
  | jq '.'

echo ""

# =============================================================================
# 3. Single Worker Prediction
# =============================================================================
print_header "3. Single Worker Prediction"
print_info "Making a single worker prediction..."

curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict" \
  -d '{
    "data": {
      "worker_id": "demo_worker_001",
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
  }' \
  | jq '.'

echo ""

# =============================================================================
# 4. Single Prediction with Minimal Data
# =============================================================================
print_header "4. Single Prediction - Minimal Required Data"
print_info "Making prediction with only required fields..."

curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict" \
  -d '{
    "data": {
      "Age": 45,
      "Gender": 0,
      "Temperature": 28.0,
      "Humidity": 65.0,
      "hrv_mean_hr": 78.0
    }
  }' \
  | jq '.'

echo ""

# =============================================================================
# 5. Batch Prediction
# =============================================================================
print_header "5. Batch Prediction"
print_info "Processing multiple workers in batch..."

curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict_batch" \
  -d '{
    "data": [
      {
        "worker_id": "batch_worker_001",
        "Age": 30,
        "Gender": 1,
        "Temperature": 32.5,
        "Humidity": 75.0,
        "hrv_mean_hr": 85.0,
        "hrv_mean_nni": 706.0
      },
      {
        "worker_id": "batch_worker_002",
        "Age": 45,
        "Gender": 0,
        "Temperature": 28.0,
        "Humidity": 65.0,
        "hrv_mean_hr": 78.0,
        "hrv_mean_nni": 750.0
      },
      {
        "worker_id": "batch_worker_003",
        "Age": 35,
        "Gender": 1,
        "Temperature": 35.0,
        "Humidity": 80.0,
        "hrv_mean_hr": 95.0,
        "hrv_mean_nni": 650.0
      }
    ],
    "options": {
      "use_conservative": true,
      "log_compliance": true
    },
    "parallel_processing": true
  }' \
  | jq '.'

echo ""

# =============================================================================
# 6. Asynchronous Batch Submission
# =============================================================================
print_header "6. Asynchronous Batch Processing"
print_info "Submitting large batch for async processing..."

# Submit async batch job
JOB_RESPONSE=$(curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict_batch_async" \
  -d '{
    "data": [
      {
        "worker_id": "async_worker_001",
        "Age": 30,
        "Gender": 1,
        "Temperature": 32.5,
        "Humidity": 75.0,
        "hrv_mean_hr": 85.0
      },
      {
        "worker_id": "async_worker_002",
        "Age": 25,
        "Gender": 0,
        "Temperature": 29.0,
        "Humidity": 70.0,
        "hrv_mean_hr": 82.0
      }
    ],
    "options": {
      "use_conservative": true,
      "log_compliance": true
    },
    "chunk_size": 50,
    "priority": "normal"
  }')

echo "$JOB_RESPONSE" | jq '.'

# Extract job ID for status checking
JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')

if [ "$JOB_ID" != "null" ] && [ "$JOB_ID" != "" ]; then
    echo ""
    print_info "Checking job status for job ID: $JOB_ID"

    # Check job status
    curl -s "${COMMON_HEADERS[@]}" \
      "$API_BASE_URL/api/v1/batch_status/$JOB_ID" \
      | jq '.'

    echo ""
    print_info "Waiting 5 seconds before checking results..."
    sleep 5

    # Try to get results
    print_info "Attempting to retrieve job results..."
    curl -s "${COMMON_HEADERS[@]}" \
      "$API_BASE_URL/api/v1/batch_results/$JOB_ID" \
      | jq '.'
fi

echo ""

# =============================================================================
# 7. List Batch Jobs
# =============================================================================
print_header "7. List Batch Jobs"
print_info "Listing recent batch jobs..."

curl -s "${COMMON_HEADERS[@]}" \
  "$API_BASE_URL/api/v1/batch_jobs?limit=10" \
  | jq '.'

echo ""

# =============================================================================
# 8. Generate Test Data
# =============================================================================
print_header "8. Generate Test Data"
print_info "Generating random test data..."

curl -s "${COMMON_HEADERS[@]}" \
  "$API_BASE_URL/api/v1/generate_random?count=5&risk_profile=mixed" \
  | jq '.'

echo ""

# =============================================================================
# 9. Error Handling Examples
# =============================================================================
print_header "9. Error Handling Examples"

print_info "Testing invalid API key..."
curl -s -H "X-API-Key: invalid-key" -H "Content-Type: application/json" \
  "$API_BASE_URL/api/v1/predict" \
  -d '{"data": {"Age": 30}}' \
  | jq '.'

echo ""

print_info "Testing missing required fields..."
curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict" \
  -d '{
    "data": {
      "Age": 30
      // Missing required fields
    }
  }' \
  | jq '.'

echo ""

print_info "Testing out-of-range values..."
curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict" \
  -d '{
    "data": {
      "Age": 150,
      "Gender": 1,
      "Temperature": 100,
      "Humidity": 75.0,
      "hrv_mean_hr": 85.0
    }
  }' \
  | jq '.'

echo ""

# =============================================================================
# 10. Performance Testing
# =============================================================================
print_header "10. Performance Testing"
print_info "Testing API performance with concurrent requests..."

# Function to make a single request and measure time
make_request() {
    local start_time=$(date +%s.%N)

    local response=$(curl -s "${COMMON_HEADERS[@]}" \
      -X POST "$API_BASE_URL/api/v1/predict" \
      -d '{
        "data": {
          "Age": 30,
          "Gender": 1,
          "Temperature": 32.0,
          "Humidity": 75.0,
          "hrv_mean_hr": 85.0
        }
      }')

    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc)

    local status=$(echo "$response" | jq -r '.risk_level // "ERROR"')
    echo "Request completed in ${duration}s - Status: $status"
}

print_info "Making 5 concurrent requests..."
for i in {1..5}; do
    make_request &
done
wait

echo ""

# =============================================================================
# 11. Integration Examples
# =============================================================================
print_header "11. Real-world Integration Examples"

print_info "Simulating IoT sensor data integration..."
curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict" \
  -d '{
    "data": {
      "worker_id": "iot_sensor_001",
      "Age": 35,
      "Gender": 1,
      "Temperature": 33.2,
      "Humidity": 78.5,
      "hrv_mean_hr": 88.3,
      "hrv_mean_nni": 695.2,
      "hrv_rmssd": 23.8,
      "hrv_sdnn": 42.1,
      "location": "Construction Site A",
      "shift_start_time": "2024-01-01T08:00:00Z",
      "activity_level": "high"
    },
    "options": {
      "use_conservative": true,
      "log_compliance": true
    }
  }' \
  | jq '.'

echo ""

print_info "Simulating wearable device batch upload..."
curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict_batch" \
  -d '{
    "data": [
      {
        "worker_id": "wearable_001",
        "Age": 28,
        "Gender": 0,
        "Temperature": 31.5,
        "Humidity": 72.0,
        "hrv_mean_hr": 82.0,
        "timestamp": "2024-01-01T14:00:00Z"
      },
      {
        "worker_id": "wearable_002",
        "Age": 42,
        "Gender": 1,
        "Temperature": 34.0,
        "Humidity": 75.0,
        "hrv_mean_hr": 92.0,
        "timestamp": "2024-01-01T14:00:00Z"
      }
    ],
    "options": {
      "use_conservative": true,
      "log_compliance": true
    }
  }' \
  | jq '.batch_statistics'

echo ""

# =============================================================================
# 12. OSHA Compliance Workflow
# =============================================================================
print_header "12. OSHA Compliance Workflow"
print_info "Demonstrating OSHA compliance features..."

# High-risk scenario for OSHA logging
curl -s "${COMMON_HEADERS[@]}" \
  -X POST "$API_BASE_URL/api/v1/predict" \
  -d '{
    "data": {
      "worker_id": "compliance_test_001",
      "Age": 45,
      "Gender": 1,
      "Temperature": 38.5,
      "Humidity": 85.0,
      "hrv_mean_hr": 115.0,
      "hrv_mean_nni": 520.0,
      "work_location": "Outdoor Construction",
      "supervisor_id": "SUP_001"
    },
    "options": {
      "use_conservative": true,
      "log_compliance": true
    }
  }' \
  | jq '{
    risk_level: .risk_level,
    requires_immediate_attention: .requires_immediate_attention,
    osha_recommendations: .osha_recommendations,
    compliance_logged: (.processing_time_ms > 0)
  }'

echo ""

# =============================================================================
# Summary
# =============================================================================
print_header "Summary"
print_success "All API examples completed successfully!"
print_info "For more detailed documentation, visit: $API_BASE_URL/docs"
print_info "Integration examples available at: https://docs.heatguard.com/examples"

echo ""
print_info "Common HTTP Status Codes:"
echo "  200 - Success"
echo "  202 - Accepted (async operations)"
echo "  400 - Bad Request (invalid data)"
echo "  401 - Unauthorized (invalid API key)"
echo "  422 - Validation Error (data validation failed)"
echo "  429 - Rate Limited"
echo "  500 - Internal Server Error"

echo ""
print_info "Response Time Expectations:"
echo "  Single Prediction: < 200ms"
echo "  Batch Prediction (100 workers): < 5s"
echo "  Health Check: < 50ms"

echo ""
print_info "Rate Limits:"
echo "  Default: 1000 requests/minute"
echo "  Burst: 100 requests/10 seconds"