#!/usr/bin/env python3
"""
Twitter OAuth 2.0 Integration
Handles OAuth flow for write permissions with callback URL support
"""

import logging
import secrets
import base64
import hashlib
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs
import tweepy
import requests
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class TwitterOAuth:
    """Twitter OAuth 2.0 handler with PKCE for write permissions"""
    
    def __init__(self, 
                 client_id: str,
                 client_secret: str,
                 callback_url: str,
                 scopes: list = None):
        """Initialize OAuth handler"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = callback_url
        self.scopes = scopes or [
            'tweet.read', 
            'tweet.write', 
            'users.read',
            'offline.access'  # For refresh tokens
        ]
        
        # OAuth endpoints
        self.auth_url = "https://twitter.com/i/oauth2/authorize"
        self.token_url = "https://api.twitter.com/2/oauth2/token"
        
        # PKCE state
        self.code_verifier = None
        self.code_challenge = None
        self.state = None
        
        logger.info(f"🔐 Twitter OAuth initialized with callback: {self.callback_url}")
    
    def generate_auth_url(self) -> Tuple[str, str]:
        """Generate authorization URL with PKCE"""
        
        # Generate PKCE parameters
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        self.code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        # Generate state for CSRF protection
        self.state = secrets.token_urlsafe(32)
        
        # Build authorization URL
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.callback_url,
            'scope': ' '.join(self.scopes),
            'state': self.state,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        
        logger.info("🔗 Generated OAuth authorization URL")
        return auth_url, self.state
    
    def exchange_code_for_tokens(self, 
                                authorization_code: str,
                                received_state: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        
        # Validate state
        if received_state != self.state:
            raise ValueError("Invalid state parameter - possible CSRF attack")
        
        if not self.code_verifier:
            raise ValueError("No code verifier found - call generate_auth_url first")
        
        # Prepare token exchange
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        # Use Basic only if client_secret is configured (confidential client)
        if self.client_secret:
            headers['Authorization'] = f'Basic {self._get_basic_auth()}'
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.callback_url,
            'code_verifier': self.code_verifier,
            'client_id': self.client_id
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            
            # Store token metadata
            tokens['expires_at'] = datetime.now() + timedelta(seconds=tokens.get('expires_in', 7200))
            tokens['obtained_at'] = datetime.now().isoformat()
            
            logger.info("✅ Successfully exchanged code for tokens")
            return tokens
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token exchange failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        # Use Basic only if client_secret is configured (confidential client)
        if self.client_secret:
            headers['Authorization'] = f'Basic {self._get_basic_auth()}'
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id
        }
        
        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            response.raise_for_status()
            
            tokens = response.json()
            tokens['expires_at'] = datetime.now() + timedelta(seconds=tokens.get('expires_in', 7200))
            tokens['refreshed_at'] = datetime.now().isoformat()
            
            logger.info("🔄 Successfully refreshed access token")
            return tokens
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Token refresh failed: {e}")
            raise
    
    def create_authenticated_client(self, access_token: str) -> tweepy.Client:
        """Create Tweepy client with OAuth 2.0 user access token"""
        
        # For OAuth 2.0 user context authentication, Tweepy expects the access token
        # to be passed as bearer_token, but it represents user context, not app-only
        # Reference: https://docs.x.com/fundamentals/authentication/oauth-2-0/overview
        
        return tweepy.Client(
            bearer_token=access_token,
            wait_on_rate_limit=True
        )
    
    def validate_tokens(self, tokens: Dict[str, Any]) -> bool:
        """Validate if tokens are still valid"""
        
        if 'expires_at' not in tokens:
            return False
        
        # Check if token is expired (with 5 minute buffer)
        expires_at = datetime.fromisoformat(tokens['expires_at'])
        buffer_time = datetime.now() + timedelta(minutes=5)
        
        return expires_at > buffer_time
    
    def _get_basic_auth(self) -> str:
        """Get base64 encoded client credentials"""
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()

class TokenStorage:
    """Simple file-based token storage"""
    
    def __init__(self, storage_path: str = "tokens.json"):
        self.storage_path = storage_path
    
    def save_tokens(self, user_id: str, tokens: Dict[str, Any]) -> None:
        """Save tokens for a user"""
        import json
        
        try:
            # Load existing tokens
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    all_tokens = json.load(f)
            else:
                all_tokens = {}
            
            # Convert datetime objects to strings
            serializable_tokens = {}
            for key, value in tokens.items():
                if isinstance(value, datetime):
                    serializable_tokens[key] = value.isoformat()
                else:
                    serializable_tokens[key] = value
            
            # Save tokens for user
            all_tokens[user_id] = serializable_tokens
            
            with open(self.storage_path, 'w') as f:
                json.dump(all_tokens, f, indent=2)
            
            logger.info(f"💾 Saved tokens for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
    
    def load_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load tokens for a user"""
        import json
        
        try:
            if not os.path.exists(self.storage_path):
                return None
            
            with open(self.storage_path, 'r') as f:
                all_tokens = json.load(f)
            
            return all_tokens.get(user_id)
            
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
            return None
    
    def delete_tokens(self, user_id: str) -> None:
        """Delete tokens for a user"""
        import json
        
        try:
            if not os.path.exists(self.storage_path):
                return
            
            with open(self.storage_path, 'r') as f:
                all_tokens = json.load(f)
            
            if user_id in all_tokens:
                del all_tokens[user_id]
                
                with open(self.storage_path, 'w') as f:
                    json.dump(all_tokens, f, indent=2)
                
                logger.info(f"🗑️ Deleted tokens for user: {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete tokens: {e}")

def get_oauth_config_from_env() -> Dict[str, str]:
    """Load OAuth configuration from environment"""
    
    def _strip_quotes(value: str) -> str:
        if not value:
            return value
        return value.strip().strip('"').strip("'")
    
    return {
        'client_id': _strip_quotes(os.getenv('TWITTER_OAUTH_CLIENT_ID', '')),
        'client_secret': _strip_quotes(os.getenv('TWITTER_OAUTH_CLIENT_SECRET', '')),
        'callback_url': _strip_quotes(os.getenv('TWITTER_OAUTH_CALLBACK_URL', 'http://localhost:8000/auth/twitter/callback'))
    }
