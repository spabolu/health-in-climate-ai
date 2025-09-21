/**
 * HeatGuard Pro Alert Center
 * Central alert management interface with filtering, sorting, and bulk actions
 */

'use client';

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import AlertCard from './AlertCard';
import { HealthAlert } from '@/types/thermal-comfort';
import {
  AlertTriangle,
  Search,
  Filter,
  ArrowUpDown,
  CheckCircle,
  Archive,
  Bell,
  RefreshCw,
  Download,
} from 'lucide-react';

interface AlertCenterProps {
  alerts: HealthAlert[];
  onAcknowledge?: (alertId: string) => Promise<void>;
  onResolve?: (alertId: string) => Promise<void>;
  onViewWorker?: (workerId: string) => void;
  onEmergencyContact?: (workerId: string) => void;
  onRefresh?: () => void;
  onExport?: (alerts: HealthAlert[]) => void;
  loading?: boolean;
  error?: string | null;
  className?: string;
}

type AlertFilter = 'all' | 'unacknowledged' | 'acknowledged' | 'resolved';
type SeverityFilter = 'all' | 'critical' | 'high' | 'moderate' | 'low';
type SortField = 'timestamp' | 'severity' | 'type' | 'location' | 'worker';

const severityOrder = { critical: 4, high: 3, moderate: 2, low: 1 };

export default function AlertCenter({
  alerts,
  onAcknowledge,
  onResolve,
  onViewWorker,
  onEmergencyContact,
  onRefresh,
  onExport,
  loading = false,
  error = null,
  className = '',
}: AlertCenterProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all');
  const [sortField, setSortField] = useState<SortField>('timestamp');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [selectedAlerts, setSelectedAlerts] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<AlertFilter>('unacknowledged');

  // Filter and sort alerts
  const filteredAlerts = useMemo(() => {
    let filtered = alerts;

    // Apply text search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(alert =>
        alert.message.toLowerCase().includes(term) ||
        alert.location.toLowerCase().includes(term) ||
        alert.worker_id.toLowerCase().includes(term) ||
        alert.alert_type.toLowerCase().includes(term)
      );
    }

    // Apply status filter
    // Note: statusFilter is hardcoded to 'all' - no filtering needed

    // Apply severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'timestamp':
          comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          break;
        case 'severity':
          comparison = (severityOrder[a.severity] || 0) - (severityOrder[b.severity] || 0);
          break;
        case 'type':
          comparison = a.alert_type.localeCompare(b.alert_type);
          break;
        case 'location':
          comparison = a.location.localeCompare(b.location);
          break;
        case 'worker':
          comparison = a.worker_id.localeCompare(b.worker_id);
          break;
        default:
          comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [alerts, searchTerm, severityFilter, sortField, sortDirection]);

  // Group alerts by status for tabs
  const alertsByStatus = useMemo(() => {
    const groups = {
      unacknowledged: alerts.filter(a => !a.acknowledged && !a.resolved),
      acknowledged: alerts.filter(a => a.acknowledged && !a.resolved),
      resolved: alerts.filter(a => a.resolved),
      all: alerts,
    };
    return groups;
  }, [alerts]);

  // Statistics
  const stats = useMemo(() => {
    const critical = alerts.filter(a => a.severity === 'critical' && !a.resolved).length;
    const high = alerts.filter(a => a.severity === 'high' && !a.resolved).length;
    const unacknowledged = alerts.filter(a => !a.acknowledged && !a.resolved).length;
    const total = alerts.length;

    return { critical, high, unacknowledged, total };
  }, [alerts]);

  // Handle bulk actions
  const handleBulkAcknowledge = async () => {
    if (!onAcknowledge) return;
    const promises = Array.from(selectedAlerts).map(id => onAcknowledge(id));
    await Promise.all(promises);
    setSelectedAlerts(new Set());
  };

  const handleBulkResolve = async () => {
    if (!onResolve) return;
    const promises = Array.from(selectedAlerts).map(id => onResolve(id));
    await Promise.all(promises);
    setSelectedAlerts(new Set());
  };

  const handleSelectAll = () => {
    if (selectedAlerts.size === filteredAlerts.length) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set(filteredAlerts.map(a => a.id)));
    }
  };

  const toggleSelection = (alertId: string) => {
    const newSelection = new Set(selectedAlerts);
    if (newSelection.has(alertId)) {
      newSelection.delete(alertId);
    } else {
      newSelection.add(alertId);
    }
    setSelectedAlerts(newSelection);
  };

  if (loading) {
    return (
      <div className={`p-8 ${className}`}>
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-8 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">Unable to load alerts</p>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={onRefresh}>Try Again</Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Statistics */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div className="flex items-center space-x-6">
          <h1 className="text-2xl font-bold text-gray-900">Alert Center</h1>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
              {stats.critical} Critical
            </Badge>
            <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
              {stats.high} High Priority
            </Badge>
            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
              {stats.unacknowledged} Unacknowledged
            </Badge>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={() => onExport?.(filteredAlerts)}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
          <Input
            placeholder="Search alerts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Severity Filter */}
        <Select value={severityFilter} onValueChange={(value: SeverityFilter) => setSeverityFilter(value)}>
          <SelectTrigger className="w-40">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severities</SelectItem>
            <SelectItem value="critical">Critical Only</SelectItem>
            <SelectItem value="high">High Priority</SelectItem>
            <SelectItem value="moderate">Moderate</SelectItem>
            <SelectItem value="low">Low Priority</SelectItem>
          </SelectContent>
        </Select>

        {/* Sort Options */}
        <Select value={sortField} onValueChange={(value: SortField) => setSortField(value)}>
          <SelectTrigger className="w-44">
            <ArrowUpDown className="mr-2 h-4 w-4" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="timestamp">Sort by Time</SelectItem>
            <SelectItem value="severity">Sort by Severity</SelectItem>
            <SelectItem value="type">Sort by Type</SelectItem>
            <SelectItem value="location">Sort by Location</SelectItem>
            <SelectItem value="worker">Sort by Worker</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
        >
          {sortDirection === 'asc' ? '↑' : '↓'}
        </Button>
      </div>

      {/* Bulk Actions */}
      {selectedAlerts.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-blue-800 font-medium">
              {selectedAlerts.size} alert{selectedAlerts.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex items-center space-x-2">
              <Button size="sm" onClick={handleBulkAcknowledge}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Acknowledge All
              </Button>
              <Button size="sm" variant="outline" onClick={handleBulkResolve}>
                <Archive className="h-4 w-4 mr-2" />
                Resolve All
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedAlerts(new Set())}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Alert Tabs */}
      <Tabs value={activeTab} onValueChange={(value: string) => setActiveTab(value as AlertFilter)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="unacknowledged" className="relative">
            Unacknowledged
            {alertsByStatus.unacknowledged.length > 0 && (
              <Badge variant="destructive" className="absolute -top-2 -right-2 h-5 w-5 p-0 text-xs">
                {alertsByStatus.unacknowledged.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="acknowledged">
            Acknowledged ({alertsByStatus.acknowledged.length})
          </TabsTrigger>
          <TabsTrigger value="resolved">
            Resolved ({alertsByStatus.resolved.length})
          </TabsTrigger>
          <TabsTrigger value="all">
            All ({alertsByStatus.all.length})
          </TabsTrigger>
        </TabsList>

        {Object.entries(alertsByStatus).map(([status, statusAlerts]) => (
          <TabsContent key={status} value={status} className="space-y-4">
            {/* Select All Checkbox */}
            {statusAlerts.length > 0 && (
              <div className="flex items-center space-x-2 pb-2 border-b border-gray-200">
                <Checkbox
                  checked={selectedAlerts.size === filteredAlerts.length && filteredAlerts.length > 0}
                  onCheckedChange={handleSelectAll}
                />
                <span className="text-sm text-gray-600">Select all visible alerts</span>
              </div>
            )}

            {/* Alert List */}
            {statusAlerts.length === 0 ? (
              <div className="text-center py-12">
                <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-900 mb-2">
                  No {status} alerts
                </p>
                <p className="text-gray-600">
                  {status === 'unacknowledged'
                    ? 'All alerts have been acknowledged'
                    : `No ${status} alerts to display`
                  }
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredAlerts
                  .filter(alert => {
                    if (status === 'unacknowledged') return !alert.acknowledged && !alert.resolved;
                    if (status === 'acknowledged') return alert.acknowledged && !alert.resolved;
                    if (status === 'resolved') return alert.resolved;
                    return true;
                  })
                  .map(alert => (
                    <div key={alert.id} className="flex items-start space-x-3">
                      <Checkbox
                        checked={selectedAlerts.has(alert.id)}
                        onCheckedChange={() => toggleSelection(alert.id)}
                        className="mt-6"
                      />
                      <div className="flex-1">
                        <AlertCard
                          alert={alert}
                          variant="default"
                          onAcknowledge={onAcknowledge}
                          onResolve={onResolve}
                          onViewWorker={onViewWorker}
                          onEmergencyContact={onEmergencyContact}
                        />
                      </div>
                    </div>
                  ))
                }
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>

      {/* Results Summary */}
      {filteredAlerts.length > 0 && (
        <div className="text-center text-sm text-gray-500 pt-4 border-t">
          Showing {filteredAlerts.length} of {alerts.length} alerts
        </div>
      )}
    </div>
  );
}