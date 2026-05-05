"""
Retry utilities with decorators
"""
import time
import random
import logging
from functools import wraps
import requests

logger = logging.getLogger(__name__)

def retry_on_network_error(max_retries=3):
    """
    Retry decorator for network errors only
    
    Args:
        max_retries: Maximum number of retry attempts
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    
                    wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(f"{func.__name__} retry {attempt + 1}/{max_retries}: {e}. Wait {wait_time:.1f}s")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

def request_with_retry(func, retries=3, delay=2):
    """
    Function-based retry for requests
    
    Args:
        func: Function to retry
        retries: Number of retry attempts
        delay: Base delay between retries
    """
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Request failed after {retries} attempts: {e}")
                raise
            wait_time = delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    return None