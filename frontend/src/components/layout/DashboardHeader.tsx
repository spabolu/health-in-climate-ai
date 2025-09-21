/**
 * HeatGuard Pro Dashboard Header
 * Main header with real-time status indicators
 */

'use client';

import { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useDashboardMetrics, useHealthAlerts } from '@/hooks/use-thermal-comfort';
import {
  AlertTriangle,
  Shield,
  Users,
  Thermometer,
  Activity,
  Settings,
  Bell,
  RefreshCw,
  Wifi,
  WifiOff,
} from 'lucide-react';

export default function DashboardHeader() {
  const { metrics, isLoading, isRefreshing, error } = useDashboardMetrics();
  const { criticalAlerts, unacknowledgedAlerts } = useHealthAlerts();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'reconnecting'>('connected');

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Simulate connection status for demo
  useEffect(() => {
    const checkConnection = () => {
      // In a real app, this would check actual API connectivity
      if (error) {
        setConnectionStatus('disconnected');
      } else if (isRefreshing) {
        setConnectionStatus('reconnecting');
      } else {
        setConnectionStatus('connected');
      }
    };

    checkConnection();
  }, [error, isRefreshing]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500';
      case 'reconnecting':
        return 'bg-yellow-500';
      case 'disconnected':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="sticky top-0 z-50 w-full border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      {/* Critical Alerts Banner */}
      {criticalAlerts.length > 0 && (
        <Alert className="border-red-200 bg-red-50 text-red-900 rounded-none border-b">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription className="font-medium">
            <span className="font-semibold">{criticalAlerts.length} Critical Alert{criticalAlerts.length !== 1 ? 's' : ''}</span>
            {' - '}Immediate attention required for worker safety
          </AlertDescription>
        </Alert>
      )}

      <div className="flex h-16 items-center justify-between px-6">
        {/* Logo and Title */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
              <Shield className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gray-900">HeatGuard Pro</h1>
          </div>

          <Badge variant="secondary" className="hidden md:inline-flex">
            Workforce Safety Platform
          </Badge>
        </div>

        {/* Real-time Status Indicators */}
        <div className="flex items-center space-x-4">
          {/* Key Metrics */}
          {!isLoading && metrics && (
            <div className="hidden lg:flex items-center space-x-6">
              <Card className="p-2 bg-gray-50">
                <div className="flex items-center space-x-2 text-sm">
                  <Users className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">{metrics.active_workers ?? 0}/{metrics.total_workers ?? 0}</span>
                  <span className="text-gray-600">Active</span>
                </div>
              </Card>

              <Card className="p-2 bg-gray-50">
                <div className="flex items-center space-x-2 text-sm">
                  <Thermometer className="h-4 w-4 text-orange-600" />
                  <span className="font-medium">{metrics.average_temperature?.toFixed(1) ?? '--'}°C</span>
                  <span className="text-gray-600">Avg Temp</span>
                </div>
              </Card>

              {(metrics.workers_at_risk ?? 0) > 0 && (
                <Card className="p-2 bg-yellow-50 border-yellow-200">
                  <div className="flex items-center space-x-2 text-sm">
                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                    <span className="font-medium text-yellow-800">{metrics.workers_at_risk ?? 0}</span>
                    <span className="text-yellow-700">At Risk</span>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            <div className={`h-2 w-2 rounded-full ${getStatusColor(connectionStatus)} animate-pulse`} />
            {connectionStatus === 'connected' ? (
              <Wifi className="h-4 w-4 text-green-600" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-600" />
            )}
            <span className="hidden sm:block text-xs text-gray-600 capitalize">
              {connectionStatus}
            </span>
          </div>

          {/* Notifications */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-4 w-4" />
                {unacknowledgedAlerts.length > 0 && (
                  <Badge
                    variant="destructive"
                    className="absolute -top-2 -right-2 h-5 w-5 p-0 text-xs"
                  >
                    {unacknowledgedAlerts.length > 9 ? '9+' : unacknowledgedAlerts.length}
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-80">
              {unacknowledgedAlerts.length === 0 ? (
                <DropdownMenuItem disabled>
                  No new notifications
                </DropdownMenuItem>
              ) : (
                <>
                  {unacknowledgedAlerts.slice(0, 5).map(alert => (
                    <DropdownMenuItem key={alert.id} className="flex flex-col items-start p-3">
                      <div className="flex items-center space-x-2 w-full">
                        <AlertTriangle className={`h-4 w-4 ${
                          alert.severity === 'critical' ? 'text-red-500' :
                          alert.severity === 'high' ? 'text-orange-500' :
                          alert.severity === 'moderate' ? 'text-yellow-500' : 'text-blue-500'
                        }`} />
                        <Badge variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}>
                          {alert.severity}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium mt-1">{alert.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{alert.location}</p>
                    </DropdownMenuItem>
                  ))}
                  {unacknowledgedAlerts.length > 5 && (
                    <DropdownMenuItem className="text-center text-blue-600">
                      View {unacknowledgedAlerts.length - 5} more notifications
                    </DropdownMenuItem>
                  )}
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Refresh Button */}
          <Button variant="ghost" size="sm" disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>

          {/* Settings Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Activity className="mr-2 h-4 w-4" />
                System Health
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Users className="mr-2 h-4 w-4" />
                User Management
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                Configuration
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Current Time */}
          <div className="hidden md:block text-right">
            <div className="text-sm font-medium text-gray-900">
              {formatTime(currentTime)}
            </div>
            <div className="text-xs text-gray-500">
              {formatDate(currentTime)}
            </div>
          </div>
        </div>
      </div>

      {/* Loading Bar */}
      {(isLoading || isRefreshing) && (
        <div className="h-0.5 bg-gradient-to-r from-blue-500 to-green-500 animate-pulse" />
      )}
    </div>
  );
}