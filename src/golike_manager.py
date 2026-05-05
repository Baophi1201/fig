from datetime import datetime
from curl_cffi import requests  # ✅ Use curl_cffi for impersonate support
from .utils.headers import Headers  # ✅ Use centralized headers
from .utils.logger import logger    # ✅ Use centralized logging

class GolikeManager:
    def __init__(self, account):
        self.account = account
        logger.info("Initializing GolikeManager...")
        auth = self.account['authorization']
        self.headers = Headers.golike(auth)  # ✅ Use centralized headers
        self.session = requests.Session()    # ✅ Reuse session
    
    def get_me_account(self):
        # Lấy số coin
        get_coin = self.session.get(
            'https://gateway.golike.net/api/statistics/report',
            impersonate='safari_ios',
            headers=self.headers,
            timeout=15
        ).json()

        platform = [
            'facebook', 'instagram', 'tiktok', 'youtube', 'lazada',
            'shopee', 'linkedin', 'twitter', 'review', 'pinterest',
            'threads', 'traffic', 'snapchat'
        ]

        self.pending_coin = 0
        self.total_coin = 0

        for pf in platform:
            pf_data = get_coin.get(pf)
            if pf_data:
                self.pending_coin += pf_data.get('pending_coin', 0)
                self.total_coin += pf_data.get('hold_coin', 0)

        logger.info(f"Account coins - Pending: {self.pending_coin}, Total: {self.total_coin}")

        # Lấy thông tin account
        info_account = self.session.get(
            'https://gateway.golike.net/api/users/me',
            impersonate='safari_ios',
            headers=self.headers,
            timeout=15
        ).json()

        self.id_account = info_account['data'].get('id')
        self.email_account = info_account['data'].get('email')
        self.name_account = info_account['data'].get('name')
        self.username_account = info_account['data'].get('username')

        # Không load danh sách Instagram accounts từ API.
        # Chỉ lưu những nick mà user tự nhập cookie (xem account_service.update_instagram_cookies)

        # Ghi vào dict account
        self.account['pending_coin'] = self.pending_coin
        self.account['total_coin'] = self.total_coin
        self.account['id_account'] = self.id_account
        self.account['email_account'] = self.email_account
        self.account['name_account'] = self.name_account
        self.account['username_account'] = self.username_account
        self.account['status'] = 'ready'

        return self.account
    

# if __name__ == "__main__":
#     GolikeManager({
#         'authorization': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOlwvXC9nYXRld2F5LmdvbGlrZS5uZXRcL2FwaVwvbG9naW4iLCJpYXQiOjE3NTc0MTQyOTMsImV4cCI6MTc4ODk1MDI5MywibmJmIjoxNzU3NDE0MjkzLCJqdGkiOiJlVDBqUTl5UndmRkxyaTBaIiwic3ViIjozMDc5MDE2LCJwcnYiOiJiOTEyNzk5NzhmMTFhYTdiYzU2NzA0ODdmZmYwMWUyMjgyNTNmZTQ4In0.fp-APrTEYr2i514R06UQCXwrjvNvCnzEtG_UnjgYFt0'
#     }).get_me_account()

