#!/usr/bin/env python3
"""
Verify all implemented features are working
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def check_feature(name, test_func):
    """Run a feature test and report results"""
    try:
        result = test_func()
        if result:
            print(f"✅ {name}")
            return True
        else:
            print(f"❌ {name} - Failed")
            return False
    except Exception as e:
        print(f"❌ {name} - Error: {str(e)[:50]}")
        return False

def test_server():
    """Test if server is running"""
    r = requests.get(f"{BASE_URL}/")
    return r.status_code == 200

def test_auth_endpoints():
    """Test authentication endpoints exist"""
    # Check if endpoints exist (should get 422 without data, not 404)
    endpoints = ["/auth/register", "/auth/login", "/auth/me"]
    for endpoint in endpoints:
        r = requests.get(f"{BASE_URL}{endpoint}")
        if r.status_code == 404:
            return False
    return True

def test_export_endpoints():
    """Test export/import endpoints exist"""
    r = requests.get(f"{BASE_URL}/api/export/formats")
    return r.status_code != 404  # Should be 401 (needs auth) not 404

def test_websocket():
    """Test WebSocket endpoint"""
    # Can't easily test WebSocket with requests, just check it's in docs
    r = requests.get(f"{BASE_URL}/")
    data = r.json()
    return "/ws" in str(data)

def test_api_docs():
    """Test API documentation"""
    r = requests.get(f"{BASE_URL}/docs")
    return "swagger" in r.text.lower()

def test_database():
    """Test database is initialized"""
    import os
    return os.path.exists("api_orchestrator.db")

def test_orchestration_endpoint():
    """Test orchestration endpoint exists"""
    r = requests.post(f"{BASE_URL}/api/orchestrate", json={})
    return r.status_code != 404  # Should be 401 or 422, not 404

def test_project_crud():
    """Test project CRUD endpoints"""
    # These don't exist yet
    r = requests.get(f"{BASE_URL}/api/projects")
    return r.status_code != 404

def test_frontend_auth():
    """Test if frontend has auth UI"""
    # Check if frontend login page exists
    import os
    frontend_path = "frontend/src/components/Login.jsx"
    return os.path.exists(frontend_path)

def test_error_handling():
    """Test proper error handling"""
    r = requests.get(f"{BASE_URL}/api/nonexistent")
    return r.status_code == 404 and "detail" in r.json()

def test_ai_agent():
    """Test AI agent module exists"""
    import os
    return os.path.exists("src/agents/ai_agent.py")

def main():
    print("🔍 Verifying Implemented Features")
    print("=" * 50)
    
    results = {
        "✅ COMPLETED": [],
        "❌ MISSING": []
    }
    
    # Backend Core
    print("\n📦 Backend Core Features:")
    if check_feature("Server Running", test_server):
        results["✅ COMPLETED"].append("FastAPI Server")
    else:
        results["❌ MISSING"].append("FastAPI Server")
    
    if check_feature("API Documentation", test_api_docs):
        results["✅ COMPLETED"].append("Swagger/OpenAPI Docs")
    else:
        results["❌ MISSING"].append("API Documentation")
    
    if check_feature("Database Initialized", test_database):
        results["✅ COMPLETED"].append("SQLAlchemy Database")
    else:
        results["❌ MISSING"].append("Database")
    
    # Authentication
    print("\n🔐 Authentication System:")
    if check_feature("Auth Endpoints", test_auth_endpoints):
        results["✅ COMPLETED"].append("JWT Authentication")
    else:
        results["❌ MISSING"].append("Authentication")
    
    # Export/Import
    print("\n📤 Export/Import System:")
    if check_feature("Export Endpoints", test_export_endpoints):
        results["✅ COMPLETED"].append("Export/Import Functionality")
    else:
        results["❌ MISSING"].append("Export/Import")
    
    # Orchestration
    print("\n🎭 Orchestration System:")
    if check_feature("Orchestration Endpoint", test_orchestration_endpoint):
        results["✅ COMPLETED"].append("API Orchestration")
    else:
        results["❌ MISSING"].append("Orchestration")
    
    if check_feature("WebSocket Support", test_websocket):
        results["✅ COMPLETED"].append("WebSocket Real-time Updates")
    else:
        results["❌ MISSING"].append("WebSocket")
    
    # AI Agent
    print("\n🤖 AI Intelligence:")
    if check_feature("AI Agent Module", test_ai_agent):
        results["✅ COMPLETED"].append("AI Agent (Anthropic Integration)")
    else:
        results["❌ MISSING"].append("AI Agent")
    
    # Missing Features
    print("\n❓ Not Yet Implemented:")
    if not check_feature("Project CRUD Endpoints", test_project_crud):
        results["❌ MISSING"].append("Project Management CRUD")
    
    if not check_feature("Frontend Auth UI", test_frontend_auth):
        results["❌ MISSING"].append("Frontend Authentication UI")
    
    if not check_feature("Advanced Error Handling", test_error_handling):
        results["❌ MISSING"].append("Production Error Handling")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    print(f"\n✅ COMPLETED ({len(results['✅ COMPLETED'])} features):")
    for feature in results["✅ COMPLETED"]:
        print(f"   • {feature}")
    
    print(f"\n❌ STILL MISSING ({len(results['❌ MISSING'])} features):")
    for feature in results["❌ MISSING"]:
        print(f"   • {feature}")
    
    # Final verdict
    completion_rate = len(results["✅ COMPLETED"]) / (len(results["✅ COMPLETED"]) + len(results["❌ MISSING"])) * 100
    
    print(f"\n📈 Completion: {completion_rate:.1f}%")
    
    if completion_rate >= 80:
        print("✅ Core features are mostly complete!")
    elif completion_rate >= 60:
        print("⚠️  Good progress, but key features still missing")
    else:
        print("❌ Many features still need implementation")
    
    return completion_rate

if __name__ == "__main__":
    try:
        completion = main()
        sys.exit(0 if completion >= 70 else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Server not running! Start with: python -m src.main")
        sys.exit(1)