'use client'

import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import {
  TrendingUp,
  Users,
  Thermometer,
  Heart,
  AlertTriangle,
  RefreshCw,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { WorkerCard } from './worker-card'
import type { Worker, BiometricReading, DashboardMetrics } from '@/types'

// Mock data for workers and readings
const mockWorkers: Worker[] = [
  {
    id: 'worker_001',
    name: 'John Smith',
    age: 34,
    gender: 'male',
    medical_conditions: [],
    heat_tolerance: 'normal',
    emergency_contact: { name: 'Jane Smith', phone: '555-0101' },
    assigned_location: 'Factory Floor A',
    shift_pattern: 'Morning (6AM-2PM)',
    created_at: '2024-01-15T06:00:00Z',
    updated_at: '2024-09-21T09:30:00Z',
    status: 'active',
    current_risk: 'high',
    active_alerts: 2
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
    active_alerts: 0
  },
  {
    id: 'worker_003',
    name: 'David Johnson',
    age: 42,
    gender: 'male',
    medical_conditions: ['hypertension'],
    heat_tolerance: 'high',
    emergency_contact: { name: 'Sarah Johnson', phone: '555-0103' },
    assigned_location: 'Loading Dock',
    shift_pattern: 'Afternoon (2PM-10PM)',
    created_at: '2024-01-20T14:00:00Z',
    updated_at: '2024-09-21T09:30:00Z',
    status: 'active',
    current_risk: 'low',
    active_alerts: 0
  },
  {
    id: 'worker_004',
    name: 'Sarah Wilson',
    age: 31,
    gender: 'female',
    medical_conditions: [],
    heat_tolerance: 'normal',
    emergency_contact: { name: 'Mike Wilson', phone: '555-0104' },
    assigned_location: 'Factory Floor B',
    shift_pattern: 'Morning (6AM-2PM)',
    created_at: '2024-01-25T06:00:00Z',
    updated_at: '2024-09-21T09:30:00Z',
    status: 'active',
    current_risk: 'critical',
    active_alerts: 3
  }
]

const generateMockReading = (worker: Worker): BiometricReading => {
  const baseTemp = 25 + Math.random() * 15 // 25-40°C
  const heartRate = 70 + Math.random() * 50 // 70-120 bpm

  // Adjust based on risk level
  const riskMultiplier = worker.current_risk === 'critical' ? 1.4 :
                        worker.current_risk === 'high' ? 1.2 :
                        worker.current_risk === 'moderate' ? 1.1 : 1.0

  return {
    id: Date.now(),
    worker_id: worker.id,
    timestamp: new Date().toISOString(),
    Gender: worker.gender === 'male' ? 1 : 0,
    Age: worker.age,
    Temperature: baseTemp,
    Humidity: 40 + Math.random() * 40, // 40-80%
    AirVelocity: 0.5 + Math.random() * 1.5,
    HeartRate: heartRate * riskMultiplier,
    SkinTemperature: baseTemp + (Math.random() * 4 - 2),
    CoreBodyTemperature: 36.5 + Math.random() * 2 * riskMultiplier,
    SkinConductance: 0.2 + Math.random() * 0.6,
    MetabolicRate: 1.0 + Math.random() * 2.0,
    ActivityLevel: Math.floor(1 + Math.random() * 5),
    ClothingInsulation: 0.5 + Math.random() * 1.0,
    RespiratoryRate: 12 + Math.random() * 16,
    HydrationLevel: Math.max(0.3, 1.0 - (riskMultiplier - 1) * 0.5 + Math.random() * 0.3),
    location_id: worker.assigned_location
  }
}

// Generate trend data for charts
const generateTrendData = () => {
  const data = []
  const now = new Date()

  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 5 * 60000) // Every 5 minutes
    data.push({
      time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      avgTemp: 28 + Math.random() * 8,
      avgHeartRate: 85 + Math.random() * 20,
      riskScore: 1 + Math.random() * 3,
      activeWorkers: 85 + Math.floor(Math.random() * 10)
    })
  }

  return data
}

interface RealTimeMonitorProps {
  selectedLocation?: string
}

export function RealTimeMonitor({ selectedLocation }: RealTimeMonitorProps) {
  const [workers, setWorkers] = useState<Worker[]>(mockWorkers)
  const [readings, setReadings] = useState<Map<string, BiometricReading>>(new Map())
  const [trendData, setTrendData] = useState(() => generateTrendData())
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [filterRisk, setFilterRisk] = useState<string>('all')

  // Simulate real-time updates
  useEffect(() => {
    const updateData = () => {
      const newReadings = new Map<string, BiometricReading>()
      workers.forEach(worker => {
        newReadings.set(worker.id, generateMockReading(worker))
      })
      setReadings(newReadings)

      // Update trend data
      setTrendData(prev => {
        const newData = [...prev.slice(1)]
        const latest = prev[prev.length - 1]
        newData.push({
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          avgTemp: latest.avgTemp + (Math.random() - 0.5) * 2,
          avgHeartRate: latest.avgHeartRate + (Math.random() - 0.5) * 5,
          riskScore: Math.max(1, Math.min(4, latest.riskScore + (Math.random() - 0.5) * 0.5)),
          activeWorkers: Math.max(80, Math.min(95, latest.activeWorkers + (Math.random() - 0.5) * 2))
        })
        return newData
      })
    }

    // Initial load
    updateData()

    // Update every 5 seconds for demo
    const interval = setInterval(updateData, 5000)
    return () => clearInterval(interval)
  }, [workers])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  const filteredWorkers = workers.filter(worker => {
    if (selectedLocation && worker.assigned_location !== selectedLocation) return false
    if (filterRisk === 'all') return true
    return worker.current_risk === filterRisk
  })

  const getRiskCounts = () => {
    const counts = { critical: 0, high: 0, moderate: 0, low: 0 }
    filteredWorkers.forEach(worker => {
      if (worker.current_risk && worker.current_risk in counts) {
        counts[worker.current_risk as keyof typeof counts]++
      }
    })
    return counts
  }

  const riskCounts = getRiskCounts()

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Real-Time Worker Monitoring</h2>
          <p className="text-muted-foreground">
            Live biometric data and heat risk assessment for {filteredWorkers.length} workers
            {selectedLocation && ` in ${selectedLocation}`}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Filter className="h-4 w-4" />
            <select
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="text-sm border rounded px-2 py-1"
            >
              <option value="all">All Risk Levels</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="moderate">Moderate</option>
              <option value="low">Low</option>
            </select>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Risk Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-red-200 bg-red-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-600">Critical</p>
                <p className="text-2xl font-bold text-red-700">{riskCounts.critical}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-orange-200 bg-orange-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">High</p>
                <p className="text-2xl font-bold text-orange-700">{riskCounts.high}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-600">Moderate</p>
                <p className="text-2xl font-bold text-yellow-700">{riskCounts.moderate}</p>
              </div>
              <Thermometer className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-200 bg-green-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Low</p>
                <p className="text-2xl font-bold text-green-700">{riskCounts.low}</p>
              </div>
              <Users className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Real-time Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Heat Risk Trends</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avgTemp"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  name="Avg Temperature (°C)"
                />
                <Line
                  type="monotone"
                  dataKey="riskScore"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Risk Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Heart className="h-5 w-5" />
              <span>Biometric Trends</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avgHeartRate"
                  stroke="#dc2626"
                  strokeWidth={2}
                  name="Avg Heart Rate (bpm)"
                />
                <Line
                  type="monotone"
                  dataKey="activeWorkers"
                  stroke="#16a34a"
                  strokeWidth={2}
                  name="Active Workers"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Worker Cards Grid */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Individual Worker Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredWorkers.map(worker => (
            <WorkerCard
              key={worker.id}
              worker={worker}
              latestReading={readings.get(worker.id)}
              onViewDetails={(workerId) => {
                console.log('View details for:', workerId)
                // TODO: Navigate to worker detail page
              }}
              onGenerateAlert={(workerId) => {
                console.log('Generate alert for:', workerId)
                // TODO: Create alert
              }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}