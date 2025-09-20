"""
Example Usage of Thermal Comfort Prediction
==========================================

This script demonstrates how to use the thermal comfort predictor
with real wearable device data.
"""

from predict_thermal_comfort import ThermalComfortPredictor
import pandas as pd
import json


def example_real_time_monitoring():
    """Example of real-time thermal comfort monitoring."""
    print("🔄 REAL-TIME MONITORING EXAMPLE")
    print("=" * 40)
    
    # Initialize predictor
    predictor = ThermalComfortPredictor()
    
    # Simulate real-time data from wearable device
    wearable_data = {
        # Demographics
        'Gender': 1,  # Male
        'Age': 28,
        
        # Environmental sensors
        'Temperature': 29.5,  # Hot day
        'Humidity': 70,       # High humidity
        
        # Heart Rate Variability from wearable
        'hrv_mean_hr': 85,           # Elevated heart rate
        'hrv_mean_nni': 705,         # Lower HRV (stress indicator)
        'hrv_sdnn': 45,              # Reduced variability
        'hrv_rmssd': 35,             # Lower parasympathetic activity
        'hrv_total_power': 1200,     # Reduced total power
        'hrv_lf': 400,               # Low frequency power
        'hrv_hf': 300,               # High frequency power
        'hrv_lf_hf_ratio': 1.33,     # Elevated LF/HF ratio
        
        # Additional HRV metrics (using defaults for others)
        **{f'hrv_{metric}': 0.0 for metric in [
            'median_nni', 'range_nni', 'sdsd', 'nni_50', 'pnni_50',
            'nni_20', 'pnni_20', 'cvsd', 'cvnni', 'min_hr', 'max_hr',
            'std_hr', 'vlf', 'lfnu', 'hfnu', 'SD1', 'SD2', 'SD2SD1',
            'CSI', 'CVI', 'CSI_Modified', 'mean', 'std', 'min', 'max',
            'ptp', 'sum', 'energy', 'skewness', 'kurtosis', 'peaks',
            'rms', 'lineintegral', 'n_above_mean', 'n_below_mean',
            'n_sign_changes', 'iqr', 'iqr_5_95', 'pct_5', 'pct_95',
            'entropy', 'perm_entropy', 'svd_entropy'
        ]}
    }
    
    # Make prediction
    result = predictor.predict_single(wearable_data)
    
    # Display results
    print(f"📱 Wearable Device Reading:")
    print(f"   • Heart Rate: {wearable_data['hrv_mean_hr']} bpm")
    print(f"   • Temperature: {wearable_data['Temperature']}°C")
    print(f"   • Humidity: {wearable_data['Humidity']}%")
    print(f"   • HRV SDNN: {wearable_data['hrv_sdnn']} ms")
    
    print(f"\n🎯 Thermal Comfort Assessment:")
    print(f"   • Comfort Level: {result['comfort_level']}")
    print(f"   • Risk Level: {result['risk_assessment']}")
    print(f"   • Comfort Score: {result['comfort_score_final']}/1.0")
    print(f"   • Confidence: {result['confidence']}")
    
    print(f"\n⚠️  Alert System:")
    if result['comfort_score_final'] > 0.7:
        print("   🚨 HIGH THERMAL STRESS DETECTED!")
    elif result['comfort_score_final'] > 0.5:
        print("   ⚠️  Moderate thermal stress")
    else:
        print("   ✅ Thermal comfort within acceptable range")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(result['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    return result


def example_batch_processing():
    """Example of processing multiple samples."""
    print("\n📊 BATCH PROCESSING EXAMPLE")
    print("=" * 40)
    
    # Initialize predictor
    predictor = ThermalComfortPredictor()
    
    # Create sample data for multiple time points
    batch_data = []
    for i in range(5):
        sample = predictor.get_feature_template()
        sample.update({
            'Temperature': 25 + i * 2,  # Increasing temperature
            'Humidity': 50 + i * 5,     # Increasing humidity
            'hrv_mean_hr': 70 + i * 3,  # Increasing heart rate
            'Age': 25,
            'Gender': 1
        })
        batch_data.append(sample)
    
    # Convert to DataFrame
    batch_df = pd.DataFrame(batch_data)
    
    # Process batch
    results = predictor.predict_batch(batch_df)
    
    # Display results
    print("Time Series Analysis:")
    print("-" * 60)
    print(f"{'Time':<6} {'Temp':<6} {'HR':<4} {'Score':<6} {'Level':<20} {'Risk'}")
    print("-" * 60)
    
    for i, result in enumerate(results):
        temp = batch_data[i]['Temperature']
        hr = batch_data[i]['hrv_mean_hr']
        score = result['comfort_score_final']
        level = result['comfort_level']
        risk = result['risk_assessment']
        
        print(f"{i+1:<6} {temp:<6.1f} {hr:<4.0f} {score:<6.3f} {level:<20} {risk}")
    
    return results


def example_custom_bias():
    """Example of using custom conservative bias."""
    print("\n⚖️  CUSTOM BIAS EXAMPLE")
    print("=" * 40)
    
    # Initialize predictor
    predictor = ThermalComfortPredictor()
    
    # Sample data
    sample_data = predictor.get_feature_template()
    sample_data.update({
        'Temperature': 27,
        'Humidity': 60,
        'hrv_mean_hr': 78,
        'Age': 30,
        'Gender': 1
    })
    
    # Compare different bias levels
    bias_levels = [0.0, 0.1, 0.15, 0.2, 0.25]
    
    print("Conservative Bias Comparison:")
    print("-" * 50)
    print(f"{'Bias':<6} {'Score':<6} {'Level':<20} {'Risk'}")
    print("-" * 50)
    
    for bias in bias_levels:
        result = predictor.predict_single(
            sample_data, 
            use_conservative=True, 
            conservative_bias=bias
        )
        
        score = result['comfort_score_final']
        level = result['comfort_level']
        risk = result['risk_assessment']
        
        print(f"{bias:<6.2f} {score:<6.3f} {level:<20} {risk}")
    
    print(f"\n📝 Bias Selection Guide:")
    print(f"   • 0.00: No bias (standard scoring)")
    print(f"   • 0.10: Mild conservative approach")
    print(f"   • 0.15: Balanced protection (recommended)")
    print(f"   • 0.20: High conservative approach")
    print(f"   • 0.25: Maximum conservative approach")


def save_predictions_to_file(results, filename="thermal_predictions.json"):
    """Save prediction results to JSON file."""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Results saved to {filename}")


def main():
    """Run all examples."""
    print("🌡️ THERMAL COMFORT PREDICTION EXAMPLES")
    print("=" * 50)
    
    try:
        # Real-time monitoring example
        realtime_result = example_real_time_monitoring()
        
        # Batch processing example
        batch_results = example_batch_processing()
        
        # Custom bias example
        example_custom_bias()
        
        # Save results
        all_results = {
            'realtime_example': realtime_result,
            'batch_examples': batch_results
        }
        save_predictions_to_file(all_results)
        
        print(f"\n✅ All examples completed successfully!")
        print(f"🚀 Ready for integration with your wearable device system!")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure you've trained the model first by running main.py")


if __name__ == "__main__":
    main()