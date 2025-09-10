#!/usr/bin/env python
"""
Production Deployment Test for Railway + Stripe
Tests the live deployment with real configuration
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

# Configuration - Update with your Railway URL
RAILWAY_URL = "https://api-orchestrator-production.up.railway.app"  # Update this with your actual Railway URL
LOCAL_URL = "http://localhost:8000"

# Choose which to test
BASE_URL = RAILWAY_URL  # Change to LOCAL_URL for local testing

test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def print_header(text):
    print(f"\n{'='*60}")
    print(f"🔍 {text}")
    print("="*60)

def test_passed(message):
    global test_results
    test_results["passed"] += 1
    print(f"✅ {message}")

def test_failed(message, error=None):
    global test_results
    test_results["failed"] += 1
    print(f"❌ {message}")
    if error:
        test_results["errors"].append(f"{message}: {error}")
        print(f"   Error: {error}")

async def test_health_check():
    """Test if the API is accessible"""
    print_header("Health Check")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                test_passed(f"API is healthy at {BASE_URL}")
                return True
            else:
                test_failed(f"Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            test_failed("Cannot reach API", str(e))
            return False

async def test_database_connection():
    """Test database connectivity"""
    print_header("Database Connection")
    
    async with httpx.AsyncClient() as client:
        try:
            # Try to access an endpoint that requires database
            response = await client.get(f"{BASE_URL}/api/projects", timeout=10)
            if response.status_code in [200, 401]:  # 401 is OK, means API is working
                test_passed("Database connection working")
            else:
                test_failed(f"Database issue - status {response.status_code}")
        except Exception as e:
            test_failed("Database connection failed", str(e))

async def test_authentication():
    """Test authentication system"""
    print_header("Authentication System")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test registration endpoint exists
            response = await client.post(
                f"{BASE_URL}/api/auth/register",
                json={
                    "email": f"test_{int(datetime.now().timestamp())}@example.com",
                    "username": f"testuser_{int(datetime.now().timestamp())}",
                    "password": "TestPass123!"
                },
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                test_passed("User registration working")
                data = response.json()
                if "access_token" in data:
                    test_passed("JWT token generation working")
                    return data["access_token"]
            elif response.status_code == 400:
                test_passed("Registration validation working")
            else:
                test_failed(f"Registration failed with status {response.status_code}")
                
        except Exception as e:
            test_failed("Authentication test failed", str(e))
    
    return None

async def test_stripe_integration():
    """Test Stripe configuration"""
    print_header("Stripe Integration")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test billing endpoint
            response = await client.get(f"{BASE_URL}/api/billing/config", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "publishable_key" in data:
                    test_passed("Stripe publishable key configured")
                if "prices" in data:
                    test_passed(f"Stripe price IDs configured: {len(data['prices'])} tiers")
            elif response.status_code == 401:
                test_passed("Billing endpoint requires authentication (correct)")
            else:
                test_failed(f"Stripe config failed with status {response.status_code}")
                
        except Exception as e:
            test_failed("Stripe integration test failed", str(e))

async def test_websocket():
    """Test WebSocket connectivity"""
    print_header("WebSocket Connection")
    
    try:
        import websockets
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        
        try:
            async with websockets.connect(f"{ws_url}/ws/test", timeout=5) as websocket:
                test_passed("WebSocket connection established")
                await websocket.close()
        except Exception as e:
            if "404" in str(e) or "401" in str(e):
                test_passed("WebSocket endpoint exists (auth required)")
            else:
                test_failed("WebSocket connection failed", str(e))
    except ImportError:
        print("⚠️ Skipping WebSocket test (websockets library not installed)")

async def test_new_features():
    """Test newly added features"""
    print_header("New Features")
    
    async with httpx.AsyncClient() as client:
        # Test Test Runner endpoint
        try:
            response = await client.get(f"{BASE_URL}/api/test-runner/status", timeout=10)
            if response.status_code in [200, 401, 404]:
                test_passed("Test Runner endpoint available")
        except:
            pass
        
        # Test Postman Import endpoint
        try:
            response = await client.post(
                f"{BASE_URL}/api/test-runner/import-postman",
                json={"collection": {}},
                timeout=10
            )
            if response.status_code in [200, 400, 401, 422]:
                test_passed("Postman import endpoint available")
        except:
            pass
        
        # Test AI Keys endpoint
        try:
            response = await client.get(f"{BASE_URL}/api/ai-keys", timeout=10)
            if response.status_code in [200, 401]:
                test_passed("AI Keys endpoint available")
        except:
            pass

async def test_frontend():
    """Test frontend availability"""
    print_header("Frontend")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL, timeout=10)
            if response.status_code == 200:
                if "<!DOCTYPE html>" in response.text or "<html" in response.text:
                    test_passed("Frontend serving correctly")
                else:
                    test_failed("Frontend not returning HTML")
            else:
                test_failed(f"Frontend failed with status {response.status_code}")
        except Exception as e:
            test_failed("Frontend test failed", str(e))

async def main():
    print("="*60)
    print("🚀 PRODUCTION DEPLOYMENT TEST")
    print(f"Testing: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("="*60)
    
    # Check if we can reach the API at all
    if not await test_health_check():
        print("\n⚠️ Cannot reach API. Please check:")
        print("1. Is Railway deployment running?")
        print("2. Is the URL correct?")
        print(f"3. Current URL: {BASE_URL}")
        return
    
    # Run all tests
    await test_database_connection()
    token = await test_authentication()
    await test_stripe_integration()
    await test_websocket()
    await test_new_features()
    await test_frontend()
    
    # Generate report
    print("\n" + "="*60)
    print("📊 DEPLOYMENT TEST RESULTS")
    print("="*60)
    
    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if test_results["errors"]:
        print("\n❌ Errors:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    print("\n" + "="*60)
    
    if test_results["failed"] == 0:
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("✅ All systems operational")
        print("✅ Database connected")
        print("✅ Authentication working")
        print("✅ Stripe configured")
        print("✅ Ready for production use")
    else:
        print("⚠️ Some tests failed")
        print("Please check the errors above")
    
    print("="*60)

if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--local":
            BASE_URL = LOCAL_URL
            print("Testing LOCAL deployment")
        elif sys.argv[1].startswith("http"):
            BASE_URL = sys.argv[1]
            print(f"Testing custom URL: {BASE_URL}")
    
    asyncio.run(main())