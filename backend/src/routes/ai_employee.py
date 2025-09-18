"""
AI Employee System API Routes
Production-ready endpoints for the autonomous engineering system
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db
from src.auth import get_current_user
from src.ai_employee.ai_employee_orchestrator import AIEmployeeOrchestrator
from src.ai_employee.code_generation_agent import CodeGenerationAgent
from src.ai_employee.self_learning_system import SelfLearningSystem
from src.ai_employee.database_agent import DatabaseAgent
from src.ai_employee.git_agent import GitAgent
from src.ai_employee.cloud_deployment_agent import CloudDeploymentAgent
from src.ai_employee.devops_agent import DevOpsAgent

router = APIRouter(prefix="/api/ai-employee", tags=["AI Employee System"])

# Initialize AI Employee with default config
ai_employee_config = {
    "git_enabled": True,
    "cloud_provider": "AWS",
    "db_connection_string": os.getenv("DATABASE_URL", "sqlite:///ai_employee.db")
}
ai_employee = AIEmployeeOrchestrator(ai_employee_config)

class NaturalLanguageRequest(BaseModel):
    """Request model for natural language processing"""
    request: str
    context: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    """Request model for complex task execution"""
    task_description: str
    requirements: Optional[List[str]] = []
    auto_deploy: bool = False

class CodeGenerationRequest(BaseModel):
    """Request model for code generation"""
    api_spec: Dict[str, Any]
    language: str = "python"
    framework: Optional[str] = None

class CodeFixRequest(BaseModel):
    """Request model for code fixing"""
    broken_code: str
    error_message: str
    language: str = "python"

class DatabaseOptimizationRequest(BaseModel):
    """Request model for database optimization"""
    query: str
    db_type: str = "postgresql"

class VulnerabilityCheckRequest(BaseModel):
    """Request model for vulnerability checking"""
    api_spec: Dict[str, Any]
    historical_data: Optional[List[Dict[str, Any]]] = []

class DeploymentRequest(BaseModel):
    """Request model for cloud deployment"""
    service_config: Dict[str, Any]
    provider: str = "AWS"
    optimize_cost: bool = True

@router.post("/process-request")
async def process_natural_language_request(
    request: NaturalLanguageRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Process a natural language request and execute appropriate action"""

    try:
        result = await ai_employee.process_request(
            request.request,
            context=request.context
        )

        return {
            "success": True,
            "action": result.get("action"),
            "status": result.get("status"),
            "result": result.get("result"),
            "execution_time": result.get("execution_time")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/execute-task")
async def execute_complex_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Execute a complex multi-step task"""

    try:
        result = await ai_employee.execute_task(request.task_description)

        return {
            "success": True,
            "main_task": result.get("main_task"),
            "subtasks": result.get("subtasks"),
            "status": result.get("status"),
            "results": result.get("results"),
            "total_time": result.get("total_time")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate-code")
async def generate_api_client(
    request: CodeGenerationRequest,
    current_user = Depends(get_current_user)
):
    """Generate API client code with intelligent patterns"""

    try:
        agent = CodeGenerationAgent()
        result = await agent.generate_api_client(
            request.api_spec,
            request.language,
            framework=request.framework
        )

        return {
            "success": True,
            "code": result.code,
            "language": result.language,
            "framework": result.framework,
            "patterns_detected": result.complexity_analysis,
            "lines_of_code": len(result.code.split('\n'))
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fix-code")
async def fix_broken_code(
    request: CodeFixRequest,
    current_user = Depends(get_current_user)
):
    """Fix broken code using AST analysis"""

    try:
        agent = CodeGenerationAgent()
        fixed_code = await agent.fix_broken_code(
            request.broken_code,
            request.error_message,
            request.language
        )

        return {
            "success": True,
            "fixed_code": fixed_code,
            "original_code": request.broken_code,
            "changes_made": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/optimize-database")
async def optimize_database_query(
    request: DatabaseOptimizationRequest,
    current_user = Depends(get_current_user)
):
    """Optimize database query using real SQL optimization"""

    try:
        agent = DatabaseAgent(ai_employee_config["db_connection_string"])
        result = await agent.optimize_query(request.query)

        return {
            "success": True,
            "original_query": result.original_query,
            "optimized_query": result.optimized_query,
            "improvements": result.improvements,
            "expected_performance_gain": result.expected_performance_gain
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/predict-issues")
async def predict_vulnerabilities(
    request: VulnerabilityCheckRequest,
    current_user = Depends(get_current_user)
):
    """Predict potential issues using ML models"""

    try:
        system = SelfLearningSystem()
        predictions = await system.predict_issues(
            request.api_spec,
            request.historical_data
        )

        return {
            "success": True,
            "predictions": [
                {
                    "issue_type": pred.issue_type,
                    "description": pred.description,
                    "probability": pred.probability,
                    "suggested_fixes": pred.suggested_fixes,
                    "priority": pred.priority
                }
                for pred in predictions
            ],
            "total_issues": len(predictions),
            "high_priority_count": sum(1 for p in predictions if p.priority == "high")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/deploy-service")
async def deploy_to_cloud(
    request: DeploymentRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """Deploy service to cloud with cost optimization"""

    try:
        agent = CloudDeploymentAgent()

        # Deploy based on provider
        if request.provider == "AWS":
            result = await agent.deploy_to_aws(request.service_config)
        elif request.provider == "GCP":
            result = await agent.deploy_to_gcp(request.service_config)
        elif request.provider == "Azure":
            result = await agent.deploy_to_azure(request.service_config)
        else:
            raise ValueError(f"Unsupported provider: {request.provider}")

        # Optimize costs if requested
        cost_savings = {}
        if request.optimize_cost:
            cost_optimization = await agent.optimize_costs()
            cost_savings = {
                "total_savings": cost_optimization["total_savings"],
                "recommendations": cost_optimization["recommendations"][:3]
            }

        return {
            "success": True,
            "deployment": result,
            "cost_optimization": cost_savings
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def get_ai_employee_status(
    current_user = Depends(get_current_user)
):
    """Get current status of AI Employee system"""

    try:
        status = await ai_employee.get_status()

        return {
            "success": True,
            "state": status["state"],
            "agents": status["agents"],
            "capabilities": status.get("capabilities", {}),
            "tasks_completed": status.get("tasks_completed", 0),
            "current_task": status.get("current_task"),
            "system_health": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/intelligence-report")
async def get_intelligence_report(
    current_user = Depends(get_current_user)
):
    """Get intelligence report showing learning progress"""

    try:
        report = await ai_employee.get_intelligence_report()

        return {
            "success": True,
            "intelligence_level": report.get("intelligence_level"),
            "patterns_learned": report.get("patterns_learned"),
            "vulnerabilities_detected": report.get("vulnerabilities_detected"),
            "optimizations_applied": report.get("optimizations_applied"),
            "success_rate": report.get("success_rate"),
            "capabilities": report.get("capabilities"),
            "recent_learnings": report.get("recent_learnings", [])[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/learn")
async def learn_from_interaction(
    interaction: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """Submit interaction data for learning"""

    try:
        await ai_employee.learn_from_interaction(interaction)

        return {
            "success": True,
            "message": "Learning data processed successfully",
            "patterns_updated": True
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/capabilities")
async def list_capabilities(
    current_user = Depends(get_current_user)
):
    """List all available AI Employee capabilities"""

    return {
        "success": True,
        "capabilities": {
            "code_generation": {
                "enabled": True,
                "features": [
                    "API client generation",
                    "Multi-language support",
                    "Code fixing with AST",
                    "Microservice scaffolding",
                    "Pattern recognition"
                ]
            },
            "database_optimization": {
                "enabled": True,
                "features": [
                    "Query optimization",
                    "Index recommendations",
                    "Performance monitoring",
                    "Anomaly detection",
                    "Capacity planning"
                ]
            },
            "self_learning": {
                "enabled": True,
                "features": [
                    "ML-based predictions",
                    "Pattern learning",
                    "Vulnerability detection",
                    "Performance prediction",
                    "Adaptive improvements"
                ]
            },
            "cloud_deployment": {
                "enabled": True,
                "features": [
                    "Multi-cloud support",
                    "Cost optimization",
                    "Auto-scaling",
                    "Disaster recovery",
                    "Resource monitoring"
                ]
            },
            "devops_automation": {
                "enabled": True,
                "features": [
                    "CI/CD pipeline generation",
                    "Container orchestration",
                    "Infrastructure as code",
                    "Monitoring setup",
                    "Automated testing"
                ]
            },
            "git_operations": {
                "enabled": True,
                "features": [
                    "Automated commits",
                    "Branch management",
                    "Change analysis",
                    "Code review assistance",
                    "Merge conflict resolution"
                ]
            }
        },
        "total_agents": 6,
        "production_ready": True,
        "version": "2.0.0"
    }