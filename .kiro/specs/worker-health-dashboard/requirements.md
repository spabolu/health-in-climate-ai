# Requirements Document

## Introduction

The Worker Health Dashboard is a professional web application that displays real-time health monitoring data for workers using HRV (Heart Rate Variability) and environmental sensors. The system integrates with an existing ML backend to provide risk assessment scores and enables simulation of health status changes for demonstration purposes. This MVP is designed for hackathon presentation, focusing on clear visualization of worker health status through a color-coded risk assessment system.

## Requirements

### Requirement 1

**User Story:** As a safety manager, I want to view a list of all monitored workers with their current health status, so that I can quickly identify workers at risk.

#### Acceptance Criteria

1. WHEN the dashboard loads THEN the system SHALL display a table of all workers with randomly generated names
2. WHEN displaying worker data THEN the system SHALL show all 55 health metrics (Gender, Age, 53 HRV metrics, Temperature, Humidity) for each worker
3. WHEN a worker's risk score is calculated THEN the system SHALL display a color-coded indicator ranging from green (0.0 risk) to red (1.0 risk)
4. WHEN the risk score changes THEN the system SHALL update the color indicator in real-time to reflect the new risk level

### Requirement 2

**User Story:** As a demonstration user, I want to simulate health deterioration for a specific worker, so that I can show how the system responds to changing health conditions.

#### Acceptance Criteria

1. WHEN I click the "Simulate Heat Up" button THEN the system SHALL gradually increase health risk values for worker "John Doe"
2. WHEN simulating heat up THEN the system SHALL send progressively higher temperature and humidity values to the backend model
3. WHEN simulation is active THEN the system SHALL query the backend model continuously and update the risk score display
4. WHEN the risk score increases THEN the system SHALL transition the color indicator from green toward red
5. IF I click a "View" button during simulation THEN the system SHALL display the current values being sent to the model

### Requirement 3

**User Story:** As a demonstration user, I want to simulate health recovery for a specific worker, so that I can show how the system responds to improving health conditions.

#### Acceptance Criteria

1. WHEN I click the "Cool Down" button THEN the system SHALL gradually decrease health risk values for worker "John Doe"
2. WHEN simulating cool down THEN the system SHALL send progressively lower temperature and humidity values to the backend model
3. WHEN cool down is active THEN the system SHALL query the backend model continuously and update the risk score display
4. WHEN the risk score decreases THEN the system SHALL transition the color indicator from red toward green

### Requirement 4

**User Story:** As a system integrator, I want the dashboard to communicate with the existing backend model, so that risk assessments are based on real ML predictions.

#### Acceptance Criteria

1. WHEN sending worker data to the backend THEN the system SHALL format data with all 55 required features
2. WHEN receiving backend response THEN the system SHALL extract risk_score, predicted_class, and confidence values
3. WHEN the backend returns a risk_score THEN the system SHALL convert the 0-1 range to appropriate color coding
4. IF the backend is unavailable THEN the system SHALL display an appropriate error message

### Requirement 5

**User Story:** As a hackathon judge, I want to see a professional-looking dashboard interface, so that I can evaluate the solution's presentation quality.

#### Acceptance Criteria

1. WHEN viewing the dashboard THEN the system SHALL display a clean, professional table layout
2. WHEN displaying worker information THEN the system SHALL organize data in clearly labeled columns
3. WHEN showing risk indicators THEN the system SHALL use intuitive color coding (green = safe, red = danger)
4. WHEN displaying simulation controls THEN the system SHALL provide clearly labeled buttons for heat up and cool down actions
5. WHEN the interface loads THEN the system SHALL be responsive and work without requiring additional setup or configuration