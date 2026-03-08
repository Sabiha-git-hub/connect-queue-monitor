"""
Configuration Manager for Amazon Connect Workshop App

This module loads and validates all configuration settings from environment variables.
Think of it as the "control panel" for your app - all settings are defined here.

Key Concepts:
- Environment Variables: Settings stored outside your code (in .env file)
- Validation: Checking that required settings are present and correctly formatted
- UUID: Universally Unique Identifier - Amazon Connect uses this format for instance IDs
"""

import os
import re
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
# This reads the .env file and makes variables available via os.getenv()
load_dotenv()


class Config:
    """
    Application configuration loaded from environment variables.
    
    This class acts as a central place to access all app settings.
    Instead of calling os.getenv() everywhere, we use Config.SETTING_NAME
    """
    
    # ============================================
    # AWS Configuration
    # ============================================
    
    # AWS region where your Amazon Connect instance is located
    # Try CONNECT_AWS_REGION first (for Amplify), fallback to AWS_REGION
    AWS_REGION = os.getenv('CONNECT_AWS_REGION') or os.getenv('AWS_REGION', 'us-east-1')
    
    # AWS credentials (optional - can use IAM roles or AWS CLI config instead)
    # Try CONNECT_AWS_* first (for Amplify), fallback to AWS_*
    AWS_ACCESS_KEY_ID = os.getenv('CONNECT_AWS_ACCESS_KEY_ID') or os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('CONNECT_AWS_SECRET_ACCESS_KEY') or os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_SESSION_TOKEN = os.getenv('CONNECT_AWS_SESSION_TOKEN') or os.getenv('AWS_SESSION_TOKEN')
    
    # ============================================
    # Amazon Connect Configuration
    # ============================================
    
    # Your Amazon Connect instance ID (UUID format)
    CONNECT_INSTANCE_ID = os.getenv('CONNECT_INSTANCE_ID', '')
    
    # Your Amazon Connect instance URL (for Streams API)
    CONNECT_INSTANCE_URL = os.getenv('CONNECT_INSTANCE_URL', '')
    
    # ============================================
    # Flask Application Configuration
    # ============================================
    
    # Secret key for Flask session management (keeps user sessions secure)
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Debug mode - shows detailed errors (only use in development!)
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # ============================================
    # Iframe Embedding Configuration
    # ============================================
    
    # Comma-separated list of allowed origins for CORS and iframe embedding
    # These are the domains that can embed your app in an iframe
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '')
    
    @classmethod
    def validate(cls):
        """
        Validate that all required configuration is present and correctly formatted.
        
        This is called when the app starts to catch configuration errors early.
        It's better to fail fast with a clear error than to crash mysteriously later!
        
        Raises:
            ValueError: If any required configuration is missing or invalid
        """
        errors = []
        
        # Check AWS Region
        if not cls.AWS_REGION:
            errors.append("AWS_REGION is required")
        
        # Check Amazon Connect Instance ID
        if not cls.CONNECT_INSTANCE_ID:
            errors.append("CONNECT_INSTANCE_ID is required")
        elif not cls._is_valid_uuid(cls.CONNECT_INSTANCE_ID):
            errors.append(
                f"CONNECT_INSTANCE_ID must be a valid UUID format "
                f"(xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), "
                f"got: {cls.CONNECT_INSTANCE_ID}"
            )
        
        # Check Amazon Connect Instance URL
        if not cls.CONNECT_INSTANCE_URL:
            errors.append("CONNECT_INSTANCE_URL is required")
        elif not cls.CONNECT_INSTANCE_URL.startswith('https://'):
            errors.append(
                f"CONNECT_INSTANCE_URL must start with https://, "
                f"got: {cls.CONNECT_INSTANCE_URL}"
            )
        
        # Check Flask Secret Key (warn if using default)
        if cls.FLASK_SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append(
                "FLASK_SECRET_KEY is using default value. "
                "Generate a secure random key for production!"
            )
        
        # Check Allowed Origins for iframe embedding
        if not cls.ALLOWED_ORIGINS:
            errors.append(
                "ALLOWED_ORIGINS is required for iframe embedding. "
                "Add your Amazon Connect instance domains."
            )
        
        # If there are errors, raise ValueError with all error messages
        if errors:
            error_message = "\n".join([f"  - {error}" for error in errors])
            raise ValueError(f"Configuration validation failed:\n{error_message}")
    
    @classmethod
    def get_instance_id(cls) -> str:
        """
        Get the Connect instance ID with format validation.
        
        Returns:
            The validated instance ID
            
        Raises:
            ValueError: If instance ID is not in valid UUID format
        """
        instance_id = cls.CONNECT_INSTANCE_ID
        
        if not cls._is_valid_uuid(instance_id):
            raise ValueError(
                f"Invalid Connect instance ID format. "
                f"Expected UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx), "
                f"got: {instance_id}"
            )
        
        return instance_id
    
    @classmethod
    def get_allowed_origins(cls) -> List[str]:
        """
        Parse and return the list of allowed origins for CORS/iframe embedding.
        
        Returns:
            List of allowed origin URLs
        """
        if not cls.ALLOWED_ORIGINS:
            return []
        
        # Split by comma and strip whitespace from each origin
        origins = [origin.strip() for origin in cls.ALLOWED_ORIGINS.split(',')]
        
        # Filter out empty strings
        origins = [origin for origin in origins if origin]
        
        return origins
    
    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        """
        Check if a string is in valid UUID format.
        
        UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        Where x is a hexadecimal digit (0-9, a-f)
        
        Args:
            uuid_string: String to validate
            
        Returns:
            True if valid UUID format, False otherwise
        """
        # Regular expression pattern for UUID format
        # ^ = start of string, $ = end of string
        # [0-9a-f] = any hexadecimal digit
        # {8} = exactly 8 characters
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE  # Accept both uppercase and lowercase
        )
        
        return bool(uuid_pattern.match(uuid_string))


# Note: Configuration validation is now done explicitly in run.py
# This allows better control over startup behavior and error handling
