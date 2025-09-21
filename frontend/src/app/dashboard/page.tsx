/**
 * HeatGuard Pro Main Dashboard Page
 * Real-time workforce safety monitoring dashboard
 */

'use client';

import { useDashboardMetrics, useHealthAlerts } from '@/hooks/use-thermal-comfort';
import DashboardLayout, {
  DashboardPageContainer,
  DashboardGrid,
  DashboardWidget,
  DashboardMetricsRow,
  MetricCard,
} from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Users,
  Thermometer,
  AlertTriangle,
  Shield,
  Activity,
  TrendingUp,
  Clock,
  MapPin,
  RefreshCw,
  Settings,
} from 'lucide-react';

export default function DashboardPage() {
  const { metrics, isLoading, error } = useDashboardMetrics();
  const { alerts, criticalAlerts, unacknowledgedAlerts } = useHealthAlerts();

  return (
    <DashboardLayout>
      <DashboardPageContainer
        title="Live Monitoring Dashboard"
        description="Real-time worker safety and thermal comfort monitoring"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Live Monitoring' },
        ]}
        actions={
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm">
              <Shield className="h-4 w-4 mr-2" />
              Emergency Mode
            </Button>
          </div>
        }
      >
        {/* Key Metrics Row */}
        <DashboardMetricsRow>
          <MetricCard
            title="Active Workers"
            value={metrics?.active_workers || 0}
            change={{
              value: 5,
              type: 'increase',
              period: 'last hour',
            }}
            icon={<Users className="h-6 w-6" />}
            color="blue"
          />
          <MetricCard
            title="Average Temperature"
            value={`${metrics?.average_temperature?.toFixed(1) || '--'}°C`}
            change={{
              value: 2.3,
              type: 'increase',
              period: 'last hour',
            }}
            icon={<Thermometer className="h-6 w-6" />}
            color="yellow"
          />
          <MetricCard
            title="Workers at Risk"
            value={metrics?.workers_at_risk || 0}
            change={{
              value: 1,
              type: 'decrease',
              period: 'last hour',
            }}
            icon={<AlertTriangle className="h-6 w-6" />}
            color={metrics?.workers_at_risk ? 'red' : 'green'}
          />
          <MetricCard
            title="Compliance Score"
            value={`${metrics?.compliance_score || 0}%`}
            change={{
              value: 0.5,
              type: 'increase',
              period: 'last week',
            }}
            icon={<Shield className="h-6 w-6" />}
            color="green"
          />
        </DashboardMetricsRow>

        {/* Main Dashboard Grid */}
        <DashboardGrid>
          {/* Critical Alerts Widget */}
          <DashboardWidget
            title="Critical Alerts"
            description="Immediate attention required"
            colSpan={2}
            loading={isLoading}
            error={error}
          >
            <div className="space-y-3">
              {criticalAlerts.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="h-12 w-12 text-green-500 mx-auto mb-3" />
                  <p className="text-gray-600">No critical alerts</p>
                  <p className="text-sm text-gray-500">All workers are safe</p>
                </div>
              ) : (
                criticalAlerts.slice(0, 3).map(alert => (
                  <div key={alert.id} className="flex items-start space-x-3 p-3 bg-red-50 rounded-lg border border-red-200">
                    <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <Badge variant="destructive">{alert.severity}</Badge>
                        <span className="text-xs text-gray-500">
                          {new Date(alert.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="font-medium text-gray-900 mt-1">{alert.message}</p>
                      <p className="text-sm text-gray-600">{alert.location}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </DashboardWidget>

          {/* Worker Status Overview */}
          <DashboardWidget
            title="Worker Status"
            description="Current workforce overview"
            loading={isLoading}
            error={error}
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Workers</span>
                <span className="font-semibold">{metrics?.total_workers || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active</span>
                <span className="font-semibold text-green-600">{metrics?.active_workers || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">At Risk</span>
                <span className="font-semibold text-red-600">{metrics?.workers_at_risk || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Off Duty</span>
                <span className="font-semibold text-gray-500">
                  {(metrics?.total_workers || 0) - (metrics?.active_workers || 0)}
                </span>
              </div>
            </div>
          </DashboardWidget>

          {/* Environmental Conditions */}
          <DashboardWidget
            title="Environmental Conditions"
            description="Current site conditions"
            loading={isLoading}
            error={error}
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Thermometer className="h-4 w-4 text-orange-500" />
                  <span className="text-sm text-gray-600">Temperature</span>
                </div>
                <span className="font-semibold">{metrics?.average_temperature?.toFixed(1) || '--'}°C</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="h-4 w-4 text-blue-500" />
                  <span className="text-sm text-gray-600">Humidity</span>
                </div>
                <span className="font-semibold">{metrics?.average_humidity?.toFixed(0) || '--'}%</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-600">Last Update</span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date().toLocaleTimeString()}
                </span>
              </div>
            </div>
          </DashboardWidget>

          {/* Recent Activity */}
          <DashboardWidget
            title="Recent Activity"
            description="Latest system events"
            colSpan={2}
            loading={isLoading}
            error={error}
          >
            <div className="space-y-3">
              {unacknowledgedAlerts.slice(0, 5).map(alert => (
                <div key={alert.id} className="flex items-start space-x-3 p-2 hover:bg-gray-50 rounded">
                  <div className="flex-shrink-0">
                    <div className={`h-2 w-2 rounded-full mt-2 ${
                      alert.severity === 'critical' ? 'bg-red-500' :
                      alert.severity === 'high' ? 'bg-orange-500' :
                      alert.severity === 'moderate' ? 'bg-yellow-500' : 'bg-blue-500'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-900">{alert.alert_type.replace('_', ' ')}</span>
                      <span className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <MapPin className="h-3 w-3 text-gray-400" />
                      <span className="text-xs text-gray-500">{alert.location}</span>
                    </div>
                  </div>
                </div>
              ))}
              {unacknowledgedAlerts.length === 0 && (
                <div className="text-center py-4">
                  <Activity className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">No recent activity</p>
                </div>
              )}
            </div>
          </DashboardWidget>

          {/* Performance Metrics */}
          <DashboardWidget
            title="Today's Performance"
            description="Daily safety metrics"
            loading={isLoading}
            error={error}
          >
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Incidents Today</span>
                <span className="font-semibold text-red-600">{metrics?.incidents_today || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Safety Score</span>
                <span className="font-semibold text-green-600">{metrics?.compliance_score || 0}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Avg Response Time</span>
                <span className="font-semibold">2.3 min</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Uptime</span>
                <span className="font-semibold text-green-600">99.8%</span>
              </div>
            </div>
          </DashboardWidget>

          {/* Quick Actions */}
          <DashboardWidget
            title="Quick Actions"
            description="Emergency and common tasks"
          >
            <div className="space-y-2">
              <Button className="w-full justify-start" variant="outline" size="sm">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Emergency Alert
              </Button>
              <Button className="w-full justify-start" variant="outline" size="sm">
                <Users className="h-4 w-4 mr-2" />
                Add Worker
              </Button>
              <Button className="w-full justify-start" variant="outline" size="sm">
                <TrendingUp className="h-4 w-4 mr-2" />
                Generate Report
              </Button>
              <Button className="w-full justify-start" variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                System Settings
              </Button>
            </div>
          </DashboardWidget>
        </DashboardGrid>
      </DashboardPageContainer>
    </DashboardLayout>
  );
}