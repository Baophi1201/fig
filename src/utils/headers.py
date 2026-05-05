"""
Centralized headers management
"""

class Headers:
    """Centralized headers for all APIs"""
    
    @staticmethod
    def golike(authorization):
        """GoLike API headers"""
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
            'authorization': f'Bearer {authorization}',
            'content-type': 'application/json;charset=utf-8',
            'origin': 'https://app.golike.net',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            't': 'VFZSak1VNTZXVE5OVkZVMFRWRTlQUT09',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        }
    
    @staticmethod
    def instagram(cookie=None, csrftoken=None):
        """Instagram API headers"""
        headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.instagram.com',
            'referer': 'https://www.instagram.com/',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'x-asbd-id': '359341',
            'x-ig-app-id': '936619743392459',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        if cookie:
            headers['cookie'] = cookie
        
        if csrftoken:
            headers['x-csrftoken'] = csrftoken
        
        return headers