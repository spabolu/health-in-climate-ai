/**
 * HeatGuard Pro Risk Analysis Chart
 * Comprehensive risk visualization showing historical trends, predictions, and safety assessments
 */

'use client';

import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { ThermalComfortPrediction } from '@/types/thermal-comfort';
import {
  AlertTriangle,
  Shield,
  TrendingUp,
  TrendingDown,
  Target,
  Download,
  BarChart3,
  Activity,
} from 'lucide-react';

interface RiskDataPoint {
  timestamp: string;
  riskLevel: 'low' | 'moderate' | 'high' | 'critical';
  riskScore: number; // 0-100
  thermalComfort: string;
  confidence: number;
  temperature: number;
  humidity: number;
  heartRate?: number;
  incidentOccurred?: boolean;
  predictedRisk?: number; // Future risk prediction
  workerId?: string;
  location?: string;
}

interface RiskAnalysisChartProps {
  data: RiskDataPoint[];
  title?: string;
  height?: number;
  showPredictions?: boolean;
  showIncidents?: boolean;
  showConfidenceBands?: boolean;
  timeRange?: '1h' | '4h' | '12h' | '24h' | '7d' | '30d';
  onExport?: () => void;
  className?: string;
}

const RISK_LEVELS = {
  low: { value: 25, color: '#22C55E', label: 'Low Risk' },
  moderate: { value: 50, color: '#FBBF24', label: 'Moderate Risk' },
  high: { value: 75, color: '#F97316', label: 'High Risk' },
  critical: { value: 100, color: '#EF4444', label: 'Critical Risk' },
};

const RISK_THRESHOLDS = [
  { value: 25, label: 'Low', color: '#22C55E' },
  { value: 50, label: 'Moderate', color: '#FBBF24' },
  { value: 75, label: 'High', color: '#F97316' },
  { value: 100, label: 'Critical', color: '#EF4444' },
];

export default function RiskAnalysisChart({
  data,
  title = 'Risk Analysis & Predictions',
  height = 500,
  showPredictions = true,
  showIncidents = true,
  showConfidenceBands = true,
  timeRange = '24h',
  onExport,
  className = '',
}: RiskAnalysisChartProps) {
  // Process and enhance data
  const chartData = useMemo(() => {
    const now = new Date();
    const timeRanges = {
      '1h': 60 * 60 * 1000,
      '4h': 4 * 60 * 60 * 1000,
      '12h': 12 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000,
    };

    const cutoffTime = now.getTime() - timeRanges[timeRange];

    return data
      .filter(item => new Date(item.timestamp).getTime() >= cutoffTime)
      .map((item, index, array) => {
        // Calculate moving average for smoother trend line
        const windowSize = Math.min(5, array.length);
        const start = Math.max(0, index - Math.floor(windowSize / 2));
        const end = Math.min(array.length, start + windowSize);
        const window = array.slice(start, end);
        const movingAvgRisk = window.reduce((sum, d) => sum + d.riskScore, 0) / window.length;

        // Calculate confidence bands
        const confidenceLower = Math.max(0, item.riskScore - (1 - item.confidence) * 50);
        const confidenceUpper = Math.min(100, item.riskScore + (1 - item.confidence) * 50);

        // Predict future risk based on trend (simplified)
        let predictedRisk;
        if (showPredictions && index > 2) {
          const recentTrend = array.slice(Math.max(0, index - 3), index + 1);
          const trendSlope = (recentTrend[recentTrend.length - 1].riskScore - recentTrend[0].riskScore) / recentTrend.length;
          predictedRisk = Math.max(0, Math.min(100, item.riskScore + trendSlope * 2));
        }

        return {
          ...item,
          movingAvgRisk,
          confidenceLower,
          confidenceUpper,
          predictedRisk,
          riskLevelValue: RISK_LEVELS[item.riskLevel].value,
          displayTime: new Date(item.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
          displayDate: new Date(item.timestamp).toLocaleDateString(),
          fullTimestamp: new Date(item.timestamp).toLocaleString(),
        };
      })
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
  }, [data, timeRange, showPredictions]);

  // Calculate comprehensive statistics
  const analytics = useMemo(() => {
    if (chartData.length === 0) return null;

    const riskScores = chartData.map(d => d.riskScore);
    const avgRisk = riskScores.reduce((sum, val) => sum + val, 0) / riskScores.length;
    const maxRisk = Math.max(...riskScores);
    const minRisk = Math.min(...riskScores);

    // Risk distribution
    const riskDistribution = {
      low: chartData.filter(d => d.riskLevel === 'low').length,
      moderate: chartData.filter(d => d.riskLevel === 'moderate').length,
      high: chartData.filter(d => d.riskLevel === 'high').length,
      critical: chartData.filter(d => d.riskLevel === 'critical').length,
    };

    // Incidents
    const incidents = chartData.filter(d => d.incidentOccurred).length;
    const incidentRate = incidents / chartData.length;

    // Trend analysis
    const trend = riskScores.length > 1
      ? riskScores[riskScores.length - 1] - riskScores[0]
      : 0;

    // Risk escalation events (when risk jumps significantly)
    const escalations = chartData.filter((d, i) => {
      if (i === 0) return false;
      return d.riskScore - chartData[i - 1].riskScore > 20;
    }).length;

    // Average confidence
    const avgConfidence = chartData.reduce((sum, d) => sum + d.confidence, 0) / chartData.length;

    // Time spent in each risk level
    const totalTime = chartData.length;
    const timeDistribution = {
      low: (riskDistribution.low / totalTime) * 100,
      moderate: (riskDistribution.moderate / totalTime) * 100,
      high: (riskDistribution.high / totalTime) * 100,
      critical: (riskDistribution.critical / totalTime) * 100,
    };

    return {
      avgRisk: avgRisk.toFixed(1),
      maxRisk: maxRisk.toFixed(1),
      minRisk: minRisk.toFixed(1),
      riskDistribution,
      timeDistribution,
      incidents,
      incidentRate: (incidentRate * 100).toFixed(1),
      trend,
      escalations,
      avgConfidence: (avgConfidence * 100).toFixed(1),
      dataPoints: chartData.length,
    };
  }, [chartData]);

  // Get current risk assessment
  const getCurrentRiskLevel = () => {
    if (chartData.length === 0) return 'unknown';
    const latest = chartData[chartData.length - 1];
    return latest.riskLevel;
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg min-w-[250px]">
          <p className="font-medium text-gray-900 mb-3">
            {data.fullTimestamp}
          </p>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Risk Score:</span>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-900">
                  {data.riskScore.toFixed(0)}%
                </span>
                <Badge
                  variant={data.riskLevel === 'critical' ? 'destructive' : 'secondary'}
                  style={{
                    backgroundColor: RISK_LEVELS[data.riskLevel].color + '20',
                    borderColor: RISK_LEVELS[data.riskLevel].color,
                    color: RISK_LEVELS[data.riskLevel].color
                  }}
                >
                  {RISK_LEVELS[data.riskLevel].label}
                </Badge>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Confidence:</span>
              <span className="text-sm font-medium text-gray-900">
                {(data.confidence * 100).toFixed(0)}%
              </span>
            </div>
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
            {data.heartRate && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Heart Rate:</span>
                <span className="text-sm font-medium text-gray-900">
                  {data.heartRate} BPM
                </span>
              </div>
            )}
            {data.predictedRisk && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Predicted Risk:</span>
                <span className="text-sm font-medium text-blue-600">
                  {data.predictedRisk.toFixed(0)}%
                </span>
              </div>
            )}
            {data.incidentOccurred && (
              <div className="text-center">
                <Badge variant="destructive">INCIDENT OCCURRED</Badge>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  const currentRiskLevel = getCurrentRiskLevel();

  if (chartData.length === 0) {
    return (
      <Card className={`p-6 ${className}`}>
        <div className="text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">No risk data</p>
          <p className="text-gray-600">No risk analysis data available for the selected time range</p>
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
            <p className="text-sm text-gray-600">Analysis for last {timeRange}</p>
            <Badge
              variant={currentRiskLevel === 'critical' ? 'destructive' : 'secondary'}
              style={{
                backgroundColor: RISK_LEVELS[currentRiskLevel]?.color + '20',
                borderColor: RISK_LEVELS[currentRiskLevel]?.color,
                color: RISK_LEVELS[currentRiskLevel]?.color
              }}
            >
              Current: {RISK_LEVELS[currentRiskLevel]?.label || 'Unknown'}
            </Badge>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {analytics && (
            <div className="flex items-center space-x-1 text-sm text-gray-600">
              {analytics.trend > 5 ? (
                <TrendingUp className="h-4 w-4 text-red-500" />
              ) : analytics.trend < -5 ? (
                <TrendingDown className="h-4 w-4 text-green-500" />
              ) : (
                <Activity className="h-4 w-4 text-gray-500" />
              )}
              <span>
                {analytics.trend > 5 ? 'Increasing' :
                 analytics.trend < -5 ? 'Decreasing' : 'Stable'}
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

      {/* Risk Overview */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center space-x-2">
              <Target className="h-4 w-4 text-gray-600" />
              <span className="text-xs text-gray-600">Avg Risk</span>
            </div>
            <p className="text-lg font-semibold text-gray-900">{analytics.avgRisk}%</p>
            <p className="text-xs text-gray-500">Range: {analytics.minRisk}-{analytics.maxRisk}%</p>
          </div>

          <div className="bg-red-50 rounded-lg p-3 border border-red-200">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <span className="text-xs text-red-600">Incidents</span>
            </div>
            <p className="text-lg font-semibold text-red-900">{analytics.incidents}</p>
            <p className="text-xs text-red-700">{analytics.incidentRate}% rate</p>
          </div>

          <div className="bg-orange-50 rounded-lg p-3 border border-orange-200">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-orange-600" />
              <span className="text-xs text-orange-600">Escalations</span>
            </div>
            <p className="text-lg font-semibold text-orange-900">{analytics.escalations}</p>
            <p className="text-xs text-orange-700">Risk spikes</p>
          </div>

          <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-blue-600" />
              <span className="text-xs text-blue-600">Confidence</span>
            </div>
            <p className="text-lg font-semibold text-blue-900">{analytics.avgConfidence}%</p>
            <p className="text-xs text-blue-700">Avg accuracy</p>
          </div>
        </div>
      )}

      {/* Risk Time Distribution */}
      {analytics && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Risk Level Distribution</h4>
          <div className="grid grid-cols-4 gap-2 mb-2">
            {Object.entries(analytics.timeDistribution).map(([level, percentage]) => (
              <div key={level} className="text-center">
                <div className="text-xs text-gray-600 mb-1">
                  {RISK_LEVELS[level as keyof typeof RISK_LEVELS].label}
                </div>
                <Progress
                  value={percentage}
                  className="h-2"
                  style={{
                    '--progress-background': RISK_LEVELS[level as keyof typeof RISK_LEVELS].color,
                  } as React.CSSProperties}
                />
                <div className="text-xs text-gray-500 mt-1">{percentage.toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critical Risk Warning */}
      {currentRiskLevel === 'critical' && (
        <Alert className="mb-6 border-red-500 bg-red-100">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800 font-medium">
            CRITICAL RISK LEVEL: Immediate intervention required to prevent heat-related incidents.
          </AlertDescription>
        </Alert>
      )}

      {/* Risk Analysis Chart */}
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
            domain={[0, 100]}
            label={{ value: 'Risk Score (%)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Risk threshold lines */}
          {RISK_THRESHOLDS.map(threshold => (
            <ReferenceLine
              key={threshold.value}
              y={threshold.value}
              stroke={threshold.color}
              strokeDasharray="5 5"
              strokeOpacity={0.7}
            />
          ))}

          {/* Confidence bands */}
          {showConfidenceBands && (
            <Area
              type="monotone"
              dataKey="confidenceUpper"
              stroke="transparent"
              fill="#3B82F6"
              fillOpacity={0.1}
            />
          )}

          {/* Main risk score line */}
          <Line
            type="monotone"
            dataKey="riskScore"
            stroke="#EF4444"
            strokeWidth={3}
            dot={{ r: 4, fill: '#EF4444' }}
            activeDot={{ r: 6, fill: '#EF4444' }}
            name="Risk Score"
          />

          {/* Moving average trend line */}
          <Line
            type="monotone"
            dataKey="movingAvgRisk"
            stroke="#6B7280"
            strokeWidth={2}
            strokeDasharray="8 4"
            dot={false}
            name="Trend"
          />

          {/* Predicted risk line */}
          {showPredictions && (
            <Line
              type="monotone"
              dataKey="predictedRisk"
              stroke="#2563EB"
              strokeWidth={2}
              strokeDasharray="4 4"
              dot={{ r: 2, fill: '#2563EB' }}
              name="Predicted"
              connectNulls={false}
            />
          )}

          {/* Incident markers */}
          {showIncidents && (
            <Scatter
              dataKey="riskScore"
              shape={(props: any) => {
                if (!props.payload.incidentOccurred) return null;
                return (
                  <circle
                    cx={props.cx}
                    cy={props.cy}
                    r={8}
                    fill="#DC2626"
                    stroke="#FFFFFF"
                    strokeWidth={2}
                  />
                );
              }}
              name="Incidents"
            />
          )}

          {/* Temperature correlation bars (scaled and offset) */}
          <Bar
            dataKey="temperature"
            fill="#F97316"
            fillOpacity={0.2}
            yAxisId="temp"
            name="Temperature"
          />

          {/* Hidden Y-axis for temperature */}
          <YAxis yAxisId="temp" hide domain={[0, 50]} />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Risk Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Risk Levels Summary */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Risk Level Breakdown</h4>
            <div className="space-y-2">
              {Object.entries(analytics?.riskDistribution || {}).map(([level, count]) => {
                const config = RISK_LEVELS[level as keyof typeof RISK_LEVELS];
                const percentage = analytics ? (count / analytics.dataPoints * 100).toFixed(1) : '0';
                return (
                  <div key={level} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: config.color }}
                      />
                      <span className="text-sm text-gray-700">{config.label}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-medium text-gray-900">{count}</span>
                      <span className="text-gray-500 ml-1">({percentage}%)</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Key Insights */}
          <div>
            <h4 className="font-medium text-gray-900 mb-3">Key Insights</h4>
            <div className="space-y-2 text-sm text-gray-700">
              {analytics && analytics.trend > 10 && (
                <div className="flex items-center space-x-2 text-red-700">
                  <TrendingUp className="h-4 w-4" />
                  <span>Risk levels are increasing significantly</span>
                </div>
              )}
              {analytics && analytics.escalations > 0 && (
                <div className="flex items-center space-x-2 text-orange-700">
                  <AlertTriangle className="h-4 w-4" />
                  <span>{analytics.escalations} rapid risk escalation events detected</span>
                </div>
              )}
              {analytics && parseFloat(analytics.incidentRate) > 5 && (
                <div className="flex items-center space-x-2 text-red-700">
                  <AlertTriangle className="h-4 w-4" />
                  <span>High incident rate: {analytics.incidentRate}%</span>
                </div>
              )}
              {analytics && parseFloat(analytics.avgConfidence) < 70 && (
                <div className="flex items-center space-x-2 text-yellow-700">
                  <Shield className="h-4 w-4" />
                  <span>Low prediction confidence: {analytics.avgConfidence}%</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}