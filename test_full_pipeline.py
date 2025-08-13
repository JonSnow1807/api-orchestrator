#!/usr/bin/env python3
"""
Test the complete orchestration pipeline including the new Test Generator Agent
Run this after adding test_agent.py to your project
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.orchestrator import APIOrchestrator, AgentType
from src.agents.discovery_agent import DiscoveryAgent
from src.agents.spec_agent import SpecGeneratorAgent
from src.agents.test_agent import TestGeneratorAgent

async def test_full_pipeline():
    """Test the complete orchestration with all three agents"""
    
    print("=" * 60)
    print("🚀 API Orchestrator - Full Pipeline Test")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = APIOrchestrator()
    
    # Register all agents
    print("\n📦 Registering agents...")
    orchestrator.register_agent(AgentType.DISCOVERY, DiscoveryAgent())
    orchestrator.register_agent(AgentType.SPEC_GENERATOR, SpecGeneratorAgent())
    orchestrator.register_agent(AgentType.TEST_GENERATOR, TestGeneratorAgent())
    
    # Run orchestration
    print("\n🔄 Starting orchestration...")
    source_path = "src"  # Scan the src directory
    
    try:
        # Run the full orchestration pipeline
        results = await orchestrator.orchestrate(source_path)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 ORCHESTRATION RESULTS")
        print("=" * 60)
        
        print(f"\n✅ APIs Discovered: {len(results['apis'])}")
        for api in results['apis'][:5]:  # Show first 5
            print(f"   - {api['method']} {api['path']}")
        
        print(f"\n✅ OpenAPI Spec Generated:")
        if 'paths' in results['specs']:
            print(f"   - Paths: {len(results['specs']['paths'])}")
            print(f"   - Schemas: {len(results['specs'].get('components', {}).get('schemas', {}))}")
        
        print(f"\n✅ Tests Generated: {len(results['tests'])}")
        for test in results['tests']:
            print(f"   - {test['framework']}: {test['filename']} ({test['type']})")
        
        # Save results
        print("\n💾 Saving results...")
        
        # Save OpenAPI spec
        spec_file = Path("generated_spec.json")
        with open(spec_file, 'w') as f:
            json.dump(results['specs'], f, indent=2)
        print(f"   ✓ OpenAPI spec saved to: {spec_file}")
        
        # Save generated tests
        test_dir = Path("generated_tests")
        test_dir.mkdir(exist_ok=True)
        
        test_agent = orchestrator.agents[AgentType.TEST_GENERATOR]
        exported = test_agent.export_tests(str(test_dir))
        
        print(f"   ✓ Tests exported to: {test_dir}/")
        for framework, path in exported.items():
            print(f"     - {framework}: {path}")
        
        # Display test statistics
        stats = test_agent.get_test_statistics()
        print(f"\n📈 Test Statistics:")
        print(f"   - Total test files: {stats['total_tests']}")
        print(f"   - Frameworks: {stats['frameworks']}")
        print(f"   - Test types: {stats['test_types']}")
        
        # Check for errors
        if results['errors']:
            print(f"\n⚠️ Errors encountered:")
            for error in results['errors']:
                print(f"   - {error}")
        
        print("\n" + "=" * 60)
        print("✨ Full pipeline test completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during orchestration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_test_generator_standalone():
    """Test the Test Generator Agent independently"""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Test Generator Agent Standalone")
    print("=" * 60)
    
    # Create a sample OpenAPI spec
    sample_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "http://localhost:8000"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "tags": ["Users"],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                },
                "post": {
                    "summary": "Create user",
                    "tags": ["Users"],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "Created"}
                    }
                }
            },
            "/users/{id}": {
                "get": {
                    "summary": "Get user by ID",
                    "tags": ["Users"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                },
                "delete": {
                    "summary": "Delete user",
                    "tags": ["Users"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "204": {"description": "Deleted"}
                    }
                }
            }
        }
    }
    
    # Initialize test generator
    test_generator = TestGeneratorAgent()
    
    # Generate tests with different options
    print("\n📝 Generating comprehensive test suite...")
    
    options = {
        'frameworks': ['pytest', 'postman', 'locust'],
        'include_negative': True,
        'include_edge_cases': True,
        'include_load_tests': True,
        'coverage_target': 100
    }
    
    tests = await test_generator.create_tests(sample_spec, options)
    
    print(f"\n✅ Generated {len(tests)} test files:")
    for test in tests:
        print(f"   - {test['framework']}: {test['filename']}")
        print(f"     Type: {test['type']}")
        print(f"     Size: {len(test['content'])} characters")
    
    # Export tests
    test_dir = Path("sample_generated_tests")
    test_dir.mkdir(exist_ok=True)
    
    for test in tests:
        file_path = test_dir / test['filename']
        file_path.write_text(test['content'])
        print(f"\n   ✓ Saved: {file_path}")
    
    print("\n✨ Standalone test completed!")
    return True

async def main():
    """Main test runner"""
    
    print("\n" + "🎯" * 30)
    print("API ORCHESTRATOR - TEST GENERATOR VERIFICATION")
    print("🎯" * 30)
    
    # Test standalone first
    success = await test_test_generator_standalone()
    
    if success:
        # Then test full pipeline
        success = await test_full_pipeline()
    
    if success:
        print("\n" + "🎉" * 20)
        print("ALL TESTS PASSED! Test Generator Agent is working!")
        print("🎉" * 20)
        
        print("\n📋 Next Steps:")
        print("1. ✅ Test Generator Agent is complete")
        print("2. 🔄 Move to Step 10: Create FastAPI server with WebSocket")
        print("3. 🎨 Then Step 11: Build React UI")
        print("\n💡 The generated tests are in:")
        print("   - generated_tests/      (from full pipeline)")
        print("   - sample_generated_tests/ (from standalone test)")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())
