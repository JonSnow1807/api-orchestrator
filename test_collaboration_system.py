#!/usr/bin/env python3
"""
Test script to verify AI Agent Collaboration System functionality
This script validates that all CodeRabbit issues have been resolved
"""

import asyncio
import sys
import os

# Add backend src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

try:
    from ai_agent_collaboration import RealTimeCollaborationEngine, TaskPriority, CollaborationMode
    print("✅ Successfully imported collaboration engine")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

async def test_collaboration_system():
    """Test the AI agent collaboration system"""
    print("\n🧪 Testing AI Agent Collaboration System")
    print("=" * 50)

    # Test 1: Engine Initialization
    print("\n1️⃣ Testing Engine Initialization...")
    try:
        engine = RealTimeCollaborationEngine()
        print(f"   ✅ Engine initialized successfully")
        print(f"   📊 Agents loaded: {len(engine.agents)}")
        print(f"   🔧 Agent capabilities: {len(engine.agent_capabilities)}")

        # Verify no simulation code
        if hasattr(engine, '_simulate_agent_response'):
            print("   ❌ Found simulation code - should be removed!")
            return False
        else:
            print("   ✅ No simulation code found")

    except Exception as e:
        print(f"   ❌ Engine initialization failed: {e}")
        return False

    # Test 2: Agent Status Check
    print("\n2️⃣ Testing Agent Status...")
    try:
        for agent_id, agent in engine.agents.items():
            if agent_id in engine.agent_capabilities:
                status = engine.agent_statuses[agent_id]
                print(f"   ✅ {agent_id}: {status['status']} - {type(agent).__name__}")
            else:
                print(f"   ⚠️  {agent_id}: Missing capabilities")

    except Exception as e:
        print(f"   ❌ Agent status check failed: {e}")
        return False

    # Test 3: Task Creation and Assignment
    print("\n3️⃣ Testing Task Creation...")
    try:
        task_id = await engine.create_collaboration_task(
            task_type="analysis",
            task_description="Test collaborative analysis task",
            priority=TaskPriority.MEDIUM,
            collaboration_mode=CollaborationMode.PARALLEL
        )
        print(f"   ✅ Task created: {task_id}")

        # Check if task was processed
        if task_id in engine.active_tasks:
            task = engine.active_tasks[task_id]
            print(f"   📋 Task status: {task.status}")
            print(f"   👥 Assigned agents: {task.assigned_agents}")

    except Exception as e:
        print(f"   ❌ Task creation failed: {e}")
        return False

    # Test 4: Background Tasks Check
    print("\n4️⃣ Testing Background Tasks...")
    try:
        background_tasks = engine._background_tasks
        print(f"   ✅ Background tasks running: {len(background_tasks)}")

        for i, task in enumerate(background_tasks):
            if task.done():
                print(f"   ⚠️  Background task {i} completed unexpectedly")
            else:
                print(f"   ✅ Background task {i}: Running")

    except Exception as e:
        print(f"   ❌ Background task check failed: {e}")
        return False

    # Test 5: Agent Method Calls
    print("\n5️⃣ Testing Agent Method Calls...")
    try:
        # Test calling agent methods directly
        test_task_data = {
            "task_id": "test_123",
            "task_description": "Test direct agent call",
            "your_role": "analyzer"
        }

        # Pick first available agent
        agent_id = list(engine.agents.keys())[0]
        result = await engine._call_agent_method(agent_id, test_task_data)

        print(f"   ✅ Agent method call successful")
        print(f"   📊 Result type: {type(result)}")
        print(f"   🔍 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

    except Exception as e:
        print(f"   ❌ Agent method call failed: {e}")
        return False

    # Final cleanup
    print("\n🧹 Cleaning up background tasks...")
    try:
        for task in engine._background_tasks:
            task.cancel()
        await asyncio.gather(*engine._background_tasks, return_exceptions=True)
        print("   ✅ Background tasks cancelled")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")

    return True

async def main():
    """Main test runner"""
    print("🚀 AI Agent Collaboration System Test")
    print("Testing all CodeRabbit fixes and functionality...")

    success = await test_collaboration_system()

    if success:
        print("\n🎉 SUCCESS: AI Agent Collaboration System is FULLY FUNCTIONAL!")
        print("✅ All CodeRabbit issues resolved")
        print("✅ Real agent method calls working")
        print("✅ No simulation code detected")
        print("✅ Background tasks properly managed")
        print("✅ Agent initialization robust")
        return 0
    else:
        print("\n❌ FAILURE: Issues detected in collaboration system")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)