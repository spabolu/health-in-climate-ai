/**
 * HeatGuard Pro Thermal Comfort Chart
 * Time-series visualization of thermal comfort predictions with safety zones
 */

'use client';

import { useMemo } from 'react';
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
  Area,
  ComposedChart,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ThermalComfortPrediction } from '@/types/thermal-comfort';
import {
  Download,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertTriangle,
  Thermometer,
} from 'lucide-react';

interface ThermalComfortDataPoint {
  timestamp: string;
  thermalComfort: string;
  thermalComfortValue: number;
  riskLevel: string;
  riskLevelValue: number;
  confidence: number;
  temperature?: number;
  humidity?: number;
  heatIndex?: number;
  workerId?: string;
  workerName?: string;
}

interface ThermalComfortChartProps {
  data: ThermalComfortDataPoint[];
  title?: string;
  height?: number;
  showTemperature?: boolean;
  showRiskLevel?: boolean;
  showConfidence?: boolean;
  timeRange?: '1h' | '4h' | '12h' | '24h' | '7d';
  onExport?: () => void;
  className?: string;
}

// Thermal comfort scale mapping
const thermalComfortScale = {
  'Cold': 1,
  'Cool': 2,
  'Slightly Cool': 3,
  'Neutral': 4,
  'Slightly Warm': 5,
  'Warm': 6,
  'Hot': 7,
};

// Risk level mapping
const riskLevelScale = {
  'low': 1,
  'moderate': 2,
  'high': 3,
  'critical': 4,
};

// Color schemes
const thermalComfortColors = {
  1: '#3B82F6', // Blue - Cold
  2: '#60A5FA', // Light Blue - Cool
  3: '#86EFAC', // Light Green - Slightly Cool
  4: '#22C55E', // Green - Neutral
  5: '#FBBF24', // Yellow - Slightly Warm
  6: '#F97316', // Orange - Warm
  7: '#EF4444', // Red - Hot
};

const riskLevelColors = {
  1: '#22C55E', // Green - Low
  2: '#FBBF24', // Yellow - Moderate
  3: '#F97316', // Orange - High
  4: '#EF4444', // Red - Critical
};

export default function ThermalComfortChart({
  data,
  title = 'Thermal Comfort Trends',
  height = 400,
  showTemperature = true,
  showRiskLevel = true,
  showConfidence = false,
  timeRange = '12h',
  onExport,
  className = '',
}: ThermalComfortChartProps) {
  // Process and filter data based on time range
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
        thermalComfortValue: thermalComfortScale[item.thermalComfort as keyof typeof thermalComfortScale] || 4,
        riskLevelValue: riskLevelScale[item.riskLevel as keyof typeof riskLevelScale] || 1,
        displayTime: new Date(item.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        displayDate: new Date(item.timestamp).toLocaleDateString(),
      }))
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [data, timeRange]);

  // Calculate statistics
  const stats = useMemo(() => {
    if (chartData.length === 0) return null;

    const avgComfort = chartData.reduce((sum, item) => sum + item.thermalComfortValue, 0) / chartData.length;
    const avgRisk = chartData.reduce((sum, item) => sum + item.riskLevelValue, 0) / chartData.length;
    const criticalEvents = chartData.filter(item => item.riskLevelValue === 4).length;
    const trend = chartData.length > 1
      ? chartData[chartData.length - 1].thermalComfortValue - chartData[0].thermalComfortValue
      : 0;

    return {
      avgComfort: avgComfort.toFixed(1),
      avgRisk: avgRisk.toFixed(1),
      criticalEvents,
      trend,
      dataPoints: chartData.length,
    };
  }, [chartData]);

  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">
            {data.displayTime} - {data.displayDate}
          </p>
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Thermal Comfort:</span>
              <Badge
                style={{
                  backgroundColor: thermalComfortColors[data.thermalComfortValue] + '20',
                  borderColor: thermalComfortColors[data.thermalComfortValue],
                  color: thermalComfortColors[data.thermalComfortValue]
                }}
              >
                {data.thermalComfort}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Risk Level:</span>
              <Badge
                variant={data.riskLevelValue === 4 ? 'destructive' : 'secondary'}
                style={{
                  backgroundColor: riskLevelColors[data.riskLevelValue] + '20',
                  borderColor: riskLevelColors[data.riskLevelValue],
                  color: riskLevelColors[data.riskLevelValue]
                }}
              >
                {data.riskLevel.toUpperCase()}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Confidence:</span>
              <span className="text-sm font-medium text-gray-900">
                {(data.confidence * 100).toFixed(0)}%
              </span>
            </div>
            {data.temperature && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Temperature:</span>
                <span className="text-sm font-medium text-gray-900">
                  {data.temperature.toFixed(1)}°C
                </span>
              </div>
            )}
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
          <Thermometer className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">No thermal comfort data</p>
          <p className="text-gray-600">No data available for the selected time range</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600 mt-1">
            Showing data for the last {timeRange}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {stats && (
            <div className="flex items-center space-x-2">
              {stats.trend > 0.5 ? (
                <TrendingUp className="h-4 w-4 text-red-500" />
              ) : stats.trend < -0.5 ? (
                <TrendingDown className="h-4 w-4 text-blue-500" />
              ) : (
                <Minus className="h-4 w-4 text-gray-500" />
              )}
              <span className="text-sm text-gray-600">
                {stats.dataPoints} points
              </span>
            </div>
          )}
          {onExport && (
            <Button variant="outline" size="sm" onClick={onExport}>
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          )}
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Avg Comfort</p>
            <p className="text-lg font-semibold text-gray-900">{stats.avgComfort}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Avg Risk</p>
            <p className="text-lg font-semibold text-gray-900">{stats.avgRisk}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Critical Events</p>
            <p className="text-lg font-semibold text-red-600">{stats.criticalEvents}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600">Trend</p>
            <div className="flex items-center space-x-1">
              {stats.trend > 0.5 ? (
                <TrendingUp className="h-4 w-4 text-red-500" />
              ) : stats.trend < -0.5 ? (
                <TrendingDown className="h-4 w-4 text-blue-500" />
              ) : (
                <Minus className="h-4 w-4 text-gray-500" />
              )}
              <span className="text-sm text-gray-900">
                {stats.trend > 0.5 ? 'Warming' : stats.trend < -0.5 ? 'Cooling' : 'Stable'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis
            dataKey="displayTime"
            stroke="#6B7280"
            fontSize={12}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="#6B7280"
            fontSize={12}
            domain={[0.5, 7.5]}
            tickFormatter={(value) => {
              const labels = ['', 'Cold', 'Cool', 'S.Cool', 'Neutral', 'S.Warm', 'Warm', 'Hot'];
              return labels[Math.round(value)] || '';
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Safety Zones */}
          <ReferenceLine y={3.5} stroke="#22C55E" strokeDasharray="5 5" strokeWidth={2} />
          <ReferenceLine y={4.5} stroke="#22C55E" strokeDasharray="5 5" strokeWidth={2} />

          {/* Thermal Comfort Line */}
          <Line
            type="monotone"
            dataKey="thermalComfortValue"
            stroke="#2563EB"
            strokeWidth={3}
            dot={{ r: 4, fill: '#2563EB' }}
            activeDot={{ r: 6, fill: '#2563EB' }}
            name="Thermal Comfort"
          />

          {/* Risk Level Line */}
          {showRiskLevel && (
            <Line
              type="monotone"
              dataKey="riskLevelValue"
              stroke="#EF4444"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={{ r: 3, fill: '#EF4444' }}
              yAxisId="right"
              name="Risk Level"
            />
          )}

          {/* Temperature Line */}
          {showTemperature && (
            <Line
              type="monotone"
              dataKey="temperature"
              stroke="#F97316"
              strokeWidth={2}
              dot={{ r: 2, fill: '#F97316' }}
              yAxisId="temp"
              name="Temperature (°C)"
            />
          )}

          {/* Secondary Y-axis for risk level */}
          {showRiskLevel && (
            <YAxis
              yAxisId="right"
              orientation="right"
              stroke="#EF4444"
              fontSize={12}
              domain={[0.5, 4.5]}
              tickFormatter={(value) => {
                const labels = ['', 'Low', 'Moderate', 'High', 'Critical'];
                return labels[Math.round(value)] || '';
              }}
            />
          )}

          {/* Temperature Y-axis */}
          {showTemperature && (
            <YAxis
              yAxisId="temp"
              hide
              domain={['dataMin - 2', 'dataMax + 2']}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Warning Indicators */}
      {stats && stats.criticalEvents > 0 && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-red-800">
              {stats.criticalEvents} critical event{stats.criticalEvents !== 1 ? 's' : ''} detected
            </span>
          </div>
        </div>
      )}
    </Card>
  );
}