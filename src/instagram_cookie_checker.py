"""
Instagram Cookie Checker
Kiểm tra tính hợp lệ của Instagram cookies
✅ Dùng curl_cffi để TLS fingerprint khớp với runner (tránh mismatch checkpoint)
"""
from curl_cffi import requests  # ✅ Same TLS stack as instagram_runner
import re
from datetime import datetime
from .utils.proxy import parse_proxy
from .utils.headers import Headers
from .utils.logger import logger


class InstagramCookieChecker:
    def __init__(self, cookie, proxy=None):
        self.cookie = cookie
        self.proxy = proxy
        # ✅ curl_cffi Session — same fingerprint as runner
        self.session = requests.Session()
        self.headers = Headers.instagram(cookie=cookie)
        self.username = None
        self.status = 'unknown'

    def parse_cookie(self):
        """Parse cookie string thành dict"""
        cookie_dict = {}
        try:
            for item in self.cookie.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    cookie_dict[key.strip()] = value.strip()
            return cookie_dict
        except Exception as e:
            logger.error(f"Error parsing cookie: {e}")
            return {}

    def check_user(self):
        """
        Kiểm tra cookie bằng cách truy cập Instagram homepage.
        Dùng curl_cffi impersonate='chrome131' để TLS khớp với runner.
        """
        try:
            # Parse và set cookies vào session
            cookie_dict = self.parse_cookie()
            if not cookie_dict:
                return {
                    'success': False,
                    'status': 'die',
                    'username': None,
                    'message': 'Cookie không hợp lệ hoặc rỗng',
                    'checked_at': datetime.now().isoformat()
                }

            for key, value in cookie_dict.items():
                self.session.cookies.set(key, value, domain='.instagram.com')

            # Setup proxy nếu có
            proxies = parse_proxy(self.proxy)

            # ✅ curl_cffi GET với impersonate chrome — khớp TLS với runner
            response = self.session.get(
                'https://www.instagram.com/',
                headers=self.headers,
                proxies=proxies or {},
                impersonate='chrome131',
                timeout=15,
                allow_redirects=True
            )

            logger.info(f"Cookie check status: {response.status_code}")

            if response.status_code == 200:
                response_text = response.text

                # ✅ Parse username bằng regex (bền hơn split)
                username_patterns = [
                    r'"username":"([^"]+)"',
                    r'"user":\s*\{[^}]*"username":"([^"]+)"',
                    r'window\._sharedData[^}]*"username":"([^"]+)"',
                ]

                username_found = None
                for pattern in username_patterns:
                    match = re.search(pattern, response_text)
                    if match:
                        username_found = match.group(1)
                        break

                if username_found:
                    self.username = username_found
                    self.status = 'live'
                    logger.info(f"✅ Cookie LIVE — @{self.username}")
                    return {
                        'success': True,
                        'status': 'live',
                        'username': self.username,
                        'message': f'Cookie LIVE — @{self.username}',
                        'checked_at': datetime.now().isoformat()
                    }

                # Không tìm thấy username — check redirect/challenge
                response_lower = response.url.lower() + ' ' + response_text[:2000].lower()
                die_indicators = ['login', 'challenge', 'checkpoint', 'two_factor', 'suspicious_login']

                if any(ind in response_lower for ind in die_indicators):
                    msg = 'Cookie DIE — Yêu cầu đăng nhập lại hoặc challenge'
                else:
                    msg = 'Cookie DIE — Không tìm thấy username'

                self.status = 'die'
                logger.warning(f"❌ {msg}")
                return {
                    'success': True,
                    'status': 'die',
                    'username': None,
                    'message': msg,
                    'checked_at': datetime.now().isoformat()
                }

            elif response.status_code in [301, 302]:
                self.status = 'die'
                return {
                    'success': True,
                    'status': 'die',
                    'username': None,
                    'message': f'Cookie DIE — Redirect đến {response.url}',
                    'checked_at': datetime.now().isoformat()
                }

            else:
                self.status = 'die'
                return {
                    'success': True,
                    'status': 'die',
                    'username': None,
                    'message': f'Cookie DIE — HTTP {response.status_code}',
                    'checked_at': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error checking cookie: {e}")
            # Phân loại lỗi để caller xử lý đúng
            msg = str(e)
            if 'timeout' in msg.lower() or 'timed out' in msg.lower():
                msg = 'Timeout — Không thể kết nối Instagram'
            elif 'proxy' in msg.lower():
                msg = 'Lỗi Proxy — Không thể kết nối qua proxy'
            return {
                'success': False,
                'status': 'error',
                'username': None,
                'message': msg,
                'checked_at': datetime.now().isoformat()
            }
