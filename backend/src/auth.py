"""
Authentication module for API Orchestrator
Handles JWT tokens, password hashing, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
import os

from src.database import get_db, User, DatabaseManager
from src.config import settings

# Configuration from secure settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator('username')
    def validate_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        return v.strip()
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    
class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    subscription_tier: str
    api_calls_remaining: int
    created_at: str

# Authentication utilities
class AuthManager:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a plain password"""
        # Security checks
        if not password:
            raise ValueError("Password cannot be empty")
        if len(password) > 1000:  # Prevent DoS with very long passwords
            raise ValueError("Password exceeds maximum allowed length")
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and verify a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthManager.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user"""
        # Validate password strength
        is_valid, message = settings.validate_password(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()
        
        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        hashed_password = AuthManager.get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name or user_data.username,
            is_active=True,
            subscription_tier="free",
            api_calls_limit=100,  # Free tier limit
            api_calls_this_month=0  # Initialize to 0
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user

# Dependency functions
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = AuthManager.decode_token(token)
    if payload is None:
        raise credentials_exception
    
    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception
    
    email: str = payload.get("email")
    if email is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def check_api_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Check if user has API calls remaining and track usage for billing"""
    from src.billing import BillingManager, PRICING_TIERS
    
    # Get tier configuration
    tier_config = PRICING_TIERS.get(current_user.subscription_tier, PRICING_TIERS["free"])
    api_limit = tier_config["api_calls"]
    
    # Check if unlimited (-1 means unlimited)
    if api_limit == -1:
        # Track usage for enterprise users
        billing = BillingManager(db)
        billing.track_usage(
            user_id=current_user.id,
            event_type="api_call",
            quantity=1,
            metadata={"tier": "enterprise"}
        )
        return current_user
    
    # Check if within limits
    if current_user.api_calls_this_month >= api_limit:
        # Allow overage for paid tiers (usage-based billing)
        if current_user.subscription_tier != "free":
            billing = BillingManager(db)
            billing.track_usage(
                user_id=current_user.id,
                event_type="api_call",
                quantity=1,
                metadata={"overage": True}
            )
            return current_user
        else:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"API limit exceeded. Upgrade to a paid tier for more API calls."
            )
    
    # Track normal usage
    billing = BillingManager(db)
    billing.track_usage(
        user_id=current_user.id,
        event_type="api_call",
        quantity=1,
        metadata={"within_limit": True}
    )
    
    return current_user

# Subscription tier limits
SUBSCRIPTION_TIERS = {
    "free": {
        "api_calls": 100,
        "projects": 3,
        "mock_servers": 1,
        "export_formats": ["json"],
        "ai_analysis": False
    },
    "starter": {
        "api_calls": 1000,
        "projects": 10,
        "mock_servers": 3,
        "export_formats": ["json", "yaml"],
        "ai_analysis": True
    },
    "growth": {
        "api_calls": 10000,
        "projects": 50,
        "mock_servers": 10,
        "export_formats": ["json", "yaml", "postman", "openapi"],
        "ai_analysis": True
    },
    "enterprise": {
        "api_calls": -1,  # Unlimited
        "projects": -1,
        "mock_servers": -1,
        "export_formats": ["all"],
        "ai_analysis": True
    }
}

def check_subscription_feature(user: User, feature: str, required_value: Any = None) -> bool:
    """Check if user's subscription tier allows a feature"""
    tier_limits = SUBSCRIPTION_TIERS.get(user.subscription_tier, SUBSCRIPTION_TIERS["free"])
    
    if feature not in tier_limits:
        return False
    
    limit = tier_limits[feature]
    
    # Handle unlimited (-1)
    if limit == -1:
        return True
    
    # Handle boolean features
    if isinstance(limit, bool):
        return limit
    
    # Handle numeric limits
    if isinstance(limit, int) and required_value is not None:
        return required_value <= limit
    
    # Handle list features (e.g., export formats)
    if isinstance(limit, list):
        if "all" in limit:
            return True
        if required_value:
            return required_value in limit
        return True
    
    return True