/**
 * HeatGuard Pro Thermal Comfort Indicator
 * Visual display of thermal comfort prediction and safety recommendations
 */

'use client';

import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ThermalComfortPrediction } from '@/types/thermal-comfort';
import {
  Thermometer,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  Gauge,
} from 'lucide-react';

interface ThermalComfortIndicatorProps {
  prediction: ThermalComfortPrediction;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  showRecommendations?: boolean;
}

const thermalComfortColors = {
  'Cold': { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-200', value: 1 },
  'Cool': { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-100', value: 2 },
  'Slightly Cool': { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-100', value: 3 },
  'Neutral': { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200', value: 4 },
  'Slightly Warm': { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-100', value: 5 },
  'Warm': { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', value: 6 },
  'Hot': { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200', value: 7 },
};

const riskLevelConfig = {
  low: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    icon: CheckCircle,
    label: 'Low Risk',
  },
  moderate: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    icon: Activity,
    label: 'Moderate Risk',
  },
  high: {
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    icon: AlertTriangle,
    label: 'High Risk',
  },
  critical: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    icon: AlertTriangle,
    label: 'Critical Risk',
  },
};

const actionConfig = {
  continue: {
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: CheckCircle,
    label: 'Continue Work',
  },
  caution: {
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    icon: Activity,
    label: 'Proceed with Caution',
  },
  rest: {
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    icon: Clock,
    label: 'Take Rest Break',
  },
  immediate_action: {
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: AlertTriangle,
    label: 'Immediate Action Required',
  },
};

export default function ThermalComfortIndicator({
  prediction,
  className = '',
  size = 'md',
  showDetails = true,
  showRecommendations = true,
}: ThermalComfortIndicatorProps) {
  const thermalStyle = thermalComfortColors[prediction.thermal_comfort];
  const riskConfig = riskLevelConfig[prediction.risk_level];
  const actionStyle = actionConfig[prediction.recommended_action];
  const RiskIcon = riskConfig.icon;
  const ActionIcon = actionStyle.icon;

  const sizeClasses = {
    sm: {
      container: 'p-3',
      title: 'text-sm',
      value: 'text-lg',
      description: 'text-xs',
    },
    md: {
      container: 'p-4',
      title: 'text-base',
      value: 'text-xl',
      description: 'text-sm',
    },
    lg: {
      container: 'p-6',
      title: 'text-lg',
      value: 'text-2xl',
      description: 'text-base',
    },
  };

  const classes = sizeClasses[size];

  // Convert thermal comfort to numerical scale for progress bar
  const getThermalComfortProgress = () => {
    return (thermalStyle.value / 7) * 100;
  };

  const getConfidenceColor = () => {
    if (prediction.confidence >= 0.8) return 'text-green-600';
    if (prediction.confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={`bg-white border rounded-lg ${classes.container} ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Thermometer className={`h-5 w-5 ${riskConfig.color}`} />
          <h3 className={`font-semibold text-gray-900 ${classes.title}`}>
            Thermal Comfort
          </h3>
        </div>
        <Badge
          variant={prediction.risk_level === 'critical' ? 'destructive' : 'secondary'}
          className="flex items-center space-x-1"
        >
          <RiskIcon className="h-3 w-3" />
          <span>{riskConfig.label}</span>
        </Badge>
      </div>

      {/* Main Status Display */}
      <div className={`rounded-lg border ${thermalStyle.border} ${thermalStyle.bg} p-4 mb-4`}>
        <div className="text-center">
          <p className={`font-bold ${classes.value} ${thermalStyle.text} mb-2`}>
            {prediction.thermal_comfort}
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm">
            <div className="flex items-center space-x-1">
              <Shield className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">
                {(prediction.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <Gauge className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">
                {new Date(prediction.prediction_timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>

        {/* Thermal Comfort Scale */}
        <div className="mt-4">
          <div className="flex justify-between text-xs text-gray-600 mb-2">
            <span>Cold</span>
            <span>Neutral</span>
            <span>Hot</span>
          </div>
          <div className="relative">
            <Progress
              value={getThermalComfortProgress()}
              className="h-3 bg-gray-200"
            />
            <div
              className="absolute top-0 left-1/2 transform -translate-x-1/2 w-1 h-3 bg-green-600 opacity-75"
              title="Optimal Range"
            />
          </div>
        </div>
      </div>

      {/* Recommended Action */}
      <div className={`rounded-lg border ${actionStyle.border} ${actionStyle.bg} p-3 mb-4`}>
        <div className="flex items-center space-x-2">
          <ActionIcon className={`h-4 w-4 ${actionStyle.color}`} />
          <span className={`font-medium ${actionStyle.color} ${classes.description}`}>
            {actionStyle.label}
          </span>
        </div>
        {prediction.break_recommendation_minutes && (
          <p className={`mt-1 ${classes.description} text-gray-600`}>
            Recommended break: {prediction.break_recommendation_minutes} minutes
          </p>
        )}
      </div>

      {/* Additional Details */}
      {showDetails && (
        <div className="space-y-3">
          {/* Risk Level Details */}
          <div className={`rounded border ${riskConfig.borderColor} ${riskConfig.bgColor} p-3`}>
            <div className="flex items-center justify-between">
              <span className={`font-medium ${classes.description} ${riskConfig.color}`}>
                Risk Assessment
              </span>
              <Badge variant="outline" className="text-xs">
                {prediction.risk_level.toUpperCase()}
              </Badge>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-500">Confidence:</span>
                <span className={`ml-2 font-medium ${getConfidenceColor()}`}>
                  {(prediction.confidence * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-gray-500">Model:</span>
                <span className="ml-2 font-medium text-gray-700">
                  {prediction.model_version}
                </span>
              </div>
            </div>
          </div>

          {/* Environmental Context */}
          {(prediction.heat_index || prediction.wet_bulb_temperature) && (
            <div className="grid grid-cols-2 gap-3">
              {prediction.heat_index && (
                <div className="bg-gray-50 rounded p-2">
                  <p className="text-xs text-gray-500">Heat Index</p>
                  <p className="font-semibold text-gray-900">
                    {prediction.heat_index.toFixed(1)}°F
                  </p>
                </div>
              )}
              {prediction.wet_bulb_temperature && (
                <div className="bg-gray-50 rounded p-2">
                  <p className="text-xs text-gray-500">WBGT</p>
                  <p className="font-semibold text-gray-900">
                    {prediction.wet_bulb_temperature.toFixed(1)}°C
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Safety Recommendations */}
      {showRecommendations && prediction.risk_level !== 'low' && (
        <Alert className="mt-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="text-sm">
            {prediction.risk_level === 'critical' && (
              <span className="text-red-700 font-medium">
                Critical heat stress risk detected. Immediate cooling and medical attention may be required.
              </span>
            )}
            {prediction.risk_level === 'high' && (
              <span className="text-orange-700 font-medium">
                High heat stress risk. Take frequent breaks in cool areas and ensure adequate hydration.
              </span>
            )}
            {prediction.risk_level === 'moderate' && (
              <span className="text-yellow-700 font-medium">
                Monitor closely and take precautionary measures to prevent heat stress.
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}

/**
 * Compact Thermal Comfort Badge
 * Minimal display for grid views
 */
interface ThermalComfortBadgeProps {
  thermalComfort: ThermalComfortPrediction['thermal_comfort'];
  riskLevel: ThermalComfortPrediction['risk_level'];
  className?: string;
}

export function ThermalComfortBadge({
  thermalComfort,
  riskLevel,
  className = ''
}: ThermalComfortBadgeProps) {
  const thermalStyle = thermalComfortColors[thermalComfort];
  const riskConfig = riskLevelConfig[riskLevel];

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <Badge
        className={`${thermalStyle.bg} ${thermalStyle.text} border-0`}
      >
        {thermalComfort}
      </Badge>
      <Badge
        variant={riskLevel === 'critical' ? 'destructive' : 'secondary'}
        className="text-xs"
      >
        {riskConfig.label}
      </Badge>
    </div>
  );
}