'use client'

import React, { useState, useEffect } from 'react'
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  X,
  User,
  MapPin,
  Thermometer,
  Heart,
  Bell
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { Alert } from '@/types'

interface AlertNotificationProps {
  alert: Alert
  onAcknowledge?: (alertId: string) => void
  onResolve?: (alertId: string) => void
  onDismiss?: (alertId: string) => void
  showActions?: boolean
  compact?: boolean
}

export function AlertNotification({
  alert,
  onAcknowledge,
  onResolve,
  onDismiss,
  showActions = true,
  compact = false
}: AlertNotificationProps) {
  const [isVisible, setIsVisible] = useState(true)

  const getSeverityConfig = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          bgColor: 'bg-red-50 border-red-200',
          textColor: 'text-red-800',
          iconColor: 'text-red-600',
          badgeVariant: 'danger' as const,
          pulseColor: 'bg-red-500',
          icon: AlertTriangle
        }
      case 'high':
        return {
          bgColor: 'bg-orange-50 border-orange-200',
          textColor: 'text-orange-800',
          iconColor: 'text-orange-600',
          badgeVariant: 'warning' as const,
          pulseColor: 'bg-orange-500',
          icon: AlertTriangle
        }
      case 'moderate':
        return {
          bgColor: 'bg-yellow-50 border-yellow-200',
          textColor: 'text-yellow-800',
          iconColor: 'text-yellow-600',
          badgeVariant: 'warning' as const,
          pulseColor: 'bg-yellow-500',
          icon: AlertTriangle
        }
      default:
        return {
          bgColor: 'bg-blue-50 border-blue-200',
          textColor: 'text-blue-800',
          iconColor: 'text-blue-600',
          badgeVariant: 'secondary' as const,
          pulseColor: 'bg-blue-500',
          icon: Bell
        }
    }
  }

  const getAlertTypeIcon = (alertType: string) => {
    switch (alertType) {
      case 'heat_exhaustion_risk':
      case 'temperature_spike':
        return Thermometer
      case 'high_heart_rate':
        return Heart
      case 'dehydration_warning':
        return AlertTriangle
      default:
        return AlertTriangle
    }
  }

  const formatTimestamp = (timestamp: string) => {
    const now = new Date()
    const alertTime = new Date(timestamp)
    const diffMs = now.getTime() - alertTime.getTime()
    const diffMins = Math.floor(diffMs / (1000 * 60))

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    return alertTime.toLocaleDateString()
  }

  const config = getSeverityConfig(alert.severity)
  const AlertTypeIcon = getAlertTypeIcon(alert.alert_type)
  const StatusIcon = config.icon

  const handleAcknowledge = () => {
    onAcknowledge?.(alert.id)
  }

  const handleResolve = () => {
    onResolve?.(alert.id)
  }

  const handleDismiss = () => {
    setIsVisible(false)
    setTimeout(() => onDismiss?.(alert.id), 300)
  }

  if (!isVisible) return null

  if (compact) {
    return (
      <div className={`flex items-center space-x-3 p-3 rounded-lg border transition-all ${config.bgColor}`}>
        <div className="flex-shrink-0">
          <StatusIcon className={`h-4 w-4 ${config.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <p className={`text-sm font-medium ${config.textColor}`}>
              {alert.worker_name}
            </p>
            <Badge variant={config.badgeVariant} className="text-xs">
              {alert.severity.toUpperCase()}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground truncate">
            {alert.message}
          </p>
        </div>
        {onDismiss && (
          <Button variant="ghost" size="sm" onClick={handleDismiss}>
            <X className="h-3 w-3" />
          </Button>
        )}
      </div>
    )
  }

  return (
    <Card className={`${config.bgColor} transition-all duration-300 ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}`}>
      <CardContent className="p-4">
        <div className="flex items-start space-x-4">
          {/* Alert Icon with Pulse Animation */}
          <div className="flex-shrink-0 relative">
            <div className={`absolute inset-0 ${config.pulseColor} rounded-full animate-pulse opacity-75`}></div>
            <div className="relative bg-white rounded-full p-2 shadow-sm">
              <StatusIcon className={`h-5 w-5 ${config.iconColor}`} />
            </div>
          </div>

          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <h4 className={`text-sm font-semibold ${config.textColor}`}>
                  {alert.worker_name || `Worker ${alert.worker_id}`}
                </h4>
                <Badge variant={config.badgeVariant} className="text-xs">
                  {alert.severity.toUpperCase()}
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-muted-foreground">
                  {formatTimestamp(alert.timestamp)}
                </span>
                {onDismiss && (
                  <Button variant="ghost" size="sm" onClick={handleDismiss}>
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>

            {/* Alert Message */}
            <p className={`text-sm ${config.textColor} mb-3`}>
              {alert.message}
            </p>

            {/* Alert Details */}
            <div className="flex items-center space-x-4 text-xs text-muted-foreground mb-3">
              <div className="flex items-center space-x-1">
                <AlertTypeIcon className="h-3 w-3" />
                <span className="capitalize">{alert.alert_type.replace('_', ' ')}</span>
              </div>
              <div className="flex items-center space-x-1">
                <MapPin className="h-3 w-3" />
                <span>{alert.location}</span>
              </div>
              <div className="flex items-center space-x-1">
                <User className="h-3 w-3" />
                <span>ID: {alert.worker_id}</span>
              </div>
            </div>

            {/* Recommended Actions */}
            {alert.recommended_actions && alert.recommended_actions.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-medium text-muted-foreground mb-2">Recommended Actions:</p>
                <ul className="text-xs text-muted-foreground space-y-1">
                  {alert.recommended_actions.map((action, index) => (
                    <li key={index} className="flex items-start space-x-1">
                      <span className="text-primary">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Status Indicators */}
            <div className="flex items-center space-x-3 mb-4">
              {alert.acknowledged && (
                <div className="flex items-center space-x-1 text-xs text-green-600">
                  <CheckCircle className="h-3 w-3" />
                  <span>Acknowledged</span>
                </div>
              )}
              {alert.resolved && (
                <div className="flex items-center space-x-1 text-xs text-green-600">
                  <CheckCircle className="h-3 w-3" />
                  <span>Resolved</span>
                </div>
              )}
              {!alert.acknowledged && !alert.resolved && (
                <div className="flex items-center space-x-1 text-xs text-amber-600">
                  <Clock className="h-3 w-3" />
                  <span>Pending Action</span>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            {showActions && (
              <div className="flex space-x-2">
                {!alert.acknowledged && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleAcknowledge}
                    className="text-xs"
                  >
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Acknowledge
                  </Button>
                )}
                {!alert.resolved && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleResolve}
                    className="text-xs"
                  >
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Resolve
                  </Button>
                )}
                {alert.severity === 'critical' && (
                  <Button
                    variant="destructive"
                    size="sm"
                    className="text-xs"
                  >
                    Emergency Protocol
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}