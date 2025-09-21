/**
 * HeatGuard Pro Alert Notifications
 * Toast notification system for real-time alerts
 */
/* eslint-disable no-console */

'use client';

import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { HealthAlert } from '@/types/thermal-comfort';
import {
  AlertTriangle,
  Bell,
  CheckCircle,
  Phone,
  Eye,
  MapPin,
  Clock,
} from 'lucide-react';

interface AlertNotificationsProps {
  alerts: HealthAlert[];
  onAcknowledge?: (alertId: string) => void;
  onViewWorker?: (workerId: string) => void;
  onEmergencyContact?: (workerId: string) => void;
  enableSound?: boolean;
  maxToasts?: number;
}

const severityConfig = {
  low: {
    icon: Bell,
    duration: 4000,
    className: 'border-blue-200 bg-blue-50',
  },
  moderate: {
    icon: Bell,
    duration: 6000,
    className: 'border-yellow-200 bg-yellow-50',
  },
  high: {
    icon: AlertTriangle,
    duration: 8000,
    className: 'border-orange-200 bg-orange-50',
  },
  critical: {
    icon: AlertTriangle,
    duration: 0, // Never auto-dismiss critical alerts
    className: 'border-red-200 bg-red-50',
  },
};

export default function AlertNotifications({
  alerts,
  onAcknowledge,
  onViewWorker,
  onEmergencyContact,
  enableSound = true,
  maxToasts = 5,
}: AlertNotificationsProps) {
  const previousAlertsRef = useRef<Set<string>>(new Set());
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize audio for notifications (in production, you'd use actual audio files)
  useEffect(() => {
    if (enableSound && typeof window !== 'undefined') {
      // audioRef.current = new Audio('/notification-sound.mp3');
      // In this demo, we'll just use browser's built-in beep or console log
    }
  }, [enableSound]);

  // Monitor for new alerts and show notifications
  useEffect(() => {
    const currentAlertIds = new Set(alerts.map(alert => alert.id));
    const newAlerts = alerts.filter(
      alert => !previousAlertsRef.current.has(alert.id) && !alert.acknowledged
    );

    // Show notifications for new alerts
    newAlerts.forEach(alert => {
      showAlertNotification(alert);
    });

    // Update the ref with current alert IDs
    previousAlertsRef.current = currentAlertIds;
  }, [alerts]);

  const playNotificationSound = (severity: HealthAlert['severity']) => {
    if (!enableSound) return;

    // In a real app, you'd play different sounds for different severities
    if (severity === 'critical') {
      console.log('🚨 CRITICAL ALERT SOUND');
      // Multiple beeps or urgent sound
    } else if (severity === 'high') {
      console.log('⚠️ HIGH PRIORITY SOUND');
      // Single urgent beep
    } else {
      console.log('🔔 NOTIFICATION SOUND');
      // Gentle notification sound
    }
  };

  const showAlertNotification = (alert: HealthAlert) => {
    const config = severityConfig[alert.severity];
    const Icon = config.icon;

    playNotificationSound(alert.severity);

    const formatTime = (timestamp: string) => {
      return new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const getAlertTypeLabel = (type: string) => {
      const labels: Record<string, string> = {
        heat_exhaustion_risk: 'Heat Exhaustion Risk',
        dehydration_warning: 'Dehydration Warning',
        heart_rate_anomaly: 'Heart Rate Anomaly',
        critical_temperature: 'Critical Temperature',
      };
      return labels[type] || type.replace('_', ' ');
    };

    // Create custom toast content
    const toastContent = (
      <div className={`p-2 rounded-lg border ${config.className}`}>
        <div className="flex items-start space-x-3">
          <div className={`
            p-2 rounded-full mt-1
            ${alert.severity === 'critical' ? 'bg-red-600 animate-pulse' :
              alert.severity === 'high' ? 'bg-orange-600' :
              alert.severity === 'moderate' ? 'bg-yellow-600' : 'bg-blue-600'}
          `}>
            <Icon className="h-4 w-4 text-white" />
          </div>

          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center space-x-2 mb-2">
              <Badge
                variant={alert.severity === 'critical' ? 'destructive' : 'secondary'}
                className="text-xs"
              >
                {alert.severity.toUpperCase()}
              </Badge>
              <span className="font-semibold text-gray-900 text-sm">
                {getAlertTypeLabel(alert.alert_type)}
              </span>
            </div>

            {/* Message */}
            <p className="text-sm text-gray-800 mb-3 line-clamp-2">
              {alert.message}
            </p>

            {/* Metadata */}
            <div className="flex items-center space-x-4 text-xs text-gray-600 mb-3">
              <div className="flex items-center space-x-1">
                <MapPin className="h-3 w-3" />
                <span>{alert.location}</span>
              </div>
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{formatTime(alert.timestamp)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs"
                onClick={() => onAcknowledge?.(alert.id)}
              >
                <CheckCircle className="h-3 w-3 mr-1" />
                Acknowledge
              </Button>

              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs"
                onClick={() => onViewWorker?.(alert.worker_id)}
              >
                <Eye className="h-3 w-3 mr-1" />
                View Worker
              </Button>

              {alert.severity === 'critical' && (
                <Button
                  size="sm"
                  variant="destructive"
                  className="h-7 text-xs"
                  onClick={() => onEmergencyContact?.(alert.worker_id)}
                >
                  <Phone className="h-3 w-3 mr-1" />
                  Emergency
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    );

    // Show toast with appropriate duration and styling
    if (alert.severity === 'critical') {
      toast(toastContent, {
        duration: Infinity, // Critical alerts don't auto-dismiss
        id: alert.id,
        className: 'border-red-500',
        position: 'top-center',
      });
    } else {
      toast(toastContent, {
        duration: config.duration,
        id: alert.id,
        position: 'top-right',
      });
    }
  };

  // Component doesn't render anything visible, just manages notifications
  return null;
}

/**
 * Alert Summary Notification
 * Shows a summary when multiple alerts are triggered simultaneously
 */
interface AlertSummaryNotificationProps {
  newAlertCount: number;
  criticalCount: number;
  onViewAlerts: () => void;
}

export function AlertSummaryNotification({
  newAlertCount,
  criticalCount,
  onViewAlerts,
}: AlertSummaryNotificationProps) {
  useEffect(() => {
    if (newAlertCount <= 1) return; // Don't show summary for single alerts

    const summaryContent = (
      <div className="p-3 border border-orange-200 bg-orange-50 rounded-lg">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-full bg-orange-600">
            <AlertTriangle className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <Badge variant="secondary">MULTIPLE ALERTS</Badge>
              {criticalCount > 0 && (
                <Badge variant="destructive">{criticalCount} CRITICAL</Badge>
              )}
            </div>
            <p className="text-sm text-gray-900 font-medium">
              {newAlertCount} new alerts require attention
            </p>
            <Button
              size="sm"
              className="mt-2 h-7 text-xs"
              onClick={onViewAlerts}
            >
              View All Alerts
            </Button>
          </div>
        </div>
      </div>
    );

    toast(summaryContent, {
      duration: 8000,
      position: 'top-center',
      id: 'alert-summary',
    });
  }, [newAlertCount, criticalCount, onViewAlerts]);

  return null;
}

/**
 * Notification Settings
 * Allows users to customize notification preferences
 */
export interface NotificationSettings {
  enableSound: boolean;
  enableDesktopNotifications: boolean;
  criticalAlertsOnly: boolean;
  maxToasts: number;
  autoAcknowledgeAfter: number; // minutes
}

export const defaultNotificationSettings: NotificationSettings = {
  enableSound: true,
  enableDesktopNotifications: true,
  criticalAlertsOnly: false,
  maxToasts: 5,
  autoAcknowledgeAfter: 30,
};

/**
 * Browser Notification Manager
 * Handles browser push notifications for when the app is not in focus
 */
export class BrowserNotificationManager {
  private static instance: BrowserNotificationManager;
  private permission: NotificationPermission = 'default';

  private constructor() {
    if (typeof window !== 'undefined' && 'Notification' in window) {
      this.permission = Notification.permission;
    }
  }

  public static getInstance(): BrowserNotificationManager {
    if (!BrowserNotificationManager.instance) {
      BrowserNotificationManager.instance = new BrowserNotificationManager();
    }
    return BrowserNotificationManager.instance;
  }

  public async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support desktop notifications');
      return false;
    }

    if (this.permission === 'default') {
      this.permission = await Notification.requestPermission();
    }

    return this.permission === 'granted';
  }

  public showNotification(alert: HealthAlert): void {
    if (this.permission !== 'granted') return;

    const options: NotificationOptions = {
      body: alert.message,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: alert.id,
      requireInteraction: alert.severity === 'critical',
      data: {
        alertId: alert.id,
        workerId: alert.worker_id,
        severity: alert.severity,
      },
    };

    const notification = new Notification(
      `HeatGuard Pro - ${alert.severity.toUpperCase()} Alert`,
      options
    );

    notification.onclick = () => {
      window.focus();
      notification.close();
    };

    // Auto-close non-critical notifications after 10 seconds
    if (alert.severity !== 'critical') {
      setTimeout(() => notification.close(), 10000);
    }
  }
}