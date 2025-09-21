/**
 * HeatGuard Pro Alert Card Component
 * Individual alert display with action buttons and severity indicators
 */

'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { HealthAlert } from '@/types/thermal-comfort';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  MapPin,
  User,
  Phone,
  Eye,
  MoreVertical,
  Bell,
  Archive,
  Flag,
} from 'lucide-react';

interface AlertCardProps {
  alert: HealthAlert;
  className?: string;
  variant?: 'default' | 'compact' | 'detailed';
  showWorkerInfo?: boolean;
  onAcknowledge?: (alertId: string) => Promise<void>;
  onResolve?: (alertId: string) => Promise<void>;
  onViewWorker?: (workerId: string) => void;
  onEmergencyContact?: (workerId: string) => void;
  isProcessing?: boolean;
}

const severityConfig = {
  low: {
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    badgeVariant: 'secondary' as const,
    icon: Bell,
  },
  moderate: {
    color: 'text-yellow-600',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    badgeVariant: 'secondary' as const,
    icon: AlertTriangle,
  },
  high: {
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    badgeVariant: 'outline' as const,
    icon: AlertTriangle,
  },
  critical: {
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
    badgeVariant: 'destructive' as const,
    icon: AlertTriangle,
  },
};

const alertTypeLabels = {
  heat_exhaustion_risk: 'Heat Exhaustion Risk',
  dehydration_warning: 'Dehydration Warning',
  heart_rate_anomaly: 'Heart Rate Anomaly',
  critical_temperature: 'Critical Temperature',
};

export default function AlertCard({
  alert,
  className = '',
  variant = 'default',
  showWorkerInfo = true,
  onAcknowledge,
  onResolve,
  onViewWorker,
  onEmergencyContact,
  isProcessing = false,
}: AlertCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localProcessing, setLocalProcessing] = useState<'acknowledge' | 'resolve' | null>(null);

  const severityStyle = severityConfig[alert.severity];
  const SeverityIcon = severityStyle.icon;

  const getInitials = (workerId: string) => {
    return workerId.slice(-3).toUpperCase();
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const handleAcknowledge = async () => {
    if (!onAcknowledge || isProcessing || localProcessing) return;
    setLocalProcessing('acknowledge');
    try {
      await onAcknowledge(alert.id);
    } finally {
      setLocalProcessing(null);
    }
  };

  const handleResolve = async () => {
    if (!onResolve || isProcessing || localProcessing) return;
    setLocalProcessing('resolve');
    try {
      await onResolve(alert.id);
    } finally {
      setLocalProcessing(null);
    }
  };

  // Compact variant for lists
  if (variant === 'compact') {
    return (
      <Card className={`${severityStyle.border} border-l-4 hover:shadow-md transition-shadow ${className}`}>
        <div className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <SeverityIcon className={`h-5 w-5 ${severityStyle.color}`} />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <Badge variant={severityStyle.badgeVariant} className="text-xs">
                    {alert.severity.toUpperCase()}
                  </Badge>
                  <span className="text-sm font-medium text-gray-900">
                    {alertTypeLabels[alert.alert_type] || alert.alert_type}
                  </span>
                  <span className="text-xs text-gray-500">{formatTime(alert.timestamp)}</span>
                </div>
                <p className="text-sm text-gray-600 mt-1 line-clamp-1">{alert.message}</p>
                {showWorkerInfo && (
                  <div className="flex items-center space-x-2 mt-1 text-xs text-gray-500">
                    <MapPin className="h-3 w-3" />
                    <span>{alert.location}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {alert.acknowledged && <CheckCircle className="h-4 w-4 text-green-500" />}
              {alert.resolved && <Archive className="h-4 w-4 text-gray-500" />}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <MoreVertical className="h-3 w-3" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  {!alert.acknowledged && (
                    <DropdownMenuItem onClick={handleAcknowledge}>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Acknowledge
                    </DropdownMenuItem>
                  )}
                  {!alert.resolved && (
                    <DropdownMenuItem onClick={handleResolve}>
                      <Archive className="mr-2 h-4 w-4" />
                      Resolve
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => onViewWorker?.(alert.worker_id)}>
                    <Eye className="mr-2 h-4 w-4" />
                    View Worker
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEmergencyContact?.(alert.worker_id)}>
                    <Phone className="mr-2 h-4 w-4" />
                    Emergency Contact
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  // Default and detailed variants
  return (
    <Card className={`${severityStyle.border} border-l-4 ${className}`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${severityStyle.bg}`}>
              <SeverityIcon className={`h-5 w-5 ${severityStyle.color}`} />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <Badge variant={severityStyle.badgeVariant}>
                  {alert.severity.toUpperCase()}
                </Badge>
                <span className="text-lg font-semibold text-gray-900">
                  {alertTypeLabels[alert.alert_type] || alert.alert_type}
                </span>
              </div>
              <div className="flex items-center space-x-2 mt-1 text-sm text-gray-500">
                <Clock className="h-4 w-4" />
                <span>{formatTime(alert.timestamp)}</span>
                <span>•</span>
                <span>{new Date(alert.timestamp).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {alert.acknowledged && (
              <Badge variant="outline" className="text-green-600 border-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Acknowledged
              </Badge>
            )}
            {alert.resolved && (
              <Badge variant="outline" className="text-gray-600 border-gray-600">
                <Archive className="h-3 w-3 mr-1" />
                Resolved
              </Badge>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setIsExpanded(!isExpanded)}>
                  <Eye className="mr-2 h-4 w-4" />
                  {isExpanded ? 'Show Less' : 'Show More'}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Flag className="mr-2 h-4 w-4" />
                  Flag as Important
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Message */}
        <div className="mb-4">
          <p className="text-gray-900 font-medium mb-2">{alert.message}</p>
        </div>

        {/* Worker and Location Info */}
        {showWorkerInfo && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Avatar className="h-10 w-10">
                  <AvatarFallback>{getInitials(alert.worker_id)}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-gray-900">Worker {alert.worker_id}</p>
                  <div className="flex items-center space-x-1 text-sm text-gray-600">
                    <MapPin className="h-3 w-3" />
                    <span>{alert.location}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onViewWorker?.(alert.worker_id)}
                >
                  <User className="h-4 w-4 mr-2" />
                  View Worker
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEmergencyContact?.(alert.worker_id)}
                >
                  <Phone className="h-4 w-4 mr-2" />
                  Emergency
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Recommended Actions */}
        {alert.recommended_actions.length > 0 && (
          <div className="mb-4">
            <h4 className="font-medium text-gray-900 mb-2">Recommended Actions:</h4>
            <ul className="space-y-1">
              {alert.recommended_actions.map((action, index) => (
                <li key={index} className="flex items-start space-x-2 text-sm text-gray-700">
                  <span className="text-blue-500 mt-1">•</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Expanded Details */}
        {isExpanded && variant === 'detailed' && (
          <div className="border-t border-gray-200 pt-4 space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Alert ID:</span>
                <span className="ml-2 font-mono text-gray-900">{alert.id}</span>
              </div>
              <div>
                <span className="text-gray-500">Worker ID:</span>
                <span className="ml-2 font-mono text-gray-900">{alert.worker_id}</span>
              </div>
              <div>
                <span className="text-gray-500">Created:</span>
                <span className="ml-2 text-gray-900">
                  {new Date(alert.timestamp).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Location:</span>
                <span className="ml-2 text-gray-900">{alert.location}</span>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        {!alert.resolved && (
          <div className="flex items-center space-x-3 pt-4 border-t border-gray-200">
            {!alert.acknowledged && (
              <Button
                onClick={handleAcknowledge}
                disabled={isProcessing || localProcessing === 'acknowledge'}
                className="flex items-center space-x-2"
              >
                {localProcessing === 'acknowledge' ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                ) : (
                  <CheckCircle className="h-4 w-4" />
                )}
                <span>Acknowledge</span>
              </Button>
            )}
            <Button
              variant="outline"
              onClick={handleResolve}
              disabled={isProcessing || localProcessing === 'resolve'}
              className="flex items-center space-x-2"
            >
              {localProcessing === 'resolve' ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-600 border-t-transparent" />
              ) : (
                <Archive className="h-4 w-4" />
              )}
              <span>Resolve</span>
            </Button>
            {alert.severity === 'critical' && (
              <Button
                variant="destructive"
                onClick={() => onEmergencyContact?.(alert.worker_id)}
                className="flex items-center space-x-2"
              >
                <Phone className="h-4 w-4" />
                <span>Emergency Contact</span>
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}