"""
Multi-Protocol API Routes
Support for WebSocket, gRPC, SOAP, and SSE testing
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio

from src.database import get_db
from src.auth import get_current_user
from src.multi_protocol import (
    WebSocketTester, SOAPTester, GRPCTester, SSETester,
    MultiProtocolTest, ProtocolType
)

router = APIRouter(prefix="/api/multi-protocol", tags=["Multi-Protocol"])

class WebSocketTestRequest(BaseModel):
    """Request model for WebSocket testing"""
    url: str
    messages: List[Dict[str, Any]]
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    save_result: bool = False
    project_id: Optional[int] = None

class SOAPTestRequest(BaseModel):
    """Request model for SOAP testing"""
    url: str
    soap_action: str
    method_name: str
    parameters: Dict[str, Any]
    namespace: Optional[str] = "http://tempuri.org/"
    headers: Optional[Dict[str, str]] = None
    use_soap_12: bool = False
    save_result: bool = False
    project_id: Optional[int] = None

class GRPCTestRequest(BaseModel):
    """Request model for gRPC testing"""
    url: str
    service: str
    method: str
    request_data: Dict[str, Any]
    metadata: Optional[Dict[str, str]] = None
    save_result: bool = False
    project_id: Optional[int] = None

class SSETestRequest(BaseModel):
    """Request model for SSE testing"""
    url: str
    headers: Optional[Dict[str, str]] = None
    max_events: int = 10
    timeout: int = 30
    save_result: bool = False
    project_id: Optional[int] = None

@router.post("/websocket/test")
async def test_websocket(
    request: WebSocketTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test WebSocket endpoint"""
    
    try:
        # Run WebSocket test
        result = await WebSocketTester.connect_and_test(
            url=request.url,
            messages=request.messages,
            headers=request.headers,
            timeout=request.timeout
        )
        
        # Save test configuration if requested
        if request.save_result and request.project_id:
            test_config = MultiProtocolTest(
                project_id=request.project_id,
                name=f"WebSocket: {request.url}",
                protocol=ProtocolType.WEBSOCKET,
                endpoint_url=request.url,
                config={
                    "headers": request.headers,
                    "timeout": request.timeout
                },
                test_data=request.messages,
                last_test_result=result
            )
            db.add(test_config)
            db.commit()
            
            result["test_id"] = test_config.id
        
        return {
            "success": len(result.get("errors", [])) == 0,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"WebSocket test failed: {str(e)}")

@router.post("/soap/test")
async def test_soap(
    request: SOAPTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test SOAP web service"""
    
    try:
        # Generate SOAP request body
        soap_body = SOAPTester.generate_soap_request(
            method_name=request.method_name,
            parameters=request.parameters,
            namespace=request.namespace
        )
        
        # Call SOAP method
        result = await SOAPTester.call_soap_method(
            url=request.url,
            soap_action=request.soap_action,
            soap_body=soap_body,
            headers=request.headers,
            use_soap_12=request.use_soap_12
        )
        
        # Save test configuration if requested
        if request.save_result and request.project_id:
            test_config = MultiProtocolTest(
                project_id=request.project_id,
                name=f"SOAP: {request.method_name}",
                protocol=ProtocolType.SOAP,
                endpoint_url=request.url,
                config={
                    "soap_action": request.soap_action,
                    "namespace": request.namespace,
                    "use_soap_12": request.use_soap_12,
                    "headers": request.headers
                },
                test_data={
                    "method": request.method_name,
                    "parameters": request.parameters
                },
                last_test_result=result
            )
            db.add(test_config)
            db.commit()
            
            result["test_id"] = test_config.id
        
        return {
            "success": result.get("soap_fault") is None and result.get("status_code") == 200,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SOAP test failed: {str(e)}")

@router.post("/grpc/test")
async def test_grpc(
    request: GRPCTestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test gRPC service"""
    
    try:
        # Call gRPC method
        result = await GRPCTester.call_grpc_method(
            url=request.url,
            service=request.service,
            method=request.method,
            request_data=request.request_data,
            metadata=request.metadata
        )
        
        # Save test configuration if requested
        if request.save_result and request.project_id:
            test_config = MultiProtocolTest(
                project_id=request.project_id,
                name=f"gRPC: {request.service}/{request.method}",
                protocol=ProtocolType.GRPC,
                endpoint_url=request.url,
                config={
                    "service": request.service,
                    "method": request.method,
                    "metadata": request.metadata
                },
                test_data=request.request_data,
                last_test_result=result
            )
            db.add(test_config)
            db.commit()
            
            result["test_id"] = test_config.id
        
        return {
            "success": result.get("grpc_status") == 0 or result.get("grpc_status") is None,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"gRPC test failed: {str(e)}")

@router.post("/sse/test")
async def test_sse(
    request: SSETestRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Test Server-Sent Events endpoint"""
    
    try:
        # Connect to SSE endpoint
        result = await SSETester.connect_and_listen(
            url=request.url,
            headers=request.headers,
            max_events=request.max_events,
            timeout=request.timeout
        )
        
        # Save test configuration if requested
        if request.save_result and request.project_id:
            test_config = MultiProtocolTest(
                project_id=request.project_id,
                name=f"SSE: {request.url}",
                protocol=ProtocolType.SSE,
                endpoint_url=request.url,
                config={
                    "headers": request.headers,
                    "max_events": request.max_events,
                    "timeout": request.timeout
                },
                test_data={},
                last_test_result=result
            )
            db.add(test_config)
            db.commit()
            
            result["test_id"] = test_config.id
        
        return {
            "success": len(result.get("errors", [])) == 0,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SSE test failed: {str(e)}")

@router.get("/tests")
async def list_multi_protocol_tests(
    project_id: Optional[int] = None,
    protocol: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List saved multi-protocol tests"""
    
    query = db.query(MultiProtocolTest)
    
    if project_id:
        query = query.filter(MultiProtocolTest.project_id == project_id)
    
    if protocol:
        query = query.filter(MultiProtocolTest.protocol == protocol)
    
    tests = query.all()
    
    return {
        "success": True,
        "tests": [
            {
                "id": test.id,
                "name": test.name,
                "protocol": test.protocol,
                "endpoint_url": test.endpoint_url,
                "last_test_at": test.last_test_at,
                "success_rate": test.success_rate,
                "avg_response_time_ms": test.avg_response_time_ms
            }
            for test in tests
        ]
    }

@router.get("/test/{test_id}")
async def get_multi_protocol_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get details of a saved multi-protocol test"""
    
    test = db.query(MultiProtocolTest).filter(
        MultiProtocolTest.id == test_id
    ).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return {
        "success": True,
        "test": {
            "id": test.id,
            "name": test.name,
            "protocol": test.protocol,
            "endpoint_url": test.endpoint_url,
            "config": test.config,
            "test_data": test.test_data,
            "last_test_result": test.last_test_result,
            "last_test_at": test.last_test_at,
            "success_rate": test.success_rate,
            "avg_response_time_ms": test.avg_response_time_ms
        }
    }

@router.post("/test/{test_id}/rerun")
async def rerun_multi_protocol_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Rerun a saved multi-protocol test"""
    
    test = db.query(MultiProtocolTest).filter(
        MultiProtocolTest.id == test_id
    ).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Rerun based on protocol
    result = None
    
    if test.protocol == ProtocolType.WEBSOCKET:
        result = await WebSocketTester.connect_and_test(
            url=test.endpoint_url,
            messages=test.test_data,
            headers=test.config.get("headers"),
            timeout=test.config.get("timeout", 30)
        )
    
    elif test.protocol == ProtocolType.SOAP:
        soap_body = SOAPTester.generate_soap_request(
            method_name=test.test_data.get("method"),
            parameters=test.test_data.get("parameters"),
            namespace=test.config.get("namespace")
        )
        result = await SOAPTester.call_soap_method(
            url=test.endpoint_url,
            soap_action=test.config.get("soap_action"),
            soap_body=soap_body,
            headers=test.config.get("headers"),
            use_soap_12=test.config.get("use_soap_12", False)
        )
    
    elif test.protocol == ProtocolType.GRPC:
        result = await GRPCTester.call_grpc_method(
            url=test.endpoint_url,
            service=test.config.get("service"),
            method=test.config.get("method"),
            request_data=test.test_data,
            metadata=test.config.get("metadata")
        )
    
    elif test.protocol == ProtocolType.SSE:
        result = await SSETester.connect_and_listen(
            url=test.endpoint_url,
            headers=test.config.get("headers"),
            max_events=test.config.get("max_events", 10),
            timeout=test.config.get("timeout", 30)
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown protocol: {test.protocol}")
    
    # Update test with new result
    test.last_test_at = datetime.utcnow()
    test.last_test_result = result
    db.commit()
    
    return {
        "success": True,
        "result": result
    }

@router.delete("/test/{test_id}")
async def delete_multi_protocol_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a saved multi-protocol test"""
    
    test = db.query(MultiProtocolTest).filter(
        MultiProtocolTest.id == test_id
    ).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    db.delete(test)
    db.commit()
    
    return {
        "success": True,
        "message": "Test deleted successfully"
    }

@router.get("/websocket/sample-messages")
async def get_websocket_sample_messages(
    endpoint_type: str = "echo"
):
    """Get sample WebSocket messages for testing"""
    
    messages = WebSocketTester.generate_test_messages(endpoint_type)
    
    return {
        "success": True,
        "endpoint_type": endpoint_type,
        "messages": messages
    }

@router.post("/grpc/discover")
async def discover_grpc_services(
    url: str,
    current_user = Depends(get_current_user)
):
    """Discover gRPC services using reflection"""
    
    try:
        # Try to call reflection service
        result = await GRPCTester.call_grpc_method(
            url=url,
            service="grpc.reflection.v1alpha.ServerReflection",
            method="ServerReflectionInfo",
            request_data=GRPCTester.generate_reflection_request()
        )
        
        return {
            "success": True,
            "services": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"gRPC discovery failed: {str(e)}")