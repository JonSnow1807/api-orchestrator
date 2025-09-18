#!/usr/bin/env python3
"""
File Modification Verification - Precise measurement of actual changes
"""

import asyncio
import sys
import os
import tempfile
import difflib

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from autonomous_security_tools import SecurityToolExecutor

async def test_exact_file_modifications():
    """Test exactly what gets modified in files"""
    print("🔬 FILE MODIFICATION VERIFICATION")
    print("=" * 50)

    # Original test content
    original_content = """from flask import Flask, request
import hashlib

app = Flask(__name__)

@app.route('/user/<user_id>')
def get_user(user_id):
    return f"User data for {user_id}"

@app.route('/login', methods=['POST'])
def login():
    password = request.form['password']
    hash_value = hashlib.md5(password.encode()).hexdigest()
    return {"hash": hash_value}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(original_content)
        temp_file_path = temp_file.name

    print("📝 BEFORE:")
    print(original_content)

    try:
        executor = SecurityToolExecutor()
        executor.safe_mode = False

        # Run remediation
        await executor.execute_advanced_remediation(
            {"target_file": temp_file_path},
            {"path": "/user/{user_id}", "method": "GET", "security": []},
            "Test application"
        )

        # Read modified content
        with open(temp_file_path, 'r') as f:
            modified_content = f.read()

        print("\n📝 AFTER:")
        print(modified_content)

        # Show exact differences
        print("\n🔍 EXACT DIFFERENCES:")
        diff = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            modified_content.splitlines(keepends=True),
            fromfile='original',
            tofile='modified',
            lineterm=''
        ))

        if diff:
            for line in diff:
                print(line.rstrip())
        else:
            print("No differences found")

        # Count specific changes
        changes_detected = {
            "md5_to_sha256": "sha256" in modified_content and "md5" not in modified_content,
            "debug_disabled": "debug=False" in modified_content,
            "auth_added": "# Added by autonomous security" in modified_content,
            "env_vars": "os.getenv" in modified_content,
            "imports_added": modified_content.count("import") > original_content.count("import")
        }

        print(f"\n✅ VERIFIED CHANGES:")
        actual_changes = 0
        for change, detected in changes_detected.items():
            status = "YES" if detected else "NO"
            if detected:
                actual_changes += 1
            print(f"   {change}: {status}")

        print(f"\n📊 TOTAL VERIFIED CHANGES: {actual_changes}/5")

        return actual_changes, len(diff) > 0

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

async def main():
    changes, file_modified = await test_exact_file_modifications()

    print(f"\n🎯 FINAL VERIFICATION:")
    print(f"   File was modified: {file_modified}")
    print(f"   Verified changes: {changes}")

    if changes >= 3:
        print("✅ Strong autonomous modification capability")
    elif changes >= 2:
        print("✅ Good autonomous modification capability")
    elif changes >= 1:
        print("⚠️ Basic autonomous modification capability")
    else:
        print("❌ No autonomous modification detected")

if __name__ == "__main__":
    asyncio.run(main())