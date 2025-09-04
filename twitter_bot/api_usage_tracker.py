#!/usr/bin/env python3
"""
Twitter API Usage Tracker
Monitors API usage to stay within free tier limits
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class APIUsageTracker:
    """Track Twitter API usage for free tier compliance"""
    
    def __init__(self, usage_file: str = "api_usage.json"):
        self.usage_file = Path(usage_file)
        self.usage_data = self._load_usage_data()
        
        # Twitter API v2 Free Tier Limits (CORRECTED)
        # Based on user clarification:
        # - 100 posts can be RETRIEVED per month (read operations)
        # - 500 posts/replies can be WRITTEN per month (write operations)
        self.MONTHLY_READ_LIMIT = 100   # Read/retrieve posts per month
        self.MONTHLY_WRITE_LIMIT = 500  # Write/post per month
        self.DAILY_READ_LIMIT = 3       # ~3 reads/day (conservative)
        self.DAILY_WRITE_LIMIT = 16     # 6 posts + 10 replies = 16 writes/day
        
        logger.info("📊 API Usage Tracker initialized")
    
    def _load_usage_data(self) -> Dict[str, Any]:
        """Load existing usage data"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load usage data: {e}")
        
        # Initialize new usage data
        return {
            "current_month": datetime.now().strftime("%Y-%m"),
            "posts_this_month": 0,
            "reads_this_month": 0,
            "daily_posts": {},
            "daily_reads": {},
            "last_reset": datetime.now().isoformat(),
            "rate_limit_reset_times": {},
            "consecutive_errors": 0
        }
    
    def _save_usage_data(self):
        """Save usage data to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def _check_month_rollover(self):
        """Check if we need to reset monthly counters"""
        current_month = datetime.now().strftime("%Y-%m")
        
        if self.usage_data.get("current_month") != current_month:
            logger.info(f"📅 Month rollover detected: {self.usage_data.get('current_month')} -> {current_month}")
            
            # Reset monthly counters
            self.usage_data["current_month"] = current_month
            self.usage_data["posts_this_month"] = 0
            self.usage_data["reads_this_month"] = 0
            self.usage_data["daily_posts"] = {}
            self.usage_data["daily_reads"] = {}
            self.usage_data["last_reset"] = datetime.now().isoformat()
            self.usage_data["consecutive_errors"] = 0
            
            self._save_usage_data()
    
    def can_post(self) -> bool:
        """Check if we can make a post within limits"""
        self._check_month_rollover()
        
        current_posts = self.usage_data.get("posts_this_month", 0)
        remaining = self.MONTHLY_WRITE_LIMIT - current_posts
        
        if remaining <= 0:
            logger.warning(f"⚠️ Monthly write limit reached: {current_posts}/{self.MONTHLY_WRITE_LIMIT}")
            return False
        
        # Check daily limit (conservative: max 16 writes per day)
        today = datetime.now().strftime("%Y-%m-%d")
        daily_posts = self.usage_data.get("daily_posts", {}).get(today, 0)
        
        if daily_posts >= self.DAILY_WRITE_LIMIT:
            logger.warning(f"⚠️ Daily write limit reached: {daily_posts}/{self.DAILY_WRITE_LIMIT}")
            return False
        
        return True
    
    def can_read(self) -> bool:
        """Check if we can make a read request within limits"""
        self._check_month_rollover()
        
        current_reads = self.usage_data.get("reads_this_month", 0)
        remaining = self.MONTHLY_READ_LIMIT - current_reads
        
        if remaining <= 0:
            logger.warning(f"⚠️ Monthly read limit reached: {current_reads}/{self.MONTHLY_READ_LIMIT}")
            return False
        
        # Check daily limit (conservative: max 3 reads per day)
        today = datetime.now().strftime("%Y-%m-%d")
        daily_reads = self.usage_data.get("daily_reads", {}).get(today, 0)
        
        if daily_reads >= self.DAILY_READ_LIMIT:
            logger.warning(f"⚠️ Daily read limit reached: {daily_reads}/{self.DAILY_READ_LIMIT}")
            return False
        
        return True
    
    def can_engage(self) -> bool:
        """Check if we can make an engagement (write) within limits"""
        # Engagement is also a write operation, so use the same limits as posting
        return self.can_post()
    
    def record_post(self):
        """Record a successful post"""
        self._check_month_rollover()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Update monthly counter
        self.usage_data["posts_this_month"] = self.usage_data.get("posts_this_month", 0) + 1
        
        # Update daily counter
        if "daily_posts" not in self.usage_data:
            self.usage_data["daily_posts"] = {}
        
        self.usage_data["daily_posts"][today] = self.usage_data["daily_posts"].get(today, 0) + 1
        
        self._save_usage_data()
        
        logger.info(f"📊 Post recorded: {self.usage_data['posts_this_month']}/{self.MONTHLY_WRITE_LIMIT} monthly, {self.usage_data['daily_posts'][today]}/{self.DAILY_WRITE_LIMIT} daily")
    
    def record_read(self):
        """Record a successful read operation"""
        self._check_month_rollover()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Update monthly counter
        self.usage_data["reads_this_month"] = self.usage_data.get("reads_this_month", 0) + 1
        
        # Update daily counter
        if "daily_reads" not in self.usage_data:
            self.usage_data["daily_reads"] = {}
        
        self.usage_data["daily_reads"][today] = self.usage_data["daily_reads"].get(today, 0) + 1
        
        self._save_usage_data()
        
        logger.info(f"📊 Read recorded: {self.usage_data['reads_this_month']}/{self.MONTHLY_READ_LIMIT} monthly, {self.usage_data['daily_reads'][today]}/{self.DAILY_READ_LIMIT} daily")
    
    def record_write(self):
        """Record a successful write (engagement) - same as post"""
        # Engagements are counted as posts since they're both write operations
        self.record_post()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        self._check_month_rollover()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "monthly_usage": {
                "writes": f"{self.usage_data.get('posts_this_month', 0)}/{self.MONTHLY_WRITE_LIMIT}",
                "reads": f"{self.usage_data.get('reads_this_month', 0)}/{self.MONTHLY_READ_LIMIT}",
                "writes_remaining": self.MONTHLY_WRITE_LIMIT - self.usage_data.get('posts_this_month', 0),
                "reads_remaining": self.MONTHLY_READ_LIMIT - self.usage_data.get('reads_this_month', 0)
            },
            "daily_usage": {
                "writes": f"{self.usage_data.get('daily_posts', {}).get(today, 0)}/{self.DAILY_WRITE_LIMIT}",
                "reads": f"{self.usage_data.get('daily_reads', {}).get(today, 0)}/{self.DAILY_READ_LIMIT}"
            },
            "limits_status": {
                "can_post": self.can_post(),
                "can_read": self.can_read(),
                "can_engage": self.can_engage()
            },
            "efficiency_metrics": {
                "monthly_write_utilization": f"{(self.usage_data.get('posts_this_month', 0) / self.MONTHLY_WRITE_LIMIT * 100):.1f}%",
                "monthly_read_utilization": f"{(self.usage_data.get('reads_this_month', 0) / self.MONTHLY_READ_LIMIT * 100):.1f}%"
            }
        }
