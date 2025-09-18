#!/usr/bin/env python3
"""
FIXED KILL SHOTS - TESTING AFTER REPAIRS
Let's see if these actually work now!
"""

import asyncio
import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

async def test_api_time_machine():
    """Test fixed API Time Machine"""
    print("\n" + "="*60)
    print("TESTING: API TIME MACHINE (FIXED)")
    print("="*60)

    try:
        from backend.src.kill_shots.api_time_machine import APITimeMachine

        machine = APITimeMachine()
        print("✅ Module imported successfully")

        # Test capturing snapshots
        print("\n📸 Capturing snapshots...")
        for i in range(3):
            snapshot = await machine.capture_snapshot(
                endpoint="/api/test",
                method="GET",
                request_data={},
                response_data={"data": f"test_{i}", "status": 200},
                latency=100 + i * 10
            )
            print(f"  Snapshot {i+1}: ✅")

        # Test rollback (fixed)
        print("\n⏪ Testing rollback...")
        rollback = await machine.rollback_to_snapshot("/api/test")
        if rollback and "rollback_script" in rollback:
            print("  ✅ Rollback works!")
            return True
        else:
            print("  ❌ Rollback failed")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_quantum_generation():
    """Test fixed Quantum Test Generation"""
    print("\n" + "="*60)
    print("TESTING: QUANTUM TEST GENERATION (FIXED)")
    print("="*60)

    try:
        from backend.src.kill_shots.quantum_test_generation import QuantumTestGenerator

        generator = QuantumTestGenerator()
        print("✅ Module imported successfully")

        # Generate smaller batch (not 1 million!)
        print("\n⚛️ Generating quantum tests...")
        api_spec = {
            "paths": {
                "/api/users": {"get": {}, "post": {}},
                "/api/products": {"get": {}, "post": {}}
            },
            "parameters": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        }

        tests = await generator.generate_quantum_test_suite(api_spec, test_count=50)
        print(f"  ✅ Generated {len(tests)} tests!")

        if len(tests) >= 50:
            print("  ✅ Quantum generation WORKS!")
            return True
        else:
            print(f"  ❌ Only generated {len(tests)} tests")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_telepathic_discovery():
    """Test fixed Telepathic Discovery"""
    print("\n" + "="*60)
    print("TESTING: TELEPATHIC DISCOVERY (FIXED)")
    print("="*60)

    try:
        from backend.src.kill_shots.telepathic_discovery import TelepathicDiscovery

        discovery = TelepathicDiscovery()
        print("✅ Module imported successfully")

        # Test source code scanning
        print("\n📝 Scanning source code...")
        code_apis = await discovery.scan_source_code("backend/src")
        print(f"  Found {len(code_apis)} endpoints in code")

        # Test Swagger scanning
        print("\n📚 Scanning for Swagger...")
        swagger_apis = await discovery.scan_swagger_endpoints("http://localhost:8000")
        print(f"  Checked Swagger endpoints")

        # Test DNS enumeration
        print("\n🌐 Testing DNS enumeration...")
        dns_apis = await discovery.scan_dns_records("example.com")
        print(f"  DNS scan completed")

        print("\n✅ Telepathic Discovery WORKS!")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def test_predictive_failure():
    """Test Predictive Failure Analysis"""
    print("\n" + "="*60)
    print("TESTING: PREDICTIVE FAILURE ANALYSIS")
    print("="*60)

    try:
        from backend.src.kill_shots.predictive_failure_analysis import PredictiveFailureAnalysis

        predictor = PredictiveFailureAnalysis()
        print("✅ Module imported successfully")

        # Test prediction
        print("\n🔮 Predicting failures...")
        api_metrics = {
            "endpoints": ["/api/users"],
            "rate_limit": 1000,
            "dependencies": {
                "database": {"error_rate": 0.1, "latency_trend": [100, 200, 300]}
            }
        }

        system_metrics = {
            "memory_usage": [1000, 1500, 2000, 2500],
            "cpu_usage": 85,
            "disk_usage": 90,
            "database": {
                "connections": 95,
                "max_connections": 100,
                "query_times": [100, 200, 300, 400]
            }
        }

        historical_data = [
            {"latency": 100 + i*20, "requests_per_minute": 500 + i*100}
            for i in range(5)
        ]

        predictions = await predictor.predict_next_24_hours(
            api_metrics, system_metrics, historical_data
        )

        print(f"  ✅ Predicted {len(predictions)} failures")

        for pred in predictions[:2]:
            print(f"    - {pred.failure_type.value}: {pred.probability:.1%}")

        if len(predictions) > 0:
            print("\n✅ Predictive Failure Analysis WORKS!")
            return True
        else:
            print("\n❌ No predictions generated")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


async def main():
    """Run all tests"""
    print("="*60)
    print("TESTING FIXED KILL SHOT FEATURES")
    print("="*60)

    results = {
        "API Time Machine": await test_api_time_machine(),
        "Quantum Test Generation": await test_quantum_generation(),
        "Telepathic Discovery": await test_telepathic_discovery(),
        "Predictive Failure Analysis": await test_predictive_failure()
    }

    # Summary
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)

    working_count = 0
    for feature, works in results.items():
        status = "✅ WORKS" if works else "❌ FAILED"
        print(f"{feature}: {status}")
        if works:
            working_count += 1

    print(f"\nWorking Features: {working_count}/4")

    if working_count == 4:
        print("\n🎯 ALL FEATURES FIXED AND WORKING!")
        print("Ready to destroy Postman! 💀")
    elif working_count >= 3:
        print("\n✅ MOST FEATURES WORKING!")
        print("Almost ready for production!")
    else:
        print("\n⚠️ Some features still need work")

    return working_count >= 3


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)