"""
LLM Decision Engine - Ultra Premium Feature
Enables autonomous AI agents that make intelligent decisions and execute actions
"""

import json
import asyncio
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Conditional imports for production resilience
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️ Warning: anthropic package not available, LLM decisions disabled")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ Warning: openai package not available, falling back to anthropic only")

class DecisionType(Enum):
    """Types of decisions the LLM can make"""
    ANALYSIS_PLAN = "analysis_plan"
    ACTION_SEQUENCE = "action_sequence"
    TOOL_SELECTION = "tool_selection"
    RISK_ASSESSMENT = "risk_assessment"
    OPTIMIZATION_STRATEGY = "optimization_strategy"

class RiskLevel(Enum):
    """Risk levels for automated actions"""
    SAFE = "safe"           # No risk, auto-execute
    LOW = "low"             # Minor risk, auto-execute with logging
    MEDIUM = "medium"       # Some risk, require user approval
    HIGH = "high"           # High risk, require explicit user confirmation
    CRITICAL = "critical"   # Never auto-execute, manual only

@dataclass
class DecisionContext:
    """Context information for LLM decision making"""
    user_id: str
    project_id: str
    endpoint_data: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    available_tools: List[str]
    current_findings: Dict[str, Any]
    business_context: Optional[str] = None

@dataclass
class AgentAction:
    """Represents an action an agent can take"""
    action_id: str
    tool_name: str
    parameters: Dict[str, Any]
    risk_level: RiskLevel
    reasoning: str
    expected_outcome: str
    estimated_duration: int  # seconds
    depends_on: Optional[List[str]] = None  # Other action IDs this depends on

@dataclass
class DecisionPlan:
    """A complete plan of actions decided by the LLM"""
    plan_id: str
    decision_type: DecisionType
    actions: List[AgentAction]
    total_estimated_duration: int
    confidence_score: float
    reasoning: str
    risk_assessment: RiskLevel
    requires_approval: bool
    created_at: datetime

class LLMDecisionEngine:
    """
    Core LLM Decision Engine for Ultra Premium autonomous agents
    """

    def __init__(self, api_key: str = None, provider: str = "anthropic"):
        self.provider = provider
        self.anthropic_client = None
        self.openai_client = None
        self.logger = logging.getLogger(__name__)

        # Initialize the appropriate client
        self._initialize_clients(api_key)

        # Decision history for learning
        self.decision_history: List[DecisionPlan] = []

        # Tool registry - maps tool names to descriptions
        self.tool_registry = {
            "security_vulnerability_scan": "Scans for security vulnerabilities using OWASP standards",
            "auth_mechanism_analysis": "Analyzes authentication and authorization mechanisms",
            "data_exposure_check": "Checks for potential sensitive data exposure",
            "rate_limiting_test": "Tests for rate limiting and DoS protection",
            "ssl_configuration_check": "Verifies SSL/TLS configuration and certificates",
            "input_validation_test": "Tests input validation and sanitization",
            "session_management_audit": "Audits session management security",
            "cors_policy_analysis": "Analyzes CORS policy configuration",
            "header_security_scan": "Scans security headers and configurations",
            "compliance_check": "Checks compliance with standards (GDPR, HIPAA, PCI-DSS)",
            "auto_fix_security_headers": "Automatically fixes common security header issues",
            "auto_update_environment_vars": "Updates environment variables with secure defaults",
            "auto_generate_tests": "Generates comprehensive test suites",
            "auto_optimize_performance": "Optimizes API performance automatically"
        }

    def _initialize_clients(self, api_key: str = None):
        """Initialize LLM clients based on availability and preference"""
        if self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self.anthropic_client = anthropic.AsyncAnthropic(
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
            )
            self.logger.info("Initialized Anthropic client for LLM decisions")
        elif self.provider == "openai" and OPENAI_AVAILABLE:
            self.openai_client = openai.AsyncOpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY")
            )
            self.logger.info("Initialized OpenAI client for LLM decisions")
        else:
            self.logger.warning("No LLM client available - decisions will be limited")

    async def create_decision_plan(
        self,
        context: DecisionContext,
        decision_type: DecisionType
    ) -> DecisionPlan:
        """
        Core method: LLM creates an intelligent decision plan
        """
        if not self._has_llm_client():
            return self._create_fallback_plan(context, decision_type)

        try:
            # Build the prompt for the LLM
            prompt = self._build_decision_prompt(context, decision_type)

            # Get LLM response
            llm_response = await self._call_llm(prompt)

            # Parse and validate the response
            decision_plan = self._parse_llm_response(llm_response, context, decision_type)

            # Store for learning
            self.decision_history.append(decision_plan)

            self.logger.info(f"Created decision plan {decision_plan.plan_id} with {len(decision_plan.actions)} actions")
            return decision_plan

        except Exception as e:
            self.logger.error(f"Error creating decision plan: {str(e)}")
            return self._create_fallback_plan(context, decision_type)

    def _build_decision_prompt(self, context: DecisionContext, decision_type: DecisionType) -> str:
        """Build the prompt for LLM decision making"""

        base_prompt = f"""
You are an expert AI agent specializing in API security and optimization. Your task is to create an intelligent action plan for {decision_type.value}.

CONTEXT:
- Endpoint: {context.endpoint_data.get('path', 'Unknown')} [{context.endpoint_data.get('method', 'Unknown')}]
- Project Type: {context.business_context or 'General API'}
- Available Tools: {', '.join(context.available_tools)}
- Current Findings: {json.dumps(context.current_findings, indent=2)}

DECISION GUIDELINES:
1. SAFETY FIRST: Always assess risk before recommending actions
2. USER PREFERENCES: Consider the user's past preferences and approval patterns
3. BUSINESS IMPACT: Prioritize actions with high business value
4. EFFICIENCY: Choose the most effective combination of tools
5. DEPENDENCIES: Order actions logically with proper dependencies

RISK LEVELS:
- SAFE: No risk of breaking functionality (e.g., generating reports)
- LOW: Minimal risk with easy rollback (e.g., adding security headers)
- MEDIUM: Some risk, needs user approval (e.g., changing authentication)
- HIGH: High risk, explicit confirmation needed (e.g., modifying core logic)
- CRITICAL: Never auto-execute (e.g., deleting data)

YOUR TASK:
Create a comprehensive action plan that:
1. Analyzes the current state
2. Identifies specific actions to take
3. Estimates risk and duration for each action
4. Provides clear reasoning for each decision
5. Orders actions optimally

RESPONSE FORMAT (JSON):
{{
  "reasoning": "Your overall strategy and reasoning",
  "confidence_score": 0.85,
  "risk_assessment": "LOW",
  "requires_approval": false,
  "actions": [
    {{
      "action_id": "action_1",
      "tool_name": "security_vulnerability_scan",
      "parameters": {{"target": "authentication", "depth": "comprehensive"}},
      "risk_level": "SAFE",
      "reasoning": "Initial security scan to identify vulnerabilities",
      "expected_outcome": "List of security issues found",
      "estimated_duration": 30,
      "depends_on": null
    }}
  ]
}}
"""

        # Add specific context based on decision type
        if decision_type == DecisionType.ANALYSIS_PLAN:
            base_prompt += """
SPECIFIC FOCUS: Create a comprehensive analysis plan to understand the current state before taking any actions.
Priority: Discovery and assessment over immediate fixes.
"""
        elif decision_type == DecisionType.ACTION_SEQUENCE:
            base_prompt += """
SPECIFIC FOCUS: Create an action sequence to fix identified issues automatically.
Priority: Safe automated fixes that improve security/performance.
"""

        return base_prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call the appropriate LLM with the prompt"""
        if self.anthropic_client:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return response.content[0].text
        elif self.openai_client:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        else:
            raise Exception("No LLM client available")

    def _parse_llm_response(
        self,
        response: str,
        context: DecisionContext,
        decision_type: DecisionType
    ) -> DecisionPlan:
        """Parse LLM response into a structured DecisionPlan"""
        try:
            # Extract JSON from response if needed
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()

            data = json.loads(response)

            # Create AgentAction objects
            actions = []
            for action_data in data.get("actions", []):
                action = AgentAction(
                    action_id=action_data["action_id"],
                    tool_name=action_data["tool_name"],
                    parameters=action_data["parameters"],
                    risk_level=RiskLevel(action_data["risk_level"]),
                    reasoning=action_data["reasoning"],
                    expected_outcome=action_data["expected_outcome"],
                    estimated_duration=action_data["estimated_duration"],
                    depends_on=action_data.get("depends_on")
                )
                actions.append(action)

            # Create decision plan
            plan = DecisionPlan(
                plan_id=f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{context.user_id}",
                decision_type=decision_type,
                actions=actions,
                total_estimated_duration=sum(a.estimated_duration for a in actions),
                confidence_score=data.get("confidence_score", 0.7),
                reasoning=data.get("reasoning", "No reasoning provided"),
                risk_assessment=RiskLevel(data.get("risk_assessment", "MEDIUM")),
                requires_approval=data.get("requires_approval", True),
                created_at=datetime.now()
            )

            return plan

        except Exception as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}")
            return self._create_fallback_plan(context, decision_type)

    def _create_fallback_plan(self, context: DecisionContext, decision_type: DecisionType) -> DecisionPlan:
        """Create a basic fallback plan when LLM is unavailable"""
        basic_actions = [
            AgentAction(
                action_id="fallback_1",
                tool_name="security_vulnerability_scan",
                parameters={"target": "general", "depth": "basic"},
                risk_level=RiskLevel.SAFE,
                reasoning="Fallback basic security scan",
                expected_outcome="Basic security assessment",
                estimated_duration=60
            )
        ]

        return DecisionPlan(
            plan_id=f"fallback_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            decision_type=decision_type,
            actions=basic_actions,
            total_estimated_duration=60,
            confidence_score=0.5,
            reasoning="Fallback plan due to LLM unavailability",
            risk_assessment=RiskLevel.SAFE,
            requires_approval=True,
            created_at=datetime.now()
        )

    def _has_llm_client(self) -> bool:
        """Check if any LLM client is available"""
        return self.anthropic_client is not None or self.openai_client is not None

    async def execute_action(self, action: AgentAction, context: DecisionContext) -> Dict[str, Any]:
        """
        Execute a single action (to be implemented by specific agents)
        This is a template method that specific agents should override
        """
        self.logger.info(f"Executing action {action.action_id}: {action.tool_name}")

        # This would be implemented by the specific agent
        # For now, return a placeholder result
        return {
            "action_id": action.action_id,
            "status": "simulated",
            "result": f"Simulated execution of {action.tool_name}",
            "timestamp": datetime.now().isoformat()
        }

    def learn_from_feedback(self, plan_id: str, user_feedback: Dict[str, Any]):
        """
        Learn from user feedback to improve future decisions
        """
        # Find the plan
        plan = next((p for p in self.decision_history if p.plan_id == plan_id), None)
        if not plan:
            return

        # Store feedback for future improvement
        # This could be used to fine-tune prompts or decision logic
        self.logger.info(f"Learning from feedback for plan {plan_id}: {user_feedback}")

    def get_decision_summary(self, plan: DecisionPlan) -> Dict[str, Any]:
        """
        Get a user-friendly summary of a decision plan
        """
        return {
            "plan_id": plan.plan_id,
            "summary": plan.reasoning,
            "total_actions": len(plan.actions),
            "estimated_duration_minutes": plan.total_estimated_duration // 60,
            "confidence": f"{plan.confidence_score:.0%}",
            "risk_level": plan.risk_assessment.value,
            "requires_approval": plan.requires_approval,
            "actions_preview": [
                {
                    "action": action.tool_name,
                    "purpose": action.reasoning,
                    "risk": action.risk_level.value
                }
                for action in plan.actions[:3]  # Show first 3 actions
            ]
        }