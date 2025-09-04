#!/usr/bin/env python3
"""
Rate Limit Optimizer
Advanced rate limiting strategies for maximum API utilization
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import threading

logger = logging.getLogger(__name__)

class RateLimitOptimizer:
    """Advanced rate limit optimization for Twitter API v2"""
    
    def __init__(self):
        self.endpoint_windows = {}
        self.global_backoff = 0
        self.lock = threading.Lock()
        
        # Twitter API v2 rate limits (requests per 15-minute window)
        self.RATE_LIMITS = {
            'search_recent': 300,  # Search tweets
            'create_tweet': 300,   # Post tweets  
            'create_reply': 300,   # Reply to tweets
            'get_users': 300,      # Get user info
            'get_tweets': 300      # Get specific tweets
        }
        
        logger.info("⚡ Rate Limit Optimizer initialized")
    
    def can_make_request(self, endpoint: str) -> bool:
        """Check if we can make a request to the endpoint"""
        with self.lock:
            current_time = datetime.now()
            
            # Check global backoff
            if self.global_backoff > 0:
                if current_time.timestamp() < self.global_backoff:
                    return False
                else:
                    self.global_backoff = 0
            
            # Check endpoint-specific rate limit
            if endpoint not in self.endpoint_windows:
                self.endpoint_windows[endpoint] = []
            
            # Clean old requests (older than 15 minutes)
            window_start = current_time - timedelta(minutes=15)
            self.endpoint_windows[endpoint] = [
                req_time for req_time in self.endpoint_windows[endpoint]
                if req_time > window_start
            ]
            
            # Check if we're under the limit
            current_requests = len(self.endpoint_windows[endpoint])
            limit = self.RATE_LIMITS.get(endpoint, 300)
            
            if current_requests >= limit:
                logger.warning(f"⚠️ Rate limit reached for {endpoint}: {current_requests}/{limit}")
                return False
            
            return True
    
    def record_request(self, endpoint: str):
        """Record a successful request"""
        with self.lock:
            current_time = datetime.now()
            
            if endpoint not in self.endpoint_windows:
                self.endpoint_windows[endpoint] = []
            
            self.endpoint_windows[endpoint].append(current_time)
            
            # Log efficiency
            current_requests = len(self.endpoint_windows[endpoint])
            limit = self.RATE_LIMITS.get(endpoint, 300)
            efficiency = (current_requests / limit) * 100
            
            logger.debug(f"📊 {endpoint}: {current_requests}/{limit} ({efficiency:.1f}% utilization)")
    
    def handle_rate_limit_error(self, endpoint: str, reset_time: Optional[int] = None):
        """Handle rate limit errors with intelligent backoff"""
        with self.lock:
            current_time = datetime.now()
            
            if reset_time:
                # Use the actual reset time from headers
                backoff_until = reset_time
                logger.warning(f"⏱️ Rate limited on {endpoint}, backing off until {datetime.fromtimestamp(reset_time)}")
            else:
                # Default 15-minute backoff
                backoff_until = (current_time + timedelta(minutes=15)).timestamp()
                logger.warning(f"⏱️ Rate limited on {endpoint}, backing off for 15 minutes")
            
            # Set global backoff to the reset time
            self.global_backoff = max(self.global_backoff, backoff_until)
    
    def get_optimal_delay(self, endpoint: str) -> float:
        """Calculate optimal delay between requests"""
        with self.lock:
            if endpoint not in self.endpoint_windows:
                return 0.1  # Minimal delay for new endpoints
            
            current_requests = len(self.endpoint_windows[endpoint])
            limit = self.RATE_LIMITS.get(endpoint, 300)
            
            if current_requests == 0:
                return 0.1
            
            # Calculate optimal spacing for remaining requests
            remaining_requests = limit - current_requests
            remaining_time = 900  # 15 minutes in seconds
            
            if remaining_requests <= 0:
                return remaining_time  # Wait for window reset
            
            # Optimal delay to spread requests evenly
            optimal_delay = remaining_time / remaining_requests
            
            # Ensure minimum delay of 0.1 seconds
            return max(0.1, min(optimal_delay, 60))  # Cap at 1 minute
    
    def get_efficiency_stats(self) -> Dict[str, Dict]:
        """Get efficiency statistics for all endpoints"""
        with self.lock:
            stats = {}
            current_time = datetime.now()
            window_start = current_time - timedelta(minutes=15)
            
            for endpoint, requests in self.endpoint_windows.items():
                # Clean old requests
                recent_requests = [req for req in requests if req > window_start]
                limit = self.RATE_LIMITS.get(endpoint, 300)
                utilization = (len(recent_requests) / limit) * 100
                
                stats[endpoint] = {
                    'requests_in_window': len(recent_requests),
                    'limit': limit,
                    'utilization': f"{utilization:.1f}%",
                    'remaining': limit - len(recent_requests),
                    'optimal_delay': self.get_optimal_delay(endpoint)
                }
            
            return stats
    
    def optimize_request_timing(self, endpoint: str) -> bool:
        """Intelligent request timing optimization"""
        if not self.can_make_request(endpoint):
            return False
        
        # Get optimal delay and apply it
        delay = self.get_optimal_delay(endpoint)
        if delay > 0.1:
            logger.debug(f"⏱️ Applying optimal delay of {delay:.2f}s for {endpoint}")
            time.sleep(delay)
        
        return True
