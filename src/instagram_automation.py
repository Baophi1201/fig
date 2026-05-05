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
        
        # Exhausted accounts tracking
        self.exhausted_ig_accounts = set()
        
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
        
        # Cleanup sessions
        try:
            self.session_manager.close_all_sessions()
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
        
        logger.info("🛑 Graceful shutdown completed")
    
    def run_instagram_account(self, account_ig, data_account, account_mission_count, account_earnings_dict):
        """Run missions for 1 Instagram account"""
        if not self.is_running:
            return
            
        if account_ig['id_account_golike'] in self.exhausted_ig_accounts:
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
            with self.stats_lock:
                self.exhausted_ig_accounts.add(account_ig['id_account_golike'])
            logger.warning(f"⚠️ Cannot load homepage for @{account_ig['username']} - Skipped")
            return
        
        # Run missions
        for i in range(self.switch_account):
            if not self.is_running:
                break
            
            with self.stats_lock:
                if account_ig['id_account_golike'] in self.exhausted_ig_accounts:
                    break
            
            try:
                # Get job from GoLike
                mission_golike = Get_golike(data_account['authorization'], account_ig['id_account_golike']).get_instagram()
                
                if not self.is_running:
                    break
                
                if int(mission_golike['status']) == 400:
                    with self.stats_lock:
                        self.exhausted_ig_accounts.add(account_ig['id_account_golike'])
                    logger.warning(f"⚠️ @{account_ig['username']} out of jobs")
                    break
                
                # Execute mission
                if mission_golike['type'] == 'follow':
                    result = client.follow_user(mission_golike['object_id'], homepage_data)
                elif mission_golike['type'] == 'like':
                    result = client.like_post(mission_golike['object_id'], homepage_data)
                elif mission_golike['type'] == 'comment':
                    # Skip comment jobs
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
                
                # Check result
                if result.get('status') == 'ok':
                    # Wait before completing (configurable)
                    time.sleep(config.COMPLETE_JOB_DELAY)
                    
                    if not self.is_running:
                        break
                    
                    # Complete job
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
                        # Skip failed job
                        Get_golike(data_account['authorization'], account_ig['id_account_golike']).skip_job(
                            mission_golike['id_nv'], account_ig['id_account_golike'], 
                            mission_golike['object_id'], mission_golike['type']
                        )
                        logger.warning("❌ Complete job failed - Skipped")
                elif result.get('status') == 'checkpoint':
                    with self.stats_lock:
                        self.exhausted_ig_accounts.add(account_ig['id_account_golike'])
                    logger.warning(f"⚠️ Checkpoint detected for @{account_ig['username']}")
                    break
                else:
                    logger.warning(f"⚠️ Action failed: {result}")
                
                # ✅ Delay giữa từng job (interruptible)
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
        
        # Delay after finishing all jobs for this account
        if self.is_running and account_mission_count['count'] < self.stop_account:
            delay_remaining = self.delay
            while delay_remaining > 0 and self.is_running:
                sleep_time = min(0.5, delay_remaining)
                time.sleep(sleep_time)
                delay_remaining -= sleep_time
    
    def run_mission(self, data_account):
        """Run missions for one GoLike account with multi-threading"""
        logger.info(f"🚀 Starting GoLike: {data_account['name_account']} - {len(data_account['instagram_accounts'])} IG accounts")
        
        # Shared variables for threads
        account_mission_count = {'count': 0}
        account_earnings_dict = {'total': 0}
        
        while account_mission_count['count'] < self.stop_account and self.is_running:
            if not self.is_running:
                break
            
            # Check if all accounts exhausted
            active_ig_accounts = [
                ig for ig in data_account['instagram_accounts']
                if ig['id_account_golike'] not in self.exhausted_ig_accounts
            ]
            
            if not active_ig_accounts:
                logger.info(f"🚫 All IG accounts exhausted for {data_account['username_account']}")
                break
            
            # Run threads for Instagram accounts
            ig_threads = []
            for account_ig in active_ig_accounts:
                if not self.is_running:
                    break
                
                if account_ig['id_account_golike'] in self.exhausted_ig_accounts:
                    continue
                
                t = threading.Thread(
                    target=self.run_instagram_account,
                    args=(account_ig, data_account, account_mission_count, account_earnings_dict)
                )
                t.start()
                ig_threads.append(t)
                
                # Delay between threads (configurable)
                if self.is_running and len(active_ig_accounts) > 1:
                    time.sleep(config.THREAD_DELAY)
            
            # Wait for all threads to complete
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