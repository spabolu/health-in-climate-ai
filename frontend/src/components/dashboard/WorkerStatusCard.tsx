/**
 * HeatGuard Pro Worker Status Card
 * Comprehensive worker status display with biometric data and thermal comfort prediction
 */

'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import BiometricIndicator, { BiometricSummary } from './BiometricIndicator';
import ThermalComfortIndicator, { ThermalComfortBadge } from './ThermalComfortIndicator';
import { WorkerProfile, BiometricData, ThermalComfortPrediction } from '@/types/thermal-comfort';
import {
  User,
  MapPin,
  Clock,
  Phone,
  AlertTriangle,
  Settings,
  Activity,
  Eye,
  Bell,
  MoreVertical,
  Wifi,
  WifiOff,
} from 'lucide-react';

interface WorkerStatusCardProps {
  worker: WorkerProfile;
  biometricData?: BiometricData;
  prediction?: ThermalComfortPrediction;
  className?: string;
  variant?: 'compact' | 'detailed' | 'summary';
  isOnline?: boolean;
  lastUpdate?: string;
  onViewDetails?: (workerId: string) => void;
  onEmergencyContact?: (workerId: string) => void;
  onAcknowledgeAlert?: (workerId: string) => void;
}

export default function WorkerStatusCard({
  worker,
  biometricData,
  prediction,
  className = '',
  variant = 'detailed',
  isOnline = true,
  lastUpdate,
  onViewDetails,
  onEmergencyContact,
  onAcknowledgeAlert,
}: WorkerStatusCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Determine overall worker status
  const getOverallStatus = () => {
    if (!prediction || !biometricData) return 'unknown';
    if (prediction.risk_level === 'critical') return 'critical';
    if (prediction.risk_level === 'high') return 'warning';
    return 'safe';
  };

  const overallStatus = getOverallStatus();

  const statusConfig = {
    safe: {
      color: 'border-green-200 bg-green-50',
      textColor: 'text-green-800',
      badgeVariant: 'default' as const,
      indicator: 'bg-green-500',
    },
    warning: {
      color: 'border-yellow-200 bg-yellow-50',
      textColor: 'text-yellow-800',
      badgeVariant: 'secondary' as const,
      indicator: 'bg-yellow-500',
    },
    critical: {
      color: 'border-red-200 bg-red-50',
      textColor: 'text-red-800',
      badgeVariant: 'destructive' as const,
      indicator: 'bg-red-500',
    },
    unknown: {
      color: 'border-gray-200 bg-gray-50',
      textColor: 'text-gray-800',
      badgeVariant: 'outline' as const,
      indicator: 'bg-gray-500',
    },
  };

  const status = statusConfig[overallStatus];

  // Get worker initials for avatar
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase();
  };

  // Format time since last update
  const getTimeSinceUpdate = () => {
    if (!lastUpdate) return 'No data';
    const diff = Date.now() - new Date(lastUpdate).getTime();
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    if (minutes > 0) return `${minutes}m ago`;
    return `${seconds}s ago`;
  };

  // Compact variant for grid views
  if (variant === 'compact') {
    return (
      <Card className={`${status.color} border-2 ${className}`}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Avatar className="h-10 w-10">
                  <AvatarImage src={`/avatars/${worker.id}.jpg`} />
                  <AvatarFallback>{getInitials(worker.name)}</AvatarFallback>
                </Avatar>
                <div className={`absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-white ${status.indicator}`} />
              </div>
              <div>
                <h3 className="font-medium text-gray-900">{worker.name}</h3>
                <p className="text-sm text-gray-600">{worker.assigned_location}</p>
              </div>
            </div>
            <div className="flex items-center space-x-1">
              {isOnline ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onViewDetails?.(worker.id)}>
                    <Eye className="mr-2 h-4 w-4" />
                    View Details
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEmergencyContact?.(worker.id)}>
                    <Phone className="mr-2 h-4 w-4" />
                    Emergency Contact
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => onAcknowledgeAlert?.(worker.id)}>
                    <Bell className="mr-2 h-4 w-4" />
                    Acknowledge Alert
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          {biometricData && prediction && (
            <div className="space-y-2">
              <ThermalComfortBadge
                thermalComfort={prediction.thermal_comfort}
                riskLevel={prediction.risk_level}
              />
              <BiometricSummary
                heartRate={biometricData.HeartRate}
                bodyTemperature={biometricData.CoreBodyTemperature}
                skinTemperature={biometricData.SkinTemperature}
                hydration={biometricData.HydrationLevel || 0.7}
                overallStatus={overallStatus}
              />
            </div>
          )}

          <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
            <span>{getTimeSinceUpdate()}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs"
            >
              {isExpanded ? 'Less' : 'More'}
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  // Summary variant for list views
  if (variant === 'summary') {
    return (
      <Card className={`${status.color} border-l-4 ${className}`}>
        <div className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Avatar className="h-12 w-12">
                <AvatarImage src={`/avatars/${worker.id}.jpg`} />
                <AvatarFallback>{getInitials(worker.name)}</AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-gray-900">{worker.name}</h3>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <MapPin className="h-3 w-3" />
                  <span>{worker.assigned_location}</span>
                </div>
                {prediction && (
                  <ThermalComfortBadge
                    thermalComfort={prediction.thermal_comfort}
                    riskLevel={prediction.risk_level}
                    className="mt-1"
                  />
                )}
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {biometricData && (
                <div className="text-right text-sm">
                  <p className="font-medium text-gray-900">
                    {biometricData.CoreBodyTemperature.toFixed(1)}°C
                  </p>
                  <p className="text-gray-600">{biometricData.HeartRate} BPM</p>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Badge variant={status.badgeVariant}>
                  {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onViewDetails?.(worker.id)}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Detailed variant - full worker status display
  return (
    <Card className={`${status.color} border-2 ${className}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Avatar className="h-16 w-16">
                <AvatarImage src={`/avatars/${worker.id}.jpg`} />
                <AvatarFallback className="text-lg">{getInitials(worker.name)}</AvatarFallback>
              </Avatar>
              <div className={`absolute -bottom-1 -right-1 h-4 w-4 rounded-full border-2 border-white ${status.indicator}`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{worker.name}</h3>
              <div className="flex items-center space-x-2 text-sm text-gray-600 mt-1">
                <MapPin className="h-4 w-4" />
                <span>{worker.assigned_location}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600 mt-1">
                <User className="h-4 w-4" />
                <span>{worker.gender}, {worker.age} years old</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className="text-right text-sm text-gray-500">
              <p>Last Update</p>
              <p className="font-medium">{getTimeSinceUpdate()}</p>
            </div>
            {isOnline ? (
              <Wifi className="h-5 w-5 text-green-500" />
            ) : (
              <WifiOff className="h-5 w-5 text-red-500" />
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onViewDetails?.(worker.id)}>
                  <Eye className="mr-2 h-4 w-4" />
                  Full Details
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEmergencyContact?.(worker.id)}>
                  <Phone className="mr-2 h-4 w-4" />
                  Emergency Contact
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onAcknowledgeAlert?.(worker.id)}>
                  <Bell className="mr-2 h-4 w-4" />
                  Acknowledge Alert
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Activity className="mr-2 h-4 w-4" />
                  View History
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Thermal Comfort Prediction */}
          {prediction && (
            <ThermalComfortIndicator
              prediction={prediction}
              size="md"
              showDetails={false}
              showRecommendations={false}
            />
          )}

          {/* Key Biometrics */}
          {biometricData && (
            <div className="space-y-4">
              <h4 className="font-medium text-gray-900">Key Vitals</h4>
              <div className="grid grid-cols-2 gap-3">
                <BiometricIndicator
                  type="heart_rate"
                  value={biometricData.HeartRate}
                  unit="BPM"
                  label="Heart Rate"
                  status={biometricData.HeartRate > 120 ? 'warning' : biometricData.HeartRate > 140 ? 'critical' : 'safe'}
                  threshold={{
                    min: 60,
                    max: 100,
                    warningMax: 120,
                  }}
                  size="sm"
                  showProgress
                />
                <BiometricIndicator
                  type="body_temperature"
                  value={biometricData.CoreBodyTemperature}
                  unit="°C"
                  label="Body Temp"
                  status={biometricData.CoreBodyTemperature > 38 ? 'warning' : biometricData.CoreBodyTemperature > 39 ? 'critical' : 'safe'}
                  threshold={{
                    min: 36.5,
                    max: 37.5,
                    warningMax: 38,
                  }}
                  size="sm"
                  showProgress
                />
              </div>
            </div>
          )}
        </div>

        {/* Expandable Details */}
        {isExpanded && biometricData && (
          <div className="border-t border-gray-200 pt-6">
            <h4 className="font-medium text-gray-900 mb-4">Detailed Biometrics</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <BiometricIndicator
                type="skin_temperature"
                value={biometricData.SkinTemperature}
                unit="°C"
                label="Skin Temperature"
                status={biometricData.SkinTemperature > 35 ? 'warning' : 'safe'}
                threshold={{
                  min: 30,
                  max: 35,
                  warningMax: 36,
                }}
                size="sm"
              />
              <BiometricIndicator
                type="skin_conductance"
                value={biometricData.SkinConductance}
                unit="μS"
                label="Skin Conductance"
                status="safe"
                threshold={{
                  min: 5,
                  max: 25,
                }}
                size="sm"
              />
              <BiometricIndicator
                type="hydration"
                value={biometricData.HydrationLevel || 0.7}
                unit=""
                label="Hydration Level"
                status={biometricData.HydrationLevel && biometricData.HydrationLevel < 0.6 ? 'warning' : 'safe'}
                threshold={{
                  min: 0,
                  max: 1,
                  warningMin: 0.6,
                }}
                size="sm"
                showProgress
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-600">{worker.shift_pattern}</span>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Show Less' : 'Show More'}
            </Button>
            <Button
              size="sm"
              onClick={() => onViewDetails?.(worker.id)}
            >
              Full Details
            </Button>
            {overallStatus === 'critical' && (
              <Button
                variant="destructive"
                size="sm"
                onClick={() => onEmergencyContact?.(worker.id)}
              >
                <AlertTriangle className="h-4 w-4 mr-2" />
                Emergency
              </Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}