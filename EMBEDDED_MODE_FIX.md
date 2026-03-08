# Embedded Mode Fix - No Login Page for Agents

## Problem
When agents clicked on the third-party app in Amazon Connect, they were seeing a login page instead of automatically seeing their queues.

## Root Cause
The application was designed to show the login page first, then detect if it was in embedded mode and trigger automatic login. This created a brief moment where agents saw the login form before being redirected.

## Solution
Modified the application to:

1. **Pass Connect Instance URL to Template**: Updated `app/routes.py` to pass the `connect_instance_url` to the template so the Streams API can initialize properly.

2. **Fixed Template Variable**: Changed `{{ config.CONNECT_INSTANCE_URL }}` to `{{ connect_instance_url }}` in `index.html` to use the correct variable.

3. **Fixed Data Structure**: Updated the `/agent/queues/refresh` endpoint to return the correct field names that match what the frontend JavaScript expects:
   - Changed `id` → `queue_id`
   - Changed `name` → `queue_name`
   - Changed `calls` → `contacts_in_queue`

4. **Fixed Queue View Template**: Updated `queue_view()` route to pass `queues` instead of `queue_metrics` to match the template expectations.

## How It Works Now

### Embedded Mode (Inside Amazon Connect)
1. Agent clicks on third-party app in Amazon Connect
2. App loads and immediately detects it's in embedded mode
3. Streams API automatically detects the logged-in agent
4. Agent is auto-logged in via `/agent/auto-login` endpoint
5. Agent is redirected to queue view - **NO LOGIN PAGE SHOWN**
6. Agent sees their queues and call counts immediately

### Standalone Mode (Development/Testing)
1. Developer opens app in browser directly
2. App detects it's in standalone mode
3. Login form is shown
4. Developer enters username manually
5. Developer is redirected to queue view

## Testing

### Test Embedded Mode
1. Configure your third-party app in Amazon Connect console
2. Add the app URL: `https://your-domain.com/` (or `http://localhost:5000/` for testing)
3. Log in to Amazon Connect as an agent
4. Click on the third-party app icon
5. **Expected**: You should see the queue view immediately, no login page

### Test Standalone Mode
1. Open `http://localhost:5000/` in a regular browser (not embedded)
2. **Expected**: You should see the login form
3. Enter your agent username
4. **Expected**: You should be redirected to queue view

## Files Modified
- `app/routes.py` - Pass connect_instance_url to template, fix data structures
- `app/templates/index.html` - Use correct template variable for CCP URL

## Next Steps
To deploy this to production:
1. Make sure your `.env` file has the correct `CONNECT_INSTANCE_URL`
2. Deploy the application to a web server (AWS EC2, Elastic Beanstalk, etc.)
3. Configure HTTPS (required for Amazon Connect embedding)
4. Add your app URL to Amazon Connect third-party applications
5. Test with real agents

## Important Notes
- The app MUST be served over HTTPS when embedded in Amazon Connect
- The `ALLOWED_ORIGINS` in `.env` must include your Amazon Connect instance domain
- Agents must be logged into Amazon Connect for automatic detection to work
