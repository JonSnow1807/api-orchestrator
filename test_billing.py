#!/usr/bin/env python
"""
Test script for billing system
Run this to verify billing features are working
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_billing_system():
    """Test the billing system in mock mode"""
    
    print("🧪 Testing Billing System in MOCK MODE")
    print("=" * 50)
    
    # Step 1: Register a test user
    print("\n1️⃣ Registering test user...")
    register_data = {
        "email": f"billing_test_{datetime.now().timestamp()}@test.com",
        "password": "TestPassword123!",
        "username": f"billing_test_{int(datetime.now().timestamp())}"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        print("✅ User registered successfully")
        user_data = response.json()
    else:
        print(f"❌ Registration failed: {response.text}")
        return
    
    # Step 2: Login
    print("\n2️⃣ Logging in...")
    login_data = {
        "username": register_data["email"],
        "password": register_data["password"]
    }
    
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    if response.status_code == 200:
        print("✅ Login successful")
        token_data = response.json()
        token = token_data["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Get initial billing info
    print("\n3️⃣ Getting initial billing info...")
    response = requests.get(f"{BASE_URL}/api/billing/info", headers=headers)
    if response.status_code == 200:
        billing_info = response.json()
        print(f"✅ Current tier: {billing_info['subscription']['tier']}")
        print(f"   API calls limit: {billing_info['limits']['api_calls']}")
        print(f"   Current usage: {billing_info['usage']['api_calls']}")
    else:
        print(f"❌ Failed to get billing info: {response.text}")
    
    # Step 4: Get pricing tiers
    print("\n4️⃣ Getting pricing tiers...")
    response = requests.get(f"{BASE_URL}/api/billing/pricing")
    if response.status_code == 200:
        pricing = response.json()
        print("✅ Available tiers:")
        for tier, config in pricing["tiers"].items():
            print(f"   - {tier}: ${config['price']}/month")
    else:
        print(f"❌ Failed to get pricing: {response.text}")
    
    # Step 5: Upgrade to Starter tier (mock)
    print("\n5️⃣ Upgrading to Starter tier (MOCK)...")
    upgrade_data = {"tier": "starter"}
    response = requests.post(
        f"{BASE_URL}/api/billing/subscription",
        json=upgrade_data,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upgrade successful!")
        print(f"   Subscription ID: {result['subscription_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Message: {result.get('message', 'Upgraded successfully')}")
    else:
        print(f"❌ Upgrade failed: {response.text}")
    
    # Step 6: Verify upgrade
    print("\n6️⃣ Verifying upgrade...")
    response = requests.get(f"{BASE_URL}/api/billing/info", headers=headers)
    if response.status_code == 200:
        billing_info = response.json()
        print(f"✅ New tier: {billing_info['subscription']['tier']}")
        print(f"   New API calls limit: {billing_info['limits']['api_calls']}")
    else:
        print(f"❌ Failed to verify: {response.text}")
    
    # Step 7: Track usage
    print("\n7️⃣ Tracking usage event...")
    usage_data = {
        "event_type": "api_call",
        "quantity": 5,
        "metadata": {"test": True}
    }
    response = requests.post(
        f"{BASE_URL}/api/billing/usage",
        json=usage_data,
        headers=headers
    )
    
    if response.status_code == 200:
        usage = response.json()
        print(f"✅ Usage tracked!")
        print(f"   Event ID: {usage['event_id']}")
        print(f"   Cost: ${usage['cost']}")
        print(f"   Total API calls this month: {usage['usage_this_month']['api_calls']}")
    else:
        print(f"❌ Failed to track usage: {response.text}")
    
    # Step 8: Test enterprise upgrade request
    print("\n8️⃣ Requesting enterprise upgrade...")
    response = requests.post(
        f"{BASE_URL}/api/billing/upgrade-to-enterprise",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Enterprise request submitted")
        print(f"   {result['message']}")
    else:
        print(f"❌ Failed to request enterprise: {response.text}")
    
    print("\n" + "=" * 50)
    print("✨ Billing system test completed!")
    print("\nNOTE: This test ran in MOCK MODE - no real charges occurred")
    print("To enable real Stripe integration, add your Stripe keys to .env")
    print("See STRIPE_SETUP.md for instructions")

if __name__ == "__main__":
    try:
        test_billing_system()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running:")
        print("   cd backend && python -m uvicorn src.main:app --reload")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")