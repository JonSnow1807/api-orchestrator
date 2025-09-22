"""
AI Agent Builder API Routes
The POSTMAN KILLER feature - Build, test, and deploy intelligent agents
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from src.database import get_db
from src.auth import get_current_user
from src.ai_agent_builder import (
    agent_builder,
    AgentType,
    AgentCapability,
    AGENT_TEMPLATES,
)

router = APIRouter(prefix="/api/ai-agents", tags=["AI Agent Builder"])


class CreateAgentRequest(BaseModel):
    """Request model for creating an AI agent"""

    name: str
    description: str
    type: str  # AgentType value
    capabilities: List[str]  # List of AgentCapability values
    model: str = "gpt-4"
    temperature: float = 0.7
    custom_prompt: Optional[str] = None
    auto_deploy: bool = False


class WorkflowStepRequest(BaseModel):
    """Request model for adding workflow step"""

    step_type: str
    config: Dict[str, Any]
    conditions: Optional[Dict[str, Any]] = None


class TestAgentRequest(BaseModel):
    """Request model for testing an agent"""

    test_input: Dict[str, Any]


class ExecuteAgentRequest(BaseModel):
    """Request model for executing a deployed agent"""

    input_data: Dict[str, Any]
    api_key: str


@router.get("/templates")
async def get_agent_templates(current_user=Depends(get_current_user)):
    """Get available agent templates"""
    return {
        "success": True,
        "templates": [
            {
                "name": template.name,
                "description": template.description,
                "type": template.type.value,
                "capabilities": [cap.value for cap in template.capabilities],
                "workflow_steps": len(template.workflow),
            }
            for template in AGENT_TEMPLATES
        ],
    }


@router.post("/create")
async def create_agent(
    request: CreateAgentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new AI agent"""

    try:
        # Convert string values to enums
        agent_type = AgentType(request.type)
        capabilities = [AgentCapability(cap) for cap in request.capabilities]

        # Create agent
        agent = await agent_builder.create_agent(
            name=request.name,
            description=request.description,
            agent_type=agent_type,
            capabilities=capabilities,
            custom_prompt=request.custom_prompt,
        )

        # Update model settings
        agent.model = request.model
        agent.temperature = request.temperature

        # Auto-deploy if requested
        if request.auto_deploy:
            deployment = await agent_builder.deploy_agent(agent.id)
            agent.endpoint = deployment["endpoint"]
            agent.api_key = deployment["api_key"]

        return {
            "success": True,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "type": agent.type.value,
                "capabilities": [cap.value for cap in agent.capabilities],
                "model": agent.model,
                "deployed": agent.deployed,
                "endpoint": agent.endpoint,
                "api_key": agent.api_key if agent.deployed else None,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-from-template")
async def create_from_template(
    template_name: str,
    custom_name: Optional[str] = None,
    auto_deploy: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create an agent from a template"""

    # Find template
    template = None
    for t in AGENT_TEMPLATES:
        if t.name == template_name:
            template = t
            break

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        # Create agent from template
        agent = await agent_builder.create_agent(
            name=custom_name or template.name,
            description=template.description,
            agent_type=template.type,
            capabilities=template.capabilities,
        )

        # Add workflow steps from template
        for step in template.workflow:
            await agent_builder.add_workflow_step(
                agent_id=agent.id, step_type=step["type"], config=step["config"]
            )

        # Auto-deploy if requested
        if auto_deploy:
            deployment = await agent_builder.deploy_agent(agent.id)
            agent.endpoint = deployment["endpoint"]
            agent.api_key = deployment["api_key"]

        return {
            "success": True,
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "type": agent.type.value,
                "template": template_name,
                "deployed": agent.deployed,
                "endpoint": agent.endpoint,
                "api_key": agent.api_key if agent.deployed else None,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
async def list_agents(current_user=Depends(get_current_user)):
    """List all agents for the current user"""

    agents = []
    for agent_id, agent in agent_builder.agents.items():
        agents.append(
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "type": agent.type.value,
                "deployed": agent.deployed,
                "created_at": agent.created_at.isoformat(),
                "workflow_steps": len(agent.workflow_steps),
                "test_cases": len(agent.test_cases),
            }
        )

    return {"success": True, "agents": agents, "total": len(agents)}


@router.get("/{agent_id}")
async def get_agent(agent_id: str, current_user=Depends(get_current_user)):
    """Get detailed information about an agent"""

    if agent_id not in agent_builder.agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = agent_builder.agents[agent_id]

    return {
        "success": True,
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "type": agent.type.value,
            "capabilities": [cap.value for cap in agent.capabilities],
            "model": agent.model,
            "temperature": agent.temperature,
            "system_prompt": agent.system_prompt,
            "tools": agent.tools,
            "workflow_steps": agent.workflow_steps,
            "deployed": agent.deployed,
            "endpoint": agent.endpoint,
            "api_key": agent.api_key if agent.deployed else None,
            "test_cases": agent.test_cases,
            "created_at": agent.created_at.isoformat(),
        },
    }


@router.post("/{agent_id}/workflow/add-step")
async def add_workflow_step(
    agent_id: str, request: WorkflowStepRequest, current_user=Depends(get_current_user)
):
    """Add a workflow step to an agent"""

    try:
        step = await agent_builder.add_workflow_step(
            agent_id=agent_id,
            step_type=request.step_type,
            config=request.config,
            conditions=request.conditions,
        )

        return {
            "success": True,
            "step": step,
            "total_steps": len(agent_builder.agents[agent_id].workflow_steps),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/test")
async def test_agent(
    agent_id: str,
    request: TestAgentRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):
    """Test an agent with sample input"""

    try:
        result = await agent_builder.test_agent(
            agent_id=agent_id, test_input=request.test_input
        )

        # Save test case
        if agent_id in agent_builder.agents:
            agent_builder.agents[agent_id].test_cases.append(
                {
                    "input": request.test_input,
                    "output": result["output"],
                    "timestamp": result["execution_time"],
                }
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/deploy")
async def deploy_agent(
    agent_id: str,
    endpoint_path: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Deploy an agent as an API endpoint"""

    try:
        result = await agent_builder.deploy_agent(
            agent_id=agent_id, endpoint_path=endpoint_path
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: str, request: ExecuteAgentRequest, background_tasks: BackgroundTasks
):
    """Execute a deployed agent (requires API key)"""

    try:
        result = await agent_builder.execute_agent(
            agent_id=agent_id, input_data=request.input_data, api_key=request.api_key
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, current_user=Depends(get_current_user)):
    """Delete an agent"""

    if agent_id not in agent_builder.agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    del agent_builder.agents[agent_id]

    return {"success": True, "message": f"Agent {agent_id} deleted successfully"}


@router.get("/capabilities/list")
async def list_capabilities(current_user=Depends(get_current_user)):
    """List all available agent capabilities"""

    return {
        "success": True,
        "capabilities": [
            {
                "name": cap.value,
                "description": {
                    "http_requests": "Make HTTP requests to APIs",
                    "data_transformation": "Transform data between formats",
                    "file_operations": "Read/write files",
                    "database_queries": "Query databases",
                    "code_generation": "Generate code snippets",
                    "natural_language": "Process natural language",
                    "scheduling": "Schedule tasks",
                    "notifications": "Send notifications",
                    "chain_apis": "Chain multiple API calls",
                    "conditional_logic": "Apply conditional logic",
                }.get(cap.value, ""),
            }
            for cap in AgentCapability
        ],
    }


@router.get("/types/list")
async def list_agent_types(current_user=Depends(get_current_user)):
    """List all available agent types"""

    return {
        "success": True,
        "types": [
            {
                "name": agent_type.value,
                "description": {
                    "api_tester": "Test and validate APIs",
                    "data_processor": "Process and transform data",
                    "workflow_automator": "Automate multi-step workflows",
                    "security_scanner": "Scan for security vulnerabilities",
                    "performance_optimizer": "Optimize API performance",
                    "documentation_generator": "Generate API documentation",
                    "mock_data_generator": "Generate mock data",
                    "integration_builder": "Build API integrations",
                    "custom": "Custom agent type",
                }.get(agent_type.value, ""),
            }
            for agent_type in AgentType
        ],
    }
