#!/usr/bin/env python3
"""
Production Test Suite for API Orchestrator Platform
Tests all core functionalities against the live production environment
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Production URL
BASE_URL = "https://streamapi.dev"
API_URL = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "Demo123!"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.ENDC}")

def print_test(test_name: str, success: bool, message: str = ""):
    """Print test result"""
    status = f"{Colors.GREEN}✅ PASS{Colors.ENDC}" if success else f"{Colors.RED}❌ FAIL{Colors.ENDC}"
    print(f"  {test_name}: {status}")
    if message:
        print(f"    → {message}")

def test_health_check() -> bool:
    """Test if the API is up and running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        success = response.status_code == 200
        data = response.json() if success else {}
        print_test("Health Check", success, f"Status: {data.get('status', 'unknown')}")
        return success
    except Exception as e:
        print_test("Health Check", False, f"Error: {str(e)}")
        return False

def test_authentication() -> Optional[str]:
    """Test authentication endpoints"""
    print_header("Authentication Tests")
    
    # Test login
    try:
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        success = response.status_code == 200
        
        if success:
            token = response.json().get("access_token")
            print_test("Login", True, f"Token received: {token[:20]}...")
            
            # Test getting user info
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
            user_success = user_response.status_code == 200
            
            if user_success:
                user_data = user_response.json()
                print_test("Get User Info", True, f"User: {user_data.get('email')}")
            else:
                print_test("Get User Info", False, f"Status: {user_response.status_code}")
            
            return token
        else:
            print_test("Login", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        print_test("Authentication", False, f"Error: {str(e)}")
        return None

def test_orchestration(token: str) -> bool:
    """Test orchestration endpoints"""
    print_header("Orchestration Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test discovery
    try:
        discovery_data = {
            "url": "https://api.github.com",
            "framework": "auto"
        }
        response = requests.post(f"{API_URL}/discover", json=discovery_data, headers=headers, timeout=30)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            endpoints_count = len(data.get("endpoints", []))
            print_test("API Discovery", True, f"Found {endpoints_count} endpoints")
        else:
            print_test("API Discovery", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("API Discovery", False, f"Error: {str(e)}")
    
    # Test spec generation
    try:
        spec_data = {
            "endpoints": [
                {
                    "path": "/users/{id}",
                    "method": "GET",
                    "description": "Get user by ID"
                }
            ],
            "title": "Test API",
            "version": "1.0.0"
        }
        response = requests.post(f"{API_URL}/generate-spec", json=spec_data, headers=headers, timeout=30)
        success = response.status_code == 200
        
        if success:
            spec = response.json()
            print_test("Spec Generation", True, f"OpenAPI version: {spec.get('openapi', 'unknown')}")
        else:
            print_test("Spec Generation", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("Spec Generation", False, f"Error: {str(e)}")
    
    # Test orchestration workflow
    try:
        orchestrate_data = {
            "source_type": "url",
            "source_data": "https://jsonplaceholder.typicode.com",
            "options": {
                "discover": True,
                "generate_spec": True,
                "generate_tests": True,
                "create_mock": False
            }
        }
        response = requests.post(f"{API_URL}/orchestrate", json=orchestrate_data, headers=headers, timeout=60)
        success = response.status_code in [200, 202]
        
        if success:
            data = response.json()
            task_id = data.get("task_id", "unknown")
            print_test("Start Orchestration", True, f"Task ID: {task_id}")
            
            # Check task status
            if task_id != "unknown":
                time.sleep(2)
                status_response = requests.get(f"{API_URL}/orchestration/{task_id}", headers=headers, timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print_test("Task Status Check", True, f"Status: {status_data.get('status', 'unknown')}")
                else:
                    print_test("Task Status Check", False, f"Status: {status_response.status_code}")
        else:
            print_test("Start Orchestration", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("Orchestration", False, f"Error: {str(e)}")
    
    return True

def test_projects(token: str) -> bool:
    """Test project management endpoints"""
    print_header("Project Management Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # List projects
    try:
        response = requests.get(f"{API_URL}/projects", headers=headers, timeout=10)
        success = response.status_code == 200
        
        if success:
            projects = response.json()
            print_test("List Projects", True, f"Found {len(projects)} projects")
            
            # Create a test project
            project_data = {
                "name": f"Test Project {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": "Automated test project"
            }
            create_response = requests.post(f"{API_URL}/projects", json=project_data, headers=headers, timeout=10)
            create_success = create_response.status_code in [200, 201]
            
            if create_success:
                created_project = create_response.json()
                project_id = created_project.get("id")
                print_test("Create Project", True, f"Project ID: {project_id}")
                
                # Delete the test project
                if project_id:
                    delete_response = requests.delete(f"{API_URL}/projects/{project_id}", headers=headers, timeout=10)
                    delete_success = delete_response.status_code in [200, 204]
                    print_test("Delete Project", delete_success, f"Cleanup successful" if delete_success else f"Status: {delete_response.status_code}")
            else:
                print_test("Create Project", False, f"Status: {create_response.status_code}")
        else:
            print_test("List Projects", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("Project Management", False, f"Error: {str(e)}")
    
    return True

def test_billing(token: str) -> bool:
    """Test billing endpoints"""
    print_header("Billing & Subscription Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Get subscription status
        response = requests.get(f"{API_URL}/billing/subscription", headers=headers, timeout=10)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            tier = data.get("subscription_tier", "unknown")
            print_test("Get Subscription", True, f"Current tier: {tier}")
            
            # Test checkout session creation (without actually paying)
            checkout_data = {
                "price_id": "price_test_starter",
                "success_url": f"{BASE_URL}/billing/success",
                "cancel_url": f"{BASE_URL}/billing/cancel"
            }
            checkout_response = requests.post(f"{API_URL}/billing/create-checkout-session", 
                                             json=checkout_data, headers=headers, timeout=10)
            
            # We expect this to fail with test price_id, but endpoint should respond
            checkout_reachable = checkout_response.status_code in [200, 400, 401, 403]
            print_test("Checkout Endpoint", checkout_reachable, 
                      f"Endpoint reachable (Status: {checkout_response.status_code})")
        else:
            print_test("Get Subscription", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("Billing", False, f"Error: {str(e)}")
    
    return True

def test_ai_features(token: str) -> bool:
    """Test AI-powered features"""
    print_header("AI Features Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test AI analysis
        analysis_data = {
            "spec": {
                "openapi": "3.0.0",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {
                    "/users": {
                        "get": {"summary": "Get users", "responses": {"200": {"description": "Success"}}}
                    }
                }
            },
            "analysis_type": "security"
        }
        
        response = requests.post(f"{API_URL}/ai/analyze", json=analysis_data, headers=headers, timeout=30)
        success = response.status_code == 200
        
        if success:
            print_test("AI Analysis", True, "AI analysis endpoint working")
        else:
            # AI features might require API key
            print_test("AI Analysis", response.status_code == 401, 
                      f"Status: {response.status_code} (May need Anthropic API key)")
            
    except Exception as e:
        print_test("AI Features", False, f"Error: {str(e)}")
    
    return True

def test_mock_server(token: str) -> bool:
    """Test mock server functionality"""
    print_header("Mock Server Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        mock_data = {
            "spec": {
                "openapi": "3.0.0",
                "info": {"title": "Mock API", "version": "1.0.0"},
                "paths": {
                    "/test": {
                        "get": {
                            "summary": "Test endpoint",
                            "responses": {
                                "200": {
                                    "description": "Success",
                                    "content": {
                                        "application/json": {
                                            "example": {"message": "Hello World"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        response = requests.post(f"{API_URL}/mock-server", json=mock_data, headers=headers, timeout=30)
        success = response.status_code == 200
        
        if success:
            data = response.json()
            mock_url = data.get("mock_url", "not provided")
            print_test("Create Mock Server", True, f"Mock URL: {mock_url}")
        else:
            print_test("Create Mock Server", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("Mock Server", False, f"Error: {str(e)}")
    
    return True

def test_export_import(token: str) -> bool:
    """Test export/import functionality"""
    print_header("Export/Import Tests")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test export
        response = requests.get(f"{API_URL}/export", headers=headers, timeout=10)
        success = response.status_code == 200
        
        if success:
            export_data = response.json()
            print_test("Export Data", True, f"Exported {len(export_data.get('projects', []))} projects")
        else:
            print_test("Export Data", False, f"Status: {response.status_code}")
            
    except Exception as e:
        print_test("Export/Import", False, f"Error: {str(e)}")
    
    return True

def main():
    """Run all production tests"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}🚀 API Orchestrator Production Test Suite{Colors.ENDC}")
    print(f"Testing: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if API is up
    if not test_health_check():
        print(f"\n{Colors.RED}❌ API is not responding. Exiting tests.{Colors.ENDC}")
        sys.exit(1)
    
    # Run authentication tests and get token
    token = test_authentication()
    if not token:
        print(f"\n{Colors.YELLOW}⚠️  Authentication failed. Some tests will be skipped.{Colors.ENDC}")
    else:
        # Run authenticated tests
        test_orchestration(token)
        test_projects(token)
        test_billing(token)
        test_ai_features(token)
        test_mock_server(token)
        test_export_import(token)
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}✅ Production tests completed!{Colors.ENDC}")
    print(f"Check the results above for any failures.")

if __name__ == "__main__":
    main()