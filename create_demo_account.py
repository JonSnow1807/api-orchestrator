#!/usr/bin/env python3
"""
Create demo account for API Orchestrator
"""

import requests
import json
import time

BASE_URL = "https://streamapi.dev"

def create_demo_account():
    """Create the demo account"""
    print("Creating demo account...")
    
    demo_user = {
        "email": "demo@example.com",
        "username": "demo",
        "password": "Demo123!",
        "full_name": "Demo User"
    }
    
    try:
        # Try to register the demo account
        response = requests.post(f"{BASE_URL}/auth/register", json=demo_user, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"✅ Demo account created successfully!")
            print(f"   Email: {demo_user['email']}")
            print(f"   Password: {demo_user['password']}")
            return True
        elif response.status_code == 400:
            # Account might already exist
            print("ℹ️  Demo account may already exist, testing login...")
            
            # Test login
            login_data = {
                "username": demo_user["email"],
                "password": demo_user["password"]
            }
            login_response = requests.post(
                f"{BASE_URL}/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if login_response.status_code == 200:
                print("✅ Demo account exists and is working!")
                return True
            else:
                print(f"⚠️  Demo account exists but login failed: {login_response.status_code}")
                return False
        else:
            print(f"❌ Failed to create demo account: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    create_demo_account()