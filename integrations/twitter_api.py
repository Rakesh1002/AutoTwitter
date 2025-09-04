#!/usr/bin/env python3
"""
Twitter API Integration
Handles all Twitter API interactions with proper error handling and rate limiting
"""

import logging
import tweepy
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
import time
from .twitter_oauth import (
    TwitterOAuth,
    TokenStorage,
    get_oauth_config_from_env,
)
import requests

logger = logging.getLogger(__name__)

class TwitterAPI:
    """Twitter API client with error handling and rate limiting"""
    
    def __init__(self, twitter_config):
        """Initialize Twitter API client - supports OAuth 2.0 and OAuth 1.0a"""
        self.config = twitter_config
        
        if not self.config.is_valid():
            raise ValueError("Invalid Twitter API configuration")
        
        # OAuth token management helpers (used for OAuth 2.0 user context)
        self.user_id = getattr(self.config, 'oauth_user_id', None) or "oauth_user"
        self.token_storage = TokenStorage()
        oauth_env = get_oauth_config_from_env()
        self.oauth_helper = TwitterOAuth(
            client_id=oauth_env.get('client_id', ''),
            client_secret=oauth_env.get('client_secret', ''),
            callback_url=oauth_env.get('callback_url', 'http://localhost:8000/auth/twitter/callback')
        )
        self._tokens: Optional[Dict[str, Any]] = None
        
        # Initialize Tweepy client - prefer OAuth 2.0 for write permissions
        if self.config.has_oauth2():
            # For OAuth 2.0 Authorization Code Flow with PKCE (User Context)
            # Pass access token as the first positional argument per Tweepy docs
            # Prefer stored tokens; refresh if needed
            tokens = self._load_or_refresh_tokens()
            access_token = (tokens or {}).get('access_token') or self.config.oauth_access_token
            # Keep a Tweepy client for read/search endpoints (works with bearer token)
            self.client = tweepy.Client(bearer_token=access_token, wait_on_rate_limit=False)
            # Keep current tokens in memory for refresh attempts
            self._tokens = tokens or {
                'access_token': access_token,
                'refresh_token': self.config.oauth_refresh_token or None
            }
            self.auth_type = "OAuth 2.0 User Context"
            logger.info("🔐 Using OAuth 2.0 Authorization Code Flow with PKCE for Twitter API")
        else:
            # Fallback to legacy OAuth 1.0a authentication
            self.client = tweepy.Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                wait_on_rate_limit=False
            )
            self.auth_type = "OAuth 1.0a"
            logger.info("🔐 Using OAuth 1.0a authentication for Twitter API")
        
        # Rate limiting state
        self.last_post_time = None
        self.last_search_time = None
        self.min_post_interval = 3600  # 1 hour between posts
        self.min_search_interval = 60   # 1 minute between searches
        
        logger.info("🐦 Twitter API client initialized")
    
    def _check_rate_limit_headers(self, response):
        """Monitor rate limit headers for optimization"""
        if hasattr(response, 'headers'):
            headers = response.headers
            
            # Extract rate limit information
            limit = headers.get('x-rate-limit-limit')
            remaining = headers.get('x-rate-limit-remaining') 
            reset = headers.get('x-rate-limit-reset')
            
            if all([limit, remaining, reset]):
                logger.info(f"📊 Rate limits: {remaining}/{limit} remaining, resets at {reset}")
                
                # Warn if getting close to limits
                remaining_int = int(remaining)
                limit_int = int(limit)
                
                if remaining_int < limit_int * 0.1:  # Less than 10% remaining
                    logger.warning(f"⚠️ Rate limit warning: Only {remaining_int} requests remaining")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def post_tweet(self, content: str, **kwargs) -> Optional[str]:
        """Post a tweet with retry logic"""
        
        try:
            # Ensure valid OAuth2 token/client before posting
            if self.auth_type == "OAuth 2.0 User Context":
                # Use direct HTTP for OAuth2 user-context posting to avoid OAuth1 fallback in Tweepy
                tweet_id = self._http_post_tweet(content, **kwargs)
                if tweet_id:
                    self.last_post_time = time.time()
                    logger.info(f"✅ Tweet posted successfully: {tweet_id}")
                    return tweet_id
                return None
            
            # Rate limiting check
            if not self._check_post_rate_limit():
                logger.warning("Post rate limit check failed")
                return None
            
            # Validate content
            if not content or len(content) > 280:
                logger.error(f"Invalid tweet content length: {len(content) if content else 0}")
                return None
            
            # Post tweet (OAuth1 flow only)
            response = self.client.create_tweet(text=content, **kwargs)
            
            if response.data:
                tweet_id = response.data['id']
                self.last_post_time = time.time()
                
                logger.info(f"✅ Tweet posted successfully: {tweet_id}")
                return tweet_id
            else:
                logger.error("Tweet post failed - no response data")
                return None
                
        except tweepy.errors.Unauthorized as e:
            # Attempt one refresh on unauthorized (likely expired token)
            logger.warning(f"Unauthorized when posting tweet: {e}. Attempting token refresh...")
            if self._attempt_refresh_and_rebuild_client():
                try:
                    if self.auth_type == "OAuth 2.0 User Context":
                        tweet_id = self._http_post_tweet(content, **kwargs)
                        if tweet_id:
                            self.last_post_time = time.time()
                            logger.info(f"✅ Tweet posted successfully after refresh: {tweet_id}")
                            return tweet_id
                    else:
                        response = self.client.create_tweet(text=content, **kwargs)
                        if response.data:
                            tweet_id = response.data['id']
                            self.last_post_time = time.time()
                            logger.info(f"✅ Tweet posted successfully after refresh: {tweet_id}")
                            return tweet_id
                except Exception as retry_err:
                    logger.error(f"Retry after refresh failed: {retry_err}")
            return None
        except tweepy.errors.TooManyRequests:
            logger.warning("Twitter rate limit exceeded")
            raise
        except tweepy.errors.Forbidden as e:
            logger.error(f"Twitter API forbidden: {e}")
            return None
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    def reply_to_tweet(self, tweet_id: str, content: str) -> Optional[str]:
        """Reply to a specific tweet"""
        
        try:
            # Ensure valid OAuth2 token/client before replying
            if self.auth_type == "OAuth 2.0 User Context":
                reply_id = self._http_reply_to_tweet(tweet_id, content)
                if reply_id:
                    self.last_post_time = time.time()
                    logger.info(f"✅ Reply posted successfully: {reply_id}")
                    return reply_id
                return None
            
            # Rate limiting check
            if not self._check_post_rate_limit():
                logger.warning("Reply rate limit check failed")
                return None
            
            # Validate content
            if not content or len(content) > 280:
                logger.error(f"Invalid reply content length: {len(content) if content else 0}")
                return None
            
            # Post reply (OAuth1 flow only)
            response = self.client.create_tweet(
                text=content,
                in_reply_to_tweet_id=tweet_id
            )
            
            if response.data:
                reply_id = response.data['id']
                self.last_post_time = time.time()
                
                logger.info(f"✅ Reply posted successfully: {reply_id}")
                return reply_id
            else:
                logger.error("Reply post failed - no response data")
                return None
                
        except tweepy.errors.Unauthorized as e:
            logger.warning(f"Unauthorized when replying: {e}. Attempting token refresh...")
            if self._attempt_refresh_and_rebuild_client():
                try:
                    if self.auth_type == "OAuth 2.0 User Context":
                        reply_id = self._http_reply_to_tweet(tweet_id, content)
                        if reply_id:
                            self.last_post_time = time.time()
                            logger.info(f"✅ Reply posted successfully after refresh: {reply_id}")
                            return reply_id
                    else:
                        response = self.client.create_tweet(
                            text=content,
                            in_reply_to_tweet_id=tweet_id
                        )
                        if response.data:
                            reply_id = response.data['id']
                            self.last_post_time = time.time()
                            logger.info(f"✅ Reply posted successfully after refresh: {reply_id}")
                            return reply_id
                except Exception as retry_err:
                    logger.error(f"Retry after refresh failed: {retry_err}")
            return None
        except Exception as e:
            logger.error(f"Error posting reply: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5)
    )
    def search_tweets(self, 
                     query: str, 
                     max_results: int = 10,
                     exclude_replies: bool = True,
                     exclude_retweets: bool = True) -> List[Dict[str, Any]]:
        """Search for tweets"""
        
        try:
            # Rate limiting check
            if not self._check_search_rate_limit():
                logger.warning("Search rate limit check failed")
                return []
            
            # Build query
            search_query = query
            if exclude_replies:
                search_query += " -is:reply"
            if exclude_retweets:
                search_query += " -is:retweet"
            
            # Search tweets
            response = self.client.search_recent_tweets(
                query=search_query,
                max_results=min(max_results, 100),  # API limit is 100
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                user_fields=['username', 'name', 'verified'],
                expansions=['author_id']
            )
            
            self.last_search_time = time.time()
            
            if not response.data:
                logger.info(f"No tweets found for query: {query}")
                return []
            
            # Process results
            tweets = []
            users_dict = {}
            
            # Create user lookup
            if response.includes and 'users' in response.includes:
                users_dict = {user.id: user for user in response.includes['users']}
            
            for tweet in response.data:
                author = users_dict.get(tweet.author_id, {})
                
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'author': {
                        'id': tweet.author_id,
                        'username': getattr(author, 'username', 'unknown'),
                        'name': getattr(author, 'name', 'Unknown'),
                        'verified': getattr(author, 'verified', False)
                    },
                    'public_metrics': tweet.public_metrics or {},
                    'context_annotations': tweet.context_annotations or []
                }
                tweets.append(tweet_data)
            
            logger.info(f"✅ Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except tweepy.errors.TooManyRequests:
            logger.warning("Search rate limit exceeded")
            return []
        except Exception as e:
            logger.error(f"Error searching tweets: {e}")
            return []
    
    def get_tweet(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific tweet by ID"""
        
        try:
            response = self.client.get_tweet(
                tweet_id,
                tweet_fields=['created_at', 'author_id', 'public_metrics'],
                user_fields=['username', 'name', 'verified'],
                expansions=['author_id']
            )
            
            if not response.data:
                logger.warning(f"Tweet not found: {tweet_id}")
                return None
            
            tweet = response.data
            author = None
            
            if response.includes and 'users' in response.includes:
                author = response.includes['users'][0]
            
            tweet_data = {
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                'author': {
                    'id': tweet.author_id,
                    'username': getattr(author, 'username', 'unknown'),
                    'name': getattr(author, 'name', 'Unknown'),
                    'verified': getattr(author, 'verified', False)
                } if author else None,
                'public_metrics': tweet.public_metrics or {}
            }
            
            return tweet_data
            
        except Exception as e:
            logger.error(f"Error getting tweet {tweet_id}: {e}")
            return None
    
    def get_user_tweets(self, 
                       username: str, 
                       max_results: int = 10) -> List[Dict[str, Any]]:
        """Get recent tweets from a specific user"""
        
        try:
            # Get user ID first
            user = self.client.get_user(username=username)
            if not user.data:
                logger.warning(f"User not found: {username}")
                return []
            
            user_id = user.data.id
            
            # Get user tweets
            response = self.client.get_users_tweets(
                user_id,
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'public_metrics'],
                exclude=['retweets', 'replies']
            )
            
            if not response.data:
                logger.info(f"No tweets found for user: {username}")
                return []
            
            tweets = []
            for tweet in response.data:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'author': {
                        'id': user_id,
                        'username': username,
                        'name': user.data.name,
                        'verified': getattr(user.data, 'verified', False)
                    },
                    'public_metrics': tweet.public_metrics or {}
                }
                tweets.append(tweet_data)
            
            logger.info(f"✅ Found {len(tweets)} tweets for user: {username}")
            return tweets
            
        except Exception as e:
            logger.error(f"Error getting tweets for user {username}: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check Twitter API connectivity and permissions"""
        
        try:
            if self.auth_type == "OAuth 2.0 User Context":
                # Use direct HTTP call for user info with OAuth2 user token
                headers = self._oauth2_headers()
                resp = requests.get("https://api.twitter.com/2/users/me", headers=headers, timeout=15)
                if resp.status_code == 401 and self._attempt_refresh_and_rebuild_client():
                    headers = self._oauth2_headers()
                    resp = requests.get("https://api.twitter.com/2/users/me", headers=headers, timeout=15)
                if resp.ok:
                    data = resp.json().get('data') or {}
                    return {
                        'status': 'healthy',
                        'user_id': data.get('id'),
                        'username': data.get('username'),
                        'name': data.get('name'),
                        'permissions': 'read_write'
                    }
                if resp.status_code == 403:
                    return {
                        'status': 'limited',
                        'error': 'Insufficient permissions - check app permissions',
                        'permissions': 'read_only'
                    }
                return {
                    'status': 'unhealthy',
                    'error': f"HTTP {resp.status_code}: {resp.text[:200]}"
                }
            else:
                # OAuth1 path via Tweepy
                user = self.client.get_me()
                if user.data:
                    return {
                        'status': 'healthy',
                        'user_id': user.data.id,
                        'username': user.data.username,
                        'name': user.data.name,
                        'permissions': 'read_write'
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'error': 'Authentication failed'
                    }
        except tweepy.errors.Forbidden:
            return {
                'status': 'limited',
                'error': 'Insufficient permissions - check app permissions',
                'permissions': 'read_only'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def _check_post_rate_limit(self) -> bool:
        """Check if we can make a post request"""
        
        if self.last_post_time is None:
            return True
        
        time_since_last = time.time() - self.last_post_time
        return time_since_last >= self.min_post_interval
    
    def _check_search_rate_limit(self) -> bool:
        """Check if we can make a search request"""
        
        if self.last_search_time is None:
            return True
        
        time_since_last = time.time() - self.last_search_time
        return time_since_last >= self.min_search_interval
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        
        current_time = time.time()
        
        post_remaining_time = 0
        if self.last_post_time:
            elapsed = current_time - self.last_post_time
            post_remaining_time = max(0, self.min_post_interval - elapsed)
        
        search_remaining_time = 0
        if self.last_search_time:
            elapsed = current_time - self.last_search_time
            search_remaining_time = max(0, self.min_search_interval - elapsed)
        
        return {
            'can_post': post_remaining_time == 0,
            'can_search': search_remaining_time == 0,
            'post_wait_seconds': post_remaining_time,
            'search_wait_seconds': search_remaining_time,
            'last_post_time': self.last_post_time,
            'last_search_time': self.last_search_time
        }

    # ---------------------------------------------------------------------
    # Internal helpers: OAuth2 token management
    # ---------------------------------------------------------------------
    def _load_or_refresh_tokens(self) -> Optional[Dict[str, Any]]:
        """Load tokens from storage; refresh if near expiry. Fallback to env."""
        try:
            stored = self.token_storage.load_tokens(self.user_id)
            if stored:
                if self.oauth_helper.validate_tokens(stored):
                    return stored
                # Try refresh if we have a refresh token
                if stored.get('refresh_token'):
                    refreshed = self.oauth_helper.refresh_access_token(stored['refresh_token'])
                    # Keep refresh token if not rotated
                    if 'refresh_token' not in refreshed and stored.get('refresh_token'):
                        refreshed['refresh_token'] = stored['refresh_token']
                    self.token_storage.save_tokens(self.user_id, refreshed)
                    return refreshed
        except Exception as e:
            logger.warning(f"Token load/refresh from storage failed: {e}")

        # Fallback to environment tokens
        if getattr(self.config, 'oauth_access_token', None):
            tokens: Dict[str, Any] = {
                'access_token': self.config.oauth_access_token
            }
            if getattr(self.config, 'oauth_refresh_token', None):
                tokens['refresh_token'] = self.config.oauth_refresh_token
            return tokens
        
        return None

    def _ensure_valid_client(self) -> None:
        """Ensure the OAuth2 client is using a valid access token."""
        if not self._tokens:
            return
        try:
            if not self.oauth_helper.validate_tokens(self._tokens):
                if self._attempt_refresh_and_rebuild_client():
                    logger.info("🔄 Refreshed access token before request")
        except Exception as e:
            logger.debug(f"Token validation error (continuing): {e}")

    def _attempt_refresh_and_rebuild_client(self) -> bool:
        """Attempt to refresh access token and rebuild Tweepy client."""
        try:
            refresh_token = None
            if self._tokens and self._tokens.get('refresh_token'):
                refresh_token = self._tokens['refresh_token']
            elif getattr(self.config, 'oauth_refresh_token', None):
                refresh_token = self.config.oauth_refresh_token
            
            if not refresh_token:
                logger.error("No refresh token available to refresh access token")
                return False
            
            refreshed = self.oauth_helper.refresh_access_token(refresh_token)
            if 'refresh_token' not in refreshed and self._tokens and self._tokens.get('refresh_token'):
                refreshed['refresh_token'] = self._tokens['refresh_token']
            # Persist and update in-memory tokens
            self.token_storage.save_tokens(self.user_id, refreshed)
            self._tokens = refreshed
            # Rebuild client with new token
            new_access_token = refreshed['access_token']
            self.client = tweepy.Client(bearer_token=new_access_token, wait_on_rate_limit=True)
            return True
        except Exception as e:
            logger.error(f"Access token refresh failed: {e}")
            return False

    def _oauth2_headers(self) -> Dict[str, str]:
        """Build OAuth2 authorization headers with current token."""
        access_token = None
        if self._tokens and self._tokens.get('access_token'):
            access_token = self._tokens['access_token']
        elif getattr(self.config, 'oauth_access_token', None):
            access_token = self.config.oauth_access_token
        if not access_token:
            raise RuntimeError("Missing OAuth2 access token")
        return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    def _http_post_tweet(self, content: str, **kwargs) -> Optional[str]:
        """Post a tweet using OAuth2 user token via direct HTTP."""
        # Respect rate limiting
        if not self._check_post_rate_limit():
            logger.warning("Post rate limit check failed")
            return None
        payload: Dict[str, Any] = {"text": content}
        # Support in_reply_to or other options via kwargs
        if 'in_reply_to_tweet_id' in kwargs:
            payload["reply"] = {"in_reply_to_tweet_id": kwargs['in_reply_to_tweet_id']}
        url = "https://api.twitter.com/2/tweets"
        headers = self._oauth2_headers()
        resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.status_code == 401 and self._attempt_refresh_and_rebuild_client():
            headers = self._oauth2_headers()
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
        if resp.ok:
            data = resp.json()
            tid = (data.get('data') or {}).get('id')
            return tid
        logger.error(f"Tweet post failed: HTTP {resp.status_code}: {resp.text[:200]}")
        return None

    def _http_reply_to_tweet(self, tweet_id: str, content: str) -> Optional[str]:
        """Reply to a tweet using OAuth2 user token via direct HTTP."""
        return self._http_post_tweet(content, in_reply_to_tweet_id=tweet_id)
