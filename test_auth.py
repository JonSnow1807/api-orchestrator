#!/usr/bin/env python3
"""
Test authentication endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """Test complete authentication flow"""
    
    # Test data
    test_user = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!"
    }
    
    print("🔐 Testing Authentication System")
    print("=" * 50)
    
    # 1. Test Registration
    print("\n1. Testing Registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    
    if response.status_code == 201:
        user_data = response.json()
        print("✅ Registration successful!")
        print(f"   User ID: {user_data['id']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Username: {user_data['username']}")
        print(f"   Subscription: {user_data['subscription_tier']}")
        print(f"   API Calls Remaining: {user_data['api_calls_remaining']}")
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Error: {response.json()}")
    
    # 2. Test Login
    print("\n2. Testing Login...")
    login_data = {
        "username": test_user["email"],  # OAuth2 form expects username field
        "password": test_user["password"]
    }
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,  # Form data, not JSON
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        tokens = response.json()
        print("✅ Login successful!")
        print(f"   Access Token: {tokens['access_token'][:50]}...")
        if tokens.get('refresh_token'):
            print(f"   Refresh Token: {tokens['refresh_token'][:50]}...")
        access_token = tokens['access_token']
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Error: {response.json()}")
        return
    
    # 3. Test Getting Current User
    print("\n3. Testing Get Current User...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    
    if response.status_code == 200:
        user_info = response.json()
        print("✅ Get current user successful!")
        print(f"   User: {user_info['username']} ({user_info['email']})")
        print(f"   Active: {user_info['is_active']}")
        print(f"   API Calls Remaining: {user_info['api_calls_remaining']}")
    else:
        print(f"❌ Get current user failed: {response.status_code}")
        print(f"   Error: {response.json()}")
    
    # 4. Test Protected Endpoint (orchestrate)
    print("\n4. Testing Protected Endpoint (Orchestrate)...")
    orchestrate_data = {
        "source_type": "directory",
        "source_path": "/test/path"
    }
    response = requests.post(
        f"{BASE_URL}/api/orchestrate",
        json=orchestrate_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Protected endpoint access successful!")
        print(f"   Task ID: {result['task_id']}")
        print(f"   Status: {result['status']}")
    else:
        print(f"⚠️  Protected endpoint returned: {response.status_code}")
        # This might fail for other reasons (path not found, etc.)
    
    # 5. Test Invalid Token
    print("\n5. Testing Invalid Token...")
    bad_headers = {"Authorization": "Bearer invalid-token-here"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=bad_headers)
    
    if response.status_code == 401:
        print("✅ Invalid token correctly rejected!")
    else:
        print(f"❌ Unexpected response for invalid token: {response.status_code}")
    
    # 6. Test Duplicate Registration
    print("\n6. Testing Duplicate Registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=test_user)
    
    if response.status_code == 400:
        print("✅ Duplicate registration correctly rejected!")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"❌ Unexpected response for duplicate: {response.status_code}")
    
    # 7. Test Refresh Token
    print("\n7. Testing Refresh Token...")
    if 'refresh_token' in tokens:
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": tokens['refresh_token']}
        )
        
        if response.status_code == 200:
            new_tokens = response.json()
            print("✅ Token refresh successful!")
            print(f"   New Access Token: {new_tokens['access_token'][:50]}...")
        else:
            print(f"❌ Token refresh failed: {response.status_code}")
    
    # 8. Test Logout
    print("\n8. Testing Logout...")
    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
    
    if response.status_code == 200:
        print("✅ Logout successful!")
        print(f"   Message: {response.json()['message']}")
    else:
        print(f"❌ Logout failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("✅ Authentication tests completed!")

if __name__ == "__main__":
    print("⚠️  Make sure the FastAPI server is running on port 8000")
    print("    Run: python -m src.main")
    print()
    
    try:
        test_auth_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        print("   Run: python -m src.main")
    except Exception as e:
        print(f"❌ Error: {e}")