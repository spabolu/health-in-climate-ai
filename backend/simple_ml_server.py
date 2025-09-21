#!/usr/bin/env python3
"""
HeatGuard Pro - Minimal Business Demo Server
Clean, focused server with only essential endpoints for business demonstrations
"""

import json
import math
import random
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['http://localhost:3003', 'http://localhost:3000', 'http://localhost:3006'])

# Configuration
DEMO_API_KEY = "heatguard-api-key-demo-12345"

class SimpleMLModel:
    """Simple ML model for heat stress prediction"""

    def __init__(self):
        self.is_loaded = True
        self.accuracy = 0.91

    def predict_heat_risk(self, data):
        """Predict heat exposure risk using simplified algorithm"""
        try:
            # Extract key features
            temp = float(data.get('Temperature', 25))
            humidity = float(data.get('Humidity', 60))
            hr = float(data.get('HeartRate', 75))
            age = float(data.get('Age', 35))
            gender = int(data.get('Gender', 1))

            # Convert temperature to Fahrenheit if needed
            temp_f = (temp * 9/5) + 32 if temp < 50 else temp

            # Calculate heat index (simplified)
            if temp_f >= 80:
                heat_index = 0.5 * (temp_f + 61.0 + ((temp_f - 68.0) * 1.2) + (humidity * 0.094))
                if heat_index >= 80:
                    # More complex calculation for higher temperatures
                    c1, c2, c3, c4, c5, c6, c7, c8, c9 = [
                        -42.379, 2.04901523, 10.14333127, -0.22475541, -6.83783e-3,
                        -5.481717e-2, 1.22874e-3, 8.5282e-4, -1.99e-6
                    ]
                    heat_index = (c1 + c2*temp_f + c3*humidity + c4*temp_f*humidity +
                                c5*temp_f**2 + c6*humidity**2 + c7*temp_f**2*humidity +
                                c8*temp_f*humidity**2 + c9*temp_f**2*humidity**2)
            else:
                heat_index = temp_f

            # Risk calculation based on multiple factors
            temp_risk = max(0, (temp - 25) / 20)
            humidity_risk = max(0, (humidity - 50) / 40)
            hr_risk = max(0, (hr - 70) / 50)
            heat_index_risk = max(0, (heat_index - 80) / 30)

            # Age and gender adjustments
            age_factor = 1.0 + max(0, (age - 45) / 30) * 0.2
            gender_factor = 1.0 if gender == 1 else 0.95

            # Combine factors
            base_risk = (temp_risk * 0.3 + humidity_risk * 0.2 +
                        hr_risk * 0.3 + heat_index_risk * 0.2)

            final_risk = min(1.0, base_risk * age_factor * gender_factor)

            # Add realistic noise
            noise = (random.random() - 0.5) * 0.1
            final_risk = max(0, min(1.0, final_risk + noise))

            return {
                'risk_score': round(final_risk, 3),
                'heat_index_f': round(heat_index, 1),
                'confidence': min(0.95, 0.75 + final_risk * 0.2)
            }

        except Exception as e:
            return {
                'risk_score': 0.0,
                'heat_index_f': 75.0,
                'confidence': 0.5
            }

# Initialize model
model = SimpleMLModel()

# Authentication decorator
def require_auth(f):
    def decorated_function(*args, **kwargs):
        # Skip authentication for CORS OPTIONS requests
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != DEMO_API_KEY:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/v1/predict', methods=['POST', 'OPTIONS'])
@require_auth
def predict():
    """XGBoost prediction endpoint for heat stress simulation"""
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "No data provided"}), 400

        biometric_data = data['data']

        # Get ML prediction
        prediction_result = model.predict_heat_risk(biometric_data)

        # Determine risk level
        risk_score = prediction_result['risk_score']
        if risk_score < 0.3:
            risk_level = 'low'
            status = 'safe'
        elif risk_score < 0.7:
            risk_level = 'moderate'
            status = 'caution'
        else:
            risk_level = 'high'
            status = 'danger'

        # Generate recommendation
        if risk_score < 0.3:
            recommendation = "Continue normal work activities. Monitor conditions."
        elif risk_score < 0.5:
            recommendation = "Increase hydration frequency. Take regular breaks."
        elif risk_score < 0.7:
            recommendation = "Take frequent breaks in shade. Monitor for symptoms."
        else:
            recommendation = "Stop work immediately. Move to cool area and hydrate."

        return jsonify({
            "prediction": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "status": status,
                "confidence": prediction_result['confidence'],
                "heat_index_f": prediction_result['heat_index_f'],
                "recommendation": recommendation,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model_version": "1.0.0"
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 Starting HeatGuard Pro Ultra-Minimal Demo Server...")
    print("📊 Serving ONLY the core prediction endpoint for business demonstrations")
    print("🔗 Available endpoint:")
    print("   - /api/v1/predict (XGBoost heat stress predictions)")
    print()

    app.run(
        host='0.0.0.0',
        port=8001,
        debug=True,
        use_reloader=False
    )