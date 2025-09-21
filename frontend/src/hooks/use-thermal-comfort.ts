/**
 * React hooks for thermal comfort prediction API
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  BiometricData,
  ThermalComfortPrediction,
  WorkerProfile,
  HealthAlert,
  DashboardMetrics,
  HistoricalData,
} from '@/types/thermal-comfort';
import { apiClient, handleApiError } from '@/lib/api-client';

/**
 * Hook for single thermal comfort prediction
 */
export function useThermalComfortPrediction() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [prediction, setPrediction] = useState<ThermalComfortPrediction | null>(null);

  const predict = useCallback(async (data: BiometricData) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.predictThermalComfort(data);
      setPrediction(result);
      return result;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    predict,
    prediction,
    isLoading,
    error,
    clearError: () => setError(null),
  };
}

/**
 * Hook for batch thermal comfort predictions
 */
export function useThermalComfortBatch() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ThermalComfortPrediction[] | null>(null);

  const predictBatch = useCallback(async (dataArray: BiometricData[]) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.predictThermalComfortBatch(dataArray);
      setResults(response.predictions);
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    predictBatch,
    results,
    isLoading,
    error,
    clearError: () => setError(null),
  };
}

/**
 * Hook for managing workers
 */
export function useWorkers() {
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiClient.getWorkers();
      setWorkers(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addWorker = useCallback(async (worker: Omit<WorkerProfile, 'id' | 'created_at' | 'updated_at'>) => {
    try {
      const newWorker = await apiClient.createWorker(worker);
      setWorkers(prev => [...prev, newWorker]);
      return newWorker;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    }
  }, []);

  const updateWorker = useCallback(async (workerId: string, updates: Partial<WorkerProfile>) => {
    try {
      const updatedWorker = await apiClient.updateWorker(workerId, updates);
      setWorkers(prev => prev.map(w => w.id === workerId ? updatedWorker : w));
      return updatedWorker;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    }
  }, []);

  const removeWorker = useCallback(async (workerId: string) => {
    try {
      await apiClient.deleteWorker(workerId);
      setWorkers(prev => prev.filter(w => w.id !== workerId));
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    }
  }, []);

  // Fetch workers on mount
  useEffect(() => {
    fetchWorkers();
  }, [fetchWorkers]);

  return {
    workers,
    isLoading,
    error,
    fetchWorkers,
    addWorker,
    updateWorker,
    removeWorker,
    clearError: () => setError(null),
  };
}

/**
 * Hook for health alerts management
 */
export function useHealthAlerts(workerId?: string) {
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiClient.getAlerts(workerId);
      setAlerts(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [workerId]);

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      const updatedAlert = await apiClient.acknowledgeAlert(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? updatedAlert : a));
      return updatedAlert;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    }
  }, []);

  const resolveAlert = useCallback(async (alertId: string) => {
    try {
      const updatedAlert = await apiClient.resolveAlert(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? updatedAlert : a));
      return updatedAlert;
    } catch (err) {
      setError(handleApiError(err));
      throw err;
    }
  }, []);

  // Computed values
  const criticalAlerts = useMemo(() =>
    alerts.filter(alert => alert.severity === 'critical' && !alert.resolved), [alerts]
  );

  const unacknowledgedAlerts = useMemo(() =>
    alerts.filter(alert => !alert.acknowledged && !alert.resolved), [alerts]
  );

  // Fetch alerts on mount or when workerId changes
  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return {
    alerts,
    criticalAlerts,
    unacknowledgedAlerts,
    isLoading,
    error,
    fetchAlerts,
    acknowledgeAlert,
    resolveAlert,
    clearError: () => setError(null),
  };
}

/**
 * Hook for dashboard metrics with auto-refresh
 */
export function useDashboardMetrics() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refreshInterval = parseInt(
    process.env.NEXT_PUBLIC_METRICS_POLLING_INTERVAL || '30000'
  );

  const fetchMetrics = useCallback(async (isAutoRefresh = false) => {
    if (isAutoRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const data = await apiClient.getDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Auto-refresh metrics
  useEffect(() => {
    fetchMetrics();

    const interval = setInterval(() => {
      fetchMetrics(true);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  return {
    metrics,
    isLoading,
    isRefreshing,
    error,
    fetchMetrics,
    clearError: () => setError(null),
  };
}

/**
 * Hook for real-time worker data polling
 */
export function useRealTimeWorkerData(workerId: string) {
  const [biometricData, setBiometricData] = useState<BiometricData | null>(null);
  const [prediction, setPrediction] = useState<ThermalComfortPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const pollingInterval = parseInt(
    process.env.NEXT_PUBLIC_REALTIME_POLLING_INTERVAL || '5000'
  );

  const fetchRealTimeData = useCallback(async () => {
    try {
      const data = await apiClient.getRealTimeWorkerData(workerId);
      setBiometricData(data);

      // Get prediction for the current data
      const predictionResult = await apiClient.predictThermalComfort(data);
      setPrediction(predictionResult);

      setIsConnected(true);
      setError(null);
    } catch (err) {
      setError(handleApiError(err));
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [workerId]);

  // Start polling on mount
  useEffect(() => {
    if (!workerId) return;

    fetchRealTimeData();

    const interval = setInterval(fetchRealTimeData, pollingInterval);

    return () => clearInterval(interval);
  }, [fetchRealTimeData, pollingInterval, workerId]);

  return {
    biometricData,
    prediction,
    isLoading,
    error,
    isConnected,
    lastUpdate: biometricData?.timestamp,
    clearError: () => setError(null),
  };
}

/**
 * Hook for historical data analysis
 */
export function useHistoricalData(workerId: string, dateRange: { start: string; end: string }) {
  const [data, setData] = useState<HistoricalData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHistoricalData = useCallback(async () => {
    if (!workerId || !dateRange.start || !dateRange.end) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.getHistoricalData(
        workerId,
        dateRange.start,
        dateRange.end
      );
      setData(result);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [workerId, dateRange.start, dateRange.end]);

  // Fetch data when parameters change
  useEffect(() => {
    fetchHistoricalData();
  }, [fetchHistoricalData]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchHistoricalData,
    clearError: () => setError(null),
  };
}