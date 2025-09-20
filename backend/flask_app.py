"""
Thermal Comfort Prediction Flask API
===================================

A Flask web application that provides thermal comfort predictions
from wearable device data with data generation utilities.

Endpoints:
- POST /predict: Single prediction
- POST /predict_batch: Batch predictions
- GET /generate_random: Generate random test data
- GET /generate_ramp_up: Generate data ramping from green to red
- GET /generate_ramp_down: Generate data ramping from red to green
- GET /health: Health check
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from datetime import datetime
import traceback
from predict_thermal_comfort import ThermalComfortPredictor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global predictor instance
predictor = None

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

def generate_base_features():
    """Generate base feature template with comfortable baseline values."""
    return {
        # Demographics
        'Gender': 1,  # Male
        'Age': 30,
        
        # Environmental (will be modified for ramping)
        'Temperature': 22.0,
        'Humidity': 50.0,
        
        # HRV Features (comfortable baseline values)
        'hrv_mean_nni': 850,
        'hrv_median_nni': 860,
        'hrv_range_nni': 400,
        'hrv_sdsd': 45,
        'hrv_rmssd': 42,
        'hrv_nni_50': 25,
        'hrv_pnni_50': 15,
        'hrv_nni_20': 45,
        'hrv_pnni_20': 35,
        'hrv_cvsd': 0.05,
        'hrv_sdnn': 50,
        'hrv_cvnni': 0.06,
        'hrv_mean_hr': 70,
        'hrv_min_hr': 60,
        'hrv_max_hr': 85,
        'hrv_std_hr': 8,
        'hrv_total_power': 3000,
        'hrv_vlf': 800,
        'hrv_lf': 1200,
        'hrv_hf': 1000,
        'hrv_lf_hf_ratio': 1.2,
        'hrv_lfnu': 55,
        'hrv_hfnu': 45,
        'hrv_SD1': 30,
        'hrv_SD2': 65,
        'hrv_SD2SD1': 2.2,
        'hrv_CSI': 2.5,
        'hrv_CVI': 3.2,
        'hrv_CSI_Modified': 2.8,
        'hrv_mean': 850,
        'hrv_std': 45,
        'hrv_min': 650,
        'hrv_max': 1050,
        'hrv_ptp': 400,
        'hrv_sum': 108800,
        'hrv_energy': 92500000,
        'hrv_skewness': 0.2,
        'hrv_kurtosis': 2.8,
        'hrv_peaks': 128,
        'hrv_rms': 855,
        'hrv_lineintegral': 54400,
        'hrv_n_above_mean': 64,
        'hrv_n_below_mean': 64,
        'hrv_n_sign_changes': 45,
        'hrv_iqr': 60,
        'hrv_iqr_5_95': 320,
        'hrv_pct_5': 720,
        'hrv_pct_95': 1040,
        'hrv_entropy': 4.8,
        'hrv_perm_entropy': 0.95,
        'hrv_svd_entropy': 0.65
    }

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    global predictor
    return jsonify({
        'status': 'healthy' if predictor is not None else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': predictor is not None
    })

@app.route('/predict', methods=['POST'])
def predict_single():
    """Single prediction endpoint."""
    try:
        if predictor is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract parameters
        features = data.get('features', {})
        use_conservative = data.get('use_conservative', True)
        conservative_bias = data.get('conservative_bias', None)
        
        if not features:
            return jsonify({'error': 'No features provided'}), 400
        
        # Make prediction
        result = predictor.predict_single(
            features, 
            use_conservative=use_conservative,
            conservative_bias=conservative_bias
        )
        
        return jsonify({
            'success': True,
            'prediction': result,
            'request_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    """Batch prediction endpoint."""
    try:
        if predictor is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract parameters
        features_list = data.get('features_list', [])
        use_conservative = data.get('use_conservative', True)
        conservative_bias = data.get('conservative_bias', None)
        
        if not features_list:
            return jsonify({'error': 'No features list provided'}), 400
        
        # Convert to DataFrame
        features_df = pd.DataFrame(features_list)
        
        # Make predictions
        results = predictor.predict_batch(
            features_df,
            use_conservative=use_conservative,
            conservative_bias=conservative_bias
        )
        
        return jsonify({
            'success': True,
            'predictions': results,
            'count': len(results),
            'request_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/features', methods=['GET'])
def get_features():
    """Get the list of required features for predictions."""
    try:
        if predictor is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        # Get feature template
        template = predictor.get_feature_template()
        
        # Categorize features
        hrv_features = [f for f in predictor.feature_columns if f.startswith('hrv_')]
        demo_features = [f for f in predictor.feature_columns if f in ['Gender', 'Age']]
        env_features = [f for f in predictor.feature_columns if f in ['Temperature', 'Humidity']]
        
        return jsonify({
            'success': True,
            'required_features': predictor.feature_columns,
            'feature_template': template,
            'feature_categories': {
                'demographics': {
                    'features': demo_features,
                    'count': len(demo_features),
                    'description': 'User demographic information'
                },
                'environmental': {
                    'features': env_features,
                    'count': len(env_features),
                    'description': 'Environmental sensor data'
                },
                'hrv': {
                    'features': hrv_features,
                    'count': len(hrv_features),
                    'description': 'Heart rate variability metrics from wearable device'
                }
            },
            'total_features': len(predictor.feature_columns),
            'feature_notes': {
                'Gender': 'Use 1 for Male, 0 for Female',
                'Age': 'Age in years',
                'Temperature': 'Temperature in Celsius',
                'Humidity': 'Humidity percentage (0-100)',
                'hrv_*': 'Heart rate variability metrics from wearable device'
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/validate_features', methods=['POST'])
def validate_features():
    """Validate that the provided feature data is in the correct format."""
    try:
        if predictor is None:
            return jsonify({'error': 'Model not loaded'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        features = data.get('features', {})
        if not features:
            return jsonify({'error': 'No features provided'}), 400
        
        # Check for required features
        required_features = set(predictor.feature_columns)
        provided_features = set(features.keys())
        
        missing_features = required_features - provided_features
        extra_features = provided_features - required_features
        
        # Validate data types and ranges
        validation_errors = []
        
        for feature, value in features.items():
            if feature in required_features:
                # Check if value is numeric
                try:
                    float(value)
                except (ValueError, TypeError):
                    validation_errors.append(f"{feature}: must be numeric, got {type(value).__name__}")
                    continue
                
                # Specific validations
                if feature == 'Gender' and value not in [0, 1]:
                    validation_errors.append(f"Gender: must be 0 (Female) or 1 (Male), got {value}")
                elif feature == 'Age' and (value < 0 or value > 120):
                    validation_errors.append(f"Age: must be between 0-120, got {value}")
                elif feature == 'Temperature' and (value < -50 or value > 60):
                    validation_errors.append(f"Temperature: unrealistic value {value}°C")
                elif feature == 'Humidity' and (value < 0 or value > 100):
                    validation_errors.append(f"Humidity: must be between 0-100%, got {value}")
        
        is_valid = len(missing_features) == 0 and len(validation_errors) == 0
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'validation_result': {
                'missing_features': list(missing_features),
                'extra_features': list(extra_features),
                'validation_errors': validation_errors,
                'total_features_provided': len(provided_features),
                'total_features_required': len(required_features)
            },
            'message': 'Validation passed' if is_valid else 'Validation failed',
            'ready_for_prediction': is_valid
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/generate_random', methods=['GET'])
def generate_random():
    """Generate random test data with varied temperature and basic physiological changes."""
    try:
        num_samples = request.args.get('num_samples', 1, type=int)
        num_samples = min(max(num_samples, 1), 20)  # Limit between 1-20
        
        samples = []
        base = generate_base_features()
        
        for i in range(num_samples):
            sample = base.copy()
            
            # Randomize temperature (main driver)
            temp = round(np.random.uniform(18, 38), 1)
            sample['Temperature'] = temp
            
            # Adjust humidity slightly
            sample['Humidity'] = round(np.random.uniform(40, 80), 1)
            
            # Adjust physiological parameters based on temperature stress
            temp_stress = max(0, (temp - 25) / 10)  # 0 to 1.3 stress factor
            
            sample['hrv_mean_hr'] = round(70 + temp_stress * 25, 1)  # 70-95 bpm
            sample['hrv_mean_nni'] = round(850 - temp_stress * 200, 1)  # 850-650 ms
            sample['hrv_sdnn'] = round(50 - temp_stress * 25, 1)  # 50-25 ms
            sample['hrv_total_power'] = round(3000 - temp_stress * 1500, 1)  # 3000-1500
            
            samples.append(sample)
        
        return jsonify({
            'success': True,
            'data': samples if num_samples > 1 else samples[0],
            'count': num_samples,
            'type': 'random',
            'description': f'Random samples with temperatures from 18-38°C',
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/generate_ramp_up', methods=['GET'])
def generate_ramp_up():
    """Generate data ramping from comfortable (green) to critical (red) by increasing temperature."""
    try:
        num_steps = request.args.get('num_steps', 10, type=int)
        num_steps = min(max(num_steps, 3), 20)  # Limit between 3-20
        
        samples = []
        base = generate_base_features()
        
        # Temperature range: 20°C (comfortable) to 38°C (critical)
        temp_start = 20
        temp_end = 38
        temp_range = temp_end - temp_start
        
        for i in range(num_steps):
            progress = i / (num_steps - 1)  # 0 to 1
            
            sample = base.copy()
            
            # Main driver: Temperature increase
            temperature = temp_start + (progress * temp_range)
            sample['Temperature'] = round(temperature, 1)
            
            # Humidity increases slightly with temperature
            sample['Humidity'] = round(45 + progress * 35, 1)  # 45% to 80%
            
            # Physiological stress responses to temperature
            stress_factor = progress  # 0 to 1
            
            # Heart rate increases with thermal stress
            sample['hrv_mean_hr'] = round(68 + stress_factor * 27, 1)  # 68-95 bpm
            
            # HRV decreases with stress (less variability = more stress)
            sample['hrv_mean_nni'] = round(870 - stress_factor * 220, 1)  # 870-650 ms
            sample['hrv_sdnn'] = round(52 - stress_factor * 27, 1)  # 52-25 ms
            sample['hrv_rmssd'] = round(45 - stress_factor * 25, 1)  # 45-20 ms
            
            # Power spectral density decreases
            sample['hrv_total_power'] = round(3200 - stress_factor * 1700, 1)  # 3200-1500
            sample['hrv_hf'] = round(1100 - stress_factor * 600, 1)  # 1100-500
            
            # LF/HF ratio increases (sympathetic dominance)
            sample['hrv_lf_hf_ratio'] = round(1.1 + stress_factor * 1.4, 2)  # 1.1-2.5
            
            # Description based on temperature
            if temperature < 24:
                description = f"Comfortable: {temperature}°C - Optimal thermal conditions"
            elif temperature < 28:
                description = f"Mild warmth: {temperature}°C - Slight thermal stress"
            elif temperature < 32:
                description = f"Warm: {temperature}°C - Moderate thermal stress"
            elif temperature < 36:
                description = f"Hot: {temperature}°C - High thermal stress"
            else:
                description = f"Critical: {temperature}°C - Dangerous thermal stress"
            
            samples.append({
                'step': i + 1,
                'temperature': temperature,
                'progress_percent': round(progress * 100, 1),
                'features': sample,
                'description': description
            })
        
        return jsonify({
            'success': True,
            'data': samples,
            'count': num_steps,
            'type': 'ramp_up',
            'description': f'Temperature ramp from {temp_start}°C to {temp_end}°C (Green → Red)',
            'temperature_range': f'{temp_start}°C → {temp_end}°C',
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/generate_ramp_down', methods=['GET'])
def generate_ramp_down():
    """Generate data ramping from critical (red) to comfortable (green) by decreasing temperature."""
    try:
        num_steps = request.args.get('num_steps', 10, type=int)
        num_steps = min(max(num_steps, 3), 20)  # Limit between 3-20
        
        samples = []
        base = generate_base_features()
        
        # Temperature range: 38°C (critical) to 20°C (comfortable)
        temp_start = 38
        temp_end = 20
        temp_range = temp_start - temp_end
        
        for i in range(num_steps):
            progress = i / (num_steps - 1)  # 0 to 1 (cooling progress)
            
            sample = base.copy()
            
            # Main driver: Temperature decrease
            temperature = temp_start - (progress * temp_range)
            sample['Temperature'] = round(temperature, 1)
            
            # Humidity decreases with temperature
            sample['Humidity'] = round(80 - progress * 35, 1)  # 80% to 45%
            
            # Physiological recovery from thermal stress
            stress_factor = 1 - progress  # 1 to 0 (decreasing stress)
            
            # Heart rate decreases as temperature cools
            sample['hrv_mean_hr'] = round(68 + stress_factor * 27, 1)  # 95-68 bpm
            
            # HRV increases with recovery (more variability = less stress)
            sample['hrv_mean_nni'] = round(870 - stress_factor * 220, 1)  # 650-870 ms
            sample['hrv_sdnn'] = round(52 - stress_factor * 27, 1)  # 25-52 ms
            sample['hrv_rmssd'] = round(45 - stress_factor * 25, 1)  # 20-45 ms
            
            # Power spectral density increases
            sample['hrv_total_power'] = round(3200 - stress_factor * 1700, 1)  # 1500-3200
            sample['hrv_hf'] = round(1100 - stress_factor * 600, 1)  # 500-1100
            
            # LF/HF ratio decreases (parasympathetic recovery)
            sample['hrv_lf_hf_ratio'] = round(1.1 + stress_factor * 1.4, 2)  # 2.5-1.1
            
            # Description based on temperature
            if temperature > 36:
                description = f"Critical: {temperature}°C - Dangerous thermal stress"
            elif temperature > 32:
                description = f"Hot: {temperature}°C - High thermal stress"
            elif temperature > 28:
                description = f"Warm: {temperature}°C - Moderate thermal stress"
            elif temperature > 24:
                description = f"Mild warmth: {temperature}°C - Slight thermal stress"
            else:
                description = f"Comfortable: {temperature}°C - Optimal thermal conditions"
            
            samples.append({
                'step': i + 1,
                'temperature': temperature,
                'recovery_percent': round(progress * 100, 1),
                'features': sample,
                'description': description
            })
        
        return jsonify({
            'success': True,
            'data': samples,
            'count': num_steps,
            'type': 'ramp_down',
            'description': f'Temperature ramp from {temp_start}°C to {temp_end}°C (Red → Green)',
            'temperature_range': f'{temp_start}°C → {temp_end}°C',
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def api_info():
    """API documentation endpoint."""
    return jsonify({
        'message': 'Thermal Comfort Prediction API',
        'version': '1.0.0',
        'description': 'API for predicting thermal comfort from wearable device data',
        'endpoints': {
            'GET /': 'API documentation',
            'GET /health': 'Health check',
            'POST /predict': 'Single prediction from frontend data',
            'POST /predict_batch': 'Batch predictions from frontend data list',
            'GET /features': 'Get required feature list',
            'POST /validate_features': 'Validate feature data format',
            'GET /generate_random': 'Generate random test data',
            'GET /generate_ramp_up': 'Generate data ramping from green to red (temperature increase)',
            'GET /generate_ramp_down': 'Generate data ramping from red to green (temperature decrease)'
        },
        'model_status': 'loaded' if predictor is not None else 'not_loaded',
        'conservative_bias': 0.15,
        'score_interpretation': {
            '0.0-0.25': 'Comfortable (Green)',
            '0.25-0.5': 'Slightly Uncomfortable (Yellow)', 
            '0.5-0.75': 'Uncomfortable (Orange)',
            '0.75-1.0': 'Very Uncomfortable (Red)'
        }
    })

if __name__ == '__main__':
    print("🌡️ Starting Thermal Comfort Prediction API...")
    
    # Initialize predictor
    if initialize_predictor():
        print("🚀 Starting Flask server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        print("❌ Failed to start server - model not loaded")
        print("Make sure you've trained the model first by running main.py")