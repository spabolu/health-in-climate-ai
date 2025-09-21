'use client'

import React, { useState, useEffect } from 'react'
import {
  Shield,
  Users,
  AlertTriangle,
  Thermometer,
  Wind,
  Activity,
  Clock,
  CheckCircle,
  Droplets,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { DashboardMetrics, Alert } from '@/types'

// --- Helpers mapped to shadcn Badge variants ---
type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline'

const getRiskLevelBadge: (level: string) => BadgeVariant = (level) => {
  switch (level.toLowerCase()) {
    case 'low':
      return 'default'
    case 'moderate':
      return 'secondary'
    case 'high':
      return 'destructive'
    case 'critical':
      return 'destructive'
    default:
      return 'outline'
  }
}

const getSeverityBadge: (severity: string) => BadgeVariant = (severity) => {
  switch (severity.toLowerCase()) {
    case 'critical':
    case 'high':
      return 'destructive'
    case 'moderate':
      return 'secondary'
    case 'low':
      return 'default'
    default:
      return 'outline'
  }
}

// --- Mock data for development (replace with API) ---
const mockDashboardMetrics: DashboardMetrics = {
  active_workers: 87,
  total_workers: 100,
  critical_alerts: 3,
  unacknowledged_alerts: 7,
  average_risk_level: 2.1,
  environmental_conditions: {
    temperature: 28.5,
    humidity: 65.2,
    air_quality_index: 82,
    wind_speed: 1.3,
  },
  recent_readings_count: 245,
  risk_distribution: {
    comfortable: 45,
    slightly_uncomfortable: 28,
    uncomfortable: 12,
    very_uncomfortable: 2,
  },
  location_metrics: {
    'Factory Floor A': { workers_count: 25, active_alerts: 2, risk_level: 'moderate' },
    'Factory Floor B': { workers_count: 22, active_alerts: 1, risk_level: 'low' },
    Warehouse: { workers_count: 18, active_alerts: 3, risk_level: 'high' },
    'Loading Dock': { workers_count: 15, active_alerts: 1, risk_level: 'moderate' },
    'Office Area': { workers_count: 7, active_alerts: 0, risk_level: 'low' },
  },
  timestamp: new Date().toISOString(),
  system_status: 'operational',
  model_accuracy: 0.927,
  data_quality_score: 0.92,
  compliance_score: 0.952,
}

const mockRecentAlerts: Alert[] = [
  {
    id: '1',
    worker_id: 'worker_001',
    worker_name: 'John Smith',
    alert_type: 'heat_exhaustion_risk',
    severity: 'critical',
    message: 'Critical heat risk detected - immediate attention required',
    recommended_actions: ['Move to cooler area', 'Provide water', 'Monitor vital signs'],
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    acknowledged: false,
    resolved: false,
    location: 'Factory Floor A',
  },
  {
    id: '2',
    worker_id: 'worker_045',
    worker_name: 'Maria Garcia',
    alert_type: 'dehydration_warning',
    severity: 'high',
    message: 'Dehydration warning - worker needs hydration break',
    recommended_actions: ['Provide water', 'Schedule break'],
    timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
    acknowledged: true,
    resolved: false,
    location: 'Warehouse',
  },
]

export function AegisDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics>(mockDashboardMetrics)
  const [alerts, setAlerts] = useState<Alert[]>(mockRecentAlerts)
  const [loading, setLoading] = useState(false)

  // TODO: Replace with actual API calls
  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 600))
      setMetrics(mockDashboardMetrics)
      setAlerts(mockRecentAlerts)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
    const interval = setInterval(fetchDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Shield className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Aegis AI</h1>
                <p className="text-sm text-muted-foreground">Heat Exposure Monitoring System</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="default" className="flex items-center space-x-1">
                <CheckCircle className="h-3 w-3" />
                <span>{metrics.system_status.toUpperCase()}</span>
              </Badge>
              <div className="text-sm text-muted-foreground">
                Last updated: {new Date(metrics.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 container mx-auto px-6 py-6 space-y-6">
        {/* Loading state */}
        {loading && (
          <div className="text-sm text-muted-foreground">Refreshing metrics…</div>
        )}

        {/* Key Metrics Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Workers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.active_workers}</div>
              <p className="text-xs text-muted-foreground">
                of {metrics.total_workers} total workers
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{metrics.critical_alerts}</div>
              <p className="text-xs text-muted-foreground">
                {metrics.unacknowledged_alerts} unacknowledged
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Risk</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.average_risk_level.toFixed(1)}</div>
              <p className="text-xs text-muted-foreground">Scale 1-4 (Low to Critical)</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Recent Readings</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.recent_readings_count}</div>
              <p className="text-xs text-muted-foreground">In the last hour</p>
            </CardContent>
          </Card>
        </div>

        {/* Environmental Conditions & Risk Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Thermometer className="h-5 w-5" />
                <span>Environmental Conditions</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <Thermometer className="h-4 w-4 text-orange-500" />
                  <div>
                    <p className="text-2xl font-bold">
                      {metrics.environmental_conditions.temperature}°C
                    </p>
                    <p className="text-xs text-muted-foreground">Temperature</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Droplets className="h-4 w-4 text-blue-500" />
                  <div>
                    <p className="text-2xl font-bold">
                      {metrics.environmental_conditions.humidity}%
                    </p>
                    <p className="text-xs text-muted-foreground">Humidity</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Wind className="h-4 w-4 text-green-500" />
                  <div>
                    <p className="text-2xl font-bold">
                      {metrics.environmental_conditions.wind_speed} m/s
                    </p>
                    <p className="text-xs text-muted-foreground">Wind Speed</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Activity className="h-4 w-4 text-purple-500" />
                  <div>
                    <p className="text-2xl font-bold">
                      {metrics.environmental_conditions.air_quality_index}
                    </p>
                    <p className="text-xs text-muted-foreground">Air Quality Index</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Risk Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(metrics.risk_distribution).map(([risk, count]) => (
                  <div key={risk} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          risk === 'comfortable'
                            ? 'bg-green-500'
                            : risk === 'slightly_uncomfortable'
                            ? 'bg-yellow-500'
                            : risk === 'uncomfortable'
                            ? 'bg-orange-500'
                            : 'bg-red-500'
                        }`}
                      />
                      <span className="capitalize text-sm">
                        {risk.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <Badge variant="outline">{count} workers</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Location Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Location Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
              {Object.entries(metrics.location_metrics).map(([location, data]) => (
                <div key={location} className="p-4 rounded-lg border bg-card/50">
                  <h3 className="font-semibold text-sm mb-2">{location}</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Workers:</span>
                      <span className="font-medium">{data.workers_count}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Alerts:</span>
                      <Badge
                        variant={
                          data.active_alerts > 2
                            ? 'destructive'
                            : data.active_alerts > 0
                            ? 'secondary'
                            : 'default'
                        }
                        className="text-xs"
                      >
                        {data.active_alerts}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Risk Level:</span>
                      <Badge variant={getRiskLevelBadge(data.risk_level)} className="text-xs capitalize">
                        {data.risk_level}
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Recent Alerts</span>
              <Button variant="outline" size="sm">
                View All
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {alerts.map((alert) => (
                <div key={alert.id} className="flex items-start space-x-4 p-4 rounded-lg border bg-card/50">
                  <div className="flex-shrink-0">
                    {alert.acknowledged ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertTriangle
                        className={`h-5 w-5 ${
                          alert.severity === 'critical'
                            ? 'text-red-500'
                            : alert.severity === 'high'
                            ? 'text-orange-500'
                            : 'text-yellow-500'
                        }`}
                      />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="text-sm font-semibold">{alert.worker_name}</h4>
                      <div className="flex items-center space-x-2">
                        <Badge variant={getSeverityBadge(alert.severity)} className="text-xs">
                          {alert.severity.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{alert.message}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-muted-foreground">{alert.location}</span>
                      <div className="flex space-x-2">
                        {!alert.acknowledged && (
                          <Button variant="outline" size="sm">
                            Acknowledge
                          </Button>
                        )}
                        {!alert.resolved && (
                          <Button variant="outline" size="sm">
                            Resolve
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Health Footer */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-6">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span>Model Accuracy: {(metrics.model_accuracy * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  <span>Data Quality: {(metrics.data_quality_score * 100).toFixed(0)}%</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" />
                  <span>OSHA Compliance: {(metrics.compliance_score * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="text-muted-foreground">
                Protecting {metrics.total_workers} workers across {Object.keys(metrics.location_metrics).length} locations
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

export default AegisDashboard
