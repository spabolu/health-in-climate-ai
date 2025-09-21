/**
 * HeatGuard Pro Main Dashboard Layout
 * Responsive layout system with header, sidebar, and main content area
 */

'use client';

import { ReactNode } from 'react';
import { Toaster } from '@/components/ui/sonner';
import DashboardHeader from './DashboardHeader';
import DashboardSidebar from './DashboardSidebar';

interface DashboardLayoutProps {
  children: ReactNode;
  className?: string;
}

export default function DashboardLayout({ children, className = '' }: DashboardLayoutProps) {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-gray-50">
      {/* Header */}
      <DashboardHeader />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <DashboardSidebar />

        {/* Main Content Area */}
        <main className={`
          flex-1 overflow-y-auto bg-gray-50
          focus:outline-none
          ${className}
        `}>
          {/* Content Container with Grid System */}
          <div className="h-full">
            {children}
          </div>
        </main>
      </div>

      {/* Toast Notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'white',
            border: '1px solid #e5e7eb',
            color: '#374151',
          },
        }}
      />
    </div>
  );
}

/**
 * Dashboard Grid Container
 * Responsive grid system for dashboard widgets
 */
interface DashboardGridProps {
  children: ReactNode;
  className?: string;
}

export function DashboardGrid({ children, className = '' }: DashboardGridProps) {
  return (
    <div className={`
      grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4
      gap-4 p-4 h-full
      ${className}
    `}>
      {children}
    </div>
  );
}

/**
 * Dashboard Widget Container
 * Standardized container for dashboard widgets
 */
interface DashboardWidgetProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  colSpan?: 1 | 2 | 3 | 4;
  rowSpan?: 1 | 2 | 3;
  loading?: boolean;
  error?: string | null;
  actions?: ReactNode;
}

export function DashboardWidget({
  title,
  description,
  children,
  className = '',
  colSpan = 1,
  rowSpan = 1,
  loading = false,
  error = null,
  actions,
}: DashboardWidgetProps) {
  const colSpanClass = {
    1: 'col-span-1',
    2: 'col-span-1 md:col-span-2',
    3: 'col-span-1 md:col-span-2 xl:col-span-3',
    4: 'col-span-1 md:col-span-2 xl:col-span-3 2xl:col-span-4',
  }[colSpan];

  const rowSpanClass = {
    1: 'row-span-1',
    2: 'row-span-2',
    3: 'row-span-3',
  }[rowSpan];

  return (
    <div className={`
      bg-white rounded-lg border border-gray-200 shadow-sm
      flex flex-col
      ${colSpanClass} ${rowSpanClass}
      ${className}
    `}>
      {/* Widget Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {description && (
            <p className="text-sm text-gray-500 mt-1">{description}</p>
          )}
        </div>
        {actions && (
          <div className="flex items-center space-x-2">
            {actions}
          </div>
        )}
      </div>

      {/* Widget Content */}
      <div className="flex-1 p-4 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-red-500 mb-2">⚠️</div>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

/**
 * Dashboard Page Container
 * Standard page wrapper for dashboard pages
 */
interface DashboardPageContainerProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
  breadcrumbs?: Array<{ label: string; href?: string }>;
  actions?: ReactNode;
}

export function DashboardPageContainer({
  title,
  description,
  children,
  className = '',
  breadcrumbs = [],
  actions,
}: DashboardPageContainerProps) {
  return (
    <div className={`h-full flex flex-col ${className}`}>
      {/* Page Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            {/* Breadcrumbs */}
            {breadcrumbs.length > 0 && (
              <nav className="flex mb-2" aria-label="Breadcrumb">
                <ol className="inline-flex items-center space-x-1 md:space-x-3">
                  {breadcrumbs.map((crumb, index) => (
                    <li key={index} className="inline-flex items-center">
                      {index > 0 && (
                        <svg className="w-4 h-4 text-gray-400 mx-1" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                      {crumb.href ? (
                        <a
                          href={crumb.href}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {crumb.label}
                        </a>
                      ) : (
                        <span className="text-sm text-gray-500">{crumb.label}</span>
                      )}
                    </li>
                  ))}
                </ol>
              </nav>
            )}

            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {description && (
              <p className="text-gray-600 mt-1">{description}</p>
            )}
          </div>

          {actions && (
            <div className="flex items-center space-x-3">
              {actions}
            </div>
          )}
        </div>
      </div>

      {/* Page Content */}
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

/**
 * Dashboard Metrics Row
 * Quick metrics display at the top of dashboard pages
 */
interface MetricCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease' | 'neutral';
    period: string;
  };
  icon?: ReactNode;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'gray';
}

export function MetricCard({ title, value, change, icon, color = 'blue' }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    red: 'bg-red-50 text-red-600',
    gray: 'bg-gray-50 text-gray-600',
  };

  const changeColorClasses = {
    increase: 'text-green-600',
    decrease: 'text-red-600',
    neutral: 'text-gray-500',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change && (
            <div className="flex items-center mt-2">
              <span className={`text-sm font-medium ${changeColorClasses[change.type]}`}>
                {change.type === 'increase' ? '+' : change.type === 'decrease' ? '-' : ''}
                {Math.abs(change.value)}%
              </span>
              <span className="text-xs text-gray-500 ml-1">
                vs {change.period}
              </span>
            </div>
          )}
        </div>
        {icon && (
          <div className={`h-12 w-12 rounded-lg ${colorClasses[color]} flex items-center justify-center`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export interface DashboardMetricsRowProps {
  children: ReactNode;
  className?: string;
}

export function DashboardMetricsRow({ children, className = '' }: DashboardMetricsRowProps) {
  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 ${className}`}>
      {children}
    </div>
  );
}