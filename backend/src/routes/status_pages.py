"""
Status Pages API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import uuid

from src.database import get_db
from src.auth import get_current_user
from src.health_monitoring import HealthMonitor, StatusPage, ServiceStatus

router = APIRouter(prefix="/api/status-pages", tags=["Status Pages"])

# Global health monitor instance
health_monitor = HealthMonitor()

class StatusPageRequest(BaseModel):
    """Request model for creating status page"""
    name: str
    slug: str
    description: Optional[str] = None
    services: List[Dict[str, Any]]
    is_public: bool = True
    show_uptime_history: bool = True
    show_incident_timeline: bool = True
    show_response_times: bool = True
    custom_domain: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#8B5CF6"
    project_id: Optional[int] = None

@router.post("/create")
async def create_status_page(
    request: StatusPageRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new status page"""
    
    # Check if slug already exists
    existing = db.query(StatusPage).filter(StatusPage.slug == request.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Create status page
    status_page = StatusPage(
        name=request.name,
        slug=request.slug,
        description=request.description,
        services=request.services,
        is_public=request.is_public,
        show_uptime_history=request.show_uptime_history,
        show_incident_timeline=request.show_incident_timeline,
        show_response_times=request.show_response_times,
        custom_domain=request.custom_domain,
        logo_url=request.logo_url,
        primary_color=request.primary_color,
        project_id=request.project_id
    )
    
    db.add(status_page)
    db.commit()
    db.refresh(status_page)
    
    # Start monitoring in background
    monitor_id = f"status_page_{status_page.id}"
    
    async def start_monitoring():
        await health_monitor.start_monitoring(
            monitor_id=monitor_id,
            endpoints=request.services,
            interval_seconds=60
        )
    
    background_tasks.add_task(start_monitoring)
    
    return {
        "success": True,
        "status_page": {
            "id": status_page.id,
            "name": status_page.name,
            "slug": status_page.slug,
            "url": f"/status/{status_page.slug}",
            "monitoring_started": True
        }
    }

@router.get("/list")
async def list_status_pages(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all status pages for current user"""
    
    pages = db.query(StatusPage).all()
    
    return {
        "success": True,
        "status_pages": [
            {
                "id": page.id,
                "name": page.name,
                "slug": page.slug,
                "url": f"/status/{page.slug}",
                "is_public": page.is_public,
                "services_count": len(page.services) if page.services else 0,
                "created_at": page.created_at
            }
            for page in pages
        ]
    }

@router.get("/{page_id}")
async def get_status_page_config(
    page_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get status page configuration"""
    
    page = db.query(StatusPage).filter(StatusPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")
    
    return {
        "success": True,
        "status_page": {
            "id": page.id,
            "name": page.name,
            "slug": page.slug,
            "description": page.description,
            "services": page.services,
            "is_public": page.is_public,
            "show_uptime_history": page.show_uptime_history,
            "show_incident_timeline": page.show_incident_timeline,
            "show_response_times": page.show_response_times,
            "custom_domain": page.custom_domain,
            "logo_url": page.logo_url,
            "primary_color": page.primary_color
        }
    }

@router.get("/{page_id}/health")
async def get_status_page_health(
    page_id: int,
    db: Session = Depends(get_db)
):
    """Get current health status for status page"""
    
    page = db.query(StatusPage).filter(StatusPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")
    
    monitor_id = f"status_page_{page_id}"
    
    # Get health for each service
    services_health = []
    overall_status = ServiceStatus.OPERATIONAL
    
    if page.services:
        for service in page.services:
            # Get health from monitor
            health = health_monitor.get_service_health(monitor_id)
            
            if health:
                services_health.append({
                    "name": service.get("name", service.get("url")),
                    "status": health.status.value,
                    "uptime": health.uptime_percentage,
                    "response_time": health.avg_response_time_ms,
                    "last_check": health.last_check,
                    "incidents_today": health.incidents_today
                })
                
                # Update overall status
                if health.status == ServiceStatus.MAJOR_OUTAGE:
                    overall_status = ServiceStatus.MAJOR_OUTAGE
                elif health.status == ServiceStatus.PARTIAL_OUTAGE and overall_status != ServiceStatus.MAJOR_OUTAGE:
                    overall_status = ServiceStatus.PARTIAL_OUTAGE
                elif health.status == ServiceStatus.DEGRADED and overall_status == ServiceStatus.OPERATIONAL:
                    overall_status = ServiceStatus.DEGRADED
            else:
                services_health.append({
                    "name": service.get("name", service.get("url")),
                    "status": "unknown",
                    "uptime": 0,
                    "response_time": 0,
                    "last_check": None,
                    "incidents_today": 0
                })
    
    # Get uptime history
    uptime_history = health_monitor.get_uptime_history(monitor_id, days=90)
    
    # Get incident timeline
    incidents = health_monitor.get_incident_timeline(monitor_id)
    
    return {
        "success": True,
        "page_info": {
            "name": page.name,
            "description": page.description,
            "logo_url": page.logo_url,
            "primary_color": page.primary_color
        },
        "overall_status": overall_status.value,
        "services": services_health,
        "uptime_history": uptime_history if page.show_uptime_history else [],
        "incidents": incidents if page.show_incident_timeline else [],
        "show_response_times": page.show_response_times
    }

@router.put("/{page_id}")
async def update_status_page(
    page_id: int,
    request: StatusPageRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update status page configuration"""
    
    page = db.query(StatusPage).filter(StatusPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")
    
    # Update fields
    page.name = request.name
    page.description = request.description
    page.services = request.services
    page.is_public = request.is_public
    page.show_uptime_history = request.show_uptime_history
    page.show_incident_timeline = request.show_incident_timeline
    page.show_response_times = request.show_response_times
    page.custom_domain = request.custom_domain
    page.logo_url = request.logo_url
    page.primary_color = request.primary_color
    
    db.commit()
    
    # Restart monitoring with new services
    monitor_id = f"status_page_{page_id}"
    health_monitor.stop_monitoring(monitor_id)
    
    # Start new monitoring
    asyncio.create_task(health_monitor.start_monitoring(
        monitor_id=monitor_id,
        endpoints=request.services,
        interval_seconds=60
    ))
    
    return {
        "success": True,
        "message": "Status page updated successfully"
    }

@router.delete("/{page_id}")
async def delete_status_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a status page"""
    
    page = db.query(StatusPage).filter(StatusPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")
    
    # Stop monitoring
    monitor_id = f"status_page_{page_id}"
    health_monitor.stop_monitoring(monitor_id)
    
    # Delete from database
    db.delete(page)
    db.commit()
    
    return {
        "success": True,
        "message": "Status page deleted successfully"
    }

@router.get("/public/{slug}")
async def get_public_status_page(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get public status page (no auth required)"""
    
    page = db.query(StatusPage).filter(
        StatusPage.slug == slug,
        StatusPage.is_public == True
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Status page not found")
    
    # Get health data
    page_id = page.id
    monitor_id = f"status_page_{page_id}"
    
    services_health = []
    overall_status = ServiceStatus.OPERATIONAL
    
    if page.services:
        for service in page.services:
            health = health_monitor.get_service_health(monitor_id)
            
            if health:
                services_health.append({
                    "name": service.get("name", service.get("url")),
                    "status": health.status.value,
                    "uptime": health.uptime_percentage,
                    "response_time": health.avg_response_time_ms if page.show_response_times else None
                })
                
                if health.status.value != "operational":
                    overall_status = health.status
    
    return {
        "success": True,
        "page": {
            "name": page.name,
            "description": page.description,
            "logo_url": page.logo_url,
            "primary_color": page.primary_color,
            "overall_status": overall_status.value,
            "services": services_health,
            "uptime_history": health_monitor.get_uptime_history(monitor_id, 90) if page.show_uptime_history else None,
            "incidents": health_monitor.get_incident_timeline(monitor_id) if page.show_incident_timeline else None
        }
    }

# Import asyncio for background tasks
import asyncio