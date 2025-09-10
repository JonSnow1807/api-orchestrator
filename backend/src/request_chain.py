"""
Request Chaining System
Allows using response data from one request in subsequent requests
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
import json
import re
import asyncio
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.database import Base, get_db

class ChainedRequest(BaseModel):
    """Model for a request in a chain"""
    id: str
    name: str
    method: str = "GET"
    url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Union[str, Dict]] = None
    
    # Chaining configuration
    depends_on: Optional[str] = None  # ID of the request this depends on
    extract_from_response: Dict[str, str] = Field(default_factory=dict)  # Extract values from response
    conditions: List[Dict[str, Any]] = Field(default_factory=list)  # Conditions to run this request
    retry_config: Dict[str, int] = Field(default_factory=lambda: {"max_retries": 3, "delay": 1})
    timeout: int = 30
    
    # Authentication
    auth_type: Optional[str] = None  # bearer, basic, api_key
    auth_config: Dict[str, str] = Field(default_factory=dict)

class RequestChain(Base):
    """Database model for request chains"""
    __tablename__ = "request_chains"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Chain configuration
    requests = Column(JSON, nullable=False)  # List of ChainedRequest objects
    variables = Column(JSON, default=dict)  # Initial variables for the chain
    environment_id = Column(String(36), nullable=True)
    
    # Execution settings
    stop_on_failure = Column(Boolean, default=True)
    parallel_execution = Column(Boolean, default=False)
    max_parallel = Column(Integer, default=5)
    
    # Results
    last_run = Column(DateTime)
    last_status = Column(String(20))  # success, partial, failed
    last_duration_ms = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="request_chains")
    project = relationship("Project", backref="request_chains")

class ChainExecutor:
    """Executes request chains with variable extraction and substitution"""
    
    def __init__(self, db: Session):
        self.db = db
        self.context = {}  # Stores variables and responses during execution
        
    async def execute_chain(
        self,
        chain: RequestChain,
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a complete request chain"""
        
        # Initialize context with chain variables and initial variables
        self.context = {
            **(chain.variables or {}),
            **(initial_variables or {}),
            "responses": {},
            "extracted": {}
        }
        
        # Parse requests from JSON
        requests = [ChainedRequest(**req) for req in chain.requests]
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(requests)
        
        # Execute requests in order
        results = []
        failed = False
        start_time = datetime.utcnow()
        
        for request in self._topological_sort(requests, dependency_graph):
            # Check conditions
            if not self._check_conditions(request):
                results.append({
                    "id": request.id,
                    "name": request.name,
                    "status": "skipped",
                    "reason": "Conditions not met"
                })
                continue
            
            # Wait for dependencies if not parallel
            if request.depends_on and not chain.parallel_execution:
                if request.depends_on not in self.context["responses"]:
                    results.append({
                        "id": request.id,
                        "name": request.name,
                        "status": "skipped",
                        "reason": f"Dependency {request.depends_on} not found"
                    })
                    continue
            
            # Execute request
            try:
                response = await self._execute_single_request(request)
                
                # Store response in context
                self.context["responses"][request.id] = response
                
                # Extract values if configured
                if request.extract_from_response:
                    extracted = self._extract_values(response, request.extract_from_response)
                    self.context["extracted"].update(extracted)
                
                results.append({
                    "id": request.id,
                    "name": request.name,
                    "status": "success",
                    "status_code": response.get("status_code"),
                    "duration_ms": response.get("duration_ms"),
                    "extracted": extracted if request.extract_from_response else None
                })
                
            except Exception as e:
                results.append({
                    "id": request.id,
                    "name": request.name,
                    "status": "failed",
                    "error": str(e)
                })
                
                if chain.stop_on_failure:
                    failed = True
                    break
        
        # Calculate total duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Update chain status
        chain.last_run = datetime.utcnow()
        chain.last_status = "failed" if failed else "success"
        chain.last_duration_ms = duration_ms
        self.db.commit()
        
        return {
            "chain_id": chain.id,
            "chain_name": chain.name,
            "status": chain.last_status,
            "duration_ms": duration_ms,
            "requests": results,
            "context": {
                "variables": {k: v for k, v in self.context.items() if k not in ["responses", "extracted"]},
                "extracted": self.context.get("extracted", {})
            }
        }
    
    async def _execute_single_request(self, request: ChainedRequest) -> Dict[str, Any]:
        """Execute a single request with variable substitution"""
        
        # Substitute variables in URL, headers, params, and body
        url = self._substitute_variables(request.url)
        headers = {k: self._substitute_variables(v) for k, v in request.headers.items()}
        params = {k: self._substitute_variables(v) for k, v in request.params.items()}
        
        body = None
        if request.body:
            if isinstance(request.body, dict):
                body = json.dumps({k: self._substitute_variables(str(v)) for k, v in request.body.items()})
            else:
                body = self._substitute_variables(request.body)
        
        # Add authentication
        if request.auth_type == "bearer" and "token" in request.auth_config:
            headers["Authorization"] = f"Bearer {request.auth_config['token']}"
        elif request.auth_type == "api_key":
            key_name = request.auth_config.get("key_name", "X-API-Key")
            headers[key_name] = request.auth_config.get("key_value", "")
        
        # Execute request with retries
        max_retries = request.retry_config.get("max_retries", 3)
        retry_delay = request.retry_config.get("delay", 1)
        
        for attempt in range(max_retries):
            try:
                start = datetime.utcnow()
                
                async with httpx.AsyncClient(timeout=request.timeout) as client:
                    response = await client.request(
                        method=request.method,
                        url=url,
                        headers=headers,
                        params=params,
                        content=body
                    )
                    
                    duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
                    
                    # Parse response
                    try:
                        response_data = response.json()
                    except:
                        response_data = response.text
                    
                    return {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "data": response_data,
                        "duration_ms": duration_ms
                    }
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                raise e
    
    def _substitute_variables(self, text: str) -> str:
        """Substitute variables in text using {{variable}} or ${variable} syntax"""
        
        if not isinstance(text, str):
            return text
        
        result = text
        
        # Replace {{variable}} syntax
        for match in re.finditer(r'\{\{([^}]+)\}\}', text):
            var_path = match.group(1).strip()
            value = self._get_nested_value(var_path)
            if value is not None:
                result = result.replace(match.group(0), str(value))
        
        # Replace ${variable} syntax  
        for match in re.finditer(r'\$\{([^}]+)\}', text):
            var_path = match.group(1).strip()
            value = self._get_nested_value(var_path)
            if value is not None:
                result = result.replace(match.group(0), str(value))
        
        return result
    
    def _get_nested_value(self, path: str) -> Any:
        """Get nested value from context using dot notation"""
        
        # Support response references like: response.request1.data.token
        parts = path.split('.')
        
        if parts[0] == "response" and len(parts) > 1:
            # Get from responses
            request_id = parts[1]
            if request_id in self.context["responses"]:
                value = self.context["responses"][request_id]
                for part in parts[2:]:
                    if isinstance(value, dict):
                        value = value.get(part)
                    else:
                        return None
                return value
        else:
            # Get from general context
            value = self.context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        
        return None
    
    def _extract_values(self, response: Dict, extract_config: Dict[str, str]) -> Dict[str, Any]:
        """Extract values from response using JSONPath or dot notation"""
        
        extracted = {}
        response_data = response.get("data", {})
        
        for var_name, path in extract_config.items():
            # Simple dot notation extraction
            parts = path.split('.')
            value = response_data
            
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif isinstance(value, list) and part.isdigit():
                    index = int(part)
                    if index < len(value):
                        value = value[index]
                    else:
                        value = None
                else:
                    value = None
                    break
            
            if value is not None:
                extracted[var_name] = value
        
        return extracted
    
    def _check_conditions(self, request: ChainedRequest) -> bool:
        """Check if conditions are met for executing a request"""
        
        if not request.conditions:
            return True
        
        for condition in request.conditions:
            field = condition.get("field")
            operator = condition.get("operator", "equals")
            value = condition.get("value")
            
            actual_value = self._get_nested_value(field)
            
            if operator == "equals" and actual_value != value:
                return False
            elif operator == "not_equals" and actual_value == value:
                return False
            elif operator == "contains" and value not in str(actual_value):
                return False
            elif operator == "greater_than" and not (actual_value > value):
                return False
            elif operator == "less_than" and not (actual_value < value):
                return False
            elif operator == "exists" and actual_value is None:
                return False
            elif operator == "not_exists" and actual_value is not None:
                return False
        
        return True
    
    def _build_dependency_graph(self, requests: List[ChainedRequest]) -> Dict[str, List[str]]:
        """Build dependency graph for requests"""
        
        graph = {req.id: [] for req in requests}
        
        for req in requests:
            if req.depends_on:
                if req.depends_on in graph:
                    graph[req.depends_on].append(req.id)
        
        return graph
    
    def _topological_sort(self, requests: List[ChainedRequest], graph: Dict[str, List[str]]) -> List[ChainedRequest]:
        """Sort requests based on dependencies"""
        
        # Simple implementation - can be optimized
        sorted_requests = []
        request_dict = {req.id: req for req in requests}
        visited = set()
        
        def visit(req_id):
            if req_id in visited:
                return
            visited.add(req_id)
            
            # Visit dependencies first
            req = request_dict[req_id]
            if req.depends_on and req.depends_on in request_dict:
                visit(req.depends_on)
            
            sorted_requests.append(req)
        
        for req in requests:
            visit(req.id)
        
        return sorted_requests