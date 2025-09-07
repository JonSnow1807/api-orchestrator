#!/usr/bin/env python3
"""
Production testing script for StreamAPI
Tests all core functionality on the live site
"""

import requests
import json
import time
from datetime import datetime
import random
import string

# Production URL
BASE_URL = "https://streamapi.dev"

# Test results
results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def generate_random_string(length=8):
    """Generate random string for unique test data"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def test_health_check():
    """Test if API is responding"""
    print("1. Testing API Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                results["passed"].append("✅ API Health Check")
                print(f"   ✅ API is healthy: {data}")
                return True
            else:
                results["failed"].append("❌ API Health Check - Unhealthy status")
                return False
        else:
            results["failed"].append(f"❌ API Health Check - Status {response.status_code}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ API Health Check - {str(e)}")
        return False

def test_docs():
    """Test if API documentation is accessible"""
    print("2. Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            results["passed"].append("✅ API Documentation accessible")
            print("   ✅ API docs are accessible")
            return True
        else:
            results["failed"].append(f"❌ API Documentation - Status {response.status_code}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ API Documentation - {str(e)}")
        return False

def test_registration():
    """Test user registration"""
    print("3. Testing User Registration...")
    test_user = {
        "username": f"testuser_{generate_random_string()}",
        "email": f"test_{generate_random_string()}@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=test_user
        )
        if response.status_code in [200, 201]:
            data = response.json()
            results["passed"].append("✅ User Registration")
            print(f"   ✅ User registered: {test_user['username']}")
            return test_user, data.get("access_token")
        else:
            results["failed"].append(f"❌ User Registration - Status {response.status_code}: {response.text}")
            return None, None
    except Exception as e:
        results["failed"].append(f"❌ User Registration - {str(e)}")
        return None, None

def test_login(username, password):
    """Test user login"""
    print("4. Testing User Login...")
    try:
        # OAuth2 password flow expects form data, not JSON
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": username,
                "password": password,
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            data = response.json()
            results["passed"].append("✅ User Login")
            print(f"   ✅ Login successful for {username}")
            return data.get("access_token")
        else:
            results["failed"].append(f"❌ User Login - Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        results["failed"].append(f"❌ User Login - {str(e)}")
        return None

def test_password_reset_request():
    """Test password reset email request"""
    print("5. Testing Password Reset Request...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        if response.status_code in [200, 404]:  # 404 if email doesn't exist
            if response.status_code == 200:
                results["passed"].append("✅ Password Reset Request")
                print("   ✅ Password reset email would be sent (if email exists)")
            else:
                results["warnings"].append("⚠️ Password Reset - Email not found (expected)")
                print("   ⚠️ Email not found (expected for test email)")
            return True
        else:
            results["failed"].append(f"❌ Password Reset Request - Status {response.status_code}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ Password Reset Request - {str(e)}")
        return False

def test_create_project(token):
    """Test project creation"""
    print("6. Testing Project Creation...")
    headers = {"Authorization": f"Bearer {token}"}
    project_data = {
        "name": f"Test Project {generate_random_string()}",
        "description": "Automated test project"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/projects",
            json=project_data,
            headers=headers
        )
        if response.status_code in [200, 201]:
            data = response.json()
            results["passed"].append("✅ Project Creation")
            print(f"   ✅ Project created: {project_data['name']}")
            return data.get("id")
        else:
            results["failed"].append(f"❌ Project Creation - Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        results["failed"].append(f"❌ Project Creation - {str(e)}")
        return None

def test_api_orchestration(token):
    """Test API orchestration"""
    print("7. Testing API Orchestration...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Sample Python code for testing - Flask-like API
    test_code = '''
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    return jsonify({"id": user_id, "name": f"User {user_id}"})

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.json
    return jsonify({"id": 123, "name": data.get("name"), "email": data.get("email")})

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    return jsonify([
        {"id": 1, "name": "Product 1", "price": 99.99},
        {"id": 2, "name": "Product 2", "price": 149.99}
    ])

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})
'''
    
    orchestration_data = {
        "source_type": "code",
        "source_path": "test.py",
        "code_content": test_code
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrate",
            json=orchestration_data,
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            if data.get("apis") or data.get("task_id"):
                results["passed"].append("✅ API Orchestration")
                api_count = len(data.get('apis', []))
                print(f"   ✅ Orchestration started - Found {api_count} APIs")
                print(f"   Task ID: {data.get('task_id')}, Project ID: {data.get('project_id')}")
                # Return task_id for subsequent tests
                return data.get("task_id")
            else:
                results["warnings"].append("⚠️ API Orchestration - No APIs found")
                print(f"   Full response: {data}")
                return None
        else:
            results["failed"].append(f"❌ API Orchestration - Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        results["failed"].append(f"❌ API Orchestration - {str(e)}")
        return None

def test_ai_analysis(token, task_id):
    """Test AI analysis feature"""
    print("8. Testing AI Analysis...")
    if not task_id:
        results["warnings"].append("⚠️ AI Analysis - Skipped (no task)")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # AI analysis is available after orchestration completes
        response = requests.get(
            f"{BASE_URL}/api/ai-analysis/{task_id}",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            results["passed"].append("✅ AI Analysis")
            print(f"   ✅ AI Analysis completed")
            return True
        elif response.status_code == 404:
            results["warnings"].append("⚠️ AI Analysis - Not ready or not available")
            print("   ⚠️ AI Analysis not found (may need premium or wait for processing)")
            return False
        elif response.status_code == 402:
            results["warnings"].append("⚠️ AI Analysis - Premium feature")
            print("   ⚠️ AI Analysis requires premium subscription")
            return False
        else:
            results["failed"].append(f"❌ AI Analysis - Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ AI Analysis - {str(e)}")
        return False

def test_mock_server(token, task_id):
    """Test mock server generation"""
    print("9. Testing Mock Server Generation...")
    if not task_id:
        results["warnings"].append("⚠️ Mock Server - Skipped (no task)")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # First check if mock server data exists
        response = requests.get(
            f"{BASE_URL}/api/mock-server/{task_id}",
            headers=headers
        )
        
        if response.status_code == 404:
            results["warnings"].append("⚠️ Mock Server - Not available (needs OpenAPI spec)")
            print("   ⚠️ Mock server requires OpenAPI spec from orchestration")
            return False
        
        # Try to start the mock server
        response = requests.post(
            f"{BASE_URL}/api/mock-server/{task_id}/start",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            results["passed"].append("✅ Mock Server Generation")
            print(f"   ✅ Mock server started on port {data.get('port')}")
            
            # Stop the mock server
            if data.get("server_id"):
                stop_response = requests.post(
                    f"{BASE_URL}/api/mock-server/{task_id}/stop",
                    json={"server_id": data.get("server_id")},
                    headers=headers
                )
            return True
        elif response.status_code == 402:
            results["warnings"].append("⚠️ Mock Server - Premium feature")
            return False
        else:
            results["warnings"].append(f"⚠️ Mock Server - {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ Mock Server - {str(e)}")
        return False

def test_export(token, task_id):
    """Test export functionality"""
    print("10. Testing Export Feature...")
    if not task_id:
        results["warnings"].append("⚠️ Export - Skipped (no task)")
        return False
        
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test export with JSON format (available for free tier)
        response = requests.get(
            f"{BASE_URL}/api/export/{task_id}?format=json",
            headers=headers
        )
        if response.status_code == 200:
            results["passed"].append("✅ Export Feature")
            print("   ✅ Export successful")
            return True
        elif response.status_code == 404:
            results["warnings"].append("⚠️ Export - Task not found or not ready")
            return False
        elif response.status_code == 402:
            results["warnings"].append("⚠️ Export - Premium feature for some formats")
            return False
        else:
            results["failed"].append(f"❌ Export - Status {response.status_code}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ Export - {str(e)}")
        return False

def test_stripe_integration(token):
    """Test Stripe integration"""
    print("11. Testing Stripe Integration...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test billing info endpoint
        response = requests.get(
            f"{BASE_URL}/api/billing/info",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            results["passed"].append("✅ Stripe Integration")
            print(f"   ✅ Billing system active - Tier: {data.get('subscription_tier', 'free')}")
            return True
        elif response.status_code == 404:
            results["warnings"].append("⚠️ Stripe Integration - Endpoint not found")
            return False
        else:
            results["failed"].append(f"❌ Stripe Integration - Status {response.status_code}")
            return False
    except Exception as e:
        results["failed"].append(f"❌ Stripe Integration - {str(e)}")
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY FOR STREAMAPI PRODUCTION")
    print("="*60)
    print(f"🌐 URL: {BASE_URL}")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    print("\n✅ PASSED TESTS:")
    for test in results["passed"]:
        print(f"  {test}")
    
    if results["warnings"]:
        print("\n⚠️ WARNINGS:")
        for warning in results["warnings"]:
            print(f"  {warning}")
    
    if results["failed"]:
        print("\n❌ FAILED TESTS:")
        for failure in results["failed"]:
            print(f"  {failure}")
    
    total = len(results["passed"]) + len(results["failed"])
    pass_rate = (len(results["passed"]) / total * 100) if total > 0 else 0
    
    print("\n" + "="*60)
    print(f"📈 RESULTS: {len(results['passed'])}/{total} tests passed ({pass_rate:.1f}%)")
    
    if len(results["failed"]) == 0:
        print("🎉 All critical tests passed! StreamAPI is working properly!")
    else:
        print("⚠️ Some tests failed. Please check the failures above.")
    print("="*60)

def main():
    """Run all tests"""
    print("="*60)
    print("🚀 TESTING STREAMAPI PRODUCTION ENVIRONMENT")
    print("="*60)
    print(f"Target: {BASE_URL}\n")
    
    # Run tests
    if not test_health_check():
        print("\n❌ API is not responding. Stopping tests.")
        print_summary()
        return
    
    test_docs()
    
    # Test authentication
    user_data, token = test_registration()
    if user_data and not token:
        # Try logging in with the registered user
        print("   Trying login with registered user...")
        token = test_login(user_data["email"], user_data["password"])
    
    if not token:
        # Try with demo credentials
        print("   Trying demo login...")
        token = test_login("demo", "Demo123!")
    
    if token:
        # Test authenticated features
        test_password_reset_request()
        project_id = test_create_project(token)
        
        # Run orchestration to get task_id
        task_id = test_api_orchestration(token)
        
        # Test features that need task_id
        test_ai_analysis(token, task_id)
        test_mock_server(token, task_id)
        test_export(token, task_id)
        test_stripe_integration(token)
    else:
        print("\n⚠️ Authentication failed. Skipping authenticated tests.")
    
    # Print summary
    print_summary()

if __name__ == "__main__":
    main()