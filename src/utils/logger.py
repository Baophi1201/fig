"""
Centralized logging configuration
Supports LOG_LEVEL env variable: DEBUG, INFO, WARNING, ERROR
"""
import logging
import sys
import os

def setup_logger(name="GoLike", level=None):
    """
    Setup centralized logger
    
    Args:
        name: Logger name
        level: Logging level (overrides env if provided)
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # ✅ Support LOG_LEVEL env variable
    if level is None:
        env_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        level = getattr(logging, env_level, logging.INFO)
    
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger

# Default logger - reads LOG_LEVEL from env automatically
logger = setup_logger()
