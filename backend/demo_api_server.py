#!/usr/bin/env python3
"""
HeatGuard Demo API Server
Simple Flask server providing mock data for frontend integration demo
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import time
from datetime import datetime, timezone
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Demo API Key for authentication
DEMO_API_KEY = "heatguard-api-key-demo-12345"

def verify_api_key():
    """Verify API key from request headers"""
    api_key = request.headers.get('X-API-Key')
    return api_key == DEMO_API_KEY

def generate_mock_worker_data(risk_level="normal"):
    """Generate realistic mock worker biometric data"""
    base_temp = 22.0  # Comfortable baseline
    base_humidity = 50.0
    base_hr = 70

    if risk_level == "warning":
        base_temp = 32.0
        base_humidity = 80.0
        base_hr = 95
    elif risk_level == "danger":
        base_temp = 38.0
        base_humidity = 90.0
        base_hr = 120

    return {
        "worker_id": f"W{random.randint(100, 999):03d}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "Gender": random.choice([0, 1]),
        "Age": random.randint(25, 60),
        "Temperature": base_temp + random.uniform(-2, 5),
        "Humidity": min(100, base_humidity + random.uniform(-10, 15)),
        "hrv_mean_hr": base_hr + random.uniform(-10, 20),
        "hrv_mean_nni": 750 + random.uniform(-100, 100),
        "hrv_rmssd": 40 + random.uniform(-15, 15),
        "location": f"Zone {random.choice(['A', 'B', 'C'])}"
    }

def calculate_risk_score(data):
    """Calculate mock risk score based on temperature and heart rate"""
    temp = data.get('Temperature', 22)
    hr = data.get('hrv_mean_hr', 70)
    humidity = data.get('Humidity', 50)

    # Simple risk calculation for demo
    temp_risk = max(0, (temp - 20) / 20)  # Risk increases with temp above 20°C
    hr_risk = max(0, (hr - 60) / 60)      # Risk increases with HR above 60
    humidity_risk = max(0, (humidity - 40) / 60)  # Risk increases with humidity above 40%

    risk_score = min(1.0, (temp_risk + hr_risk + humidity_risk) / 3)
    return risk_score

def get_risk_level(score):
    """Convert risk score to risk level"""
    if score < 0.25:
        return "Safe"
    elif score < 0.5:
        return "Caution"
    elif score < 0.75:
        return "Warning"
    else:
        return "Danger"

def get_recommendations(risk_level, score):
    """Get safety recommendations based on risk level"""
    if risk_level == "Safe":
        return ["Continue normal work activities", "Stay hydrated"]
    elif risk_level == "Caution":
        return ["Increase water intake", "Monitor for heat stress symptoms"]
    elif risk_level == "Warning":
        return [
            "Take 15-minute break in shade every hour",
            "Drink water every 15 minutes",
            "Avoid strenuous activities"
        ]
    else:  # Danger
        return [
            "Stop work immediately",
            "Move to air-conditioned area",
            "Seek medical attention if symptoms persist",
            "Contact supervisor immediately"
        ]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "HeatGuard Demo API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": "demo mode",
        "model_status": "mock data ready"
    })

@app.route('/api/v1/health', methods=['GET'])
def health_check_v1():
    """Alternative health check endpoint for v1 API"""
    return health_check()

@app.route('/predict', methods=['POST'])
def predict_single():
    """Single worker prediction endpoint"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Calculate prediction
        risk_score = calculate_risk_score(data)
        risk_level = get_risk_level(risk_score)

        response = {
            "request_id": f"single_{int(time.time() * 1000)}",
            "worker_id": data.get('worker_id', 'unknown'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "confidence": 0.87,
            "temperature_celsius": data.get('Temperature', 22),
            "humidity_percent": data.get('Humidity', 50),
            "recommendations": get_recommendations(risk_level, risk_score),
            "requires_immediate_attention": risk_score > 0.75,
            "processing_time_ms": random.uniform(45, 150)
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route('/api/v1/predict', methods=['POST'])
def predict_single_v1():
    """V1 API version of single prediction"""
    return predict_single()

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """Batch prediction endpoint"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    try:
        request_data = request.get_json()
        if not request_data or 'data' not in request_data:
            return jsonify({"error": "No data array provided"}), 400

        data_array = request_data['data']
        predictions = []

        for data in data_array:
            risk_score = calculate_risk_score(data)
            risk_level = get_risk_level(risk_score)

            prediction = {
                "worker_id": data.get('worker_id', f'worker_{len(predictions)+1}'),
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "confidence": 0.87,
                "temperature_celsius": data.get('Temperature', 22),
                "humidity_percent": data.get('Humidity', 50),
                "recommendations": get_recommendations(risk_level, risk_score),
                "requires_immediate_attention": risk_score > 0.75,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            predictions.append(prediction)

        return jsonify({
            "success": True,
            "request_id": f"batch_{int(time.time() * 1000)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": len(predictions),
            "predictions": predictions,
            "processing_time_ms": random.uniform(100, 300)
        })

    except Exception as e:
        return jsonify({"error": f"Batch prediction failed: {str(e)}"}), 500

@app.route('/api/v1/predict_batch', methods=['POST'])
def predict_batch_v1():
    """V1 API version of batch prediction"""
    return predict_batch()

@app.route('/generate_random', methods=['GET'])
def generate_random_data():
    """Generate random test data"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    count = int(request.args.get('count', 5))
    count = min(count, 50)  # Limit to 50 for demo

    workers = []
    for i in range(count):
        risk_type = random.choices(
            ["normal", "warning", "danger"],
            weights=[70, 25, 5]  # Mostly normal, some warning, few danger
        )[0]
        worker_data = generate_mock_worker_data(risk_type)
        workers.append(worker_data)

    return jsonify(workers)

@app.route('/api/v1/generate_random', methods=['GET'])
def generate_random_data_v1():
    """V1 API version of generate random data"""
    return generate_random_data()

@app.route('/generate_ramp_up', methods=['GET'])
def generate_ramp_up_data():
    """Generate escalating risk scenario data"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    duration = int(request.args.get('duration_minutes', 30))
    points = min(duration, 20)  # Max 20 data points

    workers = []
    for i in range(points):
        progress = i / (points - 1)  # 0 to 1

        # Escalating temperature and heart rate
        temp = 22 + (progress * 20)  # 22°C to 42°C
        hr = 70 + (progress * 50)    # 70 to 120 BPM
        humidity = 50 + (progress * 40)  # 50% to 90%

        worker_data = {
            "worker_id": "DEMO_001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "Gender": 1,
            "Age": 35,
            "Temperature": temp + random.uniform(-1, 1),
            "Humidity": min(100, humidity + random.uniform(-5, 5)),
            "hrv_mean_hr": hr + random.uniform(-5, 5),
            "hrv_mean_nni": 750 - (progress * 200),  # HRV decreases with stress
            "location": "Demo Zone",
            "scenario_time": f"{i*2} minutes"  # Every 2 minutes
        }
        workers.append(worker_data)

    return jsonify(workers)

@app.route('/api/v1/generate_ramp_up', methods=['GET'])
def generate_ramp_up_data_v1():
    """V1 API version of generate ramp up data"""
    return generate_ramp_up_data()

@app.route('/generate_ramp_down', methods=['GET'])
def generate_ramp_down_data():
    """Generate de-escalating risk scenario data"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    # Similar to ramp_up but in reverse
    duration = int(request.args.get('duration_minutes', 20))
    points = min(duration, 15)

    workers = []
    for i in range(points):
        progress = 1 - (i / (points - 1))  # 1 to 0 (reverse)

        temp = 22 + (progress * 18)  # 40°C to 22°C
        hr = 70 + (progress * 40)    # 110 to 70 BPM
        humidity = 50 + (progress * 35)  # 85% to 50%

        worker_data = {
            "worker_id": "RECOVERY_001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "Gender": 1,
            "Age": 35,
            "Temperature": temp + random.uniform(-1, 1),
            "Humidity": max(30, humidity + random.uniform(-5, 5)),
            "hrv_mean_hr": hr + random.uniform(-5, 5),
            "hrv_mean_nni": 550 + ((1-progress) * 200),  # HRV recovers
            "location": "Recovery Zone",
            "scenario_time": f"{i*2} minutes into recovery"
        }
        workers.append(worker_data)

    return jsonify(workers)

@app.route('/api/v1/generate_ramp_down', methods=['GET'])
def generate_ramp_down_data_v1():
    """V1 API version of generate ramp down data"""
    return generate_ramp_down_data()

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """Mock dashboard metrics for frontend"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    metrics = {
        "total_workers": random.randint(25, 50),
        "active_workers": random.randint(20, 35),
        "high_risk_workers": random.randint(0, 5),
        "average_temperature": round(random.uniform(25, 35), 1),
        "average_humidity": round(random.uniform(60, 85), 1),
        "alert_count_today": random.randint(2, 8),
        "system_status": "operational",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

    return jsonify(metrics)

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Mock alerts for frontend"""
    if not verify_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    alerts = []

    # Generate a few mock alerts
    for i in range(random.randint(1, 4)):
        severity = random.choice(['low', 'medium', 'high'])
        alerts.append({
            "id": f"alert_{uuid.uuid4().hex[:8]}",
            "worker_id": f"W{random.randint(100, 999):03d}",
            "alert_type": "heat_stress_warning",
            "severity": severity,
            "message": f"Worker showing signs of heat stress - {severity} risk level",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "acknowledged": random.choice([True, False]),
            "location": f"Zone {random.choice(['A', 'B', 'C'])}"
        })

    return jsonify(alerts)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "service": "HeatGuard Demo API Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict_single": "POST /predict",
            "predict_batch": "POST /predict_batch",
            "generate_random": "GET /generate_random",
            "generate_ramp_up": "GET /generate_ramp_up",
            "dashboard_metrics": "GET /api/dashboard/metrics",
            "alerts": "GET /api/alerts"
        },
        "authentication": "X-API-Key header required",
        "demo_api_key": DEMO_API_KEY
    })

if __name__ == '__main__':
    print("🚀 Starting HeatGuard Demo API Server...")
    print(f"💡 Demo API Key: {DEMO_API_KEY}")
    print("🌐 CORS enabled for frontend integration")
    print("📊 Mock data endpoints ready for demo")

    # Run on port 8000 to match frontend expectations
    app.run(host='0.0.0.0', port=8000, debug=True)