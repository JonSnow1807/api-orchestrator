#!/usr/bin/env python3
"""
Test end-to-end workflow execution
"""

import sys
import os
import asyncio

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

async def test_complete_workflow():
    """Test complete workflow from decision to execution"""
    print("=" * 60)
    print("TESTING END-TO-END WORKFLOW")
    print("=" * 60)

    try:
        from backend.src.llm_decision_engine import (
            LLMDecisionEngine, DecisionContext, DecisionType
        )
        print("✅ Step 1: Imported LLM Decision Engine")

        # Create engine
        engine = LLMDecisionEngine()
        print(f"✅ Step 2: Engine created (LLM available: {engine.llm_available})")

        # Create context
        context = DecisionContext(
            user_id="test_user",
            project_id="test_project",
            endpoint_data={
                "path": "/api/payment/process",
                "method": "POST",
                "security": []
            },
            historical_data=[],
            user_preferences={},
            available_tools=[
                "security_vulnerability_scan",
                "auth_mechanism_analysis",
                "compliance_check"
            ],
            current_findings={},
            business_context="Financial payment processing endpoint"
        )
        print("✅ Step 3: Created context for payment endpoint")

        # Create decision plan
        print("\n📋 Creating decision plan...")
        plan = await engine.create_decision_plan(context, DecisionType.ANALYSIS_PLAN)

        print(f"✅ Step 4: Plan created")
        print(f"  - Plan ID: {plan.plan_id}")
        print(f"  - Actions: {len(plan.actions)}")
        print(f"  - Risk Level: {plan.risk_assessment.value}")
        print(f"  - Confidence: {plan.confidence_score:.1%}")

        # Execute actions
        print("\n🔧 Executing actions...")
        results = []
        for i, action in enumerate(plan.actions[:3], 1):  # Limit to first 3 actions
            print(f"\n  Action {i}: {action.tool_name}")
            print(f"  - Risk: {action.risk_level.value}")
            print(f"  - Reasoning: {action.reasoning[:100]}...")

            result = await engine.execute_action(action, context)
            results.append(result)

            if result.get('status') == 'completed':
                print(f"  ✅ Completed successfully")
                if 'vulnerabilities' in result:
                    vulns = result.get('vulnerabilities', [])
                    print(f"  - Found {len(vulns)} vulnerabilities")
            else:
                print(f"  ⚠️  Status: {result.get('status')}")

        # Summary
        print("\n📊 WORKFLOW SUMMARY:")
        print(f"- Plan created: ✅")
        print(f"- Total actions: {len(plan.actions)}")
        print(f"- Actions executed: {len(results)}")
        successful = sum(1 for r in results if r.get('status') == 'completed')
        print(f"- Successful: {successful}/{len(results)}")

        return successful > 0

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())

    print("\n" + "=" * 60)
    if success:
        print("✅ END-TO-END WORKFLOW WORKS")
    else:
        print("❌ WORKFLOW HAS ISSUES")
    print("=" * 60)