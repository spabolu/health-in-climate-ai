"""
Test Script for Thermal Comfort Prediction API
==============================================

This script demonstrates how to use the API with frontend data.
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:5000"

def test_api_connection():
    """Test basic API connection."""
    print("🔗 Testing API Connection...")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Connected: {data['message']}")
            print(f"✅ Model Status: {data['model_status']}")
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_health_check():
    """Test health check endpoint."""
    print("\n🏥 Testing Health Check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        data = response.json()
        print(f"✅ Health Status: {data['status']}")
        print(f"✅ Model Loaded: {data['model_loaded']}")
        return data['status'] == 'healthy'
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def get_required_features():
    """Get the list of required features."""
    print("\n📋 Getting Required Features...")
    try:
        response = requests.get(f"{API_BASE}/features")
        data = response.json()
        
        if data['success']:
            print(f"✅ Total Features Required: {data['total_features']}")
            print(f"✅ Demographics: {data['feature_categories']['demographics']['count']}")
            print(f"✅ Environmental: {data['feature_categories']['environmental']['count']}")
            print(f"✅ HRV Metrics: {data['feature_categories']['hrv']['count']}")
            return data['feature_template']
        else:
            print(f"❌ Error: {data['error']}")
            return None
    except Exception as e:
        print(f"❌ Features Error: {e}")
        return None

def create_sample_data():
    """Create sample wearable device data."""
    return {
        # Demographics
        'Gender': 1,  # Male
        'Age': 30,
        
        # Environmental sensors
        'Temperature': 28.5,  # Warm temperature
        'Humidity': 65,       # High humidity
        
        # Heart Rate Variability from wearable device
        'hrv_mean_nni': 750,
        'hrv_median_nni': 760,
        'hrv_range_nni': 350,
        'hrv_sdsd': 40,
        'hrv_rmssd': 38,
        'hrv_nni_50': 20,
        'hrv_pnni_50': 12,
        'hrv_nni_20': 40,
        'hrv_pnni_20': 30,
        'hrv_cvsd': 0.05,
        'hrv_sdnn': 45,
        'hrv_cvnni': 0.06,
        'hrv_mean_hr': 80,  # Elevated heart rate
        'hrv_min_hr': 65,
        'hrv_max_hr': 95,
        'hrv_std_hr': 10,
        'hrv_total_power': 2500,  # Reduced power (stress indicator)
        'hrv_vlf': 700,
        'hrv_lf': 1000,
        'hrv_hf': 800,
        'hrv_lf_hf_ratio': 1.25,  # Slightly elevated
        'hrv_lfnu': 55,
        'hrv_hfnu': 45,
        'hrv_SD1': 27,
        'hrv_SD2': 60,
        'hrv_SD2SD1': 2.2,
        'hrv_CSI': 2.3,
        'hrv_CVI': 3.0,
        'hrv_CSI_Modified': 2.6,
        'hrv_mean': 750,
        'hrv_std': 40,
        'hrv_min': 600,
        'hrv_max': 950,
        'hrv_ptp': 350,
        'hrv_sum': 96000,
        'hrv_energy': 85000000,
        'hrv_skewness': 0.3,
        'hrv_kurtosis': 2.9,
        'hrv_peaks': 128,
        'hrv_rms': 755,
        'hrv_lineintegral': 48000,
        'hrv_n_above_mean': 60,
        'hrv_n_below_mean': 68,
        'hrv_n_sign_changes': 42,
        'hrv_iqr': 55,
        'hrv_iqr_5_95': 280,
        'hrv_pct_5': 650,
        'hrv_pct_95': 930,
        'hrv_entropy': 4.6,
        'hrv_perm_entropy': 0.92,
        'hrv_svd_entropy': 0.62
    }

def test_feature_validation():
    """Test feature validation endpoint."""
    print("\n✅ Testing Feature Validation...")
    
    sample_data = create_sample_data()
    
    try:
        response = requests.post(
            f"{API_BASE}/validate_features",
            json={'features': sample_data},
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if data['success']:
            result = data['validation_result']
            print(f"✅ Validation Result: {data['message']}")
            print(f"✅ Ready for Prediction: {data['ready_for_prediction']}")
            print(f"✅ Features Provided: {result['total_features_provided']}")
            print(f"✅ Features Required: {result['total_features_required']}")
            
            if result['missing_features']:
                print(f"⚠️  Missing Features: {result['missing_features']}")
            if result['validation_errors']:
                print(f"❌ Validation Errors: {result['validation_errors']}")
                
            return data['ready_for_prediction']
        else:
            print(f"❌ Validation Error: {data['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Validation Request Error: {e}")
        return False

def test_single_prediction():
    """Test single prediction with sample data."""
    print("\n🎯 Testing Single Prediction...")
    
    sample_data = create_sample_data()
    
    try:
        response = requests.post(
            f"{API_BASE}/predict",
            json={
                'features': sample_data,
                'use_conservative': True,
                'conservative_bias': 0.15
            },
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if data['success']:
            pred = data['prediction']
            print(f"✅ Prediction Successful!")
            print(f"🎯 Predicted Class: {pred['predicted_class']}")
            print(f"📊 Comfort Score: {pred['comfort_score_final']:.4f}")
            print(f"🎨 Comfort Level: {pred['comfort_level']}")
            print(f"⚠️  Risk Assessment: {pred['risk_assessment']}")
            print(f"🔒 Confidence: {pred['confidence']:.3f}")
            print(f"⚖️  Conservative Bias: +{pred['conservative_bias']}")
            
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(pred['recommendations'], 1):
                print(f"   {i}. {rec}")
            
            print(f"\n📈 Class Probabilities:")
            for class_name, prob in pred['class_probabilities'].items():
                print(f"   • {class_name}: {prob:.3f}")
                
            return pred
        else:
            print(f"❌ Prediction Error: {data['error']}")
            return None
            
    except Exception as e:
        print(f"❌ Prediction Request Error: {e}")
        return None

def test_batch_prediction():
    """Test batch prediction with multiple samples."""
    print("\n📊 Testing Batch Prediction...")
    
    # Create multiple samples with different stress levels
    samples = []
    
    # Comfortable sample
    comfortable = create_sample_data()
    comfortable.update({
        'Temperature': 23,
        'Humidity': 45,
        'hrv_mean_hr': 70,
        'hrv_sdnn': 55,
        'hrv_total_power': 3200
    })
    samples.append(comfortable)
    
    # Moderate stress sample
    moderate = create_sample_data()
    moderate.update({
        'Temperature': 27,
        'Humidity': 60,
        'hrv_mean_hr': 78,
        'hrv_sdnn': 42,
        'hrv_total_power': 2400
    })
    samples.append(moderate)
    
    # High stress sample
    high_stress = create_sample_data()
    high_stress.update({
        'Temperature': 32,
        'Humidity': 80,
        'hrv_mean_hr': 90,
        'hrv_sdnn': 30,
        'hrv_total_power': 1800
    })
    samples.append(high_stress)
    
    try:
        response = requests.post(
            f"{API_BASE}/predict_batch",
            json={
                'features_list': samples,
                'use_conservative': True
            },
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if data['success']:
            predictions = data['predictions']
            print(f"✅ Batch Prediction Successful!")
            print(f"📊 Processed {data['count']} samples")
            
            print(f"\n📈 Results Summary:")
            print(f"{'Sample':<8} {'Score':<8} {'Level':<20} {'Risk':<15} {'Class'}")
            print("-" * 65)
            
            for i, pred in enumerate(predictions, 1):
                score = pred['comfort_score_final']
                level = pred['comfort_level']
                risk = pred['risk_assessment']
                class_name = pred['predicted_class']
                
                print(f"{i:<8} {score:<8.3f} {level:<20} {risk:<15} {class_name}")
                
            return predictions
        else:
            print(f"❌ Batch Prediction Error: {data['error']}")
            return None
            
    except Exception as e:
        print(f"❌ Batch Prediction Request Error: {e}")
        return None

def test_data_generation():
    """Test data generation endpoints."""
    print("\n🎲 Testing Data Generation Endpoints...")
    
    try:
        # Test random data generation
        print("  Testing random data generation...")
        response = requests.get(f"{API_BASE}/generate_random?num_samples=3")
        data = response.json()
        
        if data['success']:
            samples = data['data'] if isinstance(data['data'], list) else [data['data']]
            print(f"  ✅ Random data: {data['count']} samples generated")
            print(f"     Temperature range: {min(s['Temperature'] for s in samples):.1f}°C - {max(s['Temperature'] for s in samples):.1f}°C")
        else:
            print(f"  ❌ Random data error: {data['error']}")
        
        # Test ramp up data generation
        print("  Testing ramp up data generation...")
        response = requests.get(f"{API_BASE}/generate_ramp_up?num_steps=5")
        data = response.json()
        
        if data['success']:
            print(f"  ✅ Ramp up data: {data['count']} steps generated")
            print(f"     {data['temperature_range']} - Green → Red")
            
            # Show temperature progression
            temps = [step['temperature'] for step in data['data']]
            print(f"     Progression: {temps[0]:.1f}°C → {temps[-1]:.1f}°C")
        else:
            print(f"  ❌ Ramp up error: {data['error']}")
        
        # Test ramp down data generation
        print("  Testing ramp down data generation...")
        response = requests.get(f"{API_BASE}/generate_ramp_down?num_steps=5")
        data = response.json()
        
        if data['success']:
            print(f"  ✅ Ramp down data: {data['count']} steps generated")
            print(f"     {data['temperature_range']} - Red → Green")
            
            # Show temperature progression
            temps = [step['temperature'] for step in data['data']]
            print(f"     Progression: {temps[0]:.1f}°C → {temps[-1]:.1f}°C")
        else:
            print(f"  ❌ Ramp down error: {data['error']}")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Data generation test error: {e}")
        return False

def main():
    """Run all API tests."""
    print("🌡️ THERMAL COMFORT PREDICTION API TESTS")
    print("=" * 60)
    
    # Test connection
    if not test_api_connection():
        print("❌ Cannot connect to API. Make sure the server is running.")
        return
    
    # Test health
    if not test_health_check():
        print("❌ API is not healthy. Check model loading.")
        return
    
    # Get features
    template = get_required_features()
    if not template:
        print("❌ Cannot get feature requirements.")
        return
    
    # Test validation
    if not test_feature_validation():
        print("❌ Feature validation failed.")
        return
    
    # Test single prediction
    single_result = test_single_prediction()
    if not single_result:
        print("❌ Single prediction failed.")
        return
    
    # Test batch prediction
    batch_results = test_batch_prediction()
    if not batch_results:
        print("❌ Batch prediction failed.")
        return
    
    # Test data generation
    if not test_data_generation():
        print("❌ Data generation tests failed.")
        return
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("🚀 API is ready for frontend integration!")
    print("=" * 60)
    
    # Summary
    print(f"\n📋 INTEGRATION SUMMARY:")
    print(f"• API Base URL: {API_BASE}")
    print(f"• Required Features: {len(template)} total")
    print(f"• Conservative Bias: +0.15 (configurable)")
    print(f"• Score Range: 0.0 (comfortable) to 1.0 (critical)")
    print(f"• Supports: Single & batch predictions")
    print(f"• Validation: Built-in feature validation")
    print(f"• Data Generation: Random, ramp up/down test data")

if __name__ == "__main__":
    main()