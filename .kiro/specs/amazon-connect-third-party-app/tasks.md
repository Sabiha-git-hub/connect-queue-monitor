# Implementation Plan: Amazon Connect Third-Party App Workshop

## Overview

This implementation plan builds a progressive learning workshop application that teaches developers how to build agent-focused web applications that can be embedded as third-party applications inside Amazon Connect's agent workspace. The app uses the Amazon Connect Streams API for automatic agent detection and the Amazon Connect Python SDK for retrieving queue information. It provides agents with a personalized queue view showing call counts for their assigned queues, supporting both embedded mode (within Amazon Connect) and standalone mode (for development and testing). Implementation follows a phased approach matching the workshop's learning path, starting with basic setup, progressing through iframe compatibility, Streams API integration, agent identification with automatic detection, routing profile retrieval, queue metrics, and web interface development.

## Tasks

- [x] 1. Set up project structure and configuration
  - Create directory structure (app/, config/, tests/, docs/, static/css/, static/js/, templates/)
  - Create requirements.txt with dependencies (Flask, Flask-CORS, boto3, python-dotenv, pytest, hypothesis)
  - Create .env.example file with required configuration variables including CONNECT_INSTANCE_URL and ALLOWED_ORIGINS
  - Create .gitignore to exclude .env and Python cache files
  - Implement config/settings.py to load and validate environment variables including iframe security settings
  - _Requirements: 1.1, 1.2, 2.1, 2.4, 3A.7, 10.6_

- [ ]* 1.1 Write property test for instance ID format validation
  - **Property 1: Instance ID Format Validation**
  - **Validates: Requirements 2.2**

- [x] 2. Configure Flask for iframe embedding and security
  - [x] 2.1 Create app/__init__.py with Flask app initialization and security configuration
    - Initialize Flask application
    - Configure secret key from environment
    - Set up session management with SameSite=None for iframe context
    - Implement SecurityConfig class for iframe compatibility
    - Configure Content-Security-Policy headers with frame-ancestors directive
    - Set up CORS configuration for Amazon Connect domains
    - Register after_request handler for security headers
    - _Requirements: 3A.1, 3A.2, 3A.3, 3A.5, 10.2_

  - [ ]* 2.2 Write property test for iframe security headers configuration
    - **Property 10: Iframe Security Headers Configuration**
    - **Validates: Requirements 3A.1, 3A.2**

  - [ ]* 2.3 Write property test for CORS configuration
    - **Property 11: CORS Configuration for Amazon Connect Domains**
    - **Validates: Requirements 3A.3**

  - [ ]* 2.4 Write unit tests for security configuration
    - Test CSP headers are set correctly
    - Test CORS headers for allowed origins
    - Test session cookie configuration
    - _Requirements: 3A.1, 3A.2, 3A.3, 3A.5_

- [x] 3. Implement mode detection frontend logic
  - [x] 3.1 Create app/static/js/mode-detector.js
    - Implement ModeDetector class with detectMode() method
    - Detect if application is running in iframe
    - Identify if parent frame is Amazon Connect
    - Return mode information (embedded vs standalone)
    - Implement initializeApp() to trigger appropriate flow
    - _Requirements: 3A.6_

  - [ ]* 3.2 Write property test for mode detection accuracy
    - **Property 12: Mode Detection Accuracy**
    - **Validates: Requirements 3A.6**

  - [ ]* 3.3 Write unit tests for mode detector
    - Test iframe detection
    - Test Amazon Connect parent detection
    - Test standalone mode detection
    - _Requirements: 3A.6_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
- [x] 5. Implement Amazon Connect Streams API integration
  - [x] 5.1 Create app/static/js/streams.js with StreamsAPIIntegration class
    - Implement constructor with CCP URL and container configuration
    - Implement initialize() method to connect to Streams API with 10-second timeout
    - Subscribe to agent events using connect.agent()
    - Implement extractAgentData() to get username from agent configuration
    - Implement getAgentUsername() method
    - Implement isInitialized() check method
    - Add comprehensive error handling and logging
    - Optional: Implement onAgentStateChange() for future enhancements
    - _Requirements: 3B.1, 3B.2, 3B.3, 3B.4, 3B.5, 3B.6_

  - [ ]* 5.2 Write property test for Streams API agent detection
    - **Property 13: Streams API Agent Detection**
    - **Validates: Requirements 3B.3, 3B.4**

  - [ ]* 5.3 Write property test for automatic detection fallback
    - **Property 14: Automatic Detection Fallback**
    - **Validates: Requirements 3.6, 3B.5**

  - [ ]* 5.4 Write property test for Streams API initialization timeout
    - **Property 15: Streams API Initialization Timeout**
    - **Validates: Requirements 3B.6**

  - [ ]* 5.5 Write unit tests for Streams API integration
    - Test successful initialization
    - Test agent data extraction
    - Test timeout handling
    - Test error scenarios
    - _Requirements: 3B.1, 3B.2, 3B.3, 3B.4, 3B.5, 3B.6_

- [x] 6. Implement Amazon Connect API client wrapper
  - [x] 6.1 Create app/clients/connect_client.py with ConnectClient class
    - Initialize boto3 Connect client with region and instance ID
    - Implement search_users() method to find agents by username
    - Implement describe_user() method to get user details
    - Implement describe_routing_profile() method to get routing profile details
    - Implement list_routing_profile_queues() method to get assigned queues
    - Implement describe_queue() method to get queue names
    - Implement get_current_metric_data() method to retrieve queue metrics
    - Add comprehensive error handling and logging for all API calls
    - _Requirements: 1.3, 1.4, 1.5, 2.2, 2.3, 4.5, 5.5, 9.1, 9.2, 9.3, 9.4_

  - [x] 6.2 Create custom exception classes
  - [x] 6.2 Create custom exception classes
    - Define ConnectAPIException base class
    - Define AgentNotFoundException for invalid usernames
    - Define InvalidInstanceException for invalid instance IDs
    - Define AuthenticationException for credential issues
    - Define RateLimitException for API throttling
    - _Requirements: 1.5, 2.3, 9.1, 9.2, 9.4, 9.5_

  - [ ]* 6.3 Write unit tests for ConnectClient error handling
    - Test authentication errors
    - Test agent not found scenarios
    - Test invalid instance ID handling
    - Test rate limiting behavior
    - _Requirements: 1.5, 2.3, 9.1, 9.2, 9.4, 9.5_

- [x] 7. Implement agent service business logic with dual-mode support
  - [x] 7.1 Create app/services/agent_service.py with Agent dataclass and AgentService class
    - Define Agent dataclass with user_id, username, routing_profile_id, routing_profile_name, assigned_queue_ids, detection_mode
    - Implement get_agent_by_username() to orchestrate agent lookup and routing profile retrieval
    - Support both 'automatic' and 'manual' detection modes
    - Implement validate_agent_exists() for username validation
    - Add error handling and logging
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4_

  - [ ]* 7.2 Write property test for agent routing profile retrieval
    - **Property 2: Agent Routing Profile Retrieval**
    - **Validates: Requirements 4.1**

  - [ ]* 7.3 Write property test for queue list extraction
    - **Property 3: Queue List Extraction from Routing Profile**
    - **Validates: Requirements 4.2, 4.3**

  - [ ]* 7.4 Write property test for agent username validation across modes
    - **Property 16: Agent Username Validation Across Modes**
    - **Validates: Requirements 3.3, 3.4**

  - [ ]* 7.5 Write unit tests for AgentService
    - Test successful agent retrieval
    - Test agent not found error handling
    - Test routing profile retrieval
    - Test both automatic and manual modes
    - _Requirements: 3.2, 3.3, 3.4, 4.1, 4.3, 4.4_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement queue service business logic
  - [x] 9.1 Create app/services/queue_service.py with QueueMetrics dataclass and QueueService class
    - Define QueueMetrics dataclass with queue_id, queue_name, contacts_in_queue, error fields
    - Implement get_queue_metrics() to retrieve and combine queue details and call counts
    - Implement parallel queue detail fetching using ThreadPoolExecutor
    - Implement queue sorting by call count in descending order
    - Handle partial failures gracefully (mark individual queues with errors)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 6.7, 9.6_

  - [ ]* 9.2 Write property test for queue metrics retrieval
    - **Property 4: Queue Metrics Retrieval**
    - **Validates: Requirements 5.1, 5.2**

  - [ ]* 9.3 Write property test for queue sorting
    - **Property 6: Queue Sorting by Call Count**
    - **Validates: Requirements 6.7**

  - [ ]* 9.4 Write unit tests for QueueService
    - Test successful metrics retrieval
    - Test partial failure handling
    - Test queue sorting logic
    - Test empty queue list handling
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.7_

- [x] 10. Implement Flask web application routes with dual-mode support
  - [x] 10.1 Create app/routes.py with route handlers
    - Implement index() route to render login page or detect embedded mode
    - Implement agent_login() route to handle username submission and validation (manual mode)
    - Implement agent_auto_login() route to handle automatic login from Streams API (embedded mode)
    - Implement queue_view() route to display agent's queues with call counts
    - Implement refresh_queues() route to return updated metrics as JSON
    - Implement agent_logout() route to clear session
    - Implement health_check() route for monitoring
    - Add session management (store agent_username and detection_mode)
    - Add error handling and user-friendly error messages
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.1, 6.2, 6.3, 6.5, 6.6, 7.1, 7.2, 7.3, 7.4, 7.5, 9.7_

  - [ ]* 10.2 Write property test for error message display
    - **Property 7: Error Message Display**
    - **Validates: Requirements 6.6, 9.7**

  - [ ]* 10.3 Write property test for error logging
    - **Property 8: Error Logging**
    - **Validates: Requirements 9.8**

  - [ ]* 10.4 Write unit tests for Flask routes
    - Test login flow with valid and invalid usernames
    - Test automatic login from Streams API
    - Test session storage
    - Test queue view requires login
    - Test logout functionality
    - Test both embedded and standalone modes
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Create HTML templates with dual-mode support
  - [x] 12.1 Create app/templates/index.html for agent login and mode detection
    - Include mode detection script
    - Include Streams API script from Amazon Connect CDN
    - Create hidden CCP container for Streams API initialization
    - Create login form with username input field (shown only in standalone mode)
    - Add submit button
    - Add error message display area
    - Include workshop branding and instructions
    - Link to CSS and JavaScript files
    - _Requirements: 3.1, 3.4, 3A.4, 3B.1, 6.6_

  - [x] 12.2 Create app/templates/queue_view.html for queue display
    - Include mode detection and Streams API integration scripts
    - Display agent username at top
    - Display detection mode indicator (automatic vs manual)
    - Create table/list for queues with columns for queue name and call count
    - Add refresh button
    - Add logout button (standalone mode only)
    - Add loading indicator for refresh operations
    - Add error display areas for queue-specific errors
    - Display last updated timestamp
    - Hidden CCP container for embedded mode
    - Link to CSS and JavaScript files
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.3, 9.6, 3A.4, 3B.1_

  - [ ]* 12.3 Write property test for queue display with call counts
    - **Property 5: Queue Display with Call Counts**
    - **Validates: Requirements 5.3, 6.3**

- [x] 13. Implement frontend JavaScript for dynamic refresh and mode coordination
  - [x] 13.1 Create app/static/js/app.js
    - Coordinate with mode detector and Streams API modules
    - Handle automatic login flow (embedded mode)
    - Handle manual login flow (standalone mode)
    - Implement refresh button click handler
    - Make AJAX POST request to /agent/queues/refresh endpoint
    - Update queue display with new metrics without page reload
    - Show loading state during refresh (disable button, show spinner)
    - Re-enable refresh button after completion
    - Handle and display errors from refresh operation
    - Update last refreshed timestamp
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 3.1, 3.6_

  - [ ]* 13.2 Write property test for refresh data retrieval and display update
    - **Property 9: Refresh Data Retrieval and Display Update**
    - **Validates: Requirements 7.2, 7.4**

- [x] 14. Create CSS styling with embedded mode optimizations
  - [x] 14.1 Create app/static/css/styles.css
    - Style login page with centered form
    - Style queue view with clean table/list layout
    - Add visual hierarchy (busiest queues more prominent)
    - Style buttons (refresh, logout, submit)
    - Add loading spinner styles
    - Style error messages (red/warning colors)
    - Style mode indicator badge
    - Ensure responsive layout for desktop browsers
    - Add compact layout optimizations for embedded mode
    - Style hidden CCP container
    - Apply accessibility considerations (contrast ratios, font sizes)
    - _Requirements: 6.4, 6.6, 3A.4_

- [x] 15. Create application entry point and configuration
  - [x] 15.1 Create run.py as application entry point
    - Import Flask app from app/__init__.py
    - Validate configuration on startup
    - Run Flask development server
    - _Requirements: 2.2, 2.3_

  - [x] 15.2 Update config/settings.py with validation
    - Add validate() classmethod to check required configuration
    - Add get_instance_id() with UUID format validation
    - Add get_allowed_origins() to parse ALLOWED_ORIGINS
    - Implement fail-fast configuration validation
    - _Requirements: 2.2, 2.3, 3A.7_

- [ ] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 17. Create workshop documentation with iframe and Streams API phases
  - [ ] 17.1 Create README.md with workshop overview
    - Describe workshop purpose and learning objectives
    - Outline the 8-phase learning path (including iframe setup and Streams API)
    - List prerequisites and required software
    - Provide quick start instructions
    - Include architecture diagram description
    - List future enhancement ideas with difficulty levels
    - _Requirements: 8.1, 11.1, 11.8_

  - [ ] 17.2 Create docs/SETUP.md with detailed setup instructions
    - Document Python installation and version requirements
    - Provide virtualenv setup steps
    - List all dependencies and installation commands
    - Document AWS credential configuration options
    - Explain .env file setup with example values including CONNECT_INSTANCE_URL and ALLOWED_ORIGINS
    - Include IAM permissions requirements
    - Add verification steps to test connectivity
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 8.1, 8.8_

  - [ ] 17.3 Create docs/PHASE_1.md for SDK installation phase
    - Document boto3 installation
    - Explain AWS SDK configuration
    - Provide simple test script to verify connectivity
    - Include troubleshooting for common setup issues
    - _Requirements: 8.2_

  - [ ] 17.4 Create docs/PHASE_2.md for iframe compatibility setup phase
    - Explain iframe security constraints and requirements
    - Document Flask security header configuration (CSP, X-Frame-Options)
    - Explain CORS configuration for Amazon Connect domains
    - Document SameSite cookie policy for iframe context
    - Provide code examples with comments
    - Include testing steps for iframe compatibility
    - _Requirements: 8.3, 3A.7_

  - [ ] 17.5 Create docs/PHASE_3.md for Streams API integration phase
    - Explain Amazon Connect Streams API purpose and capabilities
    - Document Streams API script inclusion
    - Explain CCP initialization and configuration
    - Document agent object and configuration structure
    - Show how to extract agent username
    - Include error handling patterns
    - Provide code examples with SDK-specific comments
    - _Requirements: 8.4, 3B.7_

  - [ ] 17.6 Create docs/PHASE_4.md for mode detection and agent identification phase
    - Explain embedded vs standalone mode detection
    - Document automatic agent detection via Streams API
    - Explain manual username input fallback
    - Show how to coordinate between modes
    - Include code examples for both flows
    - _Requirements: 8.5_

  - [ ] 17.7 Create docs/PHASE_5.md for routing profile retrieval phase
    - Explain DescribeUser and DescribeRoutingProfile APIs
    - Document queue extraction from routing profile
    - Show how to chain multiple API calls
    - Include code examples with SDK-specific comments
    - _Requirements: 8.6_

  - [ ] 17.8 Create docs/PHASE_6.md for queue metrics phase
    - Explain GetCurrentMetricData API usage
    - Document parallel queue detail fetching
    - Show metric parsing and data combination
    - Include performance optimization patterns
    - _Requirements: 8.7_

  - [ ] 17.9 Create docs/PHASE_7.md for web interface phase
    - Document Flask route implementation for both modes
    - Explain template rendering with queue data
    - Show AJAX refresh implementation
    - Include complete user flow examples for embedded and standalone
    - _Requirements: 8.8_

  - [ ] 17.10 Create docs/PHASE_8.md for third-party app configuration phase
    - Document steps to add third-party app in Amazon Connect admin console
    - Explain application URL requirements (HTTPS, accessibility)
    - Document security profile assignment
    - Provide testing steps for embedded application
    - Include troubleshooting for common embedding issues (iframe blocking, CORS errors)
    - Document development vs production configuration differences
    - _Requirements: 8.9, 3C.1, 3C.2, 3C.3, 3C.4, 3C.5, 3C.6, 3C.7_

  - [ ] 17.11 Create docs/TROUBLESHOOTING.md
    - Document common AWS credential issues and solutions
    - Explain Connect instance ID validation errors
    - Provide guidance for API permission errors
    - Include rate limiting troubleshooting
    - Add network connectivity debugging steps
    - Document iframe embedding issues (CSP, CORS, X-Frame-Options)
    - Include Streams API initialization troubleshooting
    - Document automatic detection fallback scenarios
    - _Requirements: 8.10, 3A.7, 3B.7, 3C.7_

- [ ] 18. Add inline code comments for educational value
  - [ ] 18.1 Add detailed comments to connect_client.py
    - Explain each Amazon Connect API call purpose
    - Document API request/response formats
    - Clarify error handling patterns
    - Note SDK-specific behaviors
    - _Requirements: 8.7, 10.4_

  - [ ] 18.2 Add comments to service layer files
    - Explain business logic orchestration
    - Document data transformation steps
    - Clarify error propagation
    - Document dual-mode support
    - _Requirements: 8.7, 10.4_

  - [ ] 18.3 Add comments to routes.py
    - Explain Flask route patterns
    - Document session management
    - Clarify request/response flow
    - Document automatic vs manual login flows
    - _Requirements: 8.7, 10.4_

  - [ ] 18.4 Add comments to JavaScript modules
    - Explain mode detection logic
    - Document Streams API integration patterns
    - Clarify AJAX refresh implementation
    - Document coordination between modules
    - _Requirements: 8.7, 10.4, 3A.7, 3B.7_

- [ ] 19. Create test fixtures and configuration
  - [ ] 19.1 Create tests/conftest.py with shared fixtures
    - Create mock_connect_client fixture
    - Create Flask test client fixture
    - Create mock API response fixtures
    - Create mock Streams API fixtures
    - Set up test configuration
    - _Requirements: 10.1, 10.2_

  - [ ] 19.2 Create tests/__init__.py and test directory structure
    - Set up unit test directory
    - Set up property test directory
    - Set up integration test directory
    - Set up iframe compatibility test directory
    - Set up Streams API integration test directory
    - _Requirements: 10.1, 10.2_

- [ ] 20. Final integration and testing
  - [ ] 20.1 Run complete test suite
    - Execute all unit tests
    - Execute all property-based tests
    - Verify test coverage meets 80% minimum
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 20.2 Test complete user workflows manually in both modes
    - Test standalone mode: agent login with valid username
    - Test standalone mode: agent login with invalid username
    - Test embedded mode: automatic agent detection
    - Test embedded mode: fallback to manual input
    - Test queue view display and sorting in both modes
    - Test manual refresh functionality
    - Test logout functionality (standalone mode)
    - Test error scenarios (invalid config, API failures, Streams API timeout)
    - Test iframe embedding with proper security headers
    - Test CORS functionality from Amazon Connect domains
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 6.1, 6.2, 6.3, 6.7, 7.1, 7.2, 7.4, 9.7, 3A.1, 3A.3, 3A.4, 3B.3, 3B.5_

- [ ] 21. Checkpoint - Final validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- The implementation follows the workshop's progressive learning approach (Phases 1-8)
- Property tests validate the 16 correctness properties defined in the design (9 original + 7 new for iframe/Streams API)
- Checkpoints ensure incremental validation at key milestones
- All code should include educational comments explaining Amazon Connect SDK concepts, Streams API usage, and iframe considerations
- The application is designed for both embedded mode (within Amazon Connect) and standalone mode (local development)
- Mock Amazon Connect API calls and Streams API in tests to avoid requiring live AWS resources during development
- Security headers (CSP, CORS) are critical for iframe embedding functionality
- Streams API provides automatic agent detection in embedded mode with fallback to manual input
