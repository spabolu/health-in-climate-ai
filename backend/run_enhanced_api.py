#!/usr/bin/env python3
"""
HeatGuard Pro Enhanced API Startup Script
==========================================

Starts the enhanced Flask API with all features:
- Worker management (100 demo workers)
- Dashboard metrics
- Real-time alerts
- Historical data
- All API endpoints needed by frontend

Usage: python run_enhanced_api.py
"""

import os
import sys

def main():
    print("🌡️ HEATGUARD PRO - ENHANCED API SERVER")
    print("=" * 50)

    try:
        from enhanced_flask_app import initialize_application, app

        # Initialize everything
        if initialize_application():
            print("\n🌐 Enhanced API Features:")
            print("✅ 100+ simulated workers with profiles")
            print("✅ Worker management (CRUD operations)")
            print("✅ Dashboard metrics & analytics")
            print("✅ Real-time health alerts")
            print("✅ Historical data tracking")
            print("✅ OSHA compliance recommendations")
            print("✅ In-memory storage (no database needed)")

            print("\n📋 Key API Endpoints:")
            print("   • GET  /api/workers - Worker management")
            print("   • GET  /api/dashboard_metrics - Dashboard data")
            print("   • GET  /api/alerts - Health alerts")
            print("   • POST /api/predict_thermal_comfort - ML predictions")
            print("   • GET  /api/workers/{id}/realtime - Live monitoring")
            print("   • GET  /api/workers/{id}/historical - Trends & history")

            print("\n🚀 Starting enhanced server...")
            print("📡 Frontend should connect to: http://localhost:5000")
            print("🔗 API documentation: http://localhost:5000/api")
            print("\n⚠️  Press Ctrl+C to stop")
            print("=" * 50)

            # Start the enhanced server
            app.run(
                debug=True,
                host='0.0.0.0',
                port=5000,
                threaded=True
            )

        else:
            print("❌ Failed to initialize enhanced application")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Enhanced API server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()