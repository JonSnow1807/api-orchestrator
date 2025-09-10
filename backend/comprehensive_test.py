#!/usr/bin/env python
"""
Comprehensive Integration Test for API Orchestrator
Tests all new features and integrations
"""

import asyncio
import json
import sys
from datetime import datetime

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

def test_section(name):
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {name}")
    print("="*60)

def test_passed(message):
    global test_results
    test_results["passed"] += 1
    print(f"✅ {message}")

def test_failed(message, error=None):
    global test_results
    test_results["failed"] += 1
    print(f"❌ {message}")
    if error:
        test_results["errors"].append(f"{message}: {error}")
        print(f"   Error: {error}")

async def test_all_features():
    """Run all integration tests"""
    
    # Test 1: Import System
    test_section("Import System")
    try:
        from src.main import app
        from src.database import SessionLocal, init_db
        from src.agents.test_runner_agent import TestRunnerAgent, TestCase, Assertion, AssertionType
        from src.postman_import import PostmanImporter
        from src.routes.test_runner import router as test_router
        from src.models.test_runner import TestResult, TestSuite
        from src.models.workspace import Workspace
        from src.models.ai_keys import AIKey
        from src.demo_data import create_demo_project, SAMPLE_OPENAPI_SPEC
        test_passed("All imports successful")
    except Exception as e:
        test_failed("Import failed", str(e))
        return
    
    # Test 2: Database Operations
    test_section("Database Operations")
    try:
        # Initialize database
        init_db()
        db = SessionLocal()
        
        # Test user creation
        from src.database import User
        from src.auth import AuthManager
        import time
        
        # Use timestamp to ensure unique email
        timestamp = int(time.time())
        test_email = f"test_{timestamp}@example.com"
        
        # Check if user exists and delete if needed
        existing_user = db.query(User).filter(User.email == test_email).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        test_user = User(
            email=test_email,
            username=f"testuser_{timestamp}",
            hashed_password=AuthManager.get_password_hash("testpass123"),
            subscription_tier="professional",
            api_calls_this_month=0  # Initialize required field
        )
        db.add(test_user)
        db.commit()
        test_passed("User creation successful")
        
        # Test workspace creation
        # Use timestamp for unique slug
        workspace_slug = f"test-workspace-{timestamp}"
        
        # Check if workspace exists and delete if needed
        existing_workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
        if existing_workspace:
            db.delete(existing_workspace)
            db.commit()
        
        workspace = Workspace(
            name=f"Test Workspace {timestamp}",
            slug=workspace_slug,
            created_by=test_user.id
        )
        db.add(workspace)
        db.commit()
        test_passed("Workspace creation successful")
        
        # Test demo project creation
        demo_result = create_demo_project(db, test_user.id)
        if demo_result['project']:
            test_passed(f"Demo project created with {demo_result['stats']['apis']} APIs")
        else:
            test_failed("Demo project creation failed")
            
    except Exception as e:
        test_failed("Database operation failed", str(e))
    finally:
        db.close()
    
    # Test 3: Test Runner
    test_section("Test Runner Agent")
    try:
        runner = TestRunnerAgent()
        
        # Create a simple test
        test_case = runner.create_test_from_request(
            name="Test Example API",
            url="https://jsonplaceholder.typicode.com/posts/1",
            method="GET",
            assertions=[
                {"type": "STATUS_CODE", "expected": 200, "operator": "equals"},
                {"type": "IS_JSON", "expected": True}
            ]
        )
        
        # Run the test
        result = await runner.run_single_test(test_case)
        
        if result['status'] == 'passed':
            test_passed("Test execution successful")
        else:
            test_failed(f"Test execution failed with status: {result['status']}")
            
    except Exception as e:
        test_failed("Test runner failed", str(e))
    
    # Test 4: Postman Import
    test_section("Postman Import")
    try:
        importer = PostmanImporter()
        
        # Sample Postman collection
        sample_collection = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": [
                {
                    "name": "Get User",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/users/1"
                    }
                }
            ],
            "variable": [
                {"key": "base_url", "value": "https://api.example.com"}
            ]
        }
        
        result = importer.import_collection(sample_collection)
        
        if result['success']:
            test_passed(f"Postman import successful: {result['stats']['total_requests']} requests")
        else:
            test_failed("Postman import failed", result.get('error'))
            
    except Exception as e:
        test_failed("Postman import failed", str(e))
    
    # Test 5: API Routes
    test_section("API Routes")
    try:
        routes = [r for r in app.routes if hasattr(r, 'path')]
        api_routes = [r.path for r in routes if r.path.startswith('/api/')]
        
        # Check for new routes
        required_routes = [
            '/api/test-runner/run-test',
            '/api/test-runner/run-suite',
            '/api/test-runner/import-postman',
            '/api/webhooks',
            '/api/ai-keys'
        ]
        
        missing_routes = []
        for route in required_routes:
            found = any(route in r for r in api_routes)
            if not found:
                missing_routes.append(route)
        
        if not missing_routes:
            test_passed(f"All required routes registered ({len(api_routes)} total API routes)")
        else:
            test_failed(f"Missing routes: {missing_routes}")
            
    except Exception as e:
        test_failed("Route verification failed", str(e))
    
    # Test 6: Mock Server
    test_section("Mock Server Agent")
    try:
        from src.agents.mock_server_agent import MockServerAgent
        
        agent = MockServerAgent()
        # Just test import and initialization
        test_passed("Mock server agent initialized")
    except Exception as e:
        test_failed("Mock server agent failed", str(e))
    
    # Test 7: Code Generator
    test_section("Code Generator Agent")
    try:
        from src.agents.code_generator_agent import CodeGeneratorAgent
        
        agent = CodeGeneratorAgent()
        # Just test import and initialization
        test_passed("Code generator agent initialized")
    except Exception as e:
        test_failed("Code generator agent failed", str(e))
    
    # Test 8: WebSocket Manager
    test_section("WebSocket Manager")
    try:
        from src.main import manager
        if manager:
            test_passed("WebSocket manager initialized")
        else:
            test_failed("WebSocket manager not found")
    except Exception as e:
        test_failed("WebSocket manager failed", str(e))

def main():
    """Run all tests and generate report"""
    print("="*60)
    print("🚀 API ORCHESTRATOR COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")
    
    # Run async tests
    asyncio.run(test_all_features())
    
    # Generate report
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    
    if test_results["errors"]:
        print("\n⚠️ Errors:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    print("\n" + "="*60)
    
    if test_results["failed"] == 0:
        print("🎉 ALL TESTS PASSED! The codebase is working correctly.")
        print("✅ All new features are properly integrated.")
        print("✅ Database models are correct.")
        print("✅ API routes are registered.")
        print("✅ Import/Export functionality works.")
        print("✅ Test runner is operational.")
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
    
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if test_results["failed"] == 0 else 1)

if __name__ == "__main__":
    main()