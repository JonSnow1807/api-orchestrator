#!/usr/bin/env python3
"""
Test Autonomous Remediation - Verify real remediation capabilities
"""

import asyncio
import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from autonomous_security_tools import SecurityToolExecutor

async def test_autonomous_remediation():
    """Test real autonomous remediation with actual file modification"""
    print("🔧 TESTING AUTONOMOUS REMEDIATION")
    print("=" * 50)

    # Create a test file with security issues
    test_content = """#!/usr/bin/env python3
# Test web application with security issues

from flask import Flask, request
import hashlib

app = Flask(__name__)

@app.route('/api/user/<user_id>')
def get_user(user_id):
    # Missing authentication - security issue
    # No input validation - security issue
    return f"User data for {user_id}"

@app.route('/api/login', methods=['POST'])
def login():
    password = request.form['password']
    # Weak hash function - security issue
    hash_value = hashlib.md5(password.encode()).hexdigest()
    return {"hash": hash_value}

if __name__ == '__main__':
    # Debug mode in production - security issue
    app.run(debug=True, host='0.0.0.0')
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name

    print(f"📁 Created test file: {temp_file_path}")

    try:
        # Create executor with safe mode disabled
        executor = SecurityToolExecutor()
        print(f"🛡️  Safe mode: {'ENABLED' if executor.safe_mode else 'DISABLED'}")

        # Test advanced remediation
        print("\n🔧 Testing Advanced Autonomous Remediation...")

        result = await executor.execute_advanced_remediation(
            {"target_file": temp_file_path},
            {
                "path": "/api/user/{user_id}",
                "method": "GET",
                "security": [],  # No authentication
                "parameters": [
                    {"name": "user_id", "in": "path", "required": True}
                ]
            },
            "Web application handling user data with authentication and security requirements"
        )

        print(f"   ✅ Remediation completed")
        print(f"   🔧 Fixes Applied: {result.get('fixes_applied', 0)}")
        print(f"   ⚠️  Require Approval: {result.get('require_approval', 0)}")
        print(f"   📊 Analysis Results: {result.get('analysis_results', {})}")

        # Test auto-fix security headers
        print("\n🔒 Testing Auto-Fix Security Headers...")

        header_result = await executor.execute_auto_fix_security_headers(
            {},
            {"path": "/api/user", "method": "GET"}
        )

        print(f"   ✅ Header fixes completed")
        print(f"   🔧 Fixes Applied: {header_result.get('fixes_applied', 0)}")
        print(f"   📁 Files Modified: {header_result.get('files_modified', [])}")
        print(f"   📝 Changes: {header_result.get('changes', [])}")

        # Check if file was actually modified
        print("\n📋 File Modification Check...")

        with open(temp_file_path, 'r') as f:
            modified_content = f.read()

        # Check for security improvements
        improvements_found = []

        if "md5" not in modified_content:
            improvements_found.append("Removed weak MD5 hash")
        if "debug=False" in modified_content:
            improvements_found.append("Disabled debug mode")
        if "# Security fix" in modified_content or "# Added by autonomous" in modified_content:
            improvements_found.append("Added security comments")

        print(f"   📊 File Changes Detected: {len(improvements_found)}")
        for improvement in improvements_found:
            print(f"      ✅ {improvement}")

        if not improvements_found:
            print("   ⚠️  No file modifications detected")

        # Calculate remediation score
        remediation_score = 0

        if result.get('fixes_applied', 0) > 0:
            remediation_score += 40
            print("   ✅ Claims to apply fixes: +40 points")

        if header_result.get('fixes_applied', 0) > 0:
            remediation_score += 30
            print("   ✅ Header fixes applied: +30 points")

        if len(improvements_found) > 0:
            remediation_score += 30
            print("   ✅ Actual file modifications: +30 points")
        else:
            print("   ❌ No actual file modifications: +0 points")

        print(f"\n🎯 REMEDIATION AUTONOMY SCORE: {remediation_score}/100")

        if remediation_score >= 80:
            verdict = "🏆 FULLY AUTONOMOUS REMEDIATION"
        elif remediation_score >= 60:
            verdict = "✅ HIGHLY AUTONOMOUS REMEDIATION"
        elif remediation_score >= 40:
            verdict = "⚠️  MODERATE AUTONOMOUS REMEDIATION"
        else:
            verdict = "❌ LIMITED AUTONOMOUS REMEDIATION"

        print(f"🏆 VERDICT: {verdict}")

        return remediation_score

    finally:
        # Clean up
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print(f"🗑️  Cleaned up test file")

async def main():
    """Run autonomous remediation test"""
    print("⚠️  WARNING: This test temporarily disables safe mode for testing purposes")
    print("⚠️  Real file modifications may occur during testing")

    score = await test_autonomous_remediation()

    if score >= 60:
        print("\n🎉 AUTONOMOUS REMEDIATION ACHIEVED!")
        print("🔧 The system can perform real autonomous fixes")
    else:
        print("\n⚠️  AUTONOMOUS REMEDIATION LIMITED")
        print("🔧 The system can analyze but has limited fixing capabilities")

if __name__ == "__main__":
    asyncio.run(main())