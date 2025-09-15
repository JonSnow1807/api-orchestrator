"""
IntegrationAgent - AI agent for seamless tool integrations and workflow automation
Connects with popular development tools and platforms to create unified workflows
"""

import asyncio
import json
import requests
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import base64
import hmac
import hashlib
from urllib.parse import urlencode, urlparse

class IntegrationType(Enum):
    CI_CD = "ci_cd"
    MONITORING = "monitoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"
    COMMUNICATION = "communication"
    PROJECT_MANAGEMENT = "project_management"

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class Integration:
    """Represents a tool integration configuration"""
    integration_id: str
    name: str
    type: IntegrationType
    status: IntegrationStatus
    config: Dict[str, Any]
    webhook_url: Optional[str] = None
    api_key: Optional[str] = None
    last_sync: Optional[datetime] = None

@dataclass
class IntegrationEvent:
    """Represents an event from an integrated tool"""
    event_id: str
    integration_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    processed: bool = False

@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    integration_id: str
    success: bool
    items_synced: int
    errors: List[str]
    duration: float

class IntegrationAgent:
    """
    Enterprise-grade integration agent for connecting with external tools
    Supports popular development, monitoring, and collaboration platforms
    """

    def __init__(self):
        self.name = "IntegrationAgent"
        self.version = "1.0.0"
        self.integrations = {}
        self.event_queue = []
        self.sync_history = []
        self.webhook_handlers = {}

    async def add_integration(self, integration_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new tool integration"""
        try:
            integration_id = integration_config.get("id") or f"int_{int(time.time())}"

            integration = Integration(
                integration_id=integration_id,
                name=integration_config["name"],
                type=IntegrationType(integration_config["type"]),
                status=IntegrationStatus.PENDING,
                config=integration_config.get("config", {}),
                webhook_url=integration_config.get("webhook_url"),
                api_key=integration_config.get("api_key")
            )

            # Validate integration
            validation_result = await self._validate_integration(integration)

            if validation_result["valid"]:
                integration.status = IntegrationStatus.ACTIVE
                self.integrations[integration_id] = integration

                # Set up webhook handler if needed
                if integration.webhook_url:
                    await self._setup_webhook_handler(integration)

                return {
                    "integration_id": integration_id,
                    "status": "success",
                    "message": f"Integration '{integration.name}' added successfully",
                    "integration": {
                        "id": integration.integration_id,
                        "name": integration.name,
                        "type": integration.type.value,
                        "status": integration.status.value
                    }
                }
            else:
                return {
                    "integration_id": integration_id,
                    "status": "error",
                    "message": f"Integration validation failed: {validation_result['error']}",
                    "errors": validation_result.get("errors", [])
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to add integration: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def sync_integration(self, integration_id: str, force: bool = False) -> Dict[str, Any]:
        """Synchronize data with an integrated tool"""
        try:
            integration = self.integrations.get(integration_id)
            if not integration:
                return {"error": "Integration not found", "integration_id": integration_id}

            sync_start = time.time()

            # Check if sync is needed
            if not force and integration.last_sync:
                time_since_sync = (datetime.now() - integration.last_sync).total_seconds()
                if time_since_sync < 300:  # 5 minutes minimum between syncs
                    return {
                        "integration_id": integration_id,
                        "status": "skipped",
                        "message": "Recent sync found, use force=True to override"
                    }

            # Perform sync based on integration type
            sync_result = await self._perform_sync(integration)

            # Update integration
            integration.last_sync = datetime.now()
            sync_duration = time.time() - sync_start

            # Store sync history
            sync_record = SyncResult(
                integration_id=integration_id,
                success=sync_result["success"],
                items_synced=sync_result.get("items_synced", 0),
                errors=sync_result.get("errors", []),
                duration=sync_duration
            )
            self.sync_history.append(sync_record)

            return {
                "integration_id": integration_id,
                "sync_result": {
                    "success": sync_result["success"],
                    "items_synced": sync_result.get("items_synced", 0),
                    "duration": round(sync_duration, 2),
                    "errors": sync_result.get("errors", []),
                    "last_sync": integration.last_sync.isoformat()
                },
                "data": sync_result.get("data", {})
            }

        except Exception as e:
            return {
                "integration_id": integration_id,
                "error": f"Sync failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def handle_webhook(self, integration_id: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle incoming webhook from integrated tool"""
        try:
            integration = self.integrations.get(integration_id)
            if not integration:
                return {"error": "Integration not found", "status": 404}

            # Verify webhook signature if configured
            if integration.config.get("webhook_secret"):
                if not self._verify_webhook_signature(payload, headers, integration.config["webhook_secret"]):
                    return {"error": "Invalid webhook signature", "status": 401}

            # Create event
            event = IntegrationEvent(
                event_id=f"evt_{int(time.time())}_{integration_id}",
                integration_id=integration_id,
                event_type=payload.get("event_type", "unknown"),
                payload=payload,
                timestamp=datetime.now()
            )

            self.event_queue.append(event)

            # Process event
            processing_result = await self._process_webhook_event(event)

            # Mark as processed
            event.processed = True

            return {
                "event_id": event.event_id,
                "status": "success",
                "message": "Webhook processed successfully",
                "processing_result": processing_result
            }

        except Exception as e:
            return {
                "error": f"Webhook processing failed: {str(e)}",
                "status": 500,
                "timestamp": datetime.now().isoformat()
            }

    async def get_integration_status(self, integration_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of integrations"""
        try:
            if integration_id:
                integration = self.integrations.get(integration_id)
                if not integration:
                    return {"error": "Integration not found"}

                recent_syncs = [s for s in self.sync_history if s.integration_id == integration_id][-5:]
                recent_events = [e for e in self.event_queue if e.integration_id == integration_id][-10:]

                return {
                    "integration": {
                        "id": integration.integration_id,
                        "name": integration.name,
                        "type": integration.type.value,
                        "status": integration.status.value,
                        "last_sync": integration.last_sync.isoformat() if integration.last_sync else None
                    },
                    "recent_syncs": [{
                        "success": s.success,
                        "items_synced": s.items_synced,
                        "duration": s.duration,
                        "errors": s.errors
                    } for s in recent_syncs],
                    "recent_events": [{
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp.isoformat(),
                        "processed": e.processed
                    } for e in recent_events]
                }
            else:
                # Return all integrations status
                integrations_status = []
                for integration in self.integrations.values():
                    sync_count = len([s for s in self.sync_history if s.integration_id == integration.integration_id])
                    event_count = len([e for e in self.event_queue if e.integration_id == integration.integration_id])

                    integrations_status.append({
                        "id": integration.integration_id,
                        "name": integration.name,
                        "type": integration.type.value,
                        "status": integration.status.value,
                        "last_sync": integration.last_sync.isoformat() if integration.last_sync else None,
                        "sync_count": sync_count,
                        "event_count": event_count
                    })

                return {
                    "total_integrations": len(self.integrations),
                    "active_integrations": len([i for i in self.integrations.values() if i.status == IntegrationStatus.ACTIVE]),
                    "total_syncs": len(self.sync_history),
                    "total_events": len(self.event_queue),
                    "integrations": integrations_status
                }

        except Exception as e:
            return {
                "error": f"Failed to get integration status: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _validate_integration(self, integration: Integration) -> Dict[str, Any]:
        """Validate integration configuration"""
        try:
            if integration.type == IntegrationType.CI_CD:
                return await self._validate_cicd_integration(integration)
            elif integration.type == IntegrationType.MONITORING:
                return await self._validate_monitoring_integration(integration)
            elif integration.type == IntegrationType.COMMUNICATION:
                return await self._validate_communication_integration(integration)
            else:
                # Generic validation
                return {"valid": True, "message": "Integration configuration is valid"}

        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _validate_cicd_integration(self, integration: Integration) -> Dict[str, Any]:
        """Validate CI/CD integration (GitHub, GitLab, Jenkins, etc.)"""
        config = integration.config

        if integration.name.lower() == "github":
            if not config.get("token"):
                return {"valid": False, "error": "GitHub token is required"}

            # Test GitHub API connection
            try:
                headers = {"Authorization": f"token {config['token']}"}
                response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
                if response.status_code == 200:
                    return {"valid": True, "message": "GitHub integration validated"}
                else:
                    return {"valid": False, "error": f"GitHub API error: {response.status_code}"}
            except Exception as e:
                return {"valid": False, "error": f"GitHub connection failed: {str(e)}"}

        elif integration.name.lower() == "jenkins":
            if not config.get("url") or not config.get("username") or not config.get("token"):
                return {"valid": False, "error": "Jenkins URL, username, and token are required"}

            # Test Jenkins connection
            try:
                auth = (config["username"], config["token"])
                response = requests.get(f"{config['url']}/api/json", auth=auth, timeout=10)
                if response.status_code == 200:
                    return {"valid": True, "message": "Jenkins integration validated"}
                else:
                    return {"valid": False, "error": f"Jenkins API error: {response.status_code}"}
            except Exception as e:
                return {"valid": False, "error": f"Jenkins connection failed: {str(e)}"}

        return {"valid": True, "message": "CI/CD integration validated"}

    async def _validate_monitoring_integration(self, integration: Integration) -> Dict[str, Any]:
        """Validate monitoring integration (Datadog, New Relic, etc.)"""
        config = integration.config

        if integration.name.lower() == "datadog":
            if not config.get("api_key") or not config.get("app_key"):
                return {"valid": False, "error": "Datadog API key and App key are required"}

            # Test Datadog API
            try:
                headers = {
                    "DD-API-KEY": config["api_key"],
                    "DD-APPLICATION-KEY": config["app_key"]
                }
                response = requests.get("https://api.datadoghq.com/api/v1/validate", headers=headers, timeout=10)
                if response.status_code == 200:
                    return {"valid": True, "message": "Datadog integration validated"}
                else:
                    return {"valid": False, "error": f"Datadog API error: {response.status_code}"}
            except Exception as e:
                return {"valid": False, "error": f"Datadog connection failed: {str(e)}"}

        return {"valid": True, "message": "Monitoring integration validated"}

    async def _validate_communication_integration(self, integration: Integration) -> Dict[str, Any]:
        """Validate communication integration (Slack, Discord, etc.)"""
        config = integration.config

        if integration.name.lower() == "slack":
            if not config.get("webhook_url") and not config.get("bot_token"):
                return {"valid": False, "error": "Slack webhook URL or bot token is required"}

            # Test Slack webhook or API
            try:
                if config.get("webhook_url"):
                    test_payload = {"text": "API Orchestrator integration test"}
                    response = requests.post(config["webhook_url"], json=test_payload, timeout=10)
                    if response.status_code == 200:
                        return {"valid": True, "message": "Slack webhook validated"}
                    else:
                        return {"valid": False, "error": f"Slack webhook error: {response.status_code}"}
                elif config.get("bot_token"):
                    headers = {"Authorization": f"Bearer {config['bot_token']}"}
                    response = requests.get("https://slack.com/api/auth.test", headers=headers, timeout=10)
                    if response.status_code == 200:
                        return {"valid": True, "message": "Slack bot token validated"}
                    else:
                        return {"valid": False, "error": f"Slack API error: {response.status_code}"}
            except Exception as e:
                return {"valid": False, "error": f"Slack connection failed: {str(e)}"}

        return {"valid": True, "message": "Communication integration validated"}

    async def _perform_sync(self, integration: Integration) -> Dict[str, Any]:
        """Perform synchronization based on integration type"""
        try:
            if integration.type == IntegrationType.CI_CD:
                return await self._sync_cicd_data(integration)
            elif integration.type == IntegrationType.MONITORING:
                return await self._sync_monitoring_data(integration)
            elif integration.type == IntegrationType.PROJECT_MANAGEMENT:
                return await self._sync_project_data(integration)
            else:
                return {"success": True, "items_synced": 0, "message": "No sync required"}

        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _sync_cicd_data(self, integration: Integration) -> Dict[str, Any]:
        """Sync CI/CD pipeline data"""
        try:
            config = integration.config
            synced_items = 0

            if integration.name.lower() == "github":
                # Sync GitHub repository data
                headers = {"Authorization": f"token {config['token']}"}

                # Get repository info
                repo_url = f"https://api.github.com/repos/{config.get('owner', 'user')}/{config.get('repo', 'repo')}"
                response = requests.get(repo_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    repo_data = response.json()
                    synced_items += 1

                    # Get recent commits
                    commits_url = f"{repo_url}/commits"
                    commits_response = requests.get(commits_url, headers=headers, params={"per_page": 10}, timeout=10)

                    if commits_response.status_code == 200:
                        commits = commits_response.json()
                        synced_items += len(commits)

                    # Get workflow runs
                    workflows_url = f"{repo_url}/actions/runs"
                    workflows_response = requests.get(workflows_url, headers=headers, params={"per_page": 10}, timeout=10)

                    if workflows_response.status_code == 200:
                        workflow_runs = workflows_response.json().get("workflow_runs", [])
                        synced_items += len(workflow_runs)

                    return {
                        "success": True,
                        "items_synced": synced_items,
                        "data": {
                            "repository": repo_data,
                            "recent_commits": commits,
                            "workflow_runs": workflow_runs
                        }
                    }

            elif integration.name.lower() == "jenkins":
                # Sync Jenkins build data
                auth = (config["username"], config["token"])
                jobs_url = f"{config['url']}/api/json?tree=jobs[name,url,lastBuild[number,result,timestamp]]"
                response = requests.get(jobs_url, auth=auth, timeout=10)

                if response.status_code == 200:
                    jobs_data = response.json()
                    synced_items = len(jobs_data.get("jobs", []))

                    return {
                        "success": True,
                        "items_synced": synced_items,
                        "data": {"jenkins_jobs": jobs_data.get("jobs", [])}
                    }

            return {"success": True, "items_synced": 0}

        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _sync_monitoring_data(self, integration: Integration) -> Dict[str, Any]:
        """Sync monitoring and observability data"""
        try:
            config = integration.config
            synced_items = 0

            if integration.name.lower() == "datadog":
                headers = {
                    "DD-API-KEY": config["api_key"],
                    "DD-APPLICATION-KEY": config["app_key"]
                }

                # Get metrics
                now = int(time.time())
                one_hour_ago = now - 3600

                metrics_url = "https://api.datadoghq.com/api/v1/query"
                metrics_params = {
                    "query": "avg:system.cpu.user{*}",
                    "from": one_hour_ago,
                    "to": now
                }

                response = requests.get(metrics_url, headers=headers, params=metrics_params, timeout=10)

                if response.status_code == 200:
                    metrics_data = response.json()
                    synced_items += 1

                    return {
                        "success": True,
                        "items_synced": synced_items,
                        "data": {"metrics": metrics_data}
                    }

            return {"success": True, "items_synced": 0}

        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _sync_project_data(self, integration: Integration) -> Dict[str, Any]:
        """Sync project management data (Jira, Trello, etc.)"""
        try:
            config = integration.config
            synced_items = 0

            if integration.name.lower() == "jira":
                # Sync JIRA issues
                auth = (config["email"], config["api_token"])
                base_url = config["base_url"]

                issues_url = f"{base_url}/rest/api/3/search"
                jql_query = "project = {} ORDER BY updated DESC".format(config.get("project_key", "TEST"))

                response = requests.get(
                    issues_url,
                    auth=auth,
                    params={"jql": jql_query, "maxResults": 50},
                    timeout=10
                )

                if response.status_code == 200:
                    issues_data = response.json()
                    synced_items = len(issues_data.get("issues", []))

                    return {
                        "success": True,
                        "items_synced": synced_items,
                        "data": {"jira_issues": issues_data.get("issues", [])}
                    }

            return {"success": True, "items_synced": 0}

        except Exception as e:
            return {"success": False, "errors": [str(e)]}

    async def _setup_webhook_handler(self, integration: Integration) -> None:
        """Set up webhook handler for integration"""
        self.webhook_handlers[integration.integration_id] = {
            "url": integration.webhook_url,
            "secret": integration.config.get("webhook_secret"),
            "events": integration.config.get("webhook_events", [])
        }

    async def _process_webhook_event(self, event: IntegrationEvent) -> Dict[str, Any]:
        """Process incoming webhook event"""
        try:
            processing_result = {"actions": [], "notifications": []}

            # GitHub webhook events
            if event.event_type in ["push", "pull_request", "issues"]:
                processing_result["actions"].append(f"Processed {event.event_type} event")

                # Example: Trigger API tests on push
                if event.event_type == "push":
                    processing_result["actions"].append("Triggered API test suite")

                # Example: Update documentation on PR
                if event.event_type == "pull_request":
                    processing_result["actions"].append("Updated API documentation")

            # Jenkins webhook events
            elif event.event_type in ["build_started", "build_completed"]:
                processing_result["actions"].append(f"Processed {event.event_type} event")

                if event.event_type == "build_completed":
                    build_result = event.payload.get("result", "unknown")
                    processing_result["notifications"].append(f"Build {build_result}")

            # Monitoring alerts
            elif event.event_type in ["alert_triggered", "metric_threshold"]:
                processing_result["actions"].append("Processed monitoring alert")
                processing_result["notifications"].append("Alert notification sent")

            return processing_result

        except Exception as e:
            return {"error": f"Event processing failed: {str(e)}"}

    def _verify_webhook_signature(self, payload: Dict[str, Any], headers: Dict[str, str], secret: str) -> bool:
        """Verify webhook signature for security"""
        try:
            signature = headers.get("X-Hub-Signature-256") or headers.get("X-Signature")
            if not signature:
                return False

            payload_str = json.dumps(payload, separators=(',', ':'))
            expected_signature = hmac.new(
                secret.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, f"sha256={expected_signature}")

        except Exception:
            return False

    async def get_integration_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for new integrations"""
        try:
            current_types = set(integration.type for integration in self.integrations.values())

            recommendations = []

            # Recommend missing essential integrations
            if IntegrationType.CI_CD not in current_types:
                recommendations.append({
                    "type": "ci_cd",
                    "title": "Add CI/CD Integration",
                    "description": "Connect with GitHub, GitLab, or Jenkins for automated testing",
                    "benefits": ["Automated API testing", "Deployment notifications", "Code quality monitoring"],
                    "priority": "high"
                })

            if IntegrationType.MONITORING not in current_types:
                recommendations.append({
                    "type": "monitoring",
                    "title": "Add Monitoring Integration",
                    "description": "Connect with Datadog, New Relic, or Prometheus for observability",
                    "benefits": ["Real-time performance monitoring", "Alert management", "SLA tracking"],
                    "priority": "high"
                })

            if IntegrationType.COMMUNICATION not in current_types:
                recommendations.append({
                    "type": "communication",
                    "title": "Add Team Communication",
                    "description": "Connect with Slack, Discord, or Microsoft Teams",
                    "benefits": ["Instant notifications", "Team collaboration", "Alert routing"],
                    "priority": "medium"
                })

            # Performance-based recommendations
            if len(self.integrations) > 0:
                sync_failures = [s for s in self.sync_history if not s.success]
                if len(sync_failures) > 5:
                    recommendations.append({
                        "type": "reliability",
                        "title": "Improve Integration Reliability",
                        "description": "Several integrations have sync failures",
                        "benefits": ["Better data consistency", "Reduced manual intervention", "Improved automation"],
                        "priority": "medium"
                    })

            return {
                "recommendations": recommendations,
                "current_integrations": len(self.integrations),
                "coverage_score": self._calculate_integration_coverage_score(),
                "suggested_next_steps": [
                    "🔗 Connect essential tools for your workflow",
                    "📊 Set up monitoring and alerting",
                    "🤖 Enable automation for repetitive tasks",
                    "📢 Configure team notifications"
                ]
            }

        except Exception as e:
            return {
                "error": f"Failed to generate recommendations: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    def _calculate_integration_coverage_score(self) -> int:
        """Calculate integration coverage score (0-100)"""
        essential_types = [
            IntegrationType.CI_CD,
            IntegrationType.MONITORING,
            IntegrationType.COMMUNICATION,
            IntegrationType.TESTING
        ]

        current_types = set(integration.type for integration in self.integrations.values() if integration.status == IntegrationStatus.ACTIVE)
        coverage = len(current_types.intersection(essential_types)) / len(essential_types)

        return int(coverage * 100)

    async def cleanup_old_events(self, days: int = 7) -> Dict[str, Any]:
        """Clean up old events and sync history"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            # Clean up old events
            old_events = [e for e in self.event_queue if e.timestamp < cutoff_date]
            self.event_queue = [e for e in self.event_queue if e.timestamp >= cutoff_date]

            # Clean up old sync history (keep last 100 records per integration)
            for integration_id in self.integrations.keys():
                integration_syncs = [s for s in self.sync_history if s.integration_id == integration_id]
                if len(integration_syncs) > 100:
                    # Keep only the latest 100
                    integration_syncs.sort(key=lambda x: x.duration, reverse=True)
                    to_remove = integration_syncs[100:]
                    for sync in to_remove:
                        self.sync_history.remove(sync)

            return {
                "events_cleaned": len(old_events),
                "remaining_events": len(self.event_queue),
                "remaining_sync_records": len(self.sync_history),
                "cleanup_date": cutoff_date.isoformat()
            }

        except Exception as e:
            return {
                "error": f"Cleanup failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# Usage example and testing
if __name__ == "__main__":
    async def test_integration_agent():
        agent = IntegrationAgent()

        # Add GitHub integration
        github_config = {
            "id": "github_main",
            "name": "GitHub",
            "type": "ci_cd",
            "config": {
                "token": "ghp_example_token",
                "owner": "myorg",
                "repo": "myrepo"
            },
            "webhook_url": "https://api.example.com/webhooks/github"
        }

        result = await agent.add_integration(github_config)
        print("GitHub Integration:", json.dumps(result, indent=2))

        # Add Slack integration
        slack_config = {
            "id": "slack_main",
            "name": "Slack",
            "type": "communication",
            "config": {
                "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
            }
        }

        result = await agent.add_integration(slack_config)
        print("\nSlack Integration:", json.dumps(result, indent=2))

        # Get integration status
        status = await agent.get_integration_status()
        print("\nIntegration Status:", json.dumps(status, indent=2))

        # Get recommendations
        recommendations = await agent.get_integration_recommendations()
        print("\nRecommendations:", json.dumps(recommendations, indent=2))

    # Run test
    asyncio.run(test_integration_agent())