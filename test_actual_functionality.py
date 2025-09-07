#!/usr/bin/env python3
"""
ACTUAL functionality test - verify the core features really work
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import tempfile
from pathlib import Path

# Test Discovery Agent directly
async def test_discovery_agent():
    """Test if Discovery Agent actually finds APIs"""
    print("\n🔍 Testing Discovery Agent...")
    
    from backend.src.agents.discovery_agent import DiscoveryAgent
    
    agent = DiscoveryAgent()
    
    # Create a test file with API code
    test_code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    return []

@app.post("/users")
def create_user():
    return {}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {}
'''
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_path = f.name
    
    try:
        # Scan the file
        apis = await agent.scan(temp_path)
        
        if apis and len(apis) > 0:
            print(f"✅ Found {len(apis)} endpoints:")
            for api in apis:
                print(f"   • {api.method} {api.path}")
            return True
        else:
            print("❌ No endpoints found!")
            return False
    finally:
        os.unlink(temp_path)

# Test Spec Generator directly
async def test_spec_generator():
    """Test if Spec Generator creates valid OpenAPI"""
    print("\n📝 Testing Spec Generator...")
    
    from backend.src.agents.spec_agent import SpecGeneratorAgent
    from backend.src.core.orchestrator import APIEndpoint
    
    agent = SpecGeneratorAgent()
    
    # Create test endpoints
    test_apis = [
        APIEndpoint(
            path="/users",
            method="GET",
            handler_name="get_users",
            parameters=[],
            description="Get all users"
        ),
        APIEndpoint(
            path="/users/{user_id}",
            method="GET",
            handler_name="get_user",
            parameters=[{"name": "user_id", "type": "integer", "in": "path"}],
            description="Get user by ID"
        ),
        APIEndpoint(
            path="/users",
            method="POST",
            handler_name="create_user",
            parameters=[],
            description="Create new user"
        )
    ]
    
    spec = await agent.generate(test_apis)
    
    if spec and 'paths' in spec and len(spec['paths']) > 0:
        print(f"✅ Generated OpenAPI spec with {len(spec['paths'])} paths")
        print(f"   • OpenAPI version: {spec.get('openapi', 'N/A')}")
        print(f"   • Title: {spec.get('info', {}).get('title', 'N/A')}")
        for path in spec['paths']:
            print(f"   • Path: {path}")
        return True
    else:
        print("❌ Failed to generate valid spec!")
        return False

# Test Test Generator directly
async def test_test_generator():
    """Test if Test Generator creates actual tests"""
    print("\n🧪 Testing Test Generator...")
    
    from backend.src.agents.test_agent import TestGeneratorAgent
    
    agent = TestGeneratorAgent()
    
    # Create a simple spec
    test_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "responses": {"200": {"description": "Success"}}
                },
                "post": {
                    "summary": "Create user",
                    "responses": {"201": {"description": "Created"}}
                }
            }
        }
    }
    
    tests = await agent.create_tests(test_spec)
    
    if tests and len(tests) > 0:
        print(f"✅ Generated {len(tests)} test files:")
        for test in tests:
            print(f"   • {test.get('framework')}: {test.get('filename')}")
            # Check if content is not empty
            if test.get('content', '').strip():
                print(f"     ✓ Has content ({len(test['content'])} chars)")
            else:
                print(f"     ✗ Empty content!")
        return True
    else:
        print("❌ No tests generated!")
        return False

# Test Mock Server Generator
async def test_mock_server():
    """Test if Mock Server actually creates files"""
    print("\n🎭 Testing Mock Server Generator...")
    
    from backend.src.agents.mock_server_agent import MockServerAgent
    
    agent = MockServerAgent()
    
    # Create a simple spec
    test_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "servers": [{"url": "http://localhost:8000"}],
        "paths": {
            "/items": {
                "get": {"summary": "Get items"},
                "post": {"summary": "Create item"}
            },
            "/items/{item_id}": {
                "get": {"summary": "Get item by ID"},
                "delete": {"summary": "Delete item"}
            }
        }
    }
    
    result = await agent.generate(test_spec)
    
    if result and result.get('status') == 'created':
        print(f"✅ Mock server created:")
        print(f"   • URL: {result.get('mock_server_url')}")
        print(f"   • Directory: {result.get('mock_server_dir')}")
        
        # Check if files were actually created
        mock_dir = Path(result.get('mock_server_dir', ''))
        if mock_dir.exists():
            files = list(mock_dir.glob('*'))
            print(f"   • Files created: {len(files)}")
            for file in files:
                print(f"     - {file.name}")
            return True
        else:
            print("   ❌ Directory doesn't exist!")
            return False
    else:
        print("❌ Mock server creation failed!")
        return False

# Test AI Agent
async def test_ai_agent():
    """Test if AI Agent produces analysis"""
    print("\n🤖 Testing AI Intelligence Agent...")
    
    from backend.src.agents.ai_agent import AIIntelligenceAgent
    from backend.src.core.orchestrator import APIEndpoint
    
    agent = AIIntelligenceAgent()
    
    test_apis = [
        APIEndpoint(path="/users", method="GET", handler_name="get_users", parameters=[]),
        APIEndpoint(path="/users", method="POST", handler_name="create_user", parameters=[]),
    ]
    
    test_spec = {
        "paths": {
            "/users": {
                "get": {"summary": "Get users"},
                "post": {"summary": "Create user"}
            }
        }
    }
    
    analysis = await agent.analyze(test_apis, test_spec)
    
    if analysis:
        print(f"✅ AI Analysis completed:")
        print(f"   • Security Score: {analysis.get('security_score', 'N/A')}/100")
        print(f"   • Vulnerabilities: {len(analysis.get('vulnerabilities', []))}")
        print(f"   • Optimizations: {len(analysis.get('optimizations', []))}")
        print(f"   • Business Value: {analysis.get('business_value', {}).get('cost_savings', 'N/A')}")
        return True
    else:
        print("❌ AI analysis failed!")
        return False

# Test the complete orchestration flow
async def test_orchestration():
    """Test the complete orchestration pipeline"""
    print("\n🔄 Testing Complete Orchestration...")
    
    from backend.src.core.orchestrator import APIOrchestrator, AgentType
    from backend.src.agents.discovery_agent import DiscoveryAgent
    from backend.src.agents.spec_agent import SpecGeneratorAgent
    from backend.src.agents.test_agent import TestGeneratorAgent
    from backend.src.agents.ai_agent import AIIntelligenceAgent
    from backend.src.agents.mock_server_agent import MockServerAgent
    
    orchestrator = APIOrchestrator()
    
    # Register all agents
    orchestrator.register_agent(AgentType.DISCOVERY, DiscoveryAgent())
    orchestrator.register_agent(AgentType.SPEC_GENERATOR, SpecGeneratorAgent())
    orchestrator.register_agent(AgentType.TEST_GENERATOR, TestGeneratorAgent())
    orchestrator.register_agent(AgentType.AI_INTELLIGENCE, AIIntelligenceAgent())
    orchestrator.register_agent(AgentType.MOCK_SERVER, MockServerAgent())
    
    # Create test file
    test_code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/test")
def test_endpoint():
    return {"message": "test"}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_path = f.name
    
    try:
        result = await orchestrator.orchestrate(temp_path)
        
        if result:
            print(f"✅ Orchestration completed:")
            print(f"   • APIs found: {len(result.get('apis', []))}")
            print(f"   • Spec paths: {len(result.get('specs', {}).get('paths', {}))}")
            print(f"   • Tests generated: {len(result.get('tests', []))}")
            print(f"   • Errors: {len(result.get('errors', []))}")
            
            if result.get('errors'):
                print("   ⚠️ Errors encountered:")
                for error in result['errors']:
                    print(f"      - {error}")
            
            return len(result.get('apis', [])) > 0
        else:
            print("❌ Orchestration returned no results!")
            return False
    finally:
        os.unlink(temp_path)

async def run_all_tests():
    """Run all tests"""
    print("="*70)
    print("🔬 RUNNING ACTUAL FUNCTIONALITY TESTS")
    print("="*70)
    
    results = {}
    
    # Test each component
    results['discovery'] = await test_discovery_agent()
    results['spec'] = await test_spec_generator()
    results['tests'] = await test_test_generator()
    results['mock'] = await test_mock_server()
    results['ai'] = await test_ai_agent()
    results['orchestration'] = await test_orchestration()
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST RESULTS SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for component, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {component.capitalize()}: {'PASSED' if status else 'FAILED'}")
    
    print(f"\n📈 Score: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! The system is fully functional!")
    elif passed >= total * 0.8:
        print("\n✅ Most features working, but some issues remain.")
    elif passed >= total * 0.5:
        print("\n⚠️ Partially functional - significant issues need fixing.")
    else:
        print("\n❌ Major functionality issues - most features not working!")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)