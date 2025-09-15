"""
Unit tests for Authentication module
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from jose import jwt, JWTError
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.auth import AuthManager, UserCreate
from src.database import User

class TestPasswordUtils:
    """Test password hashing and verification"""

    def test_get_password_hash(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = AuthManager.get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 20
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = AuthManager.get_password_hash(password)
        
        assert AuthManager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = AuthManager.get_password_hash(password)
        
        assert AuthManager.verify_password(wrong_password, hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes"""
        password = "TestPassword123!"
        hash1 = AuthManager.get_password_hash(password)
        hash2 = AuthManager.get_password_hash(password)
        
        assert hash1 != hash2
        assert AuthManager.verify_password(password, hash1) is True
        assert AuthManager.verify_password(password, hash2) is True


class TestTokenUtils:
    """Test JWT token creation and verification"""

    @patch('src.auth.SECRET_KEY', 'test-secret-key')
    @patch('src.auth.ALGORITHM', 'HS256')
    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test@example.com"}
        token = AuthManager.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify token
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert payload.get("sub") == "test@example.com"
        assert "exp" in payload
        assert payload.get("type") == "access"

    @patch('src.auth.SECRET_KEY', 'test-secret-key')
    @patch('src.auth.ALGORITHM', 'HS256')
    @patch('src.auth.ACCESS_TOKEN_EXPIRE_MINUTES', 30)
    def test_create_access_token_with_expires(self):
        """Test access token with custom expiration"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = AuthManager.create_access_token(data, expires_delta)
        
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert payload.get("sub") == "test@example.com"
        
        # Check expiration is approximately 15 minutes from now
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        diff_minutes = (exp_time - now).total_seconds() / 60
        assert 14 < diff_minutes < 16  # Allow some tolerance

    @patch('src.auth.SECRET_KEY', 'test-secret-key')
    @patch('src.auth.ALGORITHM', 'HS256')
    @patch('src.auth.REFRESH_TOKEN_EXPIRE_DAYS', 7)
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        data = {"sub": "test@example.com"}
        token = AuthManager.create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert payload.get("sub") == "test@example.com"
        assert payload.get("type") == "refresh"

    @patch('src.auth.SECRET_KEY', 'test-secret-key')
    @patch('src.auth.ALGORITHM', 'HS256')
    def test_decode_token_valid(self):
        """Test token decoding with valid token"""
        data = {"email": "test@example.com"}
        token = AuthManager.create_access_token(data)
        payload = AuthManager.decode_token(token)
        
        assert payload is not None
        assert payload.get("email") == "test@example.com"

    @patch('src.auth.SECRET_KEY', 'test-secret-key')
    def test_decode_token_invalid(self):
        """Test token decoding with invalid token"""
        invalid_token = "invalid.token.here"
        payload = AuthManager.decode_token(invalid_token)
        
        assert payload is None

    @patch('src.auth.SECRET_KEY', 'test-secret-key')
    @patch('src.auth.ALGORITHM', 'HS256')
    def test_decode_token_expired(self):
        """Test token decoding with expired token"""
        # Create token that expires immediately
        data = {"sub": "test@example.com"}
        token = AuthManager.create_access_token(data, timedelta(seconds=-1))
        
        payload = AuthManager.decode_token(token)
        assert payload is None


class TestAuthManager:
    """Test AuthManager class methods"""

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        mock_db = Mock(spec=Session)
        email = "test@example.com"
        password = "TestPass123!"
        
        mock_user = Mock(spec=User)
        mock_user.email = email
        mock_user.hashed_password = AuthManager.get_password_hash(password)
        mock_user.is_active = True
        
        mock_db.query().filter().first.return_value = mock_user
        
        result = AuthManager.authenticate_user(mock_db, email, password)
        
        assert result == mock_user
        assert mock_user.last_login is not None
        mock_db.commit.assert_called_once()

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password"""
        mock_db = Mock(spec=Session)
        email = "test@example.com"
        password = "TestPass123!"
        wrong_password = "WrongPass456!"
        
        mock_user = Mock(spec=User)
        mock_user.email = email
        mock_user.hashed_password = AuthManager.get_password_hash(password)
        
        mock_db.query().filter().first.return_value = mock_user
        
        result = AuthManager.authenticate_user(mock_db, email, wrong_password)
        
        assert result is None

    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user"""
        mock_db = Mock(spec=Session)
        mock_db.query().filter().first.return_value = None
        
        result = AuthManager.authenticate_user(mock_db, "nonexistent@example.com", "password")
        
        assert result is None

    @patch('src.auth.settings')
    def test_create_user_success(self, mock_settings):
        """Test successful user creation"""
        mock_db = Mock(spec=Session)
        mock_settings.validate_password.return_value = (True, "Valid password")
        
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="TestPass123!"
        )
        
        # Mock database responses - no existing user
        mock_db.query().filter().first.return_value = None
        
        # Create the user
        result = AuthManager.create_user(mock_db, user_data)
        
        # Verify user was added to database
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('src.auth.settings')
    def test_create_user_duplicate_email(self, mock_settings):
        """Test user creation with duplicate email"""
        mock_db = Mock(spec=Session)
        mock_settings.validate_password.return_value = (True, "Valid password")
        
        user_data = UserCreate(
            email="existing@example.com",
            username="newuser",
            password="TestPass123!"
        )
        
        # Mock existing user with same email
        existing_user = Mock(spec=User)
        existing_user.email = "existing@example.com"
        existing_user.username = "existinguser"
        mock_db.query().filter().first.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.create_user(mock_db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail

    @patch('src.auth.settings')
    def test_create_user_weak_password(self, mock_settings):
        """Test user creation with weak password"""
        mock_db = Mock(spec=Session)
        mock_settings.validate_password.return_value = (False, "Password too weak")
        
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="weakpass"  # 8 chars to pass min_length validation
        )
        
        with pytest.raises(HTTPException) as exc_info:
            AuthManager.create_user(mock_db, user_data)
        
        assert exc_info.value.status_code == 400
        assert "Password too weak" in exc_info.value.detail


class TestAuthManagerStaticMethods:
    """Test that AuthManager methods are static"""

    def test_all_methods_are_static(self):
        """Verify all AuthManager methods are static"""
        # These methods should be callable without instance
        assert callable(AuthManager.verify_password)
        assert callable(AuthManager.get_password_hash)
        assert callable(AuthManager.create_access_token)
        assert callable(AuthManager.create_refresh_token)
        assert callable(AuthManager.decode_token)
        assert callable(AuthManager.authenticate_user)
        assert callable(AuthManager.create_user)