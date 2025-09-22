"""
Enterprise SSO Routes for API Orchestrator
Handles SAML 2.0 and OIDC authentication flows
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import logging

from src.database import get_db, User
from src.enterprise_sso import (
    enterprise_auth,
    get_sso_user,
    check_enterprise_features,
    get_sso_providers,
    is_sso_required_for_domain,
    SSOProvider,
)
from src.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth/sso", tags=["Enterprise SSO"])


class SSODiscoveryRequest(BaseModel):
    email: EmailStr


class SSODiscoveryResponse(BaseModel):
    sso_required: bool
    provider: Optional[SSOProvider] = None
    auth_url: Optional[str] = None


class SSOProviderResponse(BaseModel):
    providers: List[SSOProvider]


class EnterpriseStatusResponse(BaseModel):
    is_enterprise_user: bool
    sso_provider: Optional[str] = None
    features: dict


@router.post("/discover", response_model=SSODiscoveryResponse)
async def discover_sso_provider(
    discovery_request: SSODiscoveryRequest, request: Request
):
    """
    Discover SSO provider for email domain
    Returns SSO configuration and auth URL if available
    """
    try:
        email = discovery_request.email

        # Check if SSO is configured for this domain
        provider = enterprise_auth.get_provider_for_domain(email)

        if not provider:
            return SSODiscoveryResponse(
                sso_required=False, provider=None, auth_url=None
            )

        # Generate auth URL based on provider type
        auth_url = None
        if provider.type == "saml":
            return_to = str(
                request.url_for("sso_saml_callback", provider_id=provider.id)
            )
            auth_url = enterprise_auth.get_saml_auth_url(provider.id, return_to)
        elif provider.type == "oidc":
            auth_url = enterprise_auth.get_oidc_auth_url(provider.id, request)

        return SSODiscoveryResponse(
            sso_required=is_sso_required_for_domain(email),
            provider=provider,
            auth_url=auth_url,
        )

    except Exception as e:
        logger.error(f"SSO discovery error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover SSO provider",
        )


@router.get("/providers", response_model=SSOProviderResponse)
async def list_sso_providers(current_user: User = Depends(get_current_user)):
    """List all configured SSO providers"""
    try:
        providers = get_sso_providers()
        return SSOProviderResponse(providers=providers)
    except Exception as e:
        logger.error(f"Failed to list SSO providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve SSO providers",
        )


@router.get("/saml/{provider_id}/login")
async def sso_saml_login(
    provider_id: str, request: Request, return_to: Optional[str] = None
):
    """Initiate SAML SSO login"""
    try:
        auth_url = enterprise_auth.get_saml_auth_url(provider_id, return_to)
        return RedirectResponse(url=auth_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAML login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate SAML login",
        )


@router.post("/saml/{provider_id}/acs", name="sso_saml_callback")
async def sso_saml_callback(
    provider_id: str,
    request: Request,
    response: Response,
    SAMLResponse: str = Form(...),
    RelayState: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Handle SAML Assertion Consumer Service (ACS) callback"""
    try:
        # Process SAML response
        sso_user = enterprise_auth.process_saml_response(provider_id, SAMLResponse)

        # Create or update user
        user = enterprise_auth.create_or_update_user(db, sso_user)

        # Generate JWT token
        token = enterprise_auth.create_sso_token(user, provider_id)

        # Set secure cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token.access_token}",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400,  # 24 hours
        )

        # Redirect to dashboard or RelayState URL
        redirect_url = RelayState or "/dashboard"
        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAML callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SAML authentication failed",
        )


@router.get("/oidc/{provider_id}/login")
async def sso_oidc_login(
    provider_id: str, request: Request, return_to: Optional[str] = None
):
    """Initiate OIDC/OAuth2 login"""
    try:
        auth_url = enterprise_auth.get_oidc_auth_url(provider_id, request, return_to)
        return RedirectResponse(url=auth_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OIDC login",
        )


@router.get("/oidc/{provider_id}/callback", name="sso_oidc_callback")
async def sso_oidc_callback(
    provider_id: str,
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """Handle OIDC/OAuth2 callback"""
    try:
        # Process OIDC response
        sso_user = await enterprise_auth.process_oidc_callback(
            provider_id, request, code, state
        )

        # Create or update user
        user = enterprise_auth.create_or_update_user(db, sso_user)

        # Generate JWT token
        token = enterprise_auth.create_sso_token(user, provider_id)

        # Set secure cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {token.access_token}",
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400,  # 24 hours
        )

        # Redirect to return_to URL or dashboard
        return_to = request.session.get("oauth_return_to", "/dashboard")
        return RedirectResponse(url=return_to, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC authentication failed",
        )


@router.get("/status", response_model=EnterpriseStatusResponse)
async def get_enterprise_status(current_user: User = Depends(get_current_user)):
    """Get current user's enterprise/SSO status"""
    try:
        is_enterprise = (
            hasattr(current_user, "sso_provider") and current_user.sso_provider
        )
        features = check_enterprise_features(current_user)

        return EnterpriseStatusResponse(
            is_enterprise_user=is_enterprise,
            sso_provider=getattr(current_user, "sso_provider", None),
            features=features,
        )
    except Exception as e:
        logger.error(f"Enterprise status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get enterprise status",
        )


@router.post("/logout")
async def sso_logout(response: Response, current_user: User = Depends(get_sso_user)):
    """Logout SSO user"""
    try:
        # Clear cookies
        response.delete_cookie("access_token")

        # For SAML, we should ideally initiate SLO (Single Logout)
        # For now, just clear the local session

        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"SSO logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed"
        )


@router.get("/metadata/{provider_id}")
async def get_saml_metadata(provider_id: str):
    """Get SAML metadata for SP configuration"""
    try:
        if provider_id not in enterprise_auth.saml_providers:
            raise HTTPException(status_code=404, detail="SAML provider not found")

        config = enterprise_auth.saml_providers[provider_id]

        metadata_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{config['sp_entity_id']}">
    <md:SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{config['sp_acs_url']}"
            index="1"/>
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

        return Response(
            content=metadata_xml,
            media_type="application/samlmetadata+xml",
            headers={
                "Content-Disposition": f"attachment; filename={provider_id}-metadata.xml"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAML metadata error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate SAML metadata",
        )
