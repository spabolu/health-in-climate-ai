/**
 * Interactive Heat Stress Simulation & Manual Worker Data Input
 * Business demo simulation + manual input for XGBoost model predictions
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useThermalComfortPrediction } from '@/hooks/use-thermal-comfort';
import DashboardLayout, {
  DashboardPageContainer,
  DashboardGrid,
  DashboardWidget,
} from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Progress } from '@/components/ui/progress';
import {
  Activity,
  AlertTriangle,
  Shield,
  CheckCircle,
  Loader2,
  PlayCircle,
  TrendingUp,
  TrendingDown,
  Zap,
  Eye,
  Thermometer,
  Heart,
} from 'lucide-react';
import { BiometricData, ThermalComfortPrediction } from '@/types/thermal-comfort';

interface PredictionResult extends ThermalComfortPrediction {
  risk_score?: number;
  risk_level?: string;
  risk_color?: string;
  osha_recommendations?: string[];
  requires_immediate_attention?: boolean;
  processing_time_ms?: number;
}

// Heat stress simulation parameters
interface SimulationState {
  intensity: number; // 0-1 scale (0=healthy, 1=critical)
  features: Record<string, number>;
  prediction?: PredictionResult;
  isSimulating: boolean;
}

// Feature categories for organized display
interface FeatureCategory {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  features: Array<{
    key: string;
    name: string;
    unit: string;
    healthy: number;
    warning: number;
    critical: number;
    format?: (value: number) => string;
  }>;
}

// Define comprehensive feature categories with realistic ranges (moved outside component)
const featureCategories: FeatureCategory[] = [
    {
      name: 'Environmental',
      icon: Thermometer,
      features: [
        { key: 'Temperature', name: 'Air Temperature', unit: '°C', healthy: 22, warning: 32, critical: 40 },
        { key: 'Humidity', name: 'Relative Humidity', unit: '%', healthy: 50, warning: 75, critical: 95 },
        { key: 'AirVelocity', name: 'Air Movement', unit: 'm/s', healthy: 0.5, warning: 0.2, critical: 0.1 },
      ],
    },
    {
      name: 'Cardiovascular',
      icon: Heart,
      features: [
        { key: 'hrv_mean_hr', name: 'Heart Rate', unit: 'BPM', healthy: 72, warning: 95, critical: 125 },
        { key: 'hrv_mean_nni', name: 'Mean NN Intervals', unit: 'ms', healthy: 850, warning: 650, critical: 480 },
        { key: 'hrv_rmssd', name: 'HRV Variability', unit: 'ms', healthy: 45, warning: 28, critical: 15 },
        { key: 'hrv_sdnn', name: 'Heart Rate Variation', unit: 'ms', healthy: 55, warning: 35, critical: 20 },
        { key: 'hrv_total_power', name: 'HRV Total Power', unit: 'ms²', healthy: 3200, warning: 1800, critical: 800 },
        { key: 'hrv_lf_hf_ratio', name: 'Stress Indicator', unit: 'ratio', healthy: 1.2, warning: 2.5, critical: 4.8 },
      ],
    },
    {
      name: 'Physiological',
      icon: Activity,
      features: [
        { key: 'CoreBodyTemperature', name: 'Core Body Temp', unit: '°C', healthy: 37.0, warning: 38.5, critical: 40.2 },
        { key: 'SkinTemperature', name: 'Skin Temperature', unit: '°C', healthy: 33.5, warning: 36.8, critical: 39.5 },
        { key: 'SkinConductance', name: 'Skin Conductance', unit: 'μS', healthy: 8.5, warning: 18.2, critical: 32.8 },
        { key: 'RespiratoryRate', name: 'Breathing Rate', unit: '/min', healthy: 16, warning: 24, critical: 35 },
        { key: 'MetabolicRate', name: 'Metabolic Rate', unit: 'MET', healthy: 1.8, warning: 3.2, critical: 4.8 },
        { key: 'HydrationLevel', name: 'Hydration Level', unit: '%', healthy: 0.85, warning: 0.65, critical: 0.35, format: (v) => `${(v*100).toFixed(0)}%` },
      ],
    },
  ];

// Advanced HRV features for comprehensive simulation (moved outside component)
const advancedHRVFeatures = [
    { key: 'hrv_median_nni', healthy: 840, warning: 640, critical: 470 },
    { key: 'hrv_range_nni', healthy: 350, warning: 220, critical: 120 },
    { key: 'hrv_sdsd', healthy: 42, warning: 26, critical: 14 },
    { key: 'hrv_nni_50', healthy: 25, warning: 12, critical: 4 },
    { key: 'hrv_pnni_50', healthy: 18, warning: 8, critical: 2 },
    { key: 'hrv_cvsd', healthy: 0.048, warning: 0.035, critical: 0.022 },
    { key: 'hrv_cvnni', healthy: 0.055, warning: 0.042, critical: 0.028 },
    { key: 'hrv_vlf', healthy: 850, warning: 420, critical: 150 },
    { key: 'hrv_lf', healthy: 1200, warning: 680, critical: 280 },
    { key: 'hrv_hf', healthy: 980, warning: 520, critical: 180 },
    { key: 'hrv_SD1', healthy: 32, warning: 20, critical: 11 },
    { key: 'hrv_SD2', healthy: 72, warning: 45, critical: 25 },
  ];

// Interpolation function for simulating feature changes (moved outside component)
const interpolateFeature = (intensity: number, healthy: number, warning: number, critical: number): number => {
    // Add realistic noise for biological variability
    const noise = (Math.random() - 0.5) * 0.1;

    if (intensity <= 0.5) {
      // Healthy to Warning (0-0.5 maps to healthy->warning)
      const t = intensity * 2;
      return healthy + (warning - healthy) * t + healthy * noise;
    } else {
      // Warning to Critical (0.5-1.0 maps to warning->critical)
      const t = (intensity - 0.5) * 2;
      return warning + (critical - warning) * t + warning * noise;
    }
  };

export default function ManualInputPage() {
  const { predict, prediction, isLoading, error, clearError } = useThermalComfortPrediction();

  // Simulation state for business demo
  const [simulation, setSimulation] = useState<SimulationState>({
    intensity: 0,
    features: {},
    isSimulating: false,
  });


  // Use ref to prevent re-creation of updateSimulation
  const predictRef = useRef(predict);
  predictRef.current = predict;

  // Generate complete feature set based on heat stress intensity
  const generateSimulatedFeatures = useCallback((intensity: number) => {
    const features: Record<string, number> = {
      // Demographics (static)
      Gender: 1,
      Age: 32,
    };

    // Generate features for each category
    featureCategories.forEach(category => {
      category.features.forEach(feature => {
        features[feature.key] = interpolateFeature(
          intensity,
          feature.healthy,
          feature.warning,
          feature.critical
        );
      });
    });

    // Generate advanced HRV features
    advancedHRVFeatures.forEach(feature => {
      features[feature.key] = interpolateFeature(
        intensity,
        feature.healthy,
        feature.warning,
        feature.critical
      );
    });

    // Add additional features for complete model input
    features.ClothingInsulation = interpolateFeature(intensity, 0.5, 0.7, 1.0);
    features.ActivityLevel = interpolateFeature(intensity, 1, 3, 5);

    return features;
  }, []);

  // Real-time simulation update (stable reference)
  const updateSimulation = useCallback(async (intensity: number) => {
    const features = generateSimulatedFeatures(intensity);

    setSimulation(prev => ({
      ...prev,
      intensity,
      features,
      isSimulating: true,
    }));

    // Run XGBoost prediction with simulated data
    try {
      const biometricData: BiometricData = {
        Gender: features.Gender,
        Age: features.Age,
        Temperature: features.Temperature,
        Humidity: features.Humidity,
        AirVelocity: features.AirVelocity || 0.3,
        HeartRate: features.hrv_mean_hr,
        SkinTemperature: features.SkinTemperature,
        CoreBodyTemperature: features.CoreBodyTemperature,
        SkinConductance: features.SkinConductance,
        MetabolicRate: features.MetabolicRate,
        ActivityLevel: features.ActivityLevel,
        ClothingInsulation: features.ClothingInsulation,
        RespiratoryRate: features.RespiratoryRate,
        HydrationLevel: features.HydrationLevel,
        timestamp: new Date().toISOString(),
        workerId: `SIM_${Date.now()}`,
        locationId: 'SIMULATION',
      };

      const result = await predictRef.current(biometricData);

      setSimulation(prev => ({
        ...prev,
        prediction: result as PredictionResult,
        isSimulating: false,
      }));
    } catch (err) {
      console.error('Simulation prediction failed:', err);
      setSimulation(prev => ({
        ...prev,
        isSimulating: false,
      }));
    }
  }, [generateSimulatedFeatures]);

  // Initialize simulation only once
  useEffect(() => {
    updateSimulation(0);
  }, []);

  // Helper functions for visual feedback
  const getIntensityColor = (intensity: number) => {
    if (intensity < 0.33) return 'from-green-400 to-green-600';
    if (intensity < 0.66) return 'from-yellow-400 to-orange-500';
    return 'from-red-500 to-red-700';
  };

  const getIntensityLabel = (intensity: number) => {
    if (intensity < 0.33) return 'Healthy Conditions';
    if (intensity < 0.66) return 'Heat Stress Warning';
    return 'Critical Heat Exhaustion';
  };

  const getFeatureChangeIndicator = (current: number, healthy: number, critical: number) => {
    const range = Math.abs(critical - healthy);
    const change = Math.abs(current - healthy) / range;

    if (change < 0.33) return { color: 'text-green-600', icon: CheckCircle };
    if (change < 0.66) return { color: 'text-yellow-600', icon: TrendingUp };
    return { color: 'text-red-600', icon: AlertTriangle };
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: typeof value === 'string' ? (isNaN(Number(value)) ? value : Number(value)) : value
    }));
  };

  const handleManualPredict = async () => {
    try {
      clearError();

      const biometricData: BiometricData = {
        Gender: formData.Gender,
        Age: formData.Age,
        Temperature: formData.Temperature,
        Humidity: formData.Humidity,
        AirVelocity: 0.3,
        HeartRate: formData.hrv_mean_hr,
        SkinTemperature: 35.0,
        CoreBodyTemperature: 37.0,
        SkinConductance: 10.0,
        MetabolicRate: 1.5,
        ActivityLevel: 2,
        ClothingInsulation: 0.5,
        timestamp: new Date().toISOString(),
        workerId: formData.worker_id || `MANUAL_${Date.now()}`,
        locationId: formData.locationId,
      };

      const result = await predict(biometricData);
      setLastPrediction(result as PredictionResult);
    } catch (err) {
      console.error('Prediction failed:', err);
    }
  };

  const getRiskColor = (riskScore?: number): string => {
    if (!riskScore) return 'text-gray-500';
    if (riskScore < 0.25) return 'text-green-600';
    if (riskScore < 0.5) return 'text-yellow-600';
    if (riskScore < 0.75) return 'text-orange-600';
    return 'text-red-600';
  };

  const getRiskBadgeColor = (riskLevel?: string): 'default' | 'secondary' | 'destructive' => {
    if (!riskLevel) return 'default';
    const level = riskLevel.toLowerCase();
    if (level.includes('safe') || level.includes('low')) return 'secondary';
    if (level.includes('danger') || level.includes('critical') || level.includes('high')) return 'destructive';
    return 'default';
  };

  return (
    <DashboardLayout>
      <DashboardPageContainer
        title="Interactive Heat Stress Simulation"
        description="Business demo simulation showcasing real-time XGBoost predictions and worker health monitoring"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Heat Stress Simulation' },
        ]}
        actions={
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="text-blue-600 border-blue-200">
              <Zap className="h-3 w-3 mr-1" />
              Live XGBoost Predictions
            </Badge>
          </div>
        }
      >
        {/* SIMULATION CONTENT */}
        <div className="w-full">
            <DashboardGrid>
              {/* Main Simulation Control */}
              <DashboardWidget colSpan={2}>
                <Card className="h-full">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <PlayCircle className="h-5 w-5 mr-2" />
                      Interactive Heat Stress Simulation
                    </CardTitle>
                    <CardDescription>
                      Drag the slider to simulate how heat stress affects worker health metrics and XGBoost predictions in real-time
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-8">
                    {/* Gradient Slider */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <Label className="text-lg font-medium">Heat Stress Intensity</Label>
                        <Badge className={`bg-gradient-to-r ${getIntensityColor(simulation.intensity)} text-white`}>
                          {getIntensityLabel(simulation.intensity)}
                        </Badge>
                      </div>

                      <div className="relative">
                        {/* Gradient Background */}
                        <div className="absolute inset-0 h-6 bg-gradient-to-r from-green-400 via-yellow-400 via-orange-500 to-red-600 rounded-lg opacity-80"></div>

                        {/* Slider */}
                        <Slider
                          value={[simulation.intensity * 100]}
                          onValueChange={([value]) => updateSimulation(value / 100)}
                          max={100}
                          step={1}
                          className="relative z-10"
                        />
                      </div>

                      {/* Intensity Labels */}
                      <div className="flex justify-between text-sm text-gray-600">
                        <span className="flex items-center">
                          <CheckCircle className="h-4 w-4 text-green-600 mr-1" />
                          Healthy
                        </span>
                        <span className="flex items-center">
                          <TrendingUp className="h-4 w-4 text-yellow-600 mr-1" />
                          Warning
                        </span>
                        <span className="flex items-center">
                          <AlertTriangle className="h-4 w-4 text-red-600 mr-1" />
                          Critical
                        </span>
                      </div>
                    </div>

                    {/* Current Simulation Status */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {(simulation.intensity * 100).toFixed(0)}%
                        </div>
                        <div className="text-sm text-gray-600">Stress Level</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-2xl font-bold ${getRiskColor(simulation.prediction?.risk_score)}`}>
                          {simulation.prediction?.risk_score?.toFixed(3) || '--'}
                        </div>
                        <div className="text-sm text-gray-600">Risk Score</div>
                      </div>
                      <div className="text-center">
                        <Badge variant={getRiskBadgeColor(simulation.prediction?.risk_level)}>
                          {simulation.prediction?.risk_level || 'Calculating...'}
                        </Badge>
                        <div className="text-sm text-gray-600 mt-1">Risk Level</div>
                      </div>
                    </div>

                    {/* Business Explanation */}
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h4 className="font-medium text-blue-900 mb-2 flex items-center">
                        <Eye className="h-4 w-4 mr-1" />
                        What You're Seeing:
                      </h4>
                      <p className="text-sm text-blue-800">
                        {simulation.intensity < 0.33 && "Worker is in healthy conditions. All biometric indicators show normal ranges with minimal heat stress."}
                        {simulation.intensity >= 0.33 && simulation.intensity < 0.66 && "Worker is entering heat stress warning zone. Physiological systems are responding to increased thermal load."}
                        {simulation.intensity >= 0.66 && "Worker is approaching critical heat exhaustion. Multiple systems show severe stress requiring immediate intervention."}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </DashboardWidget>

              {/* Live Feature Changes Display */}
              <DashboardWidget>
                <Card className="h-full">
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Activity className="h-5 w-5 mr-2" />
                      Live Biometric Changes
                    </CardTitle>
                    <CardDescription>
                      Watch how 55+ worker health metrics change as heat stress increases
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {simulation.isSimulating && (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                        <span className="ml-2 text-gray-600">Updating model...</span>
                      </div>
                    )}

                    {featureCategories.map(category => {
                      const Icon = category.icon;
                      return (
                        <div key={category.name} className="space-y-2">
                          <h4 className="font-medium flex items-center text-gray-900">
                            <Icon className="h-4 w-4 mr-2" />
                            {category.name}
                          </h4>
                          <div className="space-y-1 pl-6">
                            {category.features.slice(0, 3).map(feature => {
                              const currentValue = simulation.features[feature.key] || 0;
                              const indicator = getFeatureChangeIndicator(currentValue, feature.healthy, feature.critical);
                              const IndicatorIcon = indicator.icon;

                              return (
                                <div key={feature.key} className="flex items-center justify-between py-1">
                                  <div className="flex items-center space-x-2">
                                    <IndicatorIcon className={`h-3 w-3 ${indicator.color}`} />
                                    <span className="text-sm text-gray-700">{feature.name}</span>
                                  </div>
                                  <span className={`text-sm font-medium ${indicator.color}`}>
                                    {feature.format ? feature.format(currentValue) : `${currentValue.toFixed(1)}${feature.unit}`}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </DashboardWidget>

              {/* XGBoost Prediction Results */}
              <DashboardWidget colSpan={2}>
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Shield className="h-5 w-5 mr-2" />
                      XGBoost Model Predictions & OSHA Recommendations
                    </CardTitle>
                    <CardDescription>
                      Real-time safety analysis from machine learning model
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {simulation.prediction ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Prediction Summary */}
                        <div className="space-y-4">
                          <div>
                            <Label className="text-sm font-medium">Thermal Comfort Level</Label>
                            <div className="text-xl font-bold text-gray-900">
                              {simulation.prediction.thermal_comfort}
                            </div>
                          </div>

                          <div>
                            <Label className="text-sm font-medium">Confidence Level</Label>
                            <div className="flex items-center space-x-2">
                              <Progress value={simulation.prediction.confidence * 100} className="flex-1" />
                              <span className="text-sm font-medium">{(simulation.prediction.confidence * 100).toFixed(0)}%</span>
                            </div>
                          </div>

                          {simulation.prediction.requires_immediate_attention && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                              <div className="flex items-center text-red-800">
                                <AlertTriangle className="h-5 w-5 mr-2" />
                                <span className="font-medium">Immediate Attention Required</span>
                              </div>
                            </div>
                          )}
                        </div>

                        {/* OSHA Recommendations */}
                        <div className="space-y-4">
                          <Label className="text-sm font-medium">Safety Recommendations</Label>
                          <div className="space-y-2">
                            {simulation.prediction.osha_recommendations?.map((rec, index) => (
                              <div key={index} className="flex items-start space-x-2">
                                <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                                <span className="text-sm text-gray-700">{rec}</span>
                              </div>
                            )) || (
                              <p className="text-sm text-gray-500">No specific recommendations at this risk level</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>Move the slider above to see XGBoost predictions</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </DashboardWidget>
            </DashboardGrid>
        </div>
      </DashboardPageContainer>
    </DashboardLayout>
  );
}