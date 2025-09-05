#!/usr/bin/env python3
"""
Test project management CRUD endpoints
"""

import pytest
import requests
import json
import time

BASE_URL = "http://localhost:8000"

@pytest.mark.integration
def test_project_crud():
    """Test project CRUD operations"""
    
    print("📁 Testing Project Management System")
    print("=" * 50)
    
    # First register and login
    print("\n1. Creating test user...")
    user_data = {
        "email": "project_test@example.com",
        "username": "projectuser",
        "password": "TestPass123!"
    }
    
    # Register
    r = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    if r.status_code != 201:
        print(f"   Registration failed, trying login...")
    
    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    r = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if r.status_code != 200:
        print(f"❌ Login failed: {r.status_code}")
        return
    
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    print("✅ Logged in successfully")
    
    # 2. Create a project
    print("\n2. Creating a project...")
    project_data = {
        "name": "My API Project",
        "description": "Test project for API orchestration",
        "source_type": "directory",
        "source_path": "/Users/test/my-api"
    }
    
    r = requests.post(f"{BASE_URL}/api/projects", json=project_data, headers=headers)
    
    if r.status_code == 201:
        project = r.json()
        project_id = project["id"]
        print(f"✅ Project created!")
        print(f"   ID: {project_id}")
        print(f"   Name: {project['name']}")
        print(f"   Created: {project['created_at']}")
    else:
        print(f"❌ Failed to create project: {r.status_code}")
        print(f"   Error: {r.text}")
        return
    
    # 3. List projects
    print("\n3. Listing projects...")
    r = requests.get(f"{BASE_URL}/api/projects", headers=headers)
    
    if r.status_code == 200:
        result = r.json()
        print(f"✅ Found {result['total']} projects")
        for proj in result["projects"]:
            print(f"   - {proj['name']} (ID: {proj['id']})")
    else:
        print(f"❌ Failed to list projects: {r.status_code}")
    
    # 4. Get specific project
    print(f"\n4. Getting project {project_id}...")
    r = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=headers)
    
    if r.status_code == 200:
        proj = r.json()
        print(f"✅ Retrieved project: {proj['name']}")
        print(f"   APIs: {proj['api_count']}")
        print(f"   Tasks: {proj['task_count']}")
    else:
        print(f"❌ Failed to get project: {r.status_code}")
    
    # 5. Update project
    print("\n5. Updating project...")
    update_data = {
        "description": "Updated description for testing",
        "source_path": "/Users/test/updated-path"
    }
    
    r = requests.put(
        f"{BASE_URL}/api/projects/{project_id}",
        json=update_data,
        headers=headers
    )
    
    if r.status_code == 200:
        updated = r.json()
        print(f"✅ Project updated!")
        print(f"   New description: {updated['description']}")
        print(f"   New path: {updated['source_path']}")
    else:
        print(f"❌ Failed to update: {r.status_code}")
    
    # 6. Get project stats
    print("\n6. Getting project statistics...")
    r = requests.get(f"{BASE_URL}/api/projects/stats/overview", headers=headers)
    
    if r.status_code == 200:
        stats = r.json()
        print(f"✅ Statistics retrieved!")
        print(f"   Total projects: {stats['total_projects']}")
        print(f"   Total APIs: {stats['total_apis']}")
        print(f"   Hours saved: {stats['hours_saved']}")
    else:
        print(f"❌ Failed to get stats: {r.status_code}")
    
    # 7. Clone project
    print("\n7. Cloning project...")
    r = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/clone?new_name=Cloned+Project",
        headers=headers
    )
    
    if r.status_code == 201:
        cloned = r.json()
        cloned_id = cloned["id"]
        print(f"✅ Project cloned!")
        print(f"   New ID: {cloned_id}")
        print(f"   Name: {cloned['name']}")
    else:
        print(f"❌ Failed to clone: {r.status_code}")
    
    # 8. Search projects
    print("\n8. Searching projects...")
    r = requests.get(
        f"{BASE_URL}/api/projects?search=API",
        headers=headers
    )
    
    if r.status_code == 200:
        result = r.json()
        print(f"✅ Search found {result['total']} projects matching 'API'")
    else:
        print(f"❌ Search failed: {r.status_code}")
    
    # 9. Start orchestration for project
    print("\n9. Starting orchestration for project...")
    r = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/orchestrate",
        headers=headers
    )
    
    if r.status_code == 200:
        orch_result = r.json()
        print(f"✅ Orchestration started!")
        print(f"   Task ID: {orch_result['task_id']}")
        print(f"   Status: {orch_result['status']}")
    else:
        print(f"❌ Orchestration failed: {r.status_code}")
    
    # 10. Delete project
    print(f"\n10. Deleting project {project_id}...")
    r = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=headers)
    
    if r.status_code == 204:
        print(f"✅ Project deleted successfully")
    else:
        print(f"❌ Failed to delete: {r.status_code}")
    
    # Cleanup - delete cloned project
    if 'cloned_id' in locals():
        requests.delete(f"{BASE_URL}/api/projects/{cloned_id}", headers=headers)
    
    print("\n" + "=" * 50)
    print("✅ Project CRUD tests completed!")

if __name__ == "__main__":
    print("Testing Project Management CRUD endpoints...")
    print("Make sure the server is running: python -m src.main")
    print()
    
    time.sleep(2)  # Give server time to start
    
    try:
        test_project_crud()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        print("   Run: python -m src.main")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()