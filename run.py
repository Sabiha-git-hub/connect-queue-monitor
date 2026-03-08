#!/usr/bin/env python3
"""
Amazon Connect Queue Monitor - Application Entry Point

This script starts the Flask development server and validates
configuration before running the application.

Usage:
    python3 run.py

The application will be available at http://localhost:5000
"""

import sys
import logging
from app import app
from config.settings import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_configuration():
    """
    Validate required configuration before starting the application.
    Exits with error code 1 if validation fails.
    """
    logger.info("🔍 Validating configuration...")
    
    try:
        # Validate all required configuration
        Config.validate()
        
        logger.info("✅ Configuration validation passed")
        logger.info(f"   - AWS Region: {Config.AWS_REGION}")
        logger.info(f"   - Connect Instance ID: {Config.get_instance_id()}")
        logger.info(f"   - Connect Instance URL: {Config.CONNECT_INSTANCE_URL}")
        logger.info(f"   - Allowed Origins: {', '.join(Config.get_allowed_origins())}")
        
        return True
        
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        logger.error("   Please check your .env file and ensure all required variables are set.")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during configuration validation: {e}")
        return False


def main():
    """
    Main entry point for the application.
    Validates configuration and starts the Flask development server.
    """
    logger.info("🚀 Starting Amazon Connect Queue Monitor...")
    
    # Validate configuration
    if not validate_configuration():
        logger.error("⛔ Application startup aborted due to configuration errors.")
        sys.exit(1)
    
    # Display startup information
    logger.info("=" * 60)
    logger.info("📊 Amazon Connect Queue Monitor")
    logger.info("   Workshop: Building Third-Party Apps for Amazon Connect")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🌐 Application will be available at:")
    logger.info("   http://localhost:8080")
    logger.info("")
    logger.info("📝 Modes supported:")
    logger.info("   - Embedded Mode: Automatic agent detection via Streams API")
    logger.info("   - Standalone Mode: Manual login for development/testing")
    logger.info("")
    logger.info("⚠️  Note: This is a development server. Do not use in production.")
    logger.info("   For production, use a WSGI server like Gunicorn or uWSGI.")
    logger.info("")
    logger.info("=" * 60)
    
    # Start Flask development server
    try:
        app.run(
            host='0.0.0.0',  # Listen on all interfaces
            port=8080,        # Using port 8080 (port 5000 often used by AirPlay on macOS)
            debug=True,  # Enable debug mode for development
            use_reloader=True  # Auto-reload on code changes
        )
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
