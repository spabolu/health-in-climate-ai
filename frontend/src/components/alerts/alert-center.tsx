'use client'

import React, { useState, useEffect } from 'react'
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  RefreshCw,
  Users,
  MapPin,
  Calendar,
  TrendingUp,
  Download
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertNotification } from './alert-notification'
import type { Alert } from '@/types'

// Mock alerts data for demonstration
const mockAlerts: Alert[] = [
  {
    id: '1',
    worker_id: 'worker_001',
    worker_name: 'John Smith',
    alert_type: 'heat_exhaustion_risk',
    severity: 'critical',
    message: 'Critical heat risk detected - Core temperature 39.2°C, Heart rate 125bpm',
    recommended_actions: [
      'Move worker to cooler area immediately',
      'Provide water and electrolytes',
      'Monitor vital signs closely',
      'Consider medical attention'
    ],
    timestamp: new Date(Date.now() - 3 * 60000).toISOString(),
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
    message: 'Dehydration warning - Hydration level below 40%, increased skin conductance',
    recommended_actions: [
      'Provide immediate hydration break',
      'Offer electrolyte drink',
      'Monitor for 15 minutes'
    ],
    timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
    acknowledged: true,
    resolved: false,
    location: 'Warehouse'
  },
  {
    id: '3',
    worker_id: 'worker_023',
    worker_name: 'David Chen',
    alert_type: 'high_heart_rate',
    severity: 'moderate',
    message: 'Elevated heart rate detected - 110bpm for extended period',
    recommended_actions: [
      'Reduce work intensity',
      'Take rest break',
      'Provide water'
    ],
    timestamp: new Date(Date.now() - 25 * 60000).toISOString(),
    acknowledged: true,
    resolved: true,
    location: 'Loading Dock'
  },
  {
    id: '4',
    worker_id: 'worker_067',
    worker_name: 'Sarah Wilson',
    alert_type: 'temperature_spike',
    severity: 'high',
    message: 'Rapid temperature increase - Environmental temp rose to 36°C',
    recommended_actions: [
      'Activate cooling systems',
      'Relocate workers if possible',
      'Increase monitoring frequency'
    ],
    timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
    acknowledged: false,
    resolved: false,
    location: 'Factory Floor B'
  },
  {
    id: '5',
    worker_id: 'worker_089',
    worker_name: 'Michael Brown',
    alert_type: 'prolonged_exposure',
    severity: 'moderate',
    message: 'Prolonged heat exposure - 4 hours in high-risk conditions',
    recommended_actions: [
      'Schedule mandatory break',
      'Rotate to cooler area',
      'Assess heat tolerance'
    ],
    timestamp: new Date(Date.now() - 67 * 60000).toISOString(),
    acknowledged: true,
    resolved: false,
    location: 'Factory Floor A'
  }
]

type FilterType = 'all' | 'critical' | 'high' | 'moderate' | 'low'
type StatusFilter = 'all' | 'pending' | 'acknowledged' | 'resolved'

interface AlertCenterProps {
  className?: string
}

export function AlertCenter({ className }: AlertCenterProps) {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts)
  const [filteredAlerts, setFilteredAlerts] = useState<Alert[]>(mockAlerts)
  const [severityFilter, setSeverityFilter] = useState<FilterType>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [locationFilter, setLocationFilter] = useState<string>('all')
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Get unique locations for filtering
  const locations = Array.from(new Set(alerts.map(alert => alert.location)))

  // Apply filters
  useEffect(() => {
    let filtered = alerts

    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter)
    }

    if (statusFilter !== 'all') {
      if (statusFilter === 'pending') {
        filtered = filtered.filter(alert => !alert.acknowledged && !alert.resolved)
      } else if (statusFilter === 'acknowledged') {
        filtered = filtered.filter(alert => alert.acknowledged && !alert.resolved)
      } else if (statusFilter === 'resolved') {
        filtered = filtered.filter(alert => alert.resolved)
      }
    }

    if (locationFilter !== 'all') {
      filtered = filtered.filter(alert => alert.location === locationFilter)
    }

    // Sort by timestamp (newest first) and severity
    filtered.sort((a, b) => {
      const severityOrder = { critical: 4, high: 3, moderate: 2, low: 1 }
      const severityDiff = severityOrder[b.severity as keyof typeof severityOrder] -
                          severityOrder[a.severity as keyof typeof severityOrder]

      if (severityDiff !== 0) return severityDiff

      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    })

    setFilteredAlerts(filtered)
  }, [alerts, severityFilter, statusFilter, locationFilter])

  // Alert statistics
  const getAlertStats = () => {
    const total = alerts.length
    const critical = alerts.filter(a => a.severity === 'critical').length
    const pending = alerts.filter(a => !a.acknowledged && !a.resolved).length
    const resolved = alerts.filter(a => a.resolved).length

    return { total, critical, pending, resolved }
  }

  const stats = getAlertStats()

  const handleAcknowledge = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ))
  }

  const handleResolve = (alertId: string) => {
    setAlerts(prev => prev.map(alert =>
      alert.id === alertId ? { ...alert, resolved: true } : alert
    ))
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    // In real implementation, fetch fresh data from API
    setIsRefreshing(false)
  }

  const handleBulkAction = (action: 'acknowledge' | 'resolve') => {
    const targetAlerts = filteredAlerts.filter(alert => {
      if (action === 'acknowledge') return !alert.acknowledged
      if (action === 'resolve') return !alert.resolved
      return false
    })

    if (action === 'acknowledge') {
      setAlerts(prev => prev.map(alert =>
        targetAlerts.some(target => target.id === alert.id)
          ? { ...alert, acknowledged: true }
          : alert
      ))
    } else if (action === 'resolve') {
      setAlerts(prev => prev.map(alert =>
        targetAlerts.some(target => target.id === alert.id)
          ? { ...alert, resolved: true }
          : alert
      ))
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center space-x-2">
            <Bell className="h-6 w-6 text-primary" />
            <span>Alert Center</span>
          </h2>
          <p className="text-muted-foreground">
            Real-time safety alerts and incident management
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Alert Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Alerts</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <Bell className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-red-200 bg-red-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">Critical</p>
                <p className="text-2xl font-bold text-red-700">{stats.critical}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-700">{stats.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-200 bg-green-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Resolved</p>
                <p className="text-2xl font-bold text-green-700">{stats.resolved}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Actions */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center space-x-4">
              <div className="flex items-center space-x-2">
                <Filter className="h-4 w-4" />
                <span className="text-sm font-medium">Filters:</span>
              </div>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as FilterType)}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="moderate">Moderate</option>
                <option value="low">Low</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
              </select>

              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="text-sm border rounded px-2 py-1"
              >
                <option value="all">All Locations</option>
                {locations.map(location => (
                  <option key={location} value={location}>{location}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction('acknowledge')}
                disabled={!filteredAlerts.some(a => !a.acknowledged)}
              >
                Acknowledge All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleBulkAction('resolve')}
                disabled={!filteredAlerts.some(a => !a.resolved)}
              >
                Resolve All
              </Button>
            </div>
          </div>

          <div className="mt-4 text-sm text-muted-foreground">
            Showing {filteredAlerts.length} of {alerts.length} alerts
          </div>
        </CardContent>
      </Card>

      {/* Alert List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <CheckCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-muted-foreground mb-2">No alerts found</h3>
              <p className="text-muted-foreground">
                {alerts.length === 0
                  ? 'No alerts have been generated yet.'
                  : 'Try adjusting your filters to see more alerts.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredAlerts.map((alert) => (
            <AlertNotification
              key={alert.id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              showActions={true}
              compact={false}
            />
          ))
        )}
      </div>
    </div>
  )
}