/**
 * HeatGuard Pro Emergency Alert Component
 * Critical emergency alert display with immediate action buttons
 */

'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { HealthAlert } from '@/types/thermal-comfort';
import {
  AlertTriangle,
  Phone,
  MapPin,
  Clock,
  User,
  CheckCircle,
  X,
  Siren,
  Heart,
  Thermometer,
} from 'lucide-react';

interface EmergencyAlertProps {
  alert: HealthAlert;
  open: boolean;
  onClose: () => void;
  onAcknowledge: () => Promise<void>;
  onEmergencyContact: () => void;
  onViewWorker: () => void;
  workerData?: {
    name: string;
    heartRate?: number;
    temperature?: number;
    location: string;
    emergencyContact?: {
      name: string;
      phone: string;
    };
  };
  autoCloseDelay?: number; // Auto close after this many seconds if acknowledged
}

export default function EmergencyAlert({
  alert,
  open,
  onClose,
  onAcknowledge,
  onEmergencyContact,
  onViewWorker,
  workerData,
  autoCloseDelay = 10,
}: EmergencyAlertProps) {
  const [isAcknowledging, setIsAcknowledging] = useState(false);
  const [countdown, setCountdown] = useState(autoCloseDelay);
  const [isAcknowledged, setIsAcknowledged] = useState(false);

  // Countdown timer for auto-close after acknowledgment
  useEffect(() => {
    if (isAcknowledged && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (isAcknowledged && countdown === 0) {
      onClose();
    }
  }, [isAcknowledged, countdown, onClose]);

  // Audio alert (in a real app, you'd play an alert sound)
  useEffect(() => {
    if (open && alert.severity === 'critical') {
      // Play emergency sound
      console.log('🚨 EMERGENCY ALERT SOUND 🚨');
    }
  }, [open, alert.severity]);

  const handleAcknowledge = async () => {
    setIsAcknowledging(true);
    try {
      await onAcknowledge();
      setIsAcknowledged(true);
      setCountdown(autoCloseDelay);
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    } finally {
      setIsAcknowledging(false);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase();
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (!open) return null;

  return (
    <>
      {/* Backdrop overlay for critical alerts */}
      {alert.severity === 'critical' && (
        <div className="fixed inset-0 bg-red-900/20 backdrop-blur-sm z-40 animate-pulse" />
      )}

      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className={`
          max-w-2xl
          ${alert.severity === 'critical' ? 'border-red-500 border-2' : 'border-orange-300 border-2'}
          ${alert.severity === 'critical' ? 'bg-red-50' : 'bg-orange-50'}
          z-50
        `}>
          {/* Pulsing border animation for critical alerts */}
          {alert.severity === 'critical' && (
            <div className="absolute inset-0 rounded-lg animate-ping border-4 border-red-500 opacity-25 pointer-events-none" />
          )}

          <DialogHeader className="pb-4">
            <div className="flex items-center space-x-3">
              <div className={`
                p-3 rounded-full animate-bounce
                ${alert.severity === 'critical' ? 'bg-red-600' : 'bg-orange-600'}
              `}>
                <Siren className="h-8 w-8 text-white" />
              </div>
              <div className="flex-1">
                <DialogTitle className={`
                  text-2xl font-bold flex items-center space-x-2
                  ${alert.severity === 'critical' ? 'text-red-900' : 'text-orange-900'}
                `}>
                  <span>EMERGENCY ALERT</span>
                  <Badge
                    variant="destructive"
                    className="animate-pulse text-sm px-3 py-1"
                  >
                    {alert.severity.toUpperCase()}
                  </Badge>
                </DialogTitle>
                <div className="flex items-center space-x-2 mt-1 text-sm text-gray-600">
                  <Clock className="h-4 w-4" />
                  <span>{formatTime(alert.timestamp)}</span>
                  <span>•</span>
                  <span>Alert ID: {alert.id.slice(-8)}</span>
                </div>
              </div>
              {!isAcknowledged && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          </DialogHeader>

          {/* Alert Message */}
          <div className="space-y-6">
            <Alert className={`
              ${alert.severity === 'critical' ? 'border-red-600 bg-red-100' : 'border-orange-600 bg-orange-100'}
            `}>
              <AlertTriangle className={`
                h-5 w-5
                ${alert.severity === 'critical' ? 'text-red-600' : 'text-orange-600'}
              `} />
              <AlertDescription className={`
                text-lg font-semibold
                ${alert.severity === 'critical' ? 'text-red-900' : 'text-orange-900'}
              `}>
                {alert.message}
              </AlertDescription>
            </Alert>

            {/* Worker Information */}
            {workerData && (
              <div className="bg-white rounded-lg p-6 border border-gray-200 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Worker Details</h3>
                  <Button variant="outline" size="sm" onClick={onViewWorker}>
                    <User className="h-4 w-4 mr-2" />
                    View Full Profile
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Worker Info */}
                  <div className="flex items-center space-x-4">
                    <Avatar className="h-16 w-16">
                      <AvatarFallback className="text-lg">
                        {getInitials(workerData.name)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-semibold text-gray-900 text-lg">{workerData.name}</p>
                      <div className="flex items-center space-x-1 text-gray-600">
                        <MapPin className="h-4 w-4" />
                        <span>{workerData.location}</span>
                      </div>
                      {workerData.emergencyContact && (
                        <div className="flex items-center space-x-1 text-gray-600 mt-1">
                          <Phone className="h-4 w-4" />
                          <span>{workerData.emergencyContact.name}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Vital Signs */}
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Current Vitals</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {workerData.heartRate && (
                        <div className="flex items-center space-x-2">
                          <Heart className={`
                            h-5 w-5 animate-pulse
                            ${workerData.heartRate > 120 ? 'text-red-500' : 'text-blue-500'}
                          `} />
                          <div>
                            <p className="font-semibold text-gray-900">{workerData.heartRate}</p>
                            <p className="text-xs text-gray-600">BPM</p>
                          </div>
                        </div>
                      )}
                      {workerData.temperature && (
                        <div className="flex items-center space-x-2">
                          <Thermometer className={`
                            h-5 w-5
                            ${workerData.temperature > 38 ? 'text-red-500' : 'text-blue-500'}
                          `} />
                          <div>
                            <p className="font-semibold text-gray-900">
                              {workerData.temperature.toFixed(1)}°C
                            </p>
                            <p className="text-xs text-gray-600">Body Temp</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommended Actions */}
            {alert.recommended_actions.length > 0 && (
              <div className="bg-white rounded-lg p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Immediate Actions Required:
                </h3>
                <ul className="space-y-2">
                  {alert.recommended_actions.map((action, index) => (
                    <li key={index} className="flex items-start space-x-3">
                      <div className={`
                        w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mt-0.5
                        ${alert.severity === 'critical' ? 'bg-red-600' : 'bg-orange-600'}
                      `}>
                        {index + 1}
                      </div>
                      <span className="text-gray-900 font-medium">{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Acknowledgment Status */}
            {isAcknowledged && (
              <Alert className="border-green-600 bg-green-100">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <AlertDescription className="text-green-900">
                  Alert acknowledged successfully. This dialog will close in {countdown} seconds.
                </AlertDescription>
              </Alert>
            )}
          </div>

          <DialogFooter className="pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between w-full">
              <div className="text-sm text-gray-600">
                Location: {alert.location}
              </div>

              <div className="flex items-center space-x-3">
                {!isAcknowledged && (
                  <>
                    <Button
                      onClick={handleAcknowledge}
                      disabled={isAcknowledging}
                      className="flex items-center space-x-2"
                    >
                      {isAcknowledging ? (
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                      ) : (
                        <CheckCircle className="h-4 w-4" />
                      )}
                      <span>Acknowledge Alert</span>
                    </Button>

                    <Button
                      variant="destructive"
                      onClick={onEmergencyContact}
                      className="flex items-center space-x-2 animate-pulse"
                    >
                      <Phone className="h-4 w-4" />
                      <span>Emergency Contact</span>
                    </Button>
                  </>
                )}

                {isAcknowledged && (
                  <Button onClick={onClose}>
                    Close ({countdown})
                  </Button>
                )}
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * Emergency Alert Trigger
 * Component that monitors for critical alerts and shows emergency dialog
 */
interface EmergencyAlertTriggerProps {
  alerts: HealthAlert[];
  onAcknowledge: (alertId: string) => Promise<void>;
  onEmergencyContact: (workerId: string) => void;
  onViewWorker: (workerId: string) => void;
  getWorkerData?: (workerId: string) => {
    name: string;
    heartRate?: number;
    temperature?: number;
    location: string;
    emergencyContact?: { name: string; phone: string };
  } | undefined;
}

export function EmergencyAlertTrigger({
  alerts,
  onAcknowledge,
  onEmergencyContact,
  onViewWorker,
  getWorkerData,
}: EmergencyAlertTriggerProps) {
  const [currentAlert, setCurrentAlert] = useState<HealthAlert | null>(null);

  // Find the most critical unacknowledged alert
  useEffect(() => {
    const criticalAlerts = alerts.filter(
      alert => alert.severity === 'critical' && !alert.acknowledged && !alert.resolved
    );

    if (criticalAlerts.length > 0) {
      // Sort by timestamp to get the most recent
      criticalAlerts.sort((a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      setCurrentAlert(criticalAlerts[0]);
    } else {
      setCurrentAlert(null);
    }
  }, [alerts]);

  if (!currentAlert) return null;

  return (
    <EmergencyAlert
      alert={currentAlert}
      open={!!currentAlert}
      onClose={() => setCurrentAlert(null)}
      onAcknowledge={() => onAcknowledge(currentAlert.id)}
      onEmergencyContact={() => onEmergencyContact(currentAlert.worker_id)}
      onViewWorker={() => onViewWorker(currentAlert.worker_id)}
      workerData={getWorkerData?.(currentAlert.worker_id)}
    />
  );
}