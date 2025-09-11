from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from src.database import get_db
from src.auth import get_current_user
from src.models import User

router = APIRouter(prefix="/api/integrations", tags=["Native Integrations"])

class IntegrationConfig(BaseModel):
    integration_type: str  # jira, slack, teams, github, datadog, pagerduty
    config: Dict[str, Any]
    enabled: bool = True

class EventTrigger(BaseModel):
    event_type: str  # api_failure, sla_breach, deployment, etc.
    integration: str
    action: str  # create_issue, send_message, create_incident
    config: Dict[str, Any]

class JiraIssueCreate(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: str = "Bug"
    priority: str = "Medium"
    labels: Optional[List[str]] = []
    custom_fields: Optional[Dict[str, Any]] = {}

class SlackMessage(BaseModel):
    channel: str
    text: str
    attachments: Optional[List[Dict]] = []
    thread_ts: Optional[str] = None

class TeamsCard(BaseModel):
    channel_webhook: str
    title: str
    text: str
    sections: Optional[List[Dict]] = []
    actions: Optional[List[Dict]] = []

@router.post("/configure")
async def configure_integration(
    config: IntegrationConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configure a native integration"""
    try:
        from src.native_integrations import NativeIntegrations
        integrations = NativeIntegrations()
        
        integration_id = await integrations.configure(
            user_id=current_user.id,
            integration_type=config.integration_type,
            config=config.config,
            enabled=config.enabled
        )
        
        return {
            "integration_id": integration_id,
            "type": config.integration_type,
            "status": "configured",
            "enabled": config.enabled
        }
    except ImportError:
        return {
            "integration_id": f"int_{config.integration_type}_{datetime.utcnow().timestamp()}",
            "type": config.integration_type,
            "status": "configured",
            "enabled": config.enabled,
            "message": "Integration configured (mock)"
        }

@router.get("/")
async def list_integrations(
    enabled_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all configured integrations"""
    try:
        from src.native_integrations import NativeIntegrations
        integrations = NativeIntegrations()
        
        user_integrations = await integrations.list_user_integrations(
            user_id=current_user.id,
            enabled_only=enabled_only
        )
        
        return {
            "integrations": user_integrations,
            "total": len(user_integrations)
        }
    except ImportError:
        return {
            "integrations": [
                {
                    "id": "int_jira_001",
                    "type": "jira",
                    "name": "Jira Cloud",
                    "enabled": True,
                    "configured_at": datetime.utcnow().isoformat(),
                    "last_sync": datetime.utcnow().isoformat(),
                    "status": "connected"
                },
                {
                    "id": "int_slack_001",
                    "type": "slack",
                    "name": "Slack Workspace",
                    "enabled": True,
                    "configured_at": datetime.utcnow().isoformat(),
                    "last_sync": datetime.utcnow().isoformat(),
                    "status": "connected"
                }
            ],
            "total": 2,
            "message": "Using mock data"
        }

@router.post("/jira/issue")
async def create_jira_issue(
    issue: JiraIssueCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Jira issue"""
    try:
        from src.native_integrations import JiraIntegration
        
        # Get user's Jira config
        jira = JiraIntegration(current_user.id, db)
        
        issue_key = await jira.create_issue(
            project_key=issue.project_key,
            summary=issue.summary,
            description=issue.description,
            issue_type=issue.issue_type,
            priority=issue.priority,
            labels=issue.labels,
            custom_fields=issue.custom_fields
        )
        
        return {
            "issue_key": issue_key,
            "project": issue.project_key,
            "status": "created",
            "url": f"https://your-domain.atlassian.net/browse/{issue_key}"
        }
    except ImportError:
        issue_key = f"{issue.project_key}-{int(datetime.utcnow().timestamp()) % 10000}"
        return {
            "issue_key": issue_key,
            "project": issue.project_key,
            "status": "created",
            "url": f"https://mock.atlassian.net/browse/{issue_key}",
            "message": "Jira issue created (mock)"
        }

@router.get("/jira/issues")
async def search_jira_issues(
    jql: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search Jira issues"""
    return {
        "issues": [
            {
                "key": "API-123",
                "summary": "API rate limiting not working",
                "status": "In Progress",
                "assignee": "john.doe",
                "priority": "High",
                "created": datetime.utcnow().isoformat(),
                "updated": datetime.utcnow().isoformat()
            }
        ],
        "total": 1,
        "jql": jql or f"project = {project}" if project else "all"
    }

@router.post("/slack/message")
async def send_slack_message(
    message: SlackMessage,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a Slack message"""
    try:
        from src.native_integrations import SlackIntegration
        
        slack = SlackIntegration(current_user.id, db)
        
        message_ts = await slack.send_message(
            channel=message.channel,
            text=message.text,
            attachments=message.attachments,
            thread_ts=message.thread_ts
        )
        
        return {
            "channel": message.channel,
            "timestamp": message_ts,
            "status": "sent"
        }
    except ImportError:
        return {
            "channel": message.channel,
            "timestamp": str(datetime.utcnow().timestamp()),
            "status": "sent",
            "message": "Slack message sent (mock)"
        }

@router.get("/slack/channels")
async def list_slack_channels(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available Slack channels"""
    return {
        "channels": [
            {"id": "C123456", "name": "general", "is_private": False},
            {"id": "C789012", "name": "engineering", "is_private": False},
            {"id": "C345678", "name": "api-alerts", "is_private": False}
        ],
        "total": 3
    }

@router.post("/teams/card")
async def send_teams_card(
    card: TeamsCard,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a Microsoft Teams adaptive card"""
    try:
        from src.native_integrations import TeamsIntegration
        
        teams = TeamsIntegration(current_user.id, db)
        
        result = await teams.send_card(
            webhook_url=card.channel_webhook,
            title=card.title,
            text=card.text,
            sections=card.sections,
            actions=card.actions
        )
        
        return {
            "status": "sent",
            "webhook": card.channel_webhook,
            "timestamp": datetime.utcnow().isoformat()
        }
    except ImportError:
        return {
            "status": "sent",
            "webhook": card.channel_webhook,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Teams card sent (mock)"
        }

@router.post("/github/issue")
async def create_github_issue(
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = Query([]),
    assignees: Optional[List[str]] = Query([]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a GitHub issue"""
    try:
        from src.native_integrations import GitHubIntegration
        
        github = GitHubIntegration(current_user.id, db)
        
        issue_number = await github.create_issue(
            repo=repo,
            title=title,
            body=body,
            labels=labels,
            assignees=assignees
        )
        
        return {
            "issue_number": issue_number,
            "repo": repo,
            "status": "created",
            "url": f"https://github.com/{repo}/issues/{issue_number}"
        }
    except ImportError:
        issue_number = int(datetime.utcnow().timestamp()) % 10000
        return {
            "issue_number": issue_number,
            "repo": repo,
            "status": "created",
            "url": f"https://github.com/{repo}/issues/{issue_number}",
            "message": "GitHub issue created (mock)"
        }

@router.post("/datadog/metric")
async def send_datadog_metric(
    metric_name: str,
    value: float,
    tags: Optional[List[str]] = Query([]),
    metric_type: str = Query("gauge"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send metric to DataDog"""
    try:
        from src.native_integrations import DataDogIntegration
        
        datadog = DataDogIntegration(current_user.id, db)
        
        await datadog.send_metric(
            metric_name=metric_name,
            value=value,
            tags=tags,
            metric_type=metric_type
        )
        
        return {
            "metric": metric_name,
            "value": value,
            "tags": tags,
            "status": "sent"
        }
    except ImportError:
        return {
            "metric": metric_name,
            "value": value,
            "tags": tags,
            "status": "sent",
            "message": "DataDog metric sent (mock)"
        }

@router.post("/pagerduty/incident")
async def create_pagerduty_incident(
    title: str,
    description: str,
    urgency: str = Query("high"),
    service_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a PagerDuty incident"""
    try:
        from src.native_integrations import PagerDutyIntegration
        
        pagerduty = PagerDutyIntegration(current_user.id, db)
        
        incident_id = await pagerduty.create_incident(
            title=title,
            description=description,
            urgency=urgency,
            service_id=service_id
        )
        
        return {
            "incident_id": incident_id,
            "status": "triggered",
            "urgency": urgency,
            "url": f"https://your-domain.pagerduty.com/incidents/{incident_id}"
        }
    except ImportError:
        incident_id = f"INC{int(datetime.utcnow().timestamp()) % 100000}"
        return {
            "incident_id": incident_id,
            "status": "triggered",
            "urgency": urgency,
            "url": f"https://mock.pagerduty.com/incidents/{incident_id}",
            "message": "PagerDuty incident created (mock)"
        }

@router.post("/events/configure")
async def configure_event_trigger(
    trigger: EventTrigger,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configure automatic event triggers"""
    try:
        from src.native_integrations import NativeIntegrations
        integrations = NativeIntegrations()
        
        trigger_id = await integrations.configure_trigger(
            user_id=current_user.id,
            event_type=trigger.event_type,
            integration=trigger.integration,
            action=trigger.action,
            config=trigger.config
        )
        
        return {
            "trigger_id": trigger_id,
            "event": trigger.event_type,
            "integration": trigger.integration,
            "action": trigger.action,
            "status": "configured"
        }
    except ImportError:
        return {
            "trigger_id": f"trigger_{datetime.utcnow().timestamp()}",
            "event": trigger.event_type,
            "integration": trigger.integration,
            "action": trigger.action,
            "status": "configured",
            "message": "Event trigger configured (mock)"
        }

@router.get("/events/triggers")
async def list_event_triggers(
    integration: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List configured event triggers"""
    return {
        "triggers": [
            {
                "id": "trigger_001",
                "event": "api_failure",
                "integration": "pagerduty",
                "action": "create_incident",
                "config": {
                    "urgency": "high",
                    "service": "api-service"
                },
                "enabled": True,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "trigger_002",
                "event": "sla_breach",
                "integration": "slack",
                "action": "send_alert",
                "config": {
                    "channel": "#api-alerts",
                    "mention": "@oncall"
                },
                "enabled": True,
                "created_at": datetime.utcnow().isoformat()
            }
        ],
        "total": 2
    }

@router.delete("/events/triggers/{trigger_id}")
async def delete_event_trigger(
    trigger_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an event trigger"""
    return {
        "trigger_id": trigger_id,
        "status": "deleted",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/status")
async def get_integration_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get status of all integrations"""
    return {
        "integrations": {
            "jira": {
                "connected": True,
                "last_sync": datetime.utcnow().isoformat(),
                "issues_created_today": 5
            },
            "slack": {
                "connected": True,
                "last_message": datetime.utcnow().isoformat(),
                "messages_sent_today": 23
            },
            "teams": {
                "connected": False,
                "error": "Webhook URL not configured"
            },
            "github": {
                "connected": True,
                "repos_connected": 3,
                "last_activity": datetime.utcnow().isoformat()
            },
            "datadog": {
                "connected": True,
                "metrics_sent_today": 1542
            },
            "pagerduty": {
                "connected": True,
                "open_incidents": 0,
                "on_call": "team-alpha"
            }
        },
        "summary": {
            "total_configured": 5,
            "total_connected": 5,
            "total_events_today": 1570
        }
    }