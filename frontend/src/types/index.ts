export interface Worker {
  id: string
  name: string
  age: number
  gender: 'male' | 'female'
  medical_conditions: string[]
  heat_tolerance: 'low' | 'normal' | 'high'
  emergency_contact: {
    name: string
    phone: string
  }
  assigned_location: string
  shift_pattern: string
  created_at: string
  updated_at: string
  status: 'active' | 'break' | 'inactive'
  last_reading?: string
  current_risk?: string
  active_alerts?: number
}

export interface BiometricReading {
  id: number
  worker_id: string
  timestamp: string
  Gender: number
  Age: number
  Temperature: number
  Humidity: number
  AirVelocity: number
  HeartRate: number
  SkinTemperature: number
  CoreBodyTemperature: number
  SkinConductance: number
  MetabolicRate: number
  ActivityLevel: number
  ClothingInsulation: number
  RespiratoryRate: number
  HydrationLevel: number
  location_id: string
  [key: string]: string | number // For HRV features
}

export interface ThermalComfortPrediction {
  id: number
  worker_id: string
  biometric_reading_id: number
  timestamp: string
  thermal_comfort: string
  risk_level: 'comfortable' | 'slightly_uncomfortable' | 'uncomfortable' | 'very_uncomfortable'
  confidence: number
  recommended_action: string
  break_recommendation_minutes: number
  model_version: string
}

export interface Alert {
  id: string
  worker_id: string
  alert_type: string
  severity: 'low' | 'moderate' | 'high' | 'critical'
  message: string
  recommended_actions: string[]
  timestamp: string
  acknowledged: boolean
  resolved: boolean
  location: string
  worker_name?: string
}

export interface DashboardMetrics {
  active_workers: number
  total_workers: number
  critical_alerts: number
  unacknowledged_alerts: number
  average_risk_level: number
  environmental_conditions: {
    temperature: number
    humidity: number
    air_quality_index: number
    wind_speed: number
  }
  recent_readings_count: number
  risk_distribution: Record<string, number>
  location_metrics: Record<string, {
    workers_count: number
    active_alerts: number
    risk_level: string
  }>
  timestamp: string
  system_status: string
  model_accuracy: number
  data_quality_score: number
  compliance_score: number
}

export interface HistoricalData {
  worker_id: string
  readings: BiometricReading[]
  predictions: ThermalComfortPrediction[]
  summary: {
    total_readings: number
    total_predictions: number
    date_range: {
      start: string | null
      end: string | null
    }
  }
}