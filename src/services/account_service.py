"""
Account Service - Handle GoLike account management
"""
import json
import os
from datetime import datetime
from ..golike_manager import GolikeManager
from ..utils.logger import logger

class AccountService:
    """Service for managing GoLike accounts"""
    
    def __init__(self, data_file='data/manager-golike.json'):
        self.data_file = data_file
        self.accounts = []
        self.load_accounts()
    
    def load_accounts(self):
        """Load accounts from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = data if isinstance(data, list) else []
                    logger.info(f"Loaded {len(self.accounts)} accounts")
        except Exception as e:
            logger.error(f"Error loading accounts: {e}")
            self.accounts = []
    
    def save_accounts(self):
        """Save accounts to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved {len(self.accounts)} accounts")
            return True
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
            return False
    
    def add_account(self, authorization):
        """Add new GoLike account"""
        try:
            # Validate authorization format
            authorization = authorization.strip()
            if authorization.lower().startswith('bearer '):
                authorization = authorization[7:].strip()
            
            if not authorization.startswith('eyJ'):
                return {
                    'success': False,
                    'message': 'Authorization token không hợp lệ! (Phải bắt đầu bằng "eyJ")'
                }
            
            # Create account object
            account_data = {
                'authorization': authorization,
                'instagram_accounts': []
            }
            
            # Get account info from GoLike API
            manager = GolikeManager(account_data)
            account_info = manager.get_me_account()
            
            # Check if account already exists
            existing = next((acc for acc in self.accounts if acc.get('id_account') == account_info.get('id_account')), None)
            
            if existing:
                return {
                    'success': False,
                    'message': f'Tài khoản {account_info.get("username_account")} đã tồn tại!'
                }
            
            # Add to accounts list
            self.accounts.append(account_info)
            
            # Save to file
            if self.save_accounts():
                return {
                    'success': True,
                    'message': f'Đã thêm tài khoản: {account_info.get("username_account")}',
                    'account': account_info
                }
            else:
                return {
                    'success': False,
                    'message': 'Không thể lưu tài khoản!'
                }
                
        except Exception as e:
            logger.error(f"Error adding account: {e}")
            return {
                'success': False,
                'message': f'Lỗi khi kiểm tra tài khoản: {str(e)}'
            }
    
    def get_accounts(self):
        """Get all accounts"""
        return self.accounts
    
    def get_account_by_index(self, index):
        """Get account by index (1-based)"""
        try:
            return self.accounts[index - 1]
        except IndexError:
            return None
    
    def get_stats(self):
        """Get account statistics"""
        total_ig = sum(len(acc.get('instagram_accounts', [])) for acc in self.accounts)
        total_coins = sum(acc.get('total_coin', 0) for acc in self.accounts)
        pending_coins = sum(acc.get('pending_coin', 0) for acc in self.accounts)
        
        return {
            'total_accounts': len(self.accounts),
            'active_accounts': sum(1 for acc in self.accounts if acc.get('status') == 'ready'),
            'total_instagram_accounts': total_ig,
            'total_coins': total_coins,
            'pending_coins': pending_coins
        }
    
    def update_instagram_cookies(self, account_indices, live_cookies):
        """
        Lưu cookie Instagram vào tài khoản GoLike.
        - Nếu nick chưa có trong list → thêm mới
        - Nếu nick đã có → cập nhật cookie
        Chỉ lưu những nick user tự nhập, không load từ API GoLike.
        """
        try:
            if account_indices == 'all':
                selected_accounts = self.accounts
            else:
                selected_accounts = [self.get_account_by_index(int(account_indices))]

            for acc in selected_accounts:
                ig_list = acc.setdefault('instagram_accounts', [])

                # Build lookup: instagram_username (lower) → index trong list
                existing_map = {
                    ig.get('instagram_username', '').lower(): i
                    for i, ig in enumerate(ig_list)
                }

                for live_item in live_cookies:
                    username_lower = live_item['username'].lower()

                    if username_lower in existing_map:
                        # Cập nhật cookie nick đã có
                        idx = existing_map[username_lower]
                        ig_list[idx]['cookie'] = live_item['cookie']
                        ig_list[idx]['status'] = 'active'
                        ig_list[idx]['last_check'] = live_item.get('checked_at')
                        logger.info(f"Updated cookie for {live_item['username']}")
                    else:
                        # Thêm nick mới (user nhập lần đầu)
                        # Lấy id_account_golike từ API GoLike nếu cần
                        ig_id_golike = live_item.get('id_account_golike') or self._fetch_ig_id(
                            acc.get('authorization'), live_item['username']
                        )
                        new_ig = {
                            'id': live_item.get('ig_id', ''),
                            'golike_account_id': acc.get('id_account'),
                            'golike_username': acc.get('username_account'),
                            'id_account_golike': ig_id_golike,
                            'instagram_username': live_item['username'],
                            'status': 'active',
                            'created_at': datetime.utcnow().isoformat() + 'Z',
                            'last_check': live_item.get('checked_at'),
                            'cookie': live_item['cookie'],
                        }
                        ig_list.append(new_ig)
                        existing_map[username_lower] = len(ig_list) - 1
                        logger.info(f"Added new IG account: {live_item['username']}")

            return self.save_accounts()

        except Exception as e:
            logger.error(f"Error updating cookies: {e}")
            return False

    def _fetch_ig_id(self, authorization, ig_username):
        """
        Lấy id_account_golike của nick Instagram từ API GoLike.
        Trả về None nếu không tìm thấy hoặc lỗi.
        """
        try:
            from ..golike_manager import GolikeManager
            from curl_cffi import requests as cffi_requests
            from .utils.headers import Headers

            headers = Headers.golike(authorization)
            session = cffi_requests.Session()
            resp = session.get(
                'https://gateway.golike.net/api/instagram-account',
                impersonate='safari_ios',
                headers=headers,
                timeout=10
            ).json()

            for ig in resp.get('data', []):
                if ig.get('instagram_username', '').lower() == ig_username.lower():
                    return ig.get('id')
        except Exception as e:
            logger.warning(f"Cannot fetch ig_id for {ig_username}: {e}")
        return None