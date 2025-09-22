import os
import secrets
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import bleach
import re
from flask import request, session
from functools import wraps

class SecurityUtils:
    def __init__(self, app=None):
        self.app = app
        self._cipher_suite = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security utilities with Flask app"""
        self.app = app
        encryption_key = app.config.get('ENCRYPTION_KEY', 'default-key')
        self._cipher_suite = self._get_cipher_suite(encryption_key)
    
    def _get_cipher_suite(self, password):
        """Generate cipher suite from password"""
        password = password.encode()
        salt = b'stable_salt_for_demo'  # In production, use random salt per encryption
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def encrypt_sensitive_data(self, data):
        """Encrypt sensitive data like account numbers"""
        if not data:
            return data
        return self._cipher_suite.encrypt(str(data).encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        try:
            return self._cipher_suite.decrypt(encrypted_data.encode()).decode()
        except:
            return None
    
    @staticmethod
    def sanitize_input(input_data, allowed_tags=None):
        """Sanitize user input to prevent XSS"""
        if not input_data:
            return input_data
        
        if allowed_tags is None:
            allowed_tags = []
        
        # Remove potentially dangerous characters and tags
        cleaned = bleach.clean(input_data, tags=allowed_tags, strip=True)
        return cleaned.strip()
    
    @staticmethod
    def validate_account_number(account_number):
        """Validate account number format"""
        if not account_number:
            return False
        # Only allow digits, length 10
        pattern = r'^\d{10}$'
        return bool(re.match(pattern, account_number))
    
    @staticmethod
    def validate_amount(amount_str):
        """Validate monetary amount"""
        try:
            amount = float(amount_str)
            return amount > 0 and amount <= 1000000  # Max 1M per transaction
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "كلمة المرور يجب أن تكون 8 أحرف على الأقل"
        
        if not re.search(r'[A-Z]', password):
            return False, "كلمة المرور يجب أن تحتوي على حرف كبير"
        
        if not re.search(r'[a-z]', password):
            return False, "كلمة المرور يجب أن تحتوي على حرف صغير"
        
        if not re.search(r'\d', password):
            return False, "كلمة المرور يجب أن تحتوي على رقم"
        
        if not re.search(r'[!@#$%^&*]', password):
            return False, "كلمة المرور يجب أن تحتوي على رمز خاص (!@#$%^&*)"
        
        return True, "كلمة مرور قوية"
    
    @staticmethod
    def generate_csrf_token():
        """Generate CSRF token"""
        return secrets.token_hex(32)
    
    @staticmethod
    def validate_csrf_token(token):
        """Validate CSRF token"""
        if not token:
            return False
        stored_token = session.get('csrf_token')
        if not stored_token:
            return False
        return token == stored_token
    
    @staticmethod
    def get_client_ip():
        """Get client IP address safely"""
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
        return request.environ.get('REMOTE_ADDR', 'unknown')
    
    @staticmethod
    def hash_sensitive_data(data):
        """Hash sensitive data for logging/auditing"""
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import redirect, url_for
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def require_csrf(f):
    """Decorator to require CSRF token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token')
            if not SecurityUtils.validate_csrf_token(token):
                return "CSRF token validation failed", 403
        return f(*args, **kwargs)
    return decorated_function
