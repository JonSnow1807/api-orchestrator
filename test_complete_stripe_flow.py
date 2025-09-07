#!/usr/bin/env python3
"""
Complete Stripe Integration Test for StreamAPI
Tests the entire payment flow from checkout to subscription activation
"""

import requests
import json
import time
from datetime import datetime
import sys

# Production URL
BASE_URL = "https://streamapi.dev"

print("="*70)
print("🔍 COMPLETE STRIPE INTEGRATION TEST FOR STREAMAPI")
print("="*70)
print(f"Target: {BASE_URL}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Test checklist
tests = {
    "api_health": False,
    "stripe_config": False,
    "checkout_creation": False,
    "webhook_endpoint": False,
    "subscription_update": False,
    "billing_reflection": False
}

def test_api_health():
    """Test if API is responding"""
    print("\n1️⃣ Testing API Health...")
    print("-" * 50)
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data.get('status')}")
            tests["api_health"] = True
            return True
        else:
            print(f"❌ API not healthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API unreachable: {str(e)}")
        return False

def test_stripe_configuration():
    """Test if Stripe is properly configured"""
    print("\n2️⃣ Testing Stripe Configuration...")
    print("-" * 50)
    
    # Test pricing endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/billing/pricing")
        if response.status_code == 200:
            print("✅ Pricing endpoint accessible")
            data = response.json()
            
            # Check for price IDs
            has_prices = False
            if isinstance(data, dict) and 'tiers' in data:
                for tier_name, tier_info in data['tiers'].items():
                    if isinstance(tier_info, dict) and tier_info.get('stripe_price_id'):
                        print(f"✅ {tier_name}: Has price ID configured")
                        has_prices = True
            
            tests["stripe_config"] = has_prices
            return has_prices
        else:
            print(f"❌ Pricing endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking Stripe config: {str(e)}")
        return False

def test_checkout_session_creation(token):
    """Test creating a Stripe checkout session"""
    print("\n3️⃣ Testing Checkout Session Creation...")
    print("-" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/billing/subscription",
            json={"tier": "starter"},
            headers=headers
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('checkout_url'):
                print(f"✅ Checkout URL received")
                print(f"   URL: {data['checkout_url'][:60]}...")
                
                # Verify it's a real Stripe URL
                if 'checkout.stripe.com' in data['checkout_url']:
                    print("✅ Valid Stripe checkout URL")
                    tests["checkout_creation"] = True
                    return data
                else:
                    print("⚠️ URL doesn't appear to be Stripe checkout")
                    return None
            else:
                print(f"❌ No checkout URL in response")
                print(f"   Response: {data}")
                return None
        else:
            print(f"❌ Failed to create checkout: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Error creating checkout: {str(e)}")
        return None

def test_webhook_configuration():
    """Test if webhook endpoint is configured"""
    print("\n4️⃣ Testing Webhook Configuration...")
    print("-" * 50)
    
    # Send a test request to webhook endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/api/billing/webhook",
            json={"type": "test"},
            headers={"Stripe-Signature": "test_signature"}
        )
        
        # We expect 400 (bad signature) not 404
        if response.status_code in [400, 401]:
            print("✅ Webhook endpoint exists and validates signatures")
            tests["webhook_endpoint"] = True
            return True
        elif response.status_code == 404:
            print("❌ Webhook endpoint not found")
            return False
        else:
            print(f"⚠️ Unexpected webhook response: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing webhook: {str(e)}")
        return False

def test_user_subscription_status(token):
    """Check user's current subscription status"""
    print("\n5️⃣ Checking User Subscription Status...")
    print("-" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/billing/info",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Current Tier: {data.get('subscription_tier', 'free')}")
            print(f"   Status: {data.get('subscription_status', 'none')}")
            print(f"   Customer ID: {data.get('stripe_customer_id', 'Not set')}")
            
            if data.get('stripe_customer_id'):
                print("✅ Stripe customer created")
                tests["subscription_update"] = True
            
            # Check if subscription is active (after payment)
            if data.get('subscription_tier') != 'free':
                print(f"✅ Premium subscription active: {data.get('subscription_tier')}")
                tests["billing_reflection"] = True
            
            return data
        else:
            print(f"❌ Failed to get billing info: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting subscription status: {str(e)}")
        return None

def create_test_user():
    """Create a test user and login"""
    print("\n👤 Creating Test User...")
    print("-" * 50)
    
    import random
    import string
    
    username = f"stripetest_{''.join(random.choices(string.ascii_lowercase, k=6))}"
    email = f"{username}@test.com"
    password = "TestStripe123!"
    
    # Register
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "full_name": "Stripe Test User"
        }
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ User created: {username}")
        
        # Login
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": email,
                "password": password,
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token = response.json().get('access_token')
            print(f"✅ Logged in successfully")
            return token, email
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None, None
    else:
        print(f"❌ Registration failed: {response.status_code}")
        return None, None

def main():
    """Run complete test suite"""
    
    # 1. Test API health
    if not test_api_health():
        print("\n❌ API is not responding. Cannot continue tests.")
        return
    
    # 2. Test Stripe configuration
    test_stripe_configuration()
    
    # 3. Create test user
    token, email = create_test_user()
    if not token:
        print("\n❌ Failed to create test user. Cannot continue.")
        return
    
    # 4. Test checkout session creation
    checkout_data = test_checkout_session_creation(token)
    
    # 5. Test webhook configuration
    test_webhook_configuration()
    
    # 6. Check subscription status
    billing_info = test_user_subscription_status(token)
    
    # Print test summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    print("\n✅ PASSED TESTS:")
    for test_name, passed in tests.items():
        if passed:
            print(f"  ✅ {test_name.replace('_', ' ').title()}")
    
    print("\n❌ FAILED TESTS:")
    for test_name, passed in tests.items():
        if not passed:
            print(f"  ❌ {test_name.replace('_', ' ').title()}")
    
    passed_count = sum(1 for p in tests.values() if p)
    total_count = len(tests)
    
    print("\n" + "-"*70)
    print(f"Score: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.0f}%)")
    
    # Provide instructions for manual testing
    print("\n" + "="*70)
    print("📝 MANUAL TESTING INSTRUCTIONS")
    print("="*70)
    
    if checkout_data and checkout_data.get('checkout_url'):
        print("\n1. Open this URL in your browser:")
        print(f"   {checkout_data['checkout_url']}")
        print("\n2. Use test card details:")
        print("   Card: 4242 4242 4242 4242")
        print("   Expiry: 12/34")
        print("   CVC: 123")
        print("   ZIP: 12345")
        print("\n3. Complete the payment")
        print("\n4. Check Railway logs for webhook processing:")
        print("   - Look for 'checkout.session.completed'")
        print("   - Look for 'Updated user X subscription to starter tier'")
        print("\n5. Return to https://streamapi.dev/billing")
        print("   - Should show 'Starter' as current plan")
        print("   - Should show increased API limits")
        
        if email:
            print(f"\n📧 Test account: {email}")
            print("   Password: TestStripe123!")
    else:
        print("\n⚠️ Could not create checkout session for manual testing")
        print("Please check the errors above and fix them first.")
    
    print("\n" + "="*70)
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED! Stripe integration is working perfectly!")
    elif passed_count >= total_count - 1:
        print("✅ Stripe integration is mostly working. Check failed tests above.")
    else:
        print("⚠️ Several issues detected. Please review the failed tests.")
    
    print("="*70)

if __name__ == "__main__":
    main()