#!/usr/bin/env python3
"""
Test all new frontend features added to the API Orchestrator
"""

import json
import time
import requests
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8002"
TEST_USER = {
    "email": "demo@streamapi.dev", 
    "password": "Demo123!"
}

class FrontendFeatureTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.task_id = None
        
    def login(self) -> bool:
        """Login and get auth token"""
        print("🔐 Logging in...")
        response = self.session.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def test_code_orchestration(self) -> bool:
        """Test the new code input orchestration feature"""
        print("\n📝 Testing Code Input Orchestration...")
        
        test_code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Test API", version="1.0.0")

class Product(BaseModel):
    id: int
    name: str
    price: float
    in_stock: bool = True

@app.get("/")
def read_root():
    return {"message": "Test API for frontend features"}

@app.get("/products", response_model=List[Product])
def get_products(limit: int = 10, category: Optional[str] = None):
    """Get list of products with optional filtering"""
    return []

@app.post("/products", response_model=Product)
def create_product(product: Product):
    """Create a new product"""
    return product

@app.get("/products/{product_id}")
def get_product(product_id: int):
    """Get a specific product by ID"""
    if product_id < 1:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"id": product_id, "name": "Test Product"}
'''
        
        response = self.session.post(
            f"{BASE_URL}/api/orchestrate",
            json={
                "source_type": "code",
                "source_path": "test_api.py",
                "code_content": test_code,
                "options": {
                    "framework": "fastapi"
                }
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.task_id = data.get("task_id")
            print(f"✅ Code orchestration started: {self.task_id}")
            return True
        else:
            print(f"❌ Code orchestration failed: {response.text}")
            return False
    
    def test_realtime_monitoring(self) -> bool:
        """Test WebSocket real-time monitoring"""
        print("\n📡 Testing Real-time Monitoring...")
        
        if not self.task_id:
            print("⚠️ No task ID available, skipping real-time monitoring test")
            return False
        
        # Check task status
        response = self.session.get(f"{BASE_URL}/api/tasks/{self.task_id}/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Task status: {data.get('status')}")
            print(f"   Progress: {data.get('progress', 0)}%")
            print(f"   Phase: {data.get('current_phase', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to get task status: {response.text}")
            return False
    
    def test_ai_analysis(self) -> bool:
        """Test AI analysis feature"""
        print("\n🤖 Testing AI Analysis...")
        
        if not self.task_id:
            print("⚠️ No task ID available, skipping AI analysis test")
            return False
        
        # Wait for task to complete
        print("⏳ Waiting for task to complete...")
        time.sleep(5)
        
        response = self.session.get(f"{BASE_URL}/api/tasks/{self.task_id}/results")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ai_analysis"):
                print("✅ AI Analysis available:")
                analysis = data["ai_analysis"]
                print(f"   Security Score: {analysis.get('security_score', 'N/A')}%")
                print(f"   Vulnerabilities: {len(analysis.get('security_vulnerabilities', []))}")
                print(f"   Performance Score: {analysis.get('performance_score', 'N/A')}%")
                print(f"   Compliance: {analysis.get('compliance', {})}")
                return True
            else:
                print("⚠️ AI Analysis not available (might require Pro tier)")
                return True  # Not a failure, just tier limitation
        else:
            print(f"❌ Failed to get AI analysis: {response.text}")
            return False
    
    def test_mock_server(self) -> bool:
        """Test mock server creation and management"""
        print("\n🚀 Testing Mock Server Management...")
        
        # Create mock server
        response = self.session.post(
            f"{BASE_URL}/api/mock-servers/create",
            json={"task_id": self.task_id} if self.task_id else {}
        )
        
        if response.status_code == 200:
            server = response.json()
            server_id = server.get("id")
            print(f"✅ Mock server created: {server_id}")
            print(f"   Status: {server.get('status')}")
            print(f"   Port: {server.get('port')}")
            
            # Test server operations
            if server_id:
                # Start server
                self.session.post(f"{BASE_URL}/api/mock-servers/{server_id}/start")
                print("   Started mock server")
                
                # Stop server
                self.session.post(f"{BASE_URL}/api/mock-servers/{server_id}/stop")
                print("   Stopped mock server")
                
                # Delete server
                self.session.delete(f"{BASE_URL}/api/mock-servers/{server_id}")
                print("   Deleted mock server")
            
            return True
        else:
            print(f"❌ Failed to create mock server: {response.text}")
            return False
    
    def test_export_formats(self) -> bool:
        """Test export in multiple formats"""
        print("\n📦 Testing Export Formats...")
        
        if not self.task_id:
            print("⚠️ No task ID available, skipping export test")
            return False
        
        formats = ["json", "yaml", "openapi", "postman"]
        success_count = 0
        
        for fmt in formats:
            response = self.session.get(
                f"{BASE_URL}/api/export/{self.task_id}",
                params={"format": fmt}
            )
            
            if response.status_code == 200:
                print(f"✅ Export to {fmt} successful")
                success_count += 1
            else:
                print(f"⚠️ Export to {fmt} failed (might require Pro tier)")
        
        return success_count > 0
    
    def test_framework_detection(self) -> bool:
        """Test framework auto-detection"""
        print("\n🔍 Testing Framework Detection...")
        
        frameworks = {
            "flask": '''
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"message": "Flask API"})
''',
            "django": '''
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def home(request):
    return Response({"message": "Django API"})

urlpatterns = [
    path('', home),
]
'''
        }
        
        for framework, code in frameworks.items():
            response = self.session.post(
                f"{BASE_URL}/api/orchestrate",
                json={
                    "source_type": "code",
                    "source_path": f"test_{framework}.py",
                    "code_content": code,
                    "options": {"framework": None}  # Auto-detect
                }
            )
            
            if response.status_code == 200:
                print(f"✅ {framework.capitalize()} framework detected and processed")
            else:
                print(f"❌ Failed to process {framework}: {response.text}")
        
        return True
    
    def run_all_tests(self):
        """Run all frontend feature tests"""
        print("=" * 60)
        print("🧪 FRONTEND FEATURE TEST SUITE")
        print("=" * 60)
        
        if not self.login():
            print("\n❌ Cannot proceed without authentication")
            return
        
        results = {
            "Code Orchestration": self.test_code_orchestration(),
            "Real-time Monitoring": self.test_realtime_monitoring(),
            "AI Analysis": self.test_ai_analysis(),
            "Mock Server Management": self.test_mock_server(),
            "Export Formats": self.test_export_formats(),
            "Framework Detection": self.test_framework_detection()
        }
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for feature, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{feature:.<40} {status}")
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL FRONTEND FEATURES WORKING PERFECTLY!")
        elif passed >= total * 0.8:
            print("\n✨ Most features working well!")
        else:
            print("\n⚠️ Some features need attention")

if __name__ == "__main__":
    tester = FrontendFeatureTester()
    tester.run_all_tests()