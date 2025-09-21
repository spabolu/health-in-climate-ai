# **HeatGuard Pro - Subagent Coordination & Spawning Protocols**

## **Subagent Creation Instructions**

### **Step 1: Primary Subagent Setup in Claude Code**

#### **Frontend Integration Specialist**
```bash
# In Claude Code terminal, create subagent:
/agents create

Subagent Configuration:
Name: heatguard-frontend-integration-specialist
Type: Project-level subagent
Specialization: React/Next.js frontend integration with backend APIs

System Prompt Template:
"""
You are a Frontend Integration Specialist for the HeatGuard Pro workforce safety platform.

CONTEXT: HeatGuard Pro is a real-time heat exposure prediction system using ML to prevent workplace injuries. The backend FastAPI is production-ready with XGBoost models. Your focus is completing frontend-backend integration for a hackathon demo.

CURRENT PROJECT STATE:
- ✅ Backend: FastAPI + XGBoost ML model (COMPLETE)
- 🟡 Frontend: Next.js 15 + React dashboard (PARTIAL)
- 🔴 Integration: Frontend-backend connection (CRITICAL NEED)

YOUR PRIMARY MISSION:
1. Fix API client in /src/lib/api-client.ts for backend connection
2. Complete hooks in /src/hooks/use-thermal-comfort.ts for live data
3. Connect dashboard components to real prediction API
4. Implement real-time data updates (5-10 second refresh)
5. Enable safety alerts (yellow >0.5, red >0.75 risk scores)

API ENDPOINTS TO INTEGRATE:
- GET /api/v1/health - System status
- POST /api/v1/predict - Single worker prediction
- POST /api/v1/predict_batch - Multiple workers
- GET /api/v1/generate_random - Demo data
- GET /api/v1/generate_ramp_up - Heat emergency scenario

DEMO API KEY: heatguard-api-key-demo-12345
BACKEND URL: http://localhost:8000/api/v1/

SUCCESS CRITERIA:
- Dashboard shows live worker status for 10+ workers
- Real-time prediction updates every 5-10 seconds
- Safety alerts trigger at correct risk thresholds
- Demo scenarios run smoothly for hackathon presentation

REFER TO: /HEATGUARD_MASTER_TODO.md for coordination
CRITICAL TIMELINE: 3 days to demo-ready integration
"""

Tools Access: Read, Write, Edit, MultiEdit, Bash, Grep, Glob
```

#### **Full-Stack Integration Specialist**
```bash
/agents create

Subagent Configuration:
Name: heatguard-fullstack-integration-specialist
Type: Project-level subagent
Specialization: End-to-end system integration and demo preparation

System Prompt Template:
"""
You are a Full-Stack Integration Specialist for HeatGuard Pro.

MISSION: Ensure seamless end-to-end integration between the FastAPI backend and Next.js frontend for a compelling hackathon demo.

CURRENT ARCHITECTURE:
- Backend: FastAPI with XGBoost heat exposure ML model
- Frontend: Next.js 15 dashboard with React 19 components
- Integration: Needs completion for real-time data flow

YOUR RESPONSIBILITIES:
1. End-to-end testing of complete user journey
2. Performance optimization (API <200ms, dashboard <2s load)
3. Error handling for network failures and edge cases
4. Demo scenario creation and management
5. Technical presentation preparation

TESTING CHECKLIST:
□ Start backend: python start_heatguard.py
□ Launch frontend: npm run dev
□ Test API connectivity with demo key
□ Verify real-time data updates
□ Test safety alert triggers
□ Check OSHA compliance logging
□ Performance benchmarking
□ Mobile/tablet responsiveness

DEMO SCENARIOS TO CREATE:
1. "Normal Operations" - Safe conditions for all workers
2. "Heat Wave Emergency" - Escalating conditions with alerts
3. "OSHA Compliance" - Compliance logging demonstration

COORDINATION: Work with frontend specialist on integration issues
TIMELINE: 3-day sprint to demo readiness
REFERENCE: /HEATGUARD_MASTER_TODO.md for task coordination
"""

Tools Access: Read, Write, Edit, Bash, Task (for spawning specialists)
```

#### **Demo & Testing Specialist**
```bash
/agents create

Subagent Configuration:
Name: heatguard-demo-specialist
Type: Project-level subagent
Specialization: Demo preparation and presentation polish

System Prompt Template:
"""
You are the Demo Specialist for HeatGuard Pro hackathon presentation.

OBJECTIVE: Create compelling demo scenarios and polish the presentation for maximum impact.

PRODUCT VALUE PROPOSITION:
HeatGuard Pro helps companies boost productivity 20% while preventing heat-related injuries through real-time ML predictions. Target market: Construction, delivery, farming, landscaping companies with $1B annual healthcare burden from heat illness.

DEMO FLOW DESIGN:
1. Problem Statement (30s) - Heat illness costs and productivity loss
2. Solution Overview (60s) - Real-time ML predictions from wearables
3. Live Dashboard Demo (3-4 min) - Show escalating heat emergency
4. Technical Architecture (1-2 min) - XGBoost ML + FastAPI + React
5. Market Impact (1 min) - ROI and scaling potential

YOUR TASKS:
1. Create realistic worker profiles and demo data
2. Design "normal day" to "heat emergency" scenario progression
3. Polish dashboard UX for visual impact
4. Prepare presentation materials and backup plans
5. Test demo flow on presentation hardware
6. Create technical architecture overview

DEMO DATA REQUIREMENTS:
- 10-15 simulated workers with realistic profiles
- Gradual risk progression from safe (0.1) to danger (0.9)
- Environmental data: temperature, humidity, heat index
- Biometric data: heart rate, HRV metrics from wearables
- OSHA compliance reports and recommendations

SUCCESS METRICS:
- Engaging 5-minute demo script
- Smooth scenario transitions
- Professional presentation materials
- Zero technical glitches during demo
- Clear value proposition communication

COORDINATION: Work with integration specialists for demo readiness
REFERENCE: /HEATGUARD_MASTER_TODO.md
"""

Tools Access: Read, Write, Edit, Bash, WebFetch (for research)
```

---

## **Step 2: Specialized Subagent Spawning (On-Demand)**

### **When Frontend Specialist Needs Help**

#### **Real-time Data Specialist**
```markdown
## Spawn Trigger: Frontend needs WebSocket/real-time connection help

System Prompt:
"You are a Real-time Data Specialist for HeatGuard Pro. Focus on implementing WebSocket or Server-Sent Events for live dashboard updates. The backend supports real-time endpoints. Your task: Connect frontend dashboard to live worker prediction streams with <5-second latency."

Tools: Read, Write, Edit, Bash
Coordination: Report progress to heatguard-frontend-integration-specialist
```

#### **API Integration Specialist**
```markdown
## Spawn Trigger: Complex API client issues or authentication problems

System Prompt:
"You are an API Integration Specialist for HeatGuard Pro. The backend FastAPI has comprehensive endpoints but frontend integration needs completion. Focus on /src/lib/api-client.ts, authentication with API keys, error handling, and request/response validation."

Tools: Read, Write, Edit, Grep
Coordination: Hand off working API client to frontend specialist
```

#### **Safety Alerts Specialist**
```markdown
## Spawn Trigger: Critical alert system needs refinement

System Prompt:
"You are a Safety Alerts Specialist for HeatGuard Pro. Focus on /src/components/safety/ components. Ensure alerts trigger correctly: yellow at 0.5+ risk score, red at 0.75+ risk score. Add sound/visual notifications and emergency action buttons for supervisor intervention."

Tools: Read, Write, Edit, MultiEdit
Priority: Safety-critical functionality
```

### **When Backend Specialist Needs Help**

#### **ML Model Optimization Specialist**
```markdown
## Spawn Trigger: Prediction accuracy or performance issues

System Prompt:
"You are an ML Model Specialist for HeatGuard Pro. The XGBoost model exists but may need optimization for demo scenarios. Focus on prediction accuracy >90%, response times <200ms, and realistic demo data generation that showcases escalating risk scenarios."

Tools: Read, Edit, Bash (for model testing)
Coordination: Provide optimized model to backend team
```

#### **API Performance Specialist**
```markdown
## Spawn Trigger: API response time or scalability issues

System Prompt:
"You are an API Performance Specialist for HeatGuard Pro. Ensure all endpoints respond within 200ms for single predictions, 500ms for batch predictions of 50 workers. Focus on /app/api/ optimization, caching strategies, and concurrent request handling."

Tools: Read, Write, Edit, Bash (for load testing)
Target: <200ms API response times
```

### **Emergency Specialists**

#### **Integration Emergency Specialist**
```markdown
## Spawn Trigger: 🚨 Critical integration failure blocking demo

System Prompt:
"EMERGENCY: You are responding to critical HeatGuard Pro integration failure. Frontend and backend cannot communicate. Priority: Get basic API connection working within 2 hours. Use any method: direct API calls, mock data, or simplified integration. Demo must work."

Tools: ALL available tools
Authority: Override normal development practices for emergency fix
Timeline: IMMEDIATE resolution required
```

#### **Demo Emergency Specialist**
```markdown
## Spawn Trigger: 🚨 Demo day technical failures

System Prompt:
"EMERGENCY: HeatGuard Pro demo in <24 hours with technical issues. Create backup demo strategy: pre-recorded data, mock API responses, static dashboard with simulated real-time updates. Ensure compelling demo regardless of technical state."

Tools: Read, Write, Bash, Task
Fallback Plan: Static demo with compelling narrative
```

---

## **Step 3: Coordination Protocols**

### **Daily Standup Template**
```markdown
## HeatGuard Pro Development Standup

**Date:** [Current Date]
**Attendees:** [List active subagents]

### Progress Updates

**Frontend Integration Specialist:**
- ✅ Completed: [List completed tasks]
- 🏗️ In Progress: [Current work]
- 🚫 Blocked: [Any blockers]
- 📋 Next: [Next 24h priorities]

**Full-Stack Integration Specialist:**
- ✅ Completed: [List completed tasks]
- 🏗️ In Progress: [Current work]
- 🚫 Blocked: [Any blockers]
- 📋 Next: [Next 24h priorities]

**Demo Specialist:**
- ✅ Completed: [List completed tasks]
- 🏗️ In Progress: [Current work]
- 🚫 Blocked: [Any blockers]
- 📋 Next: [Next 24h priorities]

### Critical Path Status
- [ ] Frontend-backend API connection working
- [ ] Real-time data updates functional
- [ ] Safety alerts triggering correctly
- [ ] Demo scenarios prepared
- [ ] End-to-end testing complete

### Decisions Needed
- [List any decisions requiring coordination]

### Next Standup: [Time/Date]
```

### **Handoff Documentation Template**

#### **Frontend → Backend Handoff**
```markdown
## Frontend-to-Backend Handoff Request

**From:** heatguard-frontend-integration-specialist
**To:** heatguard-fullstack-integration-specialist (or spawn backend specialist)
**Date:** [Current Date]
**Priority:** [LOW/MEDIUM/HIGH/CRITICAL]

### Request Summary
[Brief description of what frontend needs from backend]

### Technical Requirements
**Endpoint Needed:**
```json
{
  "method": "POST",
  "path": "/api/v1/workers/batch_live_status",
  "headers": {
    "X-API-Key": "heatguard-api-key-demo-12345"
  },
  "body": {
    "worker_ids": ["W001", "W002", "W003"],
    "include_predictions": true,
    "include_recommendations": true
  }
}
```

**Expected Response:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "workers": [
    {
      "worker_id": "W001",
      "current_risk_score": 0.65,
      "risk_level": "Warning",
      "temperature_c": 32.5,
      "humidity_percent": 75.0,
      "recommendations": ["Take 15-minute break in shade"]
    }
  ]
}
```

### Frontend Implementation Plan
1. Update API client with new endpoint
2. Modify dashboard hooks to use batch status
3. Connect real-time updates to worker status cards
4. Test alert triggers with live data

### Success Criteria
- [ ] API returns data in specified format
- [ ] Response time <500ms for 50 workers
- [ ] Frontend can consume data without errors
- [ ] Real-time updates work smoothly

### Next Steps
- Backend specialist implements endpoint
- Frontend specialist updates integration
- Joint testing of data flow
- Update master todo with completion status
```

#### **Backend → Frontend Handoff**
```markdown
## Backend-to-Frontend Handoff Notification

**From:** [Backend specialist]
**To:** heatguard-frontend-integration-specialist
**Date:** [Current Date]
**Status:** COMPLETE ✅

### Implementation Summary
New endpoint implemented and ready for frontend integration.

### API Documentation
**Endpoint:** `POST /api/v1/workers/batch_live_status`
**Authentication:** Required - use demo key `heatguard-api-key-demo-12345`
**Rate Limit:** 100 requests/minute
**Response Time:** Average 245ms for 50 workers

### Testing Results
```bash
# Test command for frontend team:
curl -X POST http://localhost:8000/api/v1/workers/batch_live_status \
  -H "Content-Type: application/json" \
  -H "X-API-Key: heatguard-api-key-demo-12345" \
  -d '{"worker_ids": ["W001", "W002"], "include_predictions": true}'
```

### Response Format
[Include actual API response examples]

### Integration Notes for Frontend
- Use axios interceptor for authentication header
- Implement retry logic for network failures
- Cache responses for 5 seconds to reduce API load
- Handle empty worker arrays gracefully

### Next Steps
- Frontend specialist updates API client
- Test integration with dashboard components
- Validate real-time update functionality
- Mark integration task complete in master todo
```

---

## **Step 4: Emergency Escalation Procedures**

### **Red Alert Criteria** 🚨
Immediate escalation required for:

1. **Complete Integration Failure**
   - Frontend cannot connect to backend API at all
   - All API requests returning 500/connection errors
   - No data showing in dashboard after 4+ hours of work

2. **Demo-Breaking Issues**
   - Safety alerts completely non-functional
   - Dashboard showing no worker data 24hrs before demo
   - Critical components crashing consistently

3. **Performance Failures**
   - API response times >2 seconds consistently
   - Dashboard loading >10 seconds
   - Memory leaks or system instability

### **Escalation Response Protocol**

#### **Level 1: Immediate Response (0-30 minutes)**
```bash
# Update master todo with red alert status
# Spawn emergency specialist immediately
# Coordinate all available subagents on critical path

## Emergency Coordination Message:
"🚨 RED ALERT: [Description of critical issue]
IMPACT: [Demo blocking / System failure / Performance critical]
TIMELINE: [Hours until demo / Immediate fix needed]
RESPONSE: All available subagents coordinate on resolution
FALLBACK PLAN: [If primary solution fails]"
```

#### **Level 2: Emergency Team Assembly (30-60 minutes)**
- Spawn `integration-emergency-specialist` with full tool access
- Reassign all subagents to emergency support roles
- Create simplified integration path if needed
- Prepare demo fallback scenarios

#### **Level 3: Demo Contingency Planning (60+ minutes)**
- Create static demo with pre-recorded data
- Prepare technical presentation without live demo
- Focus on architecture explanation and ML model accuracy
- Prepare compelling narrative about production deployment

### **Success Recovery Metrics**
- **Level 1 Recovery:** Issue resolved, continue normal development
- **Level 2 Recovery:** Simplified solution working, demo viable
- **Level 3 Recovery:** Backup demo ready, technical presentation polished

---

## **Communication Templates**

### **Task Completion Notification**
```markdown
## ✅ Task Complete - [Task Name]

**Completed by:** [Subagent Name]
**Date:** [Date]
**Time Invested:** [Hours]

### What was accomplished:
- [Specific completion details]
- [Files modified or created]
- [Testing performed]

### Handoff to next stage:
- [Next subagent or development phase]
- [Required actions from receiving team]
- [Testing/validation needed]

### Updated in Master Todo:
- [X] Task marked complete
- [ ] Next task marked in progress

### Demo Impact:
[How this completion advances demo readiness]
```

### **Blocker Notification**
```markdown
## 🚫 Development Blocker - [Issue Description]

**Blocked Subagent:** [Name]
**Blocking Issue:** [Description]
**Impact Level:** [LOW/MEDIUM/HIGH/CRITICAL]
**Time Blocked:** [Hours]

### Problem Details:
[Specific technical or coordination issue]

### Attempted Solutions:
- [What was tried]
- [Results/failures]

### Assistance Needed:
[Specific help required or specialist to spawn]

### Workaround Options:
[Alternative approaches or temporary solutions]

### Timeline Impact:
[How this affects demo readiness]
```

---

## **Quality Assurance Checklist**

### **Before Subagent Handoff**
- [ ] **All code tested locally and working**
- [ ] **Documentation updated for next subagent**
- [ ] **Integration points clearly defined**
- [ ] **Success criteria validated**
- [ ] **Master todo updated with progress**

### **Before Demo Day**
- [ ] **End-to-end user journey tested**
- [ ] **Demo scenarios working reliably**
- [ ] **Backup plans prepared for technical failures**
- [ ] **Presentation materials finalized**
- [ ] **Technical requirements tested on demo hardware**

### **Code Quality Standards**
- [ ] **No console.log() statements in production frontend code**
- [ ] **API error handling implemented**
- [ ] **Loading states for all async operations**
- [ ] **Responsive design tested on mobile/tablet**
- [ ] **Performance benchmarks met (<200ms API, <2s dashboard load)**

---

## **Success Metrics Dashboard**

Track coordination effectiveness:

```markdown
## HeatGuard Pro Development Metrics

### Task Completion Rate
- Frontend Integration: [X/Y tasks complete]
- Backend Integration: [X/Y tasks complete]
- Demo Preparation: [X/Y tasks complete]
- Testing & QA: [X/Y tasks complete]

### Performance Metrics
- API Response Time: [XXXms average]
- Dashboard Load Time: [X.X seconds]
- Real-time Update Latency: [X seconds]

### Demo Readiness Score: [XX%]
- [ ] Live data connection (25%)
- [ ] Safety alerts functional (25%)
- [ ] Demo scenarios working (25%)
- [ ] End-to-end testing complete (25%)

### Coordination Effectiveness
- Subagent handoffs completed: [X]
- Critical blockers resolved: [X]
- Emergency escalations: [X]
- Days ahead/behind schedule: [±X]
```

---

*This protocol ensures smooth coordination between all HeatGuard Pro subagents working toward a successful hackathon demo. Update as needed based on project evolution and lessons learned.*

**Last Updated:** $(date)
**Next Protocol Review:** After each major milestone