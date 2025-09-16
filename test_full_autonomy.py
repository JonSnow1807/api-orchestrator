#!/usr/bin/env python3
"""
Test Full Autonomy - Verify complete autonomous operation
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from llm_decision_engine import LLMDecisionEngine, DecisionContext, DecisionType

async def test_full_autonomous_execution():
    """Test complete autonomous workflow"""
    print("🤖 TESTING FULL AUTONOMOUS EXECUTION")
    print("=" * 50)

    # Set up environment
    env_file = 'backend/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    os.environ['ANTHROPIC_API_KEY'] = line.split('=', 1)[1].strip()
                elif line.startswith('OPENAI_API_KEY='):
                    os.environ['OPENAI_API_KEY'] = line.split('=', 1)[1].strip()

    # Create LLM engine
    engine = LLMDecisionEngine()

    # Test realistic scenario
    context = DecisionContext(
        user_id="autonomy_test",
        project_id="verification",
        endpoint_data={
            "path": "/api/v1/healthcare/patient/{patient_id}",
            "method": "GET",
            "security": [],  # Missing auth - should be flagged
            "parameters": [
                {"name": "patient_id", "in": "path", "required": True},
                {"name": "include_phi", "in": "query", "required": False}
            ]
        },
        historical_data=[],
        user_preferences={"auto_fix_low_risk": True},
        available_tools=[
            "security_vulnerability_scan",
            "auth_mechanism_analysis",
            "compliance_check",
            "auto_fix_security_headers",
            "advanced_remediation"
        ],
        current_findings={},
        business_context="Healthcare telemedicine platform processing patient PHI data with HIPAA compliance requirements"
    )

    try:
        # Step 1: AI Planning
        print("📋 Step 1: AI Decision Planning...")
        plan = await engine.create_decision_plan(context, DecisionType.ANALYSIS_PLAN)

        print(f"   ✅ Plan created: {plan.plan_id}")
        print(f"   📊 Actions planned: {len(plan.actions)}")
        print(f"   🎯 Confidence: {plan.confidence_score:.1%}")
        print(f"   ⚠️  Risk level: {plan.risk_assessment.value}")

        # Step 2: Autonomous Execution
        print("\n⚡ Step 2: Autonomous Tool Execution...")
        execution_results = []

        for i, action in enumerate(plan.actions):
            print(f"   🔧 Executing {i+1}/{len(plan.actions)}: {action.tool_name}")

            try:
                result = await engine.execute_action(action, context)
                execution_results.append({
                    'tool': action.tool_name,
                    'status': result.get('status', 'unknown'),
                    'success': result.get('status') == 'completed',
                    'findings': {
                        'vulnerabilities': result.get('vulnerabilities_found', 0),
                        'auth_issues': result.get('auth_issues_found', 0),
                        'compliance_issues': result.get('compliance_issues', 0),
                        'fixes_applied': result.get('fixes_applied', 0)
                    }
                })
                print(f"      ✅ Status: {result.get('status')}")

            except Exception as e:
                execution_results.append({
                    'tool': action.tool_name,
                    'status': 'failed',
                    'success': False,
                    'error': str(e)
                })
                print(f"      ❌ Failed: {str(e)}")

        # Step 3: Analysis
        print("\n📊 Step 3: Execution Analysis...")
        successful_executions = len([r for r in execution_results if r['success']])
        total_executions = len(execution_results)

        total_vulnerabilities = sum(r['findings'].get('vulnerabilities', 0) for r in execution_results)
        total_auth_issues = sum(r['findings'].get('auth_issues', 0) for r in execution_results)
        total_compliance_issues = sum(r['findings'].get('compliance_issues', 0) for r in execution_results)
        total_fixes = sum(r['findings'].get('fixes_applied', 0) for r in execution_results)

        print(f"   📈 Success Rate: {successful_executions}/{total_executions} ({successful_executions/total_executions*100:.1f}%)")
        print(f"   🔍 Security Findings:")
        print(f"      - Vulnerabilities: {total_vulnerabilities}")
        print(f"      - Auth Issues: {total_auth_issues}")
        print(f"      - Compliance Issues: {total_compliance_issues}")
        print(f"   🔧 Autonomous Fixes: {total_fixes}")

        # Step 4: Autonomy Assessment
        print("\n🎯 Step 4: Autonomy Assessment...")

        autonomy_score = 0

        # Planning capability (25 points)
        if len(plan.actions) > 0:
            autonomy_score += 25
            print("   ✅ AI Planning: AUTONOMOUS (25/25)")
        else:
            print("   ❌ AI Planning: FAILED (0/25)")

        # Execution capability (25 points)
        if successful_executions > 0:
            execution_score = int((successful_executions / total_executions) * 25)
            autonomy_score += execution_score
            print(f"   ✅ Tool Execution: AUTONOMOUS ({execution_score}/25)")
        else:
            print("   ❌ Tool Execution: FAILED (0/25)")

        # Real analysis (25 points)
        if total_vulnerabilities > 0 or total_auth_issues > 0 or total_compliance_issues > 0:
            autonomy_score += 25
            print("   ✅ Security Analysis: AUTONOMOUS (25/25)")
        else:
            print("   ❌ Security Analysis: FAILED (0/25)")

        # Real actions (25 points)
        if total_fixes > 0:
            autonomy_score += 25
            print("   ✅ Autonomous Remediation: AUTONOMOUS (25/25)")
        else:
            print("   ⚠️  Autonomous Remediation: LIMITED (0/25)")

        print(f"\n🏆 OVERALL AUTONOMY SCORE: {autonomy_score}/100")

        if autonomy_score >= 90:
            verdict = "🏆 FULLY AUTONOMOUS"
        elif autonomy_score >= 70:
            verdict = "✅ HIGHLY AUTONOMOUS"
        elif autonomy_score >= 50:
            verdict = "⚠️  MODERATELY AUTONOMOUS"
        else:
            verdict = "❌ LIMITED AUTONOMY"

        print(f"🎯 VERDICT: {verdict}")

        return autonomy_score >= 70

    except Exception as e:
        print(f"❌ Full autonomy test failed: {str(e)}")
        return False

async def main():
    """Run full autonomy test"""
    success = await test_full_autonomous_execution()

    if success:
        print("\n🎉 AUTONOMY ACHIEVED - System is truly autonomous!")
    else:
        print("\n⚠️  AUTONOMY LIMITED - Further improvements needed")

if __name__ == "__main__":
    asyncio.run(main())