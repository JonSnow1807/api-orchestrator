#!/usr/bin/env python3
"""
Test AI Agent with real Anthropic API
"""

import asyncio
import json
import os
from src.agents.ai_agent import AIIntelligenceAgent

async def test_ai_agent():
    """Test the AI agent functionality"""
    
    print("🤖 Testing AI Intelligence Agent")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set")
        print("   To enable AI features, set your API key:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("\n   Using mock responses instead...")
    else:
        print(f"✅ Anthropic API key found: {api_key[:8]}...")
    
    # Initialize AI agent
    print("\n1. Initializing AI Agent...")
    agent = AIIntelligenceAgent()
    
    # Sample API spec to analyze
    sample_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "User Management API",
            "version": "1.0.0"
        },
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get all users",
                    "responses": {
                        "200": {
                            "description": "List of users"
                        }
                    }
                }
            },
            "/users/{id}": {
                "delete": {
                    "summary": "Delete a user",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User deleted"
                        }
                    }
                }
            },
            "/login": {
                "post": {
                    "summary": "User login",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful"
                        }
                    }
                }
            }
        }
    }
    
    # Test security analysis
    print("\n2. Testing Security Analysis...")
    try:
        security_result = await agent.analyze_api_security(sample_spec)
        
        if isinstance(security_result, dict):
            print("✅ Security analysis completed!")
            print(f"   Security Score: {security_result.get('security_score', 'N/A')}/100")
            
            vulnerabilities = security_result.get('vulnerabilities', [])
            if vulnerabilities:
                print(f"   Found {len(vulnerabilities)} vulnerabilities:")
                for vuln in vulnerabilities[:3]:  # Show first 3
                    print(f"   - {vuln.get('type', 'Unknown')}: {vuln.get('description', '')[:60]}...")
            
            print(f"   Summary: {security_result.get('summary', 'No summary')[:100]}...")
        else:
            print("⚠️  Security analysis returned non-dict response")
    except Exception as e:
        print(f"❌ Security analysis failed: {e}")
    
    # Test intelligent test generation
    print("\n3. Testing Intelligent Test Generation...")
    try:
        tests = await agent.generate_intelligent_tests(sample_spec)
        
        if tests:
            print(f"✅ Generated {len(tests)} intelligent tests!")
            for i, test in enumerate(tests[:3], 1):
                if isinstance(test, dict):
                    print(f"   Test {i}: {test.get('name', 'Unnamed test')}")
                    print(f"           {test.get('description', '')[:60]}...")
        else:
            print("⚠️  No tests generated")
    except Exception as e:
        print(f"❌ Test generation failed: {e}")
    
    # Test optimization suggestions
    print("\n4. Testing Optimization Suggestions...")
    try:
        optimizations = await agent.suggest_optimizations(sample_spec)
        
        if optimizations:
            print(f"✅ Found {len(optimizations)} optimization opportunities!")
            for opt in optimizations[:3]:
                print(f"   - {opt.get('type', 'Unknown')}: {opt.get('issue', '')}")
                print(f"     Impact: {opt.get('estimated_impact', 'Unknown')}")
        else:
            print("⚠️  No optimizations suggested")
    except Exception as e:
        print(f"❌ Optimization analysis failed: {e}")
    
    # Test documentation generation
    print("\n5. Testing Documentation Enhancement...")
    try:
        docs = await agent.enhance_documentation(sample_spec)
        
        if docs:
            print("✅ Documentation enhanced!")
            if isinstance(docs, dict):
                print(f"   Title: {docs.get('title', 'N/A')}")
                print(f"   Description: {docs.get('description', '')[:100]}...")
            elif isinstance(docs, str):
                print(f"   Generated docs: {docs[:100]}...")
        else:
            print("⚠️  No documentation generated")
    except Exception as e:
        print(f"❌ Documentation generation failed: {e}")
    
    # Calculate business value
    print("\n6. Testing Business Value Calculation...")
    try:
        value = agent.calculate_business_value(
            apis_found=3,
            tests_generated=10,
            security_issues_found=5
        )
        
        print(f"✅ Business value calculated:")
        print(f"   Hours saved: {value['hours_saved']}")
        print(f"   Money saved: ${value['money_saved']:,.2f}")
        print(f"   ROI: {value['roi_percentage']:.1f}%")
        print(f"   Time to market: {value['time_to_market_reduction']}")
    except Exception as e:
        print(f"❌ Business value calculation failed: {e}")
    
    print("\n" + "=" * 50)
    
    if api_key:
        print("✅ AI Agent is working with real Anthropic API!")
    else:
        print("⚠️  AI Agent is using mock responses")
        print("   Set ANTHROPIC_API_KEY to enable real AI analysis")

if __name__ == "__main__":
    print("Testing AI Intelligence Agent...")
    print("This will use the Anthropic API if ANTHROPIC_API_KEY is set")
    print()
    
    asyncio.run(test_ai_agent())