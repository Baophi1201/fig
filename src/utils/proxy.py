"""
Proxy utilities
"""
import logging

logger = logging.getLogger(__name__)

def parse_proxy(proxy_string):
    """
    Parse proxy string to dict for requests
    
    Args:
        proxy_string: Format "ip:port" or "ip:port:username:password"
    
    Returns:
        dict: Proxy configuration for requests
    """
    if not proxy_string or proxy_string.strip() == '':
        return None
    
    try:
        parts = proxy_string.strip().split(':')
        if len(parts) < 2:
            logger.error(f"Invalid proxy format: {proxy_string}")
            return None
        
        ip = parts[0]
        port = parts[1]
        
        if len(parts) >= 4:
            username = parts[2]
            password = parts[3]
            proxy_url = f"http://{username}:{password}@{ip}:{port}"
        else:
            proxy_url = f"http://{ip}:{port}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    except Exception as e:
        logger.error(f"Error parsing proxy {proxy_string}: {e}")
        return None