"""
Password reset functionality for API Orchestrator
Handles secure password reset tokens and email notifications
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from src.database import Base, User
from src.auth import AuthManager
from src.config import settings


# Password Reset Token Model
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)


# Pydantic Models
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


# Password Reset Manager
class PasswordResetManager:
    TOKEN_EXPIRY_HOURS = 1  # Token expires in 1 hour

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_reset_token(cls, db: Session, user_id: int) -> str:
        """Create a password reset token for a user"""
        # Invalidate any existing tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id, PasswordResetToken.used == False
        ).update({"used": True})

        # Generate new token
        raw_token = cls.generate_reset_token()
        token_hash = cls.hash_token(raw_token)

        # Create token record
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS),
        )

        db.add(reset_token)
        db.commit()

        return raw_token

    @classmethod
    def verify_reset_token(cls, db: Session, token: str) -> Optional[User]:
        """Verify a password reset token and return the associated user"""
        token_hash = cls.hash_token(token)

        # Find token
        reset_token = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > datetime.utcnow(),
            )
            .first()
        )

        if not reset_token:
            return None

        # Get user
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        return user

    @classmethod
    def use_reset_token(cls, db: Session, token: str) -> None:
        """Mark a reset token as used"""
        token_hash = cls.hash_token(token)

        db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).update({"used": True})
        db.commit()

    @classmethod
    def cleanup_expired_tokens(cls, db: Session) -> None:
        """Remove expired tokens from the database"""
        db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < datetime.utcnow()
        ).delete()
        db.commit()


# Email Service (placeholder - implement with actual email service)
class EmailService:
    """Email service for sending password reset emails"""

    @staticmethod
    def send_password_reset_email(email: str, reset_url: str) -> bool:
        """
        Send password reset email to user

        NOTE: This is a placeholder implementation.
        In production, integrate with a real email service like:
        - SendGrid
        - AWS SES
        - Mailgun
        - SMTP server
        """

        # Check if SMTP settings are configured
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        from_email = os.getenv("FROM_EMAIL", "noreply@api-orchestrator.com")

        if not all([smtp_host, smtp_user, smtp_pass]):
            # Log the reset URL for development
            print(f"[DEV MODE] Password reset URL for {email}: {reset_url}")
            return True

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = email
            msg["Subject"] = "Password Reset Request - API Orchestrator"

            # Email body
            body = f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>You have requested to reset your password for API Orchestrator.</p>
                    <p>Click the link below to reset your password:</p>
                    <p><a href="{reset_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                    <p>Or copy and paste this URL into your browser:</p>
                    <p>{reset_url}</p>
                    <br>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you did not request this password reset, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>API Orchestrator Team</p>
                </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            # Send email
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False


# Password Reset API Functions
async def request_password_reset(db: Session, email: str) -> dict:
    """Request a password reset for a user"""
    # Find user by email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Don't reveal if email exists or not for security
        return {
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    # Check rate limiting - max 3 reset requests per hour
    recent_tokens = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.created_at > datetime.utcnow() - timedelta(hours=1),
        )
        .count()
    )

    if recent_tokens >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again later.",
        )

    # Create reset token
    reset_token = PasswordResetManager.create_reset_token(db, user.id)

    # Generate reset URL (frontend will handle this route)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"

    # Send email
    EmailService.send_password_reset_email(user.email, reset_url)

    return {
        "message": "If an account exists with this email, a password reset link has been sent."
    }


async def confirm_password_reset(db: Session, token: str, new_password: str) -> dict:
    """Confirm password reset with token and new password"""
    # Validate new password
    is_valid, message = settings.validate_password(new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Verify token
    user = PasswordResetManager.verify_reset_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Update password
    user.hashed_password = AuthManager.get_password_hash(new_password)
    user.password_changed_at = datetime.utcnow()

    # Mark token as used
    PasswordResetManager.use_reset_token(db, token)

    db.commit()

    return {"message": "Password has been successfully reset"}


async def change_password(
    db: Session, user_id: int, current_password: str, new_password: str
) -> dict:
    """Change password for authenticated user"""
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Verify current password
    if not AuthManager.verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    is_valid, message = settings.validate_password(new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Check if new password is different from current
    if AuthManager.verify_password(new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    user.hashed_password = AuthManager.get_password_hash(new_password)
    user.password_changed_at = datetime.utcnow()
    db.commit()

    return {"message": "Password has been successfully changed"}
