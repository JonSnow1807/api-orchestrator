#!/usr/bin/env python3
"""
Anonymity Verification Test - Check what data is actually sent to LLM providers
"""

import asyncio
import json
from backend.src.llm_decision_engine import LLMDecisionEngine, DecisionContext, DecisionType

class LLMDataInterceptor:
    """Intercept LLM calls to verify what data is actually being sent"""

    def __init__(self):
        self.intercepted_prompts = []
        self.intercepted_data = []

    async def mock_anthropic_call(self, model, max_tokens, messages):
        """Mock Anthropic API call to capture data"""
        prompt_content = messages[0]['content']
        self.intercepted_prompts.append(prompt_content)

        # Extract all data being sent
        data_sent = {
            'model': model,
            'max_tokens': max_tokens,
            'prompt': prompt_content
        }
        self.intercepted_data.append(data_sent)

        # Return mock response
        class MockResponse:
            def __init__(self):
                self.content = [MockContent()]

        class MockContent:
            def __init__(self):
                self.text = '{"reasoning": "mock", "confidence_score": 0.8, "risk_assessment": "safe", "requires_approval": false, "compliance_notes": "mock", "actions": []}'

        return MockResponse()

async def test_anonymity_claims():
    """Test what data is actually being sent to LLM providers"""
    print("🔍 ANONYMITY VERIFICATION TEST")
    print("=" * 70)

    # Create interceptor
    interceptor = LLMDataInterceptor()

    # Read API keys from backend .env file
    import os

    # Read the .env file directly
    env_file = 'backend/.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('ANTHROPIC_API_KEY='):
                    anthropic_key = line.split('=', 1)[1].strip()
                    os.environ['ANTHROPIC_API_KEY'] = anthropic_key
                elif line.startswith('OPENAI_API_KEY='):
                    openai_key = line.split('=', 1)[1].strip()
                    os.environ['OPENAI_API_KEY'] = openai_key

    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    print(f"📊 Configuration Check:")
    print(f"   🔑 Anthropic API Key: {'✅ Present' if anthropic_key and len(anthropic_key) > 10 else '❌ Missing'}")
    print(f"   🔑 OpenAI API Key: {'✅ Present' if openai_key and len(openai_key) > 10 else '❌ Missing'}")

    # Test with realistic user data
    test_context = DecisionContext(
        user_id="user_john_doe_12345",  # Real user ID
        project_id="my_company_secret_project",  # Real project ID
        endpoint_data={
            "path": "/api/v1/users/{user_id}/personal-data",  # Sensitive endpoint
            "method": "GET",
            "parameters": [
                {"name": "user_id", "in": "path", "required": True},
                {"name": "include_ssn", "in": "query", "required": False},
                {"name": "include_medical_records", "in": "query", "required": False}
            ],
            "security": ["jwt_token", "api_key"],
            "headers": {
                "X-Company-Internal": "CONFIDENTIAL",
                "X-User-Role": "admin"
            }
        },
        historical_data=[
            {"previous_vulnerability": "SQL injection found in user table"},
            {"compliance_violation": "HIPAA violation - medical data exposed"}
        ],
        user_preferences={
            "company_name": "Acme Corporation",
            "user_email": "john.doe@acme.com",
            "auto_fix_enabled": True
        },
        available_tools=["security_vulnerability_scan", "compliance_check"],
        current_findings={
            "sensitive_data_found": ["SSN", "medical_records", "payment_info"],
            "security_issues": ["weak_authentication", "data_exposure"]
        },
        business_context="Healthcare startup processing patient medical records and payment data with HIPAA compliance requirements in California office with 50 employees handling sensitive patient information"
    )

    engine = LLMDecisionEngine()

    # Force enable LLM if API key is available
    if anthropic_key and len(anthropic_key) > 10:
        import anthropic
        engine.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        engine.llm_available = True
        print("   ✅ Forced Anthropic LLM enabled for testing")

        # Mock the call AFTER setting up the client
        original_create = engine.anthropic_client.messages.create
        engine.anthropic_client.messages.create = interceptor.mock_anthropic_call
    else:
        # If no LLM available, directly test prompt generation
        print("   ⚠️  No LLM available - testing prompt generation directly")

        # Create a direct test of what would be sent
        test_prompt = engine._build_decision_prompt(test_context, DecisionType.ANALYSIS_PLAN)
        interceptor.intercepted_prompts.append(test_prompt)
        print("   📝 Direct prompt generation captured")

    try:
        # Make LLM call
        print("📡 Making LLM call with sensitive test data...")
        plan = await engine.create_decision_plan(test_context, DecisionType.ANALYSIS_PLAN)

        # Analyze what was sent
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   📝 Total prompts sent: {len(interceptor.intercepted_prompts)}")

        if interceptor.intercepted_prompts:
            prompt = interceptor.intercepted_prompts[0]

            # Check for sensitive data in prompt
            sensitive_indicators = {
                "User ID": "user_john_doe_12345" in prompt,
                "Project ID": "my_company_secret_project" in prompt,
                "Company Name": "Acme Corporation" in prompt,
                "User Email": "john.doe@acme.com" in prompt,
                "Endpoint Path": "/api/v1/users/{user_id}/personal-data" in prompt,
                "SSN Reference": "ssn" in prompt.lower(),
                "Medical Records": "medical_records" in prompt.lower(),
                "Internal Headers": "X-Company-Internal" in prompt,
                "CONFIDENTIAL": "CONFIDENTIAL" in prompt,
                "Historical Vulnerabilities": "SQL injection found in user table" in prompt,
                "HIPAA Violation Details": "HIPAA violation - medical data exposed" in prompt,
                "Business Context": "Healthcare startup" in prompt,
                "Employee Count": "50 employees" in prompt,
                "Office Location": "California office" in prompt
            }

            print(f"\n🚨 SENSITIVE DATA EXPOSURE CHECK:")
            exposed_count = 0
            for indicator, found in sensitive_indicators.items():
                status = "🔴 EXPOSED" if found else "✅ PROTECTED"
                print(f"   {status} {indicator}")
                if found:
                    exposed_count += 1

            print(f"\n📈 PRIVACY SCORE:")
            total_indicators = len(sensitive_indicators)
            protected_count = total_indicators - exposed_count
            privacy_score = (protected_count / total_indicators) * 100

            print(f"   🛡️  Protected: {protected_count}/{total_indicators}")
            print(f"   🚨 Exposed: {exposed_count}/{total_indicators}")
            print(f"   📊 Privacy Score: {privacy_score:.1f}%")

            # Anonymity assessment
            if privacy_score >= 90:
                anonymity_level = "EXCELLENT - Highly Anonymous"
                print(f"   🏆 ANONYMITY LEVEL: {anonymity_level}")
            elif privacy_score >= 70:
                anonymity_level = "GOOD - Mostly Anonymous"
                print(f"   ✅ ANONYMITY LEVEL: {anonymity_level}")
            elif privacy_score >= 50:
                anonymity_level = "POOR - Limited Anonymity"
                print(f"   ⚠️  ANONYMITY LEVEL: {anonymity_level}")
            else:
                anonymity_level = "CRITICAL - No Anonymity"
                print(f"   🔴 ANONYMITY LEVEL: {anonymity_level}")

            # Show actual prompt excerpt (first 500 chars)
            print(f"\n📄 PROMPT EXCERPT (first 500 chars):")
            print(f"   {prompt[:500]}...")

            # Save full prompt for detailed review
            with open('llm_prompt_analysis.txt', 'w') as f:
                f.write("LLM PROMPT ANALYSIS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Privacy Score: {privacy_score:.1f}%\n")
                f.write(f"Anonymity Level: {anonymity_level}\n\n")
                f.write("FULL PROMPT:\n")
                f.write("-" * 30 + "\n")
                f.write(prompt)

            print(f"\n💾 Full prompt saved to: llm_prompt_analysis.txt")

        else:
            print("❌ No prompts intercepted - LLM may not be configured")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

async def main():
    """Run anonymity verification"""
    await test_anonymity_claims()

if __name__ == "__main__":
    asyncio.run(main())