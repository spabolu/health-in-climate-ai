/* eslint-disable no-console */
'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { BiometricData, DashboardMetrics } from '@/types/thermal-comfort';

interface TestResults {
  health?: { status: string; timestamp: string };
  randomData?: BiometricData[];
  metrics?: DashboardMetrics;
}

export default function TestAPIPage() {
  const [results, setResults] = useState<TestResults>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testAPI = async () => {
    setLoading(true);
    setError(null);
    const testResults: TestResults = {};

    try {
      console.log('🧪 Testing API connection...');

      // Test health check
      console.log('📡 Testing health check...');
      const health = await apiClient.healthCheck();
      testResults.health = health;
      console.log('✅ Health check passed:', health);

      // Test generate random data
      console.log('📊 Testing generate random data...');
      const randomData = await apiClient.generateRandomData();
      testResults.randomData = randomData;
      console.log('✅ Random data generated:', randomData);

      // Test dashboard metrics
      console.log('📈 Testing dashboard metrics...');
      const metrics = await apiClient.getDashboardMetrics();
      testResults.metrics = metrics;
      console.log('✅ Dashboard metrics loaded:', metrics);

      setResults(testResults);
      console.log('🎉 All API tests passed!');
    } catch (err) {
      console.error('❌ API test failed:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testAPI();
  }, []);

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">API Integration Test</h1>

      <div className="space-y-4">
        <button
          onClick={testAPI}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Run API Tests'}
        </button>

        {error && (
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            <h3 className="font-bold">Error:</h3>
            <p>{error}</p>
          </div>
        )}

        {Object.keys(results).length > 0 && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Test Results:</h2>

            {results.health && (
              <div className="p-4 bg-green-100 border border-green-400 rounded">
                <h3 className="font-bold">✅ Health Check:</h3>
                <pre className="text-sm">{JSON.stringify(results.health, null, 2)}</pre>
              </div>
            )}

            {results.randomData && (
              <div className="p-4 bg-blue-100 border border-blue-400 rounded">
                <h3 className="font-bold">📊 Random Data ({results.randomData.length} workers):</h3>
                <pre className="text-sm max-h-40 overflow-y-auto">
                  {JSON.stringify(results.randomData.slice(0, 2), null, 2)}
                  {results.randomData.length > 2 && '\n... and ' + (results.randomData.length - 2) + ' more'}
                </pre>
              </div>
            )}

            {results.metrics && (
              <div className="p-4 bg-purple-100 border border-purple-400 rounded">
                <h3 className="font-bold">📈 Dashboard Metrics:</h3>
                <pre className="text-sm">{JSON.stringify(results.metrics, null, 2)}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}