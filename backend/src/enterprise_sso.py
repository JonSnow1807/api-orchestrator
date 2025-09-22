"""
Enterprise SSO Module for API Orchestrator
Supports SAML 2.0 and OIDC authentication for enterprise customers
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

# Optional imports - gracefully handle missing packages
try:
    from authlib.integrations.starlette_client import OAuth

    HAS_AUTHLIB = True
except ImportError:
    OAuth = None
    HAS_AUTHLIB = False

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.utils import OneLogin_Saml2_Utils

    HAS_SAML = True
except (ImportError, Exception) as e:
    OneLogin_Saml2_Auth = None
    OneLogin_Saml2_Settings = None
    OneLogin_Saml2_Utils = None
    HAS_SAML = False
    print(f"⚠️ SAML not available (xmlsec version mismatch): {e}")
import os
import json
import uuid

from src.database import get_db, User
from src.auth import AuthManager, Token
from src.config import settings

# Security
security = HTTPBearer()


class SSOProvider(BaseModel):
    """SSO Provider Configuration"""

    id: str
    name: str
    type: str  # "saml" or "oidc"
    enabled: bool = True
    auto_provision: bool = True
    config: Dict[str, Any]
    domains: List[str] = []  # Email domains for this provider
    created_at: datetime
    updated_at: datetime


class SSOUser(BaseModel):
    """SSO User Info"""

    email: EmailStr
    username: str
    full_name: Optional[str] = None
    groups: List[str] = []
    attributes: Dict[str, Any] = {}
    provider_id: str
    provider_user_id: str


class EnterpriseAuth:
    """Enterprise Authentication Manager"""

    def __init__(self):
        if HAS_AUTHLIB:
            self.oauth = OAuth()
        else:
            self.oauth = None
        self.saml_providers = {}
        self.oidc_providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize SSO providers from configuration"""
        # SAML Providers
        saml_config = os.getenv("SAML_PROVIDERS", "{}")
        try:
            saml_providers = json.loads(saml_config)
            for provider_id, config in saml_providers.items():
                self.saml_providers[provider_id] = config
        except json.JSONDecodeError:
            pass

        # OIDC Providers
        oidc_config = os.getenv("OIDC_PROVIDERS", "{}")
        try:
            oidc_providers = json.loads(oidc_config)
            for provider_id, config in oidc_providers.items():
                # Register OAuth client
                self.oauth.register(
                    name=provider_id,
                    client_id=config["client_id"],
                    client_secret=config["client_secret"],
                    server_metadata_url=config["discovery_url"],
                    client_kwargs=config.get(
                        "client_kwargs", {"scope": "openid email profile"}
                    ),
                )
                self.oidc_providers[provider_id] = config
        except json.JSONDecodeError:
            pass

    def get_provider_for_domain(self, email: str) -> Optional[SSOProvider]:
        """Get SSO provider for email domain"""
        domain = email.split("@")[-1].lower()

        # Check SAML providers
        for provider_id, config in self.saml_providers.items():
            if domain in config.get("domains", []):
                return SSOProvider(
                    id=provider_id,
                    name=config["name"],
                    type="saml",
                    config=config,
                    domains=config.get("domains", []),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

        # Check OIDC providers
        for provider_id, config in self.oidc_providers.items():
            if domain in config.get("domains", []):
                return SSOProvider(
                    id=provider_id,
                    name=config["name"],
                    type="oidc",
                    config=config,
                    domains=config.get("domains", []),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

        return None

    def get_saml_auth_url(self, provider_id: str, return_to: str = None) -> str:
        """Get SAML authentication URL"""
        if provider_id not in self.saml_providers:
            raise HTTPException(status_code=404, detail="SAML provider not found")

        config = self.saml_providers[provider_id]

        # Build SAML settings
        saml_settings = {
            "sp": {
                "entityId": config["sp_entity_id"],
                "assertionConsumerService": {
                    "url": config["sp_acs_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": config.get("sp_sls_url", config["sp_acs_url"]),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            },
            "idp": {
                "entityId": config["idp_entity_id"],
                "singleSignOnService": {
                    "url": config["idp_sso_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "singleLogoutService": {
                    "url": config.get("idp_sls_url", ""),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": config["idp_cert"],
            },
        }

        # Create auth request
        auth = OneLogin_Saml2_Auth({}, saml_settings)
        auth_url = auth.login(return_to=return_to)

        return auth_url

    def get_oidc_auth_url(
        self, provider_id: str, request: Request, return_to: str = None
    ) -> str:
        """Get OIDC authentication URL"""
        if provider_id not in self.oidc_providers:
            raise HTTPException(status_code=404, detail="OIDC provider not found")

        client = self.oauth.create_client(provider_id)
        redirect_uri = f"{request.base_url}auth/sso/oidc/{provider_id}/callback"

        # Add state for security
        state = str(uuid.uuid4())
        request.session["oauth_state"] = state
        if return_to:
            request.session["oauth_return_to"] = return_to

        auth_url = client.authorize_redirect_url(redirect_uri=redirect_uri, state=state)

        return auth_url

    def process_saml_response(self, provider_id: str, saml_response: str) -> SSOUser:
        """Process SAML authentication response"""
        if provider_id not in self.saml_providers:
            raise HTTPException(status_code=404, detail="SAML provider not found")

        config = self.saml_providers[provider_id]

        # Build SAML settings (same as in get_saml_auth_url)
        saml_settings = {
            "sp": {
                "entityId": config["sp_entity_id"],
                "assertionConsumerService": {
                    "url": config["sp_acs_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
            },
            "idp": {
                "entityId": config["idp_entity_id"],
                "singleSignOnService": {
                    "url": config["idp_sso_url"],
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": config["idp_cert"],
            },
        }

        # Process response
        auth = OneLogin_Saml2_Auth({}, saml_settings)
        auth.process_response()

        if not auth.is_authenticated():
            raise HTTPException(
                status_code=401,
                detail=f"SAML authentication failed: {auth.get_last_error_reason()}",
            )

        attributes = auth.get_attributes()

        # Extract user info based on attribute mapping
        attr_map = config.get("attribute_mapping", {})

        email = attributes.get(attr_map.get("email", "email"), [None])[0]
        username = attributes.get(attr_map.get("username", "username"), [email])[0]
        full_name = attributes.get(attr_map.get("full_name", "name"), [None])[0]
        groups = attributes.get(attr_map.get("groups", "groups"), [])

        if not email:
            raise HTTPException(
                status_code=400, detail="Email attribute not found in SAML response"
            )

        return SSOUser(
            email=email,
            username=username or email,
            full_name=full_name,
            groups=groups,
            attributes=attributes,
            provider_id=provider_id,
            provider_user_id=auth.get_nameid(),
        )

    async def process_oidc_callback(
        self, provider_id: str, request: Request, authorization_code: str, state: str
    ) -> SSOUser:
        """Process OIDC authentication callback"""
        if provider_id not in self.oidc_providers:
            raise HTTPException(status_code=404, detail="OIDC provider not found")

        # Verify state
        if request.session.get("oauth_state") != state:
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        client = self.oauth.create_client(provider_id)
        redirect_uri = f"{request.base_url}auth/sso/oidc/{provider_id}/callback"

        # Exchange code for token
        token = await client.authorize_access_token(
            request=request, redirect_uri=redirect_uri, code=authorization_code
        )

        # Get user info
        user_info = token.get("userinfo")
        if not user_info:
            user_info = await client.parse_id_token(token)

        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=400, detail="Email not found in OIDC response"
            )

        return SSOUser(
            email=email,
            username=user_info.get("preferred_username", email),
            full_name=user_info.get("name"),
            groups=user_info.get("groups", []),
            attributes=user_info,
            provider_id=provider_id,
            provider_user_id=user_info.get("sub"),
        )

    def create_or_update_user(self, db: Session, sso_user: SSOUser) -> User:
        """Create or update user from SSO"""
        # Check if user exists
        user = db.query(User).filter(User.email == sso_user.email).first()

        if user:
            # Update existing user
            user.username = sso_user.username
            user.full_name = sso_user.full_name
            user.last_login = datetime.utcnow()

            # Update SSO attributes
            if not hasattr(user, "sso_provider"):
                user.sso_provider = sso_user.provider_id
            if not hasattr(user, "sso_user_id"):
                user.sso_user_id = sso_user.provider_user_id

            # Enterprise users get upgraded tier
            if user.subscription_tier == "free":
                user.subscription_tier = "starter"
                user.api_calls_limit = 10000  # Generous limit for SSO users

        else:
            # Create new user
            user = User(
                email=sso_user.email,
                username=sso_user.username,
                full_name=sso_user.full_name or sso_user.username,
                hashed_password="",  # No password for SSO users
                is_active=True,
                subscription_tier="starter",  # SSO users start with starter
                api_calls_limit=10000,
                api_calls_this_month=0,
                sso_provider=sso_user.provider_id,
                sso_user_id=sso_user.provider_user_id,
                last_login=datetime.utcnow(),
            )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def create_sso_token(self, user: User, provider_id: str) -> Token:
        """Create JWT token for SSO user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = AuthManager.create_access_token(
            data={
                "email": user.email,
                "user_id": user.id,
                "sso_provider": provider_id,
                "tier": user.subscription_tier,
            },
            expires_delta=access_token_expires,
        )

        refresh_token = AuthManager.create_refresh_token(
            data={"email": user.email, "user_id": user.id, "sso_provider": provider_id}
        )

        return Token(
            access_token=access_token, refresh_token=refresh_token, token_type="bearer"
        )


# Global instance
enterprise_auth = EnterpriseAuth()


# Dependency functions
async def get_sso_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current SSO user"""
    payload = AuthManager.decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    email = payload.get("email")
    sso_provider = payload.get("sso_provider")

    if not email or not sso_provider:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SSO token"
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


def check_enterprise_features(user: User):
    """Check if user has access to enterprise features"""
    enterprise_tiers = ["professional", "enterprise"]
    sso_tiers = [
        "starter",
        "professional",
        "enterprise",
    ]  # SSO users get enhanced access

    has_sso = hasattr(user, "sso_provider") and user.sso_provider
    has_enterprise_tier = user.subscription_tier in enterprise_tiers
    has_sso_tier = user.subscription_tier in sso_tiers

    return {
        "sso_enabled": has_sso,
        "enterprise_tier": has_enterprise_tier,
        "advanced_features": has_sso or has_enterprise_tier,
        "team_features": has_sso_tier,
        "unlimited_apis": user.subscription_tier in ["professional", "enterprise"],
        "priority_support": has_enterprise_tier,
        "custom_branding": user.subscription_tier == "enterprise",
    }


# Configuration helpers
def get_sso_providers() -> List[SSOProvider]:
    """Get all configured SSO providers"""
    providers = []

    # Add SAML providers
    for provider_id, config in enterprise_auth.saml_providers.items():
        providers.append(
            SSOProvider(
                id=provider_id,
                name=config["name"],
                type="saml",
                enabled=config.get("enabled", True),
                config=config,
                domains=config.get("domains", []),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    # Add OIDC providers
    for provider_id, config in enterprise_auth.oidc_providers.items():
        providers.append(
            SSOProvider(
                id=provider_id,
                name=config["name"],
                type="oidc",
                enabled=config.get("enabled", True),
                config=config,
                domains=config.get("domains", []),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

    return providers


def is_sso_required_for_domain(email: str) -> bool:
    """Check if SSO is required for email domain"""
    provider = enterprise_auth.get_provider_for_domain(email)
    return provider is not None and provider.config.get("enforce_sso", False)
