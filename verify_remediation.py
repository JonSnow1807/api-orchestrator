#!/usr/bin/env python3
"""
Test auto-remediation with actual file modification
"""

import sys
import os
import asyncio
import shutil
from datetime import datetime

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

async def test_auto_remediation():
    """Test if auto-remediation actually modifies files"""
    print("=" * 60)
    print("TESTING AUTO-REMEDIATION")
    print("=" * 60)

    target_file = 'test_vulnerable.py'

    # First, backup the original
    backup_file = f"{target_file}.original_backup"
    shutil.copy(target_file, backup_file)
    print(f"✅ Created backup: {backup_file}")

    # Read original content
    with open(target_file, 'r') as f:
        original_content = f.read()
    print(f"📄 Original file has {len(original_content)} characters")

    try:
        # Disable safe mode for this test
        os.environ['AUTONOMOUS_SAFE_MODE'] = 'false'
        print("⚠️  Set AUTONOMOUS_SAFE_MODE=false")

        from backend.src.autonomous_security_tools import SecurityToolExecutor

        # Create executor
        executor = SecurityToolExecutor()
        print(f"✅ SecurityToolExecutor created (safe_mode={executor.safe_mode})")

        if executor.safe_mode:
            print("❌ Safe mode is still enabled! Auto-remediation won't work.")
            return False

        # Run vulnerability scan
        vuln_result = await executor.execute_security_vulnerability_scan(
            {'target_file': target_file},
            {'path': '/api/test', 'method': 'GET'}
        )
        print(f"🔍 Found {vuln_result.get('total_vulnerabilities', 0)} vulnerabilities")

        # Run advanced remediation
        remediation_result = await executor.execute_advanced_remediation(
            {'target_file': target_file, 'auto_fix': True},
            {'path': '/api/test', 'method': 'GET'},
            'test context'
        )

        fixes_applied = remediation_result.get('fixes_applied', 0)
        print(f"🔧 Fixes applied: {fixes_applied}")

        # Check if file was actually modified
        with open(target_file, 'r') as f:
            new_content = f.read()

        if new_content != original_content:
            print("✅ FILE WAS ACTUALLY MODIFIED!")
            print("\n📊 Changes made:")

            # Show some changes
            if 'debug=False' in new_content and 'debug=True' in original_content:
                print("  - Debug mode disabled")
            if 'sha256' in new_content and 'md5' in original_content:
                print("  - MD5 upgraded to SHA256")
            if 'os.environ' in new_content and 'API_KEY = "sk-' in original_content:
                print("  - Hardcoded secrets replaced with env vars")

            # Check for backup files
            import glob
            backups = glob.glob(f"{target_file}.backup.*")
            if backups:
                print(f"\n💾 Found {len(backups)} backup file(s):")
                for b in backups:
                    print(f"  - {b}")

            return True
        else:
            print("❌ FILE WAS NOT MODIFIED")
            print(f"File modified flag: {remediation_result.get('file_modified', False)}")
            return False

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Restore original file
        shutil.copy(backup_file, target_file)
        os.remove(backup_file)
        print(f"\n♻️  Restored original file from backup")

        # Clean up any created backups
        import glob
        for backup in glob.glob(f"{target_file}.backup.*"):
            os.remove(backup)
            print(f"🗑️  Cleaned up: {backup}")

        # Reset environment
        if 'AUTONOMOUS_SAFE_MODE' in os.environ:
            del os.environ['AUTONOMOUS_SAFE_MODE']

if __name__ == "__main__":
    success = asyncio.run(test_auto_remediation())

    print("\n" + "=" * 60)
    if success:
        print("✅ AUTO-REMEDIATION ACTUALLY WORKS")
    else:
        print("❌ AUTO-REMEDIATION NOT WORKING")
    print("=" * 60)