"""
WorkflowOptimizationAgent - AI agent for analyzing and optimizing user workflows
Analyzes user patterns, suggests improvements, and automates repetitive tasks
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict
import statistics


@dataclass
class WorkflowPattern:
    """Represents a detected workflow pattern"""

    pattern_id: str
    name: str
    description: str
    frequency: int
    average_time: float
    steps: List[str]
    optimization_potential: float
    suggested_improvements: List[str]


@dataclass
class UserAction:
    """Represents a user action in the workflow"""

    timestamp: datetime
    action_type: str
    endpoint: str
    duration: float
    success: bool
    context: Dict[str, Any]


class WorkflowOptimizationAgent:
    """
    Enterprise-grade workflow optimization agent
    Learns from user behavior and suggests intelligent improvements
    """

    def __init__(self):
        self.name = "WorkflowOptimizationAgent"
        self.version = "1.0.0"
        self.user_sessions = defaultdict(list)
        self.detected_patterns = []
        self.optimization_suggestions = []

    async def analyze_user_workflow(
        self, user_id: str, actions: List[UserAction]
    ) -> Dict[str, Any]:
        """Analyze user workflow and detect patterns"""
        try:
            # Store user actions
            self.user_sessions[user_id].extend(actions)

            # Detect patterns
            patterns = await self._detect_patterns(user_id)

            # Generate optimizations
            optimizations = await self._generate_optimizations(patterns)

            # Calculate efficiency metrics
            efficiency = await self._calculate_efficiency(actions)

            return {
                "user_id": user_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "detected_patterns": [
                    {
                        "pattern_id": p.pattern_id,
                        "name": p.name,
                        "description": p.description,
                        "frequency": p.frequency,
                        "optimization_potential": p.optimization_potential,
                    }
                    for p in patterns
                ],
                "optimizations": optimizations,
                "efficiency_score": efficiency["score"],
                "time_savings_potential": efficiency["time_savings"],
                "recommendations": await self._get_recommendations(
                    patterns, efficiency
                ),
            }

        except Exception as e:
            return {
                "error": f"Workflow analysis failed: {str(e)}",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            }

    async def _detect_patterns(self, user_id: str) -> List[WorkflowPattern]:
        """Detect recurring patterns in user workflows"""
        actions = self.user_sessions.get(user_id, [])
        if len(actions) < 3:
            return []

        patterns = []

        # Pattern 1: API Testing Sequences
        testing_sequences = self._find_testing_sequences(actions)
        if testing_sequences:
            patterns.append(
                WorkflowPattern(
                    pattern_id="api_testing_sequence",
                    name="API Testing Workflow",
                    description="Recurring pattern of API endpoint testing",
                    frequency=len(testing_sequences),
                    average_time=statistics.mean(
                        [seq["duration"] for seq in testing_sequences]
                    ),
                    steps=[
                        "Create request",
                        "Set parameters",
                        "Execute",
                        "Validate response",
                    ],
                    optimization_potential=0.8,
                    suggested_improvements=[
                        "Create reusable test templates",
                        "Set up automated validation rules",
                        "Use environment variables for common parameters",
                    ],
                )
            )

        # Pattern 2: Collection Management
        collection_patterns = self._find_collection_patterns(actions)
        if collection_patterns:
            patterns.append(
                WorkflowPattern(
                    pattern_id="collection_management",
                    name="Collection Management Pattern",
                    description="Frequent collection creation and organization",
                    frequency=len(collection_patterns),
                    average_time=120.0,
                    steps=[
                        "Create collection",
                        "Add requests",
                        "Organize folders",
                        "Share",
                    ],
                    optimization_potential=0.6,
                    suggested_improvements=[
                        "Use collection templates",
                        "Auto-organize by API type",
                        "Bulk import from OpenAPI specs",
                    ],
                )
            )

        # Pattern 3: Environment Switching
        env_switching = self._find_environment_switching(actions)
        if env_switching:
            patterns.append(
                WorkflowPattern(
                    pattern_id="environment_switching",
                    name="Environment Switching Pattern",
                    description="Frequent switching between environments",
                    frequency=len(env_switching),
                    average_time=30.0,
                    steps=["Select environment", "Update variables", "Test endpoints"],
                    optimization_potential=0.9,
                    suggested_improvements=[
                        "Set up environment-specific collections",
                        "Use global variables for common settings",
                        "Create environment sync shortcuts",
                    ],
                )
            )

        return patterns

    def _find_testing_sequences(self, actions: List[UserAction]) -> List[Dict]:
        """Find API testing sequences in user actions"""
        sequences = []
        current_sequence = []

        for action in actions:
            if action.action_type in [
                "create_request",
                "execute_request",
                "validate_response",
            ]:
                current_sequence.append(action)

                # If we have a complete sequence
                if (
                    len(current_sequence) >= 3
                    and action.action_type == "validate_response"
                ):
                    duration = (
                        current_sequence[-1].timestamp - current_sequence[0].timestamp
                    ).total_seconds()
                    sequences.append(
                        {"actions": current_sequence.copy(), "duration": duration}
                    )
                    current_sequence = []
            else:
                current_sequence = []

        return sequences

    def _find_collection_patterns(self, actions: List[UserAction]) -> List[Dict]:
        """Find collection management patterns"""
        collection_actions = [a for a in actions if "collection" in a.action_type]

        # Group by time windows (collections created within 1 hour)
        patterns = []
        for i, action in enumerate(collection_actions):
            related = [action]
            for j in range(i + 1, len(collection_actions)):
                if (
                    collection_actions[j].timestamp - action.timestamp
                ).total_seconds() < 3600:
                    related.append(collection_actions[j])
                else:
                    break

            if len(related) >= 2:
                patterns.append({"actions": related})

        return patterns

    def _find_environment_switching(self, actions: List[UserAction]) -> List[Dict]:
        """Find environment switching patterns"""
        env_switches = [a for a in actions if "environment" in a.action_type]

        # Count switches in time windows
        switches = []
        for i in range(len(env_switches) - 1):
            time_diff = (
                env_switches[i + 1].timestamp - env_switches[i].timestamp
            ).total_seconds()
            if time_diff < 600:  # Within 10 minutes
                switches.append({"actions": [env_switches[i], env_switches[i + 1]]})

        return switches

    async def _generate_optimizations(
        self, patterns: List[WorkflowPattern]
    ) -> List[Dict]:
        """Generate specific optimization suggestions"""
        optimizations = []

        for pattern in patterns:
            if pattern.optimization_potential > 0.7:
                optimizations.append(
                    {
                        "type": "high_priority",
                        "title": f"Optimize {pattern.name}",
                        "description": f"Save up to {pattern.optimization_potential * 100:.0f}% time on {pattern.name.lower()}",
                        "time_savings": f"{pattern.average_time * pattern.optimization_potential:.1f} seconds per workflow",
                        "implementation": pattern.suggested_improvements[0]
                        if pattern.suggested_improvements
                        else "Create automation",
                        "impact": "High",
                    }
                )
            elif pattern.optimization_potential > 0.4:
                optimizations.append(
                    {
                        "type": "medium_priority",
                        "title": f"Improve {pattern.name}",
                        "description": f"Potential {pattern.optimization_potential * 100:.0f}% efficiency gain",
                        "time_savings": f"{pattern.average_time * pattern.optimization_potential:.1f} seconds per workflow",
                        "implementation": pattern.suggested_improvements[0]
                        if pattern.suggested_improvements
                        else "Streamline process",
                        "impact": "Medium",
                    }
                )

        return optimizations

    async def _calculate_efficiency(
        self, actions: List[UserAction]
    ) -> Dict[str, float]:
        """Calculate workflow efficiency metrics"""
        if not actions:
            return {"score": 0.0, "time_savings": 0.0}

        # Calculate success rate
        successful_actions = sum(1 for a in actions if a.success)
        success_rate = successful_actions / len(actions)

        # Calculate average response time
        avg_duration = statistics.mean([a.duration for a in actions if a.duration > 0])

        # Calculate efficiency score (0-100)
        efficiency_score = (
            success_rate * 0.7 + min(1.0, 5.0 / avg_duration) * 0.3
        ) * 100

        # Estimate time savings potential
        time_savings = max(0, avg_duration - 2.0) * len(
            actions
        )  # Assume 2s optimal time

        return {
            "score": round(efficiency_score, 1),
            "time_savings": round(time_savings, 1),
            "success_rate": round(success_rate * 100, 1),
            "avg_duration": round(avg_duration, 2),
        }

    async def _get_recommendations(
        self, patterns: List[WorkflowPattern], efficiency: Dict
    ) -> List[str]:
        """Get personalized recommendations"""
        recommendations = []

        # Efficiency-based recommendations
        if efficiency["score"] < 70:
            recommendations.extend(
                [
                    "🎯 Focus on reducing request complexity to improve response times",
                    "🔄 Set up request templates for common API calls",
                    "⚡ Use environment variables to reduce manual input",
                ]
            )

        # Pattern-based recommendations
        for pattern in patterns:
            if pattern.frequency >= 5:
                recommendations.append(
                    f"🤖 Automate your '{pattern.name}' workflow - you do this {pattern.frequency} times regularly"
                )

        # General productivity recommendations
        recommendations.extend(
            [
                "📚 Create documentation for your most-used APIs",
                "🔍 Use the AI Discovery Agent to find API optimizations",
                "⏰ Schedule regular API health checks",
                "🎨 Organize collections by business domain for better workflow",
            ]
        )

        return recommendations[:6]  # Return top 6 recommendations

    async def get_workflow_insights(
        self, user_id: str, time_range: str = "7d"
    ) -> Dict[str, Any]:
        """Get comprehensive workflow insights for a user"""
        try:
            # Calculate time range
            now = datetime.now()
            if time_range == "24h":
                start_time = now - timedelta(hours=24)
            elif time_range == "7d":
                start_time = now - timedelta(days=7)
            elif time_range == "30d":
                start_time = now - timedelta(days=30)
            else:
                start_time = now - timedelta(days=7)

            # Filter actions by time range
            all_actions = self.user_sessions.get(user_id, [])
            filtered_actions = [a for a in all_actions if a.timestamp >= start_time]

            if not filtered_actions:
                return {
                    "insights": "No workflow data available for the selected time range",
                    "recommendations": [
                        "Start using the platform to get personalized insights!"
                    ],
                }

            # Generate insights
            insights = {
                "summary": {
                    "total_actions": len(filtered_actions),
                    "time_range": time_range,
                    "most_active_day": self._get_most_active_day(filtered_actions),
                    "average_session_length": self._calculate_avg_session_length(
                        filtered_actions
                    ),
                },
                "productivity_score": await self._calculate_productivity_score(
                    filtered_actions
                ),
                "top_patterns": await self._get_top_patterns(user_id),
                "efficiency_trends": await self._get_efficiency_trends(
                    filtered_actions
                ),
                "suggested_automations": await self._suggest_automations(
                    filtered_actions
                ),
            }

            return insights

        except Exception as e:
            return {
                "error": f"Failed to generate workflow insights: {str(e)}",
                "user_id": user_id,
            }

    def _get_most_active_day(self, actions: List[UserAction]) -> str:
        """Find the most active day of the week"""
        day_counts = defaultdict(int)
        for action in actions:
            day_counts[action.timestamp.strftime("%A")] += 1

        return (
            max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else "No data"
        )

    def _calculate_avg_session_length(self, actions: List[UserAction]) -> float:
        """Calculate average session length in minutes"""
        if len(actions) < 2:
            return 0.0

        # Group actions into sessions (gap > 30 minutes = new session)
        sessions = []
        current_session = [actions[0]]

        for i in range(1, len(actions)):
            time_gap = (
                actions[i].timestamp - actions[i - 1].timestamp
            ).total_seconds() / 60
            if time_gap <= 30:  # Same session
                current_session.append(actions[i])
            else:  # New session
                if len(current_session) > 1:
                    session_length = (
                        current_session[-1].timestamp - current_session[0].timestamp
                    ).total_seconds() / 60
                    sessions.append(session_length)
                current_session = [actions[i]]

        # Add last session
        if len(current_session) > 1:
            session_length = (
                current_session[-1].timestamp - current_session[0].timestamp
            ).total_seconds() / 60
            sessions.append(session_length)

        return round(statistics.mean(sessions), 1) if sessions else 0.0

    async def _calculate_productivity_score(self, actions: List[UserAction]) -> int:
        """Calculate a productivity score (0-100)"""
        if not actions:
            return 0

        # Factors: Success rate, speed, variety of actions
        success_rate = sum(1 for a in actions if a.success) / len(actions)
        avg_speed = 1 / (
            statistics.mean([a.duration for a in actions if a.duration > 0]) + 1
        )
        action_variety = (
            len(set(a.action_type for a in actions)) / 10
        )  # Normalize to max 10 action types

        score = (success_rate * 0.5 + avg_speed * 0.3 + action_variety * 0.2) * 100
        return max(0, min(100, int(score)))

    async def _get_top_patterns(self, user_id: str) -> List[Dict]:
        """Get top workflow patterns for user"""
        patterns = await self._detect_patterns(user_id)
        return sorted(
            patterns, key=lambda p: p.frequency * p.optimization_potential, reverse=True
        )[:3]

    async def _get_efficiency_trends(self, actions: List[UserAction]) -> List[Dict]:
        """Calculate efficiency trends over time"""
        if len(actions) < 10:
            return []

        # Group by days
        daily_efficiency = defaultdict(list)
        for action in actions:
            day = action.timestamp.date()
            daily_efficiency[day].append(action.duration)

        trends = []
        for day, durations in daily_efficiency.items():
            avg_duration = statistics.mean(durations)
            trends.append(
                {
                    "date": day.isoformat(),
                    "efficiency": round(
                        max(0, (5.0 - avg_duration) / 5.0 * 100), 1
                    ),  # 5s = 0% efficiency, 0s = 100%
                    "requests": len(durations),
                }
            )

        return sorted(trends, key=lambda x: x["date"])[-7:]  # Last 7 days

    async def _suggest_automations(self, actions: List[UserAction]) -> List[str]:
        """Suggest specific automations based on user behavior"""
        suggestions = []

        # Analyze action patterns
        action_counts = defaultdict(int)
        for action in actions:
            action_counts[action.action_type] += 1

        # High-frequency actions that can be automated
        if action_counts.get("execute_request", 0) > 20:
            suggestions.append(
                "🤖 Set up automated API health checks for your frequently tested endpoints"
            )

        if action_counts.get("create_request", 0) > 15:
            suggestions.append(
                "📋 Create request templates for your most common API patterns"
            )

        if action_counts.get("switch_environment", 0) > 10:
            suggestions.append(
                "🔄 Set up environment-specific test suites to reduce manual switching"
            )

        return suggestions[:3]  # Top 3 suggestions


# Usage example and testing
if __name__ == "__main__":

    async def test_workflow_agent():
        agent = WorkflowOptimizationAgent()

        # Create sample user actions
        sample_actions = [
            UserAction(
                timestamp=datetime.now() - timedelta(minutes=30),
                action_type="create_request",
                endpoint="/api/users",
                duration=2.5,
                success=True,
                context={"method": "GET"},
            ),
            UserAction(
                timestamp=datetime.now() - timedelta(minutes=29),
                action_type="execute_request",
                endpoint="/api/users",
                duration=1.2,
                success=True,
                context={"status": 200},
            ),
            UserAction(
                timestamp=datetime.now() - timedelta(minutes=28),
                action_type="validate_response",
                endpoint="/api/users",
                duration=0.8,
                success=True,
                context={"validation": "passed"},
            ),
        ]

        # Analyze workflow
        analysis = await agent.analyze_user_workflow("test_user", sample_actions)
        print("Workflow Analysis:", json.dumps(analysis, indent=2))

        # Get insights
        insights = await agent.get_workflow_insights("test_user")
        print("\nWorkflow Insights:", json.dumps(insights, indent=2))

    # Run test
    asyncio.run(test_workflow_agent())
