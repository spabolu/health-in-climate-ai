/**
 * HeatGuard Pro Main Dashboard Page
 * Real-time workforce safety monitoring dashboard
 */

'use client';

import DashboardLayout, {
  DashboardPageContainer,
  DashboardGrid,
  DashboardWidget,
} from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import {
  Thermometer,
  Shield,
  Activity,
  RefreshCw,
} from 'lucide-react';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <DashboardPageContainer
        title="Live Monitoring Dashboard"
        description="Real-time worker safety and thermal comfort monitoring"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Live Monitoring' },
        ]}
        actions={
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Button size="sm">
              <Shield className="h-4 w-4 mr-2" />
              Emergency Mode
            </Button>
          </div>
        }
      >
        {/* Main Dashboard Grid */}
        <DashboardGrid>
          {/* System Status Widget */}
          <DashboardWidget
            title="System Status"
            description="HeatGuard Pro monitoring system"
            colSpan={3}
          >
            <div className="text-center py-12">
              <Shield className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">System Online</h3>
              <p className="text-gray-600 mb-4">Heat stress monitoring system is operational</p>
              <div className="flex justify-center space-x-8 text-sm">
                <div className="text-center">
                  <div className="h-3 w-3 bg-green-500 rounded-full mx-auto mb-1"></div>
                  <span className="text-gray-600">Sensors</span>
                </div>
                <div className="text-center">
                  <div className="h-3 w-3 bg-green-500 rounded-full mx-auto mb-1"></div>
                  <span className="text-gray-600">AI Model</span>
                </div>
                <div className="text-center">
                  <div className="h-3 w-3 bg-green-500 rounded-full mx-auto mb-1"></div>
                  <span className="text-gray-600">Monitoring</span>
                </div>
              </div>
            </div>
          </DashboardWidget>

          {/* Business Demo Information */}
          <DashboardWidget
            title="Business Demo Features"
            description="Available functionality"
            colSpan={2}
          >
            <div className="space-y-6">
              <div className="flex items-start space-x-3">
                <Activity className="h-5 w-5 text-blue-500 mt-1" />
                <div>
                  <h4 className="font-medium text-gray-900">Live Monitoring</h4>
                  <p className="text-sm text-gray-600">Real-time dashboard view for workforce oversight</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Thermometer className="h-5 w-5 text-orange-500 mt-1" />
                <div>
                  <h4 className="font-medium text-gray-900">Heat Stress Simulation</h4>
                  <p className="text-sm text-gray-600">Interactive demo showing XGBoost ML predictions for various heat conditions</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <Shield className="h-5 w-5 text-green-500 mt-1" />
                <div>
                  <h4 className="font-medium text-gray-900">AI-Powered Safety</h4>
                  <p className="text-sm text-gray-600">Machine learning model predicts heat exhaustion risk in real-time</p>
                </div>
              </div>
            </div>
          </DashboardWidget>
        </DashboardGrid>
      </DashboardPageContainer>
    </DashboardLayout>
  );
}