#!/usr/bin/env python3
"""
Verify module integration actually works
"""

import sys
import os
import asyncio

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

async def test_actual_execution():
    """Test if the LLM engine can actually call autonomous tools"""
    print("=" * 60)
    print("TESTING ACTUAL MODULE INTEGRATION")
    print("=" * 60)

    try:
        # Import the LLM decision engine
        from backend.src.llm_decision_engine import (
            LLMDecisionEngine, DecisionContext, AgentAction, RiskLevel
        )
        print("✅ Step 1: LLM Decision Engine imported")

        # Create engine
        engine = LLMDecisionEngine()
        print("✅ Step 2: Engine created")

        # Create test context
        context = DecisionContext(
            user_id="test",
            project_id="test",
            endpoint_data={"path": "/api/test", "method": "GET"},
            historical_data=[],
            user_preferences={},
            available_tools=["security_vulnerability_scan"],
            current_findings={},
            business_context="test"
        )
        print("✅ Step 3: Context created")

        # Create test action
        action = AgentAction(
            action_id="test_1",
            tool_name="security_vulnerability_scan",
            parameters={"target": "comprehensive"},
            risk_level=RiskLevel.SAFE,
            reasoning="Test scan",
            expected_outcome="Find vulnerabilities",
            estimated_duration=30
        )
        print("✅ Step 4: Action created")

        # Try to execute
        print("\n🔧 Attempting to execute action...")
        result = await engine.execute_action(action, context)

        print("\n📊 EXECUTION RESULT:")
        print(f"Status: {result.get('status')}")
        print(f"Action ID: {result.get('action_id')}")

        if 'error' in result:
            print(f"❌ Error: {result.get('error')}")
            print(f"Result: {result.get('result')}")

            # Check if it's the module import issue
            if 'Module import failed' in result.get('error', ''):
                print("\n⚠️  MODULE IMPORT ISSUE DETECTED")
                print("The autonomous_security_tools module exists but:")
                print("- The import fails at runtime in execute_action")
                return False
        else:
            print(f"✅ Result: {result.get('result')}")
            if 'vulnerabilities' in result:
                print(f"✅ Found {len(result.get('vulnerabilities', []))} vulnerabilities")
            return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_actual_execution())

    print("\n" + "=" * 60)
    if success:
        print("✅ MODULE INTEGRATION WORKING")
    else:
        print("❌ MODULE INTEGRATION STILL HAS ISSUES")
    print("=" * 60)