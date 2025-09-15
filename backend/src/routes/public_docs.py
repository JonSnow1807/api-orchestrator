"""
Public API Documentation Routes
Handles public documentation hosting with custom domains
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, List, Any
import os
import json
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
import hashlib
import asyncio
from pathlib import Path

from src.database import get_db, Project, User
from src.auth import get_current_user
from src.public_docs_generator import PublicDocumentation, DocumentationGenerator

router = APIRouter(prefix="/api/docs", tags=["Public Documentation"])

class PublicDocsRequest(BaseModel):
    """Request to create/update public documentation"""
    project_id: int
    title: str
    description: Optional[str] = None
    version: str = "1.0.0"
    base_url: Optional[HttpUrl] = None
    theme: str = "modern"
    logo_url: Optional[HttpUrl] = None
    custom_domain: Optional[str] = None
    openapi_spec: Optional[Dict[str, Any]] = None
    getting_started: Optional[str] = None
    auth_description: Optional[str] = None
    code_examples: Optional[Dict[str, Any]] = None

class PublicDocsResponse(BaseModel):
    """Response for public documentation"""
    id: int
    project_id: int
    title: str
    description: Optional[str]
    version: str
    public_url: str
    custom_domain: Optional[str]
    theme: str
    is_public: bool
    created_at: str
    updated_at: str

class DocsHostingConfig(BaseModel):
    """Documentation hosting configuration"""
    subdomain: str
    custom_domain: Optional[str] = None
    ssl_enabled: bool = True
    password_protected: bool = False
    password: Optional[str] = None
    analytics_id: Optional[str] = None
    seo_enabled: bool = True

@router.post("/public", response_model=PublicDocsResponse)
async def create_public_docs(
    docs_request: PublicDocsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update public API documentation"""
    try:
        # Verify user owns the project
        project = db.query(Project).filter(
            Project.id == docs_request.project_id,
            Project.user_id == current_user.id
        ).first()

        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )

        # Generate subdomain if not specified
        subdomain = f"{project.name.lower().replace(' ', '-')}-{current_user.id}"

        # Check if documentation already exists
        existing_docs = db.query(PublicDocumentation).filter(
            PublicDocumentation.project_id == docs_request.project_id
        ).first()

        if existing_docs:
            # Update existing documentation
            existing_docs.title = docs_request.title
            existing_docs.description = docs_request.description
            existing_docs.version = docs_request.version
            existing_docs.base_url = str(docs_request.base_url) if docs_request.base_url else None
            existing_docs.theme = docs_request.theme
            existing_docs.logo_url = str(docs_request.logo_url) if docs_request.logo_url else None
            existing_docs.openapi_spec = docs_request.openapi_spec
            existing_docs.getting_started = docs_request.getting_started
            existing_docs.auth_description = docs_request.auth_description
            existing_docs.code_examples = docs_request.code_examples
            existing_docs.updated_at = datetime.utcnow()

            docs = existing_docs
        else:
            # Create new documentation
            docs = PublicDocumentation(
                project_id=docs_request.project_id,
                title=docs_request.title,
                description=docs_request.description,
                version=docs_request.version,
                base_url=str(docs_request.base_url) if docs_request.base_url else None,
                theme=docs_request.theme,
                logo_url=str(docs_request.logo_url) if docs_request.logo_url else None,
                subdomain=subdomain,
                custom_domain=docs_request.custom_domain,
                openapi_spec=docs_request.openapi_spec,
                getting_started=docs_request.getting_started,
                auth_description=docs_request.auth_description,
                code_examples=docs_request.code_examples,
                is_public=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(docs)

        db.commit()
        db.refresh(docs)

        # Generate static documentation files
        await generate_static_docs(docs, db)

        public_url = f"https://docs.streamapi.dev/{docs.subdomain}"
        if docs.custom_domain:
            public_url = f"https://{docs.custom_domain}"

        return PublicDocsResponse(
            id=docs.id,
            project_id=docs.project_id,
            title=docs.title,
            description=docs.description,
            version=docs.version,
            public_url=public_url,
            custom_domain=docs.custom_domain,
            theme=docs.theme,
            is_public=docs.is_public,
            created_at=docs.created_at.isoformat(),
            updated_at=docs.updated_at.isoformat()
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create public documentation: {str(e)}"
        )

@router.get("/public/{project_id}", response_model=PublicDocsResponse)
async def get_public_docs(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get public documentation for a project"""
    docs = db.query(PublicDocumentation).filter(
        PublicDocumentation.project_id == project_id
    ).first()

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="Public documentation not found"
        )

    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    public_url = f"https://docs.streamapi.dev/{docs.subdomain}"
    if docs.custom_domain:
        public_url = f"https://{docs.custom_domain}"

    return PublicDocsResponse(
        id=docs.id,
        project_id=docs.project_id,
        title=docs.title,
        description=docs.description,
        version=docs.version,
        public_url=public_url,
        custom_domain=docs.custom_domain,
        theme=docs.theme,
        is_public=docs.is_public,
        created_at=docs.created_at.isoformat(),
        updated_at=docs.updated_at.isoformat()
    )

@router.delete("/public/{project_id}")
async def delete_public_docs(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete public documentation for a project"""
    # Verify user owns the project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    docs = db.query(PublicDocumentation).filter(
        PublicDocumentation.project_id == project_id
    ).first()

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="Public documentation not found"
        )

    # Remove static files
    await cleanup_static_docs(docs.subdomain)

    db.delete(docs)
    db.commit()

    return {"message": "Public documentation deleted successfully"}

@router.get("/hosted/{subdomain}", response_class=HTMLResponse)
async def serve_public_docs(
    subdomain: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Serve public documentation via subdomain"""
    # Find documentation by subdomain
    docs = db.query(PublicDocumentation).filter(
        PublicDocumentation.subdomain == subdomain,
        PublicDocumentation.is_public == True
    ).first()

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="Documentation not found"
        )

    # Check if custom domain is configured
    host = request.headers.get("host", "").lower()
    if docs.custom_domain and host != docs.custom_domain:
        # Redirect to custom domain
        return RedirectResponse(
            url=f"https://{docs.custom_domain}",
            status_code=301
        )

    # Generate and serve documentation HTML
    html_content = await render_documentation(docs, request)

    return HTMLResponse(
        content=html_content,
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Frame-Options": "SAMEORIGIN",
            "X-Content-Type-Options": "nosniff"
        }
    )

@router.get("/hosted/{subdomain}/openapi.json")
async def serve_openapi_spec(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """Serve OpenAPI specification"""
    docs = db.query(PublicDocumentation).filter(
        PublicDocumentation.subdomain == subdomain,
        PublicDocumentation.is_public == True
    ).first()

    if not docs or not docs.openapi_spec:
        raise HTTPException(
            status_code=404,
            detail="OpenAPI specification not found"
        )

    return Response(
        content=json.dumps(docs.openapi_spec, indent=2),
        media_type="application/json",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.post("/preview")
async def preview_docs(
    docs_request: PublicDocsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Preview documentation without publishing"""
    try:
        # Create temporary docs object for preview
        temp_docs = PublicDocumentation(
            project_id=docs_request.project_id,
            title=docs_request.title,
            description=docs_request.description,
            version=docs_request.version,
            base_url=str(docs_request.base_url) if docs_request.base_url else None,
            theme=docs_request.theme,
            logo_url=str(docs_request.logo_url) if docs_request.logo_url else None,
            openapi_spec=docs_request.openapi_spec,
            getting_started=docs_request.getting_started,
            auth_description=docs_request.auth_description,
            code_examples=docs_request.code_examples
        )

        # Generate preview HTML
        generator = DocumentationGenerator()
        html_content = generator.generate_html_docs(temp_docs)

        return {
            "preview_html": html_content,
            "estimated_size": len(html_content.encode('utf-8')),
            "seo_score": calculate_seo_score(temp_docs),
            "performance_score": calculate_performance_score(html_content)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )

@router.get("/analytics/{subdomain}")
async def get_docs_analytics(
    subdomain: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for public documentation"""
    docs = db.query(PublicDocumentation).filter(
        PublicDocumentation.subdomain == subdomain
    ).first()

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="Documentation not found"
        )

    # Verify ownership
    project = db.query(Project).filter(
        Project.id == docs.project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    # Get analytics data (placeholder - integrate with real analytics)
    analytics_data = {
        "page_views": 1234,
        "unique_visitors": 567,
        "top_pages": [
            {"path": "/", "views": 456},
            {"path": "/endpoints", "views": 234},
            {"path": "/authentication", "views": 123}
        ],
        "referrers": [
            {"source": "google.com", "visits": 123},
            {"source": "github.com", "visits": 89},
            {"source": "direct", "visits": 345}
        ],
        "countries": [
            {"country": "United States", "visits": 234},
            {"country": "United Kingdom", "visits": 123},
            {"country": "Germany", "visits": 89}
        ],
        "period": "last_30_days"
    }

    return analytics_data

# Helper functions

async def generate_static_docs(docs: PublicDocumentation, db: Session):
    """Generate static documentation files for hosting"""
    try:
        generator = DocumentationGenerator()

        # Generate HTML
        html_content = generator.generate_html_docs(docs)

        # Create directory for static files
        docs_dir = Path(f"/app/static/docs/{docs.subdomain}")
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        (docs_dir / "index.html").write_text(html_content, encoding='utf-8')

        # Generate additional files
        if docs.openapi_spec:
            (docs_dir / "openapi.json").write_text(
                json.dumps(docs.openapi_spec, indent=2),
                encoding='utf-8'
            )

        # Generate sitemap
        sitemap_content = generator.generate_sitemap(docs)
        (docs_dir / "sitemap.xml").write_text(sitemap_content, encoding='utf-8')

        # Generate robots.txt
        robots_content = generator.generate_robots_txt(docs)
        (docs_dir / "robots.txt").write_text(robots_content, encoding='utf-8')

    except Exception as e:
        print(f"Error generating static docs: {e}")

async def cleanup_static_docs(subdomain: str):
    """Remove static documentation files"""
    try:
        import shutil
        docs_dir = Path(f"/app/static/docs/{subdomain}")
        if docs_dir.exists():
            shutil.rmtree(docs_dir)
    except Exception as e:
        print(f"Error cleaning up static docs: {e}")

async def render_documentation(docs: PublicDocumentation, request: Request) -> str:
    """Render documentation HTML"""
    try:
        generator = DocumentationGenerator()
        html_content = generator.generate_html_docs(docs)

        # Add analytics if configured
        if docs.analytics_id:
            analytics_code = f"""
            <script async src="https://www.googletagmanager.com/gtag/js?id={docs.analytics_id}"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){{dataLayer.push(arguments);}}
              gtag('js', new Date());
              gtag('config', '{docs.analytics_id}');
            </script>
            """
            html_content = html_content.replace("</head>", f"{analytics_code}</head>")

        return html_content

    except Exception as e:
        return f"<html><body><h1>Error loading documentation</h1><p>{str(e)}</p></body></html>"

def calculate_seo_score(docs: PublicDocumentation) -> int:
    """Calculate SEO score for documentation"""
    score = 0

    # Title check
    if docs.title and len(docs.title) >= 10:
        score += 20

    # Description check
    if docs.description and len(docs.description) >= 50:
        score += 20

    # OpenAPI spec check
    if docs.openapi_spec:
        score += 20

    # Getting started check
    if docs.getting_started:
        score += 20

    # Logo/branding check
    if docs.logo_url:
        score += 10

    # Custom domain check
    if docs.custom_domain:
        score += 10

    return min(score, 100)

def calculate_performance_score(html_content: str) -> int:
    """Calculate performance score for documentation"""
    score = 100

    # Size penalty
    size_kb = len(html_content.encode('utf-8')) / 1024
    if size_kb > 100:
        score -= min(30, (size_kb - 100) / 10)

    # External resources penalty
    external_resources = html_content.count('http://') + html_content.count('https://')
    score -= min(20, external_resources * 2)

    return max(int(score), 0)