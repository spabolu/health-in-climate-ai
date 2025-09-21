/**
 * HeatGuard Pro Dashboard Sidebar
 * Navigation sidebar with safety priority organization
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  Activity,
  UserPlus,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  priority: 'high' | 'normal';
  description?: string;
}

interface DashboardSidebarProps {
  className?: string;
}

export default function DashboardSidebar({ className = '' }: DashboardSidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const navigationItems: NavigationItem[] = [
    {
      name: 'Live Monitoring',
      href: '/dashboard',
      icon: Activity,
      priority: 'high',
      description: 'Real-time monitoring dashboard',
    },
    {
      name: 'Heat Stress Simulation',
      href: '/dashboard/manual-input',
      icon: UserPlus,
      priority: 'normal',
      description: 'Interactive business demo',
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
          `}
        >
          <div className="flex items-center space-x-3">
            <Icon className={`h-5 w-5 ${active ? 'text-white' : ''}`} />
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
        </Button>
      </Link>
    );
  };

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
        {!isCollapsed && (
          <div className="mb-4">
            <h3 className="px-3 mb-2 text-xs font-semibold text-blue-600 uppercase tracking-wider">
              HeatGuard Pro
            </h3>
          </div>
        )}

        <div className="space-y-1">
          {navigationItems.map(renderNavigationItem)}
        </div>
      </div>
    </div>
  );
}