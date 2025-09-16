#!/usr/bin/env python3
"""
Autonomy Verification Test - Check if the system actually performs autonomous actions or just simulates them
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from backend.src.autonomous_security_tools import SecurityToolExecutor
from backend.src.llm_decision_engine import LLMDecisionEngine, DecisionContext, DecisionType

class AutonomyVerifier:
    """Verify actual autonomy vs simulation"""

    def __init__(self):
        self.verification_results = {}

    async def test_vulnerability_scanning_autonomy(self):
        """Test if vulnerability scanning actually analyzes real code/endpoints"""
        print("🔍 TESTING VULNERABILITY SCANNING AUTONOMY")
        print("-" * 50)

        executor = SecurityToolExecutor()

        # Test 1: Different endpoint types should produce different results
        endpoints = [
            {
                "path": "/api/v1/admin/users",
                "method": "GET",
                "security": [],  # No auth
                "parameters": []
            },
            {
                "path": "/api/v1/public/health",
                "method": "GET",
                "security": [{"type": "jwt", "scheme": "bearer"}],  # With auth
                "parameters": [{"name": "detailed", "in": "query"}]
            },
            {
                "path": "/api/v1/payment/process",
                "method": "POST",
                "security": [{"type": "apiKey"}, {"type": "jwt"}],  # Multiple auth
                "parameters": [
                    {"name": "amount", "in": "body", "required": True},
                    {"name": "card_number", "in": "body", "required": True}
                ]
            }
        ]

        results = []
        for i, endpoint in enumerate(endpoints):
            print(f"   Testing endpoint {i+1}: {endpoint['method']} {endpoint['path']}")
            result = await executor.execute_security_vulnerability_scan({}, endpoint)
            results.append({
                'endpoint': endpoint['path'],
                'vulnerabilities': result.get('vulnerabilities_found', 0),
                'issues': result.get('vulnerabilities', []),
                'recommendations': result.get('recommendations', [])
            })

        # Analyze if results are dynamic based on input
        unique_vuln_counts = set(r['vulnerabilities'] for r in results)
        different_recommendations = len(set(str(r['recommendations']) for r in results))

        autonomy_score = 0
        if len(unique_vuln_counts) > 1:
            autonomy_score += 40  # Different vulnerability counts = analyzing input
        if different_recommendations > 1:
            autonomy_score += 30  # Different recommendations = contextual analysis
        if any(len(r['issues']) > 0 for r in results):
            autonomy_score += 30  # Actually finding issues = real analysis

        print(f"   📊 Results:")
        for r in results:
            print(f"      {r['endpoint']}: {r['vulnerabilities']} vulns, {len(r['recommendations'])} recommendations")

        print(f"   🎯 Autonomy Score: {autonomy_score}/100")

        self.verification_results['vulnerability_scanning'] = {
            'score': autonomy_score,
            'evidence': f"Found {len(unique_vuln_counts)} unique vulnerability patterns across {len(endpoints)} endpoints",
            'autonomous': autonomy_score >= 60
        }

    async def test_compliance_checking_autonomy(self):
        """Test if compliance checking actually varies by industry/context"""
        print("\n📋 TESTING COMPLIANCE CHECKING AUTONOMY")
        print("-" * 50)

        executor = SecurityToolExecutor()

        # Test with different business contexts
        contexts = [
            ("Healthcare telemedicine platform", {"path": "/api/patient/records", "method": "GET"}),
            ("Financial payment processor", {"path": "/api/transactions", "method": "POST"}),
            ("Generic e-commerce site", {"path": "/api/products", "method": "GET"})
        ]

        results = []
        for context, endpoint in contexts:
            print(f"   Testing context: {context[:30]}...")
            result = await executor.execute_compliance_check({}, endpoint, context)

            frameworks = result.get('frameworks_checked', [])
            issues = result.get('compliance_issues', 0)

            results.append({
                'context': context,
                'frameworks': frameworks,
                'issues': issues,
                'industry_intelligence': result.get('industry_intelligence', {})
            })

        # Analyze if frameworks/analysis varies by industry
        unique_frameworks = set()
        for r in results:
            unique_frameworks.update(r['frameworks'])

        framework_variation = len(set(str(sorted(r['frameworks'])) for r in results))
        industry_intelligence_variation = len(set(str(r['industry_intelligence'].get('industry', 'none')) for r in results))

        autonomy_score = 0
        if framework_variation > 1:
            autonomy_score += 40  # Different frameworks for different industries
        if industry_intelligence_variation > 1:
            autonomy_score += 30  # Industry-specific intelligence
        if len(unique_frameworks) >= 5:
            autonomy_score += 30  # Substantial framework knowledge

        print(f"   📊 Results:")
        for r in results:
            industry = r['industry_intelligence'].get('industry', 'Unknown')
            print(f"      {industry}: {len(r['frameworks'])} frameworks, {r['issues']} issues")

        print(f"   🎯 Autonomy Score: {autonomy_score}/100")

        self.verification_results['compliance_checking'] = {
            'score': autonomy_score,
            'evidence': f"Applied {len(unique_frameworks)} unique frameworks across {len(contexts)} industries",
            'autonomous': autonomy_score >= 60
        }

    async def test_remediation_autonomy(self):
        """Test if auto-remediation actually makes real changes"""
        print("\n🔧 TESTING AUTO-REMEDIATION AUTONOMY")
        print("-" * 50)

        executor = SecurityToolExecutor()

        # Create a temporary file to test if remediation actually writes files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write("""
# Test security issues
import hashlib

def weak_hash(data):
    return hashlib.md5(data).hexdigest()  # Weak hash

def sql_query(user_input):
    query = f"SELECT * FROM users WHERE name = '{user_input}'"  # SQL injection
    return query

def unsafe_eval(code):
    return eval(code)  # Code injection
""")
            temp_file_path = temp_file.name

        try:
            # Test remediation on the file
            result = await executor.execute_advanced_remediation(
                {"target_file": temp_file_path},
                {"path": "/api/test", "method": "POST"},
                "Test application with security issues"
            )

            # Check if file was actually modified
            with open(temp_file_path, 'r') as f:
                modified_content = f.read()

            # Analyze changes
            fixes_applied = result.get('fixes_applied', 0)
            recommendations = result.get('recommendations', [])

            # Check if content was actually changed
            content_changed = "md5" not in modified_content or "eval(" not in modified_content

            autonomy_score = 0
            if fixes_applied > 0:
                autonomy_score += 40  # Claims to apply fixes
            if len(recommendations) > 0:
                autonomy_score += 20  # Provides recommendations
            if content_changed:
                autonomy_score += 40  # Actually modified content
            else:
                autonomy_score -= 20  # Claims fixes but no actual changes

            print(f"   📊 Results:")
            print(f"      Fixes Applied: {fixes_applied}")
            print(f"      Recommendations: {len(recommendations)}")
            print(f"      File Modified: {'✅ Yes' if content_changed else '❌ No'}")

            print(f"   🎯 Autonomy Score: {autonomy_score}/100")

            self.verification_results['auto_remediation'] = {
                'score': autonomy_score,
                'evidence': f"Claimed {fixes_applied} fixes, file modified: {content_changed}",
                'autonomous': autonomy_score >= 60
            }

        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    async def test_end_to_end_autonomy(self):
        """Test full autonomous workflow"""
        print("\n🤖 TESTING END-TO-END AUTONOMY")
        print("-" * 50)

        # Set up environment
        import os
        env_file = 'backend/.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        os.environ['ANTHROPIC_API_KEY'] = line.split('=', 1)[1].strip()

        engine = LLMDecisionEngine()

        # Test realistic scenario
        context = DecisionContext(
            user_id="autonomy_test",
            project_id="verification",
            endpoint_data={
                "path": "/api/v1/sensitive/data",
                "method": "POST",
                "security": [],  # Deliberately insecure
                "parameters": [
                    {"name": "user_data", "in": "body", "required": True}
                ]
            },
            historical_data=[],
            user_preferences={"auto_fix_low_risk": True},
            available_tools=[
                "security_vulnerability_scan",
                "auth_mechanism_analysis",
                "compliance_check",
                "advanced_remediation"
            ],
            current_findings={},
            business_context="Healthcare application processing patient data"
        )

        # Test planning
        print("   📋 Testing AI planning...")
        plan = await engine.create_decision_plan(context, DecisionType.ANALYSIS_PLAN)

        # Test execution
        print("   ⚡ Testing autonomous execution...")
        execution_results = []
        for action in plan.actions:
            try:
                result = await engine.execute_action(action, context)
                execution_results.append({
                    'tool': action.tool_name,
                    'status': result.get('status', 'unknown'),
                    'has_real_results': bool(
                        result.get('vulnerabilities_found', 0) > 0 or
                        result.get('auth_issues_found', 0) > 0 or
                        result.get('compliance_issues', 0) > 0 or
                        result.get('industry_intelligence')
                    )
                })
            except Exception as e:
                execution_results.append({
                    'tool': action.tool_name,
                    'status': 'failed',
                    'error': str(e),
                    'has_real_results': False
                })

        # Analyze autonomy
        planned_actions = len(plan.actions)
        executed_actions = len([r for r in execution_results if r['status'] != 'failed'])
        real_results = len([r for r in execution_results if r.get('has_real_results', False)])

        autonomy_score = 0
        if planned_actions > 0:
            autonomy_score += 20  # Can create plans
        if executed_actions > 0:
            autonomy_score += 30  # Can execute actions
        if real_results > 0:
            autonomy_score += 30  # Produces real results
        if executed_actions == planned_actions:
            autonomy_score += 20  # Executes full plan

        print(f"   📊 Results:")
        print(f"      Actions Planned: {planned_actions}")
        print(f"      Actions Executed: {executed_actions}")
        print(f"      Actions with Real Results: {real_results}")

        print(f"   🎯 Autonomy Score: {autonomy_score}/100")

        self.verification_results['end_to_end'] = {
            'score': autonomy_score,
            'evidence': f"Planned {planned_actions}, executed {executed_actions}, {real_results} with real results",
            'autonomous': autonomy_score >= 60
        }

    def generate_autonomy_report(self):
        """Generate final autonomy assessment"""
        print("\n" + "="*70)
        print("🏆 AUTONOMY VERIFICATION REPORT")
        print("="*70)

        total_score = 0
        total_tests = len(self.verification_results)
        autonomous_systems = 0

        for test_name, result in self.verification_results.items():
            score = result['score']
            is_autonomous = result['autonomous']
            total_score += score
            if is_autonomous:
                autonomous_systems += 1

            status = "✅ AUTONOMOUS" if is_autonomous else "❌ SIMULATED"
            print(f"{status} {test_name.upper()}: {score}/100")
            print(f"   Evidence: {result['evidence']}")

        overall_score = total_score / total_tests if total_tests > 0 else 0
        autonomy_percentage = (autonomous_systems / total_tests * 100) if total_tests > 0 else 0

        print(f"\n📊 OVERALL ASSESSMENT:")
        print(f"   🎯 Average Score: {overall_score:.1f}/100")
        print(f"   🤖 Autonomous Systems: {autonomous_systems}/{total_tests} ({autonomy_percentage:.1f}%)")

        if overall_score >= 80:
            verdict = "🏆 HIGHLY AUTONOMOUS - Real AI capabilities"
        elif overall_score >= 60:
            verdict = "✅ MODERATELY AUTONOMOUS - Some real capabilities"
        elif overall_score >= 40:
            verdict = "⚠️  LIMITED AUTONOMY - Mostly simulation"
        else:
            verdict = "❌ NOT AUTONOMOUS - Pure simulation"

        print(f"   🔍 VERDICT: {verdict}")

        # Save detailed report
        with open('autonomy_verification_report.txt', 'w') as f:
            f.write("AUTONOMY VERIFICATION REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Overall Score: {overall_score:.1f}/100\n")
            f.write(f"Autonomous Systems: {autonomous_systems}/{total_tests}\n")
            f.write(f"Verdict: {verdict}\n\n")

            for test_name, result in self.verification_results.items():
                f.write(f"{test_name.upper()}: {result['score']}/100\n")
                f.write(f"Evidence: {result['evidence']}\n")
                f.write(f"Autonomous: {result['autonomous']}\n\n")

        print(f"\n💾 Detailed report saved to: autonomy_verification_report.txt")

async def main():
    """Run autonomy verification"""
    verifier = AutonomyVerifier()

    await verifier.test_vulnerability_scanning_autonomy()
    await verifier.test_compliance_checking_autonomy()
    await verifier.test_remediation_autonomy()
    await verifier.test_end_to_end_autonomy()

    verifier.generate_autonomy_report()

if __name__ == "__main__":
    asyncio.run(main())