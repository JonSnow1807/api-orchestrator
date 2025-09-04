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
        print("⚠️ WARNING: Using generated SECRET_KEY. Set SECRET_KEY in .env for production!")
    
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./api_orchestrator.db")
    
    # AI API Keys
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:5174"
    ]
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_TIMEOUT_MINUTES: int = int(os.getenv("LOGIN_TIMEOUT_MINUTES", "15"))
    
    # File Security Settings
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: set = {'.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.jsx', '.tsx'}
    BASE_OUTPUT_DIR: Path = Path("./output")  # Restrict output to this directory
    
    # Path Security
    ALLOWED_SOURCE_PATHS: List[Path] = [
        Path.cwd(),  # Current working directory
        Path.home() / "projects",  # User's projects folder
    ]
    
    # Mock Server Settings
    MOCK_SERVER_PORT_RANGE_START: int = int(os.getenv("MOCK_SERVER_PORT_RANGE_START", "9000"))
    MOCK_SERVER_PORT_RANGE_END: int = int(os.getenv("MOCK_SERVER_PORT_RANGE_END", "9100"))
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
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
        """Validate password against policy"""
        if len(password) < cls.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {cls.PASSWORD_MIN_LENGTH} characters long"
        
        if cls.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if cls.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if cls.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        if cls.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"

settings = Settings()