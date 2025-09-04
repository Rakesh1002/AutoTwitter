#!/usr/bin/env python3
"""
OAuth Callback Server
Simple Flask server to handle Twitter OAuth callbacks
"""

import logging
from flask import Flask, request, redirect, render_template_string, jsonify
from typing import Dict, Any
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from integrations.twitter_oauth import TwitterOAuth, TokenStorage, get_oauth_config_from_env

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Global OAuth handler and storage
oauth_handler = None
token_storage = TokenStorage()

# HTML templates
SUCCESS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Twitter OAuth Success</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .success { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; }
        .tokens { background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; border-radius: 5px; margin-top: 20px; }
        code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="success">
        <h2>✅ Twitter OAuth Successful!</h2>
        <p>Your Twitter account has been successfully connected with <strong>write permissions</strong>.</p>
        <p>User ID: <code>{{ user_id }}</code></p>
        <p>Access Token: <code>{{ access_token[:20] }}...</code></p>
    </div>
    
    <div class="tokens">
        <h3>Next Steps:</h3>
        <ol>
            <li>Your tokens have been saved to <code>tokens.json</code></li>
            <li>The bot can now post tweets on your behalf</li>
            <li>You can close this window</li>
        </ol>
        
        <h4>Environment Variables to Add:</h4>
        <pre>
TWITTER_OAUTH_ACCESS_TOKEN={{ access_token }}
TWITTER_OAUTH_REFRESH_TOKEN={{ refresh_token }}
TWITTER_OAUTH_USER_ID={{ user_id }}
        </pre>
    </div>
</body>
</html>
"""

ERROR_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Twitter OAuth Error</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .error { background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="error">
        <h2>❌ OAuth Error</h2>
        <p>{{ error_message }}</p>
        <p>Please try the authorization process again.</p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Home page with OAuth start button"""
    
    global oauth_handler
    
    # Initialize OAuth handler
    config = get_oauth_config_from_env()
    if not config['client_id'] or not config['client_secret']:
        return "❌ Missing OAuth configuration. Please set TWITTER_OAUTH_CLIENT_ID and TWITTER_OAUTH_CLIENT_SECRET environment variables."
    
    oauth_handler = TwitterOAuth(
        client_id=config['client_id'],
        client_secret=config['client_secret'],
        callback_url=config['callback_url']
    )
    
    auth_url, state = oauth_handler.generate_auth_url()
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Twitter OAuth Setup</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .auth-button {{ background: #1da1f2; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            .info {{ background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>🐦 Twitter Bot OAuth Setup</h1>
        
        <div class="info">
            <h3>What this will do:</h3>
            <ul>
                <li>Connect your Twitter account to the bot</li>
                <li>Grant <strong>write permissions</strong> for posting tweets</li>
                <li>Allow the bot to post on your behalf</li>
                <li>Save authentication tokens securely</li>
            </ul>
        </div>
        
        <a href="{auth_url}" class="auth-button">🔐 Authorize Twitter Bot</a>
        
        <h3>Configuration:</h3>
        <ul>
            <li>Client ID: {config['client_id']}</li>
            <li>Callback URL: {config['callback_url']}</li>
            <li>Scopes: tweet.read, tweet.write, users.read, offline.access</li>
        </ul>
    </body>
    </html>
    """

@app.route('/auth/twitter/callback')
def twitter_callback():
    """Handle Twitter OAuth callback"""
    
    global oauth_handler, token_storage
    
    try:
        # Get authorization code and state from callback
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.error(f"OAuth error: {error}")
            return render_template_string(ERROR_TEMPLATE, error_message=f"Twitter returned error: {error}")
        
        if not code or not state:
            return render_template_string(ERROR_TEMPLATE, error_message="Missing authorization code or state parameter")
        
        if not oauth_handler:
            return render_template_string(ERROR_TEMPLATE, error_message="OAuth handler not initialized. Please restart the authorization process.")
        
        # Exchange code for tokens
        tokens = oauth_handler.exchange_code_for_tokens(code, state)
        
        # Skip get_me() call for now - just save tokens with generic user ID
        # We'll get user info when we actually use the bot for posting
        user_id = "oauth_user"
        username = "Twitter User"
        
        # Save tokens
        token_storage.save_tokens(user_id, tokens)
        
        logger.info(f"✅ OAuth successful for user: {username} ({user_id})")
        
        # Return success page
        return render_template_string(
            SUCCESS_TEMPLATE,
            user_id=user_id,
            username=username,
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token', 'N/A')
        )
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return render_template_string(ERROR_TEMPLATE, error_message=str(e))

@app.route('/status')
def status():
    """Check OAuth status and token validity"""
    
    try:
        # Load all stored tokens
        import json
        tokens_file = token_storage.storage_path
        
        if not os.path.exists(tokens_file):
            return jsonify({
                'status': 'no_tokens',
                'message': 'No tokens found. Please complete OAuth setup.'
            })
        
        with open(tokens_file, 'r') as f:
            all_tokens = json.load(f)
        
        valid_users = []
        for user_id, tokens in all_tokens.items():
            if oauth_handler and oauth_handler.validate_tokens(tokens):
                valid_users.append({
                    'user_id': user_id,
                    'has_refresh_token': 'refresh_token' in tokens,
                    'expires_at': tokens.get('expires_at', 'unknown')
                })
        
        return jsonify({
            'status': 'ok',
            'valid_users': valid_users,
            'total_users': len(all_tokens),
            'valid_count': len(valid_users)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Twitter OAuth Server',
        'callback_url': get_oauth_config_from_env()['callback_url']
    })

if __name__ == '__main__':
    # Check environment
    config = get_oauth_config_from_env()
    
    if not config['client_id'] or not config['client_secret']:
        print("❌ Missing OAuth configuration!")
        print("Please set these environment variables:")
        print("  TWITTER_OAUTH_CLIENT_ID=your_client_id")
        print("  TWITTER_OAUTH_CLIENT_SECRET=your_client_secret")
        print("  TWITTER_OAUTH_CALLBACK_URL=your_callback_url")
        sys.exit(1)
    
    print("🚀 Starting Twitter OAuth server...")
    print(f"📍 Callback URL: {config['callback_url']}")
    print(f"🔐 Client ID: {config['client_id']}")
    print("\nVisit http://localhost:8000 to start OAuth setup")
    
    # Run server
    port = int(os.getenv('OAUTH_PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
