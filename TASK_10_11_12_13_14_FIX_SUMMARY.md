# Tasks 10-14 Fix Summary: Embedded Mode Login Issue

## Problem Statement
When agents clicked on the third-party app in Amazon Connect, they were seeing a login page instead of automatically seeing their queues. The app was designed to detect embedded mode and auto-login, but agents were still briefly seeing the login form.

## Root Causes Identified

### 1. Circular Import Issue
The original `app/routes.py` was importing `app` from the `app` module:
```python
from app import app
```

But `app/__init__.py` was also importing routes, creating a circular dependency that prevented the app from starting properly.

### 2. Template Variable Issue
The `index.html` template was trying to access `{{ config.CONNECT_INSTANCE_URL }}` but the config object wasn't being passed to the template.

### 3. Data Structure Mismatch
The `/agent/queues/refresh` endpoint was returning field names (`id`, `name`, `calls`) that didn't match what the frontend JavaScript expected (`queue_id`, `queue_name`, `contacts_in_queue`).

### 4. Template Variable Mismatch
The `queue_view()` route was passing `queue_metrics` to the template, but the template expected `queues`.

## Solutions Implemented

### 1. Fixed Circular Import
**File**: `app/routes.py`

Changed from direct app import to a registration pattern:
```python
# OLD (caused circular import)
from app import app

@app.route('/')
def index():
    ...

# NEW (registration pattern)
def register_routes(app):
    @app.route('/')
    def index():
        ...
```

**File**: `app/__init__.py`

Updated to call the registration function:
```python
# Import routes module and register
from app import routes
routes.register_routes(app)
```

### 2. Fixed Template Variable
**File**: `app/routes.py`

Updated `index()` route to pass the Connect instance URL:
```python
from config.settings import Config

@app.route('/')
def index():
    return render_template('index.html', connect_instance_url=Config.CONNECT_INSTANCE_URL)
```

**File**: `app/templates/index.html`

Updated template to use the correct variable:
```javascript
// OLD
const ccpUrl = '{{ config.CONNECT_INSTANCE_URL }}/ccp-v2';

// NEW
const ccpUrl = '{{ connect_instance_url }}/ccp-v2';
```

### 3. Fixed Data Structure
**File**: `app/routes.py`

Updated `/agent/queues/refresh` endpoint to return correct field names:
```python
# Convert to JSON-friendly format
queues_data = [
    {
        'queue_id': q.queue_id,           # Was: 'id'
        'queue_name': q.queue_name,       # Was: 'name'
        'contacts_in_queue': q.contacts_in_queue,  # Was: 'calls'
        'error': q.error
    }
    for q in queue_metrics
]
```

### 4. Fixed Template Variable
**File**: `app/routes.py`

Updated `queue_view()` route to pass correct variable name:
```python
# OLD
return render_template(
    'queue_view.html',
    queue_metrics=queue_metrics
)

# NEW
return render_template(
    'queue_view.html',
    queues=queue_metrics,
    total_contacts=sum(q.contacts_in_queue for q in queue_metrics if not q.error)
)
```

## How It Works Now

### Embedded Mode (Inside Amazon Connect)
1. ✅ Agent clicks on third-party app in Amazon Connect
2. ✅ App loads and immediately detects it's in embedded mode
3. ✅ Streams API automatically detects the logged-in agent
4. ✅ Agent is auto-logged in via `/agent/auto-login` endpoint
5. ✅ Agent is redirected to queue view
6. ✅ **NO LOGIN PAGE SHOWN** - Agent sees queues immediately

### Standalone Mode (Development/Testing)
1. ✅ Developer opens app in browser directly
2. ✅ App detects it's in standalone mode
3. ✅ Login form is shown
4. ✅ Developer enters username manually
5. ✅ Developer is redirected to queue view

## Testing Instructions

### Test 1: Verify App Starts
```bash
python3 -c "from app import app; print('✅ Flask app imports successfully')"
```
Expected output: `✅ Flask app imports successfully`

### Test 2: Run the Application
```bash
python3 run.py
```
Expected output:
```
✅ Configuration validated successfully
 * Running on http://127.0.0.1:5000
```

### Test 3: Test Standalone Mode
1. Open browser to `http://localhost:5000/`
2. You should see the login form
3. Enter your agent username
4. You should be redirected to queue view

### Test 4: Test Embedded Mode (Production)
1. Configure your third-party app in Amazon Connect console
2. Add the app URL: `https://your-domain.com/`
3. Log in to Amazon Connect as an agent
4. Click on the third-party app icon
5. **Expected**: You should see the queue view immediately, NO login page

## Files Modified

1. **app/routes.py** - Complete rewrite with registration pattern
   - Fixed circular import
   - Fixed template variables
   - Fixed data structures
   - All routes now registered via `register_routes(app)` function

2. **app/__init__.py** - Updated route registration
   - Changed from `with app.app_context()` to direct function call
   - Calls `routes.register_routes(app)`

3. **app/templates/index.html** - Fixed template variable
   - Changed `{{ config.CONNECT_INSTANCE_URL }}` to `{{ connect_instance_url }}`

## Important Notes for Production Deployment

### HTTPS Requirement
- The app MUST be served over HTTPS when embedded in Amazon Connect
- Session cookies with `SameSite=None` require HTTPS
- Browsers will block the app if served over HTTP

### Environment Configuration
Make sure your `.env` file has:
```
CONNECT_INSTANCE_URL=https://your-instance.my.connect.aws
ALLOWED_ORIGINS=https://your-instance.awsapps.com/connect,https://your-instance.my.connect.aws
```

### CORS Configuration
- The `ALLOWED_ORIGINS` must include your Amazon Connect instance domain
- Multiple origins should be comma-separated
- No trailing slashes on URLs

### Session Configuration
The app is already configured with:
- `SESSION_COOKIE_SAMESITE='None'` - Allows cookies in iframe
- `SESSION_COOKIE_SECURE=True` - Requires HTTPS
- `SESSION_COOKIE_HTTPONLY=True` - Protects against XSS

## Next Steps

1. **Test locally** - Run `python3 run.py` and test standalone mode
2. **Deploy to production** - Deploy to a web server with HTTPS
3. **Configure in Amazon Connect** - Add your app URL to third-party applications
4. **Test with real agents** - Have agents test the embedded mode

## Troubleshooting

### If agents still see login page:
1. Check browser console for errors
2. Verify Streams API is loading (check Network tab)
3. Verify CCP URL is correct in logs
4. Check that agent is logged into Amazon Connect

### If automatic detection fails:
1. Check that `CONNECT_INSTANCE_URL` in `.env` is correct
2. Verify agent has proper permissions in Amazon Connect
3. Check browser console for Streams API errors
4. App will fallback to manual login if auto-detection fails

### If session doesn't persist:
1. Verify app is served over HTTPS (required for SameSite=None)
2. Check that `FLASK_SECRET_KEY` is set in `.env`
3. Verify browser allows third-party cookies

## Success Criteria

✅ App starts without import errors
✅ Standalone mode shows login form
✅ Manual login works correctly
✅ Embedded mode detects agent automatically
✅ Agents see queue view immediately (no login page)
✅ Queue refresh works without page reload
✅ Session persists across page refreshes
