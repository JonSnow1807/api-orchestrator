"""
Security Hardening System
Implements comprehensive security controls and hardening measures
"""

import os
import hashlib
import secrets
import logging
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    min_password_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    require_2fa: bool = False
    password_history_count: int = 5

class SecureRandomGenerator:
    """Cryptographically secure random number generator"""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_api_key(length: int = 64) -> str:
        """Generate secure API key"""
        return secrets.token_hex(length)

    @staticmethod
    def generate_salt() -> bytes:
        """Generate cryptographic salt"""
        return secrets.token_bytes(32)

class SecureHasher:
    """Secure password hashing using bcrypt"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with salt"""
        salt = bcrypt.gensalt(rounds=12)  # High cost factor
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hash_str: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hash_str.encode('utf-8'))
        except Exception:
            return False

    @staticmethod
    def hash_data(data: str, algorithm: str = 'sha256') -> str:
        """Hash data using specified algorithm"""
        if algorithm == 'sha256':
            return hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == 'sha512':
            return hashlib.sha512(data.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

class SecureEncryption:
    """Secure encryption/decryption using AES-256"""

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            key = os.urandom(32)  # 256-bit key
        self.key = key

    def encrypt(self, data: str) -> str:
        """Encrypt data using AES-256-CBC"""
        # Generate random IV
        iv = os.urandom(16)

        # Pad data to block size
        padding_length = 16 - (len(data) % 16)
        padded_data = data + chr(padding_length) * padding_length

        # Encrypt
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data.encode()) + encryptor.finalize()

        # Return base64 encoded IV + ciphertext
        return base64.b64encode(iv + ciphertext).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using AES-256-CBC"""
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data.encode())

            # Extract IV and ciphertext
            iv = data[:16]
            ciphertext = data[16:]

            # Decrypt
            cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()

            # Remove padding
            padding_length = padded_data[-1]
            return padded_data[:-padding_length].decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

class PasswordValidator:
    """Password strength validation"""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy

    def validate_password(self, password: str) -> tuple[bool, List[str]]:
        """Validate password against security policy"""
        errors = []

        if len(password) < self.policy.min_password_length:
            errors.append(f"Password must be at least {self.policy.min_password_length} characters long")

        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        if self.policy.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        if self.policy.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        # Check for common weak patterns
        if re.search(r'(.)\1{2,}', password):  # Three or more consecutive same characters
            errors.append("Password should not contain repeated characters")

        if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde|def)', password.lower()):
            errors.append("Password should not contain sequential characters")

        # Check against common passwords
        common_passwords = {'password', '123456', 'qwerty', 'admin', 'letmein', 'welcome'}
        if password.lower() in common_passwords:
            errors.append("Password is too common")

        return len(errors) == 0, errors

class RateLimiter:
    """Rate limiting for API endpoints"""

    def __init__(self):
        self.attempts = {}  # IP -> {'count': int, 'reset_time': datetime}
        self.logger = logging.getLogger(__name__)

    def is_allowed(self, identifier: str, max_attempts: int = 100, window_minutes: int = 60) -> bool:
        """Check if request is allowed based on rate limiting"""
        now = datetime.utcnow()

        if identifier in self.attempts:
            attempt_data = self.attempts[identifier]

            # Reset counter if window has passed
            if now > attempt_data['reset_time']:
                self.attempts[identifier] = {
                    'count': 1,
                    'reset_time': now + timedelta(minutes=window_minutes)
                }
                return True

            # Check if limit exceeded
            if attempt_data['count'] >= max_attempts:
                self.logger.warning(f"Rate limit exceeded for {identifier}")
                return False

            # Increment counter
            attempt_data['count'] += 1
            return True
        else:
            # First request
            self.attempts[identifier] = {
                'count': 1,
                'reset_time': now + timedelta(minutes=window_minutes)
            }
            return True

class InputSanitizer:
    """Input sanitization and validation"""

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")

        # Remove null bytes and control characters
        sanitized = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        # Allow alphanumeric, underscore, hyphen
        pattern = r'^[a-zA-Z0-9_-]{3,30}$'
        return re.match(pattern, username) is not None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove directory separators and special characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        sanitized = sanitized.replace('..', '')
        return sanitized[:255]  # Limit length

class SecurityHeaders:
    """HTTP security headers configuration"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }

class SessionManager:
    """Secure session management"""

    def __init__(self, timeout_minutes: int = 60):
        self.sessions = {}
        self.timeout_minutes = timeout_minutes
        self.logger = logging.getLogger(__name__)

    def create_session(self, user_id: str) -> str:
        """Create new secure session"""
        session_id = SecureRandomGenerator.generate_token(64)

        self.sessions[session_id] = {
            'user_id': user_id,
            'created': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'csrf_token': SecureRandomGenerator.generate_token(32)
        }

        return session_id

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and update last activity"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        now = datetime.utcnow()

        # Check if session expired
        if now - session['last_activity'] > timedelta(minutes=self.timeout_minutes):
            del self.sessions[session_id]
            return None

        # Update last activity
        session['last_activity'] = now
        return session

    def destroy_session(self, session_id: str):
        """Destroy session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

class SecurityAuditLogger:
    """Security event logging"""

    def __init__(self):
        self.logger = logging.getLogger('security_audit')

        # Configure security-specific logging
        if not self.logger.handlers:
            handler = logging.FileHandler('security_audit.log')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def log_login_attempt(self, username: str, ip: str, success: bool):
        """Log login attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"LOGIN_{status} - User: {username}, IP: {ip}")

    def log_password_change(self, username: str, ip: str):
        """Log password change"""
        self.logger.info(f"PASSWORD_CHANGE - User: {username}, IP: {ip}")

    def log_security_event(self, event_type: str, details: str, ip: str = None):
        """Log security event"""
        ip_info = f", IP: {ip}" if ip else ""
        self.logger.warning(f"SECURITY_EVENT - {event_type}: {details}{ip_info}")

def security_headers_middleware(func):
    """Decorator to add security headers to responses"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        response = await func(*args, **kwargs)

        # Add security headers
        headers = SecurityHeaders.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value

        return response
    return wrapper

def rate_limit(max_attempts: int = 100, window_minutes: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        limiter = RateLimiter()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract IP from request (implementation depends on framework)
            ip = "127.0.0.1"  # Placeholder - implement actual IP extraction

            if not limiter.is_allowed(ip, max_attempts, window_minutes):
                raise Exception("Rate limit exceeded")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

class SecurityManager:
    """Central security management system"""

    def __init__(self, policy: SecurityPolicy = None):
        self.policy = policy or SecurityPolicy()
        self.hasher = SecureHasher()
        self.validator = PasswordValidator(self.policy)
        self.session_manager = SessionManager(self.policy.session_timeout_minutes)
        self.audit_logger = SecurityAuditLogger()
        self.rate_limiter = RateLimiter()

        # Initialize encryption with environment key or generate new one
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if encryption_key:
            self.encryptor = SecureEncryption(base64.b64decode(encryption_key))
        else:
            self.encryptor = SecureEncryption()
            # Log warning about missing encryption key
            logging.warning("No ENCRYPTION_KEY environment variable set - using random key")

    def create_secure_user(self, username: str, password: str, email: str) -> Dict[str, Any]:
        """Create user with security validation"""
        # Validate inputs
        if not InputSanitizer.validate_username(username):
            raise ValueError("Invalid username format")

        if not InputSanitizer.validate_email(email):
            raise ValueError("Invalid email format")

        # Validate password
        is_valid, errors = self.validator.validate_password(password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {', '.join(errors)}")

        # Hash password
        password_hash = self.hasher.hash_password(password)

        return {
            'username': InputSanitizer.sanitize_string(username),
            'email': InputSanitizer.sanitize_string(email),
            'password_hash': password_hash,
            'created_at': datetime.utcnow(),
            'api_key': SecureRandomGenerator.generate_api_key()
        }

    def authenticate_user(self, username: str, password: str, ip: str) -> Optional[str]:
        """Authenticate user with rate limiting and logging"""
        # Check rate limit
        if not self.rate_limiter.is_allowed(f"login_{ip}", self.policy.max_login_attempts, 60):
            self.audit_logger.log_security_event("RATE_LIMIT_EXCEEDED", f"Login attempts for {username}", ip)
            return None

        # Placeholder for actual user lookup and password verification
        # In real implementation, this would query database
        user_exists = True  # Placeholder
        password_valid = True  # Placeholder

        if user_exists and password_valid:
            session_id = self.session_manager.create_session(username)
            self.audit_logger.log_login_attempt(username, ip, True)
            return session_id
        else:
            self.audit_logger.log_login_attempt(username, ip, False)
            return None

# Global security manager instance
security_manager = SecurityManager()

# Security utilities
def generate_secure_key() -> str:
    """Generate secure encryption key"""
    key = Fernet.generate_key()
    return base64.b64encode(key).decode()

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key or len(api_key) < 32:
        return False

    # Check if it's hexadecimal
    try:
        int(api_key, 16)
        return True
    except ValueError:
        return False

def secure_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks"""
    return secrets.compare_digest(a.encode(), b.encode())

# Environment variable validation
def validate_environment_security():
    """Validate security-related environment variables"""
    issues = []

    # Check for required variables
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing required environment variable: {var}")

    # Check for weak secrets
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 32:
        issues.append("SECRET_KEY is too short (minimum 32 characters)")

    # Check for insecure configurations
    debug_mode = os.getenv('DEBUG', '').lower()
    if debug_mode in ['true', '1', 'yes']:
        issues.append("DEBUG mode is enabled - should be disabled in production")

    return issues

if __name__ == "__main__":
    # Example usage
    security_mgr = SecurityManager()

    # Validate environment
    env_issues = validate_environment_security()
    if env_issues:
        print("⚠️  Security environment issues:")
        for issue in env_issues:
            print(f"  - {issue}")

    # Example password validation
    test_password = "MySecureP@ssw0rd123"
    is_valid, errors = security_mgr.validator.validate_password(test_password)
    print(f"Password valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    # Example encryption
    sensitive_data = "This is sensitive information"
    encrypted = security_mgr.encryptor.encrypt(sensitive_data)
    decrypted = security_mgr.encryptor.decrypt(encrypted)
    print(f"Encryption test passed: {sensitive_data == decrypted}")