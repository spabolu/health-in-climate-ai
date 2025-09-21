/**
 * Thermal Comfort Prediction Types
 * Types for HeatGuard Pro thermal comfort prediction system
 */

export interface BiometricData {
  // Demographics
  Gender: number; // 1 for Male, 0 for Female
  Age: number;

  // Environmental conditions
  Temperature: number; // Air temperature (°C)
  Humidity: number; // Relative humidity (%)
  AirVelocity: number; // Air velocity (m/s)

  // Wearable device data
  HeartRate: number; // BPM
  SkinTemperature: number; // °C
  CoreBodyTemperature: number; // °C
  SkinConductance: number; // μS (microsiemens)

  // Activity and metabolic data
  MetabolicRate: number; // MET (metabolic equivalent)
  ActivityLevel: number; // 0-5 scale
  ClothingInsulation: number; // clo units

  // Additional physiological data
  RespiratoryRate?: number; // breaths per minute
  BloodPressureSystolic?: number; // mmHg
  BloodPressureDiastolic?: number; // mmHg
  HydrationLevel?: number; // 0-1 scale

  // Time and location context
  timestamp?: string; // ISO timestamp
  workerId?: string; // Unique worker identifier
  locationId?: string; // Location/zone identifier
}

export interface ThermalComfortPrediction {
  // Core prediction results
  thermal_comfort: 'Hot' | 'Warm' | 'Slightly Warm' | 'Neutral' | 'Slightly Cool' | 'Cool' | 'Cold';
  risk_level: 'low' | 'moderate' | 'high' | 'critical';
  confidence: number; // 0-1 confidence score

  // Safety recommendations
  recommended_action: 'continue' | 'caution' | 'rest' | 'immediate_action';
  break_recommendation_minutes?: number; // Recommended break duration

  // Prediction metadata
  prediction_timestamp: string;
  model_version: string;

  // Additional context
  heat_index?: number; // Calculated heat index
  wet_bulb_temperature?: number; // WBGT if available
}

export interface BatchPredictionRequest {
  data: BiometricData[];
}

export interface BatchPredictionResponse {
  predictions: ThermalComfortPrediction[];
  batch_id: string;
  processed_count: number;
  error_count: number;
  processing_time_ms: number;
}

export interface WorkerProfile {
  id: string;
  name: string;
  age: number;
  gender: 'male' | 'female';
  medical_conditions: string[];
  heat_tolerance: 'low' | 'normal' | 'high';
  emergency_contact: {
    name: string;
    phone: string;
    relationship: string;
  };
  assigned_location: string;
  shift_pattern: string;
  created_at: string;
  updated_at: string;
}

export interface HealthAlert {
  id: string;
  worker_id: string;
  alert_type: 'heat_exhaustion_risk' | 'dehydration_warning' | 'heart_rate_anomaly' | 'critical_temperature';
  severity: 'low' | 'moderate' | 'high' | 'critical';
  message: string;
  recommended_actions: string[];
  timestamp: string;
  acknowledged: boolean;
  resolved: boolean;
  location: string;
}

export interface WorkLocation {
  id: string;
  name: string;
  description: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  environmental_sensors: boolean;
  max_workers: number;
  safety_protocols: string[];
  emergency_procedures: string[];
}

export interface HistoricalData {
  worker_id: string;
  date_range: {
    start: string;
    end: string;
  };
  thermal_comfort_trends: Array<{
    timestamp: string;
    thermal_comfort: string;
    risk_level: string;
    environmental_temp: number;
    heart_rate: number;
  }>;
  incident_count: number;
  average_risk_level: number;
  recommendations: string[];
}

export interface DashboardMetrics {
  total_workers: number;
  active_workers: number;
  workers_at_risk: number;
  critical_alerts: number;
  average_temperature: number;
  average_humidity: number;
  incidents_today: number;
  compliance_score: number; // 0-100 OSHA compliance score
}

// API Response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: string;
}

// API Error types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  timestamp: string;
}

// Real-time data streaming types
export interface RealTimeUpdate {
  type: 'biometric_update' | 'alert' | 'environmental_change' | 'worker_status';
  worker_id?: string;
  location_id?: string;
  data: unknown;
  timestamp: string;
}

export interface ComplianceReport {
  report_id: string;
  generated_at: string;
  period: {
    start: string;
    end: string;
  };
  total_incidents: number;
  osha_violations: number;
  safety_score: number;
  worker_statistics: Array<{
    worker_id: string;
    hours_worked: number;
    incidents: number;
    compliance_rating: 'excellent' | 'good' | 'needs_improvement' | 'poor';
  }>;
  recommendations: string[];
}