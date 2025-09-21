/**
 * HeatGuard Pro Worker Status Grid
 * Grid layout for displaying multiple worker status cards
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
import WorkerStatusCard from './WorkerStatusCard';
import { WorkerProfile, BiometricData, ThermalComfortPrediction } from '@/types/thermal-comfort';
import {
  Search,
  Filter,
  Users,
  AlertTriangle,
  Grid,
  List,
  ArrowUpDown,
} from 'lucide-react';

interface WorkerData {
  worker: WorkerProfile;
  biometricData?: BiometricData;
  prediction?: ThermalComfortPrediction;
  isOnline?: boolean;
  lastUpdate?: string;
}

interface WorkerStatusGridProps {
  workers: WorkerData[];
  className?: string;
  variant?: 'grid' | 'list';
  onViewDetails?: (workerId: string) => void;
  onEmergencyContact?: (workerId: string) => void;
  onAcknowledgeAlert?: (workerId: string) => void;
  loading?: boolean;
  error?: string | null;
}

type SortField = 'name' | 'location' | 'risk' | 'temperature' | 'heartRate' | 'lastUpdate';
type FilterStatus = 'all' | 'safe' | 'warning' | 'critical' | 'offline';

export default function WorkerStatusGrid({
  workers,
  className = '',
  variant = 'grid',
  onViewDetails,
  onEmergencyContact,
  onAcknowledgeAlert,
  loading = false,
  error = null,
}: WorkerStatusGridProps) {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(variant);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  // Filter and sort workers
  const filteredAndSortedWorkers = useMemo(() => {
    let filtered = workers;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(({ worker }) =>
        worker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        worker.assigned_location.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(({ worker, prediction, isOnline }) => {
        if (filterStatus === 'offline') return !isOnline;
        if (!prediction) return filterStatus === 'safe';

        switch (filterStatus) {
          case 'critical':
            return prediction.risk_level === 'critical';
          case 'warning':
            return prediction.risk_level === 'high' || prediction.risk_level === 'moderate';
          case 'safe':
            return prediction.risk_level === 'low';
          default:
            return true;
        }
      });
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue: any, bValue: any;

      switch (sortField) {
        case 'name':
          aValue = a.worker.name;
          bValue = b.worker.name;
          break;
        case 'location':
          aValue = a.worker.assigned_location;
          bValue = b.worker.assigned_location;
          break;
        case 'risk':
          const riskOrder = { critical: 4, high: 3, moderate: 2, low: 1 };
          aValue = riskOrder[a.prediction?.risk_level as keyof typeof riskOrder] || 0;
          bValue = riskOrder[b.prediction?.risk_level as keyof typeof riskOrder] || 0;
          break;
        case 'temperature':
          aValue = a.biometricData?.CoreBodyTemperature || 0;
          bValue = b.biometricData?.CoreBodyTemperature || 0;
          break;
        case 'heartRate':
          aValue = a.biometricData?.HeartRate || 0;
          bValue = b.biometricData?.HeartRate || 0;
          break;
        case 'lastUpdate':
          aValue = a.lastUpdate ? new Date(a.lastUpdate).getTime() : 0;
          bValue = b.lastUpdate ? new Date(b.lastUpdate).getTime() : 0;
          break;
        default:
          aValue = a.worker.name;
          bValue = b.worker.name;
      }

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      return sortDirection === 'asc'
        ? (aValue > bValue ? 1 : -1)
        : (bValue > aValue ? 1 : -1);
    });

    return filtered;
  }, [workers, searchTerm, filterStatus, sortField, sortDirection]);

  // Calculate status counts
  const statusCounts = useMemo(() => {
    const counts = {
      total: workers.length,
      safe: 0,
      warning: 0,
      critical: 0,
      offline: 0,
    };

    workers.forEach(({ prediction, isOnline }) => {
      if (!isOnline) {
        counts.offline++;
      } else if (!prediction || prediction.risk_level === 'low') {
        counts.safe++;
      } else if (prediction.risk_level === 'critical') {
        counts.critical++;
      } else {
        counts.warning++;
      }
    });

    return counts;
  }, [workers]);

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
          <p className="text-lg font-medium text-gray-900 mb-2">Unable to load worker data</p>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        {/* Status Summary */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Users className="h-5 w-5 text-gray-500" />
            <span className="font-medium text-gray-900">{statusCounts.total} Workers</span>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="default" className="bg-green-100 text-green-800">
              {statusCounts.safe} Safe
            </Badge>
            {statusCounts.warning > 0 && (
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                {statusCounts.warning} At Risk
              </Badge>
            )}
            {statusCounts.critical > 0 && (
              <Badge variant="destructive">
                {statusCounts.critical} Critical
              </Badge>
            )}
            {statusCounts.offline > 0 && (
              <Badge variant="outline">
                {statusCounts.offline} Offline
              </Badge>
            )}
          </div>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'grid' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('grid')}
          >
            <Grid className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'list' ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setViewMode('list')}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
          <Input
            placeholder="Search workers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Status Filter */}
        <Select value={filterStatus} onValueChange={(value: FilterStatus) => setFilterStatus(value)}>
          <SelectTrigger className="w-40">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Workers</SelectItem>
            <SelectItem value="critical">Critical Only</SelectItem>
            <SelectItem value="warning">At Risk</SelectItem>
            <SelectItem value="safe">Safe Only</SelectItem>
            <SelectItem value="offline">Offline</SelectItem>
          </SelectContent>
        </Select>

        {/* Sort Options */}
        <Select value={sortField} onValueChange={(value: SortField) => setSortField(value)}>
          <SelectTrigger className="w-44">
            <ArrowUpDown className="mr-2 h-4 w-4" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="name">Sort by Name</SelectItem>
            <SelectItem value="location">Sort by Location</SelectItem>
            <SelectItem value="risk">Sort by Risk Level</SelectItem>
            <SelectItem value="temperature">Sort by Temperature</SelectItem>
            <SelectItem value="heartRate">Sort by Heart Rate</SelectItem>
            <SelectItem value="lastUpdate">Sort by Last Update</SelectItem>
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

      {/* Workers Grid/List */}
      {filteredAndSortedWorkers.length === 0 ? (
        <div className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">No workers found</p>
          <p className="text-gray-600">
            {searchTerm || filterStatus !== 'all'
              ? 'Try adjusting your search or filter criteria'
              : 'No worker data available'
            }
          </p>
        </div>
      ) : (
        <div className={
          viewMode === 'grid'
            ? 'grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6'
            : 'space-y-4'
        }>
          {filteredAndSortedWorkers.map(({ worker, biometricData, prediction, isOnline, lastUpdate }) => (
            <WorkerStatusCard
              key={worker.id}
              worker={worker}
              biometricData={biometricData}
              prediction={prediction}
              isOnline={isOnline}
              lastUpdate={lastUpdate}
              variant={viewMode === 'grid' ? 'compact' : 'summary'}
              onViewDetails={onViewDetails}
              onEmergencyContact={onEmergencyContact}
              onAcknowledgeAlert={onAcknowledgeAlert}
            />
          ))}
        </div>
      )}

      {/* Results Count */}
      {filteredAndSortedWorkers.length > 0 && (
        <div className="text-center text-sm text-gray-500 pt-4 border-t">
          Showing {filteredAndSortedWorkers.length} of {workers.length} workers
        </div>
      )}
    </div>
  );
}