#!/usr/bin/env python3
"""
Background Scheduler
Unified background service for Twitter bot and email pipeline automation
"""

import logging
import time
import signal
import sys
from typing import Optional
from datetime import datetime
import schedule
import pytz
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import get_config
from core.database import get_database
from bot.client import TwitterBotClient
from email_pipeline.pipeline import EmailPipeline

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    """Unified background scheduler for all automation tasks"""
    
    def __init__(self, config_path: Optional[str] = None, env_path: Optional[str] = None):
        """Initialize background scheduler"""
        
        # Load configuration
        self.config = get_config(env_path, config_path)
        
        # Initialize database
        self.database = get_database(
            self.config.database.url,
            self.config.database.echo,
            self.config.database.pool_size
        )
        
        # Initialize services
        self.twitter_bot = None
        self.email_pipeline = None
        
        # Scheduler state
        self.is_running = False
        self.services_enabled = {
            'twitter_bot': True,
            'email_pipeline': True
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # IST timezone for scheduling
        self.ist = pytz.timezone('Asia/Kolkata')
        
        logger.info("🤖 Background Scheduler initialized")
    
    def initialize_services(self):
        """Initialize all services"""
        
        # Initialize Twitter Bot if configured
        if self.services_enabled['twitter_bot'] and self.config.twitter.is_valid() and self.config.ai.is_valid():
            try:
                self.twitter_bot = TwitterBotClient(self.config)
                logger.info("✅ Twitter Bot service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twitter Bot: {e}")
                self.services_enabled['twitter_bot'] = False
        else:
            logger.warning("⚠️ Twitter Bot service disabled (invalid configuration)")
            self.services_enabled['twitter_bot'] = False
        
        # Initialize Email Pipeline if configured
        if self.services_enabled['email_pipeline'] and self.config.email.is_valid() and self.config.ai.is_valid():
            try:
                self.email_pipeline = EmailPipeline(self.config)
                logger.info("✅ Email Pipeline service initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Email Pipeline: {e}")
                self.services_enabled['email_pipeline'] = False
        else:
            logger.warning("⚠️ Email Pipeline service disabled (invalid configuration)")
            self.services_enabled['email_pipeline'] = False
    
    def _ist_to_utc_time(self, ist_time_str: str) -> str:
        """Convert IST time string to UTC time string for scheduling"""
        from datetime import datetime, time
        import pytz
        
        # Parse IST time
        ist_time = datetime.strptime(ist_time_str, "%H:%M").time()
        
        # Create IST datetime for today
        ist_tz = pytz.timezone('Asia/Kolkata')
        utc_tz = pytz.UTC
        
        # Create a datetime object with IST timezone
        today = datetime.now(ist_tz).date()
        ist_datetime = ist_tz.localize(datetime.combine(today, ist_time))
        
        # Convert to UTC
        utc_datetime = ist_datetime.astimezone(utc_tz)
        
        # Return UTC time string
        return utc_datetime.strftime("%H:%M")

    def setup_twitter_schedules(self):
        """Setup Twitter bot schedules"""
        if not self.services_enabled['twitter_bot']:
            return
        
        logger.info("📅 Setting up Twitter Bot schedules...")
        
        # Schedule posting times (API limit: 500 writes/month = ~16 writes/day max)
        # Optimized strategy: 6 posts/day = ~180 posts/month
        posting_times_ist = [
            "08:00", "11:00", "14:00", "17:00", "20:00", "22:00"   # 6 strategic posts (IST)
        ]
        
        # Convert IST times to UTC for scheduling
        for ist_time in posting_times_ist:
            utc_time = self._ist_to_utc_time(ist_time)
            schedule.every().day.at(utc_time).do(
                self._safe_twitter_post_task
            )
            logger.debug(f"📅 Scheduled post: {ist_time} IST → {utc_time} UTC")
        
        # Schedule engagement/reply checks (API limit: same 500 writes/month)
        # Optimized strategy: 10 replies/day = ~300 replies/month
        engagement_times_ist = [
            "07:00", "09:00", "10:00", "12:00", "13:00",   # 5 morning/day replies (IST)
            "15:00", "16:00", "18:00", "19:00", "21:00"    # 5 evening replies (IST)
        ]
        
        # Convert IST times to UTC for scheduling
        for ist_time in engagement_times_ist:
            utc_time = self._ist_to_utc_time(ist_time)
            schedule.every().day.at(utc_time).do(
                self._safe_twitter_engagement_task
            )
            logger.debug(f"📅 Scheduled engagement: {ist_time} IST → {utc_time} UTC")
        
        # Daily analytics and cleanup at 2 AM IST
        maintenance_utc = self._ist_to_utc_time("02:00")
        schedule.every().day.at(maintenance_utc).do(
            self._daily_twitter_maintenance
        )
        logger.debug(f"📅 Scheduled maintenance: 02:00 IST → {maintenance_utc} UTC")
        
        logger.info(f"📅 Scheduled {len(posting_times_ist)} daily posts and {len(engagement_times_ist)} daily replies (Optimized: 6 posts + 10 replies = 16 writes/day total)")
        logger.info("🌍 All times converted from IST to UTC for proper scheduling")
    
    def setup_email_schedules(self):
        """Setup email pipeline schedules"""
        if not self.services_enabled['email_pipeline']:
            return
        
        logger.info("📅 Setting up Email Pipeline schedules...")
        
        # Schedule hourly emails from 6 AM to 12 AM IST
        for hour in range(6, 24):
            ist_time = f"{hour:02d}:00"
            utc_time = self._ist_to_utc_time(ist_time)
            schedule.every().day.at(utc_time).do(
                self._safe_email_task
            )
            logger.debug(f"📅 Scheduled email: {ist_time} IST → {utc_time} UTC")
        
        # Also schedule for midnight (00:00 = 12 AM IST)
        midnight_utc = self._ist_to_utc_time("00:00")
        schedule.every().day.at(midnight_utc).do(
            self._safe_email_task
        )
        logger.debug(f"📅 Scheduled email: 00:00 IST → {midnight_utc} UTC")
        
        logger.info("📅 Scheduled 19 daily email suggestions (6 AM - 12 AM IST)")
        logger.info("🌍 All email times converted from IST to UTC for proper scheduling")
    
    def start(self, enable_twitter: bool = True, enable_email: bool = True):
        """Start the background scheduler"""
        
        # Configure enabled services
        self.services_enabled['twitter_bot'] = enable_twitter
        self.services_enabled['email_pipeline'] = enable_email
        
        logger.info("🚀 Starting Background Scheduler...")
        logger.info(f"📊 Services: Twitter Bot: {enable_twitter}, Email Pipeline: {enable_email}")
        logger.info(f"🤖 AI Provider: {self.config.ai.provider.value.upper()}")
        
        # Initialize services
        self.initialize_services()
        
        # Setup schedules
        if enable_twitter:
            self.setup_twitter_schedules()
        if enable_email:
            self.setup_email_schedules()
        
        # Start scheduler loop
        self.is_running = True
        
        # Send initial status email
        self._send_startup_notification()
        
        try:
            logger.info("⏰ Background scheduler started - checking every 60 seconds")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the scheduler gracefully"""
        logger.info("🛑 Stopping Background Scheduler...")
        self.is_running = False
        
        # Clear all scheduled jobs
        schedule.clear()
        
        # Close database connections
        if self.database:
            self.database.close()
        
        logger.info("✅ Background Scheduler stopped gracefully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"📡 Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def _safe_twitter_post_task(self):
        """Safe wrapper for Twitter posting task"""
        if not self.services_enabled['twitter_bot'] or not self.twitter_bot:
            return
        
        try:
            logger.info("📅 Executing scheduled Twitter post task")
            result = self.twitter_bot.create_and_post_content()
            
            if result.get('success'):
                logger.info(f"✅ Posted tweet: {result.get('tweet_id')}")
            else:
                logger.warning(f"⚠️ Post task failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Error in Twitter post task: {e}")
    
    def _safe_twitter_engagement_task(self):
        """Safe wrapper for Twitter engagement task"""
        if not self.services_enabled['twitter_bot'] or not self.twitter_bot:
            return
        
        try:
            logger.info("📅 Executing scheduled Twitter engagement task")
            result = self.twitter_bot.discover_and_engage()
            
            if result.get('success'):
                if result.get('engaged'):
                    logger.info("✅ Engagement task completed successfully")
                elif result.get('skipped_reason') == 'rate_limit_or_auth':
                    logger.info("ℹ️ Engagement skipped due to API limits - will retry later")
                else:
                    logger.debug("ℹ️ No engagement opportunities found")
            else:
                # Don't treat engagement failures as critical errors
                logger.warning(f"⚠️ Engagement task failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            # Log but don't crash the scheduler
            logger.warning(f"⚠️ Error in Twitter engagement task (non-critical): {e}")
    
    def _safe_email_task(self):
        """Safe wrapper for email task"""
        if not self.services_enabled['email_pipeline'] or not self.email_pipeline:
            return
        
        try:
            logger.info("📅 Executing scheduled email task")
            result = self.email_pipeline.send_content_email()
            
            if result:
                logger.info("✅ Email sent successfully")
            else:
                logger.warning("⚠️ Email task failed")
                
        except Exception as e:
            logger.error(f"❌ Error in email task: {e}")
    
    def _daily_twitter_maintenance(self):
        """Daily Twitter maintenance tasks"""
        if not self.services_enabled['twitter_bot']:
            return
        
        try:
            logger.info("🔧 Executing daily Twitter maintenance")
            
            # Reset daily counters
            if self.twitter_bot:
                self.twitter_bot._daily_reset()
            
            # Database cleanup, analytics, etc. would go here
            logger.info("✅ Daily Twitter maintenance completed")
            
        except Exception as e:
            logger.error(f"❌ Error in daily maintenance: {e}")
    
    def _send_startup_notification(self):
        """Send startup notification email"""
        if not self.services_enabled['email_pipeline'] or not self.email_pipeline:
            return
        
        try:
            current_time = datetime.now(self.ist).strftime('%I:%M %p IST')
            
            # Create startup notification
            startup_content = {
                'pillar': 'system',
                'content': f'🚀 Twitter Automation Platform started at {current_time} with {self.config.ai.provider.value.upper()} AI provider. All systems operational!',
                'viral_score': 8.0,
                'hashtags': ['#Automation', '#AI'],
                'suggested_time': 'Now',
                'engagement_strategy': 'System startup notification',
                'ai_model': self.config.ai.provider.value,
                'character_count': 120
            }
            
            startup_opportunities = [
                {
                    'author': '@system',
                    'content': 'Welcome to automated Twitter growth with AI-powered content generation!',
                    'engagement_score': 95,
                    'timing': 'System startup',
                    'ai_reply_suggestion': 'Thank you! Excited to leverage AI for strategic Twitter growth. 🚀'
                }
            ]
            
            success = self.email_pipeline.smtp_client.send_content_email(
                [startup_content],  # Wrap single content dict in a list
                startup_opportunities, 
                {'startup': True}
            )
            
            if success:
                logger.info("📧 Startup notification email sent")
            
        except Exception as e:
            logger.error(f"❌ Failed to send startup notification: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            'is_running': self.is_running,
            'services': self.services_enabled,
            'ai_provider': self.config.ai.provider.value,
            'scheduled_jobs': len(schedule.jobs),
            'next_run': str(schedule.next_run()) if schedule.jobs else None
        }

def main():
    """Main entry point for background scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter Automation Background Scheduler')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--env', help='Path to .env file')
    parser.add_argument('--no-twitter', action='store_true', help='Disable Twitter bot')
    parser.add_argument('--no-email', action='store_true', help='Disable email pipeline')
    parser.add_argument('--test', action='store_true', help='Run test mode (single email)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        handlers=[
            logging.FileHandler('logs/background_scheduler.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    if args.test:
        # Test mode - send single email and exit
        logger.info("🧪 Running in test mode")
        
        config = get_config(args.env, args.config)
        
        if config.email.is_valid() and config.ai.is_valid():
            email_pipeline = EmailPipeline(config)
            success = email_pipeline.send_content_email()
            
            if success:
                logger.info("✅ Test email sent successfully")
                sys.exit(0)
            else:
                logger.error("❌ Test email failed")
                sys.exit(1)
        else:
            logger.error("❌ Email or AI configuration invalid")
            sys.exit(1)
    else:
        # Production mode
        scheduler = BackgroundScheduler(args.config, args.env)
        scheduler.start(
            enable_twitter=not args.no_twitter,
            enable_email=not args.no_email
        )

if __name__ == '__main__':
    main()
