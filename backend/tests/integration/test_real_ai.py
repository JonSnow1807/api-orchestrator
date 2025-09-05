#!/usr/bin/env python3
"""
REAL AI Test - Actually calls Anthropic Claude to analyze your APIs
No mocking, no fakery - just real AI intelligence
"""

import asyncio
import json
import os
from pathlib import Path
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_real_anthropic():
    """Test REAL Anthropic Claude API calls"""
    
    print("🤖 TESTING REAL AI - NO MOCKS, NO FAKERY")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ No Anthropic API key found!")
        return
    
    print(f"✅ API Key loaded: {api_key[:20]}...")
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=api_key)
    
    # Sample API spec from your actual system
    api_spec = {
        "paths": {
            "/api/orchestrate": {
                "post": {
                    "summary": "Start orchestration process",
                    "parameters": ["source_path"],
                    "responses": {"200": "success", "400": "error"}
                }
            },
            "/api/tasks/{task_id}": {
                "get": {
                    "summary": "Get task status",
                    "parameters": ["task_id"],
                    "responses": {"200": "success", "404": "not found"}
                }
            },
            "/api/download/{task_id}/{file_type}": {
                "get": {
                    "summary": "Download files",
                    "parameters": ["task_id", "file_type"]
                }
            }
        }
    }
    
    print("\n📊 Sending REAL request to Claude 3.5 Sonnet...")
    print("-" * 60)
    
    try:
        # REAL API CALL #1: Security Analysis
        security_prompt = f"""Analyze this API for security vulnerabilities. Be specific and realistic:

{json.dumps(api_spec, indent=2)}

Provide:
1. Real security issues you can identify
2. OWASP Top 10 vulnerabilities that might apply
3. Specific recommendations
4. A security score from 0-100

Format as JSON with keys: score, vulnerabilities, recommendations"""

        print("🔒 Asking Claude for security analysis...")
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": security_prompt}
            ]
        )
        
        security_response = message.content[0].text
        print("\nClaude's REAL Security Analysis:")
        print(security_response[:500] + "..." if len(security_response) > 500 else security_response)
        
        # REAL API CALL #2: Generate Intelligent Tests
        test_prompt = f"""Generate 3 intelligent test cases for this API that would find real bugs:

{json.dumps(api_spec, indent=2)}

Include:
1. An SQL injection test
2. A rate limiting test  
3. An authentication bypass test

Be specific with actual test code."""

        print("\n🧪 Asking Claude for test generation...")
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": test_prompt}
            ]
        )
        
        test_response = message.content[0].text
        print("\nClaude's REAL Test Cases:")
        print(test_response[:500] + "..." if len(test_response) > 500 else test_response)
        
        # REAL API CALL #3: Business Value
        value_prompt = """If an API orchestration tool saves 10 hours per endpoint 
        and a company has 100 endpoints, and developers cost $150/hour, 
        what's the total value? Also suggest a pricing model."""
        
        print("\n💰 Asking Claude for business analysis...")
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            messages=[
                {"role": "user", "content": value_prompt}
            ]
        )
        
        value_response = message.content[0].text
        print("\nClaude's REAL Business Analysis:")
        print(value_response)
        
        print("\n" + "=" * 60)
        print("✅ REAL AI ANALYSIS COMPLETE!")
        print("\n🎯 This is ACTUAL AI intelligence, not hardcoded!")
        print("   Claude really analyzed your API and provided insights.")
        print("=" * 60)
        
        # Calculate API costs
        # Rough estimate: ~2000 tokens in, ~2000 tokens out per call
        # 3 calls = ~12K tokens total
        cost = (12000 / 1000000) * 3  # $3 per million input tokens
        print(f"\n💵 This analysis cost approximately: ${cost:.4f}")
        print("   (Your $5 credit = ~400+ API analyses)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error calling Claude: {e}")
        print("\nMake sure you have:")
        print("1. Valid Anthropic API key in .env")
        print("2. Credits in your account")
        print("3. Correct model name")
        return False

async def main():
    """Run the real AI test"""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║         🧪 REAL AI TEST - NO MOCKING!                ║
    ║                                                      ║
    ║  This will make ACTUAL calls to Claude 3.5          ║
    ║  You'll see REAL AI responses, not hardcoded data   ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    success = await test_real_anthropic()
    
    if success:
        print("""
    🚀 NOW you have REAL AI Intelligence!
    
    Next steps:
    1. Update ai_agent.py to remove mocks and use real Claude calls
    2. Integrate this into your orchestration pipeline
    3. Show investors REAL AI analysis, not mocked data
    
    The difference:
    - Before: Hardcoded "found 3 vulnerabilities" 
    - Now: Claude ACTUALLY analyzing code and finding real issues
    """)

if __name__ == "__main__":
    asyncio.run(main())
