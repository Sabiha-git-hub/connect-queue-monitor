# Requirements Document

## Introduction

This document specifies requirements for enhancing the Amazon Connect Queue Monitor application with automatic agent detection, comprehensive performance metrics, and professional branding. The enhancements enable contact center agents to view their personal performance metrics and overall call center status without manual login when embedded in the Amazon Connect agent workspace.

## Glossary

- **Agent_Dashboard**: The web application that displays agent performance metrics and call center status
- **Streams_API**: Amazon Connect Streams JavaScript API for accessing agent session information
- **Agent_Workspace**: Amazon Connect's native agent interface where third-party applications can be embedded
- **Connect_API**: Amazon Connect service API accessed via boto3 for retrieving metrics and agent data
- **Agent_Username**: The unique identifier for an agent in Amazon Connect
- **Instance_Timezone**: The timezone configured for the Amazon Connect instance (EST/EDT for us-east-1)
- **Historical_Metrics**: Metrics calculated from midnight to current time in Instance_Timezone
- **Real_Time_Metrics**: Metrics reflecting current state updated within 60 seconds
- **Embedded_Mode**: Application running within Agent_Workspace iframe
- **Standalone_Mode**: Application running in a separate browser tab outside Agent_Workspace
- **Brand_Colors**: Color palette derived from organization logo (#0c072d primary)
- **ACW**: After Contact Work state where agents complete post-call tasks

## Requirements

### Requirement 1: Automatic Agent Detection

**User Story:** As a contact center agent, I want the application to automatically detect who I am when embedded in Amazon Connect, so that I don't need to manually log in every time.

#### Acceptance Criteria

1. WHEN the Agent_Dashboard loads in Embedded_Mode, THE Agent_Dashboard SHALL initialize Streams_API
2. WHEN Streams_API successfully connects, THE Agent_Dashboard SHALL retrieve the Agent_Username from the agent session
3. WHEN Agent_Username is retrieved, THE Agent_Dashboard SHALL display agent metrics without requiring manual login
4. WHEN a different agent logs into Amazon Connect on the same computer, THE Agent_Dashboard SHALL detect the new Agent_Username and update displayed metrics
5. IF Streams_API initialization fails, THEN THE Agent_Dashboard SHALL display a manual login form
6. WHEN the Agent_Dashboard loads in Standalone_Mode, THE Agent_Dashboard SHALL display a manual login form
7. WHEN Streams_API connection is established, THE Agent_Dashboard SHALL complete initialization within 5 seconds

### Requirement 2: Agent Performance Metrics Display

**User Story:** As a contact center agent, I want to see my personal performance metrics for today, so that I can understand how I'm performing.

#### Acceptance Criteria

1. WHEN an agent is authenticated, THE Agent_Dashboard SHALL retrieve Historical_Metrics from midnight to current time in Instance_Timezone
2. THE Agent_Dashboard SHALL display the total number of contacts handled by the agent today
3. THE Agent_Dashboard SHALL display the total number of contacts transferred by the agent to other agents or queues today
4. THE Agent_Dashboard SHALL display the total number of contacts that rang the agent but were not answered today
5. THE Agent_Dashboard SHALL display the average handle time in minutes and seconds for contacts handled by the agent today
6. THE Agent_Dashboard SHALL display the occupancy percentage representing time the agent was busy today
7. WHEN Historical_Metrics are unavailable, THE Agent_Dashboard SHALL display zero values with an informational message
8. THE Agent_Dashboard SHALL refresh Historical_Metrics every 60 seconds
9. WHEN calculating average handle time, THE Agent_Dashboard SHALL include talk time and hold time but exclude ACW time
10. THE Agent_Dashboard SHALL display occupancy as a percentage between 0 and 100 with one decimal place

### Requirement 3: Call Center Overview Metrics Display

**User Story:** As a contact center agent, I want to see the overall call center status, so that I understand how busy the center is and how many colleagues are available.

#### Acceptance Criteria

1. THE Agent_Dashboard SHALL retrieve Real_Time_Metrics for all agents in the Amazon Connect instance
2. THE Agent_Dashboard SHALL display the total count of agents currently logged in
3. THE Agent_Dashboard SHALL display the count of agents in Available state ready to take contacts
4. THE Agent_Dashboard SHALL display the count of agents currently handling contacts
5. THE Agent_Dashboard SHALL display the count of agents in ACW state
6. THE Agent_Dashboard SHALL refresh Real_Time_Metrics every 30 seconds
7. WHEN Real_Time_Metrics are unavailable, THE Agent_Dashboard SHALL display the last known values with a staleness indicator
8. THE Agent_Dashboard SHALL display metric update timestamps in Instance_Timezone

### Requirement 4: Queue Metrics Integration

**User Story:** As a contact center agent, I want to continue seeing queue metrics alongside my personal metrics, so that I have a complete view of the call center.

#### Acceptance Criteria

1. THE Agent_Dashboard SHALL preserve existing queue metrics display functionality
2. THE Agent_Dashboard SHALL display contacts in queue for each monitored queue
3. THE Agent_Dashboard SHALL refresh queue metrics every 30 seconds
4. THE Agent_Dashboard SHALL display agent performance metrics, call center overview metrics, and queue metrics on the same page

### Requirement 5: Application Branding

**User Story:** As a contact center manager, I want the application to display our organization's branding, so that it looks professional and matches our corporate identity.

#### Acceptance Criteria

1. THE Agent_Dashboard SHALL display the organization logo from app/static/images/logo.png in the application header
2. THE Agent_Dashboard SHALL apply Brand_Colors to the application header background
3. THE Agent_Dashboard SHALL apply Brand_Colors to primary action buttons
4. THE Agent_Dashboard SHALL use a color scheme derived from Brand_Colors for metric badges and status indicators
5. WHEN the logo file is missing, THE Agent_Dashboard SHALL display the application title text without failing to load
6. THE Agent_Dashboard SHALL maintain readable contrast ratios of at least 4.5:1 between text and backgrounds
7. THE Agent_Dashboard SHALL apply consistent spacing and typography throughout the interface

### Requirement 6: Metrics Data Retrieval

**User Story:** As a system administrator, I want the application to efficiently retrieve metrics from Amazon Connect APIs, so that the dashboard performs well and doesn't exceed API rate limits.

#### Acceptance Criteria

1. WHEN retrieving Historical_Metrics, THE Connect_API SHALL use the GetMetricDataV2 API operation
2. WHEN retrieving Real_Time_Metrics, THE Connect_API SHALL use the GetCurrentMetricData API operation
3. THE Connect_API SHALL include error handling for API throttling responses
4. IF an API request is throttled, THEN THE Connect_API SHALL implement exponential backoff with a maximum of 3 retry attempts
5. THE Connect_API SHALL cache metric responses for 15 seconds to reduce redundant API calls
6. WHEN multiple agents view the dashboard simultaneously, THE Connect_API SHALL batch requests where possible
7. THE Connect_API SHALL log API errors with sufficient detail for troubleshooting

### Requirement 7: Session Management

**User Story:** As a contact center agent, I want my session to remain active while I'm working, so that I don't lose access to my metrics during my shift.

#### Acceptance Criteria

1. WHEN an agent is authenticated in Embedded_Mode, THE Agent_Dashboard SHALL maintain the session while Streams_API connection is active
2. WHEN Streams_API connection is lost, THE Agent_Dashboard SHALL attempt to reconnect every 10 seconds for up to 5 minutes
3. IF reconnection fails after 5 minutes, THEN THE Agent_Dashboard SHALL display a connection error message
4. WHEN an agent is authenticated in Standalone_Mode, THE Agent_Dashboard SHALL maintain the session for 8 hours
5. WHEN a session expires in Standalone_Mode, THE Agent_Dashboard SHALL redirect to the login form
6. THE Agent_Dashboard SHALL store session state in browser sessionStorage not localStorage

### Requirement 8: Error Handling and User Feedback

**User Story:** As a contact center agent, I want clear error messages when something goes wrong, so that I know what action to take.

#### Acceptance Criteria

1. WHEN Streams_API fails to initialize, THE Agent_Dashboard SHALL display a message indicating automatic detection failed and manual login is required
2. WHEN Connect_API returns an authentication error, THE Agent_Dashboard SHALL display a message indicating invalid credentials
3. WHEN Connect_API returns a permission error, THE Agent_Dashboard SHALL display a message indicating insufficient permissions
4. WHEN network connectivity is lost, THE Agent_Dashboard SHALL display a message indicating connection issues
5. WHEN metrics fail to load, THE Agent_Dashboard SHALL display the error without hiding previously loaded metrics
6. THE Agent_Dashboard SHALL display loading indicators while fetching metrics
7. THE Agent_Dashboard SHALL remove loading indicators within 10 seconds regardless of API response status

### Requirement 9: Responsive Layout

**User Story:** As a contact center agent, I want the dashboard to work well in the Amazon Connect agent workspace panel, so that I can view all metrics without excessive scrolling.

#### Acceptance Criteria

1. THE Agent_Dashboard SHALL display all metric sections in a vertical layout optimized for panel widths between 400 and 800 pixels
2. THE Agent_Dashboard SHALL use responsive font sizes that remain readable at minimum panel width
3. THE Agent_Dashboard SHALL organize metrics into clearly labeled sections with visual separation
4. THE Agent_Dashboard SHALL display metric values with appropriate formatting (numbers with commas, percentages with % symbol, times in HH:MM:SS format)
5. WHEN the viewport height is less than 600 pixels, THE Agent_Dashboard SHALL enable vertical scrolling
6. THE Agent_Dashboard SHALL maintain fixed header positioning while scrolling metric content

### Requirement 10: Configuration Management

**User Story:** As a system administrator, I want to configure the Amazon Connect instance details without modifying code, so that I can deploy the application to different environments easily.

#### Acceptance Criteria

1. THE Agent_Dashboard SHALL read Amazon Connect instance ID from environment configuration
2. THE Agent_Dashboard SHALL read AWS region from environment configuration
3. THE Agent_Dashboard SHALL read Instance_Timezone from environment configuration
4. THE Agent_Dashboard SHALL validate required configuration values at application startup
5. IF required configuration is missing, THEN THE Agent_Dashboard SHALL log an error and fail to start
6. THE Agent_Dashboard SHALL support configuration via environment variables
7. THE Agent_Dashboard SHALL not expose AWS credentials in client-side code or API responses
