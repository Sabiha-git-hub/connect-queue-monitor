# HTTP 403 Error Fix

## Problem
When trying to access `http://localhost:5000/` in the browser, you got an "HTTP ERROR 403 - Access Denied" message.

## Root Cause
The Flask app was configured with strict CORS (Cross-Origin Resource Sharing) and session security settings designed for production deployment with HTTPS. These settings were blocking local development access:

1. **CORS Origins**: Only allowed requests from your Amazon Connect domains, not localhost
2. **Session Cookies**: Required HTTPS (`SESSION_COOKIE_SECURE=True`), which doesn't work with `http://localhost`
3. **X-Frame-Options**: Restricted iframe embedding

## Solution
Updated `app/__init__.py` to detect development mode and adjust security settings accordingly:

### 1. Added Localhost to CORS Origins (Development Only)
```python
# In development mode, add localhost to allowed origins
if Config.FLASK_DEBUG:
    allowed_origins.extend([
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'http://localhost:8080',
        'http://127.0.0.1:8080'
    ])
```

### 2. Adjusted Session Cookie Settings for Development
```python
if Config.FLASK_DEBUG:
    # Development mode (HTTP) - use Lax for local testing
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False
else:
    # Production mode (HTTPS) - use None for iframe embedding
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
```

### 3. Relaxed X-Frame-Options in Development
```python
if Config.FLASK_DEBUG:
    # In development, don't restrict framing for easier testing
    response.headers['X-Frame-Options'] = 'ALLOWALL'
else:
    # In production, only allow same origin
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
```

## How It Works Now

### Development Mode (FLASK_DEBUG=True)
- ✅ Allows access from `http://localhost:5000`
- ✅ Session cookies work without HTTPS
- ✅ No CORS restrictions for local testing
- ✅ Relaxed security headers for easier development

### Production Mode (FLASK_DEBUG=False)
- ✅ Strict CORS - only Amazon Connect domains allowed
- ✅ Secure session cookies - requires HTTPS
- ✅ Iframe embedding protection
- ✅ Full security headers enabled

## Testing

Now you can run the app and access it locally:

```bash
python3 run.py
```

Then open your browser to: `http://localhost:5000/`

You should now see the login page without any 403 error!

## Important Notes

### Development vs Production
The app automatically detects the mode based on `FLASK_DEBUG` in your `.env` file:
- `FLASK_DEBUG=True` → Development mode (relaxed security)
- `FLASK_DEBUG=False` → Production mode (strict security)

### Before Deploying to Production
Make sure to:
1. Set `FLASK_DEBUG=False` in your production `.env`
2. Use HTTPS (required for iframe embedding)
3. Update `ALLOWED_ORIGINS` to only include your Amazon Connect domains
4. Never expose development mode to the internet

### Security Trade-offs
Development mode is less secure but easier to work with:
- ✅ Good for: Local testing, development, debugging
- ❌ Bad for: Production deployment, public access

Production mode is secure but requires proper setup:
- ✅ Good for: Production deployment, embedded in Amazon Connect
- ❌ Bad for: Local development without HTTPS

## Files Modified
- `app/__init__.py` - Added development mode detection and conditional security settings
