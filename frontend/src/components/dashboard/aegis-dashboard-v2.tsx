'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { Alert, DashboardMetrics } from '@/types'
import {
  Activity,
  AlertTriangle,
  Bell,
  Calendar,
  CheckCircle,
  Clock,
  Droplets,
  Monitor,
  Shield,
  Thermometer,
  Users,
  Wind
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { AlertCenter } from '../alerts/alert-center'
import { NotificationSystem } from '../alerts/notification-system'
import { ComplianceDashboard } from '../compliance/compliance-dashboard'
import { ShiftScheduler } from '../scheduling/shift-scheduler'
import { RealTimeMonitor } from './real-time-monitor'

// Mock data for development - will be replaced with API calls
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
    wind_speed: 1.3
  },
  recent_readings_count: 245,
  risk_distribution: {
    'comfortable': 45,
    'slightly_uncomfortable': 28,
    'uncomfortable': 12,
    'very_uncomfortable': 2
  },
  location_metrics: {
    'Factory Floor A': { workers_count: 25, active_alerts: 2, risk_level: 'moderate' },
    'Factory Floor B': { workers_count: 22, active_alerts: 1, risk_level: 'low' },
    'Warehouse': { workers_count: 18, active_alerts: 3, risk_level: 'high' },
    'Loading Dock': { workers_count: 15, active_alerts: 1, risk_level: 'moderate' },
    'Office Area': { workers_count: 7, active_alerts: 0, risk_level: 'low' }
  },
  timestamp: new Date().toISOString(),
  system_status: 'operational',
  model_accuracy: 0.87,
  data_quality_score: 0.92,
  compliance_score: 0.95
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
    location: 'Factory Floor A'
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
    location: 'Warehouse'
  }
]

export function AegisDashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics>(mockDashboardMetrics)
  const [alerts, setAlerts] = useState<Alert[]>(mockRecentAlerts)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'realtime' | 'alerts' | 'compliance' | 'scheduling'>('overview')

  // TODO: Replace with actual API calls
  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // For now, we'll simulate loading with mock data
      await new Promise(resolve => setTimeout(resolve, 1000))
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
    // Refresh every 30 seconds for real-time updates
    const interval = setInterval(fetchDashboardData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low': return 'success'
      case 'moderate': return 'warning'
      case 'high': return 'danger'
      default: return 'secondary'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'danger'
      case 'high': return 'danger'
      case 'moderate': return 'warning'
      case 'low': return 'success'
      default: return 'secondary'
    }
  }

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
              <NotificationSystem
                alerts={alerts}
                onAlertUpdate={setAlerts}
              />
              <Badge variant="success" className="flex items-center space-x-1">
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
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-muted p-1 rounded-lg w-fit">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'overview'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Activity className="h-4 w-4 inline-block mr-2" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('realtime')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'realtime'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Monitor className="h-4 w-4 inline-block mr-2" />
            Real-Time Monitor
          </button>
          <button
            onClick={() => setActiveTab('alerts')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'alerts'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Bell className="h-4 w-4 inline-block mr-2" />
            Alert Center
            {/* {alerts.filter(a => !a.acknowledged && !a.resolved).length > 0 && (
              <Badge variant="destructive" className="ml-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
                {alerts.filter(a => !a.acknowledged && !a.resolved).length}
              </Badge>
            )} */}
          </button>
          <button
            onClick={() => setActiveTab('compliance')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'compliance'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Shield className="h-4 w-4 inline-block mr-2" />
            Compliance
          </button>
          <button
            onClick={() => setActiveTab('scheduling')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'scheduling'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <Calendar className="h-4 w-4 inline-block mr-2" />
            Scheduling
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <>
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
                  <p className="text-xs text-muted-foreground">
                    Scale 1-4 (Low to Critical)
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Recent Readings</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{metrics.recent_readings_count}</div>
                  <p className="text-xs text-muted-foreground">
                    In the last hour
                  </p>
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
                        <p className="text-2xl font-bold">{metrics.environmental_conditions.temperature}°C</p>
                        <p className="text-xs text-muted-foreground">Temperature</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Droplets className="h-4 w-4 text-blue-500" />
                      <div>
                        <p className="text-2xl font-bold">{metrics.environmental_conditions.humidity}%</p>
                        <p className="text-xs text-muted-foreground">Humidity</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Wind className="h-4 w-4 text-green-500" />
                      <div>
                        <p className="text-2xl font-bold">{metrics.environmental_conditions.wind_speed} m/s</p>
                        <p className="text-xs text-muted-foreground">Wind Speed</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Activity className="h-4 w-4 text-purple-500" />
                      <div>
                        <p className="text-2xl font-bold">{metrics.environmental_conditions.air_quality_index}</p>
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
                          <div className={`w-3 h-3 rounded-full ${
                            risk === 'comfortable' ? 'bg-green-500' :
                            risk === 'slightly_uncomfortable' ? 'bg-yellow-500' :
                            risk === 'uncomfortable' ? 'bg-orange-500' :
                            'bg-red-500'
                          }`} />
                          <span className="capitalize text-sm">{risk.replace('_', ' ')}</span>
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
                          <Badge variant={data.active_alerts > 2 ? 'danger' : data.active_alerts > 0 ? 'warning' : 'success'} className="text-xs">
                            {data.active_alerts}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>Risk Level:</span>
                          <Badge variant={getRiskLevelColor(data.risk_level) as 'success' | 'warning' | 'danger' | 'secondary'} className="text-xs capitalize">
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
                  <Button variant="outline" size="sm">View All</Button>
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
                          <AlertTriangle className={`h-5 w-5 ${
                            alert.severity === 'critical' ? 'text-red-500' :
                            alert.severity === 'high' ? 'text-orange-500' :
                            'text-yellow-500'
                          }`} />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-semibold">{alert.worker_name}</h4>
                          <div className="flex items-center space-x-2">
                            <Badge variant={getSeverityColor(alert.severity) as 'success' | 'warning' | 'danger' | 'secondary'} className="text-xs">
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
                              <Button variant="outline" size="sm">Acknowledge</Button>
                            )}
                            {!alert.resolved && (
                              <Button variant="outline" size="sm">Resolve</Button>
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
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Model Accuracy: {(metrics.model_accuracy * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>Data Quality: {(metrics.data_quality_score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>OSHA Compliance: {(metrics.compliance_score * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="text-muted-foreground">
                    Protecting {metrics.total_workers} workers across {Object.keys(metrics.location_metrics).length} locations
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {activeTab === 'realtime' && (
          <RealTimeMonitor />
        )}

        {activeTab === 'alerts' && (
          <AlertCenter />
        )}

        {activeTab === 'compliance' && (
          <ComplianceDashboard />
        )}

        {activeTab === 'scheduling' && (
          <ShiftScheduler />
        )}
      </main>
    </div>
  )
}