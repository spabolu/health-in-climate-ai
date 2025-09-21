/**
 * HeatGuard Pro Dashboard Sidebar
 * Navigation sidebar with safety priority organization
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useHealthAlerts, useDashboardMetrics } from '@/hooks/use-thermal-comfort';
import {
  Users,
  AlertTriangle,
  Activity,
  FileText,
  Calendar,
  Settings,
  BarChart3,
  MapPin,
  Shield,
  Clock,
  Thermometer,
  Bell,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline';
  priority: 'critical' | 'high' | 'normal' | 'low';
  description?: string;
}

interface DashboardSidebarProps {
  className?: string;
}

export default function DashboardSidebar({ className = '' }: DashboardSidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { criticalAlerts, unacknowledgedAlerts } = useHealthAlerts();
  const { metrics } = useDashboardMetrics();

  const navigationItems: NavigationItem[] = [
    // Critical Safety Items (Always at top)
    {
      name: 'Critical Alerts',
      href: '/dashboard/alerts',
      icon: AlertTriangle,
      badge: criticalAlerts.length > 0 ? criticalAlerts.length : undefined,
      badgeVariant: 'destructive',
      priority: 'critical',
      description: 'Immediate attention required',
    },

    // High Priority Monitoring
    {
      name: 'Live Monitoring',
      href: '/dashboard',
      icon: Activity,
      badge: metrics?.active_workers,
      badgeVariant: 'secondary',
      priority: 'high',
      description: 'Real-time worker status',
    },
    {
      name: 'Workers at Risk',
      href: '/dashboard/risk',
      icon: Shield,
      badge: metrics?.workers_at_risk || 0,
      badgeVariant: metrics?.workers_at_risk ? 'destructive' : 'outline',
      priority: 'high',
      description: 'Workers requiring attention',
    },

    // Normal Operations
    {
      name: 'All Workers',
      href: '/dashboard/workers',
      icon: Users,
      badge: metrics?.total_workers,
      badgeVariant: 'secondary',
      priority: 'normal',
      description: 'Workforce management',
    },
    {
      name: 'Environmental',
      href: '/dashboard/environmental',
      icon: Thermometer,
      priority: 'normal',
      description: 'Temperature & conditions',
    },
    {
      name: 'Locations',
      href: '/dashboard/locations',
      icon: MapPin,
      priority: 'normal',
      description: 'Work site monitoring',
    },
    {
      name: 'Analytics',
      href: '/dashboard/analytics',
      icon: BarChart3,
      priority: 'normal',
      description: 'Performance insights',
    },
    {
      name: 'Scheduling',
      href: '/dashboard/scheduling',
      icon: Calendar,
      priority: 'normal',
      description: 'Shift management',
    },

    // Lower Priority Items
    {
      name: 'Compliance',
      href: '/dashboard/compliance',
      icon: FileText,
      priority: 'low',
      description: 'OSHA reports & documentation',
    },
    {
      name: 'History',
      href: '/dashboard/history',
      icon: Clock,
      priority: 'low',
      description: 'Historical data analysis',
    },
    {
      name: 'Notifications',
      href: '/dashboard/notifications',
      icon: Bell,
      badge: unacknowledgedAlerts.length || undefined,
      badgeVariant: 'outline',
      priority: 'low',
      description: 'Alert management',
    },
  ];

  const settingsItems: NavigationItem[] = [
    {
      name: 'System Settings',
      href: '/dashboard/settings',
      icon: Settings,
      priority: 'low',
      description: 'Configuration & preferences',
    },
  ];


  const isActive = (href: string) => {
    if (href === '/dashboard' && pathname === '/dashboard') return true;
    if (href !== '/dashboard' && pathname.startsWith(href)) return true;
    return false;
  };

  const renderNavigationItem = (item: NavigationItem) => {
    const active = isActive(item.href);
    const Icon = item.icon;

    return (
      <Link key={item.href} href={item.href}>
        <Button
          variant={active ? 'default' : 'ghost'}
          className={`
            w-full justify-start h-auto p-3 mb-1
            ${active ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}
            ${item.priority === 'critical' && item.badge ? 'ring-2 ring-red-200' : ''}
          `}
        >
          <div className="flex items-center justify-between w-full">
            <div className="flex items-center space-x-3">
              <Icon className={`
                h-5 w-5
                ${item.priority === 'critical' && item.badge ? 'text-red-500' : ''}
                ${active ? 'text-white' : ''}
              `} />
              {!isCollapsed && (
                <div className="flex flex-col items-start">
                  <span className={`font-medium ${active ? 'text-white' : 'text-gray-900'}`}>
                    {item.name}
                  </span>
                  {item.description && (
                    <span className={`text-xs ${active ? 'text-blue-100' : 'text-gray-500'}`}>
                      {item.description}
                    </span>
                  )}
                </div>
              )}
            </div>

            {!isCollapsed && item.badge && (
              <Badge
                variant={item.badgeVariant || 'secondary'}
                className="ml-auto"
              >
                {item.badge}
              </Badge>
            )}
          </div>
        </Button>
      </Link>
    );
  };

  const criticalItems = navigationItems.filter(item => item.priority === 'critical');
  const highPriorityItems = navigationItems.filter(item => item.priority === 'high');
  const normalItems = navigationItems.filter(item => item.priority === 'normal');
  const lowPriorityItems = navigationItems.filter(item => item.priority === 'low');

  return (
    <div className={`
      flex flex-col h-screen bg-white border-r border-gray-200
      ${isCollapsed ? 'w-16' : 'w-64'}
      transition-all duration-300 ease-in-out
      ${className}
    `}>
      {/* Collapse Toggle */}
      <div className="p-4 flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="h-8 w-8 p-0"
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4">
        {/* Critical Safety Items */}
        {criticalItems.length > 0 && (
          <div className="mb-6">
            {!isCollapsed && (
              <h3 className="px-3 mb-2 text-xs font-semibold text-red-600 uppercase tracking-wider">
                Critical Safety
              </h3>
            )}
            <div className="space-y-1">
              {criticalItems.map(renderNavigationItem)}
            </div>
          </div>
        )}

        {/* High Priority */}
        {highPriorityItems.length > 0 && (
          <div className="mb-6">
            {!isCollapsed && (
              <h3 className="px-3 mb-2 text-xs font-semibold text-orange-600 uppercase tracking-wider">
                Active Monitoring
              </h3>
            )}
            <div className="space-y-1">
              {highPriorityItems.map(renderNavigationItem)}
            </div>
          </div>
        )}

        <Separator className="my-4" />

        {/* Normal Operations */}
        {normalItems.length > 0 && (
          <div className="mb-6">
            {!isCollapsed && (
              <h3 className="px-3 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Operations
              </h3>
            )}
            <div className="space-y-1">
              {normalItems.map(renderNavigationItem)}
            </div>
          </div>
        )}

        <Separator className="my-4" />

        {/* Lower Priority */}
        {lowPriorityItems.length > 0 && (
          <div className="mb-6">
            {!isCollapsed && (
              <h3 className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Management
              </h3>
            )}
            <div className="space-y-1">
              {lowPriorityItems.map(renderNavigationItem)}
            </div>
          </div>
        )}

        <Separator className="my-4" />

        {/* Settings */}
        <div className="space-y-1">
          {settingsItems.map(renderNavigationItem)}
        </div>
      </div>

      {/* System Status Footer */}
      {!isCollapsed && (
        <div className="p-3 border-t border-gray-200 bg-gray-50">
          <div className="text-xs text-gray-500 space-y-1">
            <div className="flex justify-between">
              <span>System Status:</span>
              <span className="text-green-600 font-medium">Online</span>
            </div>
            {metrics && (
              <>
                <div className="flex justify-between">
                  <span>Active Workers:</span>
                  <span className="font-medium">{metrics.active_workers}</span>
                </div>
                <div className="flex justify-between">
                  <span>Avg Temperature:</span>
                  <span className="font-medium">{metrics.average_temperature?.toFixed(1) ?? '--'}°C</span>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}