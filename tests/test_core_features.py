#!/usr/bin/env python3
"""
Test script for core API Orchestrator features
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "apitest@example.com"
TEST_PASSWORD = "APITest123"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message, status="info"):
    if status == "success":
        print(f"{GREEN}✓ {message}{RESET}")
    elif status == "error":
        print(f"{RED}✗ {message}{RESET}")
    elif status == "warning":
        print(f"{YELLOW}⚠ {message}{RESET}")
    else:
        print(f"{BLUE}ℹ {message}{RESET}")

class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        
    def login(self):
        """Login and get access token"""
        print_status("Attempting to login...", "info")
        
        # Try to login
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": TEST_EMAIL,  # OAuth2 uses username field for email
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print_status(f"Logged in successfully", "success")
            return True
        else:
            print_status(f"Login failed: {response.status_code} - {response.text}", "error")
            return False
    
    def test_api_discovery(self):
        """Test API Discovery feature"""
        print_status("\n=== Testing API Discovery ===", "info")
        
        # Create a simple test API file
        test_dir = Path("test_api_sample")
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "sample_api.py"
        test_file.write_text('''
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    return jsonify({"users": []})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user"""
    return jsonify({"user_id": user_id})

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    return jsonify({"message": "User created"})
''')
        
        # Test discovery
        response = requests.post(
            f"{BASE_URL}/api/orchestrate",
            json={
                "source_type": "directory",
                "source_path": str(test_dir.absolute())
            },
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            print_status(f"Discovery started with task ID: {task_id}", "success")
            
            # Wait for task to complete
            time.sleep(5)
            
            # Check task status
            status_response = requests.get(
                f"{BASE_URL}/api/tasks/{task_id}",
                headers=self.headers
            )
            
            if status_response.status_code == 200:
                task_data = status_response.json()
                print_status(f"Task status: {task_data.get('status')}", "info")
                
                if task_data.get('status') == 'completed':
                    print_status("API Discovery completed successfully", "success")
                    return True
                else:
                    print_status(f"Task not completed: {json.dumps(task_data, indent=2)}", "warning")
            else:
                print_status(f"Failed to get task status: {status_response.text}", "error")
        else:
            print_status(f"Discovery failed: {response.status_code} - {response.text}", "error")
        
        return False
    
    def test_project_creation(self):
        """Test Project Creation"""
        print_status("\n=== Testing Project Creation ===", "info")
        
        response = requests.post(
            f"{BASE_URL}/api/projects",
            json={
                "name": "Test Project",
                "description": "Testing core features",
                "source_type": "upload"
            },
            headers=self.headers
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            project_id = data.get("id")
            print_status(f"Project created with ID: {project_id}", "success")
            return project_id
        else:
            print_status(f"Project creation failed: {response.status_code} - {response.text}", "error")
            return None
    
    def test_mock_server(self):
        """Test Mock Server feature"""
        print_status("\n=== Testing Mock Server ===", "info")
        
        # Create a simple OpenAPI spec
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "version": "1.0.0"
            },
            "paths": {
                "/api/test": {
                    "get": {
                        "summary": "Test endpoint",
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "message": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Start mock server
        response = requests.post(
            f"{BASE_URL}/api/mock-server/start",
            json={"spec": openapi_spec},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"Mock server started on port: {data.get('port')}", "success")
            
            # Test mock endpoint
            mock_response = requests.get(f"http://localhost:{data.get('port')}/api/test")
            if mock_response.status_code == 200:
                print_status("Mock server responding correctly", "success")
                return True
            else:
                print_status("Mock server not responding", "warning")
        else:
            print_status(f"Mock server start failed: {response.status_code} - {response.text}", "error")
        
        return False
    
    def test_export_import(self):
        """Test Export/Import functionality"""
        print_status("\n=== Testing Export/Import ===", "info")
        
        # Get available export formats
        response = requests.get(
            f"{BASE_URL}/api/export/formats",
            headers=self.headers
        )
        
        if response.status_code == 200:
            formats = response.json()
            print_status(f"Available export formats: {', '.join(formats)}", "info")
            return True
        else:
            print_status(f"Failed to get export formats: {response.text}", "error")
            return False
    
    def run_all_tests(self):
        """Run all core feature tests"""
        print_status("\n" + "="*50, "info")
        print_status("Starting Core Features Test Suite", "info")
        print_status("="*50 + "\n", "info")
        
        # Login first
        if not self.login():
            print_status("Cannot continue without login", "error")
            return
        
        # Run tests
        results = {
            "Project Creation": self.test_project_creation(),
            "API Discovery": self.test_api_discovery(),
            "Mock Server": self.test_mock_server(),
            "Export/Import": self.test_export_import()
        }
        
        # Summary
        print_status("\n" + "="*50, "info")
        print_status("Test Results Summary", "info")
        print_status("="*50, "info")
        
        for feature, result in results.items():
            if result:
                print_status(f"{feature}: PASSED", "success")
            else:
                print_status(f"{feature}: FAILED", "error")
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        print_status(f"\nTotal: {passed}/{total} tests passed", "info")
        
        if passed == total:
            print_status("All core features are working! ✨", "success")
        else:
            print_status("Some features need attention", "warning")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()