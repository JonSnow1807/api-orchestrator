"""
Comprehensive Beta Testing Framework for Ultra Premium AI Workforce
Tests autonomous agents with realistic enterprise scenarios
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Import our agents for testing
from backend.src.agents.autonomous_security_agent import AutonomousSecurityAgent
from backend.src.llm_decision_engine import DecisionContext, DecisionType

class BetaTestingFramework:
    """
    Comprehensive testing framework for autonomous AI agents
    """

    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.performance_metrics = []
        self.logger = logging.getLogger(__name__)

        # Initialize test data based on web research
        self.test_scenarios = self._create_test_scenarios()

    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create realistic test scenarios based on enterprise requirements"""

        return [
            # Fintech API Scenarios
            {
                "scenario_name": "Payment Processing API - OWASP Critical",
                "industry": "fintech",
                "endpoint_data": {
                    "path": "/api/v1/payments/process",
                    "method": "POST",
                    "parameters": [
                        {"name": "amount", "in": "body", "required": True, "schema": {"type": "number"}},
                        {"name": "card_token", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "user_id", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "api_key", "in": "header", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "transaction_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "card_number": {"type": "string"},  # SECURITY ISSUE: Exposed PII
                                            "cvv": {"type": "string"}  # CRITICAL: CVV exposed
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "security": []  # NO AUTHENTICATION - CRITICAL ISSUE
                },
                "expected_vulnerabilities": [
                    "no_authentication",
                    "sensitive_data_exposure",
                    "missing_rate_limiting",
                    "insufficient_logging"
                ],
                "compliance_requirements": ["PCI-DSS", "GDPR"],
                "risk_tolerance": "LOW"  # Fintech requires high security
            },

            # Healthcare API Scenario
            {
                "scenario_name": "Patient Records API - HIPAA Critical",
                "industry": "healthcare",
                "endpoint_data": {
                    "path": "/api/v1/patients/{patient_id}/medical_records",
                    "method": "GET",
                    "parameters": [
                        {"name": "patient_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "include_sensitive", "in": "query", "required": False, "schema": {"type": "boolean"}}
                    ],
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "patient_name": {"type": "string"},
                                            "ssn": {"type": "string"},  # HIPAA VIOLATION
                                            "diagnosis": {"type": "string"},
                                            "medications": {"type": "array"},
                                            "insurance_info": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "security": [
                        {"type": "bearer", "scheme": "bearer"}  # Basic auth present
                    ]
                },
                "expected_vulnerabilities": [
                    "broken_object_level_authorization",  # OWASP API #1
                    "excessive_data_exposure",  # HIPAA violation
                    "missing_input_validation",
                    "insufficient_audit_logging"
                ],
                "compliance_requirements": ["HIPAA", "GDPR"],
                "risk_tolerance": "CRITICAL"  # Healthcare is zero-tolerance
            },

            # E-commerce API Scenario
            {
                "scenario_name": "E-commerce User Profile API - GDPR Focus",
                "industry": "ecommerce",
                "endpoint_data": {
                    "path": "/api/v1/users/{user_id}/profile",
                    "method": "PUT",
                    "parameters": [
                        {"name": "user_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                        {"name": "email", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "phone", "in": "body", "required": False, "schema": {"type": "string"}},
                        {"name": "address", "in": "body", "required": False, "schema": {"type": "object"}}
                    ],
                    "security": [
                        {"type": "apiKey", "in": "query", "name": "api_key"}  # API key in query - VULNERABILITY
                    ]
                },
                "expected_vulnerabilities": [
                    "broken_authentication",
                    "api_key_in_query_params",  # Logged in access logs
                    "mass_assignment_vulnerability",
                    "missing_rate_limiting"
                ],
                "compliance_requirements": ["GDPR"],
                "risk_tolerance": "MEDIUM"
            },

            # IoT/SaaS API Scenario
            {
                "scenario_name": "IoT Device Management API - Enterprise",
                "industry": "iot",
                "endpoint_data": {
                    "path": "/api/v1/devices/{device_id}/commands",
                    "method": "POST",
                    "parameters": [
                        {"name": "device_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "command", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "parameters", "in": "body", "required": False, "schema": {"type": "object"}}
                    ],
                    "security": [
                        {"type": "oauth2", "flows": {"clientCredentials": {"tokenUrl": "/oauth/token"}}}
                    ]
                },
                "expected_vulnerabilities": [
                    "server_side_request_forgery",  # OWASP API #5
                    "unrestricted_resource_consumption",  # OWASP API #4
                    "insufficient_command_validation",
                    "missing_device_authorization"
                ],
                "compliance_requirements": ["SOC2"],
                "risk_tolerance": "MEDIUM"
            },

            # Banking API Scenario - Complex
            {
                "scenario_name": "Banking Account Transfer API - High Complexity",
                "industry": "banking",
                "endpoint_data": {
                    "path": "/api/v2/accounts/transfer",
                    "method": "POST",
                    "parameters": [
                        {"name": "from_account", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "to_account", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "amount", "in": "body", "required": True, "schema": {"type": "number", "minimum": 0.01}},
                        {"name": "currency", "in": "body", "required": True, "schema": {"type": "string", "enum": ["USD", "EUR", "GBP"]}},
                        {"name": "reference", "in": "body", "required": False, "schema": {"type": "string", "maxLength": 255}}
                    ],
                    "security": [
                        {"type": "oauth2", "flows": {"authorizationCode": {"authorizationUrl": "/oauth/authorize", "tokenUrl": "/oauth/token"}}},
                        {"type": "apiKey", "in": "header", "name": "X-API-Key"}
                    ]
                },
                "expected_vulnerabilities": [
                    "race_condition_vulnerability",  # Concurrent transfers
                    "insufficient_transaction_logging",
                    "missing_fraud_detection",
                    "weak_amount_validation"
                ],
                "compliance_requirements": ["PCI-DSS", "SOX", "GDPR"],
                "risk_tolerance": "CRITICAL"
            }
        ]

    async def run_comprehensive_beta_test(self) -> Dict[str, Any]:
        """
        Run comprehensive beta testing across all scenarios
        """
        print("🚀 Starting Comprehensive Beta Testing for Ultra Premium AI Workforce")
        print("=" * 80)

        start_time = time.time()

        # Initialize the autonomous security agent
        agent = AutonomousSecurityAgent()

        total_tests = len(self.test_scenarios)
        passed_tests = 0
        failed_tests = 0

        for i, scenario in enumerate(self.test_scenarios, 1):
            print(f"\n📋 Test {i}/{total_tests}: {scenario['scenario_name']}")
            print(f"Industry: {scenario['industry'].upper()} | Risk Tolerance: {scenario['risk_tolerance']}")
            print("-" * 60)

            try:
                # Run the test
                result = await self._run_single_test(agent, scenario)

                if result['success']:
                    passed_tests += 1
                    print(f"✅ PASSED: {result['summary']}")
                else:
                    failed_tests += 1
                    print(f"❌ FAILED: {result['error']}")
                    self.failed_tests.append({
                        'scenario': scenario['scenario_name'],
                        'error': result['error'],
                        'details': result.get('details', {})
                    })

                self.test_results.append(result)

            except Exception as e:
                import traceback
                failed_tests += 1
                error_msg = f"Exception during test: {str(e)}"
                error_trace = traceback.format_exc()
                print(f"💥 ERROR: {error_msg}")
                print(f"📍 Full error trace:")
                print(error_trace)

                self.failed_tests.append({
                    'scenario': scenario['scenario_name'],
                    'error': error_msg,
                    'traceback': error_trace,
                    'exception': True
                })

        # Edge case testing
        print("\n🧪 Starting Edge Case Testing...")
        edge_case_scenarios = self._create_edge_case_scenarios()

        for scenario in edge_case_scenarios:
            print(f"\n📋 Edge Case: {scenario['scenario_name']}")
            print(f"Challenge Type: {scenario['challenge_type']} | Expected Behavior: {scenario['expected_behavior']}")
            print("-" * 60)

            try:
                result = await self._run_single_test(agent, scenario)
                if result['success']:
                    print(f"✅ PASSED: {result.get('summary', 'Edge case handled correctly')}")
                    passed_tests += 1
                else:
                    print(f"❌ FAILED: {result.get('error', 'Edge case not handled properly')}")
                    failed_tests += 1

                self.test_results.append(result)

            except Exception as e:
                import traceback
                failed_tests += 1
                error_msg = f"Exception during edge case test: {str(e)}"
                error_trace = traceback.format_exc()
                print(f"💥 ERROR: {error_msg}")
                print(f"📍 Full error trace:")
                print(error_trace)

                self.failed_tests.append({
                    'scenario': scenario['scenario_name'],
                    'error': error_msg,
                    'traceback': error_trace,
                    'exception': True,
                    'test_type': 'edge_case'
                })

            total_tests += 1

        total_time = time.time() - start_time

        # Generate comprehensive results
        results = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': f"{(passed_tests/total_tests*100):.1f}%",
                'total_execution_time': f"{total_time:.2f} seconds"
            },
            'detailed_results': self.test_results,
            'failed_tests': self.failed_tests,
            'performance_metrics': self.performance_metrics,
            'recommendations': self._generate_improvement_recommendations()
        }

        self._print_final_summary(results)
        return results

    async def _run_single_test(self, agent: AutonomousSecurityAgent, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a single test scenario
        """
        test_start = time.time()

        # Create user context based on scenario
        user_context = {
            "user_id": f"beta_user_{scenario['industry']}",
            "project_id": f"project_{scenario['industry']}_test",
            "business_context": f"{scenario['industry']} application requiring {', '.join(scenario['compliance_requirements'])} compliance",
            "preferences": {
                "auto_fix_low_risk": scenario['risk_tolerance'] in ['LOW', 'MEDIUM'],
                "require_approval_medium_risk": True,
                "never_auto_execute_high_risk": True
            },
            "historical_data": []
        }

        try:
            # Run autonomous security analysis
            result = await agent.autonomous_security_analysis(
                endpoint_data=scenario['endpoint_data'],
                user_context=user_context,
                auto_execute=False  # Always require approval for testing
            )

            execution_time = time.time() - test_start

            # Validate results
            validation = self._validate_test_result(result, scenario)

            # Track performance - Safely handle result structure
            security_issues = []
            actions_preview = []

            if isinstance(result, dict):
                analysis_results = result.get('analysis_results', {})
                if isinstance(analysis_results, dict):
                    security_issues = analysis_results.get('security_issues', [])
                elif isinstance(analysis_results, list):
                    # If analysis_results is a list, extract security issues from each item
                    for item in analysis_results:
                        if isinstance(item, dict) and item.get('status') == 'success':
                            tool_result = item.get('result', {})
                            if isinstance(tool_result, dict):
                                security_issues.extend(tool_result.get('vulnerabilities', []))

                proposed_actions = result.get('proposed_actions', {})
                if isinstance(proposed_actions, dict):
                    actions_preview = proposed_actions.get('actions_preview', [])

            self.performance_metrics.append({
                'scenario': scenario['scenario_name'],
                'execution_time': execution_time,
                'vulnerabilities_found': len(security_issues),
                'actions_proposed': len(actions_preview),
                'industry': scenario['industry']
            })

            return {
                'success': validation['passed'],
                'scenario_name': scenario['scenario_name'],
                'execution_time': execution_time,
                'result': result,
                'validation': validation,
                'summary': validation['summary'] if validation['passed'] else validation['issues'][0],
                'error': None if validation['passed'] else '; '.join(validation['issues'])
            }

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"💥 ERROR in _run_single_test: {str(e)}")
            print(f"📍 Full error trace:")
            print(error_trace)
            return {
                'success': False,
                'scenario_name': scenario['scenario_name'],
                'execution_time': time.time() - test_start,
                'error': str(e),
                'traceback': error_trace,
                'details': {'exception_type': type(e).__name__}
            }

    def _validate_test_result(self, result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate if the AI agent performed correctly for the scenario
        """
        issues = []

        # Check if analysis was performed
        if 'analysis_results' not in result:
            issues.append("No analysis results found")

        # Check if expected vulnerabilities were detected
        analysis_results = result.get('analysis_results', {})
        if isinstance(analysis_results, list):
            found_vulnerabilities = []
            for analysis in analysis_results:
                if 'result' in analysis and 'vulnerabilities' in analysis['result']:
                    for vuln in analysis['result']['vulnerabilities']:
                        found_vulnerabilities.append(vuln.get('type', ''))
        else:
            found_vulnerabilities = [
                vuln.get('type', '')
                for vuln in analysis_results.get('security_issues', [])
            ]

        expected_vulns = scenario['expected_vulnerabilities']
        missed_critical = []

        for expected in expected_vulns:
            if not any(expected in found for found in found_vulnerabilities):
                missed_critical.append(expected)

        if missed_critical:
            issues.append(f"Missed critical vulnerabilities: {', '.join(missed_critical)}")

        # Check if compliance requirements were considered
        compliance_mentioned = False
        result_text = json.dumps(result).lower()
        for compliance in scenario['compliance_requirements']:
            if compliance.lower() in result_text:
                compliance_mentioned = True
                break

        if not compliance_mentioned and scenario['compliance_requirements']:
            issues.append(f"Compliance requirements ({', '.join(scenario['compliance_requirements'])}) not addressed")

        # Check if risk assessment is appropriate
        if result.get('proposed_actions', {}).get('risk_level') == 'SAFE' and scenario['risk_tolerance'] == 'CRITICAL':
            issues.append("Risk assessment too lenient for critical scenario")

        # Positive validation
        success_indicators = []
        if found_vulnerabilities:
            success_indicators.append(f"Found {len(found_vulnerabilities)} vulnerabilities")

        if result.get('proposed_actions'):
            success_indicators.append("Generated action plan")

        if result.get('status') in ['completed', 'awaiting_approval']:
            success_indicators.append("Analysis completed successfully")

        return {
            'passed': len(issues) == 0,
            'issues': issues,
            'success_indicators': success_indicators,
            'summary': f"Found {len(found_vulnerabilities)} vulnerabilities, {len(success_indicators)} success indicators" if not issues else f"{len(issues)} validation issues"
        }

    def _generate_improvement_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate recommendations for improving the AI agents based on test results
        """
        recommendations = []

        # Analyze failure patterns
        if self.failed_tests:
            common_failures = {}
            for failure in self.failed_tests:
                error = failure['error']
                if error in common_failures:
                    common_failures[error] += 1
                else:
                    common_failures[error] = 1

            for error, count in common_failures.items():
                if count > 1:
                    recommendations.append({
                        'type': 'bug_fix',
                        'priority': 'HIGH',
                        'issue': error,
                        'frequency': count,
                        'recommendation': f"Fix recurring issue that affects {count} test scenarios"
                    })

        # Analyze performance patterns
        if self.performance_metrics:
            avg_time = sum(m['execution_time'] for m in self.performance_metrics) / len(self.performance_metrics)
            slow_tests = [m for m in self.performance_metrics if m['execution_time'] > avg_time * 1.5]

            if slow_tests:
                recommendations.append({
                    'type': 'performance',
                    'priority': 'MEDIUM',
                    'issue': f"{len(slow_tests)} tests were significantly slower than average",
                    'recommendation': "Optimize LLM prompt efficiency and caching"
                })

        # Industry-specific recommendations
        industries = list(set([m['industry'] for m in self.performance_metrics]))
        for industry in industries:
            industry_metrics = [m for m in self.performance_metrics if m['industry'] == industry]
            avg_vulns = sum(m['vulnerabilities_found'] for m in industry_metrics) / len(industry_metrics)

            if avg_vulns < 2:  # Less than 2 vulnerabilities found on average
                recommendations.append({
                    'type': 'detection_improvement',
                    'priority': 'HIGH',
                    'issue': f"Low vulnerability detection rate for {industry} industry",
                    'recommendation': f"Enhance prompts for {industry}-specific vulnerability patterns"
                })

        # LLM prompt improvements
        recommendations.append({
            'type': 'prompt_enhancement',
            'priority': 'MEDIUM',
            'issue': "Generic prompt improvements needed",
            'recommendation': "Add industry-specific context and vulnerability patterns to LLM prompts"
        })

        return recommendations

    def _print_final_summary(self, results: Dict[str, Any]):
        """
        Print comprehensive test summary
        """
        print("\n" + "=" * 80)
        print("🎯 BETA TESTING SUMMARY")
        print("=" * 80)

        summary = results['summary']
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']}")
        print(f"⏱️  Total Time: {summary['total_execution_time']}")

        if results['failed_tests']:
            print(f"\n❌ FAILED TESTS ({len(results['failed_tests'])}):")
            for failure in results['failed_tests']:
                print(f"  • {failure['scenario']}: {failure['error']}")

        print(f"\n💡 IMPROVEMENT RECOMMENDATIONS ({len(results['recommendations'])}):")
        for rec in results['recommendations']:
            priority_icon = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
            print(f"  {priority_icon} [{rec['type'].upper()}] {rec['recommendation']}")

        print("\n" + "=" * 80)

    def _create_edge_case_scenarios(self) -> List[Dict[str, Any]]:
        """Create challenging edge case scenarios to test AI agent robustness"""
        return [
            # Malformed/Missing Data Test
            {
                "scenario_name": "Malformed API Endpoint Data",
                "challenge_type": "DATA_INTEGRITY",
                "expected_behavior": "GRACEFUL_HANDLING",
                "industry": "general",
                "endpoint_data": {
                    # Deliberately malformed data
                    "path": None,
                    "method": "",
                    "parameters": "not_a_list",
                    "security": {"invalid": "structure"}
                },
                "expected_vulnerabilities": [],  # Should handle gracefully without crashing
                "compliance_requirements": [],
                "risk_tolerance": "MEDIUM"
            },

            # Complex Nested API Structure
            {
                "scenario_name": "Complex Nested API with Multiple Vulnerabilities",
                "challenge_type": "COMPLEXITY",
                "expected_behavior": "COMPREHENSIVE_ANALYSIS",
                "industry": "fintech",
                "endpoint_data": {
                    "path": "/api/v2/users/{user_id}/accounts/{account_id}/transactions/{transaction_id}",
                    "method": "PATCH",
                    "parameters": [
                        {"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "account_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "transaction_id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "amount", "in": "body", "required": True, "schema": {"type": "number"}},
                        {"name": "currency", "in": "body", "required": True, "schema": {"type": "string"}},
                        {"name": "metadata", "in": "body", "required": False, "schema": {"type": "object"}}
                    ],
                    "security": []  # No auth - major vulnerability
                },
                "expected_vulnerabilities": [
                    "broken_object_level_authorization",
                    "no_authentication",
                    "sensitive_data_exposure",
                    "mass_assignment_vulnerability",
                    "missing_rate_limiting"
                ],
                "compliance_requirements": ["PCI-DSS", "SOX"],
                "risk_tolerance": "CRITICAL"
            },

            # Empty/Minimal API
            {
                "scenario_name": "Minimal API Endpoint with No Context",
                "challenge_type": "MINIMAL_DATA",
                "expected_behavior": "BASIC_ANALYSIS",
                "industry": "general",
                "endpoint_data": {
                    "path": "/test",
                    "method": "GET"
                },
                "expected_vulnerabilities": [
                    "no_authentication",
                    "missing_rate_limiting",
                    "insufficient_logging"
                ],
                "compliance_requirements": [],
                "risk_tolerance": "LOW"
            }
        ]


# Function to run the beta test
async def run_beta_test():
    """Main function to run the beta test"""
    framework = BetaTestingFramework()
    results = await framework.run_comprehensive_beta_test()

    # Save results to file
    with open('beta_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Results saved to: beta_test_results.json")
    return results

if __name__ == "__main__":
    # Run the beta test
    asyncio.run(run_beta_test())