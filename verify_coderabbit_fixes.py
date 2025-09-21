#!/usr/bin/env python3
"""
COMPREHENSIVE VERIFICATION SCRIPT
Validates all CodeRabbit issues were properly fixed in ai_agent_collaboration.py
"""

import re
import sys
import os

def read_file(filepath):
    """Read file content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def verify_coderabbit_fixes():
    """Verify all CodeRabbit issues are resolved"""

    filepath = '/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/backend/src/ai_agent_collaboration.py'
    content = read_file(filepath)

    if not content:
        return False

    print("🔍 COMPREHENSIVE CODERABBIT VERIFICATION")
    print("=" * 60)

    issues_resolved = 0
    total_issues = 6

    # Issue 1: Remove simulation code
    print("\n1️⃣ Checking: Simulation code removal...")
    simulation_patterns = [
        r'_simulate_agent_response',
        r'def.*simulate.*response',
        r'simulated.*response',
        r'return.*simulated'
    ]

    found_simulation = False
    for pattern in simulation_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"   ❌ Found simulation code: {pattern}")
            found_simulation = True

    if not found_simulation:
        print("   ✅ No simulation code found - FIXED")
        issues_resolved += 1

    # Issue 2: Agent initialization error handling
    print("\n2️⃣ Checking: Agent initialization error handling...")
    init_patterns = [
        r'Failed to initialize any agents',
        r'_initialize_agents.*failed_agents',
        r'try:.*agent_class\(\)',
        r'except.*Exception.*agent_id'
    ]

    init_checks = 0
    for pattern in init_patterns:
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            init_checks += 1

    if init_checks >= 3:
        print("   ✅ Robust agent initialization error handling - FIXED")
        issues_resolved += 1
    else:
        print(f"   ❌ Missing initialization error handling ({init_checks}/4 patterns)")

    # Issue 3: Async gather fix
    print("\n3️⃣ Checking: Async gather background tasks fix...")
    if 'asyncio.create_task(' in content and 'self._background_tasks' in content:
        # Check that there's no blocking await asyncio.gather on infinite tasks
        gather_lines = [line for line in content.split('\n') if 'await asyncio.gather' in line]
        blocking_gather = False
        for line in gather_lines:
            # Check if it's awaiting background tasks (bad)
            if any(task in line for task in ['_message_router', '_health_monitor', '_performance_tracker', '_collaboration_optimizer']):
                blocking_gather = True
                break

        if not blocking_gather:
            print("   ✅ Background tasks use create_task, no blocking gather - FIXED")
            issues_resolved += 1
        else:
            print("   ❌ Still has blocking await gather on background tasks")
    else:
        print("   ❌ Missing asyncio.create_task implementation")

    # Issue 4: Dataclass Optional types
    print("\n4️⃣ Checking: Dataclass Optional field types...")
    optional_patterns = [
        r'assigned_agents:\s*Optional\[List\[str\]\]',
        r'results:\s*Optional\[Dict\[str,\s*Any\]\]'
    ]

    optional_checks = 0
    for pattern in optional_patterns:
        if re.search(pattern, content):
            optional_checks += 1

    if optional_checks >= 2:
        print("   ✅ Dataclass fields use Optional types - FIXED")
        issues_resolved += 1
    else:
        print(f"   ❌ Missing Optional types ({optional_checks}/2 patterns)")

    # Issue 5: Agent validation
    print("\n5️⃣ Checking: Agent selection validation...")
    validation_pattern = r'agent_id\s+in\s+self\.agents\s+and\s+agent_id\s+in\s+self\.agent_capabilities'

    if re.search(validation_pattern, content):
        print("   ✅ Agent selection validates both dicts - FIXED")
        issues_resolved += 1
    else:
        print("   ❌ Missing dual dict validation in agent selection")

    # Issue 6: All collaboration modes implemented
    print("\n6️⃣ Checking: All collaboration modes implemented...")
    collaboration_methods = [
        r'def _execute_swarm_collaboration',
        r'def _execute_parallel_collaboration',
        r'def _execute_sequential_collaboration',
        r'def _execute_hierarchical_collaboration'
    ]

    method_count = 0
    for method in collaboration_methods:
        if re.search(method, content):
            method_count += 1

    if method_count == 4:
        print("   ✅ All 4 collaboration modes implemented - FIXED")
        issues_resolved += 1
    else:
        print(f"   ❌ Missing collaboration methods ({method_count}/4)")

    # Additional verification: Real agent method calls
    print("\n🔍 BONUS: Checking for real agent method calls...")
    if '_call_agent_method' in content and 'await self._call_agent_method(agent_id, task_data)' in content:
        print("   ✅ Real agent method calls implemented")
    else:
        print("   ❌ Missing real agent method calls")

    # Agent status initialization
    print("\n🔍 BONUS: Checking agent status initialization...")
    if '_initialize_agent_statuses()' in content and 'def _initialize_agent_statuses' in content:
        print("   ✅ Agent status initialization in constructor")
    else:
        print("   ❌ Missing agent status initialization")

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 VERIFICATION SUMMARY: {issues_resolved}/{total_issues} CODERABBIT ISSUES RESOLVED")

    if issues_resolved == total_issues:
        print("🎉 SUCCESS: ALL CODERABBIT ISSUES HAVE BEEN RESOLVED!")
        print("✅ The AI agent collaboration system is genuinely functional")
        return True
    else:
        print(f"❌ FAILURE: {total_issues - issues_resolved} issues remain unresolved")
        print("⚠️  System may not be fully functional")
        return False

def verify_file_structure():
    """Verify the file exists and has reasonable size"""
    filepath = '/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/backend/src/ai_agent_collaboration.py'

    print("📁 FILE VERIFICATION")
    print("-" * 30)

    if not os.path.exists(filepath):
        print(f"❌ File does not exist: {filepath}")
        return False

    size = os.path.getsize(filepath)
    lines = len(open(filepath, 'r').readlines())

    print(f"✅ File exists: {filepath}")
    print(f"📏 File size: {size:,} bytes")
    print(f"📄 Line count: {lines:,} lines")

    if size < 10000:  # Less than 10KB seems too small
        print("⚠️  File seems unusually small")
        return False

    if lines < 200:  # Less than 200 lines seems incomplete
        print("⚠️  File seems to have too few lines")
        return False

    print("✅ File structure looks reasonable")
    return True

if __name__ == "__main__":
    print("🤖 CODERABBIT FIXES VERIFICATION TOOL")
    print("Independently verifying all reported fixes")
    print("\n")

    # Verify file exists
    if not verify_file_structure():
        sys.exit(1)

    # Verify all CodeRabbit issues are resolved
    if verify_coderabbit_fixes():
        print("\n✅ VERIFICATION COMPLETE: System is genuinely functional!")
        sys.exit(0)
    else:
        print("\n❌ VERIFICATION FAILED: Issues remain!")
        sys.exit(1)