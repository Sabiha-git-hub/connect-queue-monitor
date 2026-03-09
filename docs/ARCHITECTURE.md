# Architecture Overview

## 🏗️ System Architecture

This document explains how the Amazon Connect Queue Monitor application works, designed for beginners to understand the system.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Amazon Connect                            │
│  (Contact Center - where agents handle calls)                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Streams API (detects agent login)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                      CloudFront (HTTPS)                          │
│  https://dzh4oz4t3wz32.cloudfront.net                          │
│  (CDN - makes app fast and secure)                              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ HTTPS requests
                 │
┌────────────────▼────────────────────────────────────────────────┐
│              Elastic Beanstalk (Web Server)                      │
│  - Runs Flask application 24/7                                  │
│  - Handles sessions (keeps agents logged in)                    │
│  - Serves HTML pages and API endpoints                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ AWS SDK calls
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                   Amazon Connect APIs                            │
│  - ListUsers (find agents)                                      │
│  - DescribeUser (get agent details)                             │
│  - ListQueues (get queue list)                                  │
│  - GetCurrentMetricData (real-time metrics)                     │
│  - GetMetricDataV2 (historical metrics)                         │
└─────────────────────────────────────────────────────────────────┘
```

## Application Components

### 1. Frontend (What Users See)

**Location**: `app/templates/` and `app/static/`

#### Login Page (`index.html`)
- **Purpose**: Agent login or automatic detection
- **How it works**:
  1. Detects if running inside Amazon Connect (embedded mode)
  2. If embedded: Uses Streams API to auto-detect agent
  3. If standalone: Shows login form for manual entry
- **Key files**:
  - `templates/index.html` - HTML structure
  - `static/js/mode-detector.js` - Detects embedded vs standalone
  - `static/js/streams.js` - Amazon Connect Streams API integration

#### Dashboard Page (`queue_view.html`)
- **Purpose**: Shows agent's queues and performance metrics
- **What it displays**:
  1. **Performance Summary** (top section)
     - Calls Handled today
     - Average Handle Time
     - Calls Transferred
  2. **Queue Table** (bottom section)
     - Queue names
     - Contacts waiting
     - Agent-specific metrics per queue
     - Real-time agent availability
- **Auto-refresh**: Updates every 15 seconds automatically
- **Key files**:
  - `templates/queue_view.html` - HTML structure and JavaScript
  - `static/css/styles.css` - Styling and branding

### 2. Backend (Server Logic)

**Location**: `app/`

#### Flask Application (`app/__init__.py`)
- **Purpose**: Web server that handles HTTP requests
- **What it does**:
  - Initializes Flask app
  - Configures sessions (keeps agents logged in)
  - Sets up security headers (allows iframe embedding)
  - Configures CORS (allows cross-origin requests)
- **Key concepts**:
  - **Session**: Stores agent info so they stay logged in
  - **Cookie**: Small file stored in browser to maintain session
  - **CORS**: Allows Amazon Connect to embed the app

#### Routes (`app/routes.py`)
- **Purpose**: Defines URL endpoints (like pages on a website)
- **Endpoints**:
  1. `GET /` - Home page (login or redirect to dashboard)
  2. `POST /agent/login` - Manual login
  3. `POST /agent/auto-login` - Automatic login via Streams API
  4. `GET /agent/queues` - Dashboard page
  5. `POST /agent/queues/refresh` - Refresh metrics (AJAX)
  6. `GET|POST /agent/logout` - Logout
- **How it works**:
  - User visits URL → Flask calls appropriate function → Returns HTML or JSON

#### AWS Clients (`app/clients/`)
- **Purpose**: Communicate with AWS APIs
- **File**: `connect_client.py`
- **What it does**:
  - Wraps AWS SDK calls in easy-to-use functions
  - Handles authentication (uses AWS credentials)
  - Implements retry logic (if API call fails, try again)
  - Logs all API calls for debugging
- **Key methods**:
  - `list_users()` - Get all agents
  - `describe_user()` - Get agent details
  - `list_queues()` - Get all queues
  - `get_current_metric_data()` - Real-time metrics
  - `get_metric_data_v2()` - Historical metrics

#### Services (`app/services/`)
- **Purpose**: Business logic (combines data from multiple sources)

**Agent Service** (`agent_service.py`):
- Finds agents by username
- Gets agent's routing profile
- Gets agent's assigned queues
- Handles "agent not found" errors

**Queue Service** (`queue_service.py`):
- Gets queue details (names)
- Gets current metrics (calls waiting, agents available)
- Gets historical metrics (calls handled, transferred)
- Combines all data into easy-to-use format
- Sorts queues by busiest first

### 3. Configuration (`config/`)

**Settings** (`config/settings.py`):
- Loads environment variables (AWS credentials, Connect instance)
- Configures Flask app (secret key, session settings)
- Sets up logging
- Validates required configuration

**Environment Variables** (`.env`):
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `AWS_SESSION_TOKEN` - AWS session token (if using temporary credentials)
- `CONNECT_INSTANCE_ID` - Amazon Connect instance ID
- `CONNECT_INSTANCE_URL` - Amazon Connect instance URL
- `FLASK_SECRET_KEY` - Secret key for sessions

### 4. Deployment Configuration

**Elastic Beanstalk** (`.ebextensions/` and `.platform/`):
- `python.config` - Python environment setup
- `custom.conf` - Nginx web server configuration
- `Procfile` - Tells Elastic Beanstalk how to run the app

## Data Flow

### Login Flow (Manual)

```
1. User visits https://dzh4oz4t3wz32.cloudfront.net
   ↓
2. CloudFront forwards to Elastic Beanstalk
   ↓
3. Flask serves index.html (login page)
   ↓
4. User enters username and clicks "Login"
   ↓
5. JavaScript sends POST to /agent/login
   ↓
6. Flask calls AgentService.get_agent_by_username()
   ↓
7. AgentService calls ConnectClient.list_users()
   ↓
8. AWS returns agent data
   ↓
9. Flask stores agent info in session
   ↓
10. JavaScript redirects to /agent/queues (dashboard)
```

### Login Flow (Automatic - Embedded Mode)

```
1. Agent opens Amazon Connect CCP
   ↓
2. Amazon Connect loads app in iframe
   ↓
3. Streams API detects agent is logged in
   ↓
4. JavaScript extracts agent username
   ↓
5. JavaScript sends POST to /agent/auto-login
   ↓
6. (Same as manual login steps 6-10)
```

### Dashboard Refresh Flow (Every 15 Seconds)

```
1. JavaScript timer triggers every 15 seconds
   ↓
2. JavaScript sends POST to /agent/queues/refresh
   ↓
3. Flask gets agent_id from session
   ↓
4. Flask calls QueueService.get_queue_metrics(queue_ids, agent_id)
   ↓
5. QueueService makes 3 parallel API calls:
   a. Get queue details (names)
   b. Get current metrics (real-time)
   c. Get agent metrics (historical)
   ↓
6. QueueService combines all data
   ↓
7. Flask calls QueueService.get_agent_performance_summary(agent_id)
   ↓
8. QueueService gets aggregate metrics
   ↓
9. Flask returns JSON with all data
   ↓
10. JavaScript updates page without reload
```

## Key Technologies

### Backend
- **Python 3.9** - Programming language
- **Flask** - Web framework (handles HTTP requests)
- **boto3** - AWS SDK for Python (calls AWS APIs)
- **Flask-CORS** - Handles cross-origin requests
- **pytz** - Timezone handling (EST/EDT)

### Frontend
- **HTML5** - Page structure
- **CSS3** - Styling and layout
- **JavaScript (ES6)** - Interactivity and AJAX
- **Amazon Connect Streams API** - Agent detection

### Infrastructure
- **AWS Elastic Beanstalk** - Hosting (runs Flask app)
- **AWS CloudFront** - CDN (HTTPS and caching)
- **Amazon Connect** - Contact center APIs

## Why This Architecture?

### Why Elastic Beanstalk?
1. **Sessions**: Keeps agents logged in (Lambda is stateless)
2. **Simplicity**: One service handles everything
3. **No cold starts**: Always fast (Lambda has 1-3 second delays)
4. **Cost-effective**: ~$17/month for your usage
5. **Easy debugging**: All logs in one place

### Why CloudFront?
1. **HTTPS**: Required for Amazon Connect embedding
2. **Fast**: Caches static files (CSS, JS, images)
3. **Secure**: Protects against DDoS attacks
4. **Global**: Fast from anywhere in the world

### Why Flask?
1. **Simple**: Easy to learn for beginners
2. **Flexible**: Can handle both HTML pages and API endpoints
3. **Popular**: Lots of documentation and examples
4. **Python**: Same language as AWS SDK (boto3)

## Security

### Authentication
- Agents must log in with valid Amazon Connect username
- Session expires after 8 hours (standalone mode)
- Session tied to Streams API connection (embedded mode)

### Authorization
- App uses AWS credentials to call Connect APIs
- Credentials stored as environment variables (never in code)
- Each agent only sees their own queues

### Data Protection
- All traffic over HTTPS (encrypted)
- Cookies marked as Secure and HttpOnly
- SameSite=None for cross-origin (Amazon Connect embedding)
- Partitioned cookies for better privacy

### CORS Configuration
- Allows Amazon Connect domains to embed app
- Blocks other domains from embedding
- Credentials included in cross-origin requests

## Performance

### Caching Strategy
- CloudFront caches static files (CSS, JS, images) for 24 hours
- CloudFront does NOT cache API responses (always fresh data)
- No server-side caching (data always current)

### API Call Optimization
- Parallel API calls (fetch multiple queues at once)
- Batch operations (one call for all queues, not one per queue)
- 15-second refresh interval (balance between freshness and cost)

### Auto-Refresh Optimization
- Pauses when tab is hidden (saves API calls)
- Resumes when tab becomes visible
- Immediate refresh when returning to tab

## Monitoring and Debugging

### Logs
- **Elastic Beanstalk logs**: Application errors and API calls
- **CloudFront logs**: HTTP requests and caching
- **Browser console**: JavaScript errors and debug messages

### Debugging Tips
1. Check browser console (F12) for JavaScript errors
2. Check Elastic Beanstalk logs for Python errors
3. Check CloudWatch for AWS API errors
4. Use `/debug/session` endpoint to check session state

## Scalability

### Current Capacity
- Handles 10-50 agents easily
- t3.micro instance (1 vCPU, 1 GB RAM)
- Auto-refresh every 15 seconds per agent

### Scaling Up
- **50-100 agents**: Upgrade to t3.small ($15 → $30/month)
- **100-500 agents**: Upgrade to t3.medium + load balancer
- **500+ agents**: Consider migrating to Lambda + API Gateway

## Future Enhancements

### Potential Features
1. **Real-time updates**: WebSockets instead of polling
2. **Historical reports**: Daily/weekly performance reports
3. **Supervisor view**: See all agents' performance
4. **Alerts**: Notify when queues get too busy
5. **Mobile app**: Native iOS/Android apps

### Migration to Lambda
See `docs/LAMBDA_ALTERNATIVE.md` for detailed migration guide.

## Glossary

- **Agent**: Person who handles calls in Amazon Connect
- **Queue**: Waiting line for incoming calls
- **Routing Profile**: Defines which queues an agent handles
- **Contact**: A call, chat, or task in Amazon Connect
- **Metric**: Measurement (e.g., calls handled, average handle time)
- **Session**: Temporary storage that keeps agent logged in
- **Cookie**: Small file stored in browser to maintain session
- **AJAX**: JavaScript technique to update page without reload
- **API**: Application Programming Interface (how programs talk to each other)
- **SDK**: Software Development Kit (pre-built code to use APIs)
- **CDN**: Content Delivery Network (makes websites faster)
- **CORS**: Cross-Origin Resource Sharing (allows embedding)
- **iframe**: HTML element that embeds one webpage inside another

## Questions?

If you have questions about the architecture, check:
1. `docs/API_REFERENCE.md` - API endpoint details
2. `docs/TROUBLESHOOTING.md` - Common issues
3. Code comments - Every file has detailed explanations
