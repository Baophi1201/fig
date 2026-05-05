"""
Cookie Service - Handle Instagram cookie validation
"""
import time
from datetime import datetime
from ..instagram_cookie_checker import InstagramCookieChecker
from ..utils.logger import logger

class CookieService:
    """Service for managing Instagram cookies"""
    
    def __init__(self):
        pass
    
    def parse_cookie_input(self, lines):
        """Parse multi-line cookie input"""
        valid_cookies = []
        invalid_lines = []
        
        for idx, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            if '|' not in line:
                invalid_lines.append((idx, line, "Thiếu dấu '|'"))
                continue
            
            parts = line.split('|', 1)
            if len(parts) != 2:
                invalid_lines.append((idx, line, "Format không đúng"))
                continue
            
            username, cookie = parts[0].strip(), parts[1].strip()
            
            if not username or not cookie:
                invalid_lines.append((idx, line, "Username hoặc cookie trống"))
                continue
            
            valid_cookies.append({
                'username': username,
                'cookie': cookie,
                'line_number': idx
            })
        
        return valid_cookies, invalid_lines
    
    def validate_cookies_for_account(self, valid_cookies, selected_accounts):
        """
        Trước đây validate nick phải có trong danh sách GoLike.
        Giờ chấp nhận tất cả nick user nhập — không cần load list từ API.
        Trả về toàn bộ valid_cookies, không có invalid.
        """
        return valid_cookies, []
    
    def check_cookies(self, validated_cookies):
        """Check cookie validity (LIVE/DIE)"""
        live_cookies = []
        die_cookies = []
        error_cookies = []
        
        total = len(validated_cookies)
        
        for idx, item in enumerate(validated_cookies, 1):
            username = item['username']
            cookie = item['cookie']
            
            logger.info(f"[{idx}/{total}] Checking {username}...")
            
            try:
                checker = InstagramCookieChecker(cookie, proxy=None)
                result = checker.check_user()
                
                if result.get('status') == 'live':
                    live_cookies.append({
                        'username': username,
                        'cookie': cookie,
                        'ig_username': result.get('username'),
                        'checked_at': result.get('checked_at')
                    })
                    logger.info(f"  ✅ LIVE - {result.get('username')}")
                    
                elif result.get('status') == 'die':
                    die_cookies.append({
                        'username': username,
                        'reason': result.get('message')
                    })
                    logger.warning(f"  ❌ DIE - {result.get('message')}")
                    
                else:
                    error_cookies.append({
                        'username': username,
                        'reason': result.get('message')
                    })
                    logger.error(f"  ⚠️ ERROR - {result.get('message')}")
                
                # Delay between checks
                if idx < total:
                    time.sleep(1)
                    
            except Exception as e:
                error_cookies.append({
                    'username': username,
                    'reason': str(e)
                })
                logger.error(f"  ❌ ERROR - {str(e)}")
        
        return {
            'live': live_cookies,
            'die': die_cookies,
            'error': error_cookies,
            'summary': {
                'live_count': len(live_cookies),
                'die_count': len(die_cookies),
                'error_count': len(error_cookies),
                'total_count': total
            }
        }
    
    def get_saved_cookies(self, selected_accounts):
        """Get saved cookies from selected accounts"""
        existing_cookies = []
        
        # Get Instagram usernames from selected accounts
        selected_ig_usernames = set()
        for acc in selected_accounts:
            for ig in acc.get('instagram_accounts', []):
                selected_ig_usernames.add(ig.get('instagram_username', '').lower())
        
        # Get cookies from selected accounts only
        for acc in selected_accounts:
            for ig in acc.get('instagram_accounts', []):
                ig_username = ig.get('instagram_username', '').lower()
                
                # Check: has cookie AND belongs to this account
                if (ig.get('cookie') and 
                    ig.get('status') == 'active' and 
                    ig_username in selected_ig_usernames):
                    
                    existing_cookies.append({
                        'username': ig.get('instagram_username'),
                        'cookie': ig.get('cookie'),
                        'last_check': ig.get('last_check')
                    })
        
        return existing_cookies