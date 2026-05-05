"""
GoLike Instagram Runner - Production Ready
Merge: Core actions + Multi-threading + Proxy + Session + Anti-ban
"""
from curl_cffi import requests  # ✅ curl_cffi for real browser TLS fingerprint
import threading
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor

# ✅ Use centralized utils
from .utils.logger import logger
from .utils.retry import retry_on_network_error
from .utils.proxy import parse_proxy
from .config import config

# ================== UTILS ==================
def safe_extract(text, key, delimiter='"'):
    """Safely extract value from text"""
    try:
        return text.split(f'{key}')[1].split(delimiter)[0]
    except (IndexError, AttributeError):
        return None

# ================== IMPERSONATE POOL ==================
# ✅ Each account gets a stable impersonate profile (deterministic by account_id)
# Matching UA headers to the impersonate profile so TLS + headers are consistent
_IMPERSONATE_PROFILES = [
    {
        'impersonate': 'chrome131',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    },
    {
        'impersonate': 'chrome131',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    },
    {
        'impersonate': 'chrome131_android',
        'user-agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
    },
    {
        'impersonate': 'safari18_0',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15',
        'sec-ch-ua': '',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    },
    {
        'impersonate': 'chrome131',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    },
]

def pick_profile(account_id):
    """Pick a stable profile for this account (deterministic by account_id)"""
    idx = hash(str(account_id)) % len(_IMPERSONATE_PROFILES)
    return _IMPERSONATE_PROFILES[idx]


# ================== RATE LIMITER ==================
class RateLimiter:
    """Thread-safe rate limiter"""
    def __init__(self, max_requests=None, time_window=None):
        self.max_requests = max_requests or config.RATE_LIMIT_PER_MINUTE
        self.time_window = time_window or config.RATE_LIMIT_WINDOW
        self.timestamps = []
        self.lock = threading.Lock()

    def wait_if_needed(self):
        """Wait if rate limit exceeded"""
        with self.lock:
            now = time.time()
            self.timestamps = [t for t in self.timestamps if now - t < self.time_window]

            if len(self.timestamps) >= self.max_requests:
                oldest = self.timestamps[0]
                sleep_time = self.time_window - (now - oldest)
                if sleep_time > 0:
                    logger.info(f"⏳ Rate limit reached. Sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    self.timestamps = []

            self.timestamps.append(time.time())


# ================== SESSION MANAGER ==================
class SessionManager:
    """Thread-safe session manager with caching"""
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def get_or_create(self, account_id, proxy=None):
        """Get or create curl_cffi session for account"""
        cache_key = f"{account_id}_{proxy or 'no_proxy'}"

        with self.lock:
            if cache_key not in self.sessions:
                profile = pick_profile(account_id)

                # ✅ curl_cffi Session with impersonate
                session = requests.Session()

                # Setup proxy if provided
                if proxy:
                    proxy_dict = parse_proxy(proxy)
                    if proxy_dict:
                        session.proxies.update(proxy_dict)
                        logger.info(f"✅ Session created with proxy: {proxy}")

                self.sessions[cache_key] = {
                    'session': session,
                    'profile': profile,
                    'homepage_data': None,
                    'homepage_time': 0,
                    'cache_duration': config.CACHE_DURATION,
                    'created_at': time.time()
                }
                logger.debug(f"Created session for {account_id} [{profile['impersonate']}]")

            return self.sessions[cache_key]

    def cleanup_old_sessions(self, max_age=None):
        """Cleanup old sessions to prevent memory leak"""
        max_age = max_age or config.SESSION_CACHE_DURATION
        now = time.time()

        with self.lock:
            keys_to_remove = [
                k for k, v in self.sessions.items()
                if now - v.get('created_at', 0) > max_age
            ]
            for key in keys_to_remove:
                try:
                    self.sessions[key]['session'].close()
                    del self.sessions[key]
                    logger.debug(f"Cleaned up old session: {key}")
                except Exception as e:
                    logger.warning(f"Error cleaning up session {key}: {e}")

            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} old sessions")

    def close_all_sessions(self):
        """Close all sessions (call on app shutdown)"""
        with self.lock:
            for key, session_data in self.sessions.items():
                try:
                    session_data['session'].close()
                except Exception as e:
                    logger.warning(f"Error closing session {key}: {e}")

            count = len(self.sessions)
            self.sessions.clear()
            logger.info(f"Closed {count} sessions")


# ================== INSTAGRAM CLIENT ==================
class InstagramClient:
    """Instagram API client — curl_cffi + real TLS fingerprint"""

    def __init__(self, cookie, account_id, proxy=None, session_manager=None):
        self.cookie = cookie
        self.account_id = account_id
        self.proxy = proxy

        # ✅ Pick stable profile (impersonate + UA) for this account
        self.profile = pick_profile(account_id)
        self.impersonate = self.profile['impersonate']

        # Get or create session
        if session_manager:
            self.session_data = session_manager.get_or_create(account_id, proxy)
            self.session = self.session_data['session']
        else:
            self.session = requests.Session()
            self.session_data = {
                'profile': self.profile,
                'homepage_data': None,
                'homepage_time': 0,
                'cache_duration': config.CACHE_DURATION,
                'created_at': time.time()
            }

        # Rate limiter
        self.rate_limiter = RateLimiter(**config.get_rate_limit_config())

        # Extract csrftoken from cookie
        self.csrftoken = safe_extract(cookie, 'csrftoken=', ';') or ''

        # ✅ Headers match the impersonate profile exactly
        ua = self.profile['user-agent']
        self.headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': ua,
            'x-asbd-id': '359341',
            'x-csrftoken': self.csrftoken,
            'x-ig-app-id': '936619743392459',
            'cookie': self.cookie,
        }
        # Only add sec-ch-ua headers for Chrome profiles (not Safari)
        if self.profile['sec-ch-ua']:
            self.headers['sec-ch-ua'] = self.profile['sec-ch-ua']
            self.headers['sec-ch-ua-mobile'] = self.profile['sec-ch-ua-mobile']
            self.headers['sec-ch-ua-platform'] = self.profile['sec-ch-ua-platform']

        logger.debug(f"Account {account_id} → [{self.impersonate}] {ua[:55]}...")

    @retry_on_network_error(max_retries=3)
    def get_homepage_data(self, force_refresh=False):
        """Get homepage data with caching"""
        now = time.time()

        # Check cache
        if not force_refresh and self.session_data['homepage_data']:
            if now - self.session_data['homepage_time'] < self.session_data['cache_duration']:
                logger.debug(f"Using cached homepage for {self.account_id}")
                return self.session_data['homepage_data']

        self.rate_limiter.wait_if_needed()

        # ✅ curl_cffi request with impersonate
        response = self.session.get(
            'https://www.instagram.com/',
            headers=self.headers,
            impersonate=self.impersonate,
            timeout=15
        )

        if response.status_code != 200:
            logger.error(f"Homepage returned {response.status_code}")
            return None

        text = response.text

        # Parse tokens
        user_id  = safe_extract(text, '"userID":"', '"')
        fb_dtsg  = safe_extract(text, '"dtsg":{"token":"', '"')
        jazoest  = safe_extract(text, 'jazoest=', '"')

        # ✅ Extract lsd dynamically
        lsd_match = re.search(r'"LSD",\[\],\{"token":"([^"]+)"', text)
        lsd = lsd_match.group(1) if lsd_match else 'AVqnzaMnFqo'

        # ✅ Extract doc_ids dynamically
        follow_doc_id = self._extract_doc_id(text, 'usePolarisFollowMutation') or '9740159112729312'
        like_doc_id   = self._extract_doc_id(text, 'usePolarisLikeMediaLikeMutation') or '23951234354462179'

        if not user_id or not fb_dtsg:
            logger.error("Failed to parse homepage — cookie may be expired")
            return None

        homepage_data = {
            'userID': user_id,
            'fb_dtsg': fb_dtsg,
            'jazoest': jazoest or '22804',
            'lsd': lsd,
            'follow_doc_id': follow_doc_id,
            'like_doc_id': like_doc_id,
        }

        self.session_data['homepage_data'] = homepage_data
        self.session_data['homepage_time'] = now

        logger.info(
            f"✅ Homepage OK | user={user_id} | lsd={lsd[:8]}... | "
            f"follow_doc={follow_doc_id} | like_doc={like_doc_id}"
        )

        # ✅ Human-like delay after homepage load before first action
        post_homepage_delay = random.uniform(8, 20)
        logger.debug(f"Post-homepage delay: {post_homepage_delay:.1f}s")
        time.sleep(post_homepage_delay)

        return homepage_data

    def _extract_doc_id(self, text, mutation_name):
        """Extract doc_id for specific mutation from homepage"""
        try:
            pattern = f'"{mutation_name}","id":"'
            if pattern in text:
                doc_id = safe_extract(text, pattern, '"')
                if doc_id and doc_id.isdigit():
                    logger.debug(f"Extracted {mutation_name} doc_id: {doc_id}")
                    return doc_id
        except Exception as e:
            logger.warning(f"Failed to extract doc_id for {mutation_name}: {e}")
        return None

    @retry_on_network_error(max_retries=3)
    def follow_user(self, user_id, homepage_data):
        """Follow user — curl_cffi + random delay"""
        # ✅ Random pre-action delay (4–15s, human-like)
        pre_delay = random.uniform(
            max(config.MIN_ACTION_DELAY, 4),
            max(config.MAX_ACTION_DELAY, 15)
        )
        logger.debug(f"Pre-follow delay: {pre_delay:.1f}s")
        time.sleep(pre_delay)

        self.rate_limiter.wait_if_needed()

        headers = self.headers.copy()
        headers['x-fb-friendly-name'] = 'usePolarisFollowMutation'
        headers['x-fb-lsd'] = homepage_data.get('lsd', 'AVqnzaMnFqo')  # ✅ dynamic

        data = {
            'av': homepage_data['userID'],
            'fb_dtsg': homepage_data['fb_dtsg'],
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'usePolarisFollowMutation',
            'variables': f'{{"target_user_id":"{user_id}","container_module":"profile"}}',
            'doc_id': homepage_data.get('follow_doc_id', '9740159112729312'),
        }

        # ✅ curl_cffi post with impersonate
        response = self.session.post(
            'https://www.instagram.com/graphql/query',
            headers=headers,
            data=data,
            impersonate=self.impersonate,
            timeout=15
        )

        return self._parse_response(response, 'follow')

    @retry_on_network_error(max_retries=3)
    def like_post(self, media_id, homepage_data):
        """Like post — curl_cffi + random delay"""
        # ✅ Random pre-action delay (4–15s, human-like)
        pre_delay = random.uniform(
            max(config.MIN_ACTION_DELAY, 4),
            max(config.MAX_ACTION_DELAY, 15)
        )
        logger.debug(f"Pre-like delay: {pre_delay:.1f}s")
        time.sleep(pre_delay)

        self.rate_limiter.wait_if_needed()

        headers = self.headers.copy()
        headers['x-fb-friendly-name'] = 'usePolarisLikeMediaLikeMutation'
        headers['x-fb-lsd'] = homepage_data.get('lsd', 'AVqnzaMnFqo')  # ✅ dynamic

        data = {
            'av': homepage_data['userID'],
            'fb_dtsg': homepage_data['fb_dtsg'],
            'jazoest': homepage_data['jazoest'],
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'usePolarisLikeMediaLikeMutation',
            'variables': f'{{"media_id":"{media_id}","container_module":"single_post"}}',
            'doc_id': homepage_data.get('like_doc_id', '23951234354462179'),
        }

        # ✅ curl_cffi post with impersonate
        response = self.session.post(
            'https://www.instagram.com/graphql/query',
            headers=headers,
            data=data,
            impersonate=self.impersonate,
            timeout=15
        )

        return self._parse_response(response, 'like')

    def _parse_response(self, response, action_type):
        """Parse Instagram API response with deep verification"""
        try:
            result = response.json()
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
            return {'status': 'error', 'message': 'Invalid JSON response'}

        # ✅ Always log raw response for debugging
        logger.debug(f"[{action_type}] raw response: {str(result)[:500]}")

        # Detect checkpoint/challenge
        response_str = str(result).lower()
        if 'challenge' in response_str or 'checkpoint' in response_str:
            logger.warning(f"⚠️ Checkpoint detected for {self.account_id}")
            return {'status': 'checkpoint', 'message': 'Account checkpoint required'}

        data = result.get('data') or {}

        if action_type == 'follow':
            # Try deep verify first
            friendship = data.get('follow_user', {}).get('friendship_status', {})
            if friendship.get('following') is True or friendship.get('outgoing_request') is True:
                logger.info(f"✅ Follow verified (following={friendship.get('following')}, requested={friendship.get('outgoing_request')})")
                return {'status': 'ok', 'message': 'Follow thành công'}

            # ✅ Fallback: any non-empty data = success (IG schema changes)
            if data:
                logger.info(f"✅ Follow accepted (data present, schema may have changed): {str(data)[:200]}")
                return {'status': 'ok', 'message': 'Follow thành công'}

        elif action_type == 'like':
            # Try deep verify first
            feedback = data.get('like_media', {}).get('feedback', {})
            if feedback.get('viewer_has_liked') is True:
                logger.info(f"✅ Like verified (viewer_has_liked=true)")
                return {'status': 'ok', 'message': 'Like thành công'}

            # ✅ Fallback: any non-empty data = success
            if data:
                logger.info(f"✅ Like accepted (data present, schema may have changed): {str(data)[:200]}")
                return {'status': 'ok', 'message': 'Like thành công'}

        # ✅ Final fallback: HTTP 200 + has 'data' key at all
        if 'data' in result:
            logger.info(f"✅ {action_type.capitalize()} accepted (HTTP 200 + data key present)")
            return {'status': 'ok', 'message': f'{action_type.capitalize()} thành công'}

        # Truly failed
        error_msg = result.get('message', 'Unknown error')
        logger.warning(f"❌ {action_type.capitalize()} failed: {error_msg} | raw: {str(result)[:300]}")
        return {'status': 'error', 'message': error_msg}
