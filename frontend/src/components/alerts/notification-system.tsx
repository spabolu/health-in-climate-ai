/* eslint-disable @typescript-eslint/no-explicit-any */
'use client'

import React, { useState, useEffect, useCallback } from 'react'
import {
  Bell,
  AlertTriangle,
  X,
  Volume2,
  VolumeX
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertNotification } from './alert-notification'
import type { Alert } from '@/types'

interface NotificationSystemProps {
  alerts: Alert[]
  onAlertUpdate?: (alerts: Alert[]) => void
  maxVisible?: number
  autoHideDelay?: number
  enableSound?: boolean
}

interface ToastNotification extends Alert {
  isNew: boolean
  dismissed: boolean
}

export function NotificationSystem({
  alerts,
  onAlertUpdate,
  maxVisible = 3,
  autoHideDelay = 10000,
  enableSound = true
}: NotificationSystemProps) {
  const [notifications, setNotifications] = useState<ToastNotification[]>([])
  const [isMinimized, setIsMinimized] = useState(false)
  const [soundEnabled, setSoundEnabled] = useState(enableSound)
  const [lastAlertCount, setLastAlertCount] = useState(alerts.length)

  // Audio notification
  const playNotificationSound = useCallback(() => {
    if (!soundEnabled) return

    // Create a simple beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator.frequency.value = 800
      oscillator.type = 'sine'

      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)

      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + 0.5)
    } catch (error) {
      console.warn('Could not play notification sound:', error)
    }
  }, [soundEnabled])

  // Monitor for new alerts
  useEffect(() => {
    if (alerts.length > lastAlertCount) {
      const newAlerts = alerts.slice(lastAlertCount)

      // Add new alerts as toast notifications
      const newNotifications = newAlerts.map(alert => ({
        ...alert,
        isNew: true,
        dismissed: false
      }))

      setNotifications(prev => {
        // Only show critical and high priority alerts as toasts
        const toastWorthy = newNotifications.filter(alert =>
          alert.severity === 'critical' || alert.severity === 'high'
        )

        if (toastWorthy.length > 0) {
          playNotificationSound()
        }

        // Add new notifications and limit to maxVisible
        const updated = [...toastWorthy, ...prev].slice(0, maxVisible)
        return updated
      })
    }

    setLastAlertCount(alerts.length)
  }, [alerts, lastAlertCount, maxVisible, playNotificationSound])

  // Auto-hide notifications
  useEffect(() => {
    if (autoHideDelay <= 0) return

    const timer = setTimeout(() => {
      setNotifications(prev =>
        prev.map(notification => ({
          ...notification,
          isNew: false
        }))
      )
    }, autoHideDelay)

    return () => clearTimeout(timer)
  }, [notifications, autoHideDelay])

  const handleDismissNotification = (alertId: string) => {
    setNotifications(prev =>
      prev.filter(notification => notification.id !== alertId)
    )
  }

  const handleAcknowledgeFromNotification = (alertId: string) => {
    // Update the main alerts array
    const updatedAlerts = alerts.map(alert =>
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    )
    onAlertUpdate?.(updatedAlerts)

    // Remove from notifications
    handleDismissNotification(alertId)
  }

  const handleResolveFromNotification = (alertId: string) => {
    // Update the main alerts array
    const updatedAlerts = alerts.map(alert =>
      alert.id === alertId ? { ...alert, resolved: true } : alert
    )
    onAlertUpdate?.(updatedAlerts)

    // Remove from notifications
    handleDismissNotification(alertId)
  }

  const clearAllNotifications = () => {
    setNotifications([])
  }

  const activeNotifications = notifications.filter(n => !n.dismissed)
  const criticalCount = alerts.filter(a => a.severity === 'critical' && !a.resolved).length
  const pendingCount = alerts.filter(a => !a.acknowledged && !a.resolved).length

  return (
    <>
      {/* Notification Bell Icon (for header) */}
      <div className="relative">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsMinimized(!isMinimized)}
          className="relative"
        >
          <Bell className="h-5 w-5" />
          {pendingCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
            >
              {pendingCount > 9 ? '9+' : pendingCount}
            </Badge>
          )}
        </Button>

        {criticalCount > 0 && (
          <div className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full animate-pulse" />
        )}
      </div>

      {/* Sound Toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setSoundEnabled(!soundEnabled)}
        className="ml-2"
      >
        {soundEnabled ? (
          <Volume2 className="h-4 w-4" />
        ) : (
          <VolumeX className="h-4 w-4" />
        )}
      </Button>

      {/* Toast Notifications */}
      {!isMinimized && activeNotifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-3 w-96 max-w-[calc(100vw-2rem)]">
          {/* Header with clear all button */}
          <div className="flex items-center justify-between bg-card/95 backdrop-blur-sm rounded-lg border p-3 shadow-lg">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <span className="text-sm font-medium">
                Active Alerts ({activeNotifications.length})
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllNotifications}
                className="text-xs"
              >
                Clear All
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMinimized(true)}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>

          {/* Notification cards */}
          {activeNotifications.map((notification) => (
            <div
              key={notification.id}
              className="bg-card/95 backdrop-blur-sm rounded-lg border shadow-lg transition-all duration-300 hover:shadow-xl"
            >
              <AlertNotification
                alert={notification}
                onAcknowledge={handleAcknowledgeFromNotification}
                onResolve={handleResolveFromNotification}
                onDismiss={handleDismissNotification}
                showActions={true}
                compact={false}
              />
            </div>
          ))}
        </div>
      )}

      {/* Emergency Alert Overlay for Critical Alerts */}
      {alerts.some(a => a.severity === 'critical' && !a.acknowledged && !a.resolved) && (
        <div className="fixed inset-0 z-40 bg-red-500/10 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-red-500 rounded-lg p-6 shadow-2xl max-w-md w-full">
            <div className="text-center">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4 animate-pulse" />
              <h3 className="text-lg font-bold text-red-700 mb-2">
                Emergency Alert
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                Critical safety alerts require immediate attention
              </p>
              <div className="flex space-x-2">
                <Button
                  variant="destructive"
                  onClick={() => {
                    // Auto-acknowledge all critical alerts for demo
                    const updatedAlerts = alerts.map(alert =>
                      alert.severity === 'critical'
                        ? { ...alert, acknowledged: true }
                        : alert
                    )
                    onAlertUpdate?.(updatedAlerts)
                  }}
                  className="flex-1"
                >
                  Acknowledge All Critical
                </Button>
                <Button variant="outline" className="flex-1">
                  View Details
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}