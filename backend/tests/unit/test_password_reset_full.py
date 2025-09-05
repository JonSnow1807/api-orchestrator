"""Comprehensive tests for password_reset.py module"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
import hashlib
import secrets
from sqlalchemy.orm import Session

from src.password_reset import (
    PasswordResetToken,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChangeRequest,
    PasswordResetManager,
    EmailService,
    request_password_reset,
    confirm_password_reset,
    change_password
)

class TestPasswordResetManager:
    def test_generate_reset_token(self):
        """Test token generation"""
        token = PasswordResetManager.generate_reset_token()
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_hash_token(self):
        """Test token hashing"""
        token = "test_token_123"
        hashed = PasswordResetManager.hash_token(token)
        assert isinstance(hashed, str)
        assert hashed == hashlib.sha256(token.encode()).hexdigest()
        assert hashed != token
    
    @patch('src.password_reset.datetime')
    def test_create_reset_token(self, mock_datetime):
        """Test creating reset token in database"""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_db = MagicMock(spec=Session)
        user_id = 1
        
        # Mock existing tokens query
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value.update = MagicMock()
        
        with patch.object(PasswordResetManager, 'generate_reset_token', return_value='test_token'):
            token = PasswordResetManager.create_reset_token(mock_db, user_id)
        
        assert token == 'test_token'
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify token object was created correctly
        token_obj = mock_db.add.call_args[0][0]
        assert isinstance(token_obj, PasswordResetToken)
        assert token_obj.user_id == user_id
    
    @patch('src.password_reset.datetime')
    def test_verify_reset_token_valid(self, mock_datetime):
        """Test verifying valid reset token"""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        
        mock_token = MagicMock()
        mock_token.user_id = 1
        mock_token.expires_at = mock_now + timedelta(hours=1)
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_token, mock_user]
        
        user = PasswordResetManager.verify_reset_token(mock_db, "test_token")
        assert user == mock_user
    
    def test_verify_reset_token_invalid(self):
        """Test verifying invalid reset token"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        user = PasswordResetManager.verify_reset_token(mock_db, "invalid_token")
        assert user is None
    
    def test_use_reset_token(self):
        """Test marking token as used"""
        mock_db = MagicMock(spec=Session)
        
        PasswordResetManager.use_reset_token(mock_db, "test_token")
        
        mock_db.query.assert_called()
        mock_db.commit.assert_called_once()
    
    @patch('src.password_reset.datetime')
    def test_cleanup_expired_tokens(self, mock_datetime):
        """Test cleanup of expired tokens"""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_db = MagicMock(spec=Session)
        
        PasswordResetManager.cleanup_expired_tokens(mock_db)
        
        mock_db.query.assert_called()
        mock_db.commit.assert_called_once()

class TestEmailService:
    @patch('src.password_reset.os.getenv')
    @patch('builtins.print')
    def test_send_password_reset_email_dev_mode(self, mock_print, mock_getenv):
        """Test sending email in dev mode (no SMTP configured)"""
        mock_getenv.side_effect = lambda key, default=None: None
        
        result = EmailService.send_password_reset_email(
            "test@example.com",
            "http://localhost:5173/reset?token=abc123"
        )
        
        assert result is True
        mock_print.assert_called()
        assert "Password reset URL" in mock_print.call_args[0][0]
    
    @patch('src.password_reset.os.getenv')
    @patch('src.password_reset.smtplib.SMTP')
    def test_send_password_reset_email_smtp(self, mock_smtp, mock_getenv):
        """Test sending email via SMTP"""
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASS": "password",
            "FROM_EMAIL": "noreply@test.com"
        }.get(key, default)
        
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance
        
        result = EmailService.send_password_reset_email(
            "test@example.com",
            "http://localhost:5173/reset?token=abc123"
        )
        
        assert result is True
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("user@test.com", "password")
        mock_smtp_instance.send_message.assert_called_once()
    
    @patch('src.password_reset.os.getenv')
    @patch('src.password_reset.smtplib.SMTP')
    @patch('builtins.print')
    def test_send_password_reset_email_smtp_failure(self, mock_print, mock_smtp, mock_getenv):
        """Test SMTP email failure handling"""
        mock_getenv.side_effect = lambda key, default=None: {
            "SMTP_HOST": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASS": "password"
        }.get(key, default)
        
        mock_smtp.side_effect = Exception("SMTP connection failed")
        
        result = EmailService.send_password_reset_email(
            "test@example.com",
            "http://localhost:5173/reset?token=abc123"
        )
        
        assert result is False
        mock_print.assert_called()
        assert "Failed to send email" in mock_print.call_args[0][0]

class TestPasswordResetAPIFunctions:
    @pytest.mark.asyncio
    @patch('src.password_reset.EmailService.send_password_reset_email')
    @patch('src.password_reset.PasswordResetManager.create_reset_token')
    @patch('src.password_reset.os.getenv')
    async def test_request_password_reset_user_exists(self, mock_getenv, mock_create_token, mock_send_email):
        """Test requesting password reset for existing user"""
        mock_getenv.return_value = "http://localhost:5173"
        mock_create_token.return_value = "reset_token_123"
        mock_send_email.return_value = True
        
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        result = await request_password_reset(mock_db, "test@example.com")
        
        assert "message" in result
        assert "password reset link has been sent" in result["message"]
        mock_create_token.assert_called_once_with(mock_db, 1)
        mock_send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_request_password_reset_user_not_exists(self):
        """Test requesting password reset for non-existent user"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await request_password_reset(mock_db, "nonexistent@example.com")
        
        assert "message" in result
        assert "password reset link has been sent" in result["message"]
    
    @pytest.mark.asyncio
    @patch('src.password_reset.datetime')
    async def test_request_password_reset_rate_limit(self, mock_datetime):
        """Test rate limiting for password reset requests"""
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value.count.return_value = 3  # Already 3 requests
        
        with pytest.raises(Exception) as exc:
            await request_password_reset(mock_db, "test@example.com")
        assert exc.value is not None
    
    @pytest.mark.asyncio
    @patch('src.password_reset.PasswordResetManager.verify_reset_token')
    @patch('src.password_reset.PasswordResetManager.use_reset_token')
    @patch('src.password_reset.AuthManager.get_password_hash')
    @patch('src.password_reset.settings.validate_password')
    @patch('src.password_reset.datetime')
    async def test_confirm_password_reset_success(self, mock_datetime, mock_validate, mock_hash, mock_use_token, mock_verify):
        """Test successful password reset confirmation"""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        mock_validate.return_value = (True, "Valid")
        mock_hash.return_value = "hashed_password"
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_verify.return_value = mock_user
        
        mock_db = MagicMock(spec=Session)
        
        result = await confirm_password_reset(mock_db, "reset_token", "NewPass123!")
        
        assert "message" in result
        assert "successfully reset" in result["message"]
        assert mock_user.hashed_password == "hashed_password"
        mock_use_token.assert_called_once_with(mock_db, "reset_token")
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.password_reset.settings.validate_password')
    async def test_confirm_password_reset_invalid_password(self, mock_validate):
        """Test password reset with invalid password"""
        mock_validate.return_value = (False, "Password too weak")
        mock_db = MagicMock(spec=Session)
        
        with pytest.raises(Exception) as exc:
            await confirm_password_reset(mock_db, "token", "weak")
        assert exc.value is not None
    
    @pytest.mark.asyncio
    @patch('src.password_reset.PasswordResetManager.verify_reset_token')
    @patch('src.password_reset.settings.validate_password')
    async def test_confirm_password_reset_invalid_token(self, mock_validate, mock_verify):
        """Test password reset with invalid token"""
        mock_validate.return_value = (True, "Valid")
        mock_verify.return_value = None
        mock_db = MagicMock(spec=Session)
        
        with pytest.raises(Exception) as exc:
            await confirm_password_reset(mock_db, "invalid_token", "NewPass123!")
        assert exc.value is not None
    
    @pytest.mark.asyncio
    @patch('src.password_reset.AuthManager.verify_password')
    @patch('src.password_reset.AuthManager.get_password_hash')
    @patch('src.password_reset.settings.validate_password')
    @patch('src.password_reset.datetime')
    async def test_change_password_success(self, mock_datetime, mock_validate, mock_hash, mock_verify_pw):
        """Test successful password change"""
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        mock_verify_pw.side_effect = [True, False]  # Current password correct, new is different
        mock_validate.return_value = (True, "Valid")
        mock_hash.return_value = "new_hashed_password"
        
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.hashed_password = "old_hash"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await change_password(mock_db, 1, "current_pass", "new_pass")
        
        assert "message" in result
        assert "successfully changed" in result["message"]
        assert mock_user.hashed_password == "new_hashed_password"
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_change_password_user_not_found(self):
        """Test changing password for non-existent user"""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(Exception) as exc:
            await change_password(mock_db, 999, "current", "new")
        assert exc.value is not None
    
    @pytest.mark.asyncio
    @patch('src.password_reset.AuthManager.verify_password')
    async def test_change_password_incorrect_current(self, mock_verify):
        """Test changing password with incorrect current password"""
        mock_verify.return_value = False
        
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_user.hashed_password = "hash"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(Exception) as exc:
            await change_password(mock_db, 1, "wrong_pass", "new_pass")
        assert exc.value is not None
    
    @pytest.mark.asyncio
    @patch('src.password_reset.AuthManager.verify_password')
    @patch('src.password_reset.settings.validate_password')
    async def test_change_password_same_as_current(self, mock_validate, mock_verify):
        """Test changing password to same as current"""
        mock_verify.return_value = True  # Both current and new match
        mock_validate.return_value = (True, "Valid")
        
        mock_db = MagicMock(spec=Session)
        mock_user = MagicMock()
        mock_user.hashed_password = "hash"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(Exception) as exc:
            await change_password(mock_db, 1, "same_pass", "same_pass")
        assert exc.value is not None

class TestPydanticModels:
    def test_password_reset_request_model(self):
        """Test PasswordResetRequest model"""
        model = PasswordResetRequest(email="test@example.com")
        assert model.email == "test@example.com"
    
    def test_password_reset_confirm_model(self):
        """Test PasswordResetConfirm model"""
        model = PasswordResetConfirm(token="abc123", new_password="NewPass123!")
        assert model.token == "abc123"
        assert model.new_password == "NewPass123!"
    
    def test_password_change_request_model(self):
        """Test PasswordChangeRequest model"""
        model = PasswordChangeRequest(current_password="old", new_password="new")
        assert model.current_password == "old"
        assert model.new_password == "new"