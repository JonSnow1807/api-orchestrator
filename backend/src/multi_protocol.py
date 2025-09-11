"""
Multi-Protocol Support for API Orchestrator
Supports WebSocket, gRPC, SOAP, Server-Sent Events (SSE)
"""

import asyncio
import json
import base64
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import websockets
import httpx
from xml.etree import ElementTree as ET
import xml.dom.minidom

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Text

from src.database import Base

class ProtocolType:
    """Supported protocol types"""
    REST = "rest"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"
    GRPC = "grpc"
    SOAP = "soap"
    SSE = "sse"

class WebSocketTester:
    """WebSocket protocol testing"""
    
    @staticmethod
    async def connect_and_test(
        url: str,
        messages: List[Dict[str, Any]],
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Connect to WebSocket and send/receive messages"""
        
        results = {
            "connection": None,
            "messages_sent": [],
            "messages_received": [],
            "errors": [],
            "duration_ms": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            # Connect to WebSocket
            extra_headers = headers or {}
            async with websockets.connect(url, extra_headers=extra_headers) as websocket:
                results["connection"] = "established"
                
                # Send messages and collect responses
                for msg_config in messages:
                    message = msg_config.get("message")
                    wait_for_response = msg_config.get("wait_for_response", True)
                    response_timeout = msg_config.get("timeout", 5)
                    
                    # Send message
                    if isinstance(message, dict):
                        message = json.dumps(message)
                    
                    await websocket.send(message)
                    results["messages_sent"].append({
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    # Wait for response if configured
                    if wait_for_response:
                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=response_timeout
                            )
                            
                            # Try to parse as JSON
                            try:
                                response_data = json.loads(response)
                            except:
                                response_data = response
                            
                            results["messages_received"].append({
                                "message": response_data,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                        except asyncio.TimeoutError:
                            results["errors"].append(f"Response timeout for message: {message[:100]}")
                
        except Exception as e:
            results["connection"] = "failed"
            results["errors"].append(str(e))
        
        # Calculate duration
        duration = datetime.utcnow() - start_time
        results["duration_ms"] = int(duration.total_seconds() * 1000)
        
        return results
    
    @staticmethod
    def generate_test_messages(endpoint_type: str) -> List[Dict]:
        """Generate sample WebSocket test messages"""
        
        if endpoint_type == "chat":
            return [
                {"message": {"type": "join", "room": "test"}, "wait_for_response": True},
                {"message": {"type": "message", "text": "Hello World"}, "wait_for_response": True},
                {"message": {"type": "leave", "room": "test"}, "wait_for_response": False}
            ]
        elif endpoint_type == "echo":
            return [
                {"message": "ping", "wait_for_response": True},
                {"message": {"test": "data"}, "wait_for_response": True}
            ]
        else:
            return [
                {"message": "test", "wait_for_response": True}
            ]

class SOAPTester:
    """SOAP/XML protocol testing"""
    
    @staticmethod
    async def call_soap_method(
        url: str,
        soap_action: str,
        soap_body: str,
        headers: Optional[Dict[str, str]] = None,
        use_soap_12: bool = False
    ) -> Dict[str, Any]:
        """Call a SOAP web service method"""
        
        # SOAP envelope template
        soap_version = "1.2" if use_soap_12 else "1.1"
        namespace = "http://www.w3.org/2003/05/soap-envelope" if use_soap_12 else "http://schemas.xmlsoap.org/soap/envelope/"
        
        if not soap_body.strip().startswith("<"):
            # Wrap in SOAP envelope if not already wrapped
            envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{namespace}">
    <soap:Body>
        {soap_body}
    </soap:Body>
</soap:Envelope>"""
        else:
            envelope = soap_body
        
        # Prepare headers
        soap_headers = {
            "Content-Type": "application/soap+xml; charset=utf-8" if use_soap_12 else "text/xml; charset=utf-8",
            "SOAPAction": f'"{soap_action}"' if soap_action else '""'
        }
        if headers:
            soap_headers.update(headers)
        
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                content=envelope,
                headers=soap_headers
            )
            
            # Parse response
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "raw_response": response.text,
                "parsed_response": None,
                "soap_fault": None
            }
            
            # Try to parse XML response
            try:
                root = ET.fromstring(response.text)
                
                # Check for SOAP fault
                fault = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Fault")
                if not fault:
                    fault = root.find(".//{http://www.w3.org/2003/05/soap-envelope}Fault")
                
                if fault:
                    result["soap_fault"] = SOAPTester._parse_soap_fault(fault)
                else:
                    # Parse body
                    body = root.find(".//{http://schemas.xmlsoap.org/soap/envelope/}Body")
                    if not body:
                        body = root.find(".//{http://www.w3.org/2003/05/soap-envelope}Body")
                    
                    if body:
                        result["parsed_response"] = SOAPTester._xml_to_dict(body)
                
            except Exception as e:
                result["parse_error"] = str(e)
            
            return result
    
    @staticmethod
    def _parse_soap_fault(fault_element) -> Dict:
        """Parse SOAP fault element"""
        
        fault_info = {}
        for child in fault_element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            fault_info[tag] = child.text
        
        return fault_info
    
    @staticmethod
    def _xml_to_dict(element) -> Dict:
        """Convert XML element to dictionary"""
        
        result = {}
        
        # Add attributes
        if element.attrib:
            result["@attributes"] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            result["text"] = element.text.strip()
        
        # Add children
        for child in element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            
            if len(child) > 0 or child.attrib:
                child_data = SOAPTester._xml_to_dict(child)
            else:
                child_data = child.text.strip() if child.text else ""
            
            if tag in result:
                # Convert to list if multiple elements with same tag
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_data)
            else:
                result[tag] = child_data
        
        return result
    
    @staticmethod
    def generate_soap_request(
        method_name: str,
        parameters: Dict[str, Any],
        namespace: str = "http://tempuri.org/"
    ) -> str:
        """Generate SOAP request body"""
        
        params_xml = ""
        for key, value in parameters.items():
            params_xml += f"<{key}>{value}</{key}>"
        
        return f"""
        <{method_name} xmlns="{namespace}">
            {params_xml}
        </{method_name}>
        """

class GRPCTester:
    """gRPC protocol testing (using grpc-web/JSON format)"""
    
    @staticmethod
    async def call_grpc_method(
        url: str,
        service: str,
        method: str,
        request_data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Call a gRPC method using grpc-web JSON format"""
        
        # gRPC-Web uses special headers
        headers = {
            "Content-Type": "application/grpc-web+json",
            "X-Grpc-Web": "1",
            "X-User-Agent": "API-Orchestrator/1.0"
        }
        
        if metadata:
            for key, value in metadata.items():
                headers[f"X-Grpc-Meta-{key}"] = value
        
        # Construct the full URL
        full_url = f"{url}/{service}/{method}"
        
        # Encode request
        request_body = json.dumps(request_data)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                full_url,
                content=request_body,
                headers=headers
            )
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response": None,
                "error": None,
                "grpc_status": None
            }
            
            # Check for gRPC status in headers
            grpc_status = response.headers.get("grpc-status")
            if grpc_status:
                result["grpc_status"] = int(grpc_status)
                
                if grpc_status != "0":
                    result["error"] = {
                        "code": grpc_status,
                        "message": response.headers.get("grpc-message", "Unknown error")
                    }
            
            # Parse response
            try:
                if response.text:
                    result["response"] = json.loads(response.text)
            except:
                result["response"] = response.text
            
            return result
    
    @staticmethod
    def generate_reflection_request() -> Dict:
        """Generate a gRPC reflection request to discover services"""
        
        return {
            "file_containing_symbol": ["*"]
        }

class SSETester:
    """Server-Sent Events (SSE) testing"""
    
    @staticmethod
    async def connect_and_listen(
        url: str,
        headers: Optional[Dict[str, str]] = None,
        max_events: int = 10,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Connect to SSE endpoint and listen for events"""
        
        results = {
            "connection": None,
            "events": [],
            "errors": [],
            "duration_ms": 0
        }
        
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream('GET', url, headers=headers or {}) as response:
                    results["connection"] = "established"
                    
                    event_count = 0
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            event_data = line[5:].strip()
                            
                            # Try to parse as JSON
                            try:
                                event_data = json.loads(event_data)
                            except:
                                pass
                            
                            results["events"].append({
                                "data": event_data,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            
                            event_count += 1
                            if event_count >= max_events:
                                break
                        
                        elif line.startswith("event:"):
                            event_type = line[6:].strip()
                            if results["events"]:
                                results["events"][-1]["type"] = event_type
                        
                        elif line.startswith("id:"):
                            event_id = line[3:].strip()
                            if results["events"]:
                                results["events"][-1]["id"] = event_id
                
        except Exception as e:
            results["connection"] = "failed"
            results["errors"].append(str(e))
        
        # Calculate duration
        duration = datetime.utcnow() - start_time
        results["duration_ms"] = int(duration.total_seconds() * 1000)
        
        return results

class MultiProtocolTest(Base):
    """Store multi-protocol test configurations and results"""
    __tablename__ = "multi_protocol_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    
    # Test configuration
    name = Column(String(255), nullable=False)
    protocol = Column(String(50), nullable=False)  # websocket, grpc, soap, sse
    endpoint_url = Column(String(500), nullable=False)
    
    # Protocol-specific config
    config = Column(JSON)  # Protocol-specific configuration
    test_data = Column(JSON)  # Test messages/requests
    
    # Results
    last_test_at = Column(DateTime)
    last_test_result = Column(JSON)
    success_rate = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)