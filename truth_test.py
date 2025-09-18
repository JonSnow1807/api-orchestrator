#!/usr/bin/env python3
"""
TRUTH TEST - Let's see what ACTUALLY works vs what's fake
"""

import asyncio
import sys
import os

sys.path.insert(0, '/Users/chinmayshrivastava/Api Orchestrator/api-orchestrator/backend')

async def truth_test():
    print("=" * 80)
    print("TRUTH TEST - REVEALING WHAT'S REAL VS FAKE")
    print("=" * 80)

    results = {
        "real": [],
        "fake": [],
        "partial": []
    }

    # TEST 1: Code Generation
    print("\n1. CODE GENERATION AGENT")
    try:
        from src.ai_employee.code_generation_agent import CodeGenerationAgent
        agent = CodeGenerationAgent()

        # Test if it generates real code
        result = await agent.generate_api_client(
            {"name": "Test", "endpoints": [{"method": "GET", "path": "/test"}]},
            "python"
        )

        # Check if it's real code
        is_real_code = (
            len(result.code) > 100 and
            "import" in result.code and
            ("class" in result.code or "def" in result.code)
        )

        if is_real_code:
            print("✅ Generates real code")
            results["real"].append("Code generation")
        else:
            print("❌ Generates placeholder")
            results["fake"].append("Code generation")

        # Test fix functionality
        fixed = await agent.fix_broken_code("def test():\n    return undefined_var", "NameError", "python")
        if "undefined_var" not in fixed or fixed != "def test():\n    return undefined_var":
            print("✅ Actually fixes code")
            results["real"].append("Code fixing")
        else:
            print("❌ Doesn't really fix code")
            results["fake"].append("Code fixing")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["fake"].append("Code generation agent")

    # TEST 2: Self-Learning
    print("\n2. SELF-LEARNING SYSTEM")
    try:
        from src.ai_employee.self_learning_system import SelfLearningSystem
        system = SelfLearningSystem()

        # Test if it actually learns
        initial_kb_size = len(system.knowledge_base)
        pattern = await system.learn_from_vulnerability({"type": "SQL", "endpoint": "/test", "severity": "high"})

        # Check if it actually stored something
        if pattern.pattern_id and pattern.confidence > 0:
            print("✅ Creates learning patterns")
            results["real"].append("Learning patterns")
        else:
            print("❌ Fake learning")
            results["fake"].append("Learning patterns")

        # Test predictions
        predictions = await system.predict_issues({"paths": {"/test": {"get": {}}}})
        print(f"   Predictions made: {len(predictions)}")

        if len(predictions) == 0:
            print("⚠️  Makes no predictions (learning system might be placeholder)")
            results["partial"].append("Predictions")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["fake"].append("Self-learning system")

    # TEST 3: Database Agent
    print("\n3. DATABASE AGENT")
    try:
        from src.ai_employee.database_agent import DatabaseAgent
        agent = DatabaseAgent("sqlite:///:memory:")

        # Test optimization
        query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        result = await agent.optimize_query(query)

        # Check if it actually optimizes
        if result.optimized_query and result.optimized_query != query:
            # Check for real optimizations beyond just comments
            has_real_changes = (
                result.optimization_type and
                "none" not in result.optimization_type and
                any(opt in result.optimization_type for opt in ["select_star", "join", "where", "index", "aggregation"])
            )
            if has_real_changes or result.expected_improvement > 0:
                print(f"✅ Actually optimizes queries (Type: {result.optimization_type}, Improvement: {result.expected_improvement:.1f}%)")
                results["real"].append("Query optimization")
            elif "/*" in result.optimized_query and "*/" in result.optimized_query:
                print("⚠️  Only adds comments, doesn't really optimize")
                results["partial"].append("Query optimization")
            else:
                print("✅ Actually optimizes queries")
                results["real"].append("Query optimization")
        else:
            print("❌ No real optimization")
            results["fake"].append("Query optimization")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["fake"].append("Database agent")

    # TEST 4: Git Agent
    print("\n4. GIT AGENT")
    try:
        import tempfile
        import subprocess
        from src.ai_employee.git_agent import GitAgent

        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup real git repo
            subprocess.run(["git", "init"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmpdir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, capture_output=True)

            # Create file
            with open(f"{tmpdir}/test.txt", "w") as f:
                f.write("test content")

            agent = GitAgent(tmpdir)
            commit = await agent.commit_changes(files=["test.txt"])

            if commit.sha:
                print("✅ Creates real git commits")
                results["real"].append("Git commits")
            else:
                print("❌ Fake commits")
                results["fake"].append("Git commits")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["fake"].append("Git agent")

    # TEST 5: Cloud Deployment
    print("\n5. CLOUD DEPLOYMENT AGENT")
    try:
        from src.ai_employee.cloud_deployment_agent import CloudDeploymentAgent, CloudResource
        agent = CloudDeploymentAgent()

        # Add resources with different utilizations
        for i in range(3):
            resource = CloudResource(
                f"test-{i}", "ec2", "aws", "us-east-1", "running",
                0.10 * (i + 1), {"instance_type": "t2.large"}
            )
            agent.deployed_resources[f"test-{i}"] = resource

        # Test optimization
        opts = await agent.optimize_costs()

        # Check if optimizations are based on real metrics
        print(f"   Optimizations found: {len(opts['optimizations'])}")
        print(f"   Total savings: ${opts['total_savings']:.2f}")

        # Verify the optimizations are based on actual analysis
        has_real_optimization = False
        for opt in opts['optimizations']:
            if opt['type'] in ['downscale', 'use_spot', 'delete_unused'] and opt.get('estimated_savings', 0) > 0:
                has_real_optimization = True
                break

        if has_real_optimization and opts['total_savings'] > 0:
            print("✅ Returns real cost optimizations based on metrics")
            results["real"].append("Cost optimization")
        else:
            print("⚠️  Limited cost optimization analysis")
            results["partial"].append("Cost optimization")

        # Test disaster recovery
        dr = await agent.disaster_recovery({
            "type": "outage", "region": "us-east-1",
            "severity": "critical", "affected_services": ["web"]
        })

        if dr['incident_id'] and dr['steps_completed']:
            print("✅ Has disaster recovery structure")
            results["real"].append("Disaster recovery structure")
        else:
            print("❌ No disaster recovery")
            results["fake"].append("Disaster recovery")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        results["fake"].append("Cloud agent")

    # FINAL REPORT
    print("\n" + "=" * 80)
    print("TRUTH REPORT")
    print("=" * 80)

    print(f"\n✅ REAL FEATURES ({len(results['real'])})")
    for feature in results['real']:
        print(f"   - {feature}")

    print(f"\n⚠️ PARTIAL/SIMULATED ({len(results['partial'])})")
    for feature in results['partial']:
        print(f"   - {feature}")

    print(f"\n❌ FAKE/BROKEN ({len(results['fake'])})")
    for feature in results['fake']:
        print(f"   - {feature}")

    # Calculate honesty score
    total = len(results['real']) + len(results['partial']) + len(results['fake'])
    real_percentage = (len(results['real']) / total * 100) if total > 0 else 0
    partial_percentage = (len(results['partial']) / total * 100) if total > 0 else 0

    print(f"\n📊 HONESTY SCORE:")
    print(f"   Real: {real_percentage:.0f}%")
    print(f"   Partial: {partial_percentage:.0f}%")
    print(f"   Fake: {100 - real_percentage - partial_percentage:.0f}%")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(truth_test())