from curl_cffi import requests
import json
import time
from .utils.headers import Headers
from .utils.retry import request_with_retry
from .utils.logger import logger
from .config import config

class Get_golike:
    def __init__(self, authorization, id_account):
        self.authorization = authorization
        self.id_account = id_account
        self.session = requests.Session()  # ✅ Reuse connection
        self.headers = Headers.golike(authorization)  # ✅ Centralized headers
    
    def _request_with_retry(self, func, retries=3, delay=2):
        """✅ Use centralized retry"""
        return request_with_retry(func, retries, delay)
    def get_instagram(self):
        params = {
            'instagram_account_id': self.id_account,
            'data': 'null',
        }
        
        try:
            # ✅ Retry + Timeout (configurable)
            r = self._request_with_retry(
                lambda: self.session.get(
                    config.GOLIKE_JOBS_URL,
                    impersonate='safari_ios',
                    params=params,
                    headers=self.headers,
                    timeout=config.REQUEST_TIMEOUT
                )
            )
            
            # ✅ Check rate limit
            if r.status_code == 429:
                logger.warning("⚠️ Rate limit detected! Waiting 30s...")
                time.sleep(30)
                return {'status': 400}
            
            # ✅ Safe JSON parse
            try:
                response = r.json()
            except Exception as e:
                logger.error(f"❌ Invalid JSON response: {r.text[:100]} - {e}")
                return {'status': 400}
            
            # ✅ Detect rate limit in response
            if isinstance(response, dict):
                message = str(response.get('message', '')).lower()
                if 'too many' in message or 'rate limit' in message:
                    logger.warning(f"⚠️ Rate limit in response: {response.get('message')}")
                    time.sleep(30)
                    return {'status': 400}
            
        except Exception as e:
            logger.error(f"❌ Error calling API: {e}")
            return {'status': 400}
        
        try:
            # ✅ Validate response structure
            if not isinstance(response, dict):
                logger.error(f"❌ Response is not a dict: {type(response)}")
                return {'status': 400}
            
            if 'data' not in response:
                logger.error(f"❌ Response missing 'data' key: {response}")
                return {'status': 400}
            
            data = response['data']
            
            # ✅ Validate data structure
            if not isinstance(data, dict):
                # GoLike trả về list rỗng [] khi hết job - đây là bình thường
                if isinstance(data, list) and len(data) == 0:
                    logger.warning(f"⚠️ No jobs available (empty list returned)")
                else:
                    logger.error(f"❌ Data is not a dict: {type(data)} - value: {str(data)[:100]}")
                return {'status': 400}
            
            # ✅ Validate required fields
            if 'id' not in data:
                logger.error(f"❌ Data missing 'id' field")
                return {'status': 400}
            
            # ✅ Validate job type
            job_type = data.get('type', '')
            if job_type not in ['follow', 'like', 'comment']:
                logger.warning(f"⚠️ Unknown job type: {job_type}")
                # Không return 400, để caller xử lý
            
            job_id = data['id']
            
            # Tìm uid từ object_data
            uid = None
            users_advertising_id = job_id
            
            # Parse object_data để lấy uid
            if 'object_data' in data and data['object_data']:
                try:
                    if isinstance(data['object_data'], str):
                        object_data = json.loads(data['object_data'])
                    else:
                        object_data = data['object_data']
                    
                    # uid có thể là pk, id, user_id, owner_id
                    if isinstance(object_data, dict):
                        uid = (object_data.get('pk') or 
                               object_data.get('id') or 
                               object_data.get('user_id') or
                               object_data.get('owner_id') or
                               object_data.get('user', {}).get('pk') if isinstance(object_data.get('user'), dict) else None)
                except Exception as e:
                    logger.warning(f"⚠️ Cannot parse object_data: {e}")
            
            # Fallback: thử subscribers
            if not uid and 'subscribers' in data and data['subscribers']:
                try:
                    if isinstance(data['subscribers'], str):
                        subscribers = json.loads(data['subscribers'])
                    else:
                        subscribers = data['subscribers']
                    
                    if isinstance(subscribers, dict):
                        uid = subscribers.get('pk') or subscribers.get('id')
                except Exception as e:
                    logger.warning(f"⚠️ Cannot parse subscribers: {e}")
            
            # Fallback cuối: dùng object_id
            if not uid:
                uid = data.get('object_id')
            
            return {
                "id_nv": job_id,
                "package_name": data.get('package_name', ''),
                "object_id": data.get('object_id', ''),
                "link": data.get('link', ''),
                "type": job_type,
                "price_after_cost": data.get('price_after_cost', 0),
                "uid": str(uid) if uid else None,
                "users_fb_account_id": self.id_account,
                "users_advertising_id": users_advertising_id,
                "status": 200
            }
        except Exception as e:
            logger.error(f"❌ Error parsing job response: {e}")
            return {'status': 400}
    def skip_job(self, id_nv, id_account, object_id, type, platform='instagram'):
        json_data = {
            'description': 'Tôi không muốn làm Job này',
            'users_advertising_id': id_nv,
            'type': 'ads',
            'provider': platform,
            'fb_id': id_account,
            'error_type': 0,
        }
        
        # ✅ Retry report
        try:
            self._request_with_retry(
                lambda: self.session.post(
                    'https://gateway.golike.net/api/report/send',
                    impersonate='safari_ios',
                    headers=self.headers,
                    json=json_data,
                    timeout=10
                ),
                retries=2
            )
        except Exception as e:
            logger.warning(f"⚠️ Report failed: {e}")

        json_data = {
            'ads_id': id_nv,
            'object_id': object_id,
            'account_id': id_account,
            'type': type,
        }

        # ✅ Retry skip
        try:
            r = self._request_with_retry(
                lambda: self.session.post(
                    'https://gateway.golike.net/api/advertising/publishers/instagram/skip-jobs',
                    impersonate='safari_ios',
                    headers=self.headers,
                    json=json_data,
                    timeout=10
                ),
                retries=2
            )
            
            try:
                response = r.json()
                return response.get('skip', False)
            except Exception as e:
                logger.error(f"Skip job JSON parse error: {e}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Skip job failed: {e}")
            return False
    def complete_job(self, id_nv, id_account, object_id=None, job_type=None, uid=None, users_fb_account_id=None, users_advertising_id=None):
        """
        🔥 QUAN TRỌNG NHẤT - Complete job với retry mạnh mẽ
        
        Args:
            id_nv: Job ID
            id_account: Instagram account ID
            object_id: Object ID (user_id hoặc media_id)
            job_type: Loại job ('follow', 'like', 'comment')
            uid: UID từ response get_instagram
            users_fb_account_id: users_fb_account_id từ response
            users_advertising_id: users_advertising_id từ response
        """
        
        # ✅ RETRY COMPLETE JOB 3 LẦN (QUAN TRỌNG - LIÊN QUAN TIỀN!)
        for attempt in range(3):
            if attempt > 0:
                logger.info(f"🔄 Retry complete job attempt {attempt + 1}/3...")
                time.sleep(2 * attempt)  # Exponential backoff
            
            # 1️⃣ Thử API cũ trước (ổn định hơn)
            json_data_old = {
                'instagram_users_advertising_id': id_nv,
                'instagram_account_id': id_account,
                'async': True,
                'data': None,
            }

            try:
                r = self._request_with_retry(
                    lambda: self.session.post(
                        'https://gateway.golike.net/api/advertising/publishers/instagram/complete-jobs',
                        impersonate='safari_ios',
                        headers=self.headers,
                        json=json_data_old,
                        timeout=15  # ✅ Timeout dài hơn cho complete
                    ),
                    retries=2
                )
                
                # ✅ Safe JSON parse
                try:
                    response = r.json()
                except Exception as e:
                    logger.warning(f"⚠️ Old API invalid JSON: {r.text[:100]} - {e}")
                    response = {}
                
                # ✅ Verify success mạnh mẽ hơn
                if response.get('success') == True:
                    # Double check: có data không?
                    if 'data' in response or response.get('status') == 200:
                        logger.info(f"✅ Old API complete success!")
                        return True
                    else:
                        logger.warning(f"⚠️ Old API success but no data: {response}")
                else:
                    logger.warning(f"⚠️ Old API failed: {response.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Old API error: {e}")
            
            # 2️⃣ Thử API mới (2026)
            if object_id and job_type:
                json_data = {
                    'object_id': str(object_id),
                    'job_id': id_nv,
                    'type': job_type,
                    'uid': uid,
                    'users_fb_account_id': users_fb_account_id,
                    'users_advertising_id': users_advertising_id,
                    'message': None,
                    'retry': True
                }
                
                try:
                    r = self._request_with_retry(
                        lambda: self.session.post(
                            'https://gateway.golike.net/api/advertising/publishers/complete-jobs-2026',
                            impersonate='safari_ios',
                            headers=self.headers,
                            json=json_data,
                            timeout=15
                        ),
                        retries=2
                    )
                    
                    # ✅ Safe JSON parse
                    try:
                        response = r.json()
                    except Exception as e:
                        logger.warning(f"⚠️ New API invalid JSON: {r.text[:100]} - {e}")
                        response = {}
                    
                    # ✅ Verify success mạnh mẽ hơn
                    if response.get('success') == True or response.get('status') == 200:
                        # Double check: có data không?
                        if 'data' in response or response.get('success') == True:
                            logger.info(f"✅ New API complete success!")
                            return True
                        else:
                            logger.warning(f"⚠️ New API success but no data: {response}")
                    else:
                        logger.warning(f"⚠️ New API failed: {response.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ New API error: {e}")
        
        # 3️⃣ Cả 2 API đều thất bại sau 3 lần retry
        logger.error(f"❌ Complete job failed after 3 attempts")
        return False
    
    def report_complete_error(self, object_id, job_id, job_type, uid=None, users_advertising_id=None):
        """
        Báo lỗi khi complete job thất bại hoặc timeout
        (Hiện tại không dùng - giữ lại để dùng sau nếu cần)
        
        Args:
            object_id: Object ID (user_id hoặc media_id)
            job_id: Job ID
            job_type: Loại job ('follow', 'like', 'comment')
            uid: UID từ response get_instagram
            users_advertising_id: users_advertising_id từ response
        """
        json_data = {
            'object_id': str(object_id),
            'job_id': job_id,
            'type': job_type,
            'uid': str(uid) if uid else None,
            'users_advertising_id': users_advertising_id,
            'message': None,
            'retry': True
        }
        
        try:
            r = requests.post(
                'https://gateway.golike.net/api/advertising/publishers/report-complete-error',
                impersonate='safari_ios',
                headers=self.headers,
                json=json_data,
                timeout=10
            )
            
            if r.status_code == 200:
                return True
            else:
                return False
                
        except Exception as e:
            return False
# from golike_manager import GolikeManager
