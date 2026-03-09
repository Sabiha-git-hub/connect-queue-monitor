# API Reference

Complete reference for all API endpoints in the Connect Queue Monitor application.

## Table of Contents
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [GET /](#get-)
  - [POST /login](#post-login)
  - [POST /logout](#post-logout)
  - [GET /queue-view](#get-queue-view)
  - [GET /refresh](#get-refresh)
- [Response Formats](#response-formats)
- [Error Handling](#error-handling)

## Authentication

The application uses session-based authentication with secure HTTP-only cookies.

### Session Cookie
- **Name**: `session`
- **Attributes**: 
  - `HttpOnly`: Prevents JavaScript access (security)
  - `Secure`: Only sent over HTTPS
  - `SameSite=None`: Allows cross-domain requests (required for Amazon Connect embedding)
  - `Partitioned`: Improves privacy in third-party contexts
- **Expiration**: 24 hours from login
- **Storage**: Server-side (Flask session)

### Session Data
When a user logs in, the following data is stored in the session:
```python
{
    'agent_id': 'string',      # AWS Connect agent ID
    'agent_name': 'string'     # Agent username
}
```

## Endpoints

### GET /

**Description**: Landing page with login form

**Authentication**: Not required

**Request**:
```http
GET / HTTP/1.1
Host: dzh4oz4t3wz32.cloudfront.net
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
  <!-- Login page HTML -->
</html>
```

**Template Variables**:
- `mode`: Detection mode ('embedded' or 'standalone')
- `connect_instance_url`: Amazon Connect instance URL (for Streams API)

---

### POST /login

**Description**: Authenticate user and create session

**Authentication**: Not required

**Request**:
```http
POST /login HTTP/1.1
Host: dzh4oz4t3wz32.cloudfront.net
Content-Type: application/x-www-form-urlencoded

username=Sabiha
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Amazon Connect agent username |

**Success Response**:
```http
HTTP/1.1 302 Found
Location: /queue-view
Set-Cookie: session=<encrypted-session-data>; HttpOnly; Secure; SameSite=None; Partitioned; Path=/
```

**Error Response** (Invalid Username):
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
  <!-- Login page with error message -->
</html>
```

**Error Message**: "Invalid username. Please try again."

**Backend Process**:
1. Receives username from form
2. Calls `AgentService.get_agent_by_username(username)`
3. If agent found:
   - Stores `agent_id` and `agent_name` in session
   - Redirects to `/queue-view`
4. If agent not found:
   - Re-renders login page with error message

---

### POST /logout

**Description**: Destroy session and redirect to login

**Authentication**: Required (session cookie)

**Request**:
```http
POST /logout HTTP/1.1
Host: dzh4oz4t3wz32.cloudfront.net
Cookie: session=<encrypted-session-data>
```

**Response**:
```http
HTTP/1.1 302 Found
Location: /
Set-Cookie: session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/
```

**Backend Process**:
1. Clears session data using `session.clear()`
2. Redirects to login page (`/`)

---

### GET /queue-view

**Description**: Display agent's assigned queues with metrics and performance summary

**Authentication**: Required (session cookie)

**Request**:
```http
GET /queue-view HTTP/1.1
Host: dzh4oz4t3wz32.cloudfront.net
Cookie: session=<encrypted-session-data>
```

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
  <!-- Queue view page with metrics -->
</html>
```

**Template Variables**:
```python
{
    'agent_name': 'Sabiha',                    # Agent username
    'queues': [                                 # List of queue data
        {
            'name': 'BasicQueue',               # Queue name
            'contacts_in_queue': 5,             # Real-time: contacts waiting
            'calls_handled': 42,                # Historical: calls handled today
            'calls_transferred': 8,             # Historical: calls transferred today
            'available_agents': 3,              # Real-time: agents available
            'non_productive_agents': 2,         # Real-time: agents in custom status
            'status': 'Active'                  # Queue status
        }
    ],
    'performance_summary': {                    # Agent performance metrics
        'calls_handled': 42,                    # Total calls handled today
        'avg_handle_time': '00:05:23',         # Average handle time (HH:MM:SS)
        'calls_transferred': 8                  # Total calls transferred today
    },
    'mode': 'embedded',                         # Detection mode
    'connect_instance_url': 'https://...'      # Connect instance URL
}
```

**Error Response** (Not Authenticated):
```http
HTTP/1.1 302 Found
Location: /
```

**Backend Process**:
1. Checks if user is authenticated (session contains `agent_id`)
2. If not authenticated: Redirects to login page
3. If authenticated:
   - Calls `QueueService.get_queues_for_agent(agent_id)` to fetch queue data
   - Calls `QueueService.get_agent_performance_summary(agent_id)` to fetch performance metrics
   - Renders `queue_view.html` template with data

---

### GET /refresh

**Description**: Refresh queue metrics and performance summary (AJAX endpoint)

**Authentication**: Required (session cookie)

**Request**:
```http
GET /refresh HTTP/1.1
Host: dzh4oz4t3wz32.cloudfront.net
Cookie: session=<encrypted-session-data>
X-Requested-With: XMLHttpRequest
```

**Success Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "queues": [
        {
            "name": "BasicQueue",
            "contacts_in_queue": 5,
            "calls_handled": 42,
            "calls_transferred": 8,
            "available_agents": 3,
            "non_productive_agents": 2,
            "status": "Active"
        }
    ],
    "performance_summary": {
        "calls_handled": 42,
        "avg_handle_time": "00:05:23",
        "calls_transferred": 8
    }
}
```

**Error Response** (Not Authenticated):
```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
    "error": "Not authenticated"
}
```

**Backend Process**:
1. Checks if user is authenticated (session contains `agent_id`)
2. If not authenticated: Returns 401 error
3. If authenticated:
   - Calls `QueueService.get_queues_for_agent(agent_id)` to fetch fresh queue data
   - Calls `QueueService.get_agent_performance_summary(agent_id)` to fetch fresh performance metrics
   - Returns JSON response with updated data

**Frontend Usage**:
```javascript
// Automatic refresh every 15 seconds
setInterval(async () => {
    const response = await fetch('/refresh');
    const data = await response.json();
    
    // Update queue table
    updateQueueTable(data.queues);
    
    // Update performance summary
    updatePerformanceSummary(data.performance_summary);
}, 15000);
```

---

## Response Formats

### Queue Data Format

Each queue object contains:

```python
{
    'name': str,                    # Queue name (e.g., "BasicQueue")
    'contacts_in_queue': int,       # Number of contacts waiting (real-time)
    'calls_handled': int,           # Calls handled today (historical)
    'calls_transferred': int,       # Calls transferred today (historical)
    'available_agents': int,        # Agents available now (real-time)
    'non_productive_agents': int,   # Agents in custom status (real-time)
    'status': str                   # Queue status ("Active" or "Inactive")
}
```

**Metric Types**:
- **Real-time metrics**: Update immediately on refresh (contacts in queue, available agents, non-productive agents)
- **Historical metrics**: Update with delay (calls handled, calls transferred) - AWS Connect processes these metrics in batches

### Performance Summary Format

```python
{
    'calls_handled': int,           # Total calls handled today
    'avg_handle_time': str,         # Average handle time in HH:MM:SS format
    'calls_transferred': int        # Total calls transferred today
}
```

**Time Period**: All metrics are calculated from midnight to current time in the Connect instance timezone (America/New_York).

**Average Handle Time Calculation**:
```
avg_handle_time = total_handle_time / calls_handled
```
Where `total_handle_time` includes:
- Talk time (agent speaking with customer)
- Hold time (customer on hold)
- After call work time (agent completing post-call tasks)

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | Success | Request completed successfully |
| 302 | Redirect | Authentication required or logout |
| 401 | Unauthorized | Session expired or invalid |
| 500 | Server Error | AWS API error or internal error |

### Error Response Format

All error responses include a user-friendly message:

**HTML Error** (for page requests):
```html
<!DOCTYPE html>
<html>
<body>
    <div class="error-message">
        Invalid username. Please try again.
    </div>
</body>
</html>
```

**JSON Error** (for AJAX requests):
```json
{
    "error": "Not authenticated"
}
```

### Common Errors

#### 1. Invalid Username
**Cause**: Username not found in Amazon Connect
**Response**: Login page with error message
**Solution**: Check username spelling, ensure agent exists in Connect

#### 2. Session Expired
**Cause**: Session cookie expired (24 hours) or cleared
**Response**: Redirect to login page
**Solution**: Log in again

#### 3. AWS API Error
**Cause**: AWS Connect API rate limit, permissions issue, or service error
**Response**: 500 error with generic message
**Solution**: Check CloudWatch logs, verify IAM permissions

#### 4. No Queues Found
**Cause**: Agent not assigned to any queues in Amazon Connect
**Response**: Empty queue table with message "No queues assigned"
**Solution**: Assign agent to queues in Amazon Connect admin panel

---

## AWS Connect API Calls

The application makes the following AWS Connect API calls:

### 1. SearchUsers (Login)
**Purpose**: Find agent by username
**API**: `connect_client.search_users()`
**Filters**: `Username` equals provided username
**Returns**: Agent ID, Username, RoutingProfileId

### 2. DescribeRoutingProfile (Queue View)
**Purpose**: Get agent's assigned queues
**API**: `connect_client.describe_routing_profile()`
**Input**: RoutingProfileId from agent
**Returns**: List of QueueReferences (queue IDs and names)

### 3. GetCurrentMetricData (Queue View - Real-time)
**Purpose**: Get real-time queue metrics
**API**: `connect_client.get_current_metric_data()`
**Metrics**: 
- `CONTACTS_IN_QUEUE`: Number of contacts waiting
- `AGENTS_AVAILABLE`: Agents ready to take calls
- `AGENTS_NON_PRODUCTIVE`: Agents in custom status
**Returns**: Current values for each metric per queue

### 4. GetMetricDataV2 (Queue View - Historical)
**Purpose**: Get historical agent metrics
**API**: `connect_client.get_metric_data_v2()`
**Metrics**:
- `CONTACTS_HANDLED`: Calls handled today
- `CONTACTS_TRANSFERRED_OUT`: Calls transferred today
- `SUM_HANDLE_TIME`: Total handle time today
**Time Range**: Midnight to now (America/New_York timezone)
**Returns**: Aggregated values for each metric

### 5. GetMetricDataV2 (Performance Summary)
**Purpose**: Get agent-specific performance metrics
**API**: `connect_client.get_metric_data_v2()`
**Filters**: Specific agent ID
**Metrics**: Same as #4 above
**Returns**: Agent's personal performance data

---

## Rate Limits

AWS Connect API has rate limits:

| API Call | Rate Limit | Burst |
|----------|------------|-------|
| SearchUsers | 2 req/sec | 10 |
| DescribeRoutingProfile | 2 req/sec | 10 |
| GetCurrentMetricData | 5 req/sec | 10 |
| GetMetricDataV2 | 5 req/sec | 10 |

**Application Behavior**:
- Login: 2 API calls (SearchUsers + DescribeRoutingProfile)
- Queue View Load: 3 API calls (DescribeRoutingProfile + GetCurrentMetricData + GetMetricDataV2)
- Refresh: 3 API calls (same as Queue View Load)

**With 15-second refresh**:
- API calls per agent: 4 per minute (240 per hour)
- Cost per agent: $0.38/month (see COST_ANALYSIS.md)

---

## Security Considerations

### 1. Session Security
- Sessions stored server-side (not in client cookies)
- Session cookies are HttpOnly (prevents XSS attacks)
- Session cookies are Secure (HTTPS only)
- Session cookies use SameSite=None (required for embedding)

### 2. CORS Configuration
- Allowed origins: Amazon Connect domains only
- Credentials: Allowed (required for session cookies)
- Methods: GET, POST only

### 3. CSP Headers
- Allows embedding in Amazon Connect iframes
- Blocks embedding in other domains
- Allows Streams API scripts from Amazon Connect

### 4. Authentication
- No passwords stored (uses Amazon Connect usernames)
- Session expires after 24 hours
- Logout clears session immediately

---

## Testing Endpoints

### Using cURL

**Login**:
```bash
curl -X POST https://dzh4oz4t3wz32.cloudfront.net/login \
  -d "username=Sabiha" \
  -c cookies.txt \
  -L
```

**Queue View**:
```bash
curl https://dzh4oz4t3wz32.cloudfront.net/queue-view \
  -b cookies.txt
```

**Refresh**:
```bash
curl https://dzh4oz4t3wz32.cloudfront.net/refresh \
  -b cookies.txt \
  -H "X-Requested-With: XMLHttpRequest"
```

**Logout**:
```bash
curl -X POST https://dzh4oz4t3wz32.cloudfront.net/logout \
  -b cookies.txt \
  -L
```

### Using Browser DevTools

1. Open browser DevTools (F12)
2. Go to Network tab
3. Perform actions in the app
4. Inspect request/response details

---

## Additional Resources

- [Flask Session Documentation](https://flask.palletsprojects.com/en/2.3.x/api/#sessions)
- [AWS Connect API Reference](https://docs.aws.amazon.com/connect/latest/APIReference/)
- [HTTP Cookies (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)
- [CORS (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
