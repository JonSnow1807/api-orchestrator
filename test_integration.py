import requests
import json
import time
import websocket
import random
import string

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_email = f"test_{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com"
        self.password = "Test123!@#"
        self.results = []
    
    def log_result(self, test_name, status, details=""):
        result = f"{'✅' if status else '❌'} {test_name}"
        if details:
            result += f" - {details}"
        self.results.append(result)
        print(result)
    
    def test_register(self):
        """Test user registration"""
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/register", json={
                "email": self.user_email,
                "password": self.password,
                "name": "Test User"
            })
            if response.status_code == 200:
                self.log_result("User Registration", True, f"User {self.user_email} created")
                return True
            else:
                self.log_result("User Registration", False, f"Status {response.status_code}: {response.text[:100]}")
                return False
        except Exception as e:
            self.log_result("User Registration", False, str(e))
            return False
    
    def test_login(self):
        """Test user login"""
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/login", data={
                "username": self.user_email,
                "password": self.password
            })
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                self.log_result("User Login", True, "Token received")
                return True
            else:
                self.log_result("User Login", False, f"Status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("User Login", False, str(e))
            return False
    
    def test_v5_natural_language(self):
        """Test Natural Language Testing API"""
        try:
            # Test suggestions endpoint
            response = self.session.get(f"{BASE_URL}/api/v5/natural-language/suggestions")
            if response.status_code == 200:
                self.log_result("Natural Language - Get Suggestions", True)
            else:
                self.log_result("Natural Language - Get Suggestions", False, f"Status {response.status_code}")
            
            # Test generation endpoint
            response = self.session.post(f"{BASE_URL}/api/v5/natural-language/generate-test", json={
                "description": "Check if status is 200 and response contains email",
                "context": {}
            })
            if response.status_code == 200:
                data = response.json()
                self.log_result("Natural Language - Generate Test", True, f"Generated {len(data.get('tests', []))} tests")
            else:
                self.log_result("Natural Language - Generate Test", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Natural Language Testing", False, str(e))
    
    def test_v5_visualization(self):
        """Test Data Visualization API"""
        try:
            test_data = [
                {"name": "Product A", "sales": 100, "profit": 20},
                {"name": "Product B", "sales": 150, "profit": 35},
                {"name": "Product C", "sales": 200, "profit": 45}
            ]
            
            response = self.session.post(f"{BASE_URL}/api/v5/visualization/analyze", json={
                "data": test_data
            })
            if response.status_code == 200:
                data = response.json()
                self.log_result("Data Visualization - Analyze", True, f"Recommended: {', '.join(data.get('analysis', {}).get('recommended_viz', []))[:50]}")
            else:
                self.log_result("Data Visualization - Analyze", False, f"Status {response.status_code}")
            
            # Test transform
            response = self.session.post(f"{BASE_URL}/api/v5/visualization/transform", json={
                "data": test_data,
                "type": "bar",
                "options": {}
            })
            if response.status_code == 200:
                self.log_result("Data Visualization - Transform", True)
            else:
                self.log_result("Data Visualization - Transform", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Data Visualization", False, str(e))
    
    def test_v5_variables(self):
        """Test Enhanced Variables API"""
        try:
            # Create variable
            response = self.session.post(f"{BASE_URL}/api/v5/variables/create", json={
                "key": "TEST_API_KEY",
                "value": "secret123",
                "scope": "LOCAL"
            })
            if response.status_code == 200:
                self.log_result("Enhanced Variables - Create", True)
            else:
                self.log_result("Enhanced Variables - Create", False, f"Status {response.status_code}")
            
            # List variables
            response = self.session.get(f"{BASE_URL}/api/v5/variables/list")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Enhanced Variables - List", True, f"Found {len(data.get('variables', []))} variables")
            else:
                self.log_result("Enhanced Variables - List", False, f"Status {response.status_code}")
            
            # Detect sensitive
            response = self.session.post(f"{BASE_URL}/api/v5/variables/detect-sensitive", json={
                "value": "sk_test_123456789"
            })
            if response.status_code == 200:
                data = response.json()
                self.log_result("Enhanced Variables - Detect Sensitive", True, f"Is sensitive: {data.get('is_sensitive')}")
            else:
                self.log_result("Enhanced Variables - Detect Sensitive", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Enhanced Variables", False, str(e))
    
    def test_v5_privacy_ai(self):
        """Test Privacy AI API"""
        try:
            # Check compliance
            response = self.session.get(f"{BASE_URL}/api/v5/privacy-ai/compliance-check?regulation=GDPR")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Privacy AI - Compliance Check", True, f"GDPR compliant: {data.get('compliant')}")
            else:
                self.log_result("Privacy AI - Compliance Check", False, f"Status {response.status_code}")
            
            # Anonymize data
            response = self.session.post(f"{BASE_URL}/api/v5/privacy-ai/anonymize", json={
                "data": {
                    "email": "john.doe@example.com",
                    "phone": "+1-555-123-4567",
                    "ssn": "123-45-6789"
                }
            })
            if response.status_code == 200:
                self.log_result("Privacy AI - Anonymize", True)
            else:
                self.log_result("Privacy AI - Anonymize", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Privacy AI", False, str(e))
    
    def test_v5_offline_mode(self):
        """Test Offline Mode API"""
        try:
            # Save collection
            response = self.session.post(f"{BASE_URL}/api/v5/offline/save-collection", json={
                "collection": {
                    "name": "Test Collection",
                    "requests": []
                },
                "format": "JSON",
                "path": "./test_collections"
            })
            if response.status_code == 200:
                data = response.json()
                self.log_result("Offline Mode - Save Collection", True, f"Saved to {data.get('file_path', 'unknown')[:30]}")
            else:
                self.log_result("Offline Mode - Save Collection", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Offline Mode", False, str(e))
    
    def test_v5_virtualization(self):
        """Test Service Virtualization API"""
        try:
            # List services
            response = self.session.get(f"{BASE_URL}/api/v5/virtualization/services")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Service Virtualization - List", True, f"Found {len(data.get('services', []))} services")
            else:
                self.log_result("Service Virtualization - List", False, f"Status {response.status_code}")
            
            # Create service
            response = self.session.post(f"{BASE_URL}/api/v5/virtualization/create-service", json={
                "name": "Test Mock Service",
                "behavior": "STATIC"
            })
            if response.status_code == 200:
                self.log_result("Service Virtualization - Create", True)
            else:
                self.log_result("Service Virtualization - Create", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Service Virtualization", False, str(e))
    
    def test_projects(self):
        """Test Projects API"""
        try:
            # Create project
            response = self.session.post(f"{BASE_URL}/api/projects", json={
                "name": "Test Project",
                "description": "Integration test project"
            })
            if response.status_code == 200:
                data = response.json()
                project_id = data.get("id")
                self.log_result("Projects - Create", True, f"Project ID: {project_id}")
                
                # Get projects
                response = self.session.get(f"{BASE_URL}/api/projects")
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("Projects - List", True, f"Found {len(data.get('projects', []))} projects")
                else:
                    self.log_result("Projects - List", False, f"Status {response.status_code}")
            else:
                self.log_result("Projects - Create", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Projects", False, str(e))
    
    def test_websocket(self):
        """Test WebSocket connection"""
        try:
            if not self.token:
                self.log_result("WebSocket", False, "No token available")
                return
            
            ws_url = f"ws://localhost:8000/ws?token={self.token}"
            ws = websocket.create_connection(ws_url, timeout=5)
            
            # Send a test message
            ws.send(json.dumps({"type": "ping"}))
            
            # Wait for response
            ws.settimeout(2)
            try:
                result = ws.recv()
                self.log_result("WebSocket", True, "Connection established and responsive")
            except:
                self.log_result("WebSocket", True, "Connection established")
            
            ws.close()
        except Exception as e:
            self.log_result("WebSocket", False, str(e))
    
    def test_frontend_accessibility(self):
        """Test frontend pages are accessible"""
        try:
            pages = [
                ("/", "Landing Page"),
                ("/login", "Login Page"),
                ("/register", "Register Page"),
                ("/pricing", "Pricing Page")
            ]
            
            for path, name in pages:
                response = requests.get(f"{FRONTEND_URL}{path}")
                if response.status_code == 200:
                    self.log_result(f"Frontend - {name}", True)
                else:
                    self.log_result(f"Frontend - {name}", False, f"Status {response.status_code}")
        except Exception as e:
            self.log_result("Frontend Accessibility", False, str(e))
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*60)
        print("🧪 API ORCHESTRATOR INTEGRATION TESTS")
        print("="*60 + "\n")
        
        # Authentication tests
        print("📋 AUTHENTICATION TESTS")
        print("-"*40)
        self.test_register()
        self.test_login()
        
        # Core API tests
        print("\n📋 CORE API TESTS")
        print("-"*40)
        self.test_projects()
        self.test_websocket()
        
        # V5.0 Feature tests
        print("\n📋 V5.0 POSTMAN KILLER FEATURES")
        print("-"*40)
        self.test_v5_natural_language()
        self.test_v5_visualization()
        self.test_v5_variables()
        self.test_v5_privacy_ai()
        self.test_v5_offline_mode()
        self.test_v5_virtualization()
        
        # Frontend tests
        print("\n📋 FRONTEND TESTS")
        print("-"*40)
        self.test_frontend_accessibility()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        passed = sum(1 for r in self.results if "✅" in r)
        failed = sum(1 for r in self.results if "❌" in r)
        total = len(self.results)
        
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n⚠️ Failed Tests:")
            for result in self.results:
                if "❌" in result:
                    print(f"  {result}")
        
        return passed == total

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
