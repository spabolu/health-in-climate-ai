# HeatGuard Pro - Thermal Comfort Monitoring System

A comprehensive thermal comfort monitoring system with AI-powered heat stress prediction for workplace safety.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- npm or yarn package manager

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install flask flask-cors
   ```

3. **Start the backend server:**
   ```bash
   python simple_ml_server.py
   ```

   The backend will start on `http://localhost:8000` and serve:
   - Dashboard metrics endpoint: `/api/dashboard/metrics`
   - Health alerts endpoint: `/api/alerts`
   - Thermal comfort prediction: `/api/v1/predict`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will start on `http://localhost:3000` (or next available port like 3006)

## 🔧 System Architecture

### Backend (`simple_ml_server.py`)
- **Framework**: Flask with CORS support
- **Authentication**: API key-based (`heatguard-api-key-demo-12345`)
- **ML Model**: Custom thermal comfort prediction algorithm
- **Ports**: 8000

### Frontend (Next.js Application)
- **Framework**: Next.js 15 with TypeScript
- **UI**: Tailwind CSS + shadcn/ui components
- **State Management**: React hooks with custom API client
- **Ports**: 3000-3006 (automatically assigned)

## 📊 Available Features

### ✅ Currently Working
1. **Live Dashboard Metrics**
   - Total/active workers count
   - Environmental conditions (temperature, humidity)
   - Risk assessments and compliance scores

2. **Health Alerts System**
   - Real-time health alerts
   - Multiple severity levels (low, medium, high, critical)
   - Location-based tracking

3. **Thermal Comfort Prediction**
   - AI-powered heat stress analysis
   - Risk scoring and recommendations
   - Heat index calculations

### 🟡 Mock Implementation (Frontend Ready)
- Worker profile management
- Alert acknowledgment/resolution
- Historical data analysis
- Real-time biometric monitoring

## 🔗 API Integration

The frontend communicates with the backend via REST API:

```typescript
// Authentication header required for all requests
headers: {
  'X-API-Key': 'heatguard-api-key-demo-12345',
  'Content-Type': 'application/json'
}
```

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/metrics` | Live dashboard data |
| GET | `/api/alerts` | Health alerts list |
| POST | `/api/v1/predict` | Thermal comfort prediction |

### Example API Usage

**Dashboard Metrics:**
```bash
curl -H "X-API-Key: heatguard-api-key-demo-12345" \
     http://localhost:8000/api/dashboard/metrics
```

**Prediction:**
```bash
curl -X POST \
     -H "X-API-Key: heatguard-api-key-demo-12345" \
     -H "Content-Type: application/json" \
     -d '{"data":{"Gender":1,"Age":30,"Temperature":32,"Humidity":75,"HeartRate":95}}' \
     http://localhost:8000/api/v1/predict
```

## 🛠️ Development

### Frontend Development
```bash
# Development server
npm run dev

# Production build
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

### Backend Development
The backend uses a simple Flask server with:
- CORS enabled for frontend communication
- Mock data generation for demo purposes
- Simplified ML model for thermal comfort prediction

## 🚨 Troubleshooting

### "Failed to fetch" Errors
- ✅ **Fixed**: Authentication headers added
- ✅ **Fixed**: Endpoint paths corrected
- ✅ **Fixed**: CORS configuration updated

### Common Issues

1. **Backend not starting:**
   ```bash
   # Check if port 8000 is in use
   lsof -i :8000
   ```

2. **Frontend connection errors:**
   ```bash
   # Verify backend is running
   curl http://localhost:8000/api/dashboard/metrics \
        -H "X-API-Key: heatguard-api-key-demo-12345"
   ```

3. **Port conflicts:**
   - Backend uses port 8000 (fixed)
   - Frontend uses first available port (3000, 3006, etc.)

## 📁 Project Structure

```
health-in-climate-ai/
├── backend/
│   └── simple_ml_server.py          # Flask API server
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js pages
│   │   ├── components/              # Reusable UI components
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── lib/
│   │   │   ├── api-client.ts        # Backend API integration
│   │   │   └── utils.ts             # Utility functions
│   │   └── types/                   # TypeScript type definitions
│   ├── package.json
│   └── ...
└── README2.md                       # This file
```

## 🎯 Usage Examples

1. **Start both servers:**
   ```bash
   # Terminal 1: Backend
   cd backend && python simple_ml_server.py

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

2. **Access the application:**
   - Frontend: `http://localhost:3006` (or shown port)
   - Backend API: `http://localhost:8000`

3. **View live dashboard:**
   - Navigate to the dashboard to see real-time metrics
   - Alerts will appear automatically based on backend data
   - Environmental conditions update every 30 seconds

## 🔮 Future Enhancements

- Real database integration (currently using mock data)
- WebSocket support for real-time updates
- Advanced analytics and reporting
- Mobile application support
- Integration with IoT sensors

## 📞 Support

For issues or questions:
1. Check backend logs in terminal
2. Check browser console for frontend errors
3. Verify API authentication headers
4. Ensure both servers are running on correct ports