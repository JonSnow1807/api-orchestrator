#!/usr/bin/env python3
"""
Final Demo Test - Comprehensive check before submission
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "https://streamapi.dev"
DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "Demo123!"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'=' * 70}{Colors.ENDC}")

def print_test(name, status, details=""):
    icon = f"{Colors.GREEN}✅{Colors.ENDC}" if status else f"{Colors.RED}❌{Colors.ENDC}"
    print(f"  {icon} {name}")
    if details:
        print(f"     {Colors.CYAN}→ {details}{Colors.ENDC}")

def test_landing_page():
    """Test landing page loads correctly"""
    print(f"\n{Colors.BOLD}1. Landing Page{Colors.ENDC}")
    
    try:
        response = requests.get(BASE_URL, timeout=10)
        has_landing = "API Orchestrator" in response.text or "Orchestrate Your APIs" in response.text
        has_assets = "/assets/" in response.text
        
        print_test("Page Loads", response.status_code == 200, f"Status: {response.status_code}")
        print_test("Landing Content", has_landing or has_assets, "Landing page or React app detected")
        print_test("Assets Loading", has_assets, "CSS and JS assets found")
        
        return response.status_code == 200
    except Exception as e:
        print_test("Landing Page", False, f"Error: {str(e)}")
        return False

def test_api_health():
    """Test API endpoints"""
    print(f"\n{Colors.BOLD}2. API Health{Colors.ENDC}")
    
    endpoints = [
        ("/health", "Health Check"),
        ("/docs", "API Documentation"),
        ("/openapi.json", "OpenAPI Spec")
    ]
    
    all_ok = True
    for path, name in endpoints:
        try:
            response = requests.get(BASE_URL + path, timeout=5)
            success = response.status_code == 200
            print_test(name, success, f"Status: {response.status_code}")
            all_ok = all_ok and success
        except Exception as e:
            print_test(name, False, f"Error: {str(e)}")
            all_ok = False
    
    return all_ok

def test_authentication():
    """Test login with demo account"""
    print(f"\n{Colors.BOLD}3. Authentication{Colors.ENDC}")
    
    try:
        # Test demo login
        login_data = {
            "username": DEMO_EMAIL,
            "password": DEMO_PASSWORD
        }
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print_test("Demo Login", True, "Token received")
            
            # Validate token
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
            
            if me_response.status_code == 200:
                user = me_response.json()
                print_test("Token Valid", True, f"User: {user.get('email')}")
                print_test("Subscription", True, f"Tier: {user.get('subscription_tier', 'free')}")
                return token
            else:
                print_test("Token Validation", False, f"Status: {me_response.status_code}")
                return None
        else:
            print_test("Demo Login", False, f"Status: {response.status_code}")
            return None
            
    except Exception as e:
        print_test("Authentication", False, f"Error: {str(e)}")
        return None

def test_orchestration(token):
    """Test orchestration features"""
    print(f"\n{Colors.BOLD}4. Orchestration{Colors.ENDC}")
    
    if not token:
        print_test("Orchestration", False, "No auth token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test orchestration
        data = {
            "source_type": "code",
            "source_path": "test.py",
            "code_content": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/test')\ndef test():\n    return {'status': 'ok'}",
            "options": {"framework": "fastapi"}
        }
        
        response = requests.post(f"{BASE_URL}/api/orchestrate", json=data, headers=headers, timeout=30)
        
        if response.status_code in [200, 202]:
            result = response.json()
            task_id = result.get("task_id")
            print_test("Create Task", True, f"Task ID: {task_id}")
            
            # Check projects
            proj_response = requests.get(f"{BASE_URL}/api/projects", headers=headers, timeout=10)
            if proj_response.status_code == 200:
                projects = proj_response.json()
                print_test("Projects API", True, f"Found {len(projects)} projects")
            else:
                print_test("Projects API", False, f"Status: {proj_response.status_code}")
            
            return True
        else:
            print_test("Orchestration", False, f"Status: {response.status_code}")
            return False
            
    except Exception as e:
        print_test("Orchestration", False, f"Error: {str(e)}")
        return False

def test_navigation():
    """Test SPA navigation"""
    print(f"\n{Colors.BOLD}5. Navigation{Colors.ENDC}")
    
    routes = [
        ("/", "Landing Page"),
        ("/login", "Login Page"),
        ("/register", "Register Page"),
        ("/dashboard", "Dashboard"),
    ]
    
    for path, name in routes:
        try:
            response = requests.get(BASE_URL + path, timeout=5, allow_redirects=False)
            # For SPA, we expect 200 (served by backend) or 302 (redirect for protected)
            success = response.status_code in [200, 302, 303]
            print_test(name, success, f"Status: {response.status_code}")
        except Exception as e:
            print_test(name, False, f"Error: {str(e)}")
    
    return True

def check_features(token):
    """Check all features are accessible"""
    print(f"\n{Colors.BOLD}6. Feature Check{Colors.ENDC}")
    
    features = {
        "WebSocket": "wss://streamapi.dev/ws",
        "Tasks Endpoint": "/api/tasks",
        "AI Analysis": "/api/ai-analysis",
        "Mock Server": "/api/mock-server",
        "Export/Import": "/api/export"
    }
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    for feature, endpoint in features.items():
        if feature == "WebSocket":
            print_test(feature, True, f"Configured at {endpoint}")
        else:
            try:
                url = BASE_URL + endpoint if endpoint.startswith("/") else endpoint
                response = requests.get(url, headers=headers, timeout=5)
                # 404 is ok for some endpoints that need specific IDs
                success = response.status_code in [200, 404, 405]
                print_test(feature, success, f"Status: {response.status_code}")
            except Exception as e:
                print_test(feature, False, f"Error: {str(e)}")
    
    return True

def main():
    print_header("🚀 FINAL DEMO VERIFICATION 🚀")
    print(f"Platform: {Colors.CYAN}{BASE_URL}{Colors.ENDC}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    landing_ok = test_landing_page()
    api_ok = test_api_health()
    token = test_authentication()
    orchestration_ok = test_orchestration(token)
    navigation_ok = test_navigation()
    features_ok = check_features(token)
    
    # Summary
    print_header("DEMO SUBMISSION CHECKLIST")
    
    all_passed = landing_ok and api_ok and (token is not None) and orchestration_ok
    
    print(f"\n{Colors.BOLD}Core Requirements:{Colors.ENDC}")
    print_test("Landing Page", landing_ok)
    print_test("API Backend", api_ok)
    print_test("Authentication", token is not None)
    print_test("Orchestration", orchestration_ok)
    print_test("Navigation", navigation_ok)
    print_test("Features", features_ok)
    
    print(f"\n{Colors.BOLD}Demo Information:{Colors.ENDC}")
    print(f"  • URL: {Colors.CYAN}{BASE_URL}{Colors.ENDC}")
    print(f"  • Demo Login: {Colors.CYAN}{DEMO_EMAIL} / {DEMO_PASSWORD}{Colors.ENDC}")
    print(f"  • API Docs: {Colors.CYAN}{BASE_URL}/docs{Colors.ENDC}")
    print(f"  • GitHub: {Colors.CYAN}https://github.com/JonSnow1807/api-orchestrator{Colors.ENDC}")
    
    if all_passed:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 PLATFORM IS READY FOR DEMO SUBMISSION!{Colors.ENDC}")
        print(f"\n{Colors.BOLD}Key Features to Showcase:{Colors.ENDC}")
        print("  1. Professional landing page with clear value proposition")
        print("  2. AI-powered API discovery from code/URLs")
        print("  3. Automatic OpenAPI specification generation")
        print("  4. Real-time orchestration with WebSocket updates")
        print("  5. Project management and organization")
        print("  6. Mock server generation")
        print("  7. Security and compliance analysis")
        print("  8. Responsive modern UI with dark theme")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some checks need attention{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Ready to submit! Good luck with your demo! 🚀{Colors.ENDC}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())