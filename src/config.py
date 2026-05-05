"""
Centralized configuration for GoLike Instagram Automation
"""
import os
from typing import Dict, Any

class Config:
    """Centralized configuration management"""
    
    # ================== NETWORK SETTINGS ==================
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '15'))
    REQUEST_TIMEOUT_SHORT = int(os.getenv('REQUEST_TIMEOUT_SHORT', '10'))
    
    # ================== RATE LIMITING ==================
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '10'))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    
    # ================== CACHE SETTINGS ==================
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', '300'))  # 5 minutes
    SESSION_CACHE_DURATION = int(os.getenv('SESSION_CACHE_DURATION', '1800'))  # 30 minutes
    
    # ================== JOB EXECUTION ==================
    COMPLETE_JOB_DELAY = int(os.getenv('COMPLETE_JOB_DELAY', '10'))  # Wait before completing
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    
    # ================== THREADING ==================
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '5'))
    THREAD_DELAY = float(os.getenv('THREAD_DELAY', '2.0'))  # Delay between threads
    
    # ================== LOGGING ==================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # ================== RETRY SETTINGS ==================
    RETRY_BASE_DELAY = float(os.getenv('RETRY_BASE_DELAY', '2.0'))
    RETRY_MAX_DELAY = float(os.getenv('RETRY_MAX_DELAY', '60.0'))
    RETRY_EXPONENTIAL_BASE = float(os.getenv('RETRY_EXPONENTIAL_BASE', '2.0'))
    
    # ================== INSTAGRAM SPECIFIC ==================
    INSTAGRAM_HOMEPAGE_URL = 'https://www.instagram.com/'
    INSTAGRAM_FOLLOW_URL = 'https://www.instagram.com/web/friendships/{}/follow/'
    INSTAGRAM_LIKE_URL = 'https://www.instagram.com/web/likes/{}/like/'
    
    # ================== GOLIKE SPECIFIC ==================
    GOLIKE_BASE_URL = 'https://gateway.golike.net/api'
    GOLIKE_JOBS_URL = f'{GOLIKE_BASE_URL}/advertising/publishers/instagram/jobs'
    GOLIKE_COMPLETE_URL = f'{GOLIKE_BASE_URL}/advertising/publishers/instagram/complete-jobs'
    GOLIKE_COMPLETE_2026_URL = f'{GOLIKE_BASE_URL}/advertising/publishers/complete-jobs-2026'
    GOLIKE_SKIP_URL = f'{GOLIKE_BASE_URL}/advertising/publishers/instagram/skip-jobs'
    GOLIKE_REPORT_URL = f'{GOLIKE_BASE_URL}/report/send'
    
    # ================== ANTI-BAN SETTINGS ==================
    MIN_ACTION_DELAY = float(os.getenv('MIN_ACTION_DELAY', '1.0'))
    MAX_ACTION_DELAY = float(os.getenv('MAX_ACTION_DELAY', '3.0'))
    CHECKPOINT_COOLDOWN = int(os.getenv('CHECKPOINT_COOLDOWN', '1800'))  # 30 minutes
    
    # ================== DEVELOPMENT ==================
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
    SAVE_DEBUG_RESPONSES = os.getenv('SAVE_DEBUG_RESPONSES', 'False').lower() == 'true'
    
    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith('_') and not callable(getattr(cls, key))
        }
    
    @classmethod
    def update_from_dict(cls, config_dict: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(cls, key):
                setattr(cls, key, value)
    
    @classmethod
    def get_timeout_config(cls):
        """Get timeout configuration for different operations"""
        return {
            'default': cls.REQUEST_TIMEOUT,
            'short': cls.REQUEST_TIMEOUT_SHORT,
            'complete_job': cls.REQUEST_TIMEOUT + 5,  # Longer for complete operations
        }
    
    @classmethod
    def get_retry_config(cls):
        """Get retry configuration"""
        return {
            'max_attempts': cls.MAX_RETRY_ATTEMPTS,
            'base_delay': cls.RETRY_BASE_DELAY,
            'max_delay': cls.RETRY_MAX_DELAY,
            'exponential_base': cls.RETRY_EXPONENTIAL_BASE,
        }
    
    @classmethod
    def get_rate_limit_config(cls):
        """Get rate limiting configuration"""
        return {
            'max_requests': cls.RATE_LIMIT_PER_MINUTE,
            'time_window': cls.RATE_LIMIT_WINDOW,
        }

# ================== ENVIRONMENT-SPECIFIC CONFIGS ==================

class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG_MODE = True
    LOG_LEVEL = 'DEBUG'
    SAVE_DEBUG_RESPONSES = True
    REQUEST_TIMEOUT = 30  # Longer timeout for debugging

class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG_MODE = False
    LOG_LEVEL = 'INFO'
    SAVE_DEBUG_RESPONSES = False
    MAX_RETRY_ATTEMPTS = 5  # More retries in production

class TestingConfig(Config):
    """Testing environment configuration"""
    DEBUG_MODE = True
    LOG_LEVEL = 'DEBUG'
    REQUEST_TIMEOUT = 5  # Shorter timeout for tests
    MAX_RETRY_ATTEMPTS = 1  # No retries in tests

# ================== CONFIG FACTORY ==================

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'production').lower()
    
    if env == 'development':
        return DevelopmentConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return ProductionConfig

# Default config instance
config = get_config()