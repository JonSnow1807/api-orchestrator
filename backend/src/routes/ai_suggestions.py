"""
AI Suggestions API Routes - Real-time intelligent assistance
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from ..ai_suggestions import ai_suggestions, AISuggestion, SuggestionType
from ..auth import get_current_user

router = APIRouter(prefix="/api/ai-suggestions", tags=["AI Suggestions"])


class HeaderSuggestionRequest(BaseModel):
    method: str
    endpoint: str
    existing_headers: Optional[Dict[str, str]] = None


class PayloadSuggestionRequest(BaseModel):
    endpoint: str
    method: str
    api_spec: Optional[Dict[str, Any]] = None


class TestSuggestionRequest(BaseModel):
    endpoint: str
    response_data: Dict[str, Any]
    status_code: int


class ErrorFixRequest(BaseModel):
    error_message: str
    request_details: Dict[str, Any]


class OptimizationRequest(BaseModel):
    endpoint: str
    response_time_ms: float
    response_size_bytes: int


class SecurityCheckRequest(BaseModel):
    endpoint: str
    headers: Dict[str, str]
    auth_type: Optional[str] = None


@router.post("/headers")
async def get_header_suggestions(
    request: HeaderSuggestionRequest, current_user: dict = Depends(get_current_user)
) -> AISuggestion:
    """Get AI suggestions for HTTP headers"""
    try:
        suggestions = await ai_suggestions.get_header_suggestions(
            method=request.method,
            endpoint=request.endpoint,
            existing_headers=request.existing_headers,
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payload")
async def get_payload_suggestions(
    request: PayloadSuggestionRequest, current_user: dict = Depends(get_current_user)
) -> AISuggestion:
    """Get AI suggestions for request payload"""
    try:
        suggestions = await ai_suggestions.get_payload_suggestions(
            endpoint=request.endpoint, method=request.method, api_spec=request.api_spec
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tests")
async def get_test_suggestions(
    request: TestSuggestionRequest, current_user: dict = Depends(get_current_user)
) -> AISuggestion:
    """Get AI suggestions for test assertions"""
    try:
        suggestions = await ai_suggestions.get_test_suggestions(
            endpoint=request.endpoint,
            response_data=request.response_data,
            status_code=request.status_code,
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/error-fix")
async def get_error_fix_suggestions(
    request: ErrorFixRequest, current_user: dict = Depends(get_current_user)
) -> AISuggestion:
    """Get AI suggestions for fixing errors"""
    try:
        suggestions = await ai_suggestions.get_error_fix_suggestions(
            error_message=request.error_message, request_details=request.request_details
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization")
async def get_optimization_suggestions(
    request: OptimizationRequest, current_user: dict = Depends(get_current_user)
) -> AISuggestion:
    """Get AI suggestions for performance optimization"""
    try:
        suggestions = await ai_suggestions.get_optimization_suggestions(
            endpoint=request.endpoint,
            response_time_ms=request.response_time_ms,
            response_size_bytes=request.response_size_bytes,
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security")
async def get_security_suggestions(
    request: SecurityCheckRequest, current_user: dict = Depends(get_current_user)
) -> AISuggestion:
    """Get AI suggestions for security improvements"""
    try:
        suggestions = await ai_suggestions.get_security_suggestions(
            endpoint=request.endpoint,
            headers=request.headers,
            auth_type=request.auth_type,
        )
        return suggestions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_suggestion_types(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, List[str]]:
    """Get available suggestion types"""
    return {
        "types": [
            SuggestionType.HEADERS,
            SuggestionType.PAYLOAD,
            SuggestionType.TEST_CASE,
            SuggestionType.ERROR_FIX,
            SuggestionType.OPTIMIZATION,
            SuggestionType.SECURITY,
            SuggestionType.DOCUMENTATION,
        ],
        "descriptions": {
            SuggestionType.HEADERS: "Suggest appropriate HTTP headers",
            SuggestionType.PAYLOAD: "Generate test payloads",
            SuggestionType.TEST_CASE: "Create test assertions",
            SuggestionType.ERROR_FIX: "Fix API errors",
            SuggestionType.OPTIMIZATION: "Improve performance",
            SuggestionType.SECURITY: "Enhance security",
            SuggestionType.DOCUMENTATION: "Generate documentation",
        },
    }


@router.get("/status")
async def get_ai_status(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Check AI suggestions service status"""
    try:
        from ..ai_suggestions import AI_AVAILABLE

        return {
            "status": "operational",
            "ai_available": AI_AVAILABLE,
            "model": ai_suggestions.model if AI_AVAILABLE else "fallback",
            "features": [
                "header_suggestions",
                "payload_generation",
                "test_creation",
                "error_analysis",
                "optimization_tips",
                "security_checks",
            ],
        }
    except Exception as e:
        return {"status": "degraded", "ai_available": False, "error": str(e)}
