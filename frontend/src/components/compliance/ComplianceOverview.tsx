/**
 * HeatGuard Pro Compliance Overview
 * OSHA compliance monitoring and safety protocol tracking dashboard
 */

'use client';

import { useState, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { ComplianceReport } from '@/types/thermal-comfort';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  FileText,
  Calendar,
  TrendingUp,
  TrendingDown,
  Download,
  Eye,
  Clock,
  Users,
  Flag,
} from 'lucide-react';

interface ComplianceData {
  oshaCompliance: number; // 0-100 percentage
  totalIncidents: number;
  incidentsThisMonth: number;
  violationsCount: number;
  completedTraining: number;
  totalWorkers: number;
  lastInspection: string;
  nextInspectionDue: string;
  protocols: Array<{
    id: string;
    name: string;
    status: 'compliant' | 'warning' | 'violation';
    lastChecked: string;
    details: string;
  }>;
  recentReports: Array<{
    id: string;
    title: string;
    date: string;
    type: 'incident' | 'inspection' | 'training' | 'audit';
    status: 'pending' | 'approved' | 'needs_attention';
  }>;
  monthlyTrends: Array<{
    month: string;
    incidents: number;
    violations: number;
    complianceScore: number;
  }>;
}

interface ComplianceOverviewProps {
  data: ComplianceData;
  onGenerateReport?: () => void;
  onViewReport?: (reportId: string) => void;
  onScheduleInspection?: () => void;
  className?: string;
}

const COMPLIANCE_COLORS = {
  excellent: '#22C55E',
  good: '#84CC16',
  warning: '#F59E0B',
  poor: '#EF4444',
};

const STATUS_COLORS = {
  compliant: '#22C55E',
  warning: '#F59E0B',
  violation: '#EF4444',
  pending: '#6B7280',
  approved: '#22C55E',
  needs_attention: '#EF4444',
};

export default function ComplianceOverview({
  data,
  onGenerateReport,
  onViewReport,
  onScheduleInspection,
  className = '',
}: ComplianceOverviewProps) {
  const [selectedTimeRange, setSelectedTimeRange] = useState<'1m' | '3m' | '6m' | '1y'>('6m');

  // Calculate compliance level and trends
  const complianceAnalysis = useMemo(() => {
    const score = data.oshaCompliance;
    let level: keyof typeof COMPLIANCE_COLORS;
    let status: string;

    if (score >= 95) {
      level = 'excellent';
      status = 'Excellent Compliance';
    } else if (score >= 85) {
      level = 'good';
      status = 'Good Compliance';
    } else if (score >= 70) {
      level = 'warning';
      status = 'Needs Attention';
    } else {
      level = 'poor';
      status = 'Poor Compliance';
    }

    // Calculate trends
    const recentMonths = data.monthlyTrends.slice(-3);
    const oldMonths = data.monthlyTrends.slice(-6, -3);

    const recentAvg = recentMonths.reduce((sum, m) => sum + m.complianceScore, 0) / recentMonths.length;
    const oldAvg = oldMonths.reduce((sum, m) => sum + m.complianceScore, 0) / oldMonths.length;
    const trend = recentAvg - oldAvg;

    return {
      level,
      status,
      color: COMPLIANCE_COLORS[level],
      trend,
      isImproving: trend > 2,
      isDeclining: trend < -2,
    };
  }, [data.oshaCompliance, data.monthlyTrends]);

  // Protocol status summary
  const protocolSummary = useMemo(() => {
    const summary = {
      compliant: 0,
      warning: 0,
      violation: 0,
    };

    data.protocols.forEach(protocol => {
      summary[protocol.status]++;
    });

    return summary;
  }, [data.protocols]);

  // Training compliance rate
  const trainingRate = (data.completedTraining / data.totalWorkers) * 100;

  // Days until next inspection
  const daysUntilInspection = Math.ceil(
    (new Date(data.nextInspectionDue).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
  );

  // Pie chart data for protocol compliance
  const pieData = [
    { name: 'Compliant', value: protocolSummary.compliant, color: STATUS_COLORS.compliant },
    { name: 'Warning', value: protocolSummary.warning, color: STATUS_COLORS.warning },
    { name: 'Violation', value: protocolSummary.violation, color: STATUS_COLORS.violation },
  ];

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between space-x-4">
              <div className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600">{entry.dataKey}:</span>
              </div>
              <span className="text-sm font-medium text-gray-900">{entry.value}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">OSHA Compliance Overview</h2>
          <p className="text-gray-600 mt-1">Safety protocols and regulatory compliance monitoring</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={onScheduleInspection}>
            <Calendar className="h-4 w-4 mr-2" />
            Schedule Inspection
          </Button>
          <Button onClick={onGenerateReport}>
            <FileText className="h-4 w-4 mr-2" />
            Generate Report
          </Button>
        </div>
      </div>

      {/* Compliance Score Card */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Overall Compliance Score</h3>
          <Badge
            style={{
              backgroundColor: complianceAnalysis.color + '20',
              borderColor: complianceAnalysis.color,
              color: complianceAnalysis.color,
            }}
          >
            {complianceAnalysis.status}
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Compliance Score Gauge */}
          <div className="col-span-1">
            <div className="relative w-32 h-32 mx-auto">
              <svg className="transform -rotate-90 w-32 h-32">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="#E5E7EB"
                  strokeWidth="8"
                  fill="transparent"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke={complianceAnalysis.color}
                  strokeWidth="8"
                  fill="transparent"
                  strokeDasharray={`${(data.oshaCompliance / 100) * 351.86} 351.86`}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{data.oshaCompliance}%</p>
                  <p className="text-xs text-gray-500">Compliance</p>
                </div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="col-span-2 grid grid-cols-2 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                <span className="text-sm text-gray-600">Incidents (This Month)</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{data.incidentsThisMonth}</p>
              <p className="text-xs text-gray-500">Total this year: {data.totalIncidents}</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Flag className="h-5 w-5 text-orange-500" />
                <span className="text-sm text-gray-600">Violations</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{data.violationsCount}</p>
              <p className="text-xs text-gray-500">Active violations</p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Users className="h-5 w-5 text-blue-500" />
                <span className="text-sm text-gray-600">Training Rate</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{trainingRate.toFixed(0)}%</p>
              <p className="text-xs text-gray-500">
                {data.completedTraining}/{data.totalWorkers} workers
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="h-5 w-5 text-purple-500" />
                <span className="text-sm text-gray-600">Next Inspection</span>
              </div>
              <p className="text-2xl font-bold text-gray-900">{daysUntilInspection}</p>
              <p className="text-xs text-gray-500">days remaining</p>
            </div>
          </div>
        </div>

        {/* Trend Indicator */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {complianceAnalysis.isImproving ? (
              <TrendingUp className="h-5 w-5 text-green-500" />
            ) : complianceAnalysis.isDeclining ? (
              <TrendingDown className="h-5 w-5 text-red-500" />
            ) : (
              <div className="h-5 w-5" />
            )}
            <span className="text-sm text-gray-600">
              {complianceAnalysis.isImproving
                ? 'Compliance score is improving'
                : complianceAnalysis.isDeclining
                ? 'Compliance score is declining'
                : 'Compliance score is stable'
              } ({complianceAnalysis.trend > 0 ? '+' : ''}{complianceAnalysis.trend.toFixed(1)}%)
            </span>
          </div>
        </div>
      </Card>

      {/* Protocol Status and Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Safety Protocols Status */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Safety Protocols</h3>
            <Badge variant="outline">
              {data.protocols.length} protocols
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Protocol Status Pie Chart */}
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Protocol Legend */}
            <div className="space-y-3">
              {pieData.map((entry, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: entry.color }}
                    />
                    <span className="text-sm text-gray-700">{entry.name}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {entry.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Protocol Issues */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Recent Issues</h4>
            <div className="space-y-2">
              {data.protocols
                .filter(p => p.status !== 'compliant')
                .slice(0, 3)
                .map(protocol => (
                  <div key={protocol.id} className="flex items-start space-x-3 p-2 bg-gray-50 rounded">
                    <div
                      className="w-2 h-2 rounded-full mt-1.5"
                      style={{ backgroundColor: STATUS_COLORS[protocol.status] }}
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{protocol.name}</p>
                      <p className="text-xs text-gray-600">{protocol.details}</p>
                      <p className="text-xs text-gray-500">
                        Last checked: {new Date(protocol.lastChecked).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </Card>

        {/* Monthly Trends */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Monthly Trends</h3>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.monthlyTrends.slice(-6)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="incidents" fill="#EF4444" name="Incidents" />
                <Bar dataKey="violations" fill="#F59E0B" name="Violations" />
                <Bar
                  dataKey="complianceScore"
                  fill="#22C55E"
                  name="Compliance %"
                  yAxisId="compliance"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Recent Reports */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Reports</h3>
          <Button variant="outline" size="sm" onClick={onGenerateReport}>
            <Download className="h-4 w-4 mr-2" />
            Export All
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 text-sm font-medium text-gray-600">Title</th>
                <th className="text-left py-2 text-sm font-medium text-gray-600">Type</th>
                <th className="text-left py-2 text-sm font-medium text-gray-600">Date</th>
                <th className="text-left py-2 text-sm font-medium text-gray-600">Status</th>
                <th className="text-left py-2 text-sm font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.recentReports.map(report => (
                <tr key={report.id} className="border-b border-gray-100">
                  <td className="py-3 text-sm text-gray-900">{report.title}</td>
                  <td className="py-3">
                    <Badge variant="outline" className="text-xs">
                      {report.type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="py-3 text-sm text-gray-600">
                    {new Date(report.date).toLocaleDateString()}
                  </td>
                  <td className="py-3">
                    <Badge
                      style={{
                        backgroundColor: STATUS_COLORS[report.status] + '20',
                        borderColor: STATUS_COLORS[report.status],
                        color: STATUS_COLORS[report.status],
                      }}
                    >
                      {report.status.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="py-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewReport?.(report.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Compliance Alerts */}
      {data.violationsCount > 0 && (
        <Alert className="border-orange-200 bg-orange-50">
          <AlertTriangle className="h-4 w-4 text-orange-600" />
          <AlertDescription className="text-orange-800">
            <strong>Active Violations:</strong> {data.violationsCount} compliance violations require immediate attention.
            <Button variant="link" className="p-0 ml-2 text-orange-700 underline">
              View Details
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {daysUntilInspection <= 7 && daysUntilInspection > 0 && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <Calendar className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            <strong>Upcoming Inspection:</strong> OSHA inspection due in {daysUntilInspection} days.
            <Button variant="link" className="p-0 ml-2 text-yellow-700 underline">
              Prepare Checklist
            </Button>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}