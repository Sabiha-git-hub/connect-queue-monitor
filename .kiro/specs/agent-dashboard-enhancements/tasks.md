# Implementation Plan: Agent Dashboard Enhancements

## Overview

This implementation plan covers three main enhancements to the Amazon Connect Queue Monitor application:

1. **Automatic Agent Detection** - Already implemented in index.html via Streams API but not yet deployed
2. **Agent Performance Metrics** - Display agent-specific metrics (contacts handled, transfers, missed calls, handle time, occupancy) and call center overview (agents logged in, available, on contact, in ACW)
3. **Application Branding** - Apply professional branding with logo and color scheme (PRIMARY FOCUS)

The implementation follows a phased approach, prioritizing branding first as requested, then metrics functionality, and finally integration and testing.

## Tasks

- [x] 1. Implement application branding with logo and color scheme
  - [x] 1.1 Update CSS with branded color palette
    - Add CSS variables for brand colors (#0c072d primary, derived palette)
    - Apply brand colors to header background with gradient
    - Style primary action buttons with brand colors
    - Create metric badge styles with brand-derived colors
    - Ensure WCAG AA contrast ratios (4.5:1 minimum)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 5.7_
  
  - [ ]* 1.2 Write property test for contrast ratio compliance
    - **Property 13: Contrast Ratio Compliance**
    - **Validates: Requirements 5.6**
  
  - [x] 1.3 Update HTML templates with logo and branded header
    - Add logo image to header in index.html
    - Add logo image to header in queue_view.html
    - Implement graceful fallback if logo missing
    - Apply consistent header styling across templates
    - _Requirements: 5.1, 5.5_
  
  - [x] 1.4 Apply responsive typography and spacing
    - Define responsive font sizes for panel widths 400-800px
    - Apply consistent spacing throughout interface
    - Test readability at minimum panel width
    - _Requirements: 5.7, 9.2_

- [ ] 2. Create backend metrics service and API endpoints
  - [x] 2.1 Create metrics_service.py with data models
    - Define AgentMetrics dataclass (contacts, transfers, missed, handle time, occupancy)
    - Define OverviewMetrics dataclass (logged in, available, on contact, ACW)
    - Implement MetricsService class with caching (15 second TTL)
    - Implement timezone conversion utilities (UTC to instance timezone)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.2, 3.3, 3.4, 3.5, 10.3_
  
  - [ ]* 2.2 Write property test for historical metrics time range calculation
    - **Property 4: Historical Metrics Time Range Calculation**
    - **Validates: Requirements 2.1**
  
  - [x] 2.3 Implement agent metrics retrieval method
    - Implement get_agent_metrics() with cache check
    - Calculate time range from midnight to now in instance timezone
    - Call GetMetricDataV2 API with agent filter
    - Extract and transform metrics data
    - Calculate average handle time (talk + hold, exclude ACW)
    - Calculate occupancy percentage with one decimal place
    - Cache results with 15 second TTL
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.9, 2.10, 6.5_
  
  - [ ]* 2.4 Write property test for handle time calculation
    - **Property 7: Handle Time Calculation Excludes ACW**
    - **Validates: Requirements 2.9**
  
  - [ ]* 2.5 Write property test for occupancy formatting
    - **Property 8: Occupancy Formatting**
    - **Validates: Requirements 2.10**
  
  - [x] 2.6 Implement call center overview metrics retrieval method
    - Implement get_overview_metrics() with cache check
    - Call GetCurrentMetricData API for all agents
    - Count agents by state (logged in, available, on contact, ACW)
    - Cache results with 15 second TTL
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.5_
  
  - [ ]* 2.7 Write unit tests for metrics service
    - Test get_agent_metrics with successful data
    - Test get_agent_metrics with no data (edge case)
    - Test get_overview_metrics with successful data
    - Test cache hit within TTL
    - Test cache miss after TTL
    - Test calculate_handle_time with zero contacts (edge case)
    - Test calculate_occupancy with zero time (edge case)

- [ ] 3. Enhance Connect client with metrics API methods
  - [x] 3.1 Add get_metric_data_v2() method to connect_client.py
    - Implement GetMetricDataV2 API wrapper
    - Add parameters for time range, filters, metrics, groupings
    - Implement exponential backoff retry logic (1s, 2s, 4s, max 3 retries)
    - Add error handling for throttling, auth, and network errors
    - Add logging for API calls and errors
    - _Requirements: 6.1, 6.3, 6.4, 6.7_
  
  - [ ]* 3.2 Write property test for API retry with exponential backoff
    - **Property 14: API Retry with Exponential Backoff**
    - **Validates: Requirements 6.4**
  
  - [ ]* 3.3 Write property test for metrics response caching
    - **Property 15: Metrics Response Caching**
    - **Validates: Requirements 6.5**
  
  - [ ]* 3.4 Write unit tests for connect client enhancements
    - Test get_metric_data_v2 successful call
    - Test throttling retry with exponential backoff
    - Test max retries exceeded (fail after 3 attempts)
    - Test exponential backoff timing (1s, 2s, 4s)

- [ ] 4. Add new API routes for metrics endpoints
  - [x] 4.1 Add GET /agent/metrics endpoint
    - Validate session contains agent_username
    - Call metrics_service.get_agent_metrics()
    - Return JSON response with agent metrics
    - Handle errors (auth required, API failures)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.2, 8.3_
  
  - [x] 4.2 Add GET /agent/overview endpoint
    - Validate session contains agent_username
    - Call metrics_service.get_overview_metrics()
    - Return JSON response with overview metrics
    - Handle errors (auth required, API failures)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 8.2, 8.3_
  
  - [ ] 4.3 Add GET /health endpoint for monitoring
    - Check AWS API connectivity
    - Return healthy/unhealthy status with timestamp
    - _Requirements: 6.7_
  
  - [ ]* 4.4 Write unit tests for new routes
    - Test /agent/metrics with authenticated session
    - Test /agent/metrics without authentication (401)
    - Test /agent/overview with authenticated session
    - Test error response format
    - Test /health endpoint

- [ ] 5. Checkpoint - Backend implementation complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Create frontend dashboard application logic
  - [ ] 6.1 Create app.js with AgentDashboard class
    - Implement AgentDashboard class with state management
    - Implement fetchAgentMetrics() method
    - Implement fetchOverviewMetrics() method
    - Implement fetchQueueMetrics() method (integrate existing)
    - Implement auto-refresh timers (60s for agent, 30s for overview/queues)
    - Implement error handling that preserves previous data
    - _Requirements: 2.8, 3.6, 4.3, 8.5, 8.6_
  
  - [ ]* 6.2 Write property test for metrics refresh intervals
    - **Property 6: Metrics Refresh Interval**
    - **Validates: Requirements 2.8, 3.6, 4.3**
  
  - [ ] 6.3 Implement UI update methods for metrics display
    - Implement updateAgentMetricsDisplay() with all five metrics
    - Implement updateOverviewMetricsDisplay() with all four counts
    - Implement updateQueueMetricsDisplay() (integrate existing)
    - Format metric values (commas, percentages, time HH:MM:SS)
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 3.2, 3.3, 3.4, 3.5, 9.4_
  
  - [ ]* 6.4 Write property test for metric value formatting
    - **Property 20: Metric Value Formatting**
    - **Validates: Requirements 9.4**
  
  - [ ] 6.5 Implement error handling and loading states
    - Create ErrorHandler class with error categorization
    - Implement loading indicators (skeleton loaders)
    - Implement error banners that don't hide previous data
    - Implement staleness indicators for old data
    - Remove loading indicators within 10 seconds
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_
  
  - [ ]* 6.5 Write property test for error display without data loss
    - **Property 19: Error Display Without Data Loss**
    - **Validates: Requirements 8.5**
  
  - [ ]* 6.6 Write unit tests for dashboard application
    - Test dashboard initialization
    - Test fetchAgentMetrics success
    - Test fetchAgentMetrics error preserves data
    - Test auto-refresh intervals
    - Test display staleness indicator

- [ ] 7. Enhance Streams API integration for automatic detection
  - [ ] 7.1 Add timeout handling to streams.js
    - Implement 5 second timeout for Streams API initialization
    - Fall back to manual login on timeout
    - _Requirements: 1.5, 1.7_
  
  - [ ] 7.2 Add agent change detection to streams.js
    - Subscribe to agent refresh events
    - Detect when agent username changes
    - Trigger dashboard update on agent change
    - _Requirements: 1.4_
  
  - [ ]* 7.3 Write property test for agent change detection
    - **Property 3: Agent Change Detection**
    - **Validates: Requirements 1.4**
  
  - [ ] 7.4 Add reconnection logic to streams.js
    - Implement reconnection attempts every 10 seconds
    - Limit reconnection attempts to 5 minutes (30 attempts)
    - Display connection error after max attempts
    - _Requirements: 7.2, 7.3_
  
  - [ ]* 7.5 Write property test for reconnection attempt intervals
    - **Property 17: Reconnection Attempt Intervals**
    - **Validates: Requirements 7.2**
  
  - [ ]* 7.6 Write unit tests for Streams integration
    - Test Streams initialization in embedded mode
    - Test Streams initialization timeout (5 seconds)
    - Test agent change detection
    - Test reconnection logic

- [ ] 8. Update HTML templates with metrics sections
  - [x] 8.1 Update queue_view.html with agent metrics section
    - Add "My Performance Today" section with metric cards
    - Display contacts handled, transfers, missed, handle time, occupancy
    - Apply responsive grid layout (2 columns on narrow, 4 on wide)
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6, 9.1, 9.3_
  
  - [ ] 8.2 Add call center overview section to queue_view.html
    - Add "Call Center Overview" section with metric cards
    - Display agents logged in, available, on contact, in ACW
    - Apply consistent styling with agent metrics
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 9.3_
  
  - [x] 8.3 Preserve existing queue metrics section
    - Ensure queue metrics display below overview metrics
    - Maintain existing queue refresh functionality
    - _Requirements: 4.1, 4.2, 4.4_
  
  - [ ] 8.4 Add loading and error state templates
    - Add skeleton loader templates for metrics
    - Add error banner template
    - Add staleness indicator template
    - _Requirements: 8.6, 8.7_
  
  - [ ] 8.5 Implement responsive layout for embedded panel
    - Test layout at 400px, 600px, 800px widths
    - Enable vertical scrolling for viewport height < 600px
    - Implement fixed header with scrollable content
    - _Requirements: 9.1, 9.2, 9.5, 9.6_

- [ ] 9. Checkpoint - Frontend implementation complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement session management enhancements
  - [ ] 10.1 Add session persistence for embedded mode
    - Tie session to Streams API connection state
    - Maintain session while Streams API connected
    - _Requirements: 7.1_
  
  - [ ]* 10.2 Write property test for session persistence in embedded mode
    - **Property 16: Session Persistence in Embedded Mode**
    - **Validates: Requirements 7.1**
  
  - [ ] 10.3 Add session timeout for standalone mode
    - Implement 8 hour session timeout
    - Redirect to login on session expiration
    - Store session state in sessionStorage (not localStorage)
    - _Requirements: 7.4, 7.5, 7.6_
  
  - [ ]* 10.4 Write property test for standalone session timeout
    - **Property 18: Standalone Session Timeout**
    - **Validates: Requirements 7.4**

- [ ] 11. Add configuration validation and security checks
  - [ ] 11.1 Implement configuration validation in config/settings.py
    - Validate required environment variables at startup
    - Validate timezone format
    - Log validation errors with clear messages
    - Fail application startup if configuration invalid
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [ ] 11.2 Ensure AWS credentials never exposed to client
    - Audit all API responses for credential leakage
    - Audit client-side JavaScript for credential references
    - Add security checks in routes
    - _Requirements: 10.7_
  
  - [ ]* 11.3 Write property test for credentials exclusion from client code
    - **Property 21: Credentials Exclusion from Client Code**
    - **Validates: Requirements 10.7**

- [ ] 12. Integration testing and end-to-end validation
  - [ ]* 12.1 Test embedded mode automatic detection flow
    - Load page in iframe context
    - Verify Streams API initializes
    - Verify agent username extracted
    - Verify auto-login succeeds
    - Verify all three metric sections display
    - Verify auto-refresh works
    - _Requirements: 1.1, 1.2, 1.3, 1.7_
  
  - [ ]* 12.2 Test standalone mode manual login flow
    - Load page in browser
    - Verify login form displays
    - Enter username and submit
    - Verify manual login succeeds
    - Verify all three metric sections display
    - Verify session persists for 8 hours
    - _Requirements: 1.6, 7.4_
  
  - [ ]* 12.3 Test error recovery and graceful degradation
    - Load dashboard with metrics
    - Simulate API failure
    - Verify error message displays
    - Verify previous metrics still visible
    - Verify auto-retry succeeds
    - Verify error message clears
    - _Requirements: 8.5_
  
  - [ ]* 12.4 Test branding and responsive layout
    - Verify logo displays in header
    - Verify brand colors applied correctly
    - Test layout at 400px, 600px, 800px widths
    - Verify contrast ratios meet WCAG AA
    - Test with missing logo file (graceful fallback)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 9.1, 9.2_

- [ ] 13. Final checkpoint and deployment preparation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at major milestones
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and integration points
- Branding implementation (Task 1) is prioritized as requested by the user
- The logo file already exists at app/static/images/logo.png
- Primary brand color is #0c072d (deep navy)
- Automatic agent detection is already implemented in index.html but needs deployment
- Backend uses Python with Flask, frontend uses JavaScript
- Testing uses pytest for Python backend and Jest for JavaScript frontend
- Property-based testing uses hypothesis (Python) and fast-check (JavaScript)
