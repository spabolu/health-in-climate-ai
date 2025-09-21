'use client'

import React from 'react'
import {
  Heart,
  Thermometer,
  Droplets,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Worker, BiometricReading } from '@/types'

interface WorkerCardProps {
  worker: Worker
  latestReading?: BiometricReading
  onViewDetails?: (workerId: string) => void
  onGenerateAlert?: (workerId: string) => void
}

export function WorkerCard({ worker, latestReading, onViewDetails, onGenerateAlert }: WorkerCardProps) {
  const getRiskLevel = () => {
    if (!latestReading) return 'unknown'

    // Simple risk calculation based on temperature and heart rate
    const temp = latestReading.Temperature
    const heartRate = latestReading.HeartRate
    const skinTemp = latestReading.SkinTemperature

    if (temp > 35 || heartRate > 110 || skinTemp > 38) {
      return 'critical'
    } else if (temp > 32 || heartRate > 100 || skinTemp > 36) {
      return 'high'
    } else if (temp > 28 || heartRate > 90) {
      return 'moderate'
    }
    return 'low'
  }

  const riskLevel = getRiskLevel()

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-500 bg-red-50'
      case 'high': return 'text-orange-500 bg-orange-50'
      case 'moderate': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-500 bg-green-50'
      default: return 'text-gray-500 bg-gray-50'
    }
  }

  const getStatusIcon = (risk: string) => {
    switch (risk) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="h-4 w-4" />
      case 'moderate':
        return <Activity className="h-4 w-4" />
      case 'low':
        return <CheckCircle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const formatTime = (timestamp?: string) => {
    if (!timestamp) return 'No data'
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <Card className={`transition-all hover:shadow-md ${
      riskLevel === 'critical' ? 'ring-2 ring-red-500' :
      riskLevel === 'high' ? 'ring-1 ring-orange-500' : ''
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-full ${getRiskColor(riskLevel)}`}>
              {getStatusIcon(riskLevel)}
            </div>
            <div>
              <CardTitle className="text-base">{worker.name}</CardTitle>
              <p className="text-xs text-muted-foreground">{worker.id}</p>
            </div>
          </div>
          <div className="text-right">
            <Badge
              variant={
                riskLevel === 'critical' ? 'danger' :
                riskLevel === 'high' ? 'danger' :
                riskLevel === 'moderate' ? 'warning' :
                'success'
              }
              className="text-xs"
            >
              {riskLevel.toUpperCase()}
            </Badge>
            {worker.active_alerts && worker.active_alerts > 0 && (
              <div className="text-xs text-red-500 mt-1">
                {worker.active_alerts} alert{worker.active_alerts > 1 ? 's' : ''}
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Worker Info */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div>
            <span className="text-muted-foreground">Location:</span>
            <div className="font-medium">{worker.assigned_location}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Shift:</span>
            <div className="font-medium">{worker.shift_pattern.split(' ')[0]}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Age:</span>
            <div className="font-medium">{worker.age}</div>
          </div>
          <div>
            <span className="text-muted-foreground">Tolerance:</span>
            <div className="font-medium capitalize">{worker.heat_tolerance}</div>
          </div>
        </div>

        {/* Latest Biometric Data */}
        {latestReading && (
          <div className="space-y-3 pt-3 border-t">
            <div className="text-xs text-muted-foreground">
              Latest Reading: {formatTime(latestReading.timestamp)}
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="flex items-center space-x-2">
                <Heart className="h-3 w-3 text-red-500" />
                <div className="text-xs">
                  <div className="font-medium">{latestReading.HeartRate.toFixed(0)} bpm</div>
                  <div className="text-muted-foreground">Heart Rate</div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Thermometer className="h-3 w-3 text-orange-500" />
                <div className="text-xs">
                  <div className="font-medium">{latestReading.CoreBodyTemperature.toFixed(1)}°C</div>
                  <div className="text-muted-foreground">Body Temp</div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Thermometer className="h-3 w-3 text-blue-500" />
                <div className="text-xs">
                  <div className="font-medium">{latestReading.Temperature.toFixed(1)}°C</div>
                  <div className="text-muted-foreground">Ambient</div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Droplets className="h-3 w-3 text-cyan-500" />
                <div className="text-xs">
                  <div className="font-medium">{(latestReading.HydrationLevel * 100).toFixed(0)}%</div>
                  <div className="text-muted-foreground">Hydration</div>
                </div>
              </div>
            </div>

            {/* Risk Indicators */}
            <div className="flex justify-between items-center pt-2 border-t">
              <div className="text-xs">
                <div className="text-muted-foreground">Activity Level</div>
                <div className="font-medium">{latestReading.ActivityLevel}/5</div>
              </div>
              <div className="text-xs text-right">
                <div className="text-muted-foreground">Humidity</div>
                <div className="font-medium">{latestReading.Humidity.toFixed(0)}%</div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-2 pt-3 border-t">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails?.(worker.id)}
            className="flex-1"
          >
            View Details
          </Button>
          {riskLevel === 'critical' || riskLevel === 'high' && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => onGenerateAlert?.(worker.id)}
            >
              Alert
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}