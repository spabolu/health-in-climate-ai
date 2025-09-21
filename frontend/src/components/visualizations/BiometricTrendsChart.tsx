/**
 * HeatGuard Pro Biometric Trends Chart
 * Multi-line chart displaying worker biometric data trends with safety thresholds
 */

'use client';

import { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { BiometricData } from '@/types/thermal-comfort';
import {
  Heart,
  Thermometer,
  Droplets,
  Activity,
  TrendingUp,
  TrendingDown,
  Download,
  Settings,
  AlertTriangle,
} from 'lucide-react';

interface BiometricDataPoint {
  timestamp: string;
  heartRate: number;
  bodyTemperature: number;
  skinTemperature: number;
  skinConductance: number;
  hydrationLevel: number;
  respiratoryRate?: number;
  workerId?: string;
  workerName?: string;
}

interface BiometricTrendsChartProps {
  data: BiometricDataPoint[];
  title?: string;
  height?: number;
  workerId?: string;
  workerName?: string;
  timeRange?: '1h' | '4h' | '12h' | '24h' | '7d';
  onExport?: () => void;
  className?: string;
}

interface MetricConfig {
  key: keyof BiometricDataPoint;
  label: string;
  color: string;
  unit: string;
  icon: React.ComponentType<{ className?: string }>;
  yAxisId?: string;
  normalRange: { min: number; max: number };
  warningRange: { min: number; max: number };
  enabled: boolean;
}

const defaultMetrics: MetricConfig[] = [
  {
    key: 'heartRate',
    label: 'Heart Rate',
    color: '#EF4444',
    unit: 'BPM',
    icon: Heart,
    yAxisId: 'left',
    normalRange: { min: 60, max: 100 },
    warningRange: { min: 50, max: 120 },
    enabled: true,
  },
  {
    key: 'bodyTemperature',
    label: 'Body Temperature',
    color: '#F97316',
    unit: '°C',
    icon: Thermometer,
    yAxisId: 'temp',
    normalRange: { min: 36.5, max: 37.5 },
    warningRange: { min: 36, max: 38 },
    enabled: true,
  },
  {
    key: 'skinTemperature',
    label: 'Skin Temperature',
    color: '#FBBF24',
    unit: '°C',
    icon: Thermometer,
    yAxisId: 'temp',
    normalRange: { min: 32, max: 36 },
    warningRange: { min: 30, max: 38 },
    enabled: true,
  },
  {
    key: 'skinConductance',
    label: 'Skin Conductance',
    color: '#3B82F6',
    unit: 'μS',
    icon: Droplets,
    yAxisId: 'right',
    normalRange: { min: 5, max: 25 },
    warningRange: { min: 2, max: 50 },
    enabled: false,
  },
  {
    key: 'hydrationLevel',
    label: 'Hydration Level',
    color: '#06B6D4',
    unit: '%',
    icon: Droplets,
    yAxisId: 'percent',
    normalRange: { min: 0.7, max: 1.0 },
    warningRange: { min: 0.5, max: 1.0 },
    enabled: false,
  },
  {
    key: 'respiratoryRate',
    label: 'Respiratory Rate',
    color: '#8B5CF6',
    unit: '/min',
    icon: Activity,
    yAxisId: 'left',
    normalRange: { min: 12, max: 20 },
    warningRange: { min: 8, max: 30 },
    enabled: false,
  },
];

export default function BiometricTrendsChart({
  data,
  title = 'Biometric Trends',
  height = 400,
  workerId,
  workerName,
  timeRange = '12h',
  onExport,
  className = '',
}: BiometricTrendsChartProps) {
  const [metrics, setMetrics] = useState<MetricConfig[]>(defaultMetrics);
  const [showBrush, setShowBrush] = useState(false);

  // Process and filter data
  const chartData = useMemo(() => {
    const now = new Date();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '4h': 4 * 60 * 60 * 1000,
      '12h': 12 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
    };

    const cutoffTime = now.getTime() - timeRanges[timeRange];

    return data
      .filter(item => new Date(item.timestamp).getTime() >= cutoffTime)
      .map(item => ({
        ...item,
        hydrationLevel: item.hydrationLevel * 100, // Convert to percentage
        displayTime: new Date(item.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        displayDate: new Date(item.timestamp).toLocaleDateString(),
        fullTimestamp: new Date(item.timestamp).toLocaleString(),
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [data, timeRange]);

  // Calculate statistics for enabled metrics
  const stats = useMemo(() => {
    if (chartData.length === 0) return {};

    const enabledMetrics = metrics.filter(m => m.enabled);
    const statistics: Record<string, any> = {};

    enabledMetrics.forEach(metric => {
      const values = chartData
        .map(item => item[metric.key] as number)
        .filter(val => typeof val === 'number' && !isNaN(val));

      if (values.length > 0) {
        const avg = values.reduce((sum, val) => sum + val, 0) / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);
        const trend = values.length > 1 ? values[values.length - 1] - values[0] : 0;

        // Count values outside normal range
        const outOfRange = values.filter(val =>
          val < metric.normalRange.min || val > metric.normalRange.max
        ).length;

        statistics[metric.key] = {
          avg: avg.toFixed(metric.key === 'hydrationLevel' ? 0 : 1),
          min: min.toFixed(metric.key === 'hydrationLevel' ? 0 : 1),
          max: max.toFixed(metric.key === 'hydrationLevel' ? 0 : 1),
          trend,
          outOfRange,
          unit: metric.unit,
          label: metric.label,
          color: metric.color,
        };
      }
    });

    return statistics;
  }, [chartData, metrics]);

  // Toggle metric visibility
  const toggleMetric = (index: number) => {
    setMetrics(prev => prev.map((metric, i) =>
      i === index ? { ...metric, enabled: !metric.enabled } : metric
    ));
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg min-w-[200px]">
          <p className="font-medium text-gray-900 mb-3">
            {data.fullTimestamp}
          </p>
          <div className="space-y-2">
            {payload.map((entry: any, index: number) => {
              const metric = metrics.find(m => m.key === entry.dataKey);
              if (!metric) return null;

              const value = entry.value;
              const isOutOfRange = value < metric.normalRange.min || value > metric.normalRange.max;
              const isCritical = value < metric.warningRange.min || value > metric.warningRange.max;

              return (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-sm text-gray-600">{metric.label}:</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm font-medium ${
                      isCritical ? 'text-red-600' : isOutOfRange ? 'text-yellow-600' : 'text-gray-900'
                    }`}>
                      {value.toFixed(metric.key === 'hydrationLevel' ? 0 : 1)} {metric.unit}
                    </span>
                    {(isOutOfRange || isCritical) && (
                      <AlertTriangle className={`h-3 w-3 ${
                        isCritical ? 'text-red-500' : 'text-yellow-500'
                      }`} />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">No biometric data</p>
          <p className="text-gray-600">No data available for the selected time range</p>
        </div>
      </Card>
    );
  }

  const enabledMetrics = metrics.filter(m => m.enabled);

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <div className="flex items-center space-x-2 mt-1">
            <p className="text-sm text-gray-600">
              {workerName ? `${workerName} • ` : ''}Last {timeRange}
            </p>
            <Badge variant="outline">{chartData.length} data points</Badge>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowBrush(!showBrush)}
          >
            <Settings className="h-4 w-4 mr-2" />
            {showBrush ? 'Hide' : 'Show'} Zoom
          </Button>
          {onExport && (
            <Button variant="outline" size="sm" onClick={onExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Metric Toggles */}
      <div className="flex flex-wrap gap-3 mb-6">
        {metrics.map((metric, index) => {
          const Icon = metric.icon;
          const stat = stats[metric.key];

          return (
            <div
              key={metric.key}
              className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                metric.enabled ? 'bg-white border-gray-300' : 'bg-gray-50 border-gray-200'
              }`}
              onClick={() => toggleMetric(index)}
            >
              <Checkbox checked={metric.enabled} readOnly />
              <div className="flex items-center space-x-2">
                <Icon className="h-4 w-4" style={{ color: metric.color }} />
                <div>
                  <p className="text-sm font-medium text-gray-900">{metric.label}</p>
                  {stat && (
                    <div className="flex items-center space-x-2 text-xs text-gray-600">
                      <span>Avg: {stat.avg}{stat.unit}</span>
                      {stat.trend !== 0 && (
                        <>
                          {stat.trend > 0 ? (
                            <TrendingUp className="h-3 w-3 text-red-500" />
                          ) : (
                            <TrendingDown className="h-3 w-3 text-blue-500" />
                          )}
                        </>
                      )}
                      {stat.outOfRange > 0 && (
                        <Badge variant="destructive" className="text-xs">
                          {stat.outOfRange} alerts
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="displayTime"
            stroke="#6B7280"
            fontSize={12}
            interval="preserveStartEnd"
          />

          {/* Primary Y-axis (Heart Rate, Respiratory Rate) */}
          <YAxis
            yAxisId="left"
            stroke="#6B7280"
            fontSize={12}
            label={{ value: 'BPM / Rate', angle: -90, position: 'insideLeft' }}
          />

          {/* Temperature Y-axis */}
          <YAxis
            yAxisId="temp"
            orientation="right"
            stroke="#F97316"
            fontSize={12}
            label={{ value: '°C', angle: 90, position: 'insideRight' }}
          />

          {/* Secondary Y-axis (Skin Conductance) */}
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#3B82F6"
            fontSize={12}
            hide
          />

          {/* Percentage Y-axis (Hydration) */}
          <YAxis
            yAxisId="percent"
            domain={[0, 100]}
            hide
          />

          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Reference lines for normal ranges */}
          {enabledMetrics.map(metric => (
            <g key={`ref-${metric.key}`}>
              <ReferenceLine
                yAxisId={metric.yAxisId}
                y={metric.normalRange.min}
                stroke={metric.color}
                strokeDasharray="5 5"
                strokeOpacity={0.5}
              />
              <ReferenceLine
                yAxisId={metric.yAxisId}
                y={metric.normalRange.max}
                stroke={metric.color}
                strokeDasharray="5 5"
                strokeOpacity={0.5}
              />
            </g>
          ))}

          {/* Data Lines */}
          {enabledMetrics.map(metric => (
            <Line
              key={metric.key}
              type="monotone"
              dataKey={metric.key}
              stroke={metric.color}
              strokeWidth={2}
              dot={{ r: 3, fill: metric.color }}
              activeDot={{ r: 5, fill: metric.color }}
              yAxisId={metric.yAxisId}
              name={metric.label}
              connectNulls={false}
            />
          ))}

          {/* Brush for zooming */}
          {showBrush && (
            <Brush dataKey="displayTime" height={30} stroke="#8884d8" />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Summary Statistics */}
      {Object.keys(stats).length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h4 className="font-medium text-gray-900 mb-3">Summary Statistics</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(stats).map(([key, stat]: [string, any]) => (
              <div key={key} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: stat.color }}
                  />
                  <p className="text-xs text-gray-600">{stat.label}</p>
                </div>
                <p className="text-sm font-semibold text-gray-900">
                  {stat.avg} {stat.unit}
                </p>
                <p className="text-xs text-gray-500">
                  Range: {stat.min} - {stat.max}
                </p>
                {stat.outOfRange > 0 && (
                  <Badge variant="destructive" className="mt-1 text-xs">
                    {stat.outOfRange} anomalies
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}