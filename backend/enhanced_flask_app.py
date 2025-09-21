"""
Enhanced Thermal Comfort Prediction Flask API for HeatGuard Pro
================================================================

Extended Flask application that provides:
- All original thermal comfort prediction endpoints
- Worker profile management (in-memory)
- Dashboard metrics and analytics
- Health alerts system
- Real-time monitoring capabilities
- OSHA compliance recommendations

For demo/prototype use with simulated data (~100 workers)
"""

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import traceback
import uuid
import json
import random
import time
from collections import defaultdict
from predict_thermal_comfort import ThermalComfortPredictor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global predictor instance
predictor = None

# ===================================
# IN-MEMORY DATA STORAGE (Demo Only)
# ===================================
DEMO_DATA = {
    'workers': {},              # worker_id -> worker_profile
    'biometric_readings': [],   # list of all readings with timestamps
    'predictions': [],          # list of all predictions
    'alerts': [],              # list of active alerts
    'dashboard_cache': {},     # cached dashboard metrics
    'locations': ['Factory Floor A', 'Factory Floor B', 'Warehouse', 'Loading Dock', 'Office Area']
}

def initialize_predictor():
    """Initialize the thermal comfort predictor."""
    global predictor
    try:
        predictor = ThermalComfortPredictor()
        print("✅ Thermal comfort predictor initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize predictor: {e}")
        return False

def initialize_demo_data():
    """Initialize demo data with ~100 simulated workers."""
    print("🎭 Initializing demo data...")

    # Create 100 demo workers
    worker_names = [
        "John Smith", "Maria Garcia", "David Johnson", "Sarah Wilson", "Michael Brown",
        "Lisa Davis", "Robert Miller", "Jennifer Taylor", "William Anderson", "Jessica Thomas",
        "James Jackson", "Ashley White", "Christopher Harris", "Amanda Martin", "Daniel Thompson",
        "Emily Garcia", "Matthew Martinez", "Elizabeth Robinson", "Andrew Clark", "Stephanie Rodriguez",
        "Joshua Lewis", "Michelle Lee", "Ryan Walker", "Nicole Hall", "Brandon Allen",
        "Rachel Young", "Tyler Hernandez", "Laura King", "Kevin Wright", "Amy Lopez",
        "Justin Hill", "Kimberly Scott", "Jordan Green", "Angela Adams", "Brian Baker",
        "Melissa Gonzalez", "Aaron Nelson", "Rebecca Carter", "Jacob Mitchell", "Samantha Perez",
        "Noah Roberts", "Christine Turner", "Ethan Phillips", "Deborah Campbell", "Alexander Parker",
        "Katherine Evans", "Mason Edwards", "Sharon Collins", "Lucas Stewart", "Carol Sanchez",
        "Henry Morris", "Donna Rogers", "Owen Reed", "Ruth Cook", "Caleb Bailey", "Helen Rivera",
        "Isaac Cooper", "Linda Richardson", "Gabriel Cox", "Frances Howard", "Levi Ward",
        "Virginia Torres", "Jaxon Peterson", "Rose Gray", "Lincoln Ramirez", "Beverly James",
        "Oliver Watson", "Carolyn Brooks", "Elijah Kelly", "Janet Sanders", "Connor Price",
        "Gloria Bennett", "Landon Wood", "Evelyn Barnes", "Wyatt Ross", "Annie Henderson",
        "Hunter Coleman", "Irene Jenkins", "Eli Perry", "Marie Powell", "Nolan Long",
        "Doris Patterson", "Grayson Hughes", "Julia Flores", "Cameron Washington", "Diane Butler",
        "Adrian Simmons", "Cheryl Foster", "Julian Gonzales", "Mildred Bryant", "Josiah Alexander",
        "Andrea Russell", "Isaiah Griffin", "Joan Diaz", "Colton Hayes", "Catherine Myers",
        "Brayden Ford", "Frances Hamilton", "Luke Graham", "Dorothy Sullivan", "Aiden Wallace"
    ]

    for i, name in enumerate(worker_names):
        worker_id = f"worker_{i+1:03d}"
        worker = {
            'id': worker_id,
            'name': name,
            'age': random.randint(22, 65),
            'gender': random.choice(['male', 'female']),
            'medical_conditions': random.choice([[], ['hypertension'], ['diabetes'], ['asthma'], []]),
            'heat_tolerance': random.choice(['low', 'normal', 'high']),
            'emergency_contact': {
                'name': f"Emergency Contact for {name}",
                'phone': f"555-{random.randint(1000, 9999)}"
            },
            'assigned_location': random.choice(DEMO_DATA['locations']),
            'shift_pattern': random.choice(['Morning (6AM-2PM)', 'Afternoon (2PM-10PM)', 'Night (10PM-6AM)']),
            'created_at': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': random.choice(['active', 'active', 'active', 'active', 'break'])  # Most workers active
        }
        DEMO_DATA['workers'][worker_id] = worker

    # Generate some historical data and alerts for realism
    generate_historical_readings()
    generate_sample_alerts()

    print(f"✅ Initialized {len(DEMO_DATA['workers'])} demo workers")

def generate_historical_readings():
    """Generate some historical biometric readings for demo."""
    current_time = datetime.now()

    # Generate readings for the last 24 hours
    for _ in range(500):  # 500 historical readings
        worker_id = random.choice(list(DEMO_DATA['workers'].keys()))
        worker = DEMO_DATA['workers'][worker_id]

        # Generate timestamp in the last 24 hours
        timestamp = current_time - timedelta(
            hours=random.uniform(0, 24),
            minutes=random.uniform(0, 60)
        )

        # Generate biometric data based on worker profile with CORRECT HRV feature names
        base_temp = 22.0 + random.uniform(-3, 8)  # Environmental temp
        reading = {
            'id': len(DEMO_DATA['biometric_readings']) + 1,
            'worker_id': worker_id,
            'timestamp': timestamp.isoformat(),

            # Core features expected by ML model
            'Gender': 1 if worker['gender'] == 'male' else 0,
            'Age': worker['age'],
            'Temperature': base_temp,
            'Humidity': random.uniform(30, 80),

            # All 51 HRV features with correct names
            'hrv_mean_nni': round(random.uniform(600, 1200), 2),
            'hrv_median_nni': round(random.uniform(580, 1180), 2),
            'hrv_range_nni': round(random.uniform(100, 800), 2),
            'hrv_sdsd': round(random.uniform(10, 100), 2),
            'hrv_rmssd': round(random.uniform(15, 120), 2),
            'hrv_nni_50': round(random.uniform(5, 200), 2),
            'hrv_pnni_50': round(random.uniform(0.5, 45), 2),
            'hrv_nni_20': round(random.uniform(20, 300), 2),
            'hrv_pnni_20': round(random.uniform(5, 70), 2),
            'hrv_cvsd': round(random.uniform(0.02, 0.15), 4),
            'hrv_sdnn': round(random.uniform(20, 150), 2),
            'hrv_cvnni': round(random.uniform(0.02, 0.12), 4),
            'hrv_mean_hr': round(random.uniform(60, 120), 2),
            'hrv_min_hr': round(random.uniform(50, 90), 2),
            'hrv_max_hr': round(random.uniform(90, 150), 2),
            'hrv_std_hr': round(random.uniform(5, 25), 2),
            'hrv_total_power': round(random.uniform(1000, 8000), 2),
            'hrv_vlf': round(random.uniform(300, 2000), 2),
            'hrv_lf': round(random.uniform(200, 1500), 2),
            'hrv_hf': round(random.uniform(150, 1200), 2),
            'hrv_lf_hf_ratio': round(random.uniform(0.5, 4.0), 2),
            'hrv_lfnu': round(random.uniform(20, 80), 2),
            'hrv_hfnu': round(random.uniform(20, 80), 2),
            'hrv_SD1': round(random.uniform(10, 80), 2),
            'hrv_SD2': round(random.uniform(30, 200), 2),
            'hrv_SD2SD1': round(random.uniform(1.5, 5.0), 2),
            'hrv_CSI': round(random.uniform(1, 8), 2),
            'hrv_CVI': round(random.uniform(2, 12), 2),
            'hrv_CSI_Modified': round(random.uniform(1.2, 9), 2),
            'hrv_mean': round(random.uniform(500, 1000), 2),
            'hrv_std': round(random.uniform(50, 300), 2),
            'hrv_min': round(random.uniform(400, 800), 2),
            'hrv_max': round(random.uniform(800, 1400), 2),
            'hrv_ptp': round(random.uniform(200, 800), 2),
            'hrv_sum': round(random.uniform(50000, 500000), 2),
            'hrv_energy': round(random.uniform(100000, 1000000), 2),
            'hrv_skewness': round(random.uniform(-2, 2), 3),
            'hrv_kurtosis': round(random.uniform(0, 10), 3),
            'hrv_peaks': round(random.uniform(50, 200), 2),
            'hrv_rms': round(random.uniform(400, 900), 2),
            'hrv_lineintegral': round(random.uniform(10000, 80000), 2),
            'hrv_n_above_mean': round(random.uniform(20, 60), 2),
            'hrv_n_below_mean': round(random.uniform(20, 60), 2),
            'hrv_n_sign_changes': round(random.uniform(30, 90), 2),
            'hrv_iqr': round(random.uniform(50, 300), 2),
            'hrv_iqr_5_95': round(random.uniform(200, 800), 2),
            'hrv_pct_5': round(random.uniform(500, 700), 2),
            'hrv_pct_95': round(random.uniform(900, 1300), 2),
            'hrv_entropy': round(random.uniform(0.5, 2.0), 3),
            'hrv_perm_entropy': round(random.uniform(0.3, 1.0), 3),
            'hrv_svd_entropy': round(random.uniform(0.4, 1.2), 3),

            # Additional fields for frontend display (not used by ML model)
            'AirVelocity': random.uniform(0.1, 2.0),
            'HeartRate': random.uniform(60, 120),
            'SkinTemperature': base_temp + random.uniform(-2, 3),
            'CoreBodyTemperature': 36.5 + random.uniform(0, 2),
            'SkinConductance': random.uniform(0.1, 0.9),
            'MetabolicRate': random.uniform(1.0, 3.0),
            'ActivityLevel': random.randint(1, 5),
            'ClothingInsulation': random.uniform(0.5, 1.5),
            'RespiratoryRate': random.uniform(12, 25),
            'HydrationLevel': random.uniform(0.3, 1.0),
            'location_id': worker['assigned_location']
        }

        DEMO_DATA['biometric_readings'].append(reading)

        # Generate prediction for this reading
        try:
            if predictor:
                prediction_result = predictor.predict_single({
                    k: v for k, v in reading.items()
                    if k not in ['id', 'worker_id', 'timestamp', 'location_id']
                })

                prediction = {
                    'id': len(DEMO_DATA['predictions']) + 1,
                    'worker_id': worker_id,
                    'biometric_reading_id': reading['id'],
                    'timestamp': timestamp.isoformat(),
                    'thermal_comfort': prediction_result.get('prediction', 'neutral'),
                    'risk_level': prediction_result.get('risk_assessment', 'comfortable'),
                    'confidence': prediction_result.get('confidence', 0.8),
                    'recommended_action': prediction_result.get('recommended_action', 'continue_monitoring'),
                    'break_recommendation_minutes': prediction_result.get('break_recommendation_minutes', 0),
                    'model_version': '1.0.0'
                }

                DEMO_DATA['predictions'].append(prediction)
        except Exception as e:
            print(f"Warning: Could not generate prediction for historical data: {e}")

def generate_sample_alerts():
    """Generate some sample alerts for the demo."""
    alert_types = [
        'heat_exhaustion_risk', 'dehydration_warning', 'high_heart_rate',
        'temperature_spike', 'prolonged_exposure'
    ]

    severities = ['low', 'moderate', 'high', 'critical']

    for _ in range(15):  # Generate 15 sample alerts
        worker_id = random.choice(list(DEMO_DATA['workers'].keys()))
        worker = DEMO_DATA['workers'][worker_id]

        alert = {
            'id': str(uuid.uuid4()),
            'worker_id': worker_id,
            'alert_type': random.choice(alert_types),
            'severity': random.choice(severities),
            'message': f"Health alert for {worker['name']} - monitoring required",
            'recommended_actions': ['Monitor closely', 'Provide water', 'Consider break'],
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(5, 1440))).isoformat(),
            'acknowledged': random.choice([True, False]),
            'resolved': random.choice([True, False, False]),  # Most unresolved
            'location': worker['assigned_location']
        }

        DEMO_DATA['alerts'].append(alert)

# ===================================
# CORE PREDICTION ENDPOINTS (EXISTING)
# ===================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    status = "healthy" if predictor is not None else "model_not_loaded"
    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "model_loaded": predictor is not None,
        "workers_count": len(DEMO_DATA['workers']),
        "alerts_count": len([a for a in DEMO_DATA['alerts'] if not a['resolved']])
    })

@app.route('/predict', methods=['POST'])
@app.route('/api/predict_thermal_comfort', methods=['POST'])
def predict_thermal_comfort():
    """Predict thermal comfort for a single reading."""
    try:
        if predictor is None:
            return jsonify({"error": "Predictor not initialized"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Make prediction
        result = predictor.predict_single(data)

        # Store the reading and prediction if worker_id provided
        if 'worker_id' in data:
            # Store biometric reading
            reading = {
                'id': len(DEMO_DATA['biometric_readings']) + 1,
                'worker_id': data['worker_id'],
                'timestamp': datetime.now().isoformat(),
                **{k: v for k, v in data.items() if k != 'worker_id'}
            }
            DEMO_DATA['biometric_readings'].append(reading)

            # Store prediction
            prediction = {
                'id': len(DEMO_DATA['predictions']) + 1,
                'worker_id': data['worker_id'],
                'biometric_reading_id': reading['id'],
                'timestamp': datetime.now().isoformat(),
                'thermal_comfort': result.get('prediction', 'neutral'),
                'risk_level': result.get('risk_assessment', 'comfortable'),
                'confidence': result.get('confidence', 0.8),
                'recommended_action': result.get('recommended_action', 'continue_monitoring'),
                'break_recommendation_minutes': result.get('break_recommendation_minutes', 0),
                'model_version': '1.0.0'
            }
            DEMO_DATA['predictions'].append(prediction)

            # Check if alert should be generated
            check_and_generate_alerts(data['worker_id'], prediction)

        return jsonify(result)

    except Exception as e:
        print(f"Error in predict_thermal_comfort: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/predict_batch', methods=['POST'])
@app.route('/api/predict_thermal_comfort_batch', methods=['POST'])
def predict_thermal_comfort_batch():
    """Predict thermal comfort for multiple readings."""
    try:
        if predictor is None:
            return jsonify({"error": "Predictor not initialized"}), 500

        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"error": "No 'data' array provided"}), 400

        predictions = []
        for item in data['data']:
            try:
                result = predictor.predict_single(item)
                predictions.append({
                    "input": item,
                    "prediction": result,
                    "success": True
                })

                # Store if worker_id provided
                if 'worker_id' in item:
                    # Store reading and prediction (similar to single predict)
                    reading = {
                        'id': len(DEMO_DATA['biometric_readings']) + 1,
                        'worker_id': item['worker_id'],
                        'timestamp': datetime.now().isoformat(),
                        **{k: v for k, v in item.items() if k != 'worker_id'}
                    }
                    DEMO_DATA['biometric_readings'].append(reading)

                    prediction_record = {
                        'id': len(DEMO_DATA['predictions']) + 1,
                        'worker_id': item['worker_id'],
                        'biometric_reading_id': reading['id'],
                        'timestamp': datetime.now().isoformat(),
                        'thermal_comfort': result.get('prediction', 'neutral'),
                        'risk_level': result.get('risk_assessment', 'comfortable'),
                        'confidence': result.get('confidence', 0.8),
                        'recommended_action': result.get('recommended_action', 'continue_monitoring'),
                        'break_recommendation_minutes': result.get('break_recommendation_minutes', 0),
                        'model_version': '1.0.0'
                    }
                    DEMO_DATA['predictions'].append(prediction_record)

                    check_and_generate_alerts(item['worker_id'], prediction_record)

            except Exception as e:
                predictions.append({
                    "input": item,
                    "error": str(e),
                    "success": False
                })

        return jsonify({
            "predictions": predictions,
            "total": len(predictions),
            "successful": len([p for p in predictions if p.get('success', False)])
        })

    except Exception as e:
        print(f"Error in predict_thermal_comfort_batch: {e}")
        return jsonify({"error": str(e)}), 500

# ===================================
# DATA GENERATION ENDPOINTS
# ===================================

@app.route('/generate_random', methods=['GET'])
@app.route('/api/generate_random_data', methods=['GET'])
def generate_random_data():
    """Generate random test data for demo purposes."""
    try:
        count = min(int(request.args.get('count', 5)), 20)  # Max 20 samples

        samples = []
        worker_ids = list(DEMO_DATA['workers'].keys()) if DEMO_DATA['workers'] else None

        for i in range(count):
            # Base environmental conditions
            base_temp = 22.0 + random.uniform(-5, 15)
            humidity = random.uniform(30, 85)

            sample = {
                'Gender': random.choice([0, 1]),
                'Age': random.randint(22, 65),
                'Temperature': round(base_temp, 2),
                'Humidity': round(humidity, 2),

                # All 51 HRV features with correct names for ML model
                'hrv_mean_nni': round(random.uniform(600, 1200), 2),
                'hrv_median_nni': round(random.uniform(580, 1180), 2),
                'hrv_range_nni': round(random.uniform(100, 800), 2),
                'hrv_sdsd': round(random.uniform(10, 100), 2),
                'hrv_rmssd': round(random.uniform(15, 120), 2),
                'hrv_nni_50': round(random.uniform(5, 200), 2),
                'hrv_pnni_50': round(random.uniform(0.5, 45), 2),
                'hrv_nni_20': round(random.uniform(20, 300), 2),
                'hrv_pnni_20': round(random.uniform(5, 70), 2),
                'hrv_cvsd': round(random.uniform(0.02, 0.15), 4),
                'hrv_sdnn': round(random.uniform(20, 150), 2),
                'hrv_cvnni': round(random.uniform(0.02, 0.12), 4),
                'hrv_mean_hr': round(random.uniform(60, 120), 2),
                'hrv_min_hr': round(random.uniform(50, 90), 2),
                'hrv_max_hr': round(random.uniform(90, 150), 2),
                'hrv_std_hr': round(random.uniform(5, 25), 2),
                'hrv_total_power': round(random.uniform(1000, 8000), 2),
                'hrv_vlf': round(random.uniform(300, 2000), 2),
                'hrv_lf': round(random.uniform(200, 1500), 2),
                'hrv_hf': round(random.uniform(150, 1200), 2),
                'hrv_lf_hf_ratio': round(random.uniform(0.5, 4.0), 2),
                'hrv_lfnu': round(random.uniform(20, 80), 2),
                'hrv_hfnu': round(random.uniform(20, 80), 2),
                'hrv_SD1': round(random.uniform(10, 80), 2),
                'hrv_SD2': round(random.uniform(30, 200), 2),
                'hrv_SD2SD1': round(random.uniform(1.5, 5.0), 2),
                'hrv_CSI': round(random.uniform(1, 8), 2),
                'hrv_CVI': round(random.uniform(2, 12), 2),
                'hrv_CSI_Modified': round(random.uniform(1.2, 9), 2),
                'hrv_mean': round(random.uniform(500, 1000), 2),
                'hrv_std': round(random.uniform(50, 300), 2),
                'hrv_min': round(random.uniform(400, 800), 2),
                'hrv_max': round(random.uniform(800, 1400), 2),
                'hrv_ptp': round(random.uniform(200, 800), 2),
                'hrv_sum': round(random.uniform(50000, 500000), 2),
                'hrv_energy': round(random.uniform(100000, 1000000), 2),
                'hrv_skewness': round(random.uniform(-2, 2), 3),
                'hrv_kurtosis': round(random.uniform(0, 10), 3),
                'hrv_peaks': round(random.uniform(50, 200), 2),
                'hrv_rms': round(random.uniform(400, 900), 2),
                'hrv_lineintegral': round(random.uniform(10000, 80000), 2),
                'hrv_n_above_mean': round(random.uniform(20, 60), 2),
                'hrv_n_below_mean': round(random.uniform(20, 60), 2),
                'hrv_n_sign_changes': round(random.uniform(30, 90), 2),
                'hrv_iqr': round(random.uniform(50, 300), 2),
                'hrv_iqr_5_95': round(random.uniform(200, 800), 2),
                'hrv_pct_5': round(random.uniform(500, 700), 2),
                'hrv_pct_95': round(random.uniform(900, 1300), 2),
                'hrv_entropy': round(random.uniform(0.5, 2.0), 3),
                'hrv_perm_entropy': round(random.uniform(0.3, 1.0), 3),
                'hrv_svd_entropy': round(random.uniform(0.4, 1.2), 3),

                # Additional fields for frontend display
                'AirVelocity': round(random.uniform(0.1, 2.0), 2),
                'HeartRate': round(random.uniform(60, 130), 1),
                'SkinTemperature': round(base_temp + random.uniform(-3, 5), 2),
                'CoreBodyTemperature': round(36.5 + random.uniform(0, 2.5), 2),
                'SkinConductance': round(random.uniform(0.1, 0.9), 3),
                'MetabolicRate': round(random.uniform(1.0, 3.5), 2),
                'ActivityLevel': random.randint(1, 5),
                'ClothingInsulation': round(random.uniform(0.3, 1.8), 2),
                'RespiratoryRate': round(random.uniform(12, 28), 1),
                'HydrationLevel': round(random.uniform(0.3, 1.0), 2)
            }

            # Optionally assign to a worker for tracking
            if worker_ids and random.choice([True, False]):
                sample['worker_id'] = random.choice(worker_ids)

            samples.append(sample)

        return jsonify({
            "data": samples,
            "count": len(samples),
            "generated_at": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================
# WORKER MANAGEMENT ENDPOINTS
# ===================================

@app.route('/api/workers', methods=['GET'])
def get_workers():
    """Get all workers."""
    try:
        workers = list(DEMO_DATA['workers'].values())

        # Add real-time status for each worker
        for worker in workers:
            worker['last_reading'] = get_latest_reading_time(worker['id'])
            worker['current_risk'] = get_current_risk_level(worker['id'])
            worker['active_alerts'] = len([a for a in DEMO_DATA['alerts']
                                         if a['worker_id'] == worker['id'] and not a['resolved']])

        return jsonify(workers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workers', methods=['POST'])
def create_worker():
    """Create a new worker."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        worker_id = f"worker_{len(DEMO_DATA['workers']) + 1:03d}"

        worker = {
            'id': worker_id,
            'name': data.get('name', 'Unknown Worker'),
            'age': data.get('age', 30),
            'gender': data.get('gender', 'male'),
            'medical_conditions': data.get('medical_conditions', []),
            'heat_tolerance': data.get('heat_tolerance', 'normal'),
            'emergency_contact': data.get('emergency_contact', {}),
            'assigned_location': data.get('assigned_location', 'Factory Floor A'),
            'shift_pattern': data.get('shift_pattern', 'Morning (6AM-2PM)'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'active'
        }

        DEMO_DATA['workers'][worker_id] = worker

        return jsonify(worker), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workers/<worker_id>', methods=['GET'])
def get_worker(worker_id):
    """Get a specific worker."""
    try:
        if worker_id not in DEMO_DATA['workers']:
            return jsonify({"error": "Worker not found"}), 404

        worker = DEMO_DATA['workers'][worker_id].copy()
        worker['last_reading'] = get_latest_reading_time(worker_id)
        worker['current_risk'] = get_current_risk_level(worker_id)
        worker['active_alerts'] = len([a for a in DEMO_DATA['alerts']
                                     if a['worker_id'] == worker_id and not a['resolved']])

        return jsonify(worker)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workers/<worker_id>', methods=['PUT'])
def update_worker(worker_id):
    """Update a worker."""
    try:
        if worker_id not in DEMO_DATA['workers']:
            return jsonify({"error": "Worker not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Update worker data
        worker = DEMO_DATA['workers'][worker_id]
        for key, value in data.items():
            if key != 'id':  # Don't allow ID changes
                worker[key] = value

        worker['updated_at'] = datetime.now().isoformat()

        return jsonify(worker)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workers/<worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    """Delete a worker."""
    try:
        if worker_id not in DEMO_DATA['workers']:
            return jsonify({"error": "Worker not found"}), 404

        del DEMO_DATA['workers'][worker_id]

        # Clean up related data
        DEMO_DATA['biometric_readings'] = [r for r in DEMO_DATA['biometric_readings']
                                         if r['worker_id'] != worker_id]
        DEMO_DATA['predictions'] = [p for p in DEMO_DATA['predictions']
                                  if p['worker_id'] != worker_id]
        DEMO_DATA['alerts'] = [a for a in DEMO_DATA['alerts']
                             if a['worker_id'] != worker_id]

        return jsonify({"message": "Worker deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================
# DASHBOARD METRICS ENDPOINT
# ===================================

@app.route('/api/dashboard_metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get dashboard metrics and statistics."""
    try:
        current_time = datetime.now()

        # Active workers count
        active_workers = len([w for w in DEMO_DATA['workers'].values() if w['status'] == 'active'])

        # Critical alerts count
        critical_alerts = len([a for a in DEMO_DATA['alerts']
                             if a['severity'] == 'critical' and not a['resolved']])

        # Unacknowledged alerts
        unacknowledged_alerts = len([a for a in DEMO_DATA['alerts']
                                   if not a['acknowledged']])

        # Average risk level (from recent predictions)
        recent_predictions = [p for p in DEMO_DATA['predictions']
                            if datetime.fromisoformat(p['timestamp']) > current_time - timedelta(hours=1)]

        risk_levels = {'comfortable': 1, 'slightly_uncomfortable': 2, 'uncomfortable': 3, 'very_uncomfortable': 4}
        avg_risk = 1.5  # Default
        if recent_predictions:
            risk_values = [risk_levels.get(p['risk_level'], 1) for p in recent_predictions]
            avg_risk = sum(risk_values) / len(risk_values)

        # Environmental conditions (simulated current conditions)
        environmental_conditions = {
            'temperature': round(random.uniform(20, 35), 1),
            'humidity': round(random.uniform(40, 70), 1),
            'air_quality_index': random.randint(50, 150),
            'wind_speed': round(random.uniform(0.5, 3.0), 1)
        }

        # Recent activity summary
        recent_readings = len([r for r in DEMO_DATA['biometric_readings']
                             if datetime.fromisoformat(r['timestamp']) > current_time - timedelta(hours=1)])

        # Risk distribution
        risk_distribution = defaultdict(int)
        for prediction in recent_predictions:
            risk_distribution[prediction['risk_level']] += 1

        # Location-based metrics
        location_metrics = {}
        for location in DEMO_DATA['locations']:
            location_workers = [w for w in DEMO_DATA['workers'].values()
                              if w['assigned_location'] == location]
            location_alerts = [a for a in DEMO_DATA['alerts']
                             if a['location'] == location and not a['resolved']]

            location_metrics[location] = {
                'workers_count': len(location_workers),
                'active_alerts': len(location_alerts),
                'risk_level': random.choice(['low', 'moderate', 'high'])  # Simulated
            }

        metrics = {
            'active_workers': active_workers,
            'total_workers': len(DEMO_DATA['workers']),
            'critical_alerts': critical_alerts,
            'unacknowledged_alerts': unacknowledged_alerts,
            'average_risk_level': round(avg_risk, 2),
            'environmental_conditions': environmental_conditions,
            'recent_readings_count': recent_readings,
            'risk_distribution': dict(risk_distribution),
            'location_metrics': location_metrics,
            'timestamp': current_time.isoformat(),

            # Additional demo metrics
            'system_status': 'operational',
            'model_accuracy': 0.87,
            'data_quality_score': 0.92,
            'compliance_score': 0.95  # OSHA compliance
        }

        # Cache the metrics
        DEMO_DATA['dashboard_cache'] = metrics

        return jsonify(metrics)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================
# ALERTS MANAGEMENT ENDPOINTS
# ===================================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get health alerts with optional filtering."""
    try:
        worker_id = request.args.get('worker_id')
        severity = request.args.get('severity')
        resolved = request.args.get('resolved')
        limit = int(request.args.get('limit', 50))

        alerts = DEMO_DATA['alerts'].copy()

        # Apply filters
        if worker_id:
            alerts = [a for a in alerts if a['worker_id'] == worker_id]
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        if resolved is not None:
            resolved_bool = resolved.lower() == 'true'
            alerts = [a for a in alerts if a['resolved'] == resolved_bool]

        # Sort by timestamp (newest first) and limit
        alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)[:limit]

        # Enrich with worker names
        for alert in alerts:
            worker = DEMO_DATA['workers'].get(alert['worker_id'])
            if worker:
                alert['worker_name'] = worker['name']

        return jsonify(alerts)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new health alert."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        alert = {
            'id': str(uuid.uuid4()),
            'worker_id': data.get('worker_id'),
            'alert_type': data.get('alert_type', 'general_warning'),
            'severity': data.get('severity', 'moderate'),
            'message': data.get('message', 'Health monitoring alert'),
            'recommended_actions': data.get('recommended_actions', ['Monitor worker']),
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False,
            'resolved': False,
            'location': data.get('location', 'Unknown')
        }

        DEMO_DATA['alerts'].append(alert)

        return jsonify(alert), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert."""
    try:
        alert = next((a for a in DEMO_DATA['alerts'] if a['id'] == alert_id), None)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404

        alert['acknowledged'] = True
        alert['acknowledged_at'] = datetime.now().isoformat()

        return jsonify(alert)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert."""
    try:
        alert = next((a for a in DEMO_DATA['alerts'] if a['id'] == alert_id), None)
        if not alert:
            return jsonify({"error": "Alert not found"}), 404

        alert['resolved'] = True
        alert['resolved_at'] = datetime.now().isoformat()

        return jsonify(alert)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================
# REAL-TIME AND HISTORICAL DATA
# ===================================

@app.route('/api/workers/<worker_id>/realtime', methods=['GET'])
def get_realtime_worker_data(worker_id):
    """Get real-time data for a specific worker."""
    try:
        if worker_id not in DEMO_DATA['workers']:
            return jsonify({"error": "Worker not found"}), 404

        # Get the most recent reading for this worker
        worker_readings = [r for r in DEMO_DATA['biometric_readings']
                          if r['worker_id'] == worker_id]

        if not worker_readings:
            # Generate a live reading for demo
            worker = DEMO_DATA['workers'][worker_id]
            live_reading = generate_live_reading_for_worker(worker)
        else:
            # Get the latest reading and update timestamp
            live_reading = sorted(worker_readings, key=lambda x: x['timestamp'])[-1].copy()
            live_reading['timestamp'] = datetime.now().isoformat()

        return jsonify(live_reading)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/workers/<worker_id>/historical', methods=['GET'])
def get_historical_worker_data(worker_id):
    """Get historical data for a specific worker."""
    try:
        if worker_id not in DEMO_DATA['workers']:
            return jsonify({"error": "Worker not found"}), 404

        start_date = request.args.get('start')
        end_date = request.args.get('end')

        # Get worker's readings
        worker_readings = [r for r in DEMO_DATA['biometric_readings']
                          if r['worker_id'] == worker_id]

        # Get worker's predictions
        worker_predictions = [p for p in DEMO_DATA['predictions']
                            if p['worker_id'] == worker_id]

        # Apply date filtering if provided
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            worker_readings = [r for r in worker_readings
                             if datetime.fromisoformat(r['timestamp']) >= start_dt]
            worker_predictions = [p for p in worker_predictions
                                if datetime.fromisoformat(p['timestamp']) >= start_dt]

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            worker_readings = [r for r in worker_readings
                             if datetime.fromisoformat(r['timestamp']) <= end_dt]
            worker_predictions = [p for p in worker_predictions
                                if datetime.fromisoformat(p['timestamp']) <= end_dt]

        # Sort by timestamp
        worker_readings = sorted(worker_readings, key=lambda x: x['timestamp'])
        worker_predictions = sorted(worker_predictions, key=lambda x: x['timestamp'])

        historical_data = {
            'worker_id': worker_id,
            'readings': worker_readings,
            'predictions': worker_predictions,
            'summary': {
                'total_readings': len(worker_readings),
                'total_predictions': len(worker_predictions),
                'date_range': {
                    'start': worker_readings[0]['timestamp'] if worker_readings else None,
                    'end': worker_readings[-1]['timestamp'] if worker_readings else None
                }
            }
        }

        return jsonify(historical_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================
# HELPER FUNCTIONS
# ===================================

def get_latest_reading_time(worker_id):
    """Get the timestamp of the latest reading for a worker."""
    worker_readings = [r for r in DEMO_DATA['biometric_readings']
                      if r['worker_id'] == worker_id]
    if worker_readings:
        return sorted(worker_readings, key=lambda x: x['timestamp'])[-1]['timestamp']
    return None

def get_current_risk_level(worker_id):
    """Get the current risk level for a worker based on latest prediction."""
    worker_predictions = [p for p in DEMO_DATA['predictions']
                         if p['worker_id'] == worker_id]
    if worker_predictions:
        return sorted(worker_predictions, key=lambda x: x['timestamp'])[-1]['risk_level']
    return 'unknown'

def generate_live_reading_for_worker(worker):
    """Generate a realistic live reading for a worker."""
    base_temp = 22.0 + random.uniform(-2, 10)

    reading = {
        'id': len(DEMO_DATA['biometric_readings']) + 1,
        'worker_id': worker['id'],
        'timestamp': datetime.now().isoformat(),
        'Gender': 1 if worker['gender'] == 'male' else 0,
        'Age': worker['age'],
        'Temperature': round(base_temp, 2),
        'Humidity': round(random.uniform(35, 75), 2),
        'AirVelocity': round(random.uniform(0.2, 1.8), 2),
        'HeartRate': round(random.uniform(65, 115), 1),
        'SkinTemperature': round(base_temp + random.uniform(-2, 4), 2),
        'CoreBodyTemperature': round(36.5 + random.uniform(0, 1.5), 2),
        'SkinConductance': round(random.uniform(0.2, 0.8), 3),
        'MetabolicRate': round(random.uniform(1.2, 3.0), 2),
        'ActivityLevel': random.randint(1, 4),
        'ClothingInsulation': round(random.uniform(0.4, 1.4), 2),
        'RespiratoryRate': round(random.uniform(14, 24), 1),
        'HydrationLevel': round(random.uniform(0.4, 0.9), 2),
        'location_id': worker['assigned_location']
    }

    return reading

def check_and_generate_alerts(worker_id, prediction):
    """Check if an alert should be generated based on prediction."""
    if not worker_id or worker_id not in DEMO_DATA['workers']:
        return

    worker = DEMO_DATA['workers'][worker_id]

    # Generate alerts based on risk level and other conditions
    if prediction['risk_level'] in ['very_uncomfortable'] and prediction['confidence'] > 0.7:
        alert = {
            'id': str(uuid.uuid4()),
            'worker_id': worker_id,
            'alert_type': 'heat_exhaustion_risk',
            'severity': 'critical',
            'message': f"Critical heat risk detected for {worker['name']} - immediate attention required",
            'recommended_actions': [
                'Move worker to cooler area immediately',
                'Provide water and electrolytes',
                'Monitor vital signs',
                'Consider medical attention'
            ],
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False,
            'resolved': False,
            'location': worker['assigned_location']
        }

        # Only add if similar alert doesn't exist in last 30 minutes
        recent_alerts = [a for a in DEMO_DATA['alerts']
                        if a['worker_id'] == worker_id
                        and a['alert_type'] == 'heat_exhaustion_risk'
                        and datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(minutes=30)]

        if not recent_alerts:
            DEMO_DATA['alerts'].append(alert)

# ===================================
# API DOCUMENTATION ENDPOINT
# ===================================

@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
def api_documentation():
    """API documentation and available endpoints."""
    return jsonify({
        "name": "HeatGuard Pro - Enhanced Thermal Comfort API",
        "version": "2.0.0",
        "description": "Advanced thermal comfort prediction and worker safety monitoring system",
        "endpoints": {
            "Health & Status": {
                "GET /health": "System health check and status",
            },
            "Thermal Comfort Prediction": {
                "POST /api/predict_thermal_comfort": "Single thermal comfort prediction",
                "POST /api/predict_thermal_comfort_batch": "Batch thermal comfort predictions",
                "GET /api/generate_random_data": "Generate random test data"
            },
            "Worker Management": {
                "GET /api/workers": "Get all workers",
                "POST /api/workers": "Create new worker",
                "GET /api/workers/{id}": "Get specific worker",
                "PUT /api/workers/{id}": "Update worker",
                "DELETE /api/workers/{id}": "Delete worker",
                "GET /api/workers/{id}/realtime": "Get real-time worker data",
                "GET /api/workers/{id}/historical": "Get historical worker data"
            },
            "Dashboard & Analytics": {
                "GET /api/dashboard_metrics": "Get dashboard metrics and statistics"
            },
            "Alert Management": {
                "GET /api/alerts": "Get health alerts (with filtering)",
                "POST /api/alerts": "Create new alert",
                "POST /api/alerts/{id}/acknowledge": "Acknowledge alert",
                "POST /api/alerts/{id}/resolve": "Resolve alert"
            }
        },
        "data_storage": "In-memory (demo only)",
        "workers_count": len(DEMO_DATA['workers']),
        "predictions_count": len(DEMO_DATA['predictions']),
        "alerts_count": len(DEMO_DATA['alerts'])
    })

# ===================================
# APPLICATION INITIALIZATION
# ===================================

def initialize_application():
    """Initialize the complete application."""
    print("🚀 HEATGUARD PRO - ENHANCED FLASK API")
    print("=" * 50)

    # Initialize ML predictor
    print("🤖 Initializing thermal comfort predictor...")
    if not initialize_predictor():
        print("❌ Failed to initialize predictor")
        return False

    # Initialize demo data
    print("🎭 Setting up demo data...")
    initialize_demo_data()

    print("✅ Application initialized successfully!")
    print(f"📊 Demo data: {len(DEMO_DATA['workers'])} workers, {len(DEMO_DATA['biometric_readings'])} readings")
    print(f"🚨 Sample alerts: {len(DEMO_DATA['alerts'])} alerts generated")

    return True

if __name__ == "__main__":
    if initialize_application():
        print("\n🌐 Starting Flask server...")
        print("📡 API available at:")
        print("   • Local: http://localhost:5000")
        print("   • Documentation: http://localhost:5000/api")
        print("\n⚠️  Press Ctrl+C to stop")
        print("=" * 50)

        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    else:
        print("❌ Application initialization failed")
        exit(1)