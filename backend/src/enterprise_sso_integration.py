#!/usr/bin/env python3
"""
Enterprise SSO Integration
Comprehensive single sign-on integration with multiple providers
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import base64
import secrets
import xml.etree.ElementTree as ET
from urllib.parse import urlencode


class SSOProvider(Enum):
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"
    PING_IDENTITY = "ping_identity"
    ONELOGIN = "onelogin"
    SAML_GENERIC = "saml_generic"
    OAUTH2_GENERIC = "oauth2_generic"


class AuthMethod(Enum):
    SAML2 = "saml2"
    OIDC = "oidc"
    OAUTH2 = "oauth2"
    LDAP = "ldap"


@dataclass
class SSOConfiguration:
    provider: SSOProvider
    auth_method: AuthMethod
    client_id: str
    client_secret: str
    metadata_url: Optional[str]
    redirect_uri: str
    scopes: List[str]
    additional_config: Dict[str, Any]


@dataclass
class UserProfile:
    user_id: str
    email: str
    first_name: str
    last_name: str
    groups: List[str]
    roles: List[str]
    organization: str
    metadata: Dict[str, Any]


@dataclass
class AuthSession:
    session_id: str
    user_profile: UserProfile
    access_token: str
    refresh_token: Optional[str]
    expires_at: datetime
    provider: SSOProvider


class EnterpriseSSOIntegration:
    """
    Enterprise-grade SSO integration supporting multiple providers and protocols
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # SSO configurations for different providers
        self.sso_configs: Dict[SSOProvider, SSOConfiguration] = {}

        # Active sessions
        self.active_sessions: Dict[str, AuthSession] = {}

        # Provider metadata cache
        self.provider_metadata: Dict[SSOProvider, Dict] = {}

        # SAML/OIDC configuration cache
        self.discovery_cache: Dict[str, Dict] = {}

    def configure_sso_provider(self, provider: SSOProvider, config: SSOConfiguration):
        """Configure an SSO provider"""
        self.sso_configs[provider] = config
        self.logger.info(f"✅ Configured SSO provider: {provider.value}")

    async def initialize_providers(self):
        """Initialize all configured SSO providers"""
        self.logger.info("🚀 Initializing Enterprise SSO Integration")

        # Configure popular enterprise providers with templates
        await self._setup_provider_templates()

        # Load provider metadata
        for provider in self.sso_configs:
            try:
                await self._load_provider_metadata(provider)
                self.logger.info(f"✅ Loaded metadata for {provider.value}")
            except Exception as e:
                self.logger.error(
                    f"❌ Failed to load metadata for {provider.value}: {e}"
                )

    async def _setup_provider_templates(self):
        """Setup templates for common enterprise SSO providers"""

        # Okta OIDC Template
        if SSOProvider.OKTA not in self.sso_configs:
            okta_config = SSOConfiguration(
                provider=SSOProvider.OKTA,
                auth_method=AuthMethod.OIDC,
                client_id="",  # To be configured
                client_secret="",
                metadata_url="https://{domain}.okta.com/.well-known/openid_configuration",
                redirect_uri="http://localhost:3000/auth/callback/okta",
                scopes=["openid", "profile", "email", "groups"],
                additional_config={
                    "domain": "",  # company.okta.com
                    "audience": "api://default",
                    "issuer": "https://{domain}.okta.com/oauth2/default",
                },
            )
            self.sso_configs[SSOProvider.OKTA] = okta_config

        # Azure AD OIDC Template
        if SSOProvider.AZURE_AD not in self.sso_configs:
            azure_config = SSOConfiguration(
                provider=SSOProvider.AZURE_AD,
                auth_method=AuthMethod.OIDC,
                client_id="",
                client_secret="",
                metadata_url="https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid_configuration",
                redirect_uri="http://localhost:3000/auth/callback/azure",
                scopes=["openid", "profile", "email", "User.Read"],
                additional_config={
                    "tenant_id": "",  # Your Azure AD tenant ID
                    "authority": "https://login.microsoftonline.com/{tenant}",
                    "graph_endpoint": "https://graph.microsoft.com/v1.0",
                },
            )
            self.sso_configs[SSOProvider.AZURE_AD] = azure_config

        # Google Workspace Template
        if SSOProvider.GOOGLE_WORKSPACE not in self.sso_configs:
            google_config = SSOConfiguration(
                provider=SSOProvider.GOOGLE_WORKSPACE,
                auth_method=AuthMethod.OAUTH2,
                client_id="",
                client_secret="",
                metadata_url="https://accounts.google.com/.well-known/openid_configuration",
                redirect_uri="http://localhost:3000/auth/callback/google",
                scopes=["openid", "email", "profile"],
                additional_config={
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "hd": "",  # Hosted domain for workspace
                },
            )
            self.sso_configs[SSOProvider.GOOGLE_WORKSPACE] = google_config

        # Generic SAML Template
        if SSOProvider.SAML_GENERIC not in self.sso_configs:
            saml_config = SSOConfiguration(
                provider=SSOProvider.SAML_GENERIC,
                auth_method=AuthMethod.SAML2,
                client_id="",  # Entity ID
                client_secret="",  # Certificate
                metadata_url="",  # IdP metadata URL
                redirect_uri="http://localhost:3000/auth/callback/saml",
                scopes=[],
                additional_config={
                    "entity_id": "http://localhost:3000/metadata",
                    "assertion_consumer_service": "http://localhost:3000/auth/callback/saml",
                    "single_logout_service": "http://localhost:3000/auth/logout/saml",
                    "name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                },
            )
            self.sso_configs[SSOProvider.SAML_GENERIC] = saml_config

    async def _load_provider_metadata(self, provider: SSOProvider):
        """Load metadata for an SSO provider"""
        config = self.sso_configs[provider]

        if not config.metadata_url:
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(config.metadata_url)

                if response.status_code == 200:
                    if config.auth_method in [AuthMethod.OIDC, AuthMethod.OAUTH2]:
                        # OIDC/OAuth2 metadata is JSON
                        metadata = response.json()
                    elif config.auth_method == AuthMethod.SAML2:
                        # SAML metadata is XML
                        metadata = self._parse_saml_metadata(response.text)

                    self.provider_metadata[provider] = metadata

        except Exception as e:
            self.logger.error(f"Failed to load metadata for {provider.value}: {e}")

    def _parse_saml_metadata(self, xml_content: str) -> Dict[str, Any]:
        """Parse SAML metadata XML"""
        try:
            root = ET.fromstring(xml_content)

            # Extract key SAML endpoints and configuration
            namespaces = {
                "md": "urn:oasis:names:tc:SAML:2.0:metadata",
                "ds": "http://www.w3.org/2000/09/xmldsig#",
            }

            metadata = {
                "entity_id": root.get("entityID"),
                "sso_bindings": [],
                "slo_bindings": [],
                "certificates": [],
            }

            # Find SSO endpoints
            for sso_service in root.findall(".//md:SingleSignOnService", namespaces):
                metadata["sso_bindings"].append(
                    {
                        "binding": sso_service.get("Binding"),
                        "location": sso_service.get("Location"),
                    }
                )

            # Find SLO endpoints
            for slo_service in root.findall(".//md:SingleLogoutService", namespaces):
                metadata["slo_bindings"].append(
                    {
                        "binding": slo_service.get("Binding"),
                        "location": slo_service.get("Location"),
                    }
                )

            # Extract certificates
            for cert in root.findall(".//ds:X509Certificate", namespaces):
                if cert.text:
                    metadata["certificates"].append(cert.text.strip())

            return metadata

        except Exception as e:
            self.logger.error(f"Failed to parse SAML metadata: {e}")
            return {}

    async def initiate_sso_login(
        self, provider: SSOProvider, state: Optional[str] = None
    ) -> str:
        """Initiate SSO login flow"""
        config = self.sso_configs.get(provider)
        if not config:
            raise ValueError(f"SSO provider {provider.value} not configured")

        if config.auth_method == AuthMethod.OIDC:
            return await self._initiate_oidc_login(config, state)
        elif config.auth_method == AuthMethod.OAUTH2:
            return await self._initiate_oauth2_login(config, state)
        elif config.auth_method == AuthMethod.SAML2:
            return await self._initiate_saml_login(config, state)
        else:
            raise ValueError(f"Unsupported auth method: {config.auth_method}")

    async def _initiate_oidc_login(
        self, config: SSOConfiguration, state: Optional[str]
    ) -> str:
        """Initiate OIDC login flow"""
        metadata = self.provider_metadata.get(config.provider, {})
        auth_endpoint = metadata.get("authorization_endpoint")

        if not auth_endpoint:
            # Fallback for common providers
            if config.provider == SSOProvider.OKTA:
                domain = config.additional_config.get("domain", "")
                auth_endpoint = f"https://{domain}.okta.com/oauth2/default/v1/authorize"
            elif config.provider == SSOProvider.AZURE_AD:
                tenant = config.additional_config.get("tenant_id", "")
                auth_endpoint = (
                    f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
                )

        # Generate state and nonce for security
        if not state:
            state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "redirect_uri": config.redirect_uri,
            "state": state,
            "nonce": nonce,
        }

        auth_url = f"{auth_endpoint}?{urlencode(params)}"

        # Store state for validation
        self.discovery_cache[state] = {
            "provider": config.provider,
            "nonce": nonce,
            "timestamp": datetime.now(),
        }

        return auth_url

    async def _initiate_oauth2_login(
        self, config: SSOConfiguration, state: Optional[str]
    ) -> str:
        """Initiate OAuth2 login flow"""
        auth_endpoint = config.additional_config.get("auth_uri")

        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "redirect_uri": config.redirect_uri,
            "state": state,
        }

        # Google Workspace specific
        if config.provider == SSOProvider.GOOGLE_WORKSPACE:
            hd = config.additional_config.get("hd")
            if hd:
                params["hd"] = hd

        auth_url = f"{auth_endpoint}?{urlencode(params)}"

        self.discovery_cache[state] = {
            "provider": config.provider,
            "timestamp": datetime.now(),
        }

        return auth_url

    async def _initiate_saml_login(
        self, config: SSOConfiguration, state: Optional[str]
    ) -> str:
        """Initiate SAML login flow"""
        # Generate SAML AuthnRequest
        request_id = f"id_{secrets.token_hex(16)}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        authn_request = f"""
        <samlp:AuthnRequest
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{timestamp}"
            Destination="{self._get_saml_sso_url(config.provider)}"
            AssertionConsumerServiceURL="{config.redirect_uri}">
            <saml:Issuer>{config.additional_config.get('entity_id')}</saml:Issuer>
            <samlp:NameIDPolicy Format="{config.additional_config.get('name_id_format')}" AllowCreate="true"/>
        </samlp:AuthnRequest>
        """

        # Base64 encode the request
        encoded_request = base64.b64encode(authn_request.encode()).decode()

        # Build redirect URL
        sso_url = self._get_saml_sso_url(config.provider)
        params = {"SAMLRequest": encoded_request, "RelayState": state or ""}

        return f"{sso_url}?{urlencode(params)}"

    def _get_saml_sso_url(self, provider: SSOProvider) -> str:
        """Get SAML SSO URL for provider"""
        metadata = self.provider_metadata.get(provider, {})

        for binding in metadata.get("sso_bindings", []):
            if "HTTP-Redirect" in binding.get("binding", ""):
                return binding.get("location", "")

        return ""

    async def handle_sso_callback(
        self,
        provider: SSOProvider,
        code: Optional[str] = None,
        state: Optional[str] = None,
        saml_response: Optional[str] = None,
    ) -> AuthSession:
        """Handle SSO callback and create user session"""
        config = self.sso_configs.get(provider)
        if not config:
            raise ValueError(f"SSO provider {provider.value} not configured")

        # Validate state
        if state and state in self.discovery_cache:
            cached_data = self.discovery_cache[state]
            if cached_data["provider"] != provider:
                raise ValueError("Invalid state parameter")
            del self.discovery_cache[state]

        if config.auth_method in [AuthMethod.OIDC, AuthMethod.OAUTH2]:
            return await self._handle_oidc_callback(config, code, state)
        elif config.auth_method == AuthMethod.SAML2:
            return await self._handle_saml_callback(config, saml_response)
        else:
            raise ValueError(f"Unsupported auth method: {config.auth_method}")

    async def _handle_oidc_callback(
        self, config: SSOConfiguration, code: str, state: str
    ) -> AuthSession:
        """Handle OIDC/OAuth2 callback"""
        # Exchange code for tokens
        token_endpoint = await self._get_token_endpoint(config)

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config.redirect_uri,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise ValueError(f"Token exchange failed: {response.text}")

            tokens = response.json()

        # Get user info
        user_profile = await self._get_user_profile(config, tokens["access_token"])

        # Create session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(seconds=tokens.get("expires_in", 3600))

        session = AuthSession(
            session_id=session_id,
            user_profile=user_profile,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_at=expires_at,
            provider=config.provider,
        )

        self.active_sessions[session_id] = session

        self.logger.info(
            f"✅ Created SSO session for {user_profile.email} via {config.provider.value}"
        )

        return session

    async def _handle_saml_callback(
        self, config: SSOConfiguration, saml_response: str
    ) -> AuthSession:
        """Handle SAML callback"""
        # Decode and parse SAML response
        decoded_response = base64.b64decode(saml_response).decode()

        # Parse SAML assertion (simplified - in production use proper SAML library)
        user_profile = self._parse_saml_assertion(decoded_response)

        # Create session
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=8)  # Default SAML session

        session = AuthSession(
            session_id=session_id,
            user_profile=user_profile,
            access_token="saml_session_" + session_id,
            refresh_token=None,
            expires_at=expires_at,
            provider=config.provider,
        )

        self.active_sessions[session_id] = session

        return session

    def _parse_saml_assertion(self, saml_response: str) -> UserProfile:
        """Parse SAML assertion to extract user profile"""
        try:
            root = ET.fromstring(saml_response)

            namespaces = {
                "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
                "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            }

            # Extract user attributes
            email = ""
            first_name = ""
            last_name = ""
            groups = []

            for attr in root.findall(".//saml:Attribute", namespaces):
                attr_name = attr.get("Name", "").lower()
                attr_value = attr.find(".//saml:AttributeValue", namespaces)

                if attr_value is not None and attr_value.text:
                    if "email" in attr_name:
                        email = attr_value.text
                    elif "firstname" in attr_name or "givenname" in attr_name:
                        first_name = attr_value.text
                    elif "lastname" in attr_name or "surname" in attr_name:
                        last_name = attr_value.text
                    elif "group" in attr_name or "role" in attr_name:
                        groups.append(attr_value.text)

            return UserProfile(
                user_id=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                groups=groups,
                roles=[],
                organization="",
                metadata={},
            )

        except Exception as e:
            self.logger.error(f"Failed to parse SAML assertion: {e}")
            raise ValueError("Invalid SAML response")

    async def _get_token_endpoint(self, config: SSOConfiguration) -> str:
        """Get token endpoint for provider"""
        metadata = self.provider_metadata.get(config.provider, {})
        token_endpoint = metadata.get("token_endpoint")

        if not token_endpoint:
            # Fallback endpoints
            if config.provider == SSOProvider.OKTA:
                domain = config.additional_config.get("domain", "")
                token_endpoint = f"https://{domain}.okta.com/oauth2/default/v1/token"
            elif config.provider == SSOProvider.AZURE_AD:
                tenant = config.additional_config.get("tenant_id", "")
                token_endpoint = (
                    f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
                )
            elif config.provider == SSOProvider.GOOGLE_WORKSPACE:
                token_endpoint = "https://oauth2.googleapis.com/token"

        return token_endpoint

    async def _get_user_profile(
        self, config: SSOConfiguration, access_token: str
    ) -> UserProfile:
        """Get user profile from provider"""
        user_info_endpoint = await self._get_userinfo_endpoint(config)

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(user_info_endpoint, headers=headers)

            if response.status_code != 200:
                raise ValueError(f"Failed to get user info: {response.text}")

            user_data = response.json()

        # Map provider-specific fields to standard profile
        return self._map_user_profile(config.provider, user_data)

    async def _get_userinfo_endpoint(self, config: SSOConfiguration) -> str:
        """Get user info endpoint for provider"""
        metadata = self.provider_metadata.get(config.provider, {})
        userinfo_endpoint = metadata.get("userinfo_endpoint")

        if not userinfo_endpoint:
            # Provider-specific endpoints
            if config.provider == SSOProvider.OKTA:
                domain = config.additional_config.get("domain", "")
                userinfo_endpoint = (
                    f"https://{domain}.okta.com/oauth2/default/v1/userinfo"
                )
            elif config.provider == SSOProvider.AZURE_AD:
                userinfo_endpoint = "https://graph.microsoft.com/v1.0/me"
            elif config.provider == SSOProvider.GOOGLE_WORKSPACE:
                userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"

        return userinfo_endpoint

    def _map_user_profile(
        self, provider: SSOProvider, user_data: Dict[str, Any]
    ) -> UserProfile:
        """Map provider-specific user data to standard profile"""
        if provider == SSOProvider.OKTA:
            return UserProfile(
                user_id=user_data.get("sub", ""),
                email=user_data.get("email", ""),
                first_name=user_data.get("given_name", ""),
                last_name=user_data.get("family_name", ""),
                groups=user_data.get("groups", []),
                roles=[],
                organization=user_data.get("org", ""),
                metadata=user_data,
            )
        elif provider == SSOProvider.AZURE_AD:
            return UserProfile(
                user_id=user_data.get("id", ""),
                email=user_data.get("mail", user_data.get("userPrincipalName", "")),
                first_name=user_data.get("givenName", ""),
                last_name=user_data.get("surname", ""),
                groups=[],  # Requires additional Graph API call
                roles=[],
                organization=user_data.get("companyName", ""),
                metadata=user_data,
            )
        elif provider == SSOProvider.GOOGLE_WORKSPACE:
            return UserProfile(
                user_id=user_data.get("sub", ""),
                email=user_data.get("email", ""),
                first_name=user_data.get("given_name", ""),
                last_name=user_data.get("family_name", ""),
                groups=[],
                roles=[],
                organization=user_data.get("hd", ""),
                metadata=user_data,
            )
        else:
            # Generic mapping
            return UserProfile(
                user_id=user_data.get("sub", user_data.get("id", "")),
                email=user_data.get("email", ""),
                first_name=user_data.get("given_name", user_data.get("firstName", "")),
                last_name=user_data.get("family_name", user_data.get("lastName", "")),
                groups=user_data.get("groups", []),
                roles=user_data.get("roles", []),
                organization=user_data.get("organization", ""),
                metadata=user_data,
            )

    def get_session(self, session_id: str) -> Optional[AuthSession]:
        """Get active session by ID"""
        session = self.active_sessions.get(session_id)

        if session and session.expires_at > datetime.now():
            return session
        elif session:
            # Session expired, remove it
            del self.active_sessions[session_id]

        return None

    async def refresh_session(self, session_id: str) -> Optional[AuthSession]:
        """Refresh an expired session using refresh token"""
        session = self.active_sessions.get(session_id)

        if not session or not session.refresh_token:
            return None

        config = self.sso_configs.get(session.provider)
        if not config:
            return None

        try:
            token_endpoint = await self._get_token_endpoint(config)

            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": session.refresh_token,
                "client_id": config.client_id,
                "client_secret": config.client_secret,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    token_endpoint,
                    data=refresh_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code != 200:
                    return None

                tokens = response.json()

            # Update session
            session.access_token = tokens["access_token"]
            session.expires_at = datetime.now() + timedelta(
                seconds=tokens.get("expires_in", 3600)
            )

            if "refresh_token" in tokens:
                session.refresh_token = tokens["refresh_token"]

            return session

        except Exception as e:
            self.logger.error(f"Failed to refresh session: {e}")
            return None

    async def logout_session(self, session_id: str):
        """Logout and invalidate session"""
        session = self.active_sessions.get(session_id)

        if session:
            # Remove local session
            del self.active_sessions[session_id]

            # Attempt SSO logout if supported
            config = self.sso_configs.get(session.provider)
            if config:
                await self._initiate_sso_logout(config, session)

    async def _initiate_sso_logout(
        self, config: SSOConfiguration, session: AuthSession
    ):
        """Initiate SSO logout with provider"""
        try:
            if config.auth_method == AuthMethod.SAML2:
                # SAML logout
                await self._saml_logout(config, session)
            else:
                # OIDC/OAuth2 logout
                await self._oidc_logout(config, session)
        except Exception as e:
            self.logger.error(f"SSO logout failed: {e}")

    async def _oidc_logout(self, config: SSOConfiguration, session: AuthSession):
        """Perform OIDC logout"""
        metadata = self.provider_metadata.get(config.provider, {})
        logout_endpoint = metadata.get("end_session_endpoint")

        if logout_endpoint:
            params = {
                "id_token_hint": session.access_token,
                "post_logout_redirect_uri": config.redirect_uri,
            }

            logout_url = f"{logout_endpoint}?{urlencode(params)}"

            # In a real implementation, redirect user to logout_url
            self.logger.info(f"OIDC logout URL: {logout_url}")

    async def _saml_logout(self, config: SSOConfiguration, session: AuthSession):
        """Perform SAML logout"""
        # Generate SAML LogoutRequest
        request_id = f"logout_{secrets.token_hex(16)}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        logout_request = f"""
        <samlp:LogoutRequest
            xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
            ID="{request_id}"
            Version="2.0"
            IssueInstant="{timestamp}">
            <saml:Issuer>{config.additional_config.get('entity_id')}</saml:Issuer>
            <saml:NameID Format="{config.additional_config.get('name_id_format')}">{session.user_profile.email}</saml:NameID>
        </samlp:LogoutRequest>
        """

        # In a real implementation, send this to the IdP
        self.logger.info(
            f"SAML logout request generated for {session.user_profile.email}"
        )

    def get_provider_configuration_template(
        self, provider: SSOProvider
    ) -> Dict[str, Any]:
        """Get configuration template for a provider"""
        templates = {
            SSOProvider.OKTA: {
                "client_id": "0oa1234567890abcdef",
                "client_secret": "your_okta_client_secret",
                "domain": "your-company.okta.com",
                "metadata_url": "https://your-company.okta.com/.well-known/openid_configuration",
                "redirect_uri": "http://localhost:3000/auth/callback/okta",
                "scopes": ["openid", "profile", "email", "groups"],
            },
            SSOProvider.AZURE_AD: {
                "client_id": "12345678-1234-1234-1234-123456789012",
                "client_secret": "your_azure_client_secret",
                "tenant_id": "87654321-4321-4321-4321-210987654321",
                "metadata_url": "https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid_configuration",
                "redirect_uri": "http://localhost:3000/auth/callback/azure",
                "scopes": ["openid", "profile", "email", "User.Read"],
            },
            SSOProvider.GOOGLE_WORKSPACE: {
                "client_id": "123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com",
                "client_secret": "your_google_client_secret",
                "hosted_domain": "your-company.com",
                "metadata_url": "https://accounts.google.com/.well-known/openid_configuration",
                "redirect_uri": "http://localhost:3000/auth/callback/google",
                "scopes": ["openid", "email", "profile"],
            },
        }

        return templates.get(provider, {})

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current SSO integration status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "configured_providers": [p.value for p in self.sso_configs.keys()],
            "active_sessions": len(self.active_sessions),
            "provider_metadata_loaded": [
                p.value for p in self.provider_metadata.keys()
            ],
            "supported_providers": [p.value for p in SSOProvider],
            "supported_auth_methods": [m.value for m in AuthMethod],
        }


# Global SSO integration instance
enterprise_sso = EnterpriseSSOIntegration()


async def initialize_enterprise_sso():
    """Initialize the enterprise SSO integration"""
    await enterprise_sso.initialize_providers()


def get_sso_status():
    """Get current SSO integration status"""
    return enterprise_sso.get_integration_status()
