#!/usr/bin/env python3
"""Test V5.0 POSTMAN KILLER API endpoints"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> None:
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print(f"❌ Unknown method: {method}")
            return
            
        if 200 <= response.status_code < 300:
            print(f"✅ {method} {endpoint}: {response.status_code}")
            if response.content:
                try:
                    print(f"   Response: {json.dumps(response.json(), indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
        else:
            print(f"❌ {method} {endpoint}: {response.status_code}")
            if response.content:
                try:
                    print(f"   Error: {response.json()}")
                except:
                    print(f"   Error: {response.text[:200]}")
    except Exception as e:
        print(f"❌ {method} {endpoint}: {str(e)}")

def main():
    print("=" * 50)
    print("Testing V5.0 POSTMAN KILLER API Endpoints")
    print("=" * 50)
    
    # Natural Language Testing
    print("\n📝 Natural Language Testing")
    test_endpoint("GET", "/api/v5/natural-language/suggestions")
    test_endpoint("POST", "/api/v5/natural-language/generate-test", {
        "description": "Check if user login works",
        "context": {"endpoint": "/api/auth/login", "method": "POST"}
    })
    
    # Data Visualization
    print("\n📊 Data Visualization")
    test_endpoint("POST", "/api/v5/visualization/analyze", {
        "data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}]
    })
    test_endpoint("POST", "/api/v5/visualization/transform", {
        "data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}],
        "visualization_type": "LINE"
    })
    
    # Variable Management
    print("\n🔧 Variable Management")
    test_endpoint("POST", "/api/v5/variables/create", {
        "name": "API_KEY",
        "value": "test-key-123",
        "scope": "LOCAL"
    })
    test_endpoint("GET", "/api/v5/variables/list")
    test_endpoint("POST", "/api/v5/variables/detect-sensitive", {
        "content": "my password is secret123"
    })
    
    # Privacy AI
    print("\n🔒 Privacy AI")
    test_endpoint("GET", "/api/v5/privacy-ai/compliance-check", params={"regulation": "GDPR"})
    test_endpoint("POST", "/api/v5/privacy-ai/anonymize", {
        "data": {"email": "user@example.com", "ssn": "123-45-6789"}
    })
    
    # Offline Mode
    print("\n💾 Offline Mode")
    test_endpoint("POST", "/api/v5/offline/save-collection", {
        "collection": {"name": "Test Collection", "requests": []},
        "format": "JSON"
    })
    test_endpoint("GET", "/api/v5/offline/collections")
    test_endpoint("POST", "/api/v5/offline/sync", {
        "collection_id": "test-123"
    })
    
    # Service Virtualization
    print("\n🎭 Service Virtualization")
    test_endpoint("GET", "/api/v5/virtualization/services")
    test_endpoint("POST", "/api/v5/virtualization/create-service", {
        "name": "Mock API",
        "behavior": "STATIC"
    })
    
    print("\n" + "=" * 50)
    print("V5.0 API Testing Complete")
    print("=" * 50)

if __name__ == "__main__":
    main()