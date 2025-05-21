import os
import json
from dotenv import load_dotenv
from app.utils.logger import setup_logger

logger = setup_logger()

def load_config():
    """
    Load configuration from environment variables
    
    Returns:
        dict: Configuration values
    """
    # Load environment variables from .env file
    dotenv_path = os.path.join("configs", ".env")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info(f"Loaded configuration from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Using environment variables if available.")
    
    # Define configuration with defaults
    config = {
        # Job search parameters
        'TARGET_PAY_GRADE_MIN': os.environ.get('TARGET_PAY_GRADE_MIN', '70000'),
        'TARGET_LOCATION': os.environ.get('TARGET_LOCATION', 'New York, NY'),
        'USER_RESUME_PATH': os.environ.get('USER_RESUME_PATH', 'data/resume.pdf'),
        
        # API keys
        'INDEED_API_KEY': os.environ.get('INDEED_API_KEY', ''),
        'LINKEDIN_EMAIL': os.environ.get('LINKEDIN_EMAIL', ''),
        'LINKEDIN_PASSWORD': os.environ.get('LINKEDIN_PASSWORD', ''),
        'GOOGLE_GEMINI_API_KEY': os.environ.get('GOOGLE_GEMINI_API_KEY', ''),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
        'AI_TEXT_GENERATION_API_KEY': os.environ.get('AI_TEXT_GENERATION_API_KEY', ''),
        
        # Email notification settings
        'SMTP_HOST': os.environ.get('SMTP_HOST', ''),
        'SMTP_PORT': os.environ.get('SMTP_PORT', '587'),
        'SMTP_USER': os.environ.get('SMTP_USER', ''),
        'SMTP_PASSWORD': os.environ.get('SMTP_PASSWORD', ''),
        'NOTIFICATION_EMAIL_RECEIVER': os.environ.get('NOTIFICATION_EMAIL_RECEIVER', ''),
        
        # Application settings
        'MAX_JOBS_PER_SCAN': os.environ.get('MAX_JOBS_PER_SCAN', '50'),
        'AUTO_APPLY_ENABLED': os.environ.get('AUTO_APPLY_ENABLED', 'False').lower() in ('true', '1', 't'),
        'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO'),
    }
    
    return config

def save_config(config):
    """
    Save configuration to a file
    
    Args:
        config (dict): Configuration values
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Create configs directory if it doesn't exist
        os.makedirs("configs", exist_ok=True)
        
        # Save to JSON file (non-sensitive values only)
        safe_config = {
            'TARGET_PAY_GRADE_MIN': config.get('TARGET_PAY_GRADE_MIN', '70000'),
            'TARGET_LOCATION': config.get('TARGET_LOCATION', 'New York, NY'),
            'USER_RESUME_PATH': config.get('USER_RESUME_PATH', 'data/resume.pdf'),
            'MAX_JOBS_PER_SCAN': config.get('MAX_JOBS_PER_SCAN', '50'),
            'AUTO_APPLY_ENABLED': config.get('AUTO_APPLY_ENABLED', False),
            'LOG_LEVEL': config.get('LOG_LEVEL', 'INFO'),
            'NOTIFICATION_EMAIL_RECEIVER': config.get('NOTIFICATION_EMAIL_RECEIVER', ''),
        }
        
        with open(os.path.join("configs", "config.json"), 'w') as f:
            json.dump(safe_config, f, indent=4)
        
        logger.info("Configuration saved successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}", exc_info=True)
        return False
