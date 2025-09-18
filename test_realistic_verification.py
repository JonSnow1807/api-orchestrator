#!/usr/bin/env python3
"""
Realistic Verification Test - No inflated claims, actual measurements
"""

import asyncio
import sys
import os
import tempfile

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from autonomous_security_tools import SecurityToolExecutor

async def test_actual_capabilities():
    """Test actual capabilities with precise measurements"""
    print("🔍 REALISTIC VERIFICATION TEST")
    print("=" * 50)
    print("Testing actual capabilities without inflated claims...")

    # Create a realistic test file with known vulnerabilities
    test_content = """from flask import Flask, request
import hashlib

app = Flask(__name__)

@app.route('/user/<user_id>')
def get_user(user_id):
    return f"User: {user_id}"

@app.route('/login', methods=['POST'])
def login():
    password = request.form['password']
    return hashlib.md5(password.encode()).hexdigest()

if __name__ == '__main__':
    app.run(debug=True)
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(test_content)
        temp_file_path = temp_file.name

    print(f"📁 Test file: {temp_file_path}")

    try:
        executor = SecurityToolExecutor()
        executor.safe_mode = False  # For testing

        # Test 1: Basic vulnerability scan
        print("\n1. Testing vulnerability scan...")
        vuln_result = await executor.execute_security_vulnerability_scan(
            {"target_file": temp_file_path},
            {"path": "/user/{user_id}", "method": "GET", "security": []}
        )

        actual_vulns = len(vuln_result.get('vulnerabilities', []))
        print(f"   Result: Found {actual_vulns} vulnerabilities")

        # Test 2: Advanced remediation
        print("\n2. Testing advanced remediation...")
        remediation_result = await executor.execute_advanced_remediation(
            {"target_file": temp_file_path},
            {"path": "/user/{user_id}", "method": "GET", "security": []},
            "Test application"
        )

        actual_fixes = remediation_result.get('fixes_applied', 0)
        print(f"   Result: Applied {actual_fixes} fixes")

        # Test 3: Check actual file changes
        print("\n3. Checking actual file changes...")
        with open(temp_file_path, 'r') as f:
            modified_content = f.read()

        actual_changes = []
        if "sha256" in modified_content:
            actual_changes.append("MD5 → SHA256 upgrade")
        if "debug=False" in modified_content:
            actual_changes.append("Debug mode disabled")
        if "os.getenv" in modified_content:
            actual_changes.append("Environment variables")

        print(f"   Result: {len(actual_changes)} actual file modifications:")
        for change in actual_changes:
            print(f"      - {change}")

        # Test 4: Specialized agents (if available)
        specialized_working = 0
        print("\n4. Testing specialized agents...")

        try:
            devops_result = await executor.execute_devops_security_scan({}, {}, "")
            if devops_result.get('status') != 'unavailable':
                specialized_working += 1
                print(f"   DevOps agent: Working ({devops_result.get('total_findings', 0)} findings)")
        except:
            print("   DevOps agent: Not working")

        try:
            db_result = await executor.execute_database_security_audit({}, {}, "")
            if db_result.get('status') != 'unavailable':
                specialized_working += 1
                print(f"   Database agent: Working ({db_result.get('total_findings', 0)} findings)")
        except:
            print("   Database agent: Not working")

        try:
            refactor_result = await executor.execute_smart_code_refactoring(
                {"target_file": temp_file_path}, {}, ""
            )
            if refactor_result.get('status') != 'unavailable':
                specialized_working += 1
                print(f"   Refactoring agent: Working ({refactor_result.get('refactors_applied', 0)} refactors)")
        except:
            print("   Refactoring agent: Not working")

        # Calculate realistic score
        print("\n📊 REALISTIC ASSESSMENT:")
        print("=" * 30)

        score = 0
        max_score = 100

        # Basic functionality (40 points)
        if actual_vulns > 0:
            score += 20
            print(f"✅ Vulnerability detection: {actual_vulns} found (+20)")
        else:
            print("❌ Vulnerability detection: None found (+0)")

        if actual_fixes > 0:
            score += 20
            print(f"✅ Remediation capability: {actual_fixes} fixes (+20)")
        else:
            print("❌ Remediation capability: No fixes (+0)")

        # File modification (30 points)
        if len(actual_changes) >= 3:
            score += 30
            print(f"✅ File modification: {len(actual_changes)} types (+30)")
        elif len(actual_changes) >= 2:
            score += 20
            print(f"✅ File modification: {len(actual_changes)} types (+20)")
        elif len(actual_changes) >= 1:
            score += 10
            print(f"✅ File modification: {len(actual_changes)} types (+10)")
        else:
            print("❌ File modification: None detected (+0)")

        # Specialized capabilities (30 points)
        if specialized_working >= 3:
            score += 30
            print(f"✅ Specialized agents: {specialized_working}/3 working (+30)")
        elif specialized_working >= 2:
            score += 20
            print(f"✅ Specialized agents: {specialized_working}/3 working (+20)")
        elif specialized_working >= 1:
            score += 10
            print(f"✅ Specialized agents: {specialized_working}/3 working (+10)")
        else:
            print("❌ Specialized agents: None working (+0)")

        print(f"\n🎯 REALISTIC SCORE: {score}/{max_score}")

        # Honest assessment
        if score >= 90:
            assessment = "Excellent autonomous capabilities"
        elif score >= 75:
            assessment = "Good autonomous capabilities"
        elif score >= 60:
            assessment = "Moderate autonomous capabilities"
        elif score >= 40:
            assessment = "Basic autonomous capabilities"
        else:
            assessment = "Limited autonomous capabilities"

        print(f"📋 HONEST ASSESSMENT: {assessment}")

        return score, actual_vulns, actual_fixes, len(actual_changes), specialized_working

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        executor.safe_mode = True

async def main():
    """Run realistic verification"""
    score, vulns, fixes, changes, specialized = await test_actual_capabilities()

    print(f"\n📊 SUMMARY:")
    print(f"   Vulnerabilities detected: {vulns}")
    print(f"   Fixes applied: {fixes}")
    print(f"   File changes: {changes}")
    print(f"   Specialized agents working: {specialized}/3")
    print(f"   Overall score: {score}/100")

if __name__ == "__main__":
    asyncio.run(main())