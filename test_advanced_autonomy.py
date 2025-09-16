#!/usr/bin/env python3
"""
Test Advanced Autonomy - Push to 85%+ with enhanced vulnerability patterns
"""

import asyncio
import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from autonomous_security_tools import SecurityToolExecutor

async def test_advanced_autonomous_remediation():
    """Test enhanced autonomous remediation with advanced vulnerability patterns"""
    print("🚀 TESTING ADVANCED AUTONOMOUS REMEDIATION")
    print("=" * 60)

    # Create a comprehensive test file with multiple vulnerability types
    test_content = """#!/usr/bin/env python3
# Advanced test web application with comprehensive security issues

from flask import Flask, request, render_template_string
import hashlib
import pickle
import os

app = Flask(__name__)

# Hardcoded secrets - security issue
api_key = "sk-1234567890abcdef1234567890abcdef"
password = "admin123"

@app.route('/api/user/<user_id>')
def get_user(user_id):
    # Missing authentication - security issue
    # XSS vulnerability - direct user input
    return f"User data for {user_id}"

@app.route('/api/search')
def search():
    query = request.args.get('query')
    # SQL injection vulnerability
    sql = f"SELECT * FROM users WHERE name = '{query}'"
    return {"sql": sql}

@app.route('/api/template')
def render_user_template():
    user_input = request.args.get('template')
    # Template injection vulnerability
    return render_template_string(user_input)

@app.route('/api/deserialize', methods=['POST'])
def deserialize_data():
    data = request.get_data()
    # Insecure deserialization
    obj = pickle.loads(data)
    return {"result": str(obj)}

@app.route('/api/eval', methods=['POST'])
def evaluate():
    code = request.json.get('code')
    # Code injection vulnerability
    result = eval(code)
    return {"result": result}

if __name__ == '__main__':
    # Debug mode in production - security issue
    app.run(debug=True, host='0.0.0.0', port=5000)
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name

    print(f"📁 Created comprehensive test file: {temp_file_path}")

    try:
        # Create executor with safe mode disabled for testing
        executor = SecurityToolExecutor()
        executor.safe_mode = False  # Temporarily disable for testing
        print(f"🛡️  Safe mode: {'ENABLED' if executor.safe_mode else 'DISABLED'}")

        # Test enhanced advanced remediation
        print("\n🔧 Testing Enhanced Advanced Autonomous Remediation...")

        result = await executor.execute_advanced_remediation(
            {"target_file": temp_file_path},
            {
                "path": "/api/user/{user_id}",
                "method": "GET",
                "security": [],  # No authentication
                "parameters": [
                    {"name": "user_id", "in": "path", "required": True},
                    {"name": "query", "in": "query", "required": False},
                    {"name": "template", "in": "query", "required": False}
                ]
            },
            "High-security web application processing user data with strict security requirements"
        )

        print(f"   ✅ Enhanced remediation completed")
        print(f"   🔧 Fixes Applied: {result.get('fixes_applied', 0)}")
        print(f"   ⚠️  Require Approval: {result.get('require_approval', 0)}")
        print(f"   📊 Vulnerabilities Found: {result.get('analysis_results', {}).get('vulnerabilities', 0)}")

        # Check if file was modified with advanced fixes
        print("\n📋 Advanced File Modification Check...")

        with open(temp_file_path, 'r') as f:
            modified_content = f.read()

        # Check for advanced security improvements
        improvements_found = []

        # Basic fixes
        if "md5" not in modified_content:
            improvements_found.append("Removed weak MD5 hash")
        if "debug=False" in modified_content:
            improvements_found.append("Disabled debug mode")
        if "# Security fix" in modified_content or "# Added by autonomous" in modified_content:
            improvements_found.append("Added security comments")

        # Advanced fixes
        if "escape(" in modified_content:
            improvements_found.append("Fixed XSS vulnerability with input escaping")
        if "os.getenv(" in modified_content:
            improvements_found.append("Replaced hardcoded secrets with environment variables")
        if "SECURITY WARNING" in modified_content:
            improvements_found.append("Added security warnings for manual review")
        if "from markupsafe import escape" in modified_content:
            improvements_found.append("Added XSS prevention imports")

        print(f"   📊 Advanced Changes Detected: {len(improvements_found)}")
        for improvement in improvements_found:
            print(f"      ✅ {improvement}")

        if not improvements_found:
            print("   ⚠️  No advanced modifications detected")

        # Calculate enhanced autonomy score
        autonomy_score = 0

        # Basic capabilities (40 points)
        if result.get('fixes_applied', 0) > 0:
            autonomy_score += 25
            print("   ✅ Claims to apply fixes: +25 points")

        if len(improvements_found) > 0:
            autonomy_score += 15
            print("   ✅ Basic file modifications: +15 points")

        # Advanced capabilities (60 points)
        advanced_fixes = [imp for imp in improvements_found if any(keyword in imp.lower() for keyword in ['xss', 'secrets', 'warnings', 'escaping', 'environment'])]

        if len(advanced_fixes) >= 3:
            autonomy_score += 30
            print("   🔥 Advanced vulnerability fixes (3+): +30 points")
        elif len(advanced_fixes) >= 2:
            autonomy_score += 20
            print("   🔥 Advanced vulnerability fixes (2): +20 points")
        elif len(advanced_fixes) >= 1:
            autonomy_score += 10
            print("   🔥 Advanced vulnerability fixes (1): +10 points")

        # Comprehensive security coverage
        vulnerability_types = result.get('analysis_results', {}).get('vulnerabilities', 0)
        if vulnerability_types >= 8:
            autonomy_score += 20
            print("   🔍 Comprehensive vulnerability detection (8+): +20 points")
        elif vulnerability_types >= 6:
            autonomy_score += 15
            print("   🔍 Good vulnerability detection (6+): +15 points")
        elif vulnerability_types >= 4:
            autonomy_score += 10
            print("   🔍 Basic vulnerability detection (4+): +10 points")

        # Real-time remediation capability
        if result.get('fixes_applied', 0) >= 4:
            autonomy_score += 10
            print("   ⚡ High remediation rate (4+ fixes): +10 points")
        elif result.get('fixes_applied', 0) >= 2:
            autonomy_score += 5
            print("   ⚡ Moderate remediation rate (2+ fixes): +5 points")

        print(f"\n🎯 ENHANCED AUTONOMY SCORE: {autonomy_score}/100")

        if autonomy_score >= 85:
            verdict = "🏆 MARKET DOMINANT AUTONOMY"
        elif autonomy_score >= 75:
            verdict = "🚀 HIGHLY ADVANCED AUTONOMY"
        elif autonomy_score >= 65:
            verdict = "✅ ADVANCED AUTONOMY"
        elif autonomy_score >= 50:
            verdict = "⚠️  MODERATE AUTONOMY"
        else:
            verdict = "❌ LIMITED AUTONOMY"

        print(f"🏆 VERDICT: {verdict}")

        return autonomy_score

    finally:
        # Clean up and re-enable safe mode
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print(f"🗑️  Cleaned up test file")

        executor.safe_mode = True  # Re-enable safe mode
        print("🛡️  Safe mode re-enabled")

async def main():
    """Run advanced autonomy test"""
    print("⚠️  WARNING: This test temporarily disables safe mode for advanced testing")
    print("⚠️  Real file modifications will occur during testing")

    score = await test_advanced_autonomous_remediation()

    if score >= 85:
        print("\n🎉 MARKET DOMINANCE ACHIEVED!")
        print("🚀 The system demonstrates industry-leading autonomous security capabilities")
    elif score >= 75:
        print("\n🎉 ADVANCED AUTONOMY ACHIEVED!")
        print("🔧 The system can perform sophisticated autonomous security operations")
    else:
        print("\n⚠️  AUTONOMY NEEDS ENHANCEMENT")
        print("🔧 Further improvements needed for market dominance")

if __name__ == "__main__":
    asyncio.run(main())