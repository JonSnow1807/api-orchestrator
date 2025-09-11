"""
Native Integrations - Connect with popular tools
Jira, Slack, Teams, GitHub, Confluence, DataDog, PagerDuty
"""

import aiohttp
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
import hmac

class IntegrationType(Enum):
    """Supported integration types"""
    JIRA = "jira"
    SLACK = "slack"
    TEAMS = "teams"
    GITHUB = "github"
    GITLAB = "gitlab"
    CONFLUENCE = "confluence"
    DATADOG = "datadog"
    PAGERDUTY = "pagerduty"
    NEWRELIC = "newrelic"
    DISCORD = "discord"
    WEBHOOK = "webhook"

class IntegrationStatus(Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTHENTICATING = "authenticating"

class EventType(Enum):
    """Events that trigger integrations"""
    API_CREATED = "api_created"
    API_UPDATED = "api_updated"
    API_DELETED = "api_deleted"
    TEST_FAILED = "test_failed"
    TEST_PASSED = "test_passed"
    SECURITY_ALERT = "security_alert"
    PERFORMANCE_ALERT = "performance_alert"
    SLA_VIOLATION = "sla_violation"
    DEPLOYMENT = "deployment"
    COMMENT_ADDED = "comment_added"
    REVIEW_REQUESTED = "review_requested"

class Integration(BaseModel):
    """Integration configuration"""
    id: str = Field(default_factory=lambda: hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16])
    type: IntegrationType
    name: str
    workspace_id: str
    
    # Connection details
    base_url: str
    auth_type: str  # oauth2, api_key, basic, token
    credentials: Dict[str, Any]  # Encrypted in production
    
    # Configuration
    enabled: bool = True
    events: List[EventType] = []  # Events to listen for
    settings: Dict[str, Any] = {}  # Integration-specific settings
    
    # Mapping
    field_mappings: Dict[str, str] = {}  # Our field -> Their field
    
    # Status
    status: IntegrationStatus = IntegrationStatus.DISCONNECTED
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class JiraIntegration:
    """Jira integration handler"""
    
    def __init__(self, config: Integration):
        self.config = config
        self.session = None
        
    async def connect(self) -> bool:
        """Establish Jira connection"""
        try:
            self.session = aiohttp.ClientSession()
            
            # Test connection
            headers = self._get_headers()
            async with self.session.get(
                f"{self.config.base_url}/rest/api/3/myself",
                headers=headers
            ) as response:
                if response.status == 200:
                    self.config.status = IntegrationStatus.CONNECTED
                    return True
                else:
                    self.config.status = IntegrationStatus.ERROR
                    self.config.error_message = f"Connection failed: {response.status}"
                    return False
                    
        except Exception as e:
            self.config.status = IntegrationStatus.ERROR
            self.config.error_message = str(e)
            return False
    
    async def create_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str,
        priority: str = "Medium",
        labels: List[str] = None,
        custom_fields: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create Jira issue"""
        
        issue_data = {
            "fields": {
                "project": {"key": project_key},
                "issuetype": {"name": issue_type},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": description
                                }
                            ]
                        }
                    ]
                },
                "priority": {"name": priority}
            }
        }
        
        if labels:
            issue_data["fields"]["labels"] = labels
            
        if custom_fields:
            issue_data["fields"].update(custom_fields)
        
        headers = self._get_headers()
        
        async with self.session.post(
            f"{self.config.base_url}/rest/api/3/issue",
            headers=headers,
            json=issue_data
        ) as response:
            if response.status == 201:
                data = await response.json()
                return {
                    "success": True,
                    "issue_key": data["key"],
                    "issue_id": data["id"],
                    "url": f"{self.config.base_url}/browse/{data['key']}"
                }
            else:
                error = await response.text()
                return {
                    "success": False,
                    "error": error
                }
    
    async def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any]
    ) -> bool:
        """Update Jira issue"""
        
        update_data = {"fields": fields}
        headers = self._get_headers()
        
        async with self.session.put(
            f"{self.config.base_url}/rest/api/3/issue/{issue_key}",
            headers=headers,
            json=update_data
        ) as response:
            return response.status == 204
    
    async def add_comment(
        self,
        issue_key: str,
        comment: str
    ) -> bool:
        """Add comment to Jira issue"""
        
        comment_data = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        
        headers = self._get_headers()
        
        async with self.session.post(
            f"{self.config.base_url}/rest/api/3/issue/{issue_key}/comment",
            headers=headers,
            json=comment_data
        ) as response:
            return response.status == 201
    
    async def search_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Search Jira issues"""
        
        headers = self._get_headers()
        params = {
            "jql": jql,
            "maxResults": max_results
        }
        
        async with self.session.get(
            f"{self.config.base_url}/rest/api/3/search",
            headers=headers,
            params=params
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("issues", [])
            return []
    
    def _get_headers(self) -> Dict[str, str]:
        """Get Jira API headers"""
        
        if self.config.auth_type == "basic":
            import base64
            auth = base64.b64encode(
                f"{self.config.credentials['email']}:{self.config.credentials['api_token']}".encode()
            ).decode()
            return {
                "Authorization": f"Basic {auth}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif self.config.auth_type == "oauth2":
            return {
                "Authorization": f"Bearer {self.config.credentials['access_token']}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        return {}
    
    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()

class SlackIntegration:
    """Slack integration handler"""
    
    def __init__(self, config: Integration):
        self.config = config
        self.webhook_url = config.credentials.get("webhook_url")
        self.bot_token = config.credentials.get("bot_token")
        
    async def send_message(
        self,
        channel: str,
        text: str,
        blocks: List[Dict[str, Any]] = None,
        attachments: List[Dict[str, Any]] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """Send message to Slack"""
        
        # Use webhook for simple messages
        if self.webhook_url and not thread_ts:
            return await self._send_webhook(text, blocks, attachments)
        
        # Use API for advanced features
        if self.bot_token:
            return await self._send_api_message(channel, text, blocks, attachments, thread_ts)
        
        return False
    
    async def _send_webhook(
        self,
        text: str,
        blocks: List[Dict[str, Any]] = None,
        attachments: List[Dict[str, Any]] = None
    ) -> bool:
        """Send via webhook"""
        
        payload = {"text": text}
        
        if blocks:
            payload["blocks"] = blocks
        
        if attachments:
            payload["attachments"] = attachments
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=payload
            ) as response:
                return response.status == 200
    
    async def _send_api_message(
        self,
        channel: str,
        text: str,
        blocks: List[Dict[str, Any]] = None,
        attachments: List[Dict[str, Any]] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """Send via Slack API"""
        
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": channel,
            "text": text
        }
        
        if blocks:
            payload["blocks"] = blocks
        
        if attachments:
            payload["attachments"] = attachments
        
        if thread_ts:
            payload["thread_ts"] = thread_ts
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://slack.com/api/chat.postMessage",
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                return data.get("ok", False)
    
    async def create_alert_message(
        self,
        title: str,
        description: str,
        severity: str,
        details: Dict[str, Any],
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create formatted alert message"""
        
        color = {
            "critical": "danger",
            "high": "warning",
            "medium": "#FFA500",
            "low": "good"
        }.get(severity.lower(), "#808080")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": description
                }
            }
        ]
        
        # Add details
        if details:
            fields = []
            for key, value in details.items():
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}"
                })
            
            blocks.append({
                "type": "section",
                "fields": fields
            })
        
        # Add action button
        if action_url:
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details"
                        },
                        "url": action_url,
                        "style": "primary"
                    }
                ]
            })
        
        attachments = [
            {
                "color": color,
                "fallback": f"{title}: {description}"
            }
        ]
        
        return {
            "blocks": blocks,
            "attachments": attachments
        }

class TeamsIntegration:
    """Microsoft Teams integration handler"""
    
    def __init__(self, config: Integration):
        self.config = config
        self.webhook_url = config.credentials.get("webhook_url")
        
    async def send_message(
        self,
        title: str,
        text: str,
        sections: List[Dict[str, Any]] = None,
        actions: List[Dict[str, Any]] = None,
        theme_color: str = "0076D7"
    ) -> bool:
        """Send message to Teams"""
        
        card = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title,
            "title": title,
            "text": text
        }
        
        if sections:
            card["sections"] = sections
        
        if actions:
            card["potentialAction"] = actions
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=card
            ) as response:
                return response.status == 200
    
    async def create_alert_card(
        self,
        title: str,
        description: str,
        severity: str,
        details: Dict[str, Any],
        action_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create formatted alert card"""
        
        theme_color = {
            "critical": "FF0000",
            "high": "FFA500",
            "medium": "FFFF00",
            "low": "00FF00"
        }.get(severity.lower(), "808080")
        
        sections = [
            {
                "activityTitle": "Alert Details",
                "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "facts": [
                    {
                        "name": key,
                        "value": str(value)
                    }
                    for key, value in details.items()
                ],
                "markdown": True
            }
        ]
        
        actions = []
        if action_url:
            actions.append({
                "@type": "OpenUri",
                "name": "View Details",
                "targets": [
                    {
                        "os": "default",
                        "uri": action_url
                    }
                ]
            })
        
        return {
            "title": f"🚨 {title}",
            "text": description,
            "sections": sections,
            "actions": actions,
            "theme_color": theme_color
        }

class GitHubIntegration:
    """GitHub integration handler"""
    
    def __init__(self, config: Integration):
        self.config = config
        self.token = config.credentials.get("token")
        self.base_url = "https://api.github.com"
        
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: List[str] = None,
        assignees: List[str] = None,
        milestone: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create GitHub issue"""
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        issue_data = {
            "title": title,
            "body": body
        }
        
        if labels:
            issue_data["labels"] = labels
        
        if assignees:
            issue_data["assignees"] = assignees
        
        if milestone:
            issue_data["milestone"] = milestone
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/repos/{owner}/{repo}/issues",
                headers=headers,
                json=issue_data
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    return {
                        "success": True,
                        "issue_number": data["number"],
                        "url": data["html_url"]
                    }
                else:
                    error = await response.text()
                    return {
                        "success": False,
                        "error": error
                    }
    
    async def create_pull_request_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        commit_id: Optional[str] = None,
        path: Optional[str] = None,
        line: Optional[int] = None
    ) -> bool:
        """Create PR comment"""
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        if path and line:
            # Review comment on specific line
            comment_data = {
                "body": body,
                "commit_id": commit_id,
                "path": path,
                "line": line
            }
            url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        else:
            # Issue comment on PR
            comment_data = {"body": body}
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=comment_data
            ) as response:
                return response.status == 201
    
    async def update_commit_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,  # error, failure, pending, success
        target_url: Optional[str] = None,
        description: Optional[str] = None,
        context: str = "api-orchestrator"
    ) -> bool:
        """Update commit status"""
        
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        status_data = {
            "state": state,
            "context": context
        }
        
        if target_url:
            status_data["target_url"] = target_url
        
        if description:
            status_data["description"] = description[:140]  # GitHub limit
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/repos/{owner}/{repo}/statuses/{sha}",
                headers=headers,
                json=status_data
            ) as response:
                return response.status == 201

class DataDogIntegration:
    """DataDog integration handler"""
    
    def __init__(self, config: Integration):
        self.config = config
        self.api_key = config.credentials.get("api_key")
        self.app_key = config.credentials.get("app_key")
        self.base_url = "https://api.datadoghq.com/api/v1"
        
    async def send_metric(
        self,
        metric_name: str,
        value: float,
        tags: List[str] = None,
        metric_type: str = "gauge"  # gauge, rate, count
    ) -> bool:
        """Send metric to DataDog"""
        
        headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json"
        }
        
        timestamp = int(datetime.now().timestamp())
        
        series = {
            "series": [
                {
                    "metric": metric_name,
                    "type": metric_type,
                    "points": [[timestamp, value]],
                    "tags": tags or []
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/series",
                headers=headers,
                json=series
            ) as response:
                return response.status == 202
    
    async def create_event(
        self,
        title: str,
        text: str,
        alert_type: str = "info",  # error, warning, info, success
        tags: List[str] = None,
        aggregation_key: Optional[str] = None
    ) -> bool:
        """Create DataDog event"""
        
        headers = {
            "DD-API-KEY": self.api_key,
            "DD-APPLICATION-KEY": self.app_key,
            "Content-Type": "application/json"
        }
        
        event_data = {
            "title": title,
            "text": text,
            "alert_type": alert_type,
            "tags": tags or []
        }
        
        if aggregation_key:
            event_data["aggregation_key"] = aggregation_key
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/events",
                headers=headers,
                json=event_data
            ) as response:
                return response.status == 202

class PagerDutyIntegration:
    """PagerDuty integration handler"""
    
    def __init__(self, config: Integration):
        self.config = config
        self.integration_key = config.credentials.get("integration_key")
        self.api_key = config.credentials.get("api_key")
        
    async def trigger_incident(
        self,
        summary: str,
        source: str,
        severity: str = "error",  # critical, error, warning, info
        component: Optional[str] = None,
        group: Optional[str] = None,
        custom_details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Trigger PagerDuty incident"""
        
        event_data = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "payload": {
                "summary": summary,
                "source": source,
                "severity": severity
            }
        }
        
        if component:
            event_data["payload"]["component"] = component
        
        if group:
            event_data["payload"]["group"] = group
        
        if custom_details:
            event_data["payload"]["custom_details"] = custom_details
        
        # Generate dedup key
        dedup_key = hashlib.sha256(
            f"{summary}{source}{component}".encode()
        ).hexdigest()
        event_data["dedup_key"] = dedup_key
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=event_data
            ) as response:
                if response.status == 202:
                    data = await response.json()
                    return {
                        "success": True,
                        "dedup_key": dedup_key,
                        "message": data.get("message")
                    }
                else:
                    error = await response.text()
                    return {
                        "success": False,
                        "error": error
                    }
    
    async def resolve_incident(self, dedup_key: str) -> bool:
        """Resolve PagerDuty incident"""
        
        event_data = {
            "routing_key": self.integration_key,
            "event_action": "resolve",
            "dedup_key": dedup_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=event_data
            ) as response:
                return response.status == 202

class IntegrationManager:
    """Manage all integrations"""
    
    def __init__(self):
        self.integrations: Dict[str, Integration] = {}
        self.handlers: Dict[str, Any] = {}
        
    async def add_integration(
        self,
        integration: Integration
    ) -> Integration:
        """Add new integration"""
        
        self.integrations[integration.id] = integration
        
        # Initialize handler
        handler = await self._create_handler(integration)
        if handler:
            self.handlers[integration.id] = handler
            
            # Test connection
            if hasattr(handler, 'connect'):
                connected = await handler.connect()
                integration.status = IntegrationStatus.CONNECTED if connected else IntegrationStatus.ERROR
        
        return integration
    
    async def remove_integration(self, integration_id: str):
        """Remove integration"""
        
        if integration_id in self.handlers:
            handler = self.handlers[integration_id]
            if hasattr(handler, 'disconnect'):
                await handler.disconnect()
            del self.handlers[integration_id]
        
        if integration_id in self.integrations:
            del self.integrations[integration_id]
    
    async def handle_event(
        self,
        event_type: EventType,
        event_data: Dict[str, Any]
    ):
        """Handle event and trigger integrations"""
        
        for integration in self.integrations.values():
            if not integration.enabled:
                continue
            
            if event_type not in integration.events:
                continue
            
            handler = self.handlers.get(integration.id)
            if not handler:
                continue
            
            # Route to appropriate handler method
            await self._route_event(handler, integration, event_type, event_data)
    
    async def _create_handler(self, integration: Integration) -> Any:
        """Create handler for integration type"""
        
        handlers = {
            IntegrationType.JIRA: JiraIntegration,
            IntegrationType.SLACK: SlackIntegration,
            IntegrationType.TEAMS: TeamsIntegration,
            IntegrationType.GITHUB: GitHubIntegration,
            IntegrationType.DATADOG: DataDogIntegration,
            IntegrationType.PAGERDUTY: PagerDutyIntegration
        }
        
        handler_class = handlers.get(integration.type)
        if handler_class:
            return handler_class(integration)
        
        return None
    
    async def _route_event(
        self,
        handler: Any,
        integration: Integration,
        event_type: EventType,
        event_data: Dict[str, Any]
    ):
        """Route event to appropriate handler method"""
        
        try:
            if integration.type == IntegrationType.SLACK:
                await self._handle_slack_event(handler, event_type, event_data, integration.settings)
            elif integration.type == IntegrationType.JIRA:
                await self._handle_jira_event(handler, event_type, event_data, integration.settings)
            elif integration.type == IntegrationType.TEAMS:
                await self._handle_teams_event(handler, event_type, event_data, integration.settings)
            elif integration.type == IntegrationType.GITHUB:
                await self._handle_github_event(handler, event_type, event_data, integration.settings)
            elif integration.type == IntegrationType.DATADOG:
                await self._handle_datadog_event(handler, event_type, event_data, integration.settings)
            elif integration.type == IntegrationType.PAGERDUTY:
                await self._handle_pagerduty_event(handler, event_type, event_data, integration.settings)
        except Exception as e:
            print(f"Integration error for {integration.name}: {e}")
    
    async def _handle_slack_event(
        self,
        handler: SlackIntegration,
        event_type: EventType,
        event_data: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """Handle Slack events"""
        
        channel = settings.get("channel", "#api-alerts")
        
        if event_type == EventType.TEST_FAILED:
            message = await handler.create_alert_message(
                title="API Test Failed",
                description=f"Test '{event_data['test_name']}' failed",
                severity="high",
                details={
                    "API": event_data.get("api_name"),
                    "Endpoint": event_data.get("endpoint"),
                    "Error": event_data.get("error")
                },
                action_url=event_data.get("url")
            )
            await handler.send_message(channel, "API Test Failed", **message)
            
        elif event_type == EventType.SECURITY_ALERT:
            message = await handler.create_alert_message(
                title="Security Alert",
                description=event_data.get("description"),
                severity="critical",
                details=event_data.get("details", {}),
                action_url=event_data.get("url")
            )
            await handler.send_message(channel, "Security Alert", **message)
    
    async def _handle_jira_event(
        self,
        handler: JiraIntegration,
        event_type: EventType,
        event_data: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """Handle Jira events"""
        
        project_key = settings.get("project_key")
        
        if event_type == EventType.TEST_FAILED:
            await handler.create_issue(
                project_key=project_key,
                issue_type="Bug",
                summary=f"API Test Failed: {event_data['test_name']}",
                description=f"Test failed for {event_data.get('api_name')}\n\n{event_data.get('error')}",
                priority="High",
                labels=["api-test", "automated"]
            )
        
        elif event_type == EventType.SECURITY_ALERT:
            await handler.create_issue(
                project_key=project_key,
                issue_type="Bug",
                summary=f"Security Alert: {event_data.get('title')}",
                description=event_data.get("description"),
                priority="Critical",
                labels=["security", "automated"]
            )
    
    async def _handle_teams_event(
        self,
        handler: TeamsIntegration,
        event_type: EventType,
        event_data: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """Handle Teams events"""
        
        if event_type in [EventType.TEST_FAILED, EventType.SECURITY_ALERT, EventType.SLA_VIOLATION]:
            severity = "critical" if event_type == EventType.SECURITY_ALERT else "high"
            
            card = await handler.create_alert_card(
                title=event_data.get("title", str(event_type.value)),
                description=event_data.get("description", ""),
                severity=severity,
                details=event_data.get("details", {}),
                action_url=event_data.get("url")
            )
            
            await handler.send_message(**card)
    
    async def _handle_github_event(
        self,
        handler: GitHubIntegration,
        event_type: EventType,
        event_data: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """Handle GitHub events"""
        
        owner = settings.get("owner")
        repo = settings.get("repo")
        
        if event_type == EventType.TEST_FAILED and event_data.get("commit_sha"):
            await handler.update_commit_status(
                owner=owner,
                repo=repo,
                sha=event_data["commit_sha"],
                state="failure",
                description=f"API test failed: {event_data['test_name']}",
                target_url=event_data.get("url")
            )
        
        elif event_type == EventType.TEST_PASSED and event_data.get("commit_sha"):
            await handler.update_commit_status(
                owner=owner,
                repo=repo,
                sha=event_data["commit_sha"],
                state="success",
                description="All API tests passed",
                target_url=event_data.get("url")
            )
    
    async def _handle_datadog_event(
        self,
        handler: DataDogIntegration,
        event_type: EventType,
        event_data: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """Handle DataDog events"""
        
        tags = settings.get("tags", [])
        
        if event_type == EventType.PERFORMANCE_ALERT:
            await handler.send_metric(
                metric_name="api.response_time",
                value=event_data.get("response_time", 0),
                tags=tags + [f"endpoint:{event_data.get('endpoint')}"],
                metric_type="gauge"
            )
            
            await handler.create_event(
                title="Performance Alert",
                text=event_data.get("description"),
                alert_type="warning",
                tags=tags
            )
        
        elif event_type == EventType.SLA_VIOLATION:
            await handler.create_event(
                title="SLA Violation",
                text=event_data.get("description"),
                alert_type="error",
                tags=tags + ["sla_violation"]
            )
    
    async def _handle_pagerduty_event(
        self,
        handler: PagerDutyIntegration,
        event_type: EventType,
        event_data: Dict[str, Any],
        settings: Dict[str, Any]
    ):
        """Handle PagerDuty events"""
        
        if event_type in [EventType.SECURITY_ALERT, EventType.SLA_VIOLATION]:
            severity = "critical" if event_type == EventType.SECURITY_ALERT else "error"
            
            await handler.trigger_incident(
                summary=event_data.get("title", str(event_type.value)),
                source="api-orchestrator",
                severity=severity,
                component=event_data.get("api_name"),
                custom_details=event_data.get("details", {})
            )
        
        elif event_type == EventType.TEST_PASSED and event_data.get("dedup_key"):
            # Resolve incident if test passes
            await handler.resolve_incident(event_data["dedup_key"])

# Global integration manager
integration_manager = IntegrationManager()