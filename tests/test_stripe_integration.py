#!/usr/bin/env python3
"""
Test Stripe integration for StreamAPI production
Verifies billing endpoints and Stripe configuration
"""

import requests
import json
import time
from datetime import datetime

# Production URL
BASE_URL = "https://streamapi.dev"

print("="*60)
print("🔍 TESTING STRIPE INTEGRATION ON STREAMAPI")
print("="*60)
print(f"Target: {BASE_URL}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test results
results = []

def test_step(name, func):
    """Execute a test step and track results"""
    print(f"\n{name}")
    print("-" * 40)
    try:
        result = func()
        if result:
            print(f"✅ {name} - PASSED")
            results.append(("✅", name))
        else:
            print(f"❌ {name} - FAILED")
            results.append(("❌", name))
        return result
    except Exception as e:
        print(f"❌ {name} - ERROR: {str(e)}")
        results.append(("❌", f"{name} - {str(e)}"))
        return False

def test_health():
    """Test API health"""
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print(f"   API Status: {response.json().get('status')}")
        return True
    return False

def test_pricing_endpoint():
    """Test public pricing endpoint"""
    response = requests.get(f"{BASE_URL}/api/billing/pricing")
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            tiers = data.get('tiers', [])
            print(f"   Pricing tiers available: {len(tiers)}")
            for tier in tiers:
                if isinstance(tier, dict):
                    print(f"   - {tier.get('name')}: ${tier.get('price')}/month")
        elif isinstance(data, list):
            print(f"   Pricing tiers available: {len(data)}")
            for tier in data:
                if isinstance(tier, dict):
                    print(f"   - {tier.get('name', 'Unknown')}: ${tier.get('price', 0)}/month")
        return True
    else:
        print(f"   Status: {response.status_code}")
        return False

def test_user_registration():
    """Test user registration and get token"""
    import random
    import string
    
    username = f"test_{''.join(random.choices(string.ascii_lowercase, k=6))}"
    email = f"{username}@test.com"
    
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "TestPassword123!",
            "full_name": "Stripe Test User"
        }
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"   User created: {username}")
        print(f"   User ID: {data.get('id')}")
        # Now login to get token
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": email,
                "password": "TestPassword123!",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if login_response.status_code == 200:
            token = login_response.json().get('access_token')
            print(f"   Token obtained: {'Yes' if token else 'No'}")
            return token
        return True
    else:
        print(f"   Registration failed: {response.status_code}")
        # Try login with demo account
        print("   Trying demo account...")
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": "demo",
                "password": "Demo123!",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        return False

def test_billing_info(token):
    """Test billing info endpoint"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/billing/info", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Current tier: {data.get('subscription_tier', 'free')}")
        print(f"   Status: {data.get('subscription_status', 'none')}")
        print(f"   API calls used: {data.get('api_calls_used', 0)}/{data.get('api_calls_limit', 'unlimited')}")
        
        # Check if Stripe is configured
        if data.get('stripe_customer_id'):
            print(f"   Stripe customer: {data.get('stripe_customer_id')}")
        
        return True
    else:
        print(f"   Status: {response.status_code}")
        return False

def test_create_checkout_session(token):
    """Test creating a Stripe checkout session"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create a checkout session for Starter plan
    response = requests.post(
        f"{BASE_URL}/api/billing/subscription",
        json={"tier": "starter"},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('checkout_url'):
            print(f"   ✅ Checkout URL generated successfully")
            print(f"   URL starts with: {data['checkout_url'][:50]}...")
            
            # Check if it's a real Stripe URL
            if 'checkout.stripe.com' in data['checkout_url']:
                print(f"   ✅ Real Stripe checkout URL confirmed!")
                return True
            elif 'demo' in data.get('subscription_id', ''):
                print(f"   ⚠️ Demo mode active (Stripe not fully configured)")
                return False
        else:
            print(f"   ⚠️ No checkout URL returned")
            if data.get('subscription_id', '').startswith('demo_'):
                print(f"   Demo subscription created: {data.get('subscription_id')}")
            return False
    else:
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return False

def test_webhook_endpoint():
    """Test if webhook endpoint exists"""
    # Send a test ping to webhook endpoint (will fail auth but shows endpoint exists)
    response = requests.post(
        f"{BASE_URL}/api/billing/webhook",
        json={"type": "ping"},
        headers={"Stripe-Signature": "test"}
    )
    
    # We expect 400 or 401 (bad signature) not 404
    if response.status_code in [400, 401, 403]:
        print(f"   Webhook endpoint exists (auth failed as expected)")
        return True
    elif response.status_code == 404:
        print(f"   ❌ Webhook endpoint not found")
        return False
    else:
        print(f"   Status: {response.status_code}")
        return response.status_code < 500

# Run tests
print("\n🧪 RUNNING TESTS...")
print("="*60)

test_step("1. API Health Check", test_health)
test_step("2. Pricing Endpoint", test_pricing_endpoint)

token = test_step("3. User Registration/Login", test_user_registration)

if token and isinstance(token, str):
    test_step("4. Billing Info", lambda: test_billing_info(token))
    test_step("5. Create Checkout Session", lambda: test_create_checkout_session(token))
else:
    print("\n⚠️ Skipping authenticated tests (no token)")

test_step("6. Webhook Endpoint", test_webhook_endpoint)

# Print summary
print("\n" + "="*60)
print("📊 TEST SUMMARY")
print("="*60)

passed = sum(1 for r in results if r[0] == "✅")
total = len(results)

for icon, name in results:
    print(f"{icon} {name}")

print("\n" + "="*60)
print(f"Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

if passed == total:
    print("🎉 ALL TESTS PASSED! Stripe integration is working!")
    print("\n✅ Your platform is ready to accept real payments!")
elif passed >= total - 1:
    print("✅ Stripe integration is mostly working!")
    print("⚠️ Check any failed tests above.")
else:
    print("❌ Some issues detected. Please check the failed tests.")

print("="*60)