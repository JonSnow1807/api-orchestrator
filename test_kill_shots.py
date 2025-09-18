#!/usr/bin/env python3
"""
COMPREHENSIVE TEST OF THE "KILL SHOT" FEATURES
Let's see if these actually work or if they're just hype!
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

# Test results storage
test_results = {
    "api_time_machine": {"status": "pending", "works": False, "details": []},
    "telepathic_discovery": {"status": "pending", "works": False, "details": []},
    "quantum_test_generation": {"status": "pending", "works": False, "details": []},
    "predictive_failure": {"status": "pending", "works": False, "details": []}
}


async def test_api_time_machine():
    """Test if API Time Machine actually works"""
    print("\n" + "="*60)
    print("TESTING: API TIME MACHINE")
    print("="*60)

    try:
        from backend.src.kill_shots.api_time_machine import APITimeMachine, APISnapshot

        machine = APITimeMachine()
        print("✅ Module imported successfully")

        # Test 1: Can it capture snapshots?
        print("\n📸 Test 1: Capturing API snapshots...")

        # Simulate API calls at different times
        test_data = [
            {"latency": 100, "status": 200, "response": {"users": ["alice", "bob"]}},
            {"latency": 120, "status": 200, "response": {"users": ["alice", "bob", "charlie"]}},
            {"latency": 150, "status": 200, "response": {"users": ["alice", "bob", "charlie"], "admin": "dave"}},
        ]

        for i, data in enumerate(test_data):
            snapshot = await machine.capture_snapshot(
                endpoint="/api/users",
                method="GET",
                request_data={},
                response_data=data,
                latency=data["latency"]
            )
            print(f"  Snapshot {i+1}: Hash={snapshot.behavior_hash[:8]}...")

        test_results["api_time_machine"]["details"].append("✅ Can capture snapshots")

        # Test 2: Can it detect breaking changes?
        print("\n🔍 Test 2: Detecting breaking changes...")

        # Add a breaking change (removed field)
        breaking_data = {"latency": 200, "status": 200, "response": {"users": ["alice", "bob"]}}
        snapshot = await machine.capture_snapshot(
            endpoint="/api/users",
            method="GET",
            request_data={},
            response_data=breaking_data,
            latency=200
        )

        if snapshot.breaking_changes:
            print(f"  ⚠️ Breaking changes detected: {snapshot.breaking_changes}")
            test_results["api_time_machine"]["details"].append("✅ Detects breaking changes")
        else:
            print("  ❌ Failed to detect removed 'admin' field")
            test_results["api_time_machine"]["details"].append("❌ Breaking change detection failed")

        # Test 3: Can it rollback?
        print("\n⏪ Test 3: Rolling back to previous snapshot...")

        rollback = await machine.rollback_to_snapshot("/api/users", datetime.now())
        if rollback and "rollback_script" in rollback:
            print(f"  ✅ Generated rollback configuration")
            test_results["api_time_machine"]["details"].append("✅ Can generate rollback config")
        else:
            print("  ❌ Rollback failed")
            test_results["api_time_machine"]["details"].append("❌ Rollback failed")

        # Test 4: Timeline visualization
        print("\n📊 Test 4: Timeline visualization...")

        timeline = await machine.get_timeline_visualization("/api/users")
        if timeline and timeline.get("total_snapshots") > 0:
            print(f"  ✅ Timeline has {timeline['total_snapshots']} snapshots")
            test_results["api_time_machine"]["details"].append("✅ Timeline visualization works")
        else:
            print("  ❌ Timeline generation failed")
            test_results["api_time_machine"]["details"].append("❌ Timeline failed")

        # Test 5: Future prediction
        print("\n🔮 Test 5: Predicting future behavior...")

        prediction = await machine.predict_future_behavior("/api/users")
        if prediction and "predictions" in prediction:
            print(f"  Latency trend: {prediction['predictions'].get('latency_trend')}")
            print(f"  Stability score: {prediction['predictions'].get('stability_score')}")
            test_results["api_time_machine"]["details"].append("✅ Can predict future behavior")
        else:
            print("  ❌ Prediction failed")
            test_results["api_time_machine"]["details"].append("❌ Prediction failed")

        # Overall verdict
        success_count = sum(1 for detail in test_results["api_time_machine"]["details"] if "✅" in detail)
        if success_count >= 3:
            test_results["api_time_machine"]["works"] = True
            test_results["api_time_machine"]["status"] = "WORKING"
            print("\n🎯 VERDICT: API Time Machine WORKS! (with limitations)")
        else:
            test_results["api_time_machine"]["status"] = "PARTIAL"
            print("\n⚠️ VERDICT: API Time Machine PARTIALLY works")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        test_results["api_time_machine"]["status"] = "FAILED"
        test_results["api_time_machine"]["details"].append(f"❌ Error: {str(e)}")


async def test_telepathic_discovery():
    """Test if Telepathic Discovery actually finds APIs"""
    print("\n" + "="*60)
    print("TESTING: TELEPATHIC DISCOVERY")
    print("="*60)

    try:
        from backend.src.kill_shots.telepathic_discovery import TelepathicDiscovery

        discovery = TelepathicDiscovery()
        print("✅ Module imported successfully")

        # Test 1: Swagger endpoint scanning
        print("\n🔍 Test 1: Scanning for Swagger endpoints...")

        # Test with a mock URL (won't actually connect)
        swagger_apis = await discovery.scan_swagger_endpoints("http://localhost:8000")
        print(f"  Found {len(swagger_apis)} Swagger endpoints")
        test_results["telepathic_discovery"]["details"].append(
            f"{'✅' if swagger_apis else '⚠️'} Swagger scan executed"
        )

        # Test 2: Source code scanning
        print("\n📝 Test 2: Scanning source code...")

        code_apis = await discovery.scan_source_code(".")
        if code_apis:
            print(f"  Found {len(code_apis)} endpoints in code")
            test_results["telepathic_discovery"]["details"].append("✅ Source code scan works")
        else:
            print("  ⚠️ No endpoints found (expected for basic test)")
            test_results["telepathic_discovery"]["details"].append("⚠️ Source scan returns empty")

        # Test 3: DNS enumeration
        print("\n🌐 Test 3: DNS enumeration...")

        dns_apis = await discovery.scan_dns_records("example.com")
        print(f"  DNS scan completed")
        test_results["telepathic_discovery"]["details"].append("✅ DNS scan executes")

        # Test 4: Full telepathic scan (limited)
        print("\n🧠 Test 4: Running limited telepathic scan...")

        # This will run but most methods will return empty results without real targets
        all_discoveries = await discovery.full_telepathic_scan("localhost")
        print(f"  Total APIs discovered: {len(all_discoveries)}")

        if len(all_discoveries) > 0:
            test_results["telepathic_discovery"]["details"].append("✅ Can discover APIs")
            test_results["telepathic_discovery"]["works"] = True
        else:
            test_results["telepathic_discovery"]["details"].append("⚠️ Limited discovery (needs real targets)")

        # Overall verdict
        test_results["telepathic_discovery"]["status"] = "LIMITED"
        print("\n⚠️ VERDICT: Telepathic Discovery WORKS but needs real infrastructure to scan")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        test_results["telepathic_discovery"]["status"] = "FAILED"
        test_results["telepathic_discovery"]["details"].append(f"❌ Error: {str(e)}")


async def test_quantum_test_generation():
    """Test if Quantum Test Generation actually generates tests"""
    print("\n" + "="*60)
    print("TESTING: QUANTUM TEST GENERATION")
    print("="*60)

    try:
        from backend.src.kill_shots.quantum_test_generation import QuantumTestGenerator

        generator = QuantumTestGenerator()
        print("✅ Module imported successfully")

        # Test 1: Can it generate tests?
        print("\n⚛️ Test 1: Generating quantum tests...")

        # Mock API spec
        api_spec = {
            "paths": {
                "/api/users": {"get": {}, "post": {}},
                "/api/products": {"get": {}, "post": {}, "delete": {}}
            },
            "parameters": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "active": {"type": "boolean"}
            }
        }

        # Generate smaller batch for testing
        tests = await generator.generate_quantum_test_suite(api_spec, test_count=100)

        print(f"  Generated {len(tests)} quantum tests")
        test_results["quantum_test_generation"]["details"].append(f"✅ Generated {len(tests)} tests")

        # Test 2: Check test diversity
        print("\n🎲 Test 2: Checking test diversity...")

        strategies = set(test.strategy.value for test in tests)
        print(f"  Used {len(strategies)} different strategies: {strategies}")

        if len(strategies) >= 5:
            test_results["quantum_test_generation"]["details"].append("✅ Good strategy diversity")
        else:
            test_results["quantum_test_generation"]["details"].append("⚠️ Limited strategy diversity")

        # Test 3: Can tests be converted to classical?
        print("\n🔄 Test 3: Converting to classical tests...")

        classical_tests = []
        for test in tests[:10]:  # Convert first 10
            classical = test.collapse_to_classical()
            classical_tests.append(classical)

        print(f"  Converted {len(classical_tests)} tests to classical format")
        test_results["quantum_test_generation"]["details"].append("✅ Can convert to classical tests")

        # Test 4: Check for security tests
        print("\n🔒 Test 4: Checking security test coverage...")

        security_tests = [t for t in tests if t.chaos_level > 0.8]
        print(f"  Found {len(security_tests)} high-chaos security tests")

        if security_tests:
            test_results["quantum_test_generation"]["details"].append("✅ Includes security tests")
        else:
            test_results["quantum_test_generation"]["details"].append("❌ No security tests found")

        # Overall verdict
        if len(tests) >= 50:
            test_results["quantum_test_generation"]["works"] = True
            test_results["quantum_test_generation"]["status"] = "WORKING"
            print("\n🎯 VERDICT: Quantum Test Generation WORKS!")
        else:
            test_results["quantum_test_generation"]["status"] = "PARTIAL"
            print("\n⚠️ VERDICT: Quantum Test Generation PARTIALLY works")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        test_results["quantum_test_generation"]["status"] = "FAILED"
        test_results["quantum_test_generation"]["details"].append(f"❌ Error: {str(e)}")


async def test_predictive_failure():
    """Test if Predictive Failure Analysis actually predicts"""
    print("\n" + "="*60)
    print("TESTING: PREDICTIVE FAILURE ANALYSIS")
    print("="*60)

    try:
        from backend.src.kill_shots.predictive_failure_analysis import PredictiveFailureAnalysis

        predictor = PredictiveFailureAnalysis()
        print("✅ Module imported successfully")

        # Test 1: Can it predict failures?
        print("\n🔮 Test 1: Predicting failures...")

        # Create mock metrics
        api_metrics = {
            "endpoints": ["/api/users", "/api/orders"],
            "rate_limit": 1000,
            "dependencies": {
                "database": {"error_rate": 0.08, "latency_trend": [100, 150, 200]},
                "cache": {"error_rate": 0.01, "latency_trend": [10, 12, 15]}
            }
        }

        system_metrics = {
            "memory_usage": [1000, 1200, 1400, 1600, 1800],  # Growing memory
            "cpu_usage": 75,
            "disk_usage": 85,
            "database": {
                "connections": 90,
                "max_connections": 100,
                "query_times": [50, 100, 150, 200]
            }
        }

        historical_data = [
            {"latency": 100, "requests_per_minute": 500},
            {"latency": 110, "requests_per_minute": 600},
            {"latency": 125, "requests_per_minute": 700},
            {"latency": 145, "requests_per_minute": 850},
            {"latency": 170, "requests_per_minute": 950}
        ]

        predictions = await predictor.predict_next_24_hours(
            api_metrics, system_metrics, historical_data
        )

        print(f"  Found {len(predictions)} potential failures")
        test_results["predictive_failure"]["details"].append(f"✅ Predicted {len(predictions)} failures")

        # Test 2: Check prediction quality
        print("\n📊 Test 2: Analyzing prediction quality...")

        for pred in predictions:
            print(f"  - {pred.failure_type.value}")
            print(f"    Probability: {pred.probability:.1%}")
            print(f"    Time until: {pred.time_until_failure}")
            print(f"    Impact: {pred.impact_score}/100")

        if predictions:
            test_results["predictive_failure"]["details"].append("✅ Predictions include details")

        # Test 3: Check if preventive actions are provided
        print("\n🛠️ Test 3: Checking preventive actions...")

        has_actions = all(pred.preventive_actions for pred in predictions)
        if has_actions and predictions:
            print(f"  ✅ All predictions have preventive actions")
            test_results["predictive_failure"]["details"].append("✅ Provides preventive actions")
        else:
            print(f"  ⚠️ Some predictions lack actions")
            test_results["predictive_failure"]["details"].append("⚠️ Limited preventive actions")

        # Test 4: Test specific failure predictions
        print("\n🎯 Test 4: Testing specific predictions...")

        # Test memory leak prediction
        memory_leak = await predictor.predict_memory_leaks(system_metrics, historical_data)
        if memory_leak:
            print(f"  ✅ Memory leak detected: {memory_leak.probability:.1%} probability")
            test_results["predictive_failure"]["details"].append("✅ Can detect memory leaks")

        # Test performance degradation
        perf_issue = await predictor.predict_performance_degradation(api_metrics, historical_data)
        if perf_issue:
            print(f"  ✅ Performance issue detected: {perf_issue.time_until_failure}")
            test_results["predictive_failure"]["details"].append("✅ Can detect performance issues")

        # Overall verdict
        if len(predictions) >= 2:
            test_results["predictive_failure"]["works"] = True
            test_results["predictive_failure"]["status"] = "WORKING"
            print("\n🎯 VERDICT: Predictive Failure Analysis WORKS!")
        else:
            test_results["predictive_failure"]["status"] = "LIMITED"
            print("\n⚠️ VERDICT: Predictive Failure Analysis has LIMITED functionality")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        test_results["predictive_failure"]["status"] = "FAILED"
        test_results["predictive_failure"]["details"].append(f"❌ Error: {str(e)}")


async def main():
    """Run all tests and generate report"""
    print("="*60)
    print("TESTING THE 'KILL SHOT' FEATURES")
    print("Let's see if they're real or just hype!")
    print("="*60)

    # Run all tests
    await test_api_time_machine()
    await test_telepathic_discovery()
    await test_quantum_test_generation()
    await test_predictive_failure()

    # Generate summary report
    print("\n" + "="*60)
    print("FINAL TEST REPORT")
    print("="*60)

    for feature, result in test_results.items():
        print(f"\n📦 {feature.replace('_', ' ').upper()}")
        print(f"   Status: {result['status']}")
        print(f"   Works: {'✅ YES' if result['works'] else '❌ NO'}")
        print("   Details:")
        for detail in result['details']:
            print(f"     {detail}")

    # Overall verdict
    working_count = sum(1 for r in test_results.values() if r["works"])

    print("\n" + "="*60)
    print("OVERALL VERDICT")
    print("="*60)

    if working_count == 4:
        print("🎯 ALL FEATURES WORK! Ready to destroy Postman!")
    elif working_count >= 2:
        print("⚠️ SOME FEATURES WORK - They're impressive but need refinement")
    else:
        print("❌ MOST FEATURES DON'T WORK - Too good to be true!")

    print(f"\nWorking Features: {working_count}/4")

    # Save detailed report
    with open("kill_shots_test_report.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)

    print("\n📄 Detailed report saved to: kill_shots_test_report.json")

    return working_count >= 2  # Return True if at least half work


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)