"""
Runner Service - Handle automation execution
"""
import json
import os
import random
from ..instagram_automation import InstagramAutomation
from ..utils.logger import logger

class RunnerService:
    """Service for managing automation execution"""
    
    def __init__(self, config_file='data/config.json'):
        self.config_file = config_file
        self.config = {
            'jobs_per_account_min': 5,
            'jobs_per_account_max': 10,
            'total_jobs_target': 50,
            'delay_between_jobs_min': 2,
            'delay_between_jobs_max': 5,
        }
        self.load_config()
    
    def load_config(self):
        """Load runner configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    logger.info("Loaded runner configuration")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save runner configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            logger.info("Saved runner configuration")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get_config(self):
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, new_config):
        """Update configuration"""
        self.config.update(new_config)
        return self.save_config()
    
    def prepare_automation_data(self, selected_accounts, live_cookies):
        """Prepare data for InstagramAutomation"""
        # ✅ Use randomization for better anti-ban
        switch_account = random.randint(self.config['jobs_per_account_min'], self.config['jobs_per_account_max'])
        delay = random.randint(self.config['delay_between_jobs_min'], self.config['delay_between_jobs_max'])
        
        golike_data = {
            'golike_accounts': [],
            'stop_account': self.config['total_jobs_target'],
            'delay': delay,  # ✅ Random delay
            'taskType': ['follow', 'like'],
            'switch_account': switch_account,  # ✅ Random switch count
            'threadCountCookie': 1,
        }
        
        # Add selected accounts with cookies
        for acc in selected_accounts:
            # Get IG accounts with LIVE cookies
            ig_accounts_with_cookie = []
            for ig in acc.get('instagram_accounts', []):
                ig_username = ig.get('instagram_username', '').lower()
                
                # Find corresponding cookie
                for live_item in live_cookies:
                    if live_item['username'].lower() == ig_username:
                        ig_accounts_with_cookie.append({
                            'id': ig.get('id_account_golike'),
                            'id_account_golike': ig.get('id_account_golike'),
                            'username': ig.get('instagram_username'),
                            'cookie': live_item['cookie'],
                            'proxy': None,  # No proxy support yet
                            'status': 'active'
                        })
                        break
            
            if ig_accounts_with_cookie:
                golike_data['golike_accounts'].append({
                    'authorization': acc.get('authorization'),
                    'name_account': acc.get('name_account'),
                    'username_account': acc.get('username_account'),
                    'instagram_accounts': ig_accounts_with_cookie
                })
        
        return golike_data
    
    def run_automation(self, automation_data):
        """Run the automation"""
        try:
            runner = InstagramAutomation(automation_data)
            
            logger.info("🚀 Starting automation...")
            
            # Run automation
            runner.thread()
            
            # Get results
            results = {
                'success': True,
                'total_missions': runner.total_missions_completed,
                'total_earnings': runner.total_earnings,
                'message': 'Automation completed successfully'
            }
            
            logger.info(f"✅ Automation completed: {results['total_missions']} jobs, {results['total_earnings']}đ")
            return results
            
        except KeyboardInterrupt:
            logger.warning("🛑 Automation stopped by user")
            runner.stop()
            return {
                'success': False,
                'total_missions': runner.total_missions_completed,
                'total_earnings': runner.total_earnings,
                'message': f'Stopped by user at {runner.total_missions_completed} jobs'
            }
            
        except Exception as e:
            logger.error(f"❌ Automation error: {e}")
            return {
                'success': False,
                'total_missions': 0,
                'total_earnings': 0,
                'message': f'Error: {str(e)}'
            }
    
    def get_automation_summary(self, selected_accounts, live_cookies):
        """Get automation summary before running"""
        total_ig = sum(len(acc['instagram_accounts']) for acc in selected_accounts)
        
        return {
            'config': self.config,
            'accounts': {
                'golike_count': len(selected_accounts),
                'instagram_count': total_ig,
                'live_cookies': len(live_cookies)
            },
            'estimated': {
                'jobs_per_account': f"{self.config['jobs_per_account_min']}-{self.config['jobs_per_account_max']}",
                'total_target': self.config['total_jobs_target'],
                'delay_range': f"{self.config['delay_between_jobs_min']}-{self.config['delay_between_jobs_max']}s"
            }
        }