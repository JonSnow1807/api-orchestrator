#!/usr/bin/env python3
"""
CodeRabbit API integration script.

Usage:
    export CODERABBIT_API_KEY="cr-your-api-key-here"
    python coderabbit_review.py
"""
import requests
import json
import os

# CodeRabbit API configuration
API_KEY = os.getenv("CODERABBIT_API_KEY")
if not API_KEY:
    raise ValueError("CODERABBIT_API_KEY environment variable is required")

BASE_URL = "https://api.coderabbit.ai/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "x-coderabbitai-api-key": API_KEY
}

def check_api_status():
    """Check API connection and rate limits using documented endpoints"""
    endpoints_to_try = ["/health", "/status", "/"]

    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"Testing {endpoint} - Status Code: {response.status_code}")

            if response.status_code == 200:
                print(f"✅ API connection successful via {endpoint}")

                # Check rate limit headers
                if 'X-RateLimit-Remaining' in response.headers:
                    remaining = response.headers.get('X-RateLimit-Remaining')
                    limit = response.headers.get('X-RateLimit-Limit', 'unknown')
                    print(f"📊 Rate Limit: {remaining}/{limit} remaining")

                return True
            elif response.status_code == 429:
                print("⚠️ Rate limit exceeded")
                retry_after = response.headers.get('Retry-After', 'unknown')
                print(f"Retry after: {retry_after} seconds")
                return False
        except Exception as e:
            print(f"❌ Connection error for {endpoint}: {e}")
            continue

    print("❌ All endpoints failed")
    return False

def get_rate_limit_info():
    """Get rate limit information"""
    try:
        response = requests.get(f"{BASE_URL}/rate-limit", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Rate Limit Information:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Could not get rate limit info: {response.status_code}")
    except Exception as e:
        print(f"Error getting rate limit: {e}")

if __name__ == "__main__":
    print("🔍 CodeRabbit API Check\n")
    print(f"Using API Key: {API_KEY[:20]}...")
    
    if check_api_status():
        get_rate_limit_info()
    else:
        print("\n⏰ Please wait for rate limit to reset or check API key")
