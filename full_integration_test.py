#!/usr/bin/env python3
"""
Full Integration Test Suite for API Orchestrator v5.0 POSTMAN KILLER
Tests all features comprehensively
"""

import requests
import json
import time
import websocket
import threading
from typing import Dict, Any, List
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
        
    def add_pass(self):
        self.passed += 1
        
    def add_fail(self, error):
        self.failed += 1
        self.errors.append(error)
        
    def add_skip(self):
        self.skipped += 1

class APIOrchestrator5TestSuite:
    def __init__(self):
        self.results = TestResult()
        self.token = None
        self.ws = None
        
    def print_header(self, text):
        print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
        print(f"{Colors.BOLD}{text.center(70)}{Colors.RESET}")
        print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")
        
    def print_section(self, text):
        print(f"\n{Colors.BLUE}{Colors.BOLD}▶ {text}{Colors.RESET}")
        
    def print_success(self, text):
        print(f"  {Colors.GREEN}✅ {text}{Colors.RESET}")
        self.results.add_pass()
        
    def print_failure(self, text):
        print(f"  {Colors.RED}❌ {text}{Colors.RESET}")
        self.results.add_fail(text)
        
    def print_skip(self, text):
        print(f"  {Colors.YELLOW}⏭️  {text}{Colors.RESET}")
        self.results.add_skip()
        
    def test_auth(self):
        """Test authentication system"""
        self.print_section("Authentication System")
        
        # Register new user
        register_data = {
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
        
        try:
            resp = requests.post(f"{BASE_URL}/auth/register", json=register_data)
            if resp.status_code == 201 or resp.status_code == 200:
                self.print_success("User registration")
            else:
                self.print_failure(f"User registration: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"User registration: {str(e)}")
            
        # Login with demo user
        try:
            resp = requests.post(f"{BASE_URL}/auth/login", 
                                data={"username": "demo@example.com", "password": "Demo123!"},
                                headers={"Content-Type": "application/x-www-form-urlencoded"})
            if resp.status_code == 200:
                self.token = resp.json()["access_token"]
                self.print_success("User login")
            else:
                self.print_failure(f"User login: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"User login: {str(e)}")
            
    def test_v5_natural_language(self):
        """Test Natural Language Testing features"""
        self.print_section("Natural Language Testing (v5.0)")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get suggestions
        try:
            resp = requests.get(f"{BASE_URL}/api/v5/natural-language/suggestions", headers=headers)
            if resp.status_code == 200:
                self.print_success("Get test suggestions")
            else:
                self.print_failure(f"Get test suggestions: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Get test suggestions: {str(e)}")
            
        # Generate test from description
        try:
            test_data = {
                "description": "Verify API returns user data with valid authentication",
                "context": {"endpoint": "/api/users", "method": "GET"}
            }
            resp = requests.post(f"{BASE_URL}/api/v5/natural-language/generate-test", 
                                json=test_data, headers=headers)
            if resp.status_code == 200:
                self.print_success("Generate test from description")
            else:
                self.print_failure(f"Generate test from description: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Generate test from description: {str(e)}")
            
    def test_v5_data_visualization(self):
        """Test Data Visualization features"""
        self.print_section("Data Visualization (v5.0)")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Analyze data
        try:
            data = {
                "data": [
                    {"month": "Jan", "revenue": 10000, "users": 100},
                    {"month": "Feb", "revenue": 15000, "users": 150},
                    {"month": "Mar", "revenue": 20000, "users": 200}
                ]
            }
            resp = requests.post(f"{BASE_URL}/api/v5/visualization/analyze", 
                                json=data, headers=headers)
            if resp.status_code == 200:
                self.print_success("Analyze data for visualization")
            else:
                self.print_failure(f"Analyze data: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Analyze data: {str(e)}")
            
        # Transform data
        try:
            transform_data = {
                "data": [{"x": i, "y": i**2} for i in range(10)],
                "visualization_type": "LINE",
                "options": {"title": "Quadratic Growth"}
            }
            resp = requests.post(f"{BASE_URL}/api/v5/visualization/transform", 
                                json=transform_data, headers=headers)
            if resp.status_code == 200:
                self.print_success("Transform data for charts")
            else:
                self.print_failure(f"Transform data: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Transform data: {str(e)}")
            
    def test_v5_variable_management(self):
        """Test Enhanced Variable Management"""
        self.print_section("Variable Management (v5.0)")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create variable
        try:
            var_data = {
                "name": "TEST_API_KEY",
                "value": "sk-test-12345",
                "scope": "WORKSPACE",
                "description": "Test API key"
            }
            resp = requests.post(f"{BASE_URL}/api/v5/variables/create", 
                                json=var_data, headers=headers)
            if resp.status_code in [200, 201]:
                self.print_success("Create variable")
            else:
                self.print_failure(f"Create variable: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Create variable: {str(e)}")
            
        # Detect sensitive data
        try:
            content = {
                "content": "API_KEY=sk-prod-abc123 PASSWORD=SuperSecret123!"
            }
            resp = requests.post(f"{BASE_URL}/api/v5/variables/detect-sensitive", 
                                json=content, headers=headers)
            if resp.status_code == 200:
                self.print_success("Detect sensitive data")
            else:
                self.print_failure(f"Detect sensitive: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Detect sensitive: {str(e)}")
            
    def test_v5_privacy_ai(self):
        """Test Privacy-First AI features"""
        self.print_section("Privacy-First AI (v5.0)")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Compliance check
        for regulation in ["GDPR", "HIPAA", "SOC2", "PCI-DSS"]:
            try:
                resp = requests.get(f"{BASE_URL}/api/v5/privacy-ai/compliance-check",
                                   params={"regulation": regulation}, headers=headers)
                if resp.status_code == 200:
                    self.print_success(f"Compliance check: {regulation}")
                else:
                    self.print_failure(f"Compliance {regulation}: {resp.status_code}")
            except Exception as e:
                self.print_failure(f"Compliance {regulation}: {str(e)}")
                
        # Data anonymization
        try:
            pii_data = {
                "data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "ssn": "123-45-6789",
                    "phone": "+1-555-0123"
                },
                "mode": "CLOUD"
            }
            resp = requests.post(f"{BASE_URL}/api/v5/privacy-ai/anonymize", 
                                json=pii_data, headers=headers)
            if resp.status_code == 200:
                self.print_success("Data anonymization")
            else:
                self.print_failure(f"Data anonymization: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Data anonymization: {str(e)}")
            
    def test_v5_offline_mode(self):
        """Test Offline Mode features"""
        self.print_section("Offline Mode (v5.0)")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Save collection
        try:
            collection = {
                "collection": {
                    "name": "Integration Test Collection",
                    "requests": [
                        {"name": "List Users", "method": "GET", "url": "/api/users"},
                        {"name": "Get User", "method": "GET", "url": "/api/users/1"}
                    ]
                },
                "format": "JSON"
            }
            resp = requests.post(f"{BASE_URL}/api/v5/offline/save-collection", 
                                json=collection, headers=headers)
            if resp.status_code in [200, 201]:
                self.print_success("Save offline collection")
            else:
                self.print_failure(f"Save collection: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Save collection: {str(e)}")
            
    def test_v5_service_virtualization(self):
        """Test Service Virtualization features"""
        self.print_section("Service Virtualization (v5.0)")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create mock service
        behaviors = ["STATIC", "DYNAMIC", "STATEFUL", "CONDITIONAL", "CHAOS"]
        
        for behavior in behaviors:
            try:
                service_data = {
                    "name": f"Mock Service {behavior}",
                    "behavior": behavior,
                    "endpoints": [
                        {"path": "/test", "method": "GET", "response": {"status": "ok"}}
                    ]
                }
                resp = requests.post(f"{BASE_URL}/api/v5/virtualization/create-service", 
                                    json=service_data, headers=headers)
                if resp.status_code in [200, 201]:
                    self.print_success(f"Create {behavior} mock service")
                else:
                    self.print_failure(f"Create {behavior} service: {resp.status_code}")
            except Exception as e:
                self.print_failure(f"Create {behavior} service: {str(e)}")
                
    def test_websocket(self):
        """Test WebSocket connections"""
        self.print_section("WebSocket Real-time Updates")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        try:
            # Simple WebSocket test
            ws = websocket.WebSocket()
            ws.connect(f"{WS_URL}?token={self.token}")
            
            # Send test message
            test_msg = {"type": "ping", "data": "test"}
            ws.send(json.dumps(test_msg))
            
            # Wait for response with timeout
            ws.settimeout(2)
            response = ws.recv()
            ws.close()
            
            self.print_success("WebSocket connection and messaging")
        except Exception as e:
            self.print_failure(f"WebSocket: {str(e)}")
            
    def test_core_features(self):
        """Test core API Orchestrator features"""
        self.print_section("Core API Orchestration Features")
        
        if not self.token:
            self.print_skip("Skipping - no authentication token")
            return
            
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create project
        try:
            project_data = {
                "name": "Integration Test Project",
                "description": "Testing all features"
            }
            resp = requests.post(f"{BASE_URL}/api/projects", 
                                json=project_data, headers=headers)
            if resp.status_code in [200, 201]:
                self.print_success("Create project")
                project_id = resp.json().get("id")
            else:
                self.print_failure(f"Create project: {resp.status_code}")
                project_id = None
        except Exception as e:
            self.print_failure(f"Create project: {str(e)}")
            project_id = None
            
        # Test discovery
        if project_id:
            try:
                discover_data = {
                    "project_id": project_id,
                    "source_type": "url",
                    "source": "https://api.github.com"
                }
                resp = requests.post(f"{BASE_URL}/api/discover", 
                                    json=discover_data, headers=headers)
                if resp.status_code == 200:
                    self.print_success("API discovery")
                else:
                    self.print_failure(f"API discovery: {resp.status_code}")
            except Exception as e:
                self.print_failure(f"API discovery: {str(e)}")
                
    def test_ui_integration(self):
        """Test frontend-backend integration"""
        self.print_section("UI/Frontend Integration")
        
        # Test frontend is served
        try:
            resp = requests.get(f"{BASE_URL}/")
            if resp.status_code == 200 and ("<!DOCTYPE html>" in resp.text or "<!doctype html>" in resp.text):
                self.print_success("Frontend served correctly")
            else:
                self.print_failure(f"Frontend serving: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"Frontend serving: {str(e)}")
            
        # Test API docs
        try:
            resp = requests.get(f"{BASE_URL}/docs")
            if resp.status_code == 200:
                self.print_success("API documentation available")
            else:
                self.print_failure(f"API docs: {resp.status_code}")
        except Exception as e:
            self.print_failure(f"API docs: {str(e)}")
            
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.results.passed + self.results.failed + self.results.skipped
        success_rate = (self.results.passed / total * 100) if total > 0 else 0
        
        print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  {Colors.GREEN}Passed:  {self.results.passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed:  {self.results.failed}{Colors.RESET}")
        print(f"  {Colors.YELLOW}Skipped: {self.results.skipped}{Colors.RESET}")
        print(f"  {Colors.BOLD}Total:   {total}{Colors.RESET}")
        print(f"\n  {Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")
        
        if self.results.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
            for error in self.results.errors[:10]:  # Show first 10 errors
                print(f"  • {error}")
                
        # Overall status
        print(f"\n{Colors.BOLD}Overall Status: ", end="")
        if success_rate >= 90:
            print(f"{Colors.GREEN}✅ EXCELLENT - Ready for Production{Colors.RESET}")
        elif success_rate >= 70:
            print(f"{Colors.YELLOW}⚠️  GOOD - Minor issues to fix{Colors.RESET}")
        elif success_rate >= 50:
            print(f"{Colors.YELLOW}⚠️  FAIR - Several issues need attention{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ NEEDS WORK - Major issues found{Colors.RESET}")
            
    def run_all_tests(self):
        """Run all integration tests"""
        self.print_header("API ORCHESTRATOR v5.0 - POSTMAN KILLER")
        self.print_header("FULL INTEGRATION TEST SUITE")
        
        print(f"\n{Colors.BOLD}Test Started:{Colors.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Colors.BOLD}Backend URL:{Colors.RESET} {BASE_URL}")
        
        # Run test suites
        self.test_auth()
        self.test_core_features()
        self.test_v5_natural_language()
        self.test_v5_data_visualization()
        self.test_v5_variable_management()
        self.test_v5_privacy_ai()
        self.test_v5_offline_mode()
        self.test_v5_service_virtualization()
        self.test_websocket()
        self.test_ui_integration()
        
        # Print summary
        self.print_summary()
        
        print(f"\n{Colors.BOLD}Test Completed:{Colors.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    suite = APIOrchestrator5TestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()