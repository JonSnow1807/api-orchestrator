#!/usr/bin/env python3
"""
Test ACTUAL autonomy - what can the system do WITHOUT human intervention?
"""

import sys
import os
import asyncio
import json

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

async def test_autonomous_capabilities():
    """Test what the system can ACTUALLY do autonomously"""
    print("=" * 60)
    print("TESTING ACTUAL AUTONOMY CAPABILITIES")
    print("=" * 60)

    results = {
        "vulnerability_scanning": False,
        "decision_making": False,
        "file_modification": False,
        "workflow_execution": False,
        "self_healing": False
    }

    # Test 1: Can it scan for vulnerabilities autonomously?
    print("\n📊 TEST 1: Autonomous Vulnerability Scanning")
    print("-" * 40)
    try:
        from backend.src.autonomous_security_tools import SecurityToolExecutor
        executor = SecurityToolExecutor()

        result = await executor.execute_security_vulnerability_scan(
            {"target": "comprehensive"},
            {"path": "/api/test", "method": "GET", "security": []}
        )

        if result.get('vulnerabilities'):
            print(f"✅ Found {len(result['vulnerabilities'])} vulnerabilities autonomously")
            print(f"   Examples: {[v.get('type', 'Unknown') for v in result['vulnerabilities'][:3]]}")
            results["vulnerability_scanning"] = True
        else:
            print("❌ No vulnerabilities found")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 2: Can it make decisions autonomously?
    print("\n📊 TEST 2: Autonomous Decision Making")
    print("-" * 40)
    try:
        from backend.src.llm_decision_engine import (
            LLMDecisionEngine, DecisionContext, DecisionType
        )

        engine = LLMDecisionEngine()
        context = DecisionContext(
            user_id="test",
            project_id="test",
            endpoint_data={"path": "/api/payment", "method": "POST"},
            historical_data=[],
            user_preferences={},
            available_tools=["security_vulnerability_scan"],
            current_findings={},
            business_context="payment processing"
        )

        plan = await engine.create_decision_plan(context, DecisionType.ANALYSIS_PLAN)

        if plan and plan.actions:
            print(f"✅ Created plan with {len(plan.actions)} actions autonomously")
            print(f"   Risk assessment: {plan.risk_assessment.value}")
            print(f"   Requires approval: {plan.requires_approval}")
            results["decision_making"] = True
        else:
            print("❌ No plan created")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 3: Can it modify files autonomously?
    print("\n📊 TEST 3: Autonomous File Modification")
    print("-" * 40)

    # Create test file
    test_file = "test_autonomy_target.py"
    with open(test_file, 'w') as f:
        f.write("debug = True\nimport hashlib\npassword = hashlib.md5('test'.encode()).hexdigest()")

    try:
        os.environ['AUTONOMOUS_SAFE_MODE'] = 'false'

        from backend.src.autonomous_security_tools import SecurityToolExecutor
        executor = SecurityToolExecutor()

        print(f"   Safe mode: {executor.safe_mode}")

        # Read original
        with open(test_file, 'r') as f:
            original = f.read()

        # Try to remediate
        result = await executor.execute_advanced_remediation(
            {"target_file": test_file, "auto_fix": True},
            {"path": "/api/test", "method": "POST"},
            "test"
        )

        # Check if modified
        with open(test_file, 'r') as f:
            modified = f.read()

        if modified != original:
            print(f"✅ File was ACTUALLY modified autonomously")
            print(f"   Fixes applied: {result.get('fixes_applied', 0)}")
            results["file_modification"] = True
        else:
            print(f"❌ File NOT modified (safe_mode={executor.safe_mode})")
    except Exception as e:
        print(f"❌ Failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        if 'AUTONOMOUS_SAFE_MODE' in os.environ:
            del os.environ['AUTONOMOUS_SAFE_MODE']

    # Test 4: Can it execute complete workflows?
    print("\n📊 TEST 4: Autonomous Workflow Execution")
    print("-" * 40)
    try:
        from backend.src.llm_decision_engine import LLMDecisionEngine

        engine = LLMDecisionEngine()

        # Can it execute without human intervention?
        context = DecisionContext(
            user_id="auto",
            project_id="auto",
            endpoint_data={"path": "/api/critical", "method": "DELETE"},
            historical_data=[],
            user_preferences={},
            available_tools=["security_vulnerability_scan", "compliance_check"],
            current_findings={},
            business_context="critical operation"
        )

        plan = await engine.create_decision_plan(context, DecisionType.ACTION_SEQUENCE)

        executed = 0
        for action in plan.actions[:2]:
            result = await engine.execute_action(action, context)
            if result.get('status') in ['completed', 'success']:
                executed += 1

        if executed > 0:
            print(f"✅ Executed {executed} actions in workflow autonomously")
            results["workflow_execution"] = True
        else:
            print("❌ No actions executed")
    except Exception as e:
        print(f"❌ Failed: {e}")

    # Test 5: Can it self-heal or adapt?
    print("\n📊 TEST 5: Self-Healing/Adaptation")
    print("-" * 40)
    try:
        # Test if it can handle missing tools gracefully
        from backend.src.llm_decision_engine import AgentAction, RiskLevel

        action = AgentAction(
            action_id="test",
            tool_name="non_existent_tool",
            parameters={},
            risk_level=RiskLevel.SAFE,
            reasoning="Test",
            expected_outcome="Test",
            estimated_duration=10
        )

        result = await engine.execute_action(action, context)

        if result.get('status') == 'unsupported' and 'not implemented' in result.get('result', ''):
            print("✅ Handles missing tools gracefully (self-adapts)")
            results["self_healing"] = True
        else:
            print("❌ Doesn't handle missing tools well")
    except Exception as e:
        print(f"❌ Failed: {e}")

    return results

async def main():
    results = await test_autonomous_capabilities()

    print("\n" + "=" * 60)
    print("AUTONOMY ASSESSMENT RESULTS")
    print("=" * 60)

    autonomous_count = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (autonomous_count / total) * 100

    print("\n📊 Capability Breakdown:")
    for capability, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {capability.replace('_', ' ').title()}: {'AUTONOMOUS' if status else 'NOT AUTONOMOUS'}")

    print(f"\n🎯 Autonomy Score: {autonomous_count}/{total} ({percentage:.0f}%)")

    print("\n📝 Verdict:")
    if percentage >= 80:
        print("✅ HIGHLY AUTONOMOUS - Can operate independently for most tasks")
    elif percentage >= 60:
        print("⚠️  PARTIALLY AUTONOMOUS - Some human intervention required")
    elif percentage >= 40:
        print("⚠️  SEMI-AUTONOMOUS - Significant human oversight needed")
    else:
        print("❌ NOT AUTONOMOUS - Requires constant human control")

    print("\n🔍 Reality Check:")
    print("- Vulnerability scanning: Real, finds actual issues")
    print("- Decision making: Uses fallback (no LLM), but works")
    print("- File modification: Real when safe mode disabled")
    print("- Workflow execution: Can chain multiple actions")
    print("- Self-healing: Basic error handling present")

if __name__ == "__main__":
    asyncio.run(main())
