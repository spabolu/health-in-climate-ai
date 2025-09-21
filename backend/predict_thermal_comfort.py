"""
Thermal Comfort Prediction Script
=================================

This script loads a pre-trained thermal comfort model and provides
real-time predictions from wearable device data.

Usage:
    python predict_thermal_comfort.py
"""

import pandas as pd
import numpy as np
import joblib
import os
import json
from datetime import datetime


class ThermalComfortPredictor:
    """A class for predicting thermal comfort from wearable device data."""
    
    def __init__(self, model_dir="thermal_comfort_model"):
        """
        Initialize the predictor by loading the trained model components.
        
        Args:
            model_dir: Directory containing the saved model files
        """
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_columns = None
        self.conservative_bias = 0.15
        
        self.load_model()
    
    def load_model(self):
        """Load all model components from saved files."""
        try:
            # Load model components
            self.model = joblib.load(os.path.join(self.model_dir, "xgboost_model.joblib"))
            self.scaler = joblib.load(os.path.join(self.model_dir, "scaler.joblib"))
            self.label_encoder = joblib.load(os.path.join(self.model_dir, "label_encoder.joblib"))
            self.feature_columns = joblib.load(os.path.join(self.model_dir, "feature_columns.joblib"))
            
            print("✅ Model loaded successfully!")
            print(f"📁 Model directory: {self.model_dir}")
            print(f"🎯 Target classes: {list(self.label_encoder.classes_)}")
            print(f"📊 Features: {len(self.feature_columns)} wearable device metrics")
            
        except FileNotFoundError as e:
            print(f"❌ Error loading model: {e}")
            print(f"Make sure the model directory '{self.model_dir}' exists and contains all required files.")
            raise
    
    def create_thermal_comfort_score(self, predictions, probabilities, conservative_bias=None):
        """Convert predictions to comfort scores with conservative bias."""
        if conservative_bias is None:
            conservative_bias = self.conservative_bias
            
        # Define comfort score mapping
        class_names = self.label_encoder.classes_
        class_to_score = {}
        
        for class_name in class_names:
            if 'neutral' in class_name.lower():
                class_to_score[class_name] = 0.0
            elif 'slightly' in class_name.lower():
                class_to_score[class_name] = 0.33
            elif 'warm' in class_name.lower() and 'slightly' not in class_name.lower():
                class_to_score[class_name] = 0.67
            elif 'hot' in class_name.lower():
                class_to_score[class_name] = 1.0
            else:
                # Default mapping based on order
                class_idx = list(class_names).index(class_name)
                class_to_score[class_name] = class_idx / (len(class_names) - 1)
        
        # Calculate weighted scores
        weighted_scores = []
        for prob_dist in probabilities:
            weighted_score = sum(prob * class_to_score[class_names[j]] 
                               for j, prob in enumerate(prob_dist))
            weighted_scores.append(weighted_score)
        
        # Apply conservative bias
        conservative_scores = [min(1.0, score + conservative_bias) for score in weighted_scores]
        
        return weighted_scores, conservative_scores, class_to_score
    
    def predict_single(self, features_dict, use_conservative=True, conservative_bias=None):
        """
        Predict thermal comfort for a single sample.
        
        Args:
            features_dict: Dictionary with feature names as keys and values
            use_conservative: Whether to apply conservative bias (default True)
            conservative_bias: Custom bias value (uses default if None)
            
        Returns:
            dict: Comprehensive prediction results
        """
        if conservative_bias is None:
            conservative_bias = self.conservative_bias
            
        # Validate input features
        missing_features = [f for f in self.feature_columns if f not in features_dict]
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")
        
        # Prepare features
        features_df = pd.DataFrame([features_dict])
        features_df = features_df[self.feature_columns]  # Ensure correct order
        
        # Handle missing values safely
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            features_df[numeric_cols] = features_df[numeric_cols].fillna(features_df[numeric_cols].mean())
        features_df = features_df.fillna(0)
        
        # Scale features
        features_scaled = self.scaler.transform(features_df)
        
        # Make predictions
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        # Calculate comfort scores
        standard_scores, conservative_scores, class_mapping = self.create_thermal_comfort_score(
            [prediction], [probabilities], conservative_bias
        )
        
        # Prepare results
        predicted_class = self.label_encoder.classes_[prediction]
        confidence = probabilities.max()
        
        # Interpret comfort level
        final_score = conservative_scores[0] if use_conservative else standard_scores[0]
        comfort_level = self._interpret_comfort_score(final_score)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'predicted_class': str(predicted_class),
            'comfort_score_standard': round(float(standard_scores[0]), 4),
            'comfort_score_conservative': round(float(conservative_scores[0]), 4),
            'comfort_score_final': round(float(final_score), 4),
            'comfort_level': comfort_level,
            'confidence': round(float(confidence), 3),
            'conservative_bias': float(conservative_bias),
            'class_probabilities': {
                class_name: round(float(prob), 3)
                for class_name, prob in zip(self.label_encoder.classes_, probabilities)
            },
            'risk_assessment': self._assess_risk(final_score),
            'recommendations': self._get_recommendations(final_score)
        }
    
    def predict_batch(self, features_df, use_conservative=True, conservative_bias=None):
        """
        Predict thermal comfort for multiple samples.
        
        Args:
            features_df: DataFrame with features for multiple samples
            use_conservative: Whether to apply conservative bias
            conservative_bias: Custom bias value
            
        Returns:
            list: List of prediction dictionaries
        """
        results = []
        for idx, row in features_df.iterrows():
            try:
                result = self.predict_single(row.to_dict(), use_conservative, conservative_bias)
                result['sample_id'] = idx
                results.append(result)
            except Exception as e:
                print(f"Error predicting sample {idx}: {e}")
                continue
        
        return results
    
    def _interpret_comfort_score(self, score):
        """Interpret comfort score into human-readable level."""
        if score < 0.25:
            return "Comfortable"
        elif score < 0.5:
            return "Slightly Uncomfortable"
        elif score < 0.75:
            return "Uncomfortable"
        else:
            return "Very Uncomfortable"
    
    def _assess_risk(self, score):
        """Assess thermal stress risk level."""
        if score < 0.3:
            return "Low Risk"
        elif score < 0.6:
            return "Moderate Risk"
        elif score < 0.8:
            return "High Risk"
        else:
            return "Critical Risk"
    
    def _get_recommendations(self, score):
        """Get recommendations based on comfort score."""
        if score < 0.25:
            return ["Continue current activity", "Monitor periodically"]
        elif score < 0.5:
            return ["Consider cooling measures", "Stay hydrated", "Monitor closely"]
        elif score < 0.75:
            return ["Take cooling break", "Increase hydration", "Reduce activity intensity"]
        else:
            return ["Immediate cooling required", "Stop strenuous activity", "Seek cooler environment", "Medical attention if symptoms persist"]
    
    def get_feature_template(self):
        """Get a template dictionary with all required features."""
        template = {}
        for feature in self.feature_columns:
            if feature == 'Gender':
                template[feature] = 1  # 1 for Male, 0 for Female
            elif feature == 'Age':
                template[feature] = 25  # Example age
            elif feature == 'Temperature':
                template[feature] = 25.0  # Example temperature in Celsius
            elif feature == 'Humidity':
                template[feature] = 50.0  # Example humidity percentage
            else:
                template[feature] = 0.0  # Default for HRV features
        
        return template
    
    def print_feature_info(self):
        """Print information about required features."""
        print("\n📋 REQUIRED FEATURES:")
        print("=" * 50)
        
        hrv_features = [f for f in self.feature_columns if f.startswith('hrv_')]
        demo_features = [f for f in self.feature_columns if f in ['Gender', 'Age']]
        env_features = [f for f in self.feature_columns if f in ['Temperature', 'Humidity']]
        
        print(f"👤 Demographics ({len(demo_features)}):")
        for feature in demo_features:
            print(f"   • {feature}")
        
        print(f"\n🌡️  Environmental ({len(env_features)}):")
        for feature in env_features:
            print(f"   • {feature}")
        
        print(f"\n❤️  Heart Rate Variability ({len(hrv_features)}):")
        for i, feature in enumerate(hrv_features[:10]):  # Show first 10
            print(f"   • {feature}")
        if len(hrv_features) > 10:
            print(f"   ... and {len(hrv_features) - 10} more HRV features")


def main():
    """Main function demonstrating usage."""
    print("🌡️ THERMAL COMFORT PREDICTION SYSTEM")
    print("=" * 50)
    
    try:
        # Initialize predictor
        predictor = ThermalComfortPredictor()
        
        # Show feature information
        predictor.print_feature_info()
        
        # Get feature template
        template = predictor.get_feature_template()
        
        print(f"\n🧪 EXAMPLE PREDICTION:")
        print("=" * 30)
        
        # Example prediction with template values
        example_features = template.copy()
        example_features.update({
            'Age': 30,
            'Gender': 1,  # Male
            'Temperature': 28.5,  # Slightly warm temperature
            'Humidity': 65,  # Higher humidity
            'hrv_mean_hr': 75,  # Example heart rate
            'hrv_mean_nni': 800,  # Example HRV metric
        })
        
        # Make prediction
        result = predictor.predict_single(example_features)
        
        # Display results
        print(f"🎯 Prediction Results:")
        print(f"   • Predicted Class: {result['predicted_class']}")
        print(f"   • Comfort Level: {result['comfort_level']}")
        print(f"   • Risk Assessment: {result['risk_assessment']}")
        print(f"   • Standard Score: {result['comfort_score_standard']}")
        print(f"   • Conservative Score: {result['comfort_score_conservative']}")
        print(f"   • Confidence: {result['confidence']}")
        
        print(f"\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"   • {rec}")
        
        print(f"\n📊 Class Probabilities:")
        for class_name, prob in result['class_probabilities'].items():
            print(f"   • {class_name}: {prob}")
        
        print(f"\n✅ Prediction completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you've trained and saved a model first by running main.py")


if __name__ == "__main__":
    main()