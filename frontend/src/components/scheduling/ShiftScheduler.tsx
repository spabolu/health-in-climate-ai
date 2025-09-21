/**
 * HeatGuard Pro Shift Scheduler
 * Drag-and-drop shift scheduling with heat safety recommendations
 */

'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calendar, Users, Clock, Thermometer, AlertTriangle } from 'lucide-react';

interface Worker {
  id: string;
  name: string;
  heatTolerance: 'low' | 'normal' | 'high';
  currentStatus: 'available' | 'scheduled' | 'unavailable';
}

interface Shift {
  id: string;
  startTime: string;
  endTime: string;
  location: string;
  maxWorkers: number;
  assignedWorkers: Worker[];
  predictedTemp: number;
  riskLevel: 'low' | 'moderate' | 'high';
}

interface ShiftSchedulerProps {
  workers: Worker[];
  shifts: Shift[];
  onScheduleWorker?: (workerId: string, shiftId: string) => void;
  onUnscheduleWorker?: (workerId: string, shiftId: string) => void;
  className?: string;
}

export default function ShiftScheduler({
  workers,
  shifts,
  onScheduleWorker,
  onUnscheduleWorker,
  className = '',
}: ShiftSchedulerProps) {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      case 'moderate': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getToleranceColor = (tolerance: string) => {
    switch (tolerance) {
      case 'low': return 'text-blue-600';
      case 'normal': return 'text-gray-600';
      case 'high': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Shift Scheduler</h2>
          <p className="text-gray-600">Heat-aware workforce scheduling</p>
        </div>
        <div className="flex items-center space-x-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          />
          <Button>
            <Calendar className="h-4 w-4 mr-2" />
            Auto-Schedule
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Available Workers */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Workers</h3>
          <div className="space-y-3">
            {workers.filter(w => w.currentStatus === 'available').map(worker => (
              <div
                key={worker.id}
                className="p-3 border border-gray-200 rounded-lg cursor-move hover:shadow-md transition-shadow"
                draggable
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">{worker.name}</span>
                  <Badge className={getToleranceColor(worker.heatTolerance)}>
                    {worker.heatTolerance} tolerance
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Shifts */}
        <Card className="p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Shifts</h3>
          <div className="space-y-4">
            {shifts.map(shift => (
              <div
                key={shift.id}
                className={`p-4 border-2 border-dashed rounded-lg ${getRiskColor(shift.riskLevel)}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {shift.startTime} - {shift.endTime}
                    </h4>
                    <p className="text-sm text-gray-600">{shift.location}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex items-center space-x-1 text-sm">
                      <Thermometer className="h-4 w-4" />
                      <span>{shift.predictedTemp}°C</span>
                    </div>
                    <Badge className={getRiskColor(shift.riskLevel)}>
                      {shift.riskLevel} risk
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {shift.assignedWorkers.map(worker => (
                    <div
                      key={worker.id}
                      className="p-2 bg-white border border-gray-200 rounded text-sm"
                    >
                      <div className="font-medium">{worker.name}</div>
                      <div className="text-xs text-gray-500">
                        {worker.heatTolerance} tolerance
                      </div>
                    </div>
                  ))}

                  {/* Empty slots */}
                  {Array.from({ length: shift.maxWorkers - shift.assignedWorkers.length }).map((_, i) => (
                    <div
                      key={`empty-${i}`}
                      className="p-2 border-2 border-dashed border-gray-300 rounded text-sm text-gray-400 text-center"
                    >
                      Drop worker here
                    </div>
                  ))}
                </div>

                {shift.riskLevel === 'high' && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
                    <div className="flex items-center space-x-2">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <span className="text-sm text-red-800">
                        High heat risk - consider additional safety measures
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Scheduling Recommendations */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Heat Safety Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-blue-50 border border-blue-200 rounded">
            <div className="flex items-center space-x-2 mb-2">
              <Users className="h-5 w-5 text-blue-600" />
              <span className="font-medium text-blue-900">Worker Rotation</span>
            </div>
            <p className="text-sm text-blue-800">
              Rotate workers every 2 hours during high-heat periods
            </p>
          </div>

          <div className="p-4 bg-green-50 border border-green-200 rounded">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-900">Optimal Hours</span>
            </div>
            <p className="text-sm text-green-800">
              Schedule intensive work during cooler morning hours
            </p>
          </div>

          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
            <div className="flex items-center space-x-2 mb-2">
              <Thermometer className="h-5 w-5 text-yellow-600" />
              <span className="font-medium text-yellow-900">Heat Tolerance</span>
            </div>
            <p className="text-sm text-yellow-800">
              Match worker heat tolerance to shift risk levels
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}