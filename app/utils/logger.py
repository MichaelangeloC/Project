import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Singleton logger instance
_logger = None

def setup_logger(name="job_application_automator", log_level=None):
    """
    Set up and return a logger instance
    
    Args:
        name (str): Logger name
        log_level (str, optional): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger
    
    # Return existing logger if already set up
    if _logger is not None:
        return _logger
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatted timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    
    # Set up logger
    logger = logging.getLogger(name)
    
    # Set log level from environment or default to INFO
    if not log_level:
        log_level = os.environ.get('LOG_LEVEL', 'INFO')
    
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Configure log format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # Add file handler with rotation (10MB max size, keep 5 backup logs)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    logger.info(f"Logger initialized with level {log_level}")
    
    # Store logger as singleton
    _logger = logger
    
    return logger
