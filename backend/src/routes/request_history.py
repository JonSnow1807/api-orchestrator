"""
Request History Search and Management API
Provides powerful search capabilities for API request history
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from src.database import get_db, RequestHistory, User
from src.auth import AuthManager

router = APIRouter(prefix="/api/request-history", tags=["Request History"])

class RequestHistorySearch(BaseModel):
    """Search parameters for request history"""
    query: Optional[str] = None  # Full-text search across url, name, notes
    method: Optional[List[str]] = None  # Filter by HTTP methods
    status_codes: Optional[List[int]] = None  # Filter by status codes
    min_response_time: Optional[int] = None  # Minimum response time in ms
    max_response_time: Optional[int] = None  # Maximum response time in ms
    project_id: Optional[int] = None
    collection_id: Optional[str] = None
    tags: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    success_only: Optional[bool] = None
    
class SavedSearch(BaseModel):
    """Saved search/smart folder"""
    name: str
    description: Optional[str] = None
    search_params: RequestHistorySearch
    is_public: bool = False

class RequestHistoryResponse(BaseModel):
    """Response model for request history"""
    id: int
    method: str
    url: str
    name: Optional[str]
    status_code: Optional[int]
    response_time_ms: Optional[int]
    success: bool
    created_at: datetime
    tags: Optional[List[str]]
    project_name: Optional[str]
    
    class Config:
        from_attributes = True

@router.get("/search")
async def search_request_history(
    q: Optional[str] = Query(None, description="Search query"),
    method: Optional[List[str]] = Query(None, description="HTTP methods to filter"),
    status: Optional[List[int]] = Query(None, description="Status codes to filter"),
    min_time: Optional[int] = Query(None, description="Min response time (ms)"),
    max_time: Optional[int] = Query(None, description="Max response time (ms)"),
    project_id: Optional[int] = Query(None),
    tags: Optional[List[str]] = Query(None),
    days: Optional[int] = Query(7, description="Number of days to look back"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    sort_by: str = Query("created_at", regex="^(created_at|response_time_ms|status_code|method)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthManager.get_current_user)
):
    """
    Advanced search for request history with multiple filters.
    Supports full-text search, filtering, and sorting.
    """
    
    # Base query
    query_obj = db.query(RequestHistory).filter(
        RequestHistory.user_id == current_user["id"]
    )
    
    # Apply date filter
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query_obj = query_obj.filter(RequestHistory.created_at >= start_date)
    
    # Full-text search across multiple fields
    if q:
        search_pattern = f"%{q}%"
        query_obj = query_obj.filter(
            or_(
                RequestHistory.url.ilike(search_pattern),
                RequestHistory.name.ilike(search_pattern),
                RequestHistory.notes.ilike(search_pattern),
                RequestHistory.response_body.ilike(search_pattern)
            )
        )
    
    # Method filter
    if method:
        query_obj = query_obj.filter(RequestHistory.method.in_(method))
    
    # Status code filter
    if status:
        query_obj = query_obj.filter(RequestHistory.status_code.in_(status))
    
    # Response time filters
    if min_time is not None:
        query_obj = query_obj.filter(RequestHistory.response_time_ms >= min_time)
    if max_time is not None:
        query_obj = query_obj.filter(RequestHistory.response_time_ms <= max_time)
    
    # Project filter
    if project_id:
        query_obj = query_obj.filter(RequestHistory.project_id == project_id)
    
    # Tags filter (JSON contains)
    if tags:
        for tag in tags:
            query_obj = query_obj.filter(
                func.json_contains(RequestHistory.tags, f'"{tag}"')
            )
    
    # Apply sorting
    order_column = getattr(RequestHistory, sort_by)
    if sort_order == "desc":
        query_obj = query_obj.order_by(desc(order_column))
    else:
        query_obj = query_obj.order_by(order_column)
    
    # Get total count before pagination
    total = query_obj.count()
    
    # Apply pagination
    results = query_obj.offset(offset).limit(limit).all()
    
    # Format response
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "results": [
            {
                "id": r.id,
                "method": r.method,
                "url": r.url,
                "name": r.name,
                "status_code": r.status_code,
                "response_time_ms": r.response_time_ms,
                "success": r.success,
                "created_at": r.created_at,
                "tags": r.tags or [],
                "project_id": r.project_id
            }
            for r in results
        ]
    }

@router.get("/stats")
async def get_request_stats(
    days: int = Query(7, description="Number of days for statistics"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthManager.get_current_user)
):
    """Get statistics about request history"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get requests for the period
    requests = db.query(RequestHistory).filter(
        RequestHistory.user_id == current_user["id"],
        RequestHistory.created_at >= start_date
    ).all()
    
    if not requests:
        return {
            "total_requests": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "methods": {},
            "status_codes": {},
            "top_endpoints": []
        }
    
    # Calculate statistics
    total = len(requests)
    successful = sum(1 for r in requests if r.success)
    
    # Method distribution
    method_counts = {}
    status_counts = {}
    response_times = []
    endpoint_counts = {}
    
    for req in requests:
        # Count methods
        method_counts[req.method] = method_counts.get(req.method, 0) + 1
        
        # Count status codes
        if req.status_code:
            status_counts[str(req.status_code)] = status_counts.get(str(req.status_code), 0) + 1
        
        # Collect response times
        if req.response_time_ms:
            response_times.append(req.response_time_ms)
        
        # Count endpoints (normalize URL)
        from urllib.parse import urlparse
        parsed = urlparse(req.url)
        endpoint = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
    
    # Get top endpoints
    top_endpoints = sorted(
        endpoint_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    return {
        "total_requests": total,
        "success_rate": (successful / total * 100) if total > 0 else 0,
        "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
        "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
        "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
        "methods": method_counts,
        "status_codes": status_counts,
        "top_endpoints": [
            {"url": url, "count": count} 
            for url, count in top_endpoints
        ]
    }

@router.post("/save-search")
async def save_search(
    search: SavedSearch,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthManager.get_current_user)
):
    """Save a search as a smart folder"""
    
    # Store in a simple JSON field in user preferences
    # In a real implementation, this would be a separate table
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if not user.preferences:
        user.preferences = {"saved_searches": []}
    
    if "saved_searches" not in user.preferences:
        user.preferences["saved_searches"] = []
    
    # Add new search
    user.preferences["saved_searches"].append({
        "name": search.name,
        "description": search.description,
        "params": search.search_params.dict(),
        "created_at": datetime.utcnow().isoformat()
    })
    
    db.commit()
    
    return {"message": "Search saved successfully"}

@router.get("/saved-searches")
async def get_saved_searches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthManager.get_current_user)
):
    """Get all saved searches/smart folders"""
    
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    if not user.preferences or "saved_searches" not in user.preferences:
        return {"searches": []}
    
    return {"searches": user.preferences["saved_searches"]}

@router.delete("/{request_id}")
async def delete_request_history(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthManager.get_current_user)
):
    """Delete a specific request from history"""
    
    request = db.query(RequestHistory).filter(
        RequestHistory.id == request_id,
        RequestHistory.user_id == current_user["id"]
    ).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db.delete(request)
    db.commit()
    
    return {"message": "Request deleted successfully"}

@router.delete("/clear")
async def clear_request_history(
    days: Optional[int] = Query(None, description="Clear requests older than N days"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(AuthManager.get_current_user)
):
    """Clear request history (optionally older than N days)"""
    
    query = db.query(RequestHistory).filter(
        RequestHistory.user_id == current_user["id"]
    )
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(RequestHistory.created_at < cutoff_date)
    
    count = query.count()
    query.delete()
    db.commit()
    
    return {"message": f"Cleared {count} requests from history"}