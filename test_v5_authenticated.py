#!/usr/bin/env python3
"""Test V5.0 POSTMAN KILLER API endpoints with authentication"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def login():
    """Login and get access token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo@example.com", 
        "password": "Demo123!"
    })
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful!")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_endpoint(method: str, endpoint: str, token: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> None:
    """Test a single endpoint with authentication"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"❌ Unknown method: {method}")
            return
            
        if 200 <= response.status_code < 300:
            print(f"✅ {method} {endpoint}: {response.status_code}")
            if response.content:
                try:
                    resp_json = response.json()
                    resp_str = json.dumps(resp_json, indent=2)
                    if len(resp_str) > 200:
                        print(f"   Response preview: {resp_str[:200]}...")
                    else:
                        print(f"   Response: {resp_str}")
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
    print("=" * 60)
    print("Testing V5.0 POSTMAN KILLER API Endpoints (Authenticated)")
    print("=" * 60)
    
    # Login first
    print("\n🔐 Authentication")
    token = login()
    
    if not token:
        print("\n⚠️ Cannot proceed without authentication")
        return
    
    # Natural Language Testing
    print("\n📝 Natural Language Testing")
    test_endpoint("GET", "/api/v5/natural-language/suggestions", token)
    test_endpoint("POST", "/api/v5/natural-language/generate-test", token, {
        "description": "Check if user login works with valid credentials",
        "context": {"endpoint": "/api/auth/login", "method": "POST"}
    })
    test_endpoint("POST", "/api/v5/natural-language/process", token, {
        "query": "Create a test that verifies the API returns 200 status"
    })
    
    # Data Visualization
    print("\n📊 Data Visualization")
    test_endpoint("POST", "/api/v5/visualization/analyze", token, {
        "data": [
            {"month": "Jan", "sales": 10000, "profit": 2000},
            {"month": "Feb", "sales": 15000, "profit": 3000},
            {"month": "Mar", "sales": 12000, "profit": 2500}
        ]
    })
    test_endpoint("POST", "/api/v5/visualization/transform", token, {
        "data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}, {"x": 3, "y": 15}],
        "visualization_type": "LINE",
        "options": {"title": "Sample Line Chart", "xLabel": "Time", "yLabel": "Value"}
    })
    
    # Variable Management  
    print("\n🔧 Variable Management")
    test_endpoint("POST", "/api/v5/variables/create", token, {
        "name": "API_KEY",
        "value": "test-key-123",
        "scope": "LOCAL",
        "description": "Test API key"
    })
    test_endpoint("GET", "/api/v5/variables/list", token)
    test_endpoint("POST", "/api/v5/variables/detect-sensitive", token, {
        "content": "my password is secret123 and my API key is sk-1234567890"
    })
    test_endpoint("PUT", "/api/v5/variables/update/API_KEY", token, {
        "value": "updated-key-456",
        "description": "Updated test key"
    })
    
    # Privacy AI
    print("\n🔒 Privacy AI")
    test_endpoint("GET", "/api/v5/privacy-ai/compliance-check", token, params={"regulation": "GDPR"})
    test_endpoint("GET", "/api/v5/privacy-ai/compliance-check", token, params={"regulation": "HIPAA"})
    test_endpoint("POST", "/api/v5/privacy-ai/anonymize", token, {
        "data": {
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567", 
            "ssn": "123-45-6789",
            "credit_card": "4111-1111-1111-1111"
        },
        "mode": "CLOUD"
    })
    test_endpoint("POST", "/api/v5/privacy-ai/analyze", token, {
        "data": {"user_id": 123, "location": "New York", "purchase": 99.99}
    })
    
    # Offline Mode
    print("\n💾 Offline Mode")
    test_endpoint("POST", "/api/v5/offline/save-collection", token, {
        "collection": {
            "name": "Test Collection",
            "description": "Test offline collection",
            "requests": [
                {"name": "Get Users", "method": "GET", "url": "/api/users"},
                {"name": "Create User", "method": "POST", "url": "/api/users"}
            ]
        },
        "format": "JSON"
    })
    test_endpoint("GET", "/api/v5/offline/collections", token)
    test_endpoint("POST", "/api/v5/offline/sync", token, {
        "collection_id": "test-collection"
    })
    
    # Service Virtualization
    print("\n🎭 Service Virtualization")
    test_endpoint("GET", "/api/v5/virtualization/services", token)
    test_endpoint("POST", "/api/v5/virtualization/create-service", token, {
        "name": "Mock User API",
        "behavior": "STATIC",
        "endpoints": [
            {"path": "/users", "method": "GET", "response": {"users": []}},
            {"path": "/users/{id}", "method": "GET", "response": {"id": 1, "name": "Test"}}
        ]
    })
    test_endpoint("POST", "/api/v5/virtualization/create-service", token, {
        "name": "Dynamic Mock API",
        "behavior": "DYNAMIC",
        "rules": [{"condition": "request.method == 'GET'", "response": {"status": "ok"}}]
    })
    
    print("\n" + "=" * 60)
    print("V5.0 API Testing Complete")
    print("=" * 60)

if __name__ == "__main__":
    main()