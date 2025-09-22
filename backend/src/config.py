"""
Configuration management for API Orchestrator
Handles environment variables and security settings
"""

import os
import secrets
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings with security defaults"""

    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", None)
    if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-this":
        # Generate a secure random key if not provided
        SECRET_KEY = secrets.token_urlsafe(32)
        print(
            "⚠️ WARNING: Using generated SECRET_KEY. Set SECRET_KEY in .env for production!"
        )

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./api_orchestrator.db")

    # AI API Keys
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

    # CORS Settings - Production Ready
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "https://streamapi.dev",
        "https://app.streamapi.dev",
        "https://api.streamapi.dev",
        "https://*.streamapi.dev",
    ]

    # Additional CORS configuration
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = [
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
        "HEAD",
    ]
    CORS_ALLOW_HEADERS: List[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since",
        "X-API-Key",
        "X-Workspace-ID",
    ]

    # Rate Limiting
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_TIMEOUT_MINUTES: int = int(os.getenv("LOGIN_TIMEOUT_MINUTES", "15"))

    # File Security Settings
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: set = {
        ".py",
        ".js",
        ".ts",
        ".java",
        ".go",
        ".rb",
        ".php",
        ".jsx",
        ".tsx",
    }
    BASE_OUTPUT_DIR: Path = Path("./output")  # Restrict output to this directory

    # Path Security
    ALLOWED_SOURCE_PATHS: List[Path] = [
        Path.cwd(),  # Current working directory
        Path.home() / "projects",  # User's projects folder
    ]

    # Mock Server Settings
    MOCK_SERVER_PORT_RANGE_START: int = int(
        os.getenv("MOCK_SERVER_PORT_RANGE_START", "9000")
    )
    MOCK_SERVER_PORT_RANGE_END: int = int(
        os.getenv("MOCK_SERVER_PORT_RANGE_END", "9100")
    )

    # Password Policy - Enterprise Grade
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_MAX_CONSECUTIVE_CHARS: int = 3
    PASSWORD_BLACKLIST_COMMON: bool = True

    # Email Settings for Password Reset
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@streamapi.dev")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME", "StreamAPI")
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    # Password Reset Settings
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = int(
        os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", "24")
    )
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://streamapi.dev")

    # Error Tracking with Sentry
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT: str = os.getenv("SENTRY_ENVIRONMENT", "production")
    SENTRY_TRACES_SAMPLE_RATE: float = float(
        os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")
    )
    SENTRY_ENABLED: bool = os.getenv("SENTRY_ENABLED", "false").lower() == "true"

    @classmethod
    def validate_path(cls, path: Path) -> bool:
        """Validate that a path is within allowed directories"""
        try:
            resolved_path = path.resolve()
            # Check if path is within any allowed source path
            for allowed_path in cls.ALLOWED_SOURCE_PATHS:
                try:
                    resolved_path.relative_to(allowed_path.resolve())
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    @classmethod
    def validate_output_path(cls, path: Path) -> bool:
        """Validate that an output path is within the allowed output directory"""
        try:
            resolved_path = path.resolve()
            resolved_path.relative_to(cls.BASE_OUTPUT_DIR.resolve())
            return True
        except ValueError:
            return False

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize a filename to prevent path traversal"""
        # Remove any path components
        filename = os.path.basename(filename)
        # Remove dangerous characters
        filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
        return filename

    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, str]:
        """Validate password against enterprise-grade policy"""
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return (
                False,
                f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long",
            )

        if cls.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if cls.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if cls.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"

        if cls.PASSWORD_REQUIRE_SPECIAL and not any(
            c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password
        ):
            return False, "Password must contain at least one special character"

        # Check for consecutive characters
        if cls.PASSWORD_MAX_CONSECUTIVE_CHARS:
            for i in range(len(password) - cls.PASSWORD_MAX_CONSECUTIVE_CHARS + 1):
                substring = password[i : i + cls.PASSWORD_MAX_CONSECUTIVE_CHARS]
                # Check for consecutive identical chars
                if len(set(substring)) == 1:
                    return (
                        False,
                        f"Password cannot contain {cls.PASSWORD_MAX_CONSECUTIVE_CHARS} consecutive identical characters",
                    )
                # Check for sequential chars (abc, 123, etc.)
                if all(
                    ord(substring[j]) == ord(substring[j - 1]) + 1
                    for j in range(1, len(substring))
                ):
                    return (
                        False,
                        f"Password cannot contain {cls.PASSWORD_MAX_CONSECUTIVE_CHARS} consecutive sequential characters",
                    )

        # Check against common passwords
        if cls.PASSWORD_BLACKLIST_COMMON:
            common_passwords = {
                "password123",
                "123456789",
                "qwertyuiop",
                "password1",
                "admin123456",
                "welcome123",
                "letmein123",
                "1q2w3e4r5t",
                "password!@#",
                "adminadmin",
                "rootpassword",
                "testtest123",
                "changeme123",
                "defaultpass",
                "newpassword",
                "temppass123",
            }
            if password.lower() in common_passwords:
                return False, "Password is too common and easily guessable"

        return True, "Password meets all security requirements"


settings = Settings()
