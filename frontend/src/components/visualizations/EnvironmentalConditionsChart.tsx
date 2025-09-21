/**
 * HeatGuard Pro Environmental Conditions Chart
 * Visualization of environmental conditions with safety thresholds and heat index calculations
 */

'use client';

import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Bar,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Thermometer,
  Droplets,
  Wind,
  Sun,
  AlertTriangle,
  Download,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';

interface EnvironmentalDataPoint {
  timestamp: string;
  temperature: number; // °C
  humidity: number; // %
  airVelocity?: number; // m/s
  solarRadiation?: number; // W/m²
  heatIndex?: number; // °C
  wbgt?: number; // Wet Bulb Globe Temperature
  location?: string;
}

interface EnvironmentalConditionsChartProps {
  data: EnvironmentalDataPoint[];
  title?: string;
  height?: number;
  showHeatIndex?: boolean;
  showWBGT?: boolean;
  showSolarRadiation?: boolean;
  timeRange?: '1h' | '4h' | '12h' | '24h' | '7d';
  onExport?: () => void;
  className?: string;
}

// Safety thresholds based on OSHA and NIOSH guidelines
const SAFETY_THRESHOLDS = {
  temperature: {
    safe: 26,        // 26°C - comfortable working temperature
    caution: 30,     // 30°C - caution level
    danger: 35,      // 35°C - danger level
    extreme: 40,     // 40°C - extreme danger
  },
  humidity: {
    safe: 60,        // 60% - comfortable humidity
    caution: 70,     // 70% - increased discomfort
    danger: 80,      // 80% - high risk
  },
  heatIndex: {
    safe: 27,        // 27°C - safe
    caution: 32,     // 32°C - extreme caution
    danger: 40,      // 40°C - danger
    extreme: 51,     // 51°C - extreme danger
  },
  wbgt: {
    safe: 28,        // 28°C - safe for moderate work
    caution: 30,     // 30°C - caution
    danger: 32,      // 32°C - high risk
  },
};

export default function EnvironmentalConditionsChart({
  data,
  title = 'Environmental Conditions',
  height = 400,
  showHeatIndex = true,
  showWBGT = true,
  showSolarRadiation = false,
  timeRange = '12h',
  onExport,
  className = '',
}: EnvironmentalConditionsChartProps) {
  // Process and calculate additional metrics
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
      .map(item => {
        // Calculate heat index if not provided
        let heatIndex = item.heatIndex;
        if (!heatIndex && item.temperature && item.humidity) {
          heatIndex = calculateHeatIndex(item.temperature, item.humidity);
        }

        // Calculate apparent temperature considering wind
        let apparentTemp = item.temperature;
        if (item.airVelocity) {
          apparentTemp = calculateApparentTemperature(
            item.temperature,
            item.humidity,
            item.airVelocity
          );
        }

        return {
          ...item,
          heatIndex,
          apparentTemp,
          displayTime: new Date(item.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          displayDate: new Date(item.timestamp).toLocaleDateString(),
        };
      })
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [data, timeRange]);

  // Calculate statistics and safety assessments
  const stats = useMemo(() => {
    if (chartData.length === 0) return null;

    const temps = chartData.map(d => d.temperature);
    const humidities = chartData.map(d => d.humidity);
    const heatIndexes = chartData.map(d => d.heatIndex).filter(h => h !== undefined) as number[];

    const avgTemp = temps.reduce((sum, val) => sum + val, 0) / temps.length;
    const avgHumidity = humidities.reduce((sum, val) => sum + val, 0) / humidities.length;
    const avgHeatIndex = heatIndexes.length > 0
      ? heatIndexes.reduce((sum, val) => sum + val, 0) / heatIndexes.length
      : avgTemp;

    const maxTemp = Math.max(...temps);
    const maxHumidity = Math.max(...humidities);
    const maxHeatIndex = heatIndexes.length > 0 ? Math.max(...heatIndexes) : maxTemp;

    // Calculate safety levels
    const dangerousConditions = chartData.filter(d =>
      d.temperature > SAFETY_THRESHOLDS.temperature.danger ||
      d.humidity > SAFETY_THRESHOLDS.humidity.danger ||
      (d.heatIndex && d.heatIndex > SAFETY_THRESHOLDS.heatIndex.danger)
    ).length;

    const cautionConditions = chartData.filter(d =>
      (d.temperature > SAFETY_THRESHOLDS.temperature.caution && d.temperature <= SAFETY_THRESHOLDS.temperature.danger) ||
      (d.humidity > SAFETY_THRESHOLDS.humidity.caution && d.humidity <= SAFETY_THRESHOLDS.humidity.danger) ||
      (d.heatIndex && d.heatIndex > SAFETY_THRESHOLDS.heatIndex.caution && d.heatIndex <= SAFETY_THRESHOLDS.heatIndex.danger)
    ).length;

    // Temperature trend
    const tempTrend = temps.length > 1 ? temps[temps.length - 1] - temps[0] : 0;

    return {
      avgTemp: avgTemp.toFixed(1),
      avgHumidity: avgHumidity.toFixed(0),
      avgHeatIndex: avgHeatIndex.toFixed(1),
      maxTemp: maxTemp.toFixed(1),
      maxHumidity: maxHumidity.toFixed(0),
      maxHeatIndex: maxHeatIndex.toFixed(1),
      dangerousConditions,
      cautionConditions,
      tempTrend,
      dataPoints: chartData.length,
    };
  }, [chartData]);

  // Get current safety level
  const getCurrentSafetyLevel = () => {
    if (chartData.length === 0) return 'unknown';

    const latest = chartData[chartData.length - 1];

    if (
      latest.temperature > SAFETY_THRESHOLDS.temperature.extreme ||
      (latest.heatIndex && latest.heatIndex > SAFETY_THRESHOLDS.heatIndex.extreme)
    ) {
      return 'extreme';
    } else if (
      latest.temperature > SAFETY_THRESHOLDS.temperature.danger ||
      latest.humidity > SAFETY_THRESHOLDS.humidity.danger ||
      (latest.heatIndex && latest.heatIndex > SAFETY_THRESHOLDS.heatIndex.danger)
    ) {
      return 'danger';
    } else if (
      latest.temperature > SAFETY_THRESHOLDS.temperature.caution ||
      latest.humidity > SAFETY_THRESHOLDS.humidity.caution ||
      (latest.heatIndex && latest.heatIndex > SAFETY_THRESHOLDS.heatIndex.caution)
    ) {
      return 'caution';
    }
    return 'safe';
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">
            {data.displayTime} - {data.displayDate}
          </p>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Temperature:</span>
              <span className="text-sm font-medium text-gray-900">
                {data.temperature.toFixed(1)}°C
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Humidity:</span>
              <span className="text-sm font-medium text-gray-900">
                {data.humidity.toFixed(0)}%
              </span>
            </div>
            {data.heatIndex && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Heat Index:</span>
                <span className="text-sm font-medium text-orange-600">
                  {data.heatIndex.toFixed(1)}°C
                </span>
              </div>
            )}
            {data.airVelocity && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Wind Speed:</span>
                <span className="text-sm font-medium text-gray-900">
                  {data.airVelocity.toFixed(1)} m/s
                </span>
              </div>
            )}
            {data.wbgt && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">WBGT:</span>
                <span className="text-sm font-medium text-purple-600">
                  {data.wbgt.toFixed(1)}°C
                </span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const safetyLevel = getCurrentSafetyLevel();
  const safetyColors = {
    safe: 'text-green-600 bg-green-50 border-green-200',
    caution: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    danger: 'text-red-600 bg-red-50 border-red-200',
    extreme: 'text-red-800 bg-red-100 border-red-300',
    unknown: 'text-gray-600 bg-gray-50 border-gray-200',
  };

  if (chartData.length === 0) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <Thermometer className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">No environmental data</p>
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
          <div className="flex items-center space-x-2 mt-1">
            <p className="text-sm text-gray-600">Last {timeRange}</p>
            <Badge
              className={`${safetyColors[safetyLevel]} border`}
            >
              {safetyLevel.charAt(0).toUpperCase() + safetyLevel.slice(1)}
            </Badge>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {stats && stats.tempTrend !== 0 && (
            <div className="flex items-center space-x-1 text-sm text-gray-600">
              {stats.tempTrend > 0 ? (
                <TrendingUp className="h-4 w-4 text-red-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-blue-500" />
              )}
              <span>{Math.abs(stats.tempTrend).toFixed(1)}°C</span>
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

      {/* Current Conditions Summary */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
            <div className="flex items-center space-x-2">
              <Thermometer className="h-4 w-4 text-orange-600" />
              <span className="text-xs text-orange-600">Avg Temperature</span>
            </div>
            <p className="text-lg font-semibold text-orange-900">{stats.avgTemp}°C</p>
            <p className="text-xs text-orange-700">Max: {stats.maxTemp}°C</p>
          </div>

          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="flex items-center space-x-2">
              <Droplets className="h-4 w-4 text-blue-600" />
              <span className="text-xs text-blue-600">Avg Humidity</span>
            </div>
            <p className="text-lg font-semibold text-blue-900">{stats.avgHumidity}%</p>
            <p className="text-xs text-blue-700">Max: {stats.maxHumidity}%</p>
          </div>

          <div className="bg-red-50 rounded-lg p-3 border border-red-200">
            <div className="flex items-center space-x-2">
              <Sun className="h-4 w-4 text-red-600" />
              <span className="text-xs text-red-600">Avg Heat Index</span>
            </div>
            <p className="text-lg font-semibold text-red-900">{stats.avgHeatIndex}°C</p>
            <p className="text-xs text-red-700">Max: {stats.maxHeatIndex}°C</p>
          </div>

          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-gray-600" />
              <span className="text-xs text-gray-600">Risk Events</span>
            </div>
            <p className="text-lg font-semibold text-gray-900">{stats.dangerousConditions}</p>
            <p className="text-xs text-gray-700">Caution: {stats.cautionConditions}</p>
          </div>
        </div>
      )}

      {/* Safety Warnings */}
      {safetyLevel === 'extreme' && (
        <Alert className="mb-6 border-red-500 bg-red-100">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800 font-medium">
            EXTREME HEAT WARNING: Conditions pose severe risk to worker health. Consider suspending outdoor work.
          </AlertDescription>
        </Alert>
      )}

      {safetyLevel === 'danger' && (
        <Alert className="mb-6 border-orange-500 bg-orange-100">
          <AlertTriangle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800 font-medium">
            DANGEROUS CONDITIONS: High risk of heat-related illness. Implement heat safety protocols immediately.
          </AlertDescription>
        </Alert>
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
            yAxisId="temp"
            stroke="#F97316"
            fontSize={12}
            label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }}
          />
          <YAxis
            yAxisId="humidity"
            orientation="right"
            stroke="#3B82F6"
            fontSize={12}
            label={{ value: 'Humidity (%)', angle: 90, position: 'insideRight' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Safety threshold lines */}
          <ReferenceLine
            yAxisId="temp"
            y={SAFETY_THRESHOLDS.temperature.caution}
            stroke="#FBBF24"
            strokeDasharray="5 5"
            strokeWidth={2}
          />
          <ReferenceLine
            yAxisId="temp"
            y={SAFETY_THRESHOLDS.temperature.danger}
            stroke="#EF4444"
            strokeDasharray="5 5"
            strokeWidth={2}
          />

          {/* Temperature area */}
          <Area
            yAxisId="temp"
            type="monotone"
            dataKey="temperature"
            stroke="#F97316"
            fill="#F97316"
            fillOpacity={0.1}
            strokeWidth={2}
            name="Temperature"
          />

          {/* Heat Index line */}
          {showHeatIndex && (
            <Line
              yAxisId="temp"
              type="monotone"
              dataKey="heatIndex"
              stroke="#DC2626"
              strokeWidth={3}
              strokeDasharray="8 4"
              dot={{ r: 3, fill: '#DC2626' }}
              name="Heat Index"
            />
          )}

          {/* WBGT line */}
          {showWBGT && (
            <Line
              yAxisId="temp"
              type="monotone"
              dataKey="wbgt"
              stroke="#7C3AED"
              strokeWidth={2}
              dot={{ r: 2, fill: '#7C3AED' }}
              name="WBGT"
            />
          )}

          {/* Humidity bars */}
          <Bar
            yAxisId="humidity"
            dataKey="humidity"
            fill="#3B82F6"
            fillOpacity={0.3}
            name="Humidity"
          />

          {/* Solar radiation area */}
          {showSolarRadiation && (
            <Area
              yAxisId="solar"
              type="monotone"
              dataKey="solarRadiation"
              stroke="#FBBF24"
              fill="#FBBF24"
              fillOpacity={0.2}
              name="Solar Radiation"
            />
          )}

          {/* Hidden Y-axis for solar radiation */}
          {showSolarRadiation && (
            <YAxis yAxisId="solar" hide />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Risk Assessment Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-sm text-gray-600">Safe Conditions</p>
            <p className="text-2xl font-bold text-green-600">
              {stats ? Math.max(0, stats.dataPoints - stats.cautionConditions - stats.dangerousConditions) : 0}
            </p>
            <p className="text-xs text-gray-500">data points</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Caution Conditions</p>
            <p className="text-2xl font-bold text-yellow-600">{stats?.cautionConditions || 0}</p>
            <p className="text-xs text-gray-500">data points</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Dangerous Conditions</p>
            <p className="text-2xl font-bold text-red-600">{stats?.dangerousConditions || 0}</p>
            <p className="text-xs text-gray-500">data points</p>
          </div>
        </div>
      </div>
    </Card>
  );
}

// Heat index calculation function
function calculateHeatIndex(tempC: number, humidity: number): number {
  // Convert Celsius to Fahrenheit for calculation
  const tempF = (tempC * 9/5) + 32;

  // Simplified heat index calculation (Rothfusz regression)
  const hi = -42.379 + 2.04901523 * tempF + 10.14333127 * humidity
    - 0.22475541 * tempF * humidity - 0.00683783 * tempF * tempF
    - 0.05481717 * humidity * humidity + 0.00122874 * tempF * tempF * humidity
    + 0.00085282 * tempF * humidity * humidity - 0.00000199 * tempF * tempF * humidity * humidity;

  // Convert back to Celsius
  return (hi - 32) * 5/9;
}

// Apparent temperature calculation with wind
function calculateApparentTemperature(tempC: number, humidity: number, windSpeed: number): number {
  // Australian Apparent Temperature formula
  const e = (humidity / 100) * 6.105 * Math.exp(17.27 * tempC / (237.7 + tempC));
  return tempC + 0.33 * e - 0.7 * windSpeed - 4;
}