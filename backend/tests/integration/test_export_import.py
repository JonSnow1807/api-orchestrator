#!/usr/bin/env python3
"""
Test export/import functionality
"""

import pytest
import requests
import json
import time

BASE_URL = "http://localhost:8000"

@pytest.mark.integration
def test_export_import():
    """Test export and import functionality"""
    
    print("📦 Testing Export/Import System")
    print("=" * 50)
    
    # First, login to get auth token
    print("\n1. Logging in...")
    login_data = {
        "username": "test@example.com",
        "password": "TestPass123!"
    }
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed. Please run test_auth.py first to create user")
        return
    
    tokens = response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    print("✅ Logged in successfully")
    
    # 2. Get available export formats
    print("\n2. Getting available export formats...")
    response = requests.get(f"{BASE_URL}/api/export/formats", headers=headers)
    
    if response.status_code == 200:
        formats_data = response.json()
        print(f"✅ Subscription tier: {formats_data['subscription_tier']}")
        print(f"   Available formats: {formats_data['available_formats']}")
    else:
        print(f"❌ Failed to get formats: {response.status_code}")
    
    # 3. Create a sample OpenAPI spec to test with
    sample_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "description": "Test API for export/import",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "http://localhost:8000",
                "description": "Local server"
            }
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "description": "Retrieve a list of all users",
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "email": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create a user",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created"
                        }
                    }
                }
            }
        }
    }
    
    # 4. Save sample spec as JSON file
    print("\n3. Creating test OpenAPI spec file...")
    with open("/tmp/test_openapi.json", "w") as f:
        json.dump(sample_spec, f, indent=2)
    print("✅ Created test_openapi.json")
    
    # 5. Test import functionality
    print("\n4. Testing import...")
    with open("/tmp/test_openapi.json", "rb") as f:
        files = {"file": ("test_openapi.json", f, "application/json")}
        response = requests.post(
            f"{BASE_URL}/api/import",
            files=files,
            headers=headers
        )
    
    if response.status_code == 200:
        import_result = response.json()
        task_id = import_result["task_id"]
        print(f"✅ Import successful!")
        print(f"   Task ID: {task_id}")
        print(f"   Endpoints: {import_result['endpoints']}")
        print(f"   Schemas: {import_result['schemas']}")
    else:
        print(f"❌ Import failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # 6. Test export in different formats
    print("\n5. Testing export formats...")
    
    # Test JSON export
    print("\n   a) Testing JSON export...")
    response = requests.get(
        f"{BASE_URL}/api/export/{task_id}?format=json",
        headers=headers
    )
    
    if response.status_code == 200:
        exported_spec = response.json()
        print(f"   ✅ JSON export successful")
        print(f"      Title: {exported_spec['info']['title']}")
        print(f"      Paths: {len(exported_spec['paths'])}")
    else:
        print(f"   ❌ JSON export failed: {response.status_code}")
    
    # Test YAML export (if available)
    if "yaml" in formats_data.get("available_formats", []):
        print("\n   b) Testing YAML export...")
        response = requests.get(
            f"{BASE_URL}/api/export/{task_id}?format=yaml",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"   ✅ YAML export successful")
            print(f"      Size: {len(response.content)} bytes")
        else:
            print(f"   ❌ YAML export failed: {response.status_code}")
    
    # Test Postman export (if available)
    if "postman" in formats_data.get("available_formats", []):
        print("\n   c) Testing Postman export...")
        response = requests.get(
            f"{BASE_URL}/api/export/{task_id}?format=postman",
            headers=headers
        )
        
        if response.status_code == 200:
            postman_collection = response.json()
            print(f"   ✅ Postman export successful")
            print(f"      Collection: {postman_collection.get('info', {}).get('name', '')}")
            print(f"      Items: {len(postman_collection.get('item', []))}")
        else:
            print(f"   ❌ Postman export failed: {response.status_code}")
    
    # Test Markdown export (if available)
    if "markdown" in formats_data.get("available_formats", []):
        print("\n   d) Testing Markdown export...")
        response = requests.get(
            f"{BASE_URL}/api/export/{task_id}?format=markdown",
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"   ✅ Markdown export successful")
            print(f"      Size: {len(response.content)} bytes")
        else:
            print(f"   ❌ Markdown export failed: {response.status_code}")
    
    # 7. Test import of Postman collection
    print("\n6. Testing Postman import...")
    postman_collection = {
        "info": {
            "name": "Test Postman Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [
            {
                "name": "Get Products",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "http://api.example.com/products",
                        "host": ["api.example.com"],
                        "path": ["products"]
                    }
                }
            }
        ]
    }
    
    with open("/tmp/test_postman.json", "w") as f:
        json.dump(postman_collection, f)
    
    with open("/tmp/test_postman.json", "rb") as f:
        files = {"file": ("test_postman.json", f, "application/json")}
        response = requests.post(
            f"{BASE_URL}/api/import",
            files=files,
            headers=headers
        )
    
    if response.status_code == 200:
        import_result = response.json()
        print(f"✅ Postman import successful!")
        print(f"   Converted to OpenAPI spec")
        print(f"   Endpoints: {import_result['endpoints']}")
    else:
        print(f"❌ Postman import failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ Export/Import tests completed!")

if __name__ == "__main__":
    print("⚠️  Make sure the FastAPI server is running on port 8000")
    print("    Run: python -m src.main")
    print("⚠️  Also make sure you've run test_auth.py first to create a test user")
    print()
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    try:
        test_export_import()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        print("   Run: python -m src.main")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()