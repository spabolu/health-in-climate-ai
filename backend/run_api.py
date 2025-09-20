"""
Thermal Comfort API Startup Script
=================================

Simple script to start the Flask API server with proper error handling.
"""

import os
import sys
from flask_app import app, initialize_predictor

def check_model_files():
    """Check if required model files exist."""
    model_dir = "thermal_comfort_model"
    required_files = [
        "xgboost_model.joblib",
        "scaler.joblib", 
        "label_encoder.joblib",
        "feature_columns.joblib"
    ]
    
    if not os.path.exists(model_dir):
        return False, f"Model directory '{model_dir}' not found"
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(model_dir, file)):
            missing_files.append(file)
    
    if missing_files:
        return False, f"Missing model files: {', '.join(missing_files)}"
    
    return True, "All model files found"

def main():
    """Main startup function."""
    print("🌡️ THERMAL COMFORT PREDICTION API")
    print("=" * 50)
    
    # Check model files
    print("📁 Checking model files...")
    files_ok, message = check_model_files()
    
    if not files_ok:
        print(f"❌ {message}")
        print("\n💡 To fix this:")
        print("   1. Run 'python main.py' to train and save the model")
        print("   2. Make sure the 'thermal_comfort_model' directory exists")
        print("   3. Verify all model files are present")
        sys.exit(1)
    
    print(f"✅ {message}")
    
    # Initialize predictor
    print("🤖 Initializing thermal comfort predictor...")
    if not initialize_predictor():
        print("❌ Failed to initialize predictor")
        sys.exit(1)
    
    print("✅ Predictor initialized successfully")
    
    # Start server
    print("\n🚀 Starting Flask API server...")
    print("📡 API will be available at:")
    print("   • Local: http://localhost:5000")
    print("   • Network: http://0.0.0.0:5000")
    print("\n📋 Available endpoints:")
    print("   • GET  /health - Health check")
    print("   • POST /predict - Single prediction")
    print("   • POST /predict_batch - Batch predictions")
    print("   • GET  /generate_random - Generate random test data")
    print("   • GET  /generate_ramp_up - Generate green→red progression")
    print("   • GET  /generate_ramp_down - Generate red→green recovery")
    print("   • GET  /test_prediction_flow - Test complete workflow")
    print("\n🌐 Web interface available at: http://localhost:5000/static/index.html")
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(
            debug=False,  # Set to False for production
            host='0.0.0.0',
            port=5000,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()