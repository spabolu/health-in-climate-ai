"""
Thermal Sensation Prediction using Wearable Device Data
======================================================

This script trains an XGBoost model to predict thermal sensation using
heart rate variability (HRV) and environmental data from wearable devices.

Author: Generated for thermal comfort analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from xgboost import XGBClassifier
import seaborn as sns
from matplotlib.patches import Patch
import joblib
import os
from datetime import datetime


def define_wearable_features():
    """Define the features that can be obtained from wearable devices."""
    return [
        # Demographics
        "Gender", "Age",
        
        # Heart Rate Variability (HRV) Features from Wearable Devices
        "hrv_mean_nni", "hrv_median_nni", "hrv_range_nni",
        "hrv_sdsd", "hrv_rmssd", "hrv_nni_50", "hrv_pnni_50",
        "hrv_nni_20", "hrv_pnni_20", "hrv_cvsd", "hrv_sdnn",
        "hrv_cvnni", "hrv_mean_hr", "hrv_min_hr", "hrv_max_hr",
        "hrv_std_hr", "hrv_total_power", "hrv_vlf", "hrv_lf",
        "hrv_hf", "hrv_lf_hf_ratio", "hrv_lfnu", "hrv_hfnu",
        "hrv_SD1", "hrv_SD2", "hrv_SD2SD1", "hrv_CSI",
        "hrv_CVI", "hrv_CSI_Modified", "hrv_mean", "hrv_std",
        "hrv_min", "hrv_max", "hrv_ptp", "hrv_sum", "hrv_energy",
        "hrv_skewness", "hrv_kurtosis", "hrv_peaks", "hrv_rms",
        "hrv_lineintegral", "hrv_n_above_mean", "hrv_n_below_mean",
        "hrv_n_sign_changes", "hrv_iqr", "hrv_iqr_5_95",
        "hrv_pct_5", "hrv_pct_95", "hrv_entropy",
        "hrv_perm_entropy", "hrv_svd_entropy",
        
        # Environmental Data (from IoT sensors)
        "Temperature", "Humidity"
    ]


def load_and_explore_data():
    """Load datasets and perform initial exploration."""
    print("=" * 60)
    print("LOADING AND EXPLORING DATA")
    print("=" * 60)
    
    # Load datasets
    print("Loading datasets...")
    train_data = pd.read_csv('Train2021.csv')
    test_data = pd.read_csv('Test Data.csv')
    
    print(f"✓ Train data shape: {train_data.shape}")
    print(f"✓ Test data shape: {test_data.shape}")
    
    # Check for missing values
    train_missing = train_data.isnull().sum().sum()
    test_missing = test_data.isnull().sum().sum()
    print(f"✓ Missing values - Train: {train_missing}, Test: {test_missing}")
    
    return train_data, test_data


def prepare_features(train_data, test_data, target_column='Thermal sensation'):
    """Prepare features and target variables for modeling."""
    print("\n" + "=" * 60)
    print("PREPARING FEATURES")
    print("=" * 60)
    
    # Define and filter features
    all_features = define_wearable_features()
    available_features = [col for col in all_features if col in train_data.columns]
    missing_features = [col for col in all_features if col not in train_data.columns]
    
    if missing_features:
        print(f"⚠️  Missing features: {missing_features}")
    
    print(f"✓ Using {len(available_features)} wearable device features")
    
    # Prepare data
    X_train = train_data[available_features].copy()
    y_train = train_data[target_column]
    X_test = test_data[available_features].copy()
    y_test = test_data[target_column] if target_column in test_data.columns else None
    
    # Handle categorical features
    if 'Gender' in available_features:
        X_train['Gender'] = X_train['Gender'].map({'M': 1, 'F': 0})
        X_test['Gender'] = X_test['Gender'].map({'M': 1, 'F': 0})
        print("✓ Encoded Gender (M=1, F=0)")
    
    # Handle missing values
    X_train = X_train.fillna(X_train.mean())
    X_test = X_test.fillna(X_test.mean())
    print("✓ Filled missing values with mean")
    
    return X_train, X_test, y_train, y_test, available_features


def encode_target_and_split(X_train, y_train, y_test=None):
    """Encode target variable and split data for validation."""
    print("\n" + "=" * 60)
    print("ENCODING TARGET AND SPLITTING DATA")
    print("=" * 60)
    
    # Encode target variable
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_test_encoded = le.transform(y_test) if y_test is not None else None
    
    print(f"✓ Target classes: {list(le.classes_)}")
    print(f"✓ Class distribution: {dict(zip(le.classes_, np.bincount(y_train_encoded)))}")
    
    # Split for validation
    X_train_split, X_val, y_train_split, y_val = train_test_split(
        X_train, y_train_encoded, test_size=0.2, random_state=42, stratify=y_train_encoded
    )
    
    print(f"✓ Train split: {X_train_split.shape[0]} samples")
    print(f"✓ Validation: {X_val.shape[0]} samples")
    
    return X_train_split, X_val, y_train_split, y_val, y_test_encoded, le


def scale_features(X_train_split, X_val, X_test):
    """Scale features using StandardScaler."""
    print("\n" + "=" * 60)
    print("SCALING FEATURES")
    print("=" * 60)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_split)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    print("✓ Features scaled using StandardScaler")
    print(f"✓ Feature range after scaling: [{X_train_scaled.min():.2f}, {X_train_scaled.max():.2f}]")
    
    return X_train_scaled, X_val_scaled, X_test_scaled, scaler


def train_xgboost_model(X_train_scaled, y_train_split):
    """Train XGBoost classifier."""
    print("\n" + "=" * 60)
    print("TRAINING XGBOOST MODEL")
    print("=" * 60)
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss'
    )
    
    print("Training model...")
    model.fit(X_train_scaled, y_train_split)
    print("✓ Model training completed")
    
    return model


def create_thermal_comfort_score(predictions, probabilities, le, conservative_bias=0.15):
    """
    Convert categorical thermal sensation predictions to a continuous comfort score (0-1).
    
    Args:
        conservative_bias: Safety margin added to scores (default 0.15)
                          Higher values = more conservative (overestimate discomfort)
    
    Score interpretation (after conservative bias):
    - 0.0-0.25: Comfortable (neutral)
    - 0.25-0.5: Slightly uncomfortable (slightly warm)  
    - 0.5-0.75: Uncomfortable (warm)
    - 0.75-1.0: Very uncomfortable (hot)
    
    Conservative bias helps prevent underestimating thermal discomfort for safety/liability.
    """
    # Define thermal comfort mapping based on typical thermal sensation scale
    comfort_mapping = {
        'neutral': 0.0,
        'slightly warm': 0.33,
        'warm': 0.67,
        'hot': 1.0
    }
    
    # Get class names and create mapping
    class_names = le.classes_
    class_to_score = {}
    
    for class_name in class_names:
        # Map class names to comfort scores (handle variations in naming)
        if 'neutral' in class_name.lower():
            class_to_score[class_name] = 0.0
        elif 'slightly' in class_name.lower() or 'warm' in class_name.lower():
            class_to_score[class_name] = 0.33
        elif 'hot' in class_name.lower() and 'super' not in class_name.lower():
            class_to_score[class_name] = 0.67
        elif 'super' in class_name.lower() or 'very' in class_name.lower():
            class_to_score[class_name] = 1.0
        else:
            # Default mapping based on order
            class_idx = list(class_names).index(class_name)
            class_to_score[class_name] = class_idx / (len(class_names) - 1)
    
    # Method 1: Simple categorical mapping
    categorical_scores = np.array([class_to_score[class_names[pred]] for pred in predictions])
    
    # Method 2: Probability-weighted score (more nuanced)
    # Formula: Comfort_Score = Σ(P(class_i) × Score(class_i)) + Conservative_Bias
    weighted_scores = np.zeros(len(predictions))
    for i, prob_dist in enumerate(probabilities):
        weighted_score = 0
        for j, prob in enumerate(prob_dist):
            class_name = class_names[j]
            # This is the core equation: probability × assigned score
            weighted_score += prob * class_to_score[class_name]
        weighted_scores[i] = weighted_score
    
    # Apply conservative bias - shift scores upward for safety
    # This helps prevent underestimating thermal discomfort
    categorical_scores_conservative = np.clip(categorical_scores + conservative_bias, 0, 1)
    weighted_scores_conservative = np.clip(weighted_scores + conservative_bias, 0, 1)
    
    return (categorical_scores, weighted_scores, 
            categorical_scores_conservative, weighted_scores_conservative, 
            class_to_score, conservative_bias)


def evaluate_model(model, X_val_scaled, y_val, X_test_scaled, y_test_encoded, le):
    """Evaluate model performance on validation and test sets."""
    print("\n" + "=" * 60)
    print("MODEL EVALUATION")
    print("=" * 60)
    
    # Validation performance
    y_val_pred = model.predict(X_val_scaled)
    y_val_proba = model.predict_proba(X_val_scaled)
    val_accuracy = accuracy_score(y_val, y_val_pred)
    
    print(f"✓ Validation Accuracy: {val_accuracy:.4f} ({val_accuracy:.1%})")
    print("\nValidation Classification Report:")
    print(classification_report(y_val, y_val_pred, target_names=le.classes_))
    
    # Create thermal comfort scores for validation
    (val_categorical_scores, val_weighted_scores, 
     val_categorical_conservative, val_weighted_conservative, 
     class_mapping, conservative_bias) = create_thermal_comfort_score(y_val_pred, y_val_proba, le)
    
    print(f"\n📊 THERMAL COMFORT SCORING WITH CONSERVATIVE BIAS")
    print(f"Class to Score Mapping: {class_mapping}")
    print(f"Conservative Bias: +{conservative_bias:.3f} (for safety/liability protection)")
    print(f"\n🧮 CONSERVATIVE SCORING EQUATION:")
    print(f"   Base_Score = Σ(P(class_i) × Score(class_i))")
    print(f"   Final_Score = min(1.0, Base_Score + {conservative_bias})")
    print(f"   This overestimates discomfort to prevent underestimation risks")
    
    print(f"\nValidation Scores Comparison:")
    print(f"• Standard (weighted): {val_weighted_scores[:3]} (avg: {val_weighted_scores.mean():.3f})")
    print(f"• Conservative (weighted): {val_weighted_conservative[:3]} (avg: {val_weighted_conservative.mean():.3f})")
    print(f"• Safety margin effect: +{val_weighted_conservative.mean() - val_weighted_scores.mean():.3f} average increase")
    
    # Test performance (if available)
    if y_test_encoded is not None:
        y_test_pred = model.predict(X_test_scaled)
        y_test_proba = model.predict_proba(X_test_scaled)
        test_accuracy = accuracy_score(y_test_encoded, y_test_pred)
        
        print(f"✓ Test Accuracy: {test_accuracy:.4f} ({test_accuracy:.1%})")
        print("\nTest Classification Report:")
        print(classification_report(y_test_encoded, y_test_pred, target_names=le.classes_))
        
        # Create thermal comfort scores for test set
        (test_categorical_scores, test_weighted_scores,
         test_categorical_conservative, test_weighted_conservative,
         _, _) = create_thermal_comfort_score(y_test_pred, y_test_proba, le)
        
        print(f"\nTest Scores Comparison:")
        print(f"• Standard (weighted): avg = {test_weighted_scores.mean():.3f}")
        print(f"• Conservative (weighted): avg = {test_weighted_conservative.mean():.3f}")
        print(f"• Safety uplift: +{test_weighted_conservative.mean() - test_weighted_scores.mean():.3f}")
        
        # Plot confusion matrix and comfort score distribution
        plot_confusion_matrix(y_test_encoded, y_test_pred, le.classes_)
        plot_comfort_score_distribution(test_weighted_scores, test_weighted_conservative, 
                                      test_categorical_scores, conservative_bias)
        
        return val_accuracy, test_accuracy, val_weighted_conservative, test_weighted_conservative
    
    return val_accuracy, None, val_weighted_conservative, None


def plot_confusion_matrix(y_true, y_pred, class_names):
    """Plot confusion matrix."""
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title('Confusion Matrix - Test Set')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.show()


def plot_comfort_score_distribution(standard_scores, conservative_scores, categorical_scores, bias):
    """Plot distribution of thermal comfort scores with conservative bias comparison."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot standard vs conservative scores distribution
    ax1.hist(standard_scores, bins=20, alpha=0.6, color='skyblue', 
             label=f'Standard (avg: {standard_scores.mean():.3f})', edgecolor='black')
    ax1.hist(conservative_scores, bins=20, alpha=0.6, color='orange', 
             label=f'Conservative +{bias} (avg: {conservative_scores.mean():.3f})', edgecolor='black')
    ax1.axvline(standard_scores.mean(), color='blue', linestyle='--', alpha=0.8)
    ax1.axvline(conservative_scores.mean(), color='red', linestyle='--', alpha=0.8)
    ax1.set_xlabel('Thermal Comfort Score (0=Comfortable, 1=Very Uncomfortable)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Standard vs Conservative Comfort Scores')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add comfort zones
    ax1.axvspan(0.0, 0.25, alpha=0.2, color='green', label='Comfortable')
    ax1.axvspan(0.25, 0.5, alpha=0.2, color='yellow', label='Slightly Uncomfortable')
    ax1.axvspan(0.5, 0.75, alpha=0.2, color='orange', label='Uncomfortable')
    ax1.axvspan(0.75, 1.0, alpha=0.2, color='red', label='Very Uncomfortable')
    
    # Plot standard vs conservative scores scatter
    ax2.scatter(standard_scores, conservative_scores, alpha=0.6, color='purple')
    ax2.plot([0, 1], [0, 1], 'r--', label='No Change Line')
    ax2.plot([0, 1-bias], [bias, 1], 'g--', label=f'Conservative Shift (+{bias})')
    ax2.set_xlabel('Standard Comfort Score')
    ax2.set_ylabel('Conservative Comfort Score')
    ax2.set_title('Impact of Conservative Bias')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def create_comfort_score_predictor(model, scaler, le, conservative_bias=0.15):
    """Create a function that predicts comfort scores from raw features."""
    def predict_comfort_score(features_dict, use_conservative=True):
        """
        Predict thermal comfort score from wearable device features.
        
        Args:
            features_dict: Dictionary with feature names as keys and values
            use_conservative: Whether to apply conservative bias (default True for safety)
            
        Returns:
            dict: Contains categorical prediction, comfort scores, and confidence
        """
        # Convert to DataFrame
        features_df = pd.DataFrame([features_dict])
        
        # Scale features
        features_scaled = scaler.transform(features_df)
        
        # Get prediction and probabilities
        prediction = model.predict(features_scaled)[0]
        probabilities = model.predict_proba(features_scaled)[0]
        
        # Convert to comfort score
        (categorical_score, weighted_score, 
         categorical_conservative, weighted_conservative, 
         _, bias) = create_thermal_comfort_score([prediction], [probabilities], le, conservative_bias)
        
        # Get confidence (max probability)
        confidence = probabilities.max()
        
        # Choose which score to return based on use_conservative flag
        final_score = weighted_conservative[0] if use_conservative else weighted_score[0]
        
        return {
            'predicted_class': le.classes_[prediction],
            'comfort_score_standard': weighted_score[0],
            'comfort_score_conservative': weighted_conservative[0],
            'comfort_score_final': final_score,
            'conservative_bias': bias,
            'confidence': confidence,
            'class_probabilities': dict(zip(le.classes_, probabilities)),
            'safety_note': f"Conservative bias of +{bias} applied for liability protection" if use_conservative else "Standard scoring used"
        }
    
    return predict_comfort_score


def save_model_and_components(model, scaler, le, feature_columns, model_dir="thermal_comfort_model"):
    """Save the trained model and all necessary components for prediction."""
    
    # Create model directory
    os.makedirs(model_dir, exist_ok=True)
    
    # Save model components
    model_path = os.path.join(model_dir, "xgboost_model.joblib")
    scaler_path = os.path.join(model_dir, "scaler.joblib")
    encoder_path = os.path.join(model_dir, "label_encoder.joblib")
    features_path = os.path.join(model_dir, "feature_columns.joblib")
    metadata_path = os.path.join(model_dir, "model_metadata.txt")
    
    # Save components
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(le, encoder_path)
    joblib.dump(feature_columns, features_path)
    
    # Save metadata
    with open(metadata_path, 'w') as f:
        f.write(f"Thermal Comfort Model Metadata\n")
        f.write(f"==============================\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model Type: XGBoost Classifier\n")
        f.write(f"Number of Features: {len(feature_columns)}\n")
        f.write(f"Target Classes: {list(le.classes_)}\n")
        f.write(f"Conservative Bias: 0.15 (default)\n")
        f.write(f"\nFeature List:\n")
        for i, feature in enumerate(feature_columns, 1):
            f.write(f"{i:2d}. {feature}\n")
    
    print(f"\n💾 MODEL SAVED SUCCESSFULLY")
    print(f"✓ Model directory: {model_dir}/")
    print(f"✓ XGBoost model: {model_path}")
    print(f"✓ Feature scaler: {scaler_path}")
    print(f"✓ Label encoder: {encoder_path}")
    print(f"✓ Feature list: {features_path}")
    print(f"✓ Metadata: {metadata_path}")
    
    return model_dir


def analyze_feature_importance(model, feature_columns):
    """Analyze and visualize feature importance."""
    print("\n" + "=" * 60)
    print("FEATURE IMPORTANCE ANALYSIS")
    print("=" * 60)
    
    # Calculate feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("Top 10 Most Important Features:")
    for i, (_, row) in enumerate(feature_importance.head(10).iterrows(), 1):
        print(f"{i:2d}. {row['feature']:<20} {row['importance']:.4f}")
    
    # Categorize features
    hrv_features = [f for f in feature_columns if f.startswith('hrv_')]
    env_features = [f for f in feature_columns if f in ['Temperature', 'Humidity']]
    demo_features = [f for f in feature_columns if f in ['Gender', 'Age']]
    
    # Calculate importance by category
    hrv_importance = feature_importance[feature_importance['feature'].isin(hrv_features)]['importance'].sum()
    env_importance = feature_importance[feature_importance['feature'].isin(env_features)]['importance'].sum()
    demo_importance = feature_importance[feature_importance['feature'].isin(demo_features)]['importance'].sum()
    
    print(f"\nFeature Category Breakdown:")
    print(f"• HRV features: {len(hrv_features)} ({hrv_importance:.1%} importance)")
    print(f"• Environmental: {len(env_features)} ({env_importance:.1%} importance)")
    print(f"• Demographics: {len(demo_features)} ({demo_importance:.1%} importance)")
    
    # Plot feature importance
    plot_feature_importance(feature_importance, hrv_features, env_features, demo_features)
    
    return feature_importance


def plot_feature_importance(feature_importance, hrv_features, env_features, demo_features):
    """Plot feature importance with color coding."""
    plt.figure(figsize=(12, 8))
    
    top_features = feature_importance.head(20)
    colors = []
    for feature in top_features['feature']:
        if feature in hrv_features:
            colors.append('red')
        elif feature in env_features:
            colors.append('blue')
        else:
            colors.append('green')
    
    plt.barh(range(len(top_features)), top_features['importance'], color=colors, alpha=0.7)
    plt.yticks(range(len(top_features)), top_features['feature'])
    plt.xlabel('Feature Importance')
    plt.title('Top 20 Wearable Device Feature Importances')
    plt.gca().invert_yaxis()
    
    # Add legend
    legend_elements = [
        Patch(facecolor='red', alpha=0.7, label='HRV Features'),
        Patch(facecolor='blue', alpha=0.7, label='Environmental Features'),
        Patch(facecolor='green', alpha=0.7, label='Demographic Features')
    ]
    plt.legend(handles=legend_elements, loc='lower right')
    plt.tight_layout()
    plt.show()


def main():
    """Main execution function."""
    print("🔥 THERMAL SENSATION PREDICTION WITH WEARABLE DEVICES 🔥")
    
    # Load and explore data
    train_data, test_data = load_and_explore_data()
    
    # Prepare features
    X_train, X_test, y_train, y_test, feature_columns = prepare_features(train_data, test_data)
    
    # Encode target and split data
    X_train_split, X_val, y_train_split, y_val, y_test_encoded, le = encode_target_and_split(
        X_train, y_train, y_test
    )
    
    # Scale features
    X_train_scaled, X_val_scaled, X_test_scaled, scaler = scale_features(
        X_train_split, X_val, X_test
    )
    
    # Train model
    model = train_xgboost_model(X_train_scaled, y_train_split)
    
    # Evaluate model
    val_accuracy, test_accuracy, val_scores, test_scores = evaluate_model(
        model, X_val_scaled, y_val, X_test_scaled, y_test_encoded, le
    )
    
    # Analyze feature importance
    feature_importance = analyze_feature_importance(model, feature_columns)
    
    # Create comfort score predictor
    comfort_predictor = create_comfort_score_predictor(model, scaler, le)
    
    # Example prediction with detailed calculation
    print("\n" + "=" * 60)
    print("EXAMPLE COMFORT SCORE CALCULATION")
    print("=" * 60)
    
    # Use first test sample as example
    if len(X_test) > 0:
        example_features = X_test.iloc[0].to_dict()
        example_prediction = comfort_predictor(example_features)
        
        print("Example prediction for first test sample:")
        print(f"• Predicted class: {example_prediction['predicted_class']}")
        print(f"• Standard score: {example_prediction['comfort_score_standard']:.4f}")
        print(f"• Conservative score: {example_prediction['comfort_score_conservative']:.4f}")
        print(f"• Final score (conservative): {example_prediction['comfort_score_final']:.4f}")
        print(f"• Confidence: {example_prediction['confidence']:.3f}")
        print(f"• {example_prediction['safety_note']}")
        
        print(f"\n🧮 DETAILED CONSERVATIVE CALCULATION:")
        print(f"   Step 1: Base_Score = Σ(P(class_i) × Score(class_i))")
        
        total_score = 0
        bias = example_prediction['conservative_bias']
        
        for class_name, prob in example_prediction['class_probabilities'].items():
            # Get the score for this class
            score = 0.0
            if 'neutral' in class_name.lower():
                score = 0.0
            elif 'slightly' in class_name.lower():
                score = 0.33
            elif 'warm' in class_name.lower() and 'slightly' not in class_name.lower():
                score = 0.67
            elif 'hot' in class_name.lower():
                score = 1.0
            
            contribution = prob * score
            total_score += contribution
            print(f"   {class_name:15} = {prob:.3f} × {score:.2f} = {contribution:.4f}")
        
        print(f"   {'='*45}")
        print(f"   Base Score = {total_score:.4f}")
        print(f"   Step 2: Conservative_Score = min(1.0, Base_Score + {bias})")
        print(f"   Conservative Score = min(1.0, {total_score:.4f} + {bias}) = {min(1.0, total_score + bias):.4f}")
        
        # Interpret the conservative score
        final_score = min(1.0, total_score + bias)
        if final_score < 0.25:
            interpretation = "Comfortable"
        elif final_score < 0.5:
            interpretation = "Slightly Uncomfortable"
        elif final_score < 0.75:
            interpretation = "Uncomfortable"
        else:
            interpretation = "Very Uncomfortable"
        
        print(f"   Final Interpretation: {interpretation}")
        print(f"\n⚖️  LEGAL/SAFETY BENEFIT:")
        print(f"   • Reduces risk of underestimating thermal discomfort")
        print(f"   • Provides safety margin for liability protection")
        print(f"   • Better to overestimate than underestimate health risks")
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"✅ Model trained successfully using {len(feature_columns)} wearable device features")
    print(f"✅ Validation accuracy: {val_accuracy:.1%}")
    if test_accuracy:
        print(f"✅ Test accuracy: {test_accuracy:.1%}")
    print(f"✅ Most important feature: {feature_importance.iloc[0]['feature']}")
    
    if test_scores is not None:
        print(f"✅ Average comfort score: {test_scores.mean():.3f}")
        comfort_level = "Comfortable" if test_scores.mean() < 0.25 else \
                       "Slightly Uncomfortable" if test_scores.mean() < 0.5 else \
                       "Uncomfortable" if test_scores.mean() < 0.75 else "Very Uncomfortable"
        print(f"✅ Overall comfort level: {comfort_level}")
    
    print("\n🎯 COMFORT SCORE INTERPRETATION:")
    print("   0.0-0.25: Comfortable (neutral)")
    print("   0.25-0.5: Slightly Uncomfortable (slightly warm)")
    print("   0.5-0.75: Uncomfortable (warm)")
    print("   0.75-1.0: Very Uncomfortable (hot)")
    
    # Save the trained model and components
    model_dir = save_model_and_components(model, scaler, le, feature_columns)
    
    print("\n🎉 Analysis completed!")
    print(f"🚀 Ready for deployment! Use the prediction script with saved model.")


if __name__ == "__main__":
    main()