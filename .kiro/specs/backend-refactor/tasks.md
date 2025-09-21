# Implementation Plan

- [x] 1. Create minimal FastAPI app with single prediction endpoint





  - Write one main.py file with FastAPI app and POST /predict endpoint
  - Load XGBoost model, scaler, and label encoder on startup
  - Accept JSON features in request body and return risk score
  - _Requirements: 2.1, 2.2, 3.1, 4.1_




- [ ] 2. Update requirements.txt for FastAPI




  - Replace Flask dependencies with fastapi and uvicorn
  - Keep existing ML dependencies (pandas, numpy, scikit-learn, xgboost, joblib)
  - _Requirements: 3.1_

- [ ] 3. Remove all redundant Flask files

  - Delete flask_app.py, simple_api.py, run_api.py, test_api.py, example_usage.py
  - Delete predict_thermal_comfort.py (logic moved to main.py)
  - Keep only main.py and thermal_comfort_model/ directory
  - _Requirements: 1.1, 1.2, 1.4_