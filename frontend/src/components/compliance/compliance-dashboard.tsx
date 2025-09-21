/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

import React, { useState, useEffect } from 'react'
import {
  Shield,
  CheckCircle,
  AlertTriangle,
  FileText,
  Download,
  Calendar,
  TrendingUp,
  Award,
  Clock,
  Users,
  Thermometer,
  Heart,
  RefreshCw,
  Filter
} from 'lucide-react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { DashboardMetrics } from '@/types'

// Mock compliance data
const complianceMetrics = {
  overall_score: 95.2,
  osha_compliance: 97.8,
  heat_stress_prevention: 94.5,
  incident_rate: 0.8, // incidents per 100 workers
  training_completion: 98.5,
  equipment_maintenance: 96.2,
  documentation_score: 99.1,
  last_inspection: '2024-08-15',
  next_inspection: '2024-12-15',
  certification_status: 'valid',
  violations: 0,
  recommendations: 3
}

const monthlyCompliance = [
  { month: 'Jan', score: 92.1, incidents: 2, training: 95 },
  { month: 'Feb', score: 93.4, incidents: 1, training: 96 },
  { month: 'Mar', score: 94.8, incidents: 0, training: 97 },
  { month: 'Apr', score: 96.2, incidents: 1, training: 98 },
  { month: 'May', score: 95.1, incidents: 1, training: 98 },
  { month: 'Jun', score: 96.8, incidents: 0, training: 99 },
  { month: 'Jul', score: 95.5, incidents: 1, training: 98 },
  { month: 'Aug', score: 97.2, incidents: 0, training: 99 },
  { month: 'Sep', score: 95.2, incidents: 1, training: 98 }
]

const complianceCategories = [
  { name: 'Heat Stress Prevention', value: 94.5, color: '#f59e0b' },
  { name: 'PPE Usage', value: 97.2, color: '#10b981' },
  { name: 'Training & Education', value: 98.5, color: '#3b82f6' },
  { name: 'Emergency Procedures', value: 96.8, color: '#8b5cf6' },
  { name: 'Documentation', value: 99.1, color: '#06b6d4' },
  { name: 'Equipment Maintenance', value: 96.2, color: '#f97316' }
]

const recentInspections = [
  {
    id: '1',
    date: '2024-08-15',
    type: 'OSHA Inspection',
    inspector: 'Safety Inspector Johnson',
    status: 'Passed',
    violations: 0,
    recommendations: 2,
    score: 97.5
  },
  {
    id: '2',
    date: '2024-07-03',
    type: 'Internal Audit',
    inspector: 'Internal Safety Team',
    status: 'Passed',
    violations: 0,
    recommendations: 1,
    score: 96.8
  },
  {
    id: '3',
    date: '2024-05-20',
    type: 'Heat Stress Assessment',
    inspector: 'Occupational Health Specialist',
    status: 'Passed',
    violations: 0,
    recommendations: 3,
    score: 94.2
  }
]

const actionItems = [
  {
    id: '1',
    title: 'Update Heat Stress Training Materials',
    category: 'Training',
    priority: 'medium',
    dueDate: '2024-10-15',
    assignee: 'HR Team',
    status: 'in_progress'
  },
  {
    id: '2',
    title: 'Install Additional Cooling Stations',
    category: 'Equipment',
    priority: 'high',
    dueDate: '2024-09-30',
    assignee: 'Facilities Team',
    status: 'pending'
  },
  {
    id: '3',
    title: 'Review Emergency Response Procedures',
    category: 'Safety',
    priority: 'medium',
    dueDate: '2024-11-01',
    assignee: 'Safety Committee',
    status: 'pending'
  }
]

export function ComplianceDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<'month' | 'quarter' | 'year'>('month')
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)

  const getComplianceLevel = (score: number) => {
    if (score >= 95) return { level: 'Excellent', color: 'text-green-600', bg: 'bg-green-50' }
    if (score >= 90) return { level: 'Good', color: 'text-blue-600', bg: 'bg-blue-50' }
    if (score >= 80) return { level: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-50' }
    return { level: 'Needs Improvement', color: 'text-red-600', bg: 'bg-red-50' }
  }

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true)
    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsGeneratingReport(false)
    // In real implementation, trigger download
    console.log('Report generated for period:', selectedPeriod)
  }

  const complianceLevel = getComplianceLevel(complianceMetrics.overall_score)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center space-x-2">
            <Shield className="h-6 w-6 text-primary" />
            <span>Compliance Dashboard</span>
          </h2>
          <p className="text-muted-foreground">
            OSHA compliance monitoring and regulatory reporting
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value as any)}
            className="text-sm border rounded px-3 py-2"
          >
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
            <option value="year">This Year</option>
          </select>
          <Button
            onClick={handleGenerateReport}
            disabled={isGeneratingReport}
          >
            {isGeneratingReport ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Generate Report
          </Button>
        </div>
      </div>

      {/* Compliance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className={`${complianceLevel.bg} border-2`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Overall Score</p>
                <div className="flex items-center space-x-2">
                  <p className="text-3xl font-bold">{complianceMetrics.overall_score}%</p>
                  <Badge variant="outline" className={complianceLevel.color}>
                    {complianceLevel.level}
                  </Badge>
                </div>
              </div>
              <Award className={`h-10 w-10 ${complianceLevel.color}`} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">OSHA Compliance</p>
                <p className="text-2xl font-bold text-green-600">{complianceMetrics.osha_compliance}%</p>
                <p className="text-xs text-muted-foreground">No violations</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Incident Rate</p>
                <p className="text-2xl font-bold">{complianceMetrics.incident_rate}</p>
                <p className="text-xs text-muted-foreground">per 100 workers</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Training Complete</p>
                <p className="text-2xl font-bold">{complianceMetrics.training_completion}%</p>
                <p className="text-xs text-muted-foreground">All workers certified</p>
              </div>
              <Users className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Compliance Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyCompliance}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Compliance Score (%)"
                />
                <Line
                  type="monotone"
                  dataKey="training"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Training Completion (%)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={complianceCategories}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {complianceCategories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Inspection History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Recent Inspections</span>
            <Badge variant="default">{complianceMetrics.violations} Violations</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentInspections.map((inspection) => (
              <div key={inspection.id} className="flex items-center justify-between p-4 rounded-lg border bg-card/50">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {inspection.status === 'Passed' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-red-500" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-semibold">{inspection.type}</h4>
                    <p className="text-sm text-muted-foreground">{inspection.inspector}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="flex items-center space-x-4">
                    <div>
                      <p className="text-sm font-medium">Score: {inspection.score}%</p>
                      <p className="text-xs text-muted-foreground">{inspection.date}</p>
                    </div>
                    <div>
                      <Badge variant={inspection.status === 'Passed' ? 'default' : 'destructive'}>
                        {inspection.status}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Action Items */}
      <Card>
        <CardHeader>
          <CardTitle>Compliance Action Items</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {actionItems.map((item) => (
              <div key={item.id} className="flex items-center justify-between p-4 rounded-lg border bg-card/50">
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0">
                    {item.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : item.status === 'in_progress' ? (
                      <Clock className="h-5 w-5 text-yellow-500" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-orange-500" />
                    )}
                  </div>
                  <div>
                    <h4 className="font-semibold">{item.title}</h4>
                    <p className="text-sm text-muted-foreground">
                      Assigned to: {item.assignee} • Due: {item.dueDate}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge
                    variant={
                      item.priority === 'high' ? 'destructive' :
                      item.priority === 'medium' ? 'default' : 'secondary'
                    }
                  >
                    {item.priority.toUpperCase()}
                  </Badge>
                  <Badge variant="outline" className="capitalize">
                    {item.status.replace('_', ' ')}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Certification Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Certification Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">OSHA Heat Stress Certification</span>
                <Badge variant="default">Valid</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Last Inspection</span>
                <span className="text-sm text-muted-foreground">{complianceMetrics.last_inspection}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Next Inspection</span>
                <span className="text-sm text-muted-foreground">{complianceMetrics.next_inspection}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Documentation Score</span>
                <span className="text-sm font-semibold text-green-600">{complianceMetrics.documentation_score}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Regulatory Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-green-50 border border-green-200">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium text-green-700">No OSHA Violations</span>
                </div>
                <p className="text-xs text-green-600 mt-1">
                  Clean record for the past 12 months
                </p>
              </div>
              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium text-blue-700">Documentation Complete</span>
                </div>
                <p className="text-xs text-blue-600 mt-1">
                  All required forms and records up to date
                </p>
              </div>
              <div className="p-3 rounded-lg bg-yellow-50 border border-yellow-200">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm font-medium text-yellow-700">3 Recommendations Pending</span>
                </div>
                <p className="text-xs text-yellow-600 mt-1">
                  Non-critical improvements for enhanced safety
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}