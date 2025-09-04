#!/usr/bin/env python3
"""
Security Manager
Handles encryption, secret management, and security policies
"""

import os
import hashlib
import secrets
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages security policies and encryption"""
    
    def __init__(self, secret_key: str, encryption_key: Optional[str] = None):
        """Initialize security manager"""
        self.secret_key = secret_key
        self.encryption_key = encryption_key
        self._rate_limits = defaultdict(list)
        
        # Initialize encryption
        if encryption_key:
            self.cipher = self._create_cipher(encryption_key)
        else:
            self.cipher = None
            logger.warning("No encryption key provided - sensitive data will not be encrypted")
    
    def _create_cipher(self, password: str) -> Fernet:
        """Create encryption cipher from password"""
        # Generate key from password
        password_bytes = password.encode()
        salt = hashlib.sha256(password_bytes).digest()[:16]  # Use first 16 bytes as salt
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def encrypt_string(self, data: str) -> str:
        """Encrypt a string"""
        if not self.cipher:
            logger.warning("No encryption available - returning plain text")
            return data
        
        try:
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data
    
    def decrypt_string(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not self.cipher:
            logger.warning("No encryption available - returning data as-is")
            return encrypted_data
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data
    
    def hash_api_key(self, api_key: str) -> str:
        """Create a secure hash of an API key for logging"""
        if len(api_key) < 8:
            return "****"
        
        # Show first 4 and last 4 characters, hash the middle
        start = api_key[:4]
        end = api_key[-4:]
        middle_hash = hashlib.sha256(api_key[4:-4].encode()).hexdigest()[:8]
        
        return f"{start}***{middle_hash}***{end}"
    
    def validate_api_key_format(self, api_key: str, key_type: str = "generic") -> bool:
        """Validate API key format"""
        if not api_key:
            return False
        
        # Basic validation
        if len(api_key) < 10:
            return False
        
        # Type-specific validation
        if key_type == "twitter":
            # Twitter API keys are typically 25+ characters
            return len(api_key) >= 25
        elif key_type == "gemini":
            # Gemini API keys start with AIza
            return api_key.startswith("AIza") and len(api_key) >= 32
        
        return True
    
    def check_rate_limit(self, identifier: str, limit_per_hour: int = 100) -> bool:
        """Check if request is within rate limit"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        # Clean old entries
        self._rate_limits[identifier] = [
            timestamp for timestamp in self._rate_limits[identifier]
            if timestamp > hour_ago
        ]
        
        # Check limit
        if len(self._rate_limits[identifier]) >= limit_per_hour:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Record this request
        self._rate_limits[identifier].append(current_time)
        return True
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    def sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data for logging"""
        sanitized = {}
        sensitive_keys = {
            'password', 'secret', 'key', 'token', 'api_key', 
            'access_token', 'bearer_token', 'smtp_password'
        }
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                if isinstance(value, str) and value:
                    sanitized[key] = self.hash_api_key(value)
                else:
                    sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def validate_input(self, data: str, max_length: int = 1000) -> bool:
        """Validate user input for security"""
        if not data:
            return False
        
        # Check length
        if len(data) > max_length:
            logger.warning(f"Input too long: {len(data)} > {max_length}")
            return False
        
        # Check for potential injection attempts
        dangerous_patterns = [
            '<script', 'javascript:', 'data:', 'vbscript:',
            'onload=', 'onerror=', 'onclick=', '<?php', '<%',
            'exec(', 'eval(', '__import__'
        ]
        
        data_lower = data.lower()
        for pattern in dangerous_patterns:
            if pattern in data_lower:
                logger.warning(f"Dangerous pattern detected: {pattern}")
                return False
        
        return True
    
    def secure_filename(self, filename: str) -> str:
        """Create a secure filename"""
        # Remove dangerous characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # Ensure it's not empty and not too long
        if not safe_filename:
            safe_filename = f"file_{self.generate_secure_token(8)}"
        elif len(safe_filename) > 255:
            safe_filename = safe_filename[:240] + "_truncated"
        
        return safe_filename
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for web responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        sanitized_details = self.sanitize_for_logging(details)
        logger.warning(f"Security Event: {event_type} | Details: {sanitized_details}")
    
    def audit_configuration(self, config_dict: Dict[str, Any]) -> Dict[str, str]:
        """Audit configuration for security issues"""
        issues = {}
        
        # Check for weak secrets
        for key, value in config_dict.items():
            if 'secret' in key.lower() or 'key' in key.lower():
                if isinstance(value, str) and len(value) < 32:
                    issues[key] = "Secret too short (< 32 characters)"
        
        # Check for development settings in production
        dangerous_dev_settings = {
            'debug': True,
            'echo': True,
            'development': True
        }
        
        for key, value in config_dict.items():
            if key.lower() in dangerous_dev_settings:
                if value == dangerous_dev_settings[key.lower()]:
                    issues[key] = "Development setting enabled in production"
        
        return issues
