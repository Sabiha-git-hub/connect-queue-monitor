# Design Document: Agent Dashboard Enhancements

## Overview

This design document specifies the technical implementation for enhancing the Amazon Connect Queue Monitor application with automatic agent detection, comprehensive performance metrics, and professional branding. The enhancements transform the application from a simple queue monitor into a full-featured agent dashboard that provides both personal performance metrics and call center overview statistics.

### Goals

- Enable automatic agent detection when embedded in Amazon Connect agent workspace
- Display comprehensive agent performance metrics (contacts handled, transfers, missed calls, handle time, occupancy)
- Show real-time call center overview (agents logged in, available, on contact, in ACW)
- Apply professional branding with organization logo and color scheme
- Maintain existing queue monitoring functionality
- Ensure responsive design for embedded panel display (400-800px width)

### Non-Goals

- Real-time contact streaming or live call monitoring
- Historical trend analysis or reporting beyond current day
- Agent scheduling or workforce management features
- Multi-instance support (single Connect instance only)
- Custom metric definitions or calculations

### Architecture Principles

1. **Dual-Mode Operation**: Support both embedded mode (automatic detection via Streams API) and standalone mode (manual login)
2. **Graceful Degradation**: Fall back to manual login if automatic detection fails
3. **API Efficiency**: Cache metrics, implement retry logic, and batch requests where possible
4. **Responsive Design**: Optimize for panel widths between 400-800 pixels
5. **Security First**: Never expose AWS credentials in client-side code or API responses

## Architecture

### System Components


```
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon Connect Agent Workspace                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  Agent Dashboard (Embedded)                │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Frontend (Browser)                                  │  │  │
│  │  │  - index.html / queue_view.html                     │  │  │
│  │  │  - streams.js (Streams API Integration)             │  │  │
│  │  │  - app.js (Dashboard Logic)                         │  │  │
│  │  │  - mode-detector.js (Embedded/Standalone Detection) │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                          ↕ HTTPS                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Flask Backend (app/routes.py)                      │  │  │
│  │  │  - /agent/auto-login (Streams API auth)             │  │  │
│  │  │  - /agent/login (Manual auth)                       │  │  │
│  │  │  - /agent/metrics (Performance metrics)             │  │  │
│  │  │  - /agent/overview (Call center overview)           │  │  │
│  │  │  - /agent/queues/refresh (Queue metrics)            │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                          ↕                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Service Layer                                       │  │  │
│  │  │  - agent_service.py (Agent operations)              │  │  │
│  │  │  - queue_service.py (Queue operations)              │  │  │
│  │  │  - metrics_service.py (NEW: Metrics operations)     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                          ↕                                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Client Layer                                        │  │  │
│  │  │  - connect_client.py (Amazon Connect API wrapper)   │  │  │
│  │  │    * search_users()                                  │  │  │
│  │  │    * get_metric_data_v2() (NEW)                     │  │  │
│  │  │    * get_current_metric_data()                      │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↕ AWS API
┌─────────────────────────────────────────────────────────────────┐
│                      Amazon Connect Service                      │
│  - GetMetricDataV2 (Historical metrics)                         │
│  - GetCurrentMetricData (Real-time metrics)                     │
│  - SearchUsers (Agent lookup)                                   │
│  - DescribeUser (Agent details)                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Frontend Components

**1. Mode Detector (mode-detector.js)**
- Detects if application is running in embedded mode (within iframe) or standalone mode
- Checks for parent window and Amazon Connect context
- Determines initialization strategy

**2. Streams API Integration (streams.js)**
- Initializes Amazon Connect Streams API when in embedded mode
- Subscribes to agent events and extracts agent username
- Handles connection failures and timeouts (5 second limit)
- Provides fallback to manual login on failure

**3. Dashboard Application (app.js - NEW)**
- Manages dashboard state and UI updates
- Fetches and displays agent performance metrics
- Fetches and displays call center overview metrics
- Implements auto-refresh for metrics (30-60 second intervals)
- Handles loading states and error messages

#### Backend Components

**1. Routes (app/routes.py - ENHANCED)**
- Existing routes: /agent/login, /agent/auto-login, /agent/queues, /agent/queues/refresh
- New routes:
  - GET /agent/metrics - Returns agent performance metrics
  - GET /agent/overview - Returns call center overview metrics
  - GET /health - Health check endpoint

**2. Metrics Service (app/services/metrics_service.py - NEW)**
- Retrieves historical metrics for specific agent (today's data)
- Retrieves real-time metrics for all agents (call center overview)
- Calculates derived metrics (average handle time, occupancy percentage)
- Implements caching (15 second TTL) to reduce API calls
- Handles timezone conversion (UTC to Instance_Timezone)

**3. Connect Client (app/clients/connect_client.py - ENHANCED)**
- Existing methods: search_users, describe_user, get_current_metric_data
- New methods:
  - get_metric_data_v2() - Retrieves historical metrics using GetMetricDataV2 API
  - Implements exponential backoff for throttling (max 3 retries)
  - Adds response caching with 15 second TTL

### Data Flow

#### Automatic Agent Detection Flow (Embedded Mode)


```
1. Page loads → mode-detector.js detects embedded mode
2. streams.js initializes Streams API with CCP URL
3. Streams API connects and fires agent event
4. streams.js extracts agent username from agent configuration
5. Frontend sends POST /agent/auto-login with username
6. Backend validates agent and creates session
7. Frontend redirects to /agent/queues
8. Dashboard loads and displays:
   - Agent performance metrics (via GET /agent/metrics)
   - Call center overview (via GET /agent/overview)
   - Queue metrics (via GET /agent/queues/refresh)
9. Auto-refresh timers start (30s for overview/queues, 60s for agent metrics)
```

#### Manual Login Flow (Standalone Mode)

```
1. Page loads → mode-detector.js detects standalone mode
2. Login form displayed
3. User enters username and submits
4. Frontend sends POST /agent/login with username
5. Backend validates agent and creates session
6. Frontend redirects to /agent/queues
7. Dashboard loads and displays metrics (same as embedded mode)
8. Session expires after 8 hours
```

#### Metrics Retrieval Flow

```
Frontend Request → Flask Route → Metrics Service → Connect Client → AWS API
                                      ↓
                                  Cache Check
                                      ↓
                              Return Cached (if < 15s old)
                                      ↓
                              Make API Call (if cache miss/stale)
                                      ↓
                              Transform & Calculate
                                      ↓
                              Update Cache
                                      ↓
                              Return to Frontend
```

## Components and Interfaces

### Frontend Components

#### 1. Dashboard Application (app.js)

**Purpose**: Main dashboard logic for fetching and displaying metrics

**Key Functions**:

```javascript
class AgentDashboard {
  constructor() {
    this.agentMetrics = null;
    this.overviewMetrics = null;
    this.queueMetrics = null;
    this.refreshTimers = {};
  }

  // Initialize dashboard and start auto-refresh
  async initialize() {}

  // Fetch agent performance metrics
  async fetchAgentMetrics() {}

  // Fetch call center overview metrics
  async fetchOverviewMetrics() {}

  // Fetch queue metrics
  async fetchQueueMetrics() {}

  // Update UI with agent metrics
  updateAgentMetricsDisplay(metrics) {}

  // Update UI with overview metrics
  updateOverviewMetricsDisplay(metrics) {}

  // Update UI with queue metrics
  updateQueueMetricsDisplay(metrics) {}

  // Start auto-refresh timers
  startAutoRefresh() {}

  // Stop auto-refresh timers
  stopAutoRefresh() {}

  // Handle errors and display messages
  handleError(error, context) {}
}
```

**Auto-Refresh Configuration**:
- Agent metrics: 60 seconds
- Overview metrics: 30 seconds
- Queue metrics: 30 seconds

#### 2. Enhanced Streams Integration (streams.js)

**Enhancements**:
- Add timeout handling (5 seconds)
- Add reconnection logic (10 second intervals, 5 minute max)
- Add agent change detection

```javascript
class StreamsAPIIntegration {
  // Existing methods...

  // NEW: Monitor for agent changes
  onAgentChange(callback) {
    connect.agent((agent) => {
      agent.onRefresh(() => {
        const newUsername = this._extractAgentData(agent).username;
        if (newUsername !== this.agentUsername) {
          callback(newUsername);
        }
      });
    });
  }

  // NEW: Attempt reconnection
  async reconnect(maxAttempts = 30, interval = 10000) {
    for (let i = 0; i < maxAttempts; i++) {
      try {
        await this.initialize();
        return true;
      } catch (error) {
        await new Promise(resolve => setTimeout(resolve, interval));
      }
    }
    return false;
  }
}
```

### Backend Components

#### 1. New Routes (app/routes.py)

**GET /agent/metrics**

Purpose: Retrieve agent performance metrics for today

Request:
- Session must contain agent_username
- No query parameters required

Response:
```json
{
  "success": true,
  "agent_username": "john.doe",
  "date": "2024-01-15",
  "timezone": "America/New_York",
  "metrics": {
    "contacts_handled": 45,
    "contacts_transferred": 8,
    "contacts_missed": 2,
    "average_handle_time": {
      "seconds": 245,
      "formatted": "04:05"
    },
    "occupancy": {
      "percentage": 87.5,
      "formatted": "87.5%"
    }
  },
  "last_updated": "2024-01-15T14:30:00-05:00"
}
```

Error Response:
```json
{
  "success": false,
  "error": "Not authenticated",
  "code": "AUTH_REQUIRED"
}
```

**GET /agent/overview**

Purpose: Retrieve call center overview metrics

Request:
- Session must contain agent_username
- No query parameters required

Response:
```json
{
  "success": true,
  "metrics": {
    "agents_logged_in": 25,
    "agents_available": 8,
    "agents_on_contact": 12,
    "agents_in_acw": 5
  },
  "last_updated": "2024-01-15T14:30:00-05:00"
}
```

#### 2. Metrics Service (app/services/metrics_service.py - NEW)

**Purpose**: Business logic for retrieving and calculating metrics

**Class Structure**:

```python
from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional
import pytz

@dataclass
class AgentMetrics:
    """Agent performance metrics for today"""
    agent_username: str
    date: str
    contacts_handled: int
    contacts_transferred: int
    contacts_missed: int
    average_handle_time_seconds: int
    occupancy_percentage: float
    last_updated: datetime

@dataclass
class OverviewMetrics:
    """Call center overview metrics"""
    agents_logged_in: int
    agents_available: int
    agents_on_contact: int
    agents_in_acw: int
    last_updated: datetime

class MetricsService:
    def __init__(self, connect_client, timezone='America/New_York'):
        self.connect_client = connect_client
        self.timezone = pytz.timezone(timezone)
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 15  # seconds

    def get_agent_metrics(self, agent_username: str) -> AgentMetrics:
        """
        Retrieve agent performance metrics for today.
        
        Steps:
        1. Check cache for recent data
        2. Calculate time range (midnight to now in instance timezone)
        3. Call GetMetricDataV2 API with agent filter
        4. Extract and calculate metrics
        5. Cache results
        6. Return AgentMetrics object
        """
        pass

    def get_overview_metrics(self) -> OverviewMetrics:
        """
        Retrieve call center overview metrics.
        
        Steps:
        1. Check cache for recent data
        2. Call GetCurrentMetricData API for all agents
        3. Count agents by state
        4. Cache results
        5. Return OverviewMetrics object
        """
        pass

    def _calculate_average_handle_time(self, contacts: list) -> int:
        """
        Calculate average handle time from contact data.
        
        Formula: (sum of talk_time + hold_time) / count
        Excludes: ACW time
        Returns: Average in seconds
        """
        pass

    def _calculate_occupancy(self, agent_data: dict) -> float:
        """
        Calculate occupancy percentage.
        
        Formula: (time_on_contact + time_on_hold) / total_time * 100
        Returns: Percentage with one decimal place
        """
        pass

    def _get_today_time_range(self) -> tuple:
        """
        Get time range from midnight to now in instance timezone.
        
        Returns: (start_datetime, end_datetime) in UTC
        """
        pass

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid (< 15 seconds old)"""
        pass
```

**Caching Strategy**:
- Cache key format: `{metric_type}:{identifier}:{timestamp_bucket}`
- Example: `agent_metrics:john.doe:1705334400` (15-second buckets)
- TTL: 15 seconds
- Storage: In-memory dictionary (simple implementation)
- Future enhancement: Redis for multi-instance deployments

#### 3. Enhanced Connect Client (app/clients/connect_client.py)

**New Method: get_metric_data_v2()**

```python
def get_metric_data_v2(
    self,
    start_time: datetime,
    end_time: datetime,
    filters: dict,
    metrics: list,
    groupings: list = None
) -> dict:
    """
    Get historical metrics using GetMetricDataV2 API.
    
    Args:
        start_time: Start of time range (UTC)
        end_time: End of time range (UTC)
        filters: Filters for the query (agents, queues, routing profiles)
        metrics: List of metric definitions
        groupings: Optional groupings (AGENT, QUEUE, etc.)
    
    Returns:
        API response with metric data
    
    Implements:
        - Exponential backoff for throttling
        - Error handling for common errors
        - Logging for troubleshooting
    """
    pass
```

**Retry Logic with Exponential Backoff**:

```python
def _make_api_call_with_retry(self, api_method, **kwargs):
    """
    Make API call with exponential backoff retry logic.
    
    Retry on: ThrottlingException
    Max retries: 3
    Backoff: 1s, 2s, 4s
    """
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries + 1):
        try:
            return api_method(**kwargs)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Throttled, retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    raise RateLimitException("Max retries exceeded")
            else:
                raise
```

## Data Models

### Agent Performance Metrics

**Source**: Amazon Connect GetMetricDataV2 API

**Metrics Retrieved**:


| Metric Name | API Metric | Description | Calculation |
|-------------|------------|-------------|-------------|
| Contacts Handled | CONTACTS_HANDLED | Total contacts handled by agent today | Direct from API |
| Contacts Transferred | CONTACTS_TRANSFERRED | Contacts transferred to other agents/queues | Direct from API |
| Contacts Missed | CONTACTS_MISSED | Contacts that rang but weren't answered | Direct from API |
| Average Handle Time | HANDLE_TIME | Average time spent handling contacts | (SUM(talk_time + hold_time)) / count |
| Occupancy | OCCUPANCY | Percentage of time agent was busy | (busy_time / total_time) * 100 |

**Time Range**: Midnight to current time in Instance_Timezone (EST/EDT for us-east-1)

**API Request Example**:

```python
{
    "InstanceId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "StartTime": datetime(2024, 1, 15, 5, 0, 0),  # Midnight EST in UTC
    "EndTime": datetime(2024, 1, 15, 19, 30, 0),  # Current time in UTC
    "Filters": {
        "Agents": ["user-id-123"]
    },
    "Metrics": [
        {"Name": "CONTACTS_HANDLED"},
        {"Name": "CONTACTS_TRANSFERRED"},
        {"Name": "CONTACTS_MISSED"},
        {"Name": "HANDLE_TIME"},
        {"Name": "OCCUPANCY"}
    ],
    "Groupings": ["AGENT"]
}
```

### Call Center Overview Metrics

**Source**: Amazon Connect GetCurrentMetricData API

**Metrics Retrieved**:

| Metric Name | API Metric | Description | Calculation |
|-------------|------------|-------------|-------------|
| Agents Logged In | AGENTS_ONLINE | Total agents currently logged in | Count of agents with AGENTS_ONLINE > 0 |
| Agents Available | AGENTS_AVAILABLE | Agents in Available state | Count of agents with AGENTS_AVAILABLE > 0 |
| Agents On Contact | AGENTS_ON_CONTACT | Agents currently handling contacts | Count of agents with AGENTS_ON_CONTACT > 0 |
| Agents in ACW | AGENTS_AFTER_CONTACT_WORK | Agents in After Contact Work state | Count of agents with AGENTS_AFTER_CONTACT_WORK > 0 |

**API Request Example**:

```python
{
    "InstanceId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "Filters": {
        "Channels": ["VOICE"]
    },
    "CurrentMetrics": [
        {"Name": "AGENTS_ONLINE", "Unit": "COUNT"},
        {"Name": "AGENTS_AVAILABLE", "Unit": "COUNT"},
        {"Name": "AGENTS_ON_CONTACT", "Unit": "COUNT"},
        {"Name": "AGENTS_AFTER_CONTACT_WORK", "Unit": "COUNT"}
    ],
    "Groupings": ["CHANNEL"]
}
```

### Queue Metrics (Existing)

**Source**: Amazon Connect GetCurrentMetricData API

**Metrics Retrieved**:
- CONTACTS_IN_QUEUE: Number of contacts waiting in each queue

**No changes to existing queue metrics implementation**

## UI/UX Design

### Branded Color Scheme

**Primary Brand Color**: #0c072d (Deep navy blue from logo)

**Derived Color Palette**:

```css
:root {
    /* Brand Colors */
    --brand-primary: #0c072d;      /* Deep navy - headers, primary elements */
    --brand-secondary: #1a1450;    /* Lighter navy - hover states */
    --brand-accent: #4a3f8f;       /* Purple accent - highlights */
    
    /* Functional Colors */
    --success-color: #10b981;      /* Green - positive metrics */
    --warning-color: #f59e0b;      /* Amber - medium priority */
    --error-color: #ef4444;        /* Red - high priority/errors */
    --info-color: #3b82f6;         /* Blue - informational */
    
    /* Neutral Colors */
    --bg-primary: #ffffff;
    --bg-secondary: #f9fafb;
    --bg-tertiary: #f3f4f6;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --text-tertiary: #9ca3af;
    --border-color: #e5e7eb;
    
    /* Metric Badge Colors */
    --badge-high: #fef2f2;         /* Light red background */
    --badge-high-text: #991b1b;    /* Dark red text */
    --badge-medium: #fffbeb;       /* Light amber background */
    --badge-medium-text: #92400e;  /* Dark amber text */
    --badge-low: #f0fdf4;          /* Light green background */
    --badge-low-text: #166534;     /* Dark green text */
}
```

**Contrast Ratios** (WCAG AA compliance):
- Brand primary (#0c072d) on white: 14.8:1 ✓
- Text primary (#111827) on white: 16.1:1 ✓
- Text secondary (#6b7280) on white: 4.6:1 ✓
- All badge combinations: > 4.5:1 ✓

### Layout Structure

**Page Layout** (queue_view.html enhanced):

```
┌─────────────────────────────────────────────────────────────┐
│  Header (Fixed)                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  [Logo] Agent Dashboard                              │   │
│  │  Agent: john.doe | Routing Profile: Basic           │   │
│  │  [Logout]                                            │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  Content (Scrollable)                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  My Performance Today                                │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Contacts │ Transfer │  Missed  │ Avg Handle   │  │   │
│  │  │    45    │    8     │    2     │   04:05      │  │   │
│  │  └──────────┴──────────┴──────────┴──────────────┘  │   │
│  │  ┌──────────┐                                        │   │
│  │  │ Occupancy│                                        │   │
│  │  │  87.5%   │                                        │   │
│  │  └──────────┘                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Call Center Overview                                │   │
│  │  ┌──────────┬──────────┬──────────┬──────────────┐  │   │
│  │  │ Logged In│ Available│On Contact│     ACW      │  │   │
│  │  │    25    │    8     │    12    │      5       │  │   │
│  │  └──────────┴──────────┴──────────┴──────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Queue Status                                        │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │ Queue Name          │ Contacts in Queue     │    │   │
│  │  ├─────────────────────────────────────────────┤    │   │
│  │  │ Customer Support    │        15             │    │   │
│  │  │ Technical Support   │         8             │    │   │
│  │  │ Billing             │         3             │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│  Last updated: 2:30 PM EST                                  │
└─────────────────────────────────────────────────────────────┘
```

### Component Styling

**Header**:
```css
.app-header {
    background: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
    color: white;
    padding: 1rem 1.5rem;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header .logo {
    height: 40px;
    width: auto;
    vertical-align: middle;
    margin-right: 1rem;
}

.app-header .agent-info {
    font-size: 0.875rem;
    opacity: 0.9;
}
```

**Metric Cards**:
```css
.metric-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--brand-primary);
    margin: 0.5rem 0;
}

.metric-card .metric-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
```

**Metric Badges** (for queue counts):
```css
.metric-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.875rem;
}

.metric-badge.high {
    background: var(--badge-high);
    color: var(--badge-high-text);
}

.metric-badge.medium {
    background: var(--badge-medium);
    color: var(--badge-medium-text);
}

.metric-badge.low {
    background: var(--badge-low);
    color: var(--badge-low-text);
}
```

**Responsive Breakpoints**:
```css
/* Embedded panel (400-800px) */
@media (max-width: 800px) {
    .metric-grid {
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
    }
    
    .metric-card .metric-value {
        font-size: 1.5rem;
    }
}

/* Minimum width (400px) */
@media (max-width: 400px) {
    .metric-grid {
        grid-template-columns: 1fr;
    }
    
    .app-header {
        padding: 0.75rem 1rem;
    }
}
```

### Loading States

**Skeleton Loaders**:
```html
<div class="metric-card skeleton">
    <div class="skeleton-label"></div>
    <div class="skeleton-value"></div>
</div>
```

```css
.skeleton {
    animation: pulse 1.5s ease-in-out infinite;
}

.skeleton-label {
    height: 12px;
    width: 60%;
    background: var(--bg-tertiary);
    border-radius: 4px;
    margin: 0 auto 0.5rem;
}

.skeleton-value {
    height: 32px;
    width: 80%;
    background: var(--bg-tertiary);
    border-radius: 4px;
    margin: 0 auto;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

### Error States

**Error Message Component**:
```html
<div class="error-banner">
    <svg class="error-icon">...</svg>
    <div class="error-content">
        <strong>Unable to load metrics</strong>
        <p>Connection error. Retrying in 30 seconds...</p>
    </div>
    <button class="error-retry">Retry Now</button>
</div>
```

```css
.error-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 4px solid var(--error-color);
    border-radius: 8px;
    padding: 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}

.error-icon {
    width: 24px;
    height: 24px;
    color: var(--error-color);
    flex-shrink: 0;
}

.error-content {
    flex: 1;
}

.error-retry {
    background: var(--error-color);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
}
```

## Error Handling

### Error Categories

**1. Authentication Errors**

| Error | Cause | User Message | Action |
|-------|-------|--------------|--------|
| AUTH_REQUIRED | No session | "Please log in to continue" | Redirect to login |
| INVALID_CREDENTIALS | Wrong username | "Agent not found. Please check your username." | Show login form |
| PERMISSION_DENIED | Insufficient IAM permissions | "Access denied. Contact your administrator." | Show error, log details |

**2. API Errors**

| Error | Cause | User Message | Action |
|-------|-------|--------------|--------|
| THROTTLING | Rate limit exceeded | "Too many requests. Retrying..." | Exponential backoff |
| NETWORK_ERROR | Connection failed | "Connection error. Retrying in 30s..." | Auto-retry |
| TIMEOUT | Request timeout | "Request timed out. Please try again." | Manual retry button |
| INVALID_INSTANCE | Wrong instance ID | "Configuration error. Contact administrator." | Show error, log details |

**3. Data Errors**

| Error | Cause | User Message | Action |
|-------|-------|--------------|--------|
| NO_DATA | No metrics available | "No data available for today" | Show zero values |
| STALE_DATA | Metrics not updating | "Data may be outdated (last updated: 5 min ago)" | Show staleness indicator |
| PARSE_ERROR | Invalid API response | "Error processing data. Please refresh." | Log error, show retry |

### Error Handling Strategy

**Frontend Error Handling**:

```javascript
class ErrorHandler {
    handleError(error, context) {
        // Log error for debugging
        console.error(`Error in ${context}:`, error);
        
        // Determine error type
        const errorType = this.categorizeError(error);
        
        // Show appropriate user message
        this.showErrorMessage(errorType, context);
        
        // Take appropriate action
        switch (errorType) {
            case 'AUTH_REQUIRED':
                window.location.href = '/';
                break;
            case 'THROTTLING':
                // Handled by backend retry logic
                break;
            case 'NETWORK_ERROR':
                this.scheduleRetry(context, 30000);
                break;
            default:
                this.showRetryButton(context);
        }
    }
    
    categorizeError(error) {
        if (error.status === 401) return 'AUTH_REQUIRED';
        if (error.status === 403) return 'PERMISSION_DENIED';
        if (error.status === 404) return 'INVALID_CREDENTIALS';
        if (error.status === 429) return 'THROTTLING';
        if (error.status === 504) return 'TIMEOUT';
        if (!navigator.onLine) return 'NETWORK_ERROR';
        return 'UNKNOWN';
    }
    
    showErrorMessage(errorType, context) {
        const messages = {
            'AUTH_REQUIRED': 'Please log in to continue',
            'PERMISSION_DENIED': 'Access denied. Contact your administrator.',
            'INVALID_CREDENTIALS': 'Agent not found. Please check your username.',
            'THROTTLING': 'Too many requests. Retrying...',
            'NETWORK_ERROR': 'Connection error. Retrying in 30 seconds...',
            'TIMEOUT': 'Request timed out. Please try again.',
            'UNKNOWN': 'An error occurred. Please try again.'
        };
        
        this.displayBanner(messages[errorType] || messages['UNKNOWN']);
    }
}
```

**Backend Error Handling**:

```python
class MetricsService:
    def get_agent_metrics(self, agent_username: str) -> AgentMetrics:
        try:
            # Attempt to retrieve metrics
            metrics = self._fetch_from_api(agent_username)
            return metrics
        except RateLimitException as e:
            # Throttling handled by retry logic in connect_client
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except ConnectAPIException as e:
            # API error - log and return empty metrics
            logger.error(f"API error retrieving metrics: {e}")
            return self._get_empty_metrics(agent_username)
        except Exception as e:
            # Unexpected error - log and raise
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise

    def _get_empty_metrics(self, agent_username: str) -> AgentMetrics:
        """Return metrics with zero values when data unavailable"""
        return AgentMetrics(
            agent_username=agent_username,
            date=datetime.now(self.timezone).strftime('%Y-%m-%d'),
            contacts_handled=0,
            contacts_transferred=0,
            contacts_missed=0,
            average_handle_time_seconds=0,
            occupancy_percentage=0.0,
            last_updated=datetime.now(pytz.UTC)
        )
```

### Graceful Degradation

**Principle**: Never hide previously loaded data when new data fails to load

**Implementation**:
1. Keep last successful metrics in state
2. On error, display last known values with staleness indicator
3. Continue auto-refresh attempts in background
4. Show error banner above metrics (not instead of metrics)

```javascript
async fetchAgentMetrics() {
    try {
        const response = await fetch('/agent/metrics');
        const data = await response.json();
        
        if (data.success) {
            this.agentMetrics = data.metrics;
            this.lastSuccessfulFetch = Date.now();
            this.updateAgentMetricsDisplay(data.metrics);
            this.hideErrorBanner('agent-metrics');
        }
    } catch (error) {
        // Keep displaying old data
        if (this.agentMetrics) {
            const staleness = Date.now() - this.lastSuccessfulFetch;
            this.showStalenessIndicator('agent-metrics', staleness);
        }
        this.showErrorBanner('agent-metrics', error);
    }
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies and consolidations:

**Redundancy Analysis**:
1. Properties 2.2, 2.3, 2.4 (displaying individual metrics) can be consolidated into a single property about displaying all required agent metrics
2. Properties 3.2, 3.3, 3.4, 3.5 (displaying individual overview counts) can be consolidated into a single property about displaying all required overview metrics
3. Properties 5.2, 5.3, 5.4 (applying brand colors to different elements) can be consolidated into a single property about consistent brand color application
4. Properties 9.2, 9.3 (font sizes and section organization) are covered by the general responsive layout property

**Consolidated Properties**:
- Agent metrics display: One property covering all five metrics (contacts, transfers, missed, handle time, occupancy)
- Overview metrics display: One property covering all four counts (logged in, available, on contact, ACW)
- Brand color application: One property covering all branded elements (header, buttons, badges)
- Responsive layout: One comprehensive property covering layout, fonts, and organization

This reduces the total number of properties while maintaining complete coverage of testable requirements.

### Property 1: Streams API Username Extraction

*For any* successful Streams API connection, the agent username should be extractable from the agent configuration object.

**Validates: Requirements 1.2**

### Property 2: Automatic Login Triggers Metrics Display

*For any* agent username retrieved via Streams API, the dashboard should display agent metrics without requiring manual login form submission.

**Validates: Requirements 1.3**

### Property 3: Agent Change Detection

*For any* agent change event from Streams API, the dashboard should detect the new agent username and update the displayed metrics to reflect the new agent's data.

**Validates: Requirements 1.4**

### Property 4: Historical Metrics Time Range Calculation

*For any* authenticated agent and instance timezone, the system should calculate the historical metrics time range from midnight to current time in that timezone, correctly converted to UTC for API calls.

**Validates: Requirements 2.1**

### Property 5: Agent Metrics Display Completeness

*For any* agent with historical data, the dashboard should display all five required metrics: contacts handled, contacts transferred, contacts missed, average handle time, and occupancy percentage.

**Validates: Requirements 2.2, 2.3, 2.4, 2.5, 2.6**

### Property 6: Metrics Refresh Interval

*For any* active dashboard session, the agent metrics should refresh every 60 seconds and overview/queue metrics should refresh every 30 seconds.

**Validates: Requirements 2.8, 3.6, 4.3**

### Property 7: Handle Time Calculation Excludes ACW

*For any* set of contact records with talk time, hold time, and ACW time, the average handle time calculation should include only talk time and hold time, excluding ACW time.

**Validates: Requirements 2.9**

### Property 8: Occupancy Formatting

*For any* calculated occupancy value, the system should format it as a percentage between 0 and 100 with exactly one decimal place.

**Validates: Requirements 2.10**

### Property 9: Overview Metrics Display Completeness

*For any* real-time agent data, the dashboard should display all four required counts: agents logged in, agents available, agents on contact, and agents in ACW.

**Validates: Requirements 3.2, 3.3, 3.4, 3.5**

### Property 10: Timezone Formatting Consistency

*For any* timestamp displayed in the dashboard, it should be formatted in the configured instance timezone (not UTC).

**Validates: Requirements 3.8**

### Property 11: Queue Metrics Preservation

*For any* agent with assigned queues, the dashboard should continue to display contacts in queue for each monitored queue alongside the new metrics.

**Validates: Requirements 4.2**

### Property 12: Brand Color Consistency

*For any* branded UI element (header, buttons, badges), the applied colors should come from the defined brand color palette derived from the primary brand color #0c072d.

**Validates: Requirements 5.2, 5.3, 5.4**

### Property 13: Contrast Ratio Compliance

*For any* text and background color combination in the dashboard, the contrast ratio should be at least 4.5:1 to meet WCAG AA accessibility standards.

**Validates: Requirements 5.6**

### Property 14: API Retry with Exponential Backoff

*For any* API request that receives a throttling response, the system should retry with exponential backoff (1s, 2s, 4s) for a maximum of 3 attempts.

**Validates: Requirements 6.4**

### Property 15: Metrics Response Caching

*For any* metrics request, if a cached response exists that is less than 15 seconds old, the system should return the cached data without making a new API call.

**Validates: Requirements 6.5**

### Property 16: Session Persistence in Embedded Mode

*For any* agent authenticated in embedded mode, the session should remain valid as long as the Streams API connection is active.

**Validates: Requirements 7.1**

### Property 17: Reconnection Attempt Intervals

*For any* lost Streams API connection, the system should attempt to reconnect every 10 seconds for up to 5 minutes (30 attempts total).

**Validates: Requirements 7.2**

### Property 18: Standalone Session Timeout

*For any* agent authenticated in standalone mode, the session should expire after 8 hours of inactivity.

**Validates: Requirements 7.4**

### Property 19: Error Display Without Data Loss

*For any* metrics fetch error, the system should display the error message without hiding previously loaded metrics.

**Validates: Requirements 8.5**

### Property 20: Metric Value Formatting

*For any* metric value displayed, numbers should include comma separators, percentages should include the % symbol, and times should be formatted as HH:MM:SS or MM:SS.

**Validates: Requirements 9.4**

### Property 21: Credentials Exclusion from Client Code

*For any* API response or client-side JavaScript code, AWS credentials (access key, secret key, session token) should never be included.

**Validates: Requirements 10.7**

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing to ensure comprehensive coverage:

**Unit Tests**: Validate specific examples, edge cases, error conditions, and integration points
- Embedded mode initialization example
- Standalone mode login form display
- Missing logo graceful degradation
- Specific error message display
- API method selection (GetMetricDataV2 vs GetCurrentMetricData)
- Configuration loading from environment variables

**Property-Based Tests**: Verify universal properties across all inputs
- Username extraction from any valid Streams API agent object
- Time range calculation for any timezone and current time
- Handle time calculation for any set of contact durations
- Occupancy formatting for any calculated percentage
- Contrast ratio validation for any color combination
- Retry logic for any throttling response
- Cache behavior for any request timing
- Value formatting for any metric value

### Property-Based Testing Configuration

**Library Selection**: 
- Python backend: `hypothesis` (industry standard for Python)
- JavaScript frontend: `fast-check` (TypeScript-friendly, widely adopted)

**Test Configuration**:
```python
# Python example with hypothesis
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(
    talk_time=st.integers(min_value=0, max_value=3600),
    hold_time=st.integers(min_value=0, max_value=3600),
    acw_time=st.integers(min_value=0, max_value=600)
)
def test_handle_time_excludes_acw(talk_time, hold_time, acw_time):
    """
    Feature: agent-dashboard-enhancements, Property 7:
    For any set of contact records with talk time, hold time, and ACW time,
    the average handle time calculation should include only talk time and
    hold time, excluding ACW time.
    """
    contact = {
        'talk_time': talk_time,
        'hold_time': hold_time,
        'acw_time': acw_time
    }
    
    result = calculate_handle_time([contact])
    expected = talk_time + hold_time
    
    assert result == expected
```

```javascript
// JavaScript example with fast-check
import fc from 'fast-check';

test('Property 8: Occupancy formatting', () => {
    /**
     * Feature: agent-dashboard-enhancements, Property 8:
     * For any calculated occupancy value, the system should format it as
     * a percentage between 0 and 100 with exactly one decimal place.
     */
    fc.assert(
        fc.property(
            fc.float({ min: 0, max: 100 }),
            (occupancy) => {
                const formatted = formatOccupancy(occupancy);
                
                // Should end with %
                expect(formatted).toMatch(/%$/);
                
                // Should have exactly one decimal place
                expect(formatted).toMatch(/^\d+\.\d%$/);
                
                // Value should be between 0 and 100
                const value = parseFloat(formatted);
                expect(value).toBeGreaterThanOrEqual(0);
                expect(value).toBeLessThanOrEqual(100);
            }
        ),
        { numRuns: 100 }
    );
});
```

### Unit Test Coverage

**Backend Unit Tests** (pytest):

1. **Metrics Service Tests**:
   - `test_get_agent_metrics_success()` - Successful metrics retrieval
   - `test_get_agent_metrics_no_data()` - No data available (edge case)
   - `test_get_overview_metrics_success()` - Successful overview retrieval
   - `test_calculate_handle_time_zero_contacts()` - Edge case: no contacts
   - `test_calculate_occupancy_zero_time()` - Edge case: zero total time
   - `test_cache_hit_within_ttl()` - Cache returns data within 15s
   - `test_cache_miss_after_ttl()` - Cache expires after 15s

2. **Connect Client Tests**:
   - `test_get_metric_data_v2_success()` - Successful API call
   - `test_get_metric_data_v2_throttling_retry()` - Retry on throttling
   - `test_get_metric_data_v2_max_retries_exceeded()` - Fail after 3 retries
   - `test_exponential_backoff_timing()` - Verify backoff delays (1s, 2s, 4s)

3. **Routes Tests**:
   - `test_agent_metrics_endpoint_authenticated()` - Successful request
   - `test_agent_metrics_endpoint_unauthenticated()` - 401 response
   - `test_agent_overview_endpoint()` - Overview metrics response
   - `test_error_response_format()` - Error response structure

**Frontend Unit Tests** (Jest):

1. **Dashboard Tests**:
   - `test_initialize_dashboard()` - Dashboard initialization
   - `test_fetch_agent_metrics_success()` - Successful fetch
   - `test_fetch_agent_metrics_error_preserves_data()` - Error handling
   - `test_auto_refresh_intervals()` - Verify refresh timers
   - `test_display_staleness_indicator()` - Stale data indicator

2. **Streams Integration Tests**:
   - `test_streams_initialization_embedded_mode()` - Embedded mode init
   - `test_streams_initialization_timeout()` - 5 second timeout
   - `test_agent_change_detection()` - Agent switch detection
   - `test_reconnection_logic()` - Reconnection attempts

3. **Error Handler Tests**:
   - `test_categorize_auth_error()` - 401 categorization
   - `test_categorize_throttling_error()` - 429 categorization
   - `test_show_error_message()` - Error message display
   - `test_schedule_retry()` - Retry scheduling

### Integration Tests

**End-to-End Scenarios**:

1. **Embedded Mode Flow**:
   - Load page in iframe
   - Streams API initializes
   - Agent username extracted
   - Auto-login succeeds
   - Dashboard displays all metrics
   - Auto-refresh works

2. **Standalone Mode Flow**:
   - Load page in browser
   - Login form displayed
   - User enters username
   - Manual login succeeds
   - Dashboard displays all metrics
   - Session persists for 8 hours

3. **Error Recovery Flow**:
   - Dashboard loaded with metrics
   - API call fails
   - Error message displayed
   - Previous metrics still visible
   - Auto-retry succeeds
   - Error message cleared

### Test Data Strategy

**Mock Data Generation**:
- Use realistic agent usernames (e.g., "john.doe", "jane.smith")
- Generate contact durations in realistic ranges (30s - 30min)
- Create occupancy values between 0-100%
- Use actual timezone names (e.g., "America/New_York")

**API Response Mocking**:
- Mock boto3 client responses for GetMetricDataV2 and GetCurrentMetricData
- Include edge cases: empty results, throttling errors, network errors
- Test with various time ranges and metric combinations

### Performance Testing

**Load Testing Scenarios**:
1. 25 concurrent agents viewing dashboard
2. Metrics refresh every 30-60 seconds
3. Verify cache reduces API calls by ~75%
4. Ensure response times < 2 seconds

**Metrics to Monitor**:
- API call rate (should be reduced by caching)
- Response time (p50, p95, p99)
- Error rate (should be < 1%)
- Cache hit rate (should be > 75%)


## Configuration Management

### Environment Variables

**Required Configuration**:

```bash
# Amazon Connect Configuration
CONNECT_INSTANCE_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
CONNECT_INSTANCE_URL=https://myinstance.my.connect.aws
AWS_REGION=us-east-1
INSTANCE_TIMEZONE=America/New_York

# AWS Credentials (for backend API calls)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
# AWS_SESSION_TOKEN=... (optional, for temporary credentials)

# Flask Configuration
SECRET_KEY=your-secret-key-here
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# Application Configuration
DEBUG=False
LOG_LEVEL=INFO
```

**Configuration Validation**:

```python
# config/settings.py
class Config:
    # Required settings
    REQUIRED_SETTINGS = [
        'CONNECT_INSTANCE_ID',
        'CONNECT_INSTANCE_URL',
        'AWS_REGION',
        'INSTANCE_TIMEZONE',
        'SECRET_KEY'
    ]
    
    @classmethod
    def validate(cls):
        """Validate required configuration at startup"""
        missing = []
        for setting in cls.REQUIRED_SETTINGS:
            if not getattr(cls, setting, None):
                missing.append(setting)
        
        if missing:
            error_msg = f"Missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate timezone
        try:
            pytz.timezone(cls.INSTANCE_TIMEZONE)
        except pytz.exceptions.UnknownTimeZoneError:
            error_msg = f"Invalid timezone: {cls.INSTANCE_TIMEZONE}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("✓ Configuration validated successfully")
```

**Startup Validation**:

```python
# run.py
from config.settings import Config

if __name__ == '__main__':
    try:
        # Validate configuration before starting
        Config.validate()
        
        # Start Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=Config.DEBUG
        )
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your environment variables and try again.")
        sys.exit(1)
```

### Security Considerations

**1. Credential Protection**:
- AWS credentials stored in environment variables (never in code)
- Credentials never exposed in API responses
- Credentials never sent to client-side JavaScript
- Use IAM roles when deployed to AWS (preferred over access keys)

**2. Session Security**:
- Secure session cookies (HTTPS only)
- SameSite=None for embedded mode (required for iframe)
- HttpOnly flag to prevent JavaScript access
- 8-hour timeout for standalone mode
- Session tied to Streams API connection in embedded mode

**3. API Security**:
- All API endpoints require authentication (session check)
- CORS configured for Amazon Connect domain only
- Rate limiting on login endpoints (prevent brute force)
- Input validation on all user inputs

**4. Logging Security**:
- Never log AWS credentials
- Never log full session tokens
- Sanitize user inputs in logs
- Log security events (failed logins, permission errors)

## Deployment Considerations

### Infrastructure Requirements

**Minimum Requirements**:
- Python 3.8+
- 512 MB RAM
- 1 vCPU
- HTTPS endpoint (required for Streams API)

**Recommended for Production**:
- Python 3.11+
- 1 GB RAM
- 2 vCPU
- Auto-scaling (2-10 instances)
- Load balancer with sticky sessions
- Redis for distributed caching (optional)

### Deployment Options

**Option 1: AWS App Runner** (Recommended for simplicity)
```yaml
# apprunner.yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  command: gunicorn -w 4 -b 0.0.0.0:8080 run:app
  network:
    port: 8080
  env:
    - name: CONNECT_INSTANCE_ID
      value: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    - name: AWS_REGION
      value: "us-east-1"
```

**Option 2: AWS Elastic Beanstalk**
```yaml
# .ebextensions/01_environment.config
option_settings:
  aws:elasticbeanstalk:application:environment:
    CONNECT_INSTANCE_ID: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    AWS_REGION: "us-east-1"
    INSTANCE_TIMEZONE: "America/New_York"
```

**Option 3: Docker Container**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "run:app"]
```

### IAM Permissions Required

**Minimum IAM Policy**:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "connect:SearchUsers",
                "connect:DescribeUser",
                "connect:DescribeRoutingProfile",
                "connect:ListRoutingProfileQueues",
                "connect:DescribeQueue",
                "connect:GetCurrentMetricData",
                "connect:GetMetricDataV2"
            ],
            "Resource": [
                "arn:aws:connect:us-east-1:123456789012:instance/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "arn:aws:connect:us-east-1:123456789012:instance/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/*"
            ]
        }
    ]
}
```

### Monitoring and Observability

**Key Metrics to Monitor**:
1. API call rate (calls per minute)
2. API error rate (percentage)
3. Response time (p50, p95, p99)
4. Cache hit rate (percentage)
5. Active sessions (count)
6. Failed login attempts (count)

**Logging Strategy**:
```python
# Structured logging with context
logger.info("Agent metrics retrieved", extra={
    "agent_username": username,
    "metrics_count": len(metrics),
    "cache_hit": cache_hit,
    "response_time_ms": response_time
})
```

**Health Check Endpoint**:
```python
@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Check database connection (if applicable)
        # Check AWS API connectivity
        connect_client = ConnectClient()
        # Simple API call to verify connectivity
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now(pytz.UTC).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503
```

## Migration and Rollout Strategy

### Phase 1: Backend Implementation (Week 1)

**Tasks**:
1. Create metrics_service.py with caching
2. Add get_metric_data_v2() to connect_client.py
3. Implement retry logic with exponential backoff
4. Add new routes: /agent/metrics, /agent/overview
5. Write unit tests for new components
6. Test with mock data

**Success Criteria**:
- All unit tests passing
- API endpoints return correct data structure
- Caching reduces API calls by 75%
- Retry logic handles throttling correctly

### Phase 2: Frontend Implementation (Week 2)

**Tasks**:
1. Create app.js with dashboard logic
2. Enhance streams.js with reconnection logic
3. Update queue_view.html with new metric sections
4. Apply branded color scheme
5. Implement loading and error states
6. Add auto-refresh timers
7. Write frontend unit tests

**Success Criteria**:
- Dashboard displays all three metric sections
- Auto-refresh works correctly (30s/60s intervals)
- Error handling preserves previous data
- Responsive layout works at 400-800px width
- All frontend tests passing

### Phase 3: Integration Testing (Week 3)

**Tasks**:
1. Test embedded mode with real Amazon Connect instance
2. Test standalone mode with manual login
3. Test agent switching in embedded mode
4. Test error scenarios (API failures, network issues)
5. Test with multiple concurrent users
6. Verify caching behavior under load

**Success Criteria**:
- End-to-end flows work in both modes
- Error recovery works correctly
- Performance meets requirements (< 2s response time)
- No credential exposure in client code

### Phase 4: Deployment and Monitoring (Week 4)

**Tasks**:
1. Deploy to staging environment
2. Configure monitoring and alerts
3. Test with real agents in staging
4. Deploy to production
5. Monitor metrics for first 48 hours
6. Gather user feedback

**Success Criteria**:
- Zero downtime deployment
- No increase in error rate
- Positive user feedback
- All monitoring metrics within acceptable ranges

### Rollback Plan

**Rollback Triggers**:
- Error rate > 5%
- Response time > 5 seconds (p95)
- Critical bug affecting agent workflow
- Security vulnerability discovered

**Rollback Procedure**:
1. Revert to previous application version
2. Verify existing queue monitoring still works
3. Notify users of temporary feature removal
4. Investigate and fix issues
5. Redeploy when ready

## Future Enhancements

### Phase 2 Features (Post-Launch)

**1. Historical Trend Charts**:
- Line charts showing metrics over time (last 7 days)
- Comparison to previous day/week
- Trend indicators (up/down arrows)

**2. Agent Leaderboard**:
- Top performers by contacts handled
- Best average handle time
- Highest occupancy
- Gamification elements

**3. Real-Time Notifications**:
- Alert when queue exceeds threshold
- Notification when agent becomes available
- WebSocket for live updates (replace polling)

**4. Customizable Dashboard**:
- Drag-and-drop metric cards
- Show/hide specific metrics
- Save layout preferences per agent

**5. Export and Reporting**:
- Export metrics to CSV
- Email daily summary
- Generate PDF reports

### Technical Improvements

**1. Distributed Caching**:
- Replace in-memory cache with Redis
- Support multi-instance deployments
- Reduce API calls across all instances

**2. WebSocket Integration**:
- Replace polling with WebSocket for real-time updates
- Reduce server load
- Improve responsiveness

**3. Offline Support**:
- Service worker for offline functionality
- Cache last known metrics
- Queue actions when offline

**4. Advanced Analytics**:
- Machine learning for workload prediction
- Anomaly detection for unusual patterns
- Recommendations for schedule optimization

## Appendix

### API Reference

**GetMetricDataV2 Request Example**:

```python
response = client.get_metric_data_v2(
    InstanceId='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    StartTime=datetime(2024, 1, 15, 5, 0, 0),  # Midnight EST in UTC
    EndTime=datetime(2024, 1, 15, 19, 30, 0),   # Current time in UTC
    Filters=[
        {
            'FilterKey': 'AGENT',
            'FilterValues': ['user-id-123']
        }
    ],
    Metrics=[
        {
            'Name': 'CONTACTS_HANDLED',
            'Threshold': []
        },
        {
            'Name': 'CONTACTS_TRANSFERRED',
            'Threshold': []
        },
        {
            'Name': 'CONTACTS_MISSED',
            'Threshold': []
        },
        {
            'Name': 'AVG_HANDLE_TIME',
            'Threshold': []
        },
        {
            'Name': 'OCCUPANCY',
            'Threshold': []
        }
    ],
    Groupings=['AGENT']
)
```

**GetCurrentMetricData Request Example**:

```python
response = client.get_current_metric_data(
    InstanceId='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
    Filters={
        'Channels': ['VOICE']
    },
    CurrentMetrics=[
        {'Name': 'AGENTS_ONLINE', 'Unit': 'COUNT'},
        {'Name': 'AGENTS_AVAILABLE', 'Unit': 'COUNT'},
        {'Name': 'AGENTS_ON_CONTACT', 'Unit': 'COUNT'},
        {'Name': 'AGENTS_AFTER_CONTACT_WORK', 'Unit': 'COUNT'}
    ],
    Groupings=['CHANNEL']
)
```

### Glossary

- **ACW (After Contact Work)**: Time agents spend completing tasks after a contact ends
- **Handle Time**: Total time spent on a contact (talk time + hold time, excluding ACW)
- **Occupancy**: Percentage of time an agent is busy (on contact or in ACW)
- **Streams API**: Amazon Connect's JavaScript library for embedded applications
- **CCP (Contact Control Panel)**: Amazon Connect's agent interface
- **Instance Timezone**: The timezone configured for the Amazon Connect instance
- **Embedded Mode**: Application running within Amazon Connect agent workspace
- **Standalone Mode**: Application running in a separate browser tab
- **Property-Based Testing**: Testing approach that validates properties across many generated inputs
- **Exponential Backoff**: Retry strategy with increasing delays (1s, 2s, 4s, etc.)

### References

- [Amazon Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [Amazon Connect Streams API](https://github.com/amazon-connect/amazon-connect-streams)
- [GetMetricDataV2 Documentation](https://docs.aws.amazon.com/connect/latest/APIReference/API_GetMetricDataV2.html)
- [GetCurrentMetricData Documentation](https://docs.aws.amazon.com/connect/latest/APIReference/API_GetCurrentMetricData.html)
- [WCAG 2.1 Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Hypothesis Property-Based Testing](https://hypothesis.readthedocs.io/)
- [fast-check JavaScript Testing](https://fast-check.dev/)

