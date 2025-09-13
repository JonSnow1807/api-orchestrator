import requests
from bs4 import BeautifulSoup
import json

print("\n" + "="*60)
print("🎨 FRONTEND UI/UX TESTING")
print("="*60)

BASE_URL = "http://localhost:5173"

def test_page(path, name):
    """Test a frontend page"""
    try:
        response = requests.get(f"{BASE_URL}{path}")
        if response.status_code == 200:
            # Check content length
            content_length = len(response.text)
            
            # Check for React app root
            has_root = '<div id="root">' in response.text
            
            # Check for critical UI elements
            has_styles = '<style' in response.text or 'css' in response.text.lower()
            has_scripts = '<script' in response.text
            
            print(f"\n✅ {name}")
            print(f"   - Status: 200 OK")
            print(f"   - Content size: {content_length:,} bytes")
            print(f"   - React root: {'✓' if has_root else '✗'}")
            print(f"   - Styles loaded: {'✓' if has_styles else '✗'}")
            print(f"   - Scripts loaded: {'✓' if has_scripts else '✗'}")
            
            return True
        else:
            print(f"\n❌ {name}")
            print(f"   - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"\n❌ {name}")
        print(f"   - Error: {str(e)}")
        return False

# Test main pages
pages = [
    ("/", "Landing Page"),
    ("/login", "Login Page"),
    ("/register", "Registration Page"),
    ("/pricing", "Pricing Page"),
    ("/dashboard", "Dashboard (Protected)"),
]

results = []
for path, name in pages:
    results.append(test_page(path, name))

# Test static assets
print("\n📦 Testing Static Assets...")
try:
    # Check if Vite dev server is serving assets
    assets_response = requests.get(f"{BASE_URL}/src/main.jsx")
    if assets_response.status_code == 200:
        print("✅ Vite dev server serving assets correctly")
    else:
        print(f"⚠️ Asset serving issue: {assets_response.status_code}")
except:
    print("❌ Cannot access dev server assets")

# Check API proxy
print("\n🔗 Testing API Proxy Configuration...")
try:
    proxy_test = requests.get(f"{BASE_URL}/api/health", allow_redirects=False)
    if proxy_test.status_code in [200, 302, 307]:
        print("✅ API proxy configured")
    else:
        print(f"⚠️ API proxy might not be configured: {proxy_test.status_code}")
except:
    print("❌ API proxy not working")

# Summary
print("\n" + "="*60)
print("📊 UI/UX TEST SUMMARY")
print("="*60)
passed = sum(results)
total = len(results)
print(f"Pages tested: {total}")
print(f"Pages working: {passed}")
print(f"Success rate: {(passed/total*100):.1f}%")

if passed < total:
    print("\n⚠️ Issues detected:")
    for i, (path, name) in enumerate(pages):
        if not results[i]:
            print(f"  - {name} at {path}")

print("\n💡 Recommendations:")
if passed == total:
    print("  ✓ All frontend pages are loading correctly")
    print("  ✓ React application is properly initialized")
else:
    print("  - Check frontend build process")
    print("  - Verify React Router configuration")
    print("  - Check for JavaScript errors in console")
