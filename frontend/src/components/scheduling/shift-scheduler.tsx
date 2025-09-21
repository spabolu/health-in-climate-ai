'use client'

import React, { useState, useEffect } from 'react'
import {
  Calendar,
  Clock,
  Users,
  Thermometer,
  AlertTriangle,
  CheckCircle,
  Plus,
  Edit,
  Trash2,
  MapPin,
  Heart,
  TrendingUp,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Worker } from '@/types'

// Mock data for scheduling
const timeSlots = [
  '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00', '20:00', '21:00', '22:00'
]

const locations = [
  'Factory Floor A',
  'Factory Floor B',
  'Warehouse',
  'Loading Dock',
  'Office Area'
]

// Mock environmental risk data by time of day
const hourlyRiskData = {
  '06:00': { temp: 22, risk: 'low', productivity: 95 },
  '07:00': { temp: 24, risk: 'low', productivity: 98 },
  '08:00': { temp: 26, risk: 'low', productivity: 100 },
  '09:00': { temp: 28, risk: 'moderate', productivity: 98 },
  '10:00': { temp: 30, risk: 'moderate', productivity: 95 },
  '11:00': { temp: 32, risk: 'high', productivity: 90 },
  '12:00': { temp: 34, risk: 'high', productivity: 85 },
  '13:00': { temp: 36, risk: 'critical', productivity: 75 },
  '14:00': { temp: 38, risk: 'critical', productivity: 70 },
  '15:00': { temp: 36, risk: 'high', productivity: 80 },
  '16:00': { temp: 34, risk: 'high', productivity: 85 },
  '17:00': { temp: 31, risk: 'moderate', productivity: 90 },
  '18:00': { temp: 28, risk: 'moderate', productivity: 95 },
  '19:00': { temp: 26, risk: 'low', productivity: 92 },
  '20:00': { temp: 24, risk: 'low', productivity: 88 },
  '21:00': { temp: 23, risk: 'low', productivity: 85 },
  '22:00': { temp: 22, risk: 'low', productivity: 82 }
}

// Mock workers data
const mockWorkers: Worker[] = [
  {
    id: 'worker_001',
    name: 'John Smith',
    age: 34,
    gender: 'male',
    medical_conditions: [],
    heat_tolerance: 'high',
    emergency_contact: { name: 'Jane Smith', phone: '555-0101' },
    assigned_location: 'Factory Floor A',
    shift_pattern: 'Morning (6AM-2PM)',
    created_at: '2024-01-15T06:00:00Z',
    updated_at: '2024-09-21T09:30:00Z',
    status: 'active',
    current_risk: 'low',
    active_alerts: 0
  },
  {
    id: 'worker_002',
    name: 'Maria Garcia',
    age: 28,
    gender: 'female',
    medical_conditions: ['asthma'],
    heat_tolerance: 'low',
    emergency_contact: { name: 'Carlos Garcia', phone: '555-0102' },
    assigned_location: 'Warehouse',
    shift_pattern: 'Morning (6AM-2PM)',
    created_at: '2024-02-01T06:00:00Z',
    updated_at: '2024-09-21T09:30:00Z',
    status: 'active',
    current_risk: 'moderate',
    active_alerts: 1
  }
]

interface ShiftAssignment {
  id: string
  workerId: string
  workerName: string
  location: string
  startTime: string
  endTime: string
  date: string
  estimatedRisk: string
  expectedProductivity: number
  heatTolerance: string
  medicalConditions: string[]
}

const mockShifts: ShiftAssignment[] = [
  {
    id: '1',
    workerId: 'worker_001',
    workerName: 'John Smith',
    location: 'Factory Floor A',
    startTime: '06:00',
    endTime: '14:00',
    date: '2024-09-21',
    estimatedRisk: 'moderate',
    expectedProductivity: 92,
    heatTolerance: 'high',
    medicalConditions: []
  },
  {
    id: '2',
    workerId: 'worker_002',
    workerName: 'Maria Garcia',
    location: 'Warehouse',
    startTime: '06:00',
    endTime: '14:00',
    date: '2024-09-21',
    estimatedRisk: 'low',
    expectedProductivity: 95,
    heatTolerance: 'low',
    medicalConditions: ['asthma']
  }
]

export function ShiftScheduler() {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0])
  const [shifts, setShifts] = useState<ShiftAssignment[]>(mockShifts)
  const [workers] = useState<Worker[]>(mockWorkers)
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [showCreateForm, setShowCreateForm] = useState(false)

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'text-green-600 bg-green-50'
      case 'moderate': return 'text-yellow-600 bg-yellow-50'
      case 'high': return 'text-orange-600 bg-orange-50'
      case 'critical': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getOptimalShiftRecommendations = (worker: Worker) => {
    const recommendations = []

    if (worker.heat_tolerance === 'low') {
      recommendations.push({
        shift: 'Early Morning (6AM-2PM)',
        reason: 'Lower temperatures, reduced heat exposure risk'
      })
    } else if (worker.heat_tolerance === 'high') {
      recommendations.push({
        shift: 'Flexible',
        reason: 'High heat tolerance allows flexibility'
      })
    }

    if (worker.medical_conditions.includes('asthma')) {
      recommendations.push({
        shift: 'Morning (6AM-2PM)',
        reason: 'Better air quality, lower pollution'
      })
    }

    if (worker.age > 50) {
      recommendations.push({
        shift: 'Morning (6AM-2PM)',
        reason: 'Cooler conditions recommended for older workers'
      })
    }

    return recommendations
  }

  const calculateShiftRisk = (startTime: string, endTime: string, worker: Worker) => {
    const start = parseInt(startTime.split(':')[0])
    const end = parseInt(endTime.split(':')[0])
    let totalRisk = 0
    let riskHours = 0

    for (let hour = start; hour < end; hour++) {
      const timeKey = `${hour.toString().padStart(2, '0')}:00`
      const hourData = hourlyRiskData[timeKey as keyof typeof hourlyRiskData]

      if (hourData) {
        let riskScore = 1
        if (hourData.risk === 'moderate') riskScore = 2
        if (hourData.risk === 'high') riskScore = 3
        if (hourData.risk === 'critical') riskScore = 4

        // Adjust based on worker tolerance
        if (worker.heat_tolerance === 'low') riskScore += 1
        if (worker.heat_tolerance === 'high') riskScore -= 1
        if (worker.medical_conditions.length > 0) riskScore += 1

        totalRisk += Math.max(1, Math.min(4, riskScore))
        riskHours++
      }
    }

    const averageRisk = totalRisk / riskHours
    if (averageRisk <= 1.5) return 'low'
    if (averageRisk <= 2.5) return 'moderate'
    if (averageRisk <= 3.5) return 'high'
    return 'critical'
  }

  const calculateExpectedProductivity = (startTime: string, endTime: string, worker: Worker) => {
    const start = parseInt(startTime.split(':')[0])
    const end = parseInt(endTime.split(':')[0])
    let totalProductivity = 0
    let hours = 0

    for (let hour = start; hour < end; hour++) {
      const timeKey = `${hour.toString().padStart(2, '0')}:00`
      const hourData = hourlyRiskData[timeKey as keyof typeof hourlyRiskData]

      if (hourData) {
        let productivity = hourData.productivity

        // Adjust based on worker characteristics
        if (worker.heat_tolerance === 'low' && hourData.risk !== 'low') {
          productivity -= 10
        }
        if (worker.medical_conditions.length > 0) {
          productivity -= 5
        }
        if (worker.age > 50 && hourData.risk === 'high') {
          productivity -= 8
        }

        totalProductivity += Math.max(50, Math.min(100, productivity))
        hours++
      }
    }

    return Math.round(totalProductivity / hours)
  }

  const filteredShifts = shifts.filter(shift => {
    if (shift.date !== selectedDate) return false
    if (selectedLocation !== 'all' && shift.location !== selectedLocation) return false
    return true
  })

  return (
    <div className="space-y-6">
{/* Header */}
<div className="flex items-center justify-between">
<div>
<h2 className="text-2xl font-bold tracking-tight flex items-center space-x-2">
<Calendar className="h-6 w-6 text-primary" />
<span>Shift Scheduler</span>
</h2>
<p className="text-muted-foreground">
Optimize worker shifts based on heat risk and productivity metrics
</p>
</div>
<div className="flex items-center space-x-3">
<input
type="date"
value={selectedDate}
onChange={(e) => setSelectedDate(e.target.value)}
className="border rounded px-3 py-2"
/>
<Button onClick={() => setShowCreateForm(true)}>
<Plus className="h-4 w-4 mr-2" />
Schedule Shift
</Button>
</div>
</div>

{/* Environmental Risk Timeline */}
<Card>
<CardHeader>
<CardTitle className="flex items-center space-x-2">
<Thermometer className="h-5 w-5" />
<span>Daily Heat Risk & Productivity Timeline</span>
</CardTitle>
</CardHeader>
<CardContent>
<div className="grid grid-cols-12 gap-2">
{timeSlots.map(time => {
const data = hourlyRiskData[time as keyof typeof hourlyRiskData]
return (
<div key={time} className="text-center">
<div className="text-xs font-medium mb-1">{time}</div>
<div className={`p-2 rounded-lg text-xs ${getRiskColor(data.risk)}`}>
<div className="font-semibold">{data.temp}°C</div>
<div className="capitalize">{data.risk}</div>
<div>{data.productivity}%</div>
</div>
</div>
)
})}
</div>
<div className="mt-4 flex items-center justify-center space-x-6 text-xs">
<div className="flex items-center space-x-2">
<div className="w-3 h-3 bg-green-500 rounded"></div>
<span>Low Risk</span>
</div>
<div className="flex items-center space-x-2">
<div className="w-3 h-3 bg-yellow-500 rounded"></div>
<span>Moderate Risk</span>
</div>
<div className="flex items-center space-x-2">
<div className="w-3 h-3 bg-orange-500 rounded"></div>
<span>High Risk</span>
</div>
<div className="flex items-center space-x-2">
<div className="w-3 h-3 bg-red-500 rounded"></div>
<span>Critical Risk</span>
</div>
</div>
</CardContent>
</Card>

{/* Filters */}
<Card>
<CardContent className="p-4">
<div className="flex items-center space-x-4">
<div className="flex items-center space-x-2">
<Filter className="h-4 w-4" />
<span className="text-sm font-medium">Location:</span>
</div>
<select
value={selectedLocation}
onChange={(e) => setSelectedLocation(e.target.value)}
className="text-sm border rounded px-2 py-1"
>
<option value="all">All Locations</option>
{locations.map(location => (
<option key={location} value={location}>{location}</option>
))}
</select>
<div className="text-sm text-muted-foreground">
Showing {filteredShifts.length} shifts for {selectedDate}
</div>
</div>
</CardContent>
</Card>

{/* Current Shifts */}
<Card>
<CardHeader>
<CardTitle>Scheduled Shifts</CardTitle>
</CardHeader>
<CardContent>
<div className="space-y-4">
{filteredShifts.length === 0 ? (
<div className="text-center py-8 text-muted-foreground">
<Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
<p>No shifts scheduled for this date and location</p>
<Button 
variant="outline" 
className="mt-4"
onClick={() => setShowCreateForm(true)}
>
Schedule First Shift
</Button>
</div>
) : (
filteredShifts.map(shift => (
<div key={shift.id} className="flex items-center justify-between p-4 rounded-lg border bg-card/50">
<div className="flex items-center space-x-4">
<div className="flex-shrink-0">
<div className={`w-3 h-3 rounded-full ${
shift.estimatedRisk === 'low' ? 'bg-green-500' :
shift.estimatedRisk === 'moderate' ? 'bg-yellow-500' :
shift.estimatedRisk === 'high' ? 'bg-orange-500' :
'bg-red-500'
}`} />
</div>
<div>
<h4 className="font-semibold">{shift.workerName}</h4>
<div className="flex items-center space-x-4 text-sm text-muted-foreground">
<div className="flex items-center space-x-1">
<Clock className="h-3 w-3" />
<span>{shift.startTime} - {shift.endTime}</span>
</div>
<div className="flex items-center space-x-1">
<MapPin className="h-3 w-3" />
<span>{shift.location}</span>
</div>
</div>
</div>
</div>
<div className="flex items-center space-x-4">
<div className="text-right text-sm">
<div className="flex items-center space-x-2 mb-1">
<span>Risk:</span>
<Badge variant={shift.estimatedRisk === 'low' ? 'success' : 
shift.estimatedRisk === 'moderate' ? 'warning' : 'danger'}>
{shift.estimatedRisk.toUpperCase()}
</Badge>
</div>
<div className="flex items-center space-x-2">
<TrendingUp className="h-3 w-3" />
<span>Productivity: {shift.expectedProductivity}%</span>
</div>
</div>
<div className="flex items-center space-x-2">
<Button variant="outline" size="sm">
<Edit className="h-3 w-3" />
</Button>
<Button variant="outline" size="sm">
<Trash2 className="h-3 w-3" />
</Button>
</div>
</div>
</div>
))
)}
</div>
</CardContent>
</Card>

{/* Worker Recommendations */}
<Card>
<CardHeader>
<CardTitle>Shift Recommendations</CardTitle>
</CardHeader>
<CardContent>
<div className="space-y-4">
{workers.map(worker => {
const recommendations = getOptimalShiftRecommendations(worker)
return (
<div key={worker.id} className="p-4 rounded-lg border bg-card/50">
<div className="flex items-center justify-between mb-2">
<h4 className="font-semibold">{worker.name}</h4>
<div className="flex items-center space-x-2">
<Badge variant="outline" className="capitalize">
{worker.heat_tolerance} tolerance
</Badge>
{worker.medical_conditions.length > 0 && (
<Badge variant="warning" className="text-xs">
Medical conditions
</Badge>
)}
</div>
</div>
<div className="space-y-2">
{recommendations.map((rec, index) => (
<div key={index} className="flex items-center justify-between text-sm">
<div className="flex items-center space-x-2">
<CheckCircle className="h-3 w-3 text-green-500" />
<span className="font-medium">{rec.shift}</span>
</div>
<span className="text-muted-foreground">{rec.reason}</span>
</div>
))}
</div>
</div>
)
})}
</div>
</CardContent>
</Card>
</div>
)
}