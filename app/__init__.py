"""
Flask Application Factory with Iframe Security Configuration

This module initializes the Flask web application with special security settings
that allow it to be embedded as an iframe inside Amazon Connect's agent workspace.

Key Concepts for Beginners:
- Flask: A Python web framework that helps you build web applications
- Iframe: A way to embed one webpage inside another (like a window within a window)
- Security Headers: Special instructions sent to the browser to control security behavior
- CORS: Cross-Origin Resource Sharing - allows your app to accept requests from other domains
- Session: A way to remember information about a user across multiple page visits

Why This Matters:
When you embed your app in Amazon Connect, the browser treats it as an iframe.
Browsers have strict security rules for iframes to protect users. We need to:
1. Tell browsers it's OK for Amazon Connect to embed our app (CSP headers)
2. Allow Amazon Connect domains to make requests to our app (CORS)
3. Make session cookies work inside iframes (SameSite=None)
"""

from flask import Flask, session
from flask_cors import CORS
from config.settings import Config


class SecurityConfig:
    """
    Security configuration for iframe embedding compatibility.
    
    This class contains all the security settings needed to make your app
    work properly when embedded in Amazon Connect's agent workspace.
    """
    
    @staticmethod
    def get_csp_header(allowed_origins):
        """
        Generate Content-Security-Policy header for iframe embedding.
        
        CSP (Content-Security-Policy) tells the browser which websites are allowed
        to embed your app in an iframe. This prevents malicious sites from
        embedding your app without permission.
        
        Args:
            allowed_origins: List of domain URLs that can embed this app
            
        Returns:
            String containing the CSP header value
            
        Example:
            If allowed_origins = ['https://myinstance.awsapps.com']
            Returns: "frame-ancestors 'self' https://myinstance.awsapps.com"
            
        Explanation:
            - frame-ancestors: Controls who can embed this page in an iframe
            - 'self': The app can embed itself (for testing)
            - https://myinstance.awsapps.com: Amazon Connect can embed the app
        """
        # Start with 'self' to allow the app to embed itself
        frame_ancestors = ["'self'"]
        
        # Add each allowed origin
        frame_ancestors.extend(allowed_origins)
        
        # Join them into a single string
        csp_value = f"frame-ancestors {' '.join(frame_ancestors)}"
        
        return csp_value
    
    @staticmethod
    def configure_session_for_iframe(app):
        """
        Configure Flask session cookies to work inside iframes.
        
        Problem: By default, browsers block cookies in iframes for security.
        Solution: Set SameSite=None and Secure=True to allow iframe cookies.
        
        Args:
            app: The Flask application instance
            
        Important Notes:
            - SameSite=None: Allows cookies to be sent in cross-site contexts (iframes)
            - SESSION_COOKIE_SECURE=True: Requires HTTPS (browsers require this with SameSite=None)
            - SESSION_COOKIE_SAMESITE='None': Must be the string 'None', not Python None
            - In development (HTTP), we use Lax instead of None to allow cookies to work
        """
        from config.settings import Config
        
        if Config.FLASK_DEBUG:
            # Development mode (HTTP) - use Lax for local testing
            app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
            app.config['SESSION_COOKIE_SECURE'] = False
        else:
            # Production mode (HTTPS) - use None for iframe embedding
            app.config['SESSION_COOKIE_SAMESITE'] = 'None'
            app.config['SESSION_COOKIE_SECURE'] = True
        
        # Make session cookies accessible only via HTTP (not JavaScript)
        # This adds extra security against XSS attacks
        app.config['SESSION_COOKIE_HTTPONLY'] = True


def create_app():
    """
    Application factory function that creates and configures the Flask app.
    
    This is called the "factory pattern" - instead of creating the app directly,
    we use a function to create it. This makes testing easier and allows for
    different configurations (development vs production).
    
    Returns:
        Configured Flask application instance
    """
    
    # ============================================
    # Step 1: Create Flask Application
    # ============================================
    
    app = Flask(__name__)
    
    # Set secret key for session management
    # This key is used to encrypt session data so users can't tamper with it
    app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
    
    # Enable debug mode if configured (shows detailed errors)
    app.config['DEBUG'] = Config.FLASK_DEBUG
    
    # ============================================
    # Step 2: Configure Session for Iframe
    # ============================================
    
    SecurityConfig.configure_session_for_iframe(app)
    
    # ============================================
    # Step 3: Configure CORS
    # ============================================
    
    # Get allowed origins from configuration
    allowed_origins = Config.get_allowed_origins()
    
    # In development mode, add localhost to allowed origins
    if Config.FLASK_DEBUG:
        allowed_origins.extend([
            'http://localhost:5000',
            'http://127.0.0.1:5000',
            'http://localhost:8080',
            'http://127.0.0.1:8080'
        ])
    
    # Configure CORS to allow requests from Amazon Connect domains
    # CORS (Cross-Origin Resource Sharing) allows your app to accept requests
    # from different domains (like Amazon Connect's domain)
    CORS(
        app,
        origins=allowed_origins,  # Only these domains can make requests
        supports_credentials=True,  # Allow cookies to be sent with requests
        allow_headers=['Content-Type', 'Authorization'],  # Allowed request headers
        methods=['GET', 'POST', 'OPTIONS']  # Allowed HTTP methods
    )
    
    # ============================================
    # Step 4: Add Security Headers to All Responses
    # ============================================
    
    @app.after_request
    def add_security_headers(response):
        """
        Add security headers to every response.
        
        This function runs after every request and adds security headers
        to the response before sending it to the browser.
        
        Args:
            response: The Flask response object
            
        Returns:
            Modified response with security headers added
        """
        
        # Content-Security-Policy: Controls iframe embedding
        csp_header = SecurityConfig.get_csp_header(allowed_origins)
        response.headers['Content-Security-Policy'] = csp_header
        
        # X-Frame-Options: In development, allow same origin; in production, same origin only
        # Note: We rely on CSP frame-ancestors for iframe control, not X-Frame-Options
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # X-Content-Type-Options: Prevents browsers from guessing file types
        # This prevents security vulnerabilities from incorrect MIME type handling
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # ngrok-skip-browser-warning: Bypass ngrok warning page in iframes
        # This header tells ngrok to skip the warning page when the app is loaded in an iframe
        # Required for free ngrok accounts when embedding in Amazon Connect
        response.headers['ngrok-skip-browser-warning'] = 'true'
        
        return response
    
    # ============================================
    # Step 5: Register Routes
    # ============================================
    
    # Import routes module to register routes with the app
    # This must be done after app creation to avoid circular imports
    from app import routes
    routes.register_routes(app)
    
    # Health check route (for monitoring)
    @app.route('/health')
    def health_check():
        """
        Simple health check endpoint to verify the app is running.
        
        Returns:
            JSON response with status
        """
        return {
            'status': 'healthy',
            'message': 'Amazon Connect Workshop App is running!',
            'iframe_ready': True
        }
    
    return app


# Create the application instance
# This is what gets imported when you do: from app import app
app = create_app()
