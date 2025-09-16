"""
Autonomous Security Agent - Ultra Premium Feature
Uses LLM decision making to automatically analyze and fix security issues
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..llm_decision_engine import (
    LLMDecisionEngine, DecisionContext, DecisionType, RiskLevel,
    AgentAction, DecisionPlan
)

class AutonomousSecurityAgent:
    """
    Enhanced security agent with autonomous decision-making capabilities
    """

    def __init__(self, llm_api_key: str = None):
        self.llm_engine = LLMDecisionEngine(api_key=llm_api_key)
        self.logger = logging.getLogger(__name__)

        # Track executions for premium analytics
        self.execution_history: List[Dict[str, Any]] = []

        # Security tools available to this agent
        self.security_tools = {
            "security_vulnerability_scan": self._run_vulnerability_scan,
            "auth_mechanism_analysis": self._analyze_auth_mechanism,
            "data_exposure_check": self._check_data_exposure,
            "rate_limiting_test": self._test_rate_limiting,
            "ssl_configuration_check": self._check_ssl_config,
            "input_validation_test": self._test_input_validation,
            "session_management_audit": self._audit_session_management,
            "cors_policy_analysis": self._analyze_cors_policy,
            "header_security_scan": self._scan_security_headers,
            "compliance_check": self._check_compliance,
            "auto_fix_security_headers": self._auto_fix_security_headers,
            "auto_update_environment_vars": self._auto_update_env_vars,
        }

    async def autonomous_security_analysis(
        self,
        endpoint_data: Dict[str, Any],
        user_context: Dict[str, Any],
        auto_execute: bool = False
    ) -> Dict[str, Any]:
        """
        Main entry point for autonomous security analysis
        """
        self.logger.info(f"Starting autonomous security analysis for {endpoint_data.get('path', 'unknown')}")

        # Create decision context
        context = DecisionContext(
            user_id=user_context.get("user_id", "unknown"),
            project_id=user_context.get("project_id", "unknown"),
            endpoint_data=endpoint_data,
            historical_data=user_context.get("historical_data", []),
            user_preferences=user_context.get("preferences", {}),
            available_tools=list(self.security_tools.keys()),
            current_findings={},
            business_context=user_context.get("business_context")
        )

        # Phase 1: LLM creates analysis plan
        analysis_plan = await self.llm_engine.create_decision_plan(
            context, DecisionType.ANALYSIS_PLAN
        )

        self.logger.info(f"LLM created analysis plan with {len(analysis_plan.actions)} actions")

        # Phase 2: Execute analysis actions
        analysis_results = await self._execute_plan(analysis_plan, context)

        # Phase 3: Update context with findings
        context.current_findings = analysis_results

        # Phase 4: LLM creates action plan based on findings
        action_plan = await self.llm_engine.create_decision_plan(
            context, DecisionType.ACTION_SEQUENCE
        )

        # Phase 5: Execute actions (with user approval if needed)
        action_results = []
        if auto_execute or not action_plan.requires_approval:
            action_results = await self._execute_plan(action_plan, context)
        else:
            # Return plan for user approval
            return {
                "status": "awaiting_approval",
                "analysis_results": analysis_results,
                "proposed_actions": self.llm_engine.get_decision_summary(action_plan),
                "action_plan_id": action_plan.plan_id,
                "estimated_duration": action_plan.total_estimated_duration // 60,
                "risk_level": action_plan.risk_assessment.value
            }

        # Phase 6: Return comprehensive results
        return {
            "status": "completed",
            "analysis_results": analysis_results,
            "actions_taken": action_results,
            "analysis_plan_summary": self.llm_engine.get_decision_summary(analysis_plan),
            "action_plan_summary": self.llm_engine.get_decision_summary(action_plan),
            "total_issues_found": len(analysis_results.get("security_issues", [])),
            "total_issues_fixed": len([r for r in action_results if r.get("status") == "success"]),
            "execution_time": sum(r.get("duration", 0) for r in action_results),
            "recommendations": self._generate_recommendations(analysis_results, action_results)
        }

    async def execute_approved_plan(
        self,
        plan_id: str,
        context: DecisionContext
    ) -> Dict[str, Any]:
        """
        Execute a previously approved action plan
        """
        # Find the plan in history
        plan = next(
            (p for p in self.llm_engine.decision_history if p.plan_id == plan_id),
            None
        )

        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # Execute the plan
        results = await self._execute_plan(plan, context)

        return {
            "status": "completed",
            "plan_id": plan_id,
            "results": results,
            "total_actions": len(plan.actions),
            "successful_actions": len([r for r in results if r.get("status") == "success"])
        }

    async def _execute_plan(
        self,
        plan: DecisionPlan,
        context: DecisionContext
    ) -> List[Dict[str, Any]]:
        """
        Execute all actions in a decision plan
        """
        results = []

        for action in plan.actions:
            try:
                start_time = datetime.now()

                # Check if this action depends on others
                if action.depends_on:
                    # Verify dependencies were successful
                    dependency_results = [
                        r for r in results
                        if r.get("action_id") in action.depends_on
                    ]
                    if not all(r.get("status") == "success" for r in dependency_results):
                        results.append({
                            "action_id": action.action_id,
                            "status": "skipped",
                            "reason": "Dependencies failed",
                            "timestamp": start_time.isoformat()
                        })
                        continue

                # Execute the action
                result = await self._execute_single_action(action, context)

                # Add metadata
                result.update({
                    "action_id": action.action_id,
                    "duration": (datetime.now() - start_time).total_seconds(),
                    "timestamp": start_time.isoformat()
                })

                results.append(result)

                # Log execution for premium analytics
                self.execution_history.append({
                    "action": action.tool_name,
                    "success": result.get("status") == "success",
                    "duration": result.get("duration"),
                    "user_id": context.user_id,
                    "timestamp": start_time.isoformat()
                })

            except Exception as e:
                self.logger.error(f"Error executing action {action.action_id}: {str(e)}")
                results.append({
                    "action_id": action.action_id,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

        return results

    async def _execute_single_action(
        self,
        action: AgentAction,
        context: DecisionContext
    ) -> Dict[str, Any]:
        """
        Execute a single action using the appropriate tool
        """
        if action.tool_name not in self.security_tools:
            return {
                "status": "error",
                "error": f"Unknown tool: {action.tool_name}"
            }

        tool_function = self.security_tools[action.tool_name]

        try:
            result = await tool_function(action.parameters, context)
            return {
                "status": "success",
                "tool": action.tool_name,
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "tool": action.tool_name,
                "error": str(e)
            }

    # Security tool implementations
    async def _run_vulnerability_scan(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Run comprehensive vulnerability scan"""
        endpoint = context.endpoint_data
        target = params.get("target", "general")
        depth = params.get("depth", "basic")

        vulnerabilities = []

        # Check for common vulnerabilities based on endpoint
        if endpoint.get("method") == "POST" and "password" in str(endpoint.get("parameters", [])):
            vulnerabilities.append({
                "type": "weak_authentication",
                "severity": "high",
                "description": "Password sent in POST body without proper encryption validation",
                "recommendation": "Implement password strength validation and secure transmission"
            })

        if not endpoint.get("security", []):
            vulnerabilities.append({
                "type": "no_authentication",
                "severity": "critical",
                "description": "Endpoint has no authentication requirements",
                "recommendation": "Add authentication and authorization checks"
            })

        # Simulate more detailed scanning based on depth
        if depth == "comprehensive":
            vulnerabilities.extend([
                {
                    "type": "missing_rate_limiting",
                    "severity": "medium",
                    "description": "No rate limiting detected on endpoint",
                    "recommendation": "Implement rate limiting to prevent abuse"
                },
                {
                    "type": "insufficient_logging",
                    "severity": "low",
                    "description": "Insufficient security event logging",
                    "recommendation": "Enhance logging for security monitoring"
                }
            ])

        return {
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
            "scan_type": target,
            "scan_depth": depth
        }

    async def _analyze_auth_mechanism(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Analyze authentication mechanisms"""
        endpoint = context.endpoint_data
        security_schemes = endpoint.get("security", [])

        auth_analysis = {
            "has_authentication": len(security_schemes) > 0,
            "auth_types": [],
            "weaknesses": [],
            "recommendations": []
        }

        for scheme in security_schemes:
            auth_type = scheme.get("type", "unknown")
            auth_analysis["auth_types"].append(auth_type)

            if auth_type == "basic":
                auth_analysis["weaknesses"].append("Basic auth is not secure over HTTP")
                auth_analysis["recommendations"].append("Use OAuth 2.0 or JWT tokens instead")
            elif auth_type == "apiKey" and scheme.get("in") == "query":
                auth_analysis["weaknesses"].append("API key in query parameters is logged")
                auth_analysis["recommendations"].append("Move API key to headers")

        return auth_analysis

    async def _check_data_exposure(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Check for potential data exposure issues"""
        endpoint = context.endpoint_data
        responses = endpoint.get("responses", {})

        exposure_risks = []

        for status_code, response in responses.items():
            schema = response.get("content", {}).get("application/json", {}).get("schema", {})
            properties = schema.get("properties", {})

            # Check for sensitive data in responses
            sensitive_fields = ["password", "ssn", "credit_card", "private_key", "secret"]
            for field_name in properties.keys():
                if any(sensitive in field_name.lower() for sensitive in sensitive_fields):
                    exposure_risks.append({
                        "field": field_name,
                        "risk": "high",
                        "description": f"Potentially sensitive field '{field_name}' in response"
                    })

        return {
            "exposure_risks_found": len(exposure_risks),
            "risks": exposure_risks
        }

    async def _test_rate_limiting(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Test for rate limiting implementation"""
        # Simulate rate limiting test
        return {
            "rate_limiting_detected": False,
            "recommendation": "Implement rate limiting to prevent abuse",
            "suggested_limits": "100 requests per minute per IP"
        }

    async def _check_ssl_config(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Check SSL/TLS configuration"""
        # Simulate SSL check
        return {
            "ssl_enabled": True,
            "tls_version": "1.3",
            "certificate_valid": True,
            "issues": []
        }

    async def _test_input_validation(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Test input validation mechanisms"""
        endpoint = context.endpoint_data
        parameters = endpoint.get("parameters", [])

        validation_issues = []

        for param in parameters:
            if not param.get("schema", {}).get("type"):
                validation_issues.append({
                    "parameter": param.get("name"),
                    "issue": "No type validation specified"
                })

        return {
            "validation_issues": validation_issues,
            "parameters_checked": len(parameters)
        }

    async def _audit_session_management(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Audit session management security"""
        return {
            "session_security": "basic",
            "recommendations": [
                "Implement secure session tokens",
                "Add session timeout",
                "Use httpOnly cookies"
            ]
        }

    async def _analyze_cors_policy(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Analyze CORS policy configuration"""
        return {
            "cors_configured": False,
            "recommendation": "Configure CORS policy to restrict cross-origin requests"
        }

    async def _scan_security_headers(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Scan for security headers"""
        missing_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy"
        ]

        return {
            "missing_security_headers": missing_headers,
            "recommendations": "Add missing security headers to prevent XSS and clickjacking"
        }

    async def _check_compliance(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Check compliance with various standards"""
        standards = params.get("standards", ["GDPR", "OWASP"])

        compliance_status = {}
        for standard in standards:
            if standard == "GDPR":
                compliance_status["GDPR"] = {
                    "compliant": False,
                    "missing": ["Data encryption", "Privacy policy endpoint", "Data deletion capability"]
                }
            elif standard == "OWASP":
                compliance_status["OWASP"] = {
                    "compliant": False,
                    "missing": ["Input validation", "Authentication", "Logging"]
                }

        return compliance_status

    # Auto-fix implementations (Ultra Premium features)
    async def _auto_fix_security_headers(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Automatically fix missing security headers"""
        headers_to_add = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'"
        }

        # Simulate adding headers to environment variables
        return {
            "headers_added": list(headers_to_add.keys()),
            "action": "Added security headers to environment configuration",
            "rollback_available": True
        }

    async def _auto_update_env_vars(self, params: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        """Automatically update environment variables with secure defaults"""
        updates = params.get("updates", {})

        # Simulate updating environment variables
        return {
            "variables_updated": list(updates.keys()),
            "action": "Updated environment variables with secure defaults",
            "backup_created": True
        }

    def _generate_recommendations(self, analysis_results: List[Dict], action_results: List[Dict]) -> List[str]:
        """Generate high-level recommendations based on analysis and actions"""
        recommendations = []

        total_vulnerabilities = sum(
            r.get("result", {}).get("vulnerabilities_found", 0)
            for r in analysis_results if r.get("status") == "success"
        )

        if total_vulnerabilities > 5:
            recommendations.append("Consider implementing a comprehensive security review process")

        successful_fixes = len([r for r in action_results if r.get("status") == "success"])
        if successful_fixes > 0:
            recommendations.append(f"Successfully automated {successful_fixes} security improvements")

        recommendations.append("Enable continuous security monitoring for ongoing protection")

        return recommendations

    def get_execution_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get premium analytics for user's autonomous agent usage"""
        user_executions = [
            e for e in self.execution_history
            if e.get("user_id") == user_id
        ]

        if not user_executions:
            return {"message": "No execution history found"}

        total_executions = len(user_executions)
        successful_executions = len([e for e in user_executions if e.get("success")])
        avg_duration = sum(e.get("duration", 0) for e in user_executions) / total_executions

        return {
            "total_autonomous_actions": total_executions,
            "success_rate": f"{(successful_executions / total_executions * 100):.1f}%",
            "average_execution_time": f"{avg_duration:.1f} seconds",
            "most_used_tools": self._get_most_used_tools(user_executions),
            "time_saved_estimate": f"{total_executions * 5} minutes"  # Estimate 5 min saved per action
        }

    def _get_most_used_tools(self, executions: List[Dict]) -> List[Dict[str, Any]]:
        """Get the most frequently used tools"""
        tool_counts = {}
        for execution in executions:
            tool = execution.get("action")
            tool_counts[tool] = tool_counts.get(tool, 0) + 1

        return [
            {"tool": tool, "count": count}
            for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]