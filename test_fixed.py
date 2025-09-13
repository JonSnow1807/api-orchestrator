import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Test authentication
print("\n🔐 Testing Authentication...")
# Register
reg_response = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "test@example.com",
    "password": "Test123!",
    "name": "Test User"
})
print(f"Register: {reg_response.status_code} - {'✅' if reg_response.status_code in [200, 400] else '❌'}")

# Login
login_response = requests.post(f"{BASE_URL}/auth/login", data={
    "username": "demo@example.com",  # Use demo account
    "password": "Demo123!"
})
if login_response.status_code == 200:
    token = login_response.json().get("access_token")
    print(f"Login: ✅ Token received")
    headers = {"Authorization": f"Bearer {token}"}
else:
    print(f"Login: ❌ Status {login_response.status_code}")
    headers = {}

# Test core APIs
print("\n📦 Testing Core APIs...")
if headers:
    # Projects
    proj_response = requests.get(f"{BASE_URL}/api/projects", headers=headers)
    print(f"Projects List: {proj_response.status_code} - {'✅' if proj_response.status_code == 200 else '❌'}")
    
    # Create project
    create_response = requests.post(f"{BASE_URL}/api/projects", headers=headers, json={
        "name": "Test Project",
        "description": "Integration test"
    })
    print(f"Create Project: {create_response.status_code} - {'✅' if create_response.status_code == 200 else '❌'}")

# Test v5.0 features
print("\n🚀 Testing V5.0 Features...")
# Check if routes exist
routes_to_test = [
    ("GET", "/api/v5/natural-language/suggestions"),
    ("POST", "/api/v5/natural-language/generate-test"),
    ("POST", "/api/v5/visualization/analyze"),
    ("GET", "/api/v5/variables/list"),
    ("GET", "/api/v5/virtualization/services"),
]

for method, route in routes_to_test:
    if method == "GET":
        response = requests.get(f"{BASE_URL}{route}", headers=headers)
    else:
        response = requests.post(f"{BASE_URL}{route}", headers=headers, json={})
    
    status = "✅" if response.status_code != 404 else "❌"
    print(f"{route}: {response.status_code} - {status}")

# Test frontend
print("\n🎨 Testing Frontend...")
frontend_response = requests.get("http://localhost:5173")
print(f"Frontend Homepage: {frontend_response.status_code} - {'✅' if frontend_response.status_code == 200 else '❌'}")

# Test WebSocket
print("\n🔌 Testing WebSocket...")
if headers and 'Authorization' in headers:
    import websocket
    try:
        ws_token = token if 'token' in locals() else ""
        ws = websocket.create_connection(f"ws://localhost:8000/ws?token={ws_token}", timeout=2)
        ws.send(json.dumps({"type": "ping"}))
        ws.close()
        print(f"WebSocket: ✅ Connected")
    except Exception as e:
        print(f"WebSocket: ❌ {str(e)[:50]}")
else:
    print("WebSocket: ⚠️ No token available")

print("\n" + "="*50)
print("📊 Integration Test Complete")
print("="*50)
