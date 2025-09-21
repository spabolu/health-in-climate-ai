/**
 * Hydration-safe date hook for Next.js SSR
 * Prevents hydration mismatches by initializing with null and setting actual date after hydration
 */

'use client';

import { useState, useEffect } from 'react';

interface UseHydratedDateOptions {
  updateInterval?: number; // milliseconds, set to 0 to disable updates
  initialDate?: Date | null;
}

interface UseHydratedDateReturn {
  currentDate: Date | null;
  isHydrated: boolean;
  formatTime: (date: Date | null, options?: Intl.DateTimeFormatOptions) => string;
  formatDate: (date: Date | null, options?: Intl.DateTimeFormatOptions) => string;
}

export function useHydratedDate(options: UseHydratedDateOptions = {}): UseHydratedDateReturn {
  const { updateInterval = 1000, initialDate = null } = options;

  const [currentDate, setCurrentDate] = useState<Date | null>(initialDate);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Set initial date after hydration
    setCurrentDate(new Date());
    setIsHydrated(true);

    // Set up interval updates if specified
    if (updateInterval > 0) {
      const timer = setInterval(() => {
        setCurrentDate(new Date());
      }, updateInterval);

      return () => clearInterval(timer);
    }
  }, [updateInterval]);

  const formatTime = (date: Date | null, options?: Intl.DateTimeFormatOptions): string => {
    if (!date || !isHydrated) return '--:--:--';

    const defaultOptions: Intl.DateTimeFormatOptions = {
      hour12: true,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    };

    return date.toLocaleTimeString('en-US', { ...defaultOptions, ...options });
  };

  const formatDate = (date: Date | null, options?: Intl.DateTimeFormatOptions): string => {
    if (!date || !isHydrated) return 'Loading...';

    const defaultOptions: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };

    return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
  };

  return {
    currentDate,
    isHydrated,
    formatTime,
    formatDate,
  };
}

/**
 * Static date hook - for dates that don't need to update
 * Good for components that just need current date but don't update
 */
export function useHydratedStaticDate(): UseHydratedDateReturn {
  return useHydratedDate({ updateInterval: 0 });
}

/**
 * Fast updating date hook - for components that need frequent updates
 */
export function useHydratedFastDate(): UseHydratedDateReturn {
  return useHydratedDate({ updateInterval: 100 });
}