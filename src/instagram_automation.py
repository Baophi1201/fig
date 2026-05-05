"""
Instagram Automation - Production Ready
Wrapper around instagram_runner.py for multi-threading
"""
import threading
import time
import random
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from .instagram_runner import InstagramClient, SessionManager, RateLimiter
from .mission_golike import Get_golike
from .utils.logger import logger
from .config import config

# Thời gian chờ trước khi thử lại nick đã hết job (giây)
NO_JOB_RETRY_WAIT = 60   # chờ 60s rồi thử lại nick đó
NO_JOB_MAX_RETRIES = 3   # tối đa 3 lần retry toàn bộ vòng lặp khi tất cả nick hết job


class InstagramAutomation:
    """Production-ready Instagram automation with multi-threading"""

    def __init__(self, data):
        self.data = data
        self.stop_account = self.data['stop_account']
        self.delay = self.data['delay']
        self.taskType = self.data['taskType']
        self.switch_account = self.data['switch_account']
        self.threadCountCookie = self.data.get('threadCountCookie', 1)
        self.is_running = True

        self.total_missions_completed = 0
        self.total_earnings = 0

        # Session manager (thread-safe)
        self.session_manager = SessionManager()

        # Exhausted accounts tracking: {id_account_golike: timestamp_exhausted}
        # - Giá trị bình thường: timestamp khi hết job → retry sau NO_JOB_RETRY_WAIT giây
        # - Giá trị rất lớn (+ 1 năm): nick chết hẳn (checkpoint/cookie lỗi) → không retry
        self.exhausted_ig_accounts = {}

        # Thread-safe locks
        self.stats_lock = threading.Lock()

        # ✅ Setup graceful shutdown
        self._setup_signal_handlers()

        logger.info(f"🚀 Instagram Automation initialized with {len(self.data['golike_accounts'])} accounts")

    def _setup_signal_handlers(self):
        """✅ Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    def stop(self):
        """Stop all runners with cleanup"""
        self.is_running = False
        logger.info("🛑 Stop signal received - Cleaning up...")

        try:
            self.session_manager.close_all_sessions()
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

        logger.info("🛑 Graceful shutdown completed")

    def _is_exhausted(self, account_id):
        """
        Kiểm tra nick có đang trong trạng thái hết job không.
        Tự động xóa khỏi danh sách nếu đã hết thời gian chờ.
        """
        with self.stats_lock:
            if account_id not in self.exhausted_ig_accounts:
                return False
            elapsed = time.time() - self.exhausted_ig_accounts[account_id]
            if elapsed >= NO_JOB_RETRY_WAIT:
                # Hết thời gian chờ → cho phép thử lại
                del self.exhausted_ig_accounts[account_id]
                return False
            return True

    def _is_dead(self, account_id):
        """Nick chết hẳn (checkpoint/cookie lỗi) - không bao giờ retry"""
        with self.stats_lock:
            if account_id not in self.exhausted_ig_accounts:
                return False
            elapsed = time.time() - self.exhausted_ig_accounts[account_id]
            return elapsed >= 86400 * 30  # đánh dấu dead = timestamp + 30 ngày

    def _mark_exhausted(self, account_id, username):
        """Đánh dấu nick hết job tạm thời, sẽ retry sau NO_JOB_RETRY_WAIT giây"""
        with self.stats_lock:
            self.exhausted_ig_accounts[account_id] = time.time()
        logger.warning(f"⚠️ @{username} hết job → chờ {NO_JOB_RETRY_WAIT}s rồi thử lại")

    def _mark_dead(self, account_id, username=""):
        """Đánh dấu nick chết hẳn (checkpoint/cookie lỗi) - không retry"""
        with self.stats_lock:
            # timestamp rất xa trong tương lai → _is_exhausted sẽ không bao giờ xóa
            self.exhausted_ig_accounts[account_id] = time.time() + 86400 * 365
        if username:
            logger.warning(f"🚫 @{username} bị đánh dấu dead - không retry")

    def run_instagram_account(self, account_ig, data_account, account_mission_count, account_earnings_dict):
        """Run missions for 1 Instagram account"""
        if not self.is_running:
            return

        if self._is_exhausted(account_ig['id_account_golike']):
            return

        # Create Instagram client
        proxy_string = account_ig.get('proxy', None)
        client = InstagramClient(
            cookie=account_ig['cookie'],
            account_id=account_ig['id_account_golike'],
            proxy=proxy_string,
            session_manager=self.session_manager
        )

        # Get homepage data
        homepage_data = client.get_homepage_data()
        if not homepage_data:
            self._mark_dead(account_ig['id_account_golike'], account_ig['username'])
            logger.warning(f"⚠️ Cannot load homepage for @{account_ig['username']} - cookie lỗi, bỏ qua")
            return

        # Run missions
        for i in range(self.switch_account):
            if not self.is_running:
                break

            if self._is_exhausted(account_ig['id_account_golike']):
                break

            try:
                # Get job from GoLike
                mission_golike = Get_golike(data_account['authorization'], account_ig['id_account_golike']).get_instagram()

                if not self.is_running:
                    break

                if int(mission_golike['status']) == 400:
                    # Hết job → đánh dấu tạm thời, sẽ retry sau
                    self._mark_exhausted(account_ig['id_account_golike'], account_ig['username'])
                    break

                # Execute mission
                if mission_golike['type'] == 'follow':
                    result = client.follow_user(mission_golike['object_id'], homepage_data)
                elif mission_golike['type'] == 'like':
                    result = client.like_post(mission_golike['object_id'], homepage_data)
                elif mission_golike['type'] == 'comment':
                    Get_golike(data_account['authorization'], account_ig['id_account_golike']).skip_job(
                        mission_golike['id_nv'], account_ig['id_account_golike'],
                        mission_golike['object_id'], mission_golike['type']
                    )
                    logger.info("⏭️ Skipped comment job (not supported)")
                    continue
                else:
                    logger.warning(f"⚠️ Unknown job type: {mission_golike['type']}")
                    continue

                if not self.is_running:
                    break

                if result.get('status') == 'stopped':
                    break

                if result.get('status') == 'ok':
                    time.sleep(config.COMPLETE_JOB_DELAY)

                    if not self.is_running:
                        break

                    status_complete = Get_golike(data_account['authorization'], account_ig['id_account_golike']).complete_job(
                        id_nv=mission_golike['id_nv'],
                        id_account=account_ig['id_account_golike'],
                        object_id=mission_golike['object_id'],
                        job_type=mission_golike['type'],
                        uid=mission_golike.get('uid'),
                        users_fb_account_id=mission_golike.get('users_fb_account_id'),
                        users_advertising_id=mission_golike.get('users_advertising_id')
                    )

                    if not self.is_running:
                        break

                    if status_complete:
                        mission_earning = int(mission_golike['price_after_cost'])

                        with self.stats_lock:
                            account_earnings_dict['total'] += mission_earning
                            account_mission_count['count'] += 1
                            self.total_missions_completed += 1
                            self.total_earnings += mission_earning

                        logger.info(f"✅ #{account_mission_count['count']} - {mission_golike['type']} 💰 +{mission_earning}đ | Total: {self.total_earnings}đ")
                    else:
                        Get_golike(data_account['authorization'], account_ig['id_account_golike']).skip_job(
                            mission_golike['id_nv'], account_ig['id_account_golike'],
                            mission_golike['object_id'], mission_golike['type']
                        )
                        logger.warning("❌ Complete job failed - Skipped")

                elif result.get('status') == 'checkpoint':
                    self._mark_dead(account_ig['id_account_golike'], account_ig['username'])
                    logger.warning(f"⚠️ Checkpoint detected for @{account_ig['username']} - Disabled permanently")
                    break
                else:
                    logger.warning(f"⚠️ Action failed: {result}")

                # Delay giữa từng job (interruptible)
                if self.is_running and self.delay > 0:
                    logger.info(f"⏳ Chờ {self.delay}s trước job tiếp theo...")
                    delay_remaining = self.delay
                    while delay_remaining > 0 and self.is_running:
                        time.sleep(min(0.5, delay_remaining))
                        delay_remaining -= 0.5

            except Exception as e:
                if not self.is_running:
                    break
                logger.error(f"💥 Error processing job: {e}")
                continue

        # Delay sau khi xong tất cả job của nick này
        if self.is_running and account_mission_count['count'] < self.stop_account:
            delay_remaining = self.delay
            while delay_remaining > 0 and self.is_running:
                time.sleep(min(0.5, delay_remaining))
                delay_remaining -= 0.5

    def run_mission(self, data_account):
        """Run missions for one GoLike account with multi-threading"""
        logger.info(f"🚀 Starting GoLike: {data_account['name_account']} - {len(data_account['instagram_accounts'])} IG accounts")

        account_mission_count = {'count': 0}
        account_earnings_dict = {'total': 0}
        no_job_rounds = 0  # số vòng liên tiếp tất cả nick đều hết job

        while account_mission_count['count'] < self.stop_account and self.is_running:
            if not self.is_running:
                break

            all_ig = data_account['instagram_accounts']

            # Nick dead hẳn (checkpoint/cookie lỗi)
            dead_ids = {
                ig['id_account_golike'] for ig in all_ig
                if self._is_dead(ig['id_account_golike'])
            }

            # Nick có thể retry (chưa dead)
            retryable = [ig for ig in all_ig if ig['id_account_golike'] not in dead_ids]

            if not retryable:
                logger.warning(f"🚫 Tất cả nick IG đã chết (checkpoint/cookie lỗi) - Dừng hẳn")
                break

            # Nick đang active (không bị exhausted hoặc đã hết thời gian chờ)
            active_ig_accounts = [
                ig for ig in retryable
                if not self._is_exhausted(ig['id_account_golike'])
            ]

            if not active_ig_accounts:
                # Tất cả nick đang trong thời gian chờ retry
                no_job_rounds += 1
                if no_job_rounds > NO_JOB_MAX_RETRIES:
                    logger.warning(
                        f"🚫 Đã thử lại {NO_JOB_MAX_RETRIES} lần nhưng vẫn không có job - Dừng"
                    )
                    break

                # Tính thời gian chờ của nick sẽ sẵn sàng sớm nhất
                wait_times = []
                for ig in retryable:
                    ig_id = ig['id_account_golike']
                    with self.stats_lock:
                        ts = self.exhausted_ig_accounts.get(ig_id)
                    if ts:
                        remaining = max(0, NO_JOB_RETRY_WAIT - (time.time() - ts))
                        wait_times.append((remaining, ig['username']))

                if wait_times:
                    wait_times.sort()
                    min_wait, next_nick = wait_times[0]
                    logger.info(
                        f"⏳ Tất cả nick đang hết job (lần {no_job_rounds}/{NO_JOB_MAX_RETRIES}). "
                        f"Chờ {min_wait:.0f}s → thử lại @{next_nick}..."
                    )
                    waited = 0
                    while waited < min_wait and self.is_running:
                        time.sleep(min(5, min_wait - waited))
                        waited += 5
                else:
                    logger.info(f"⏳ Chờ {NO_JOB_RETRY_WAIT}s rồi thử lại...")
                    waited = 0
                    while waited < NO_JOB_RETRY_WAIT and self.is_running:
                        time.sleep(5)
                        waited += 5

                continue  # Quay lại đầu vòng lặp

            # Có nick active → reset bộ đếm
            no_job_rounds = 0

            # Chạy thread cho từng nick active
            ig_threads = []
            for account_ig in active_ig_accounts:
                if not self.is_running:
                    break

                if self._is_exhausted(account_ig['id_account_golike']):
                    continue

                t = threading.Thread(
                    target=self.run_instagram_account,
                    args=(account_ig, data_account, account_mission_count, account_earnings_dict)
                )
                t.start()
                ig_threads.append(t)

                if self.is_running and len(active_ig_accounts) > 1:
                    time.sleep(config.THREAD_DELAY)

            for t in ig_threads:
                t.join()

        if self.is_running:
            logger.info(f"🏁 Completed {account_mission_count['count']} jobs - {data_account['username_account']}")
            logger.info(f"💎 Account earnings: {account_earnings_dict['total']}đ")
        else:
            logger.info(f"⏹️ Stopped {data_account['username_account']} at job #{account_mission_count['count']}")

    def thread(self):
        """Main thread function - run all GoLike accounts"""
        scan_threads = []
        self.total_missions_completed = 0
        self.total_earnings = 0

        logger.info(f"🎯 Starting automation with {len(self.data['golike_accounts'])} GoLike accounts")

        for golike_account in self.data['golike_accounts']:
            if not self.is_running:
                break
            t = threading.Thread(target=self.run_mission, args=(golike_account,))
            t.start()
            scan_threads.append(t)

        for t in scan_threads:
            t.join()

        if self.is_running:
            logger.info(f"🎉 Automation completed!")
            logger.info(f"📈 Total: {self.total_missions_completed} jobs - {self.total_earnings}đ")
        else:
            logger.info(f"🛑 Automation stopped by user!")
