/**
 * HeatGuard Pro Biometric Indicator Component
 * Individual biometric data display with safety thresholds
 */

'use client';

import { ReactNode } from 'react';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Heart,
  Thermometer,
  Droplets,
  Activity,
  Gauge,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';

interface BiometricIndicatorProps {
  type: 'heart_rate' | 'body_temperature' | 'skin_temperature' | 'skin_conductance' | 'hydration' | 'respiratory_rate';
  value: number;
  unit: string;
  label: string;
  status: 'safe' | 'warning' | 'critical' | 'unknown';
  trend?: 'up' | 'down' | 'stable';
  threshold?: {
    min: number;
    max: number;
    warningMin?: number;
    warningMax?: number;
  };
  className?: string;
  showProgress?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const iconMap = {
  heart_rate: Heart,
  body_temperature: Thermometer,
  skin_temperature: Thermometer,
  skin_conductance: Droplets,
  hydration: Droplets,
  respiratory_rate: Activity,
};

const statusColors = {
  safe: 'text-green-600 bg-green-50 border-green-200',
  warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  critical: 'text-red-600 bg-red-50 border-red-200',
  unknown: 'text-gray-600 bg-gray-50 border-gray-200',
};

const statusBadgeVariants = {
  safe: 'default' as const,
  warning: 'secondary' as const,
  critical: 'destructive' as const,
  unknown: 'outline' as const,
};

export default function BiometricIndicator({
  type,
  value,
  unit,
  label,
  status,
  trend,
  threshold,
  className = '',
  showProgress = false,
  size = 'md',
}: BiometricIndicatorProps) {
  const Icon = iconMap[type] || Gauge;

  const sizeClasses = {
    sm: {
      container: 'p-3',
      icon: 'h-4 w-4',
      value: 'text-lg',
      label: 'text-xs',
    },
    md: {
      container: 'p-4',
      icon: 'h-5 w-5',
      value: 'text-xl',
      label: 'text-sm',
    },
    lg: {
      container: 'p-6',
      icon: 'h-6 w-6',
      value: 'text-2xl',
      label: 'text-base',
    },
  };

  const classes = sizeClasses[size];

  // Calculate progress percentage if threshold is provided
  const getProgressValue = () => {
    if (!threshold) return 0;
    const range = threshold.max - threshold.min;
    const progress = ((value - threshold.min) / range) * 100;
    return Math.min(Math.max(progress, 0), 100);
  };

  const getProgressColor = () => {
    if (!threshold) return 'bg-blue-600';

    if (threshold.warningMin && value < threshold.warningMin) return 'bg-yellow-500';
    if (threshold.warningMax && value > threshold.warningMax) return 'bg-yellow-500';
    if (value < threshold.min || value > threshold.max) return 'bg-red-500';
    return 'bg-green-500';
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3 text-orange-500" />;
      case 'down':
        return <TrendingDown className="h-3 w-3 text-blue-500" />;
      case 'stable':
        return <Minus className="h-3 w-3 text-gray-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'safe':
        return 'Normal';
      case 'warning':
        return 'Caution';
      case 'critical':
        return 'Critical';
      case 'unknown':
        return 'Unknown';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`
      bg-white border border-gray-200 rounded-lg
      ${statusColors[status]}
      ${classes.container}
      ${className}
    `}>
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-2">
          <Icon className={`${classes.icon} ${
            status === 'safe' ? 'text-green-600' :
            status === 'warning' ? 'text-yellow-600' :
            status === 'critical' ? 'text-red-600' : 'text-gray-600'
          }`} />
          <div>
            <p className={`font-medium text-gray-900 ${classes.label}`}>{label}</p>
            {threshold && (
              <p className="text-xs text-gray-500">
                Range: {threshold.min}-{threshold.max} {unit}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {trend && getTrendIcon()}
          <Badge variant={statusBadgeVariants[status]} className="text-xs">
            {getStatusText()}
          </Badge>
        </div>
      </div>

      <div className="mt-3">
        <div className="flex items-baseline space-x-1">
          <span className={`font-bold ${classes.value} text-gray-900`}>
            {value.toFixed(1)}
          </span>
          <span className={`${classes.label} text-gray-600`}>{unit}</span>
        </div>

        {showProgress && threshold && (
          <div className="mt-2">
            <Progress
              value={getProgressValue()}
              className="h-2"
              style={{
                '--progress-background': getProgressColor(),
              } as React.CSSProperties}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{threshold.min}</span>
              <span>{threshold.max}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Biometric Indicators Grid
 * Layout component for multiple biometric indicators
 */
interface BiometricIndicatorsGridProps {
  children: ReactNode;
  className?: string;
  columns?: 1 | 2 | 3 | 4;
}

export function BiometricIndicatorsGrid({
  children,
  className = '',
  columns = 2
}: BiometricIndicatorsGridProps) {
  const gridClasses = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={`grid ${gridClasses[columns]} gap-4 ${className}`}>
      {children}
    </div>
  );
}

/**
 * Compact Biometric Summary
 * Condensed view for multiple biometrics in limited space
 */
interface BiometricSummaryProps {
  heartRate: number;
  bodyTemperature: number;
  skinTemperature: number;
  hydration: number;
  overallStatus: 'safe' | 'warning' | 'critical';
  className?: string;
}

export function BiometricSummary({
  heartRate,
  bodyTemperature,
  skinTemperature,
  hydration,
  overallStatus,
  className = '',
}: BiometricSummaryProps) {
  const statusColor = {
    safe: 'text-green-600',
    warning: 'text-yellow-600',
    critical: 'text-red-600',
  }[overallStatus];

  return (
    <div className={`bg-white border rounded-lg p-3 ${className}`}>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex items-center space-x-2">
          <Heart className={`h-4 w-4 ${statusColor}`} />
          <span className="text-sm font-medium">{heartRate}</span>
          <span className="text-xs text-gray-500">bpm</span>
        </div>

        <div className="flex items-center space-x-2">
          <Thermometer className={`h-4 w-4 ${statusColor}`} />
          <span className="text-sm font-medium">{bodyTemperature.toFixed(1)}</span>
          <span className="text-xs text-gray-500">°C</span>
        </div>

        <div className="flex items-center space-x-2">
          <Thermometer className={`h-4 w-4 ${statusColor}`} />
          <span className="text-sm font-medium">{skinTemperature.toFixed(1)}</span>
          <span className="text-xs text-gray-500">°C skin</span>
        </div>

        <div className="flex items-center space-x-2">
          <Droplets className={`h-4 w-4 ${statusColor}`} />
          <span className="text-sm font-medium">{(hydration * 100).toFixed(0)}</span>
          <span className="text-xs text-gray-500">% hydro</span>
        </div>
      </div>
    </div>
  );
}