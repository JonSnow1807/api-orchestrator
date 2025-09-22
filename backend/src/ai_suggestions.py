"""
AI-Powered Inline Suggestions - Real-time assistance that beats Postman
Provides context-aware suggestions for API testing, headers, payloads, and more
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print(
        "Warning: AI packages not available. Inline suggestions will use fallback mode."
    )


class SuggestionType:
    """Types of AI suggestions"""

    HEADERS = "headers"
    PAYLOAD = "payload"
    ENDPOINT = "endpoint"
    TEST_CASE = "test_case"
    ERROR_FIX = "error_fix"
    OPTIMIZATION = "optimization"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


class AISuggestion(BaseModel):
    """AI suggestion model"""

    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    type: str
    context: Dict[str, Any]
    suggestions: List[Dict[str, Any]]
    confidence: float
    explanation: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class InlineAISuggestions:
    """Provide real-time AI suggestions for API development"""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        if AI_AVAILABLE:
            self.llm = ChatOpenAI(model=model, temperature=0.3, max_tokens=500)
        else:
            self.llm = None

    async def get_header_suggestions(
        self, method: str, endpoint: str, existing_headers: Dict[str, str] = None
    ) -> AISuggestion:
        """Suggest appropriate headers for an API request"""

        if not AI_AVAILABLE or not self.llm:
            return self._get_fallback_header_suggestions(
                method, endpoint, existing_headers
            )

        prompt = f"""Suggest appropriate HTTP headers for this API request:
Method: {method}
Endpoint: {endpoint}
Existing headers: {json.dumps(existing_headers or {})}

Provide common and security-related headers that might be needed.
Format: JSON array of {{"header": "name", "value": "value", "required": bool, "description": "why"}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestions = self._parse_json_response(response.content)

            return AISuggestion(
                type=SuggestionType.HEADERS,
                context={"method": method, "endpoint": endpoint},
                suggestions=suggestions,
                confidence=0.85,
                explanation="AI-suggested headers based on endpoint and method",
            )
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_header_suggestions(
                method, endpoint, existing_headers
            )

    async def get_payload_suggestions(
        self, endpoint: str, method: str, api_spec: Optional[Dict[str, Any]] = None
    ) -> AISuggestion:
        """Suggest request payload based on endpoint and spec"""

        if not AI_AVAILABLE or not self.llm:
            return self._get_fallback_payload_suggestions(endpoint, method)

        prompt = f"""Generate a sample request payload for:
Endpoint: {endpoint}
Method: {method}
API Spec: {json.dumps(api_spec) if api_spec else 'Not provided'}

Provide realistic test data with various scenarios (valid, edge cases).
Format: JSON array of {{"scenario": "name", "payload": {{}}, "description": "what it tests"}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestions = self._parse_json_response(response.content)

            return AISuggestion(
                type=SuggestionType.PAYLOAD,
                context={"endpoint": endpoint, "method": method},
                suggestions=suggestions,
                confidence=0.9,
                explanation="AI-generated test payloads for different scenarios",
            )
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_payload_suggestions(endpoint, method)

    async def get_test_suggestions(
        self, endpoint: str, response_data: Dict[str, Any], status_code: int
    ) -> AISuggestion:
        """Suggest test assertions based on API response"""

        if not AI_AVAILABLE or not self.llm:
            return self._get_fallback_test_suggestions(status_code, response_data)

        prompt = f"""Suggest test assertions for this API response:
Endpoint: {endpoint}
Status Code: {status_code}
Response: {json.dumps(response_data)[:500]}

Provide test assertions to validate the response.
Format: JSON array of {{"assertion": "description", "path": "json.path", "expected": "value", "type": "equals|contains|exists"}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestions = self._parse_json_response(response.content)

            return AISuggestion(
                type=SuggestionType.TEST_CASE,
                context={"endpoint": endpoint, "status_code": status_code},
                suggestions=suggestions,
                confidence=0.88,
                explanation="AI-suggested test assertions for response validation",
            )
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_test_suggestions(status_code, response_data)

    async def get_error_fix_suggestions(
        self, error_message: str, request_details: Dict[str, Any]
    ) -> AISuggestion:
        """Suggest fixes for API errors"""

        if not AI_AVAILABLE or not self.llm:
            return self._get_fallback_error_suggestions(error_message)

        prompt = f"""Analyze this API error and suggest fixes:
Error: {error_message}
Request: {json.dumps(request_details)[:500]}

Provide specific solutions to fix this error.
Format: JSON array of {{"fix": "description", "action": "what to do", "example": "code/value", "likelihood": 0-1}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestions = self._parse_json_response(response.content)

            return AISuggestion(
                type=SuggestionType.ERROR_FIX,
                context={"error": error_message},
                suggestions=suggestions,
                confidence=0.92,
                explanation="AI-analyzed error with suggested fixes",
            )
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_error_suggestions(error_message)

    async def get_optimization_suggestions(
        self, endpoint: str, response_time_ms: float, response_size_bytes: int
    ) -> AISuggestion:
        """Suggest performance optimizations"""

        if not AI_AVAILABLE or not self.llm:
            return self._get_fallback_optimization_suggestions(response_time_ms)

        prompt = f"""Suggest optimizations for this API:
Endpoint: {endpoint}
Response Time: {response_time_ms}ms
Response Size: {response_size_bytes} bytes

Provide specific optimization suggestions.
Format: JSON array of {{"optimization": "name", "impact": "high|medium|low", "implementation": "how to", "estimated_improvement": "percentage"}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestions = self._parse_json_response(response.content)

            return AISuggestion(
                type=SuggestionType.OPTIMIZATION,
                context={"endpoint": endpoint, "response_time": response_time_ms},
                suggestions=suggestions,
                confidence=0.8,
                explanation="AI-suggested performance optimizations",
            )
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_optimization_suggestions(response_time_ms)

    async def get_security_suggestions(
        self, endpoint: str, headers: Dict[str, str], auth_type: Optional[str] = None
    ) -> AISuggestion:
        """Suggest security improvements"""

        if not AI_AVAILABLE or not self.llm:
            return self._get_fallback_security_suggestions(headers)

        prompt = f"""Analyze security for this API:
Endpoint: {endpoint}
Headers: {json.dumps(headers)}
Auth Type: {auth_type or 'Unknown'}

Suggest security improvements.
Format: JSON array of {{"issue": "description", "severity": "critical|high|medium|low", "fix": "solution", "reference": "OWASP/standard"}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            suggestions = self._parse_json_response(response.content)

            return AISuggestion(
                type=SuggestionType.SECURITY,
                context={"endpoint": endpoint},
                suggestions=suggestions,
                confidence=0.95,
                explanation="AI-identified security recommendations",
            )
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return self._get_fallback_security_suggestions(headers)

    def _parse_json_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON from AI response"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(content)
        except Exception:
            # Fallback to simple parsing
            return [{"suggestion": content, "confidence": 0.5}]

    def _get_fallback_header_suggestions(
        self, method: str, endpoint: str, existing_headers: Dict[str, str]
    ) -> AISuggestion:
        """Fallback header suggestions when AI is not available"""

        suggestions = [
            {
                "header": "Content-Type",
                "value": "application/json",
                "required": True,
                "description": "Specify content type",
            },
            {
                "header": "Accept",
                "value": "application/json",
                "required": False,
                "description": "Specify accepted response type",
            },
            {
                "header": "Authorization",
                "value": "Bearer <token>",
                "required": True,
                "description": "Authentication token",
            },
            {
                "header": "X-Request-ID",
                "value": "<unique-id>",
                "required": False,
                "description": "Track requests",
            },
        ]

        # Filter out existing headers
        if existing_headers:
            suggestions = [
                s for s in suggestions if s["header"] not in existing_headers
            ]

        return AISuggestion(
            type=SuggestionType.HEADERS,
            context={"method": method, "endpoint": endpoint},
            suggestions=suggestions,
            confidence=0.7,
            explanation="Common header suggestions (AI unavailable)",
        )

    def _get_fallback_payload_suggestions(
        self, endpoint: str, method: str
    ) -> AISuggestion:
        """Fallback payload suggestions"""

        suggestions = [
            {
                "scenario": "Valid data",
                "payload": {
                    "name": "Test User",
                    "email": "test@example.com",
                    "age": 25,
                },
                "description": "Standard valid payload",
            },
            {
                "scenario": "Minimal data",
                "payload": {"name": "Test"},
                "description": "Minimum required fields",
            },
            {
                "scenario": "Edge case",
                "payload": {"name": "A" * 255, "email": "test@test.test", "age": 0},
                "description": "Boundary values",
            },
        ]

        return AISuggestion(
            type=SuggestionType.PAYLOAD,
            context={"endpoint": endpoint, "method": method},
            suggestions=suggestions,
            confidence=0.6,
            explanation="Generic payload examples (AI unavailable)",
        )

    def _get_fallback_test_suggestions(
        self, status_code: int, response_data: Dict[str, Any]
    ) -> AISuggestion:
        """Fallback test suggestions"""

        suggestions = [
            {
                "assertion": "Status code check",
                "path": "status",
                "expected": status_code,
                "type": "equals",
            },
            {
                "assertion": "Response not empty",
                "path": "body",
                "expected": None,
                "type": "exists",
            },
            {
                "assertion": "Has data field",
                "path": "data",
                "expected": None,
                "type": "exists",
            },
        ]

        return AISuggestion(
            type=SuggestionType.TEST_CASE,
            context={"status_code": status_code},
            suggestions=suggestions,
            confidence=0.65,
            explanation="Basic test assertions (AI unavailable)",
        )

    def _get_fallback_error_suggestions(self, error_message: str) -> AISuggestion:
        """Fallback error fix suggestions"""

        suggestions = []

        if "401" in error_message or "unauthorized" in error_message.lower():
            suggestions.append(
                {
                    "fix": "Check authentication",
                    "action": "Verify API key or token is valid",
                    "example": "Authorization: Bearer <valid-token>",
                    "likelihood": 0.9,
                }
            )

        if "404" in error_message:
            suggestions.append(
                {
                    "fix": "Check endpoint URL",
                    "action": "Verify the endpoint path is correct",
                    "example": "/api/v1/resource",
                    "likelihood": 0.85,
                }
            )

        if "500" in error_message:
            suggestions.append(
                {
                    "fix": "Server error",
                    "action": "Check server logs or contact API provider",
                    "example": "Review server-side error logs",
                    "likelihood": 0.7,
                }
            )

        if not suggestions:
            suggestions.append(
                {
                    "fix": "Generic troubleshooting",
                    "action": "Check request format and parameters",
                    "example": "Validate JSON syntax and required fields",
                    "likelihood": 0.5,
                }
            )

        return AISuggestion(
            type=SuggestionType.ERROR_FIX,
            context={"error": error_message},
            suggestions=suggestions,
            confidence=0.7,
            explanation="Common error fixes (AI unavailable)",
        )

    def _get_fallback_optimization_suggestions(
        self, response_time_ms: float
    ) -> AISuggestion:
        """Fallback optimization suggestions"""

        suggestions = []

        if response_time_ms > 1000:
            suggestions.append(
                {
                    "optimization": "Add caching",
                    "impact": "high",
                    "implementation": "Implement Redis or in-memory caching",
                    "estimated_improvement": "50-70%",
                }
            )

        if response_time_ms > 500:
            suggestions.append(
                {
                    "optimization": "Pagination",
                    "impact": "medium",
                    "implementation": "Limit results and add pagination",
                    "estimated_improvement": "30-50%",
                }
            )

        suggestions.append(
            {
                "optimization": "Compression",
                "impact": "medium",
                "implementation": "Enable gzip compression",
                "estimated_improvement": "20-40%",
            }
        )

        return AISuggestion(
            type=SuggestionType.OPTIMIZATION,
            context={"response_time": response_time_ms},
            suggestions=suggestions,
            confidence=0.75,
            explanation="Performance optimization suggestions (AI unavailable)",
        )

    def _get_fallback_security_suggestions(
        self, headers: Dict[str, str]
    ) -> AISuggestion:
        """Fallback security suggestions"""

        suggestions = []

        if "X-Frame-Options" not in headers:
            suggestions.append(
                {
                    "issue": "Missing X-Frame-Options",
                    "severity": "medium",
                    "fix": "Add X-Frame-Options: DENY header",
                    "reference": "OWASP Clickjacking",
                }
            )

        if "X-Content-Type-Options" not in headers:
            suggestions.append(
                {
                    "issue": "Missing X-Content-Type-Options",
                    "severity": "low",
                    "fix": "Add X-Content-Type-Options: nosniff",
                    "reference": "OWASP MIME Sniffing",
                }
            )

        if "Strict-Transport-Security" not in headers:
            suggestions.append(
                {
                    "issue": "Missing HSTS",
                    "severity": "high",
                    "fix": "Add Strict-Transport-Security header",
                    "reference": "OWASP Transport Security",
                }
            )

        return AISuggestion(
            type=SuggestionType.SECURITY,
            context={"headers": headers},
            suggestions=suggestions,
            confidence=0.8,
            explanation="Security header recommendations (AI unavailable)",
        )


# Global instance
ai_suggestions = InlineAISuggestions()
