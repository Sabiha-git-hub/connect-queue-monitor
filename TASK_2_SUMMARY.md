# Task 2 Complete: Flask Iframe Security Configuration ✅

## What We Built

We configured Flask with special security settings that allow your app to be embedded as an iframe inside Amazon Connect's agent workspace. Without these configurations, browsers would block your app from being embedded.

## File Created

**`app/__init__.py`** - Flask application factory with:
- Flask app initialization
- Iframe-compatible session configuration
- CORS (Cross-Origin Resource Sharing) setup
- Security headers for all responses
- Health check endpoint

## Why Iframe Security Matters

When you embed your app in Amazon Connect, browsers apply strict security rules:

### The Problem
- **Default behavior**: Browsers block cookies in iframes for security
- **Result**: Your app can't maintain user sessions when embedded
- **Solution**: Configure specific security headers and cookie settings

### What We Fixed
1. **Session Cookies**: Set `SameSite=None` to work in iframes
2. **CSP Headers**: Tell browsers Amazon Connect can embed your app
3. **CORS**: Allow requests from Amazon Connect domains

## Key Components

### 1. SecurityConfig Class

Manages all iframe security settings:

```python
class SecurityConfig:
    @staticmethod
    def get_csp_header(allowed_origins):
        # Generates: "frame-ancestors 'self' https://your-instance.awsapps.com"
        # This tells browsers which domains can embed your app
        
    @staticmethod
    def configure_session_for_iframe(app):
        # Sets SameSite=None and Secure=True for iframe cookies
```

### 2. Security Headers

Added to every response:

**Content-Security-Policy (CSP)**
- Controls which domains can embed your app in an iframe
- Format: `frame-ancestors 'self' https://your-instance.awsapps.com`
- Prevents malicious sites from embedding your app

**X-Frame-Options**
- Older way to control iframe embedding (for older browsers)
- Set to `SAMEORIGIN` for compatibility
- CSP is more flexible, but we include both

**X-Content-Type-Options**
- Set to `nosniff`
- Prevents browsers from guessing file types
- Adds security against MIME type attacks

### 3. CORS Configuration

Allows Amazon Connect domains to make requests to your app:

```python
CORS(
    app,
    origins=allowed_origins,        # Only these domains can make requests
    supports_credentials=True,      # Allow cookies with requests
    allow_headers=['Content-Type', 'Authorization'],
    methods=['GET', 'POST', 'OPTIONS']
)
```

### 4. Session Configuration

Makes session cookies work in iframes:

```python
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Allow cross-site cookies
app.config['SESSION_COOKIE_SECURE'] = True      # Require HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True    # Protect against XSS
```

## How It Works

### Request Flow

```
1. Agent opens Amazon Connect workspace
   ↓
2. Amazon Connect loads your app in an iframe
   ↓
3. Browser checks security headers
   ↓
4. CSP header says: "Amazon Connect can embed this app" ✓
   ↓
5. CORS allows requests from Amazon Connect domain ✓
   ↓
6. Session cookies work with SameSite=None ✓
   ↓
7. Your app loads successfully in the iframe!
```

## Testing

We created `test_flask_app.py` to verify the configuration:

```bash
python3 test_flask_app.py
```

**Tests performed:**
1. ✅ Flask app creation
2. ✅ Security headers present in responses
3. ✅ CSP header contains `frame-ancestors`
4. ✅ X-Frame-Options header set
5. ✅ X-Content-Type-Options header set
6. ✅ Health check endpoint working

**Result:** 🎉 All tests passed!

## Health Check Endpoint

Added `/health` route for monitoring:

```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'message': 'Amazon Connect Workshop App is running!',
        'iframe_ready': True
    }
```

**Test it:**
```bash
curl http://localhost:5000/health
```

## Configuration Requirements

Your `.env` file must have:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True

# Iframe Embedding - CRITICAL!
ALLOWED_ORIGINS=https://your-instance.awsapps.com,https://your-instance.my.connect.aws
```

**ALLOWED_ORIGINS** is crucial - it lists which domains can:
- Embed your app in an iframe
- Make CORS requests to your app

## Security Best Practices Implemented

1. **Whitelist Approach**: Only specified domains can embed your app
2. **HTTPS Required**: Session cookies require secure connections
3. **HttpOnly Cookies**: Protects against XSS attacks
4. **Content Type Protection**: Prevents MIME type sniffing
5. **Explicit CORS**: Only allowed origins can make requests

## Common Issues & Solutions

### Issue: "Refused to display in a frame"
**Cause**: CSP or X-Frame-Options blocking iframe
**Solution**: Check ALLOWED_ORIGINS includes Amazon Connect domain

### Issue: "Session not persisting in iframe"
**Cause**: SameSite cookie policy blocking
**Solution**: Ensure SameSite=None and Secure=True are set

### Issue: "CORS error when making requests"
**Cause**: Amazon Connect domain not in allowed origins
**Solution**: Add domain to ALLOWED_ORIGINS in .env

## What You Learned

1. **Iframe Security**: How browsers protect users from malicious embedding
2. **CSP Headers**: Modern way to control iframe embedding
3. **CORS**: Allowing cross-origin requests safely
4. **Session Cookies**: Making cookies work in iframe context
5. **Security Headers**: Multiple layers of protection

## Next Steps

With Flask configured for iframe embedding, you moved on to:
- **Task 3**: Mode detection (detect if embedded or standalone)
- **Task 5**: Streams API integration (automatic agent detection)

## Quick Reference

### Check Security Headers

```bash
# Start Flask app
python3 -c "from app import app; app.run()"

# In another terminal, check headers
curl -I http://localhost:5000/health
```

Look for:
- `Content-Security-Policy: frame-ancestors ...`
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`

### Test Iframe Embedding Locally

Create a test HTML file:
```html
<!DOCTYPE html>
<html>
<body>
    <h1>Iframe Test</h1>
    <iframe src="http://localhost:5000" width="800" height="600"></iframe>
</body>
</html>
```

Open in browser to test iframe embedding.
