#!/usr/bin/env python3
"""Debug test to see what the API is actually returning"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

SIMPLE_CODE = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello"}
'''

# Authenticate
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "demo@streamapi.dev",
        "password": "Demo123!",
        "grant_type": "password"
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code != 200:
    print(f"❌ Authentication failed")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ Authenticated")

# Start orchestration
response = requests.post(
    f"{BASE_URL}/api/orchestrate",
    json={
        "source_type": "code",
        "source_path": "test.py",
        "code_content": SIMPLE_CODE
    },
    headers=headers
)

if response.status_code != 200:
    print(f"❌ Orchestration failed: {response.status_code}")
    print(response.text)
    exit(1)

task_id = response.json().get("task_id")
print(f"✅ Orchestration started: {task_id}")

# Wait and check
time.sleep(2)

response = requests.get(f"{BASE_URL}/api/tasks/{task_id}", headers=headers)
print(f"\n📋 Task status response (status={response.status_code}):")
data = response.json()
print(json.dumps(data, indent=2))

# Check what's in the response
print(f"\n🔍 Keys in response: {list(data.keys())}")
print(f"Status: {data.get('status')}")
print(f"Task ID: {data.get('task_id')}")

# Check for results
if 'results' in data:
    print(f"\n📊 Results found:")
    results = data['results']
    if results:
        print(f"  Type of results: {type(results)}")
        print(f"  Results content: {results}")
    else:
        print(f"  Results is None or empty")
elif 'apis' in data:
    print(f"\n📊 Results at top level:")
    print(f"  APIs: {data.get('apis')}")
    print(f"  Specs: {data.get('specs')}")
    print(f"  Tests: {data.get('tests')}")
else:
    print(f"\n⚠️ No results found in response")