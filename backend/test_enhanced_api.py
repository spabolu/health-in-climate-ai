#!/usr/bin/env python3
"""
Test script for Enhanced HeatGuard Pro API
==========================================

Tests all the key endpoints to ensure they work correctly.
Run this after starting the enhanced API server.
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single API endpoint."""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)

        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - OK")
            return response.json()
        else:
            print(f"❌ {method} {endpoint} - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return None

def main():
    print("🧪 TESTING ENHANCED HEATGUARD PRO API")
    print("=" * 50)

    print("\n1. Testing Basic Health Check...")
    health = test_endpoint("/health")

    print("\n2. Testing API Documentation...")
    docs = test_endpoint("/api")

    print("\n3. Testing Worker Management...")
    workers = test_endpoint("/api/workers")
    if workers:
        print(f"   📊 Found {len(workers)} demo workers")

        # Test getting a specific worker
        if workers:
            worker_id = workers[0]['id']
            test_endpoint(f"/api/workers/{worker_id}")

    print("\n4. Testing Dashboard Metrics...")
    metrics = test_endpoint("/api/dashboard_metrics")
    if metrics:
        print(f"   📊 Active workers: {metrics.get('active_workers', 'N/A')}")
        print(f"   🚨 Critical alerts: {metrics.get('critical_alerts', 'N/A')}")

    print("\n5. Testing Alerts System...")
    alerts = test_endpoint("/api/alerts")
    if alerts:
        print(f"   🚨 Found {len(alerts)} alerts")

    print("\n6. Testing Data Generation...")
    test_data = test_endpoint("/api/generate_random_data?count=3")
    if test_data:
        print(f"   🎲 Generated {test_data.get('count', 0)} test samples")

    print("\n7. Testing Thermal Comfort Prediction...")
    if test_data and test_data.get('data'):
        sample = test_data['data'][0]
        prediction = test_endpoint("/api/predict_thermal_comfort", "POST", sample)
        if prediction:
            print(f"   🧠 Prediction: {prediction.get('prediction', 'N/A')}")
            print(f"   📊 Risk: {prediction.get('risk_assessment', 'N/A')}")

    print("\n8. Testing Real-time Worker Data...")
    if workers:
        worker_id = workers[0]['id']
        realtime = test_endpoint(f"/api/workers/{worker_id}/realtime")
        if realtime:
            print(f"   ⚡ Real-time data available for worker {worker_id}")

    print("\n9. Testing Historical Data...")
    if workers:
        worker_id = workers[0]['id']
        historical = test_endpoint(f"/api/workers/{worker_id}/historical")
        if historical:
            readings_count = len(historical.get('readings', []))
            predictions_count = len(historical.get('predictions', []))
            print(f"   📈 Historical data: {readings_count} readings, {predictions_count} predictions")

    print("\n" + "=" * 50)
    print("🏁 API TESTING COMPLETE")
    print("\nIf all tests show ✅, your enhanced API is ready for frontend integration!")

if __name__ == "__main__":
    print("⏳ Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    main()