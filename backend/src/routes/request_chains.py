"""
Request Chaining API Routes
Manage and execute request chains for workflow testing
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio

from src.database import get_db
from src.auth import get_current_user
from src.request_chain import RequestChain, ChainExecutor, ChainedRequest

router = APIRouter(prefix="/api/request-chains", tags=["Request Chains"])

class CreateChainRequest(BaseModel):
    """Request model for creating a request chain"""
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    requests: List[Dict[str, Any]]
    variables: Optional[Dict[str, Any]] = None
    stop_on_failure: bool = True
    parallel_execution: bool = False

class ExecuteChainRequest(BaseModel):
    """Request model for executing a chain"""
    variables: Optional[Dict[str, Any]] = None
    environment_id: Optional[str] = None

@router.post("/create")
async def create_request_chain(
    request: CreateChainRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new request chain"""
    
    # Validate requests
    try:
        for req in request.requests:
            ChainedRequest(**req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
    
    chain = RequestChain(
        user_id=current_user.id,
        project_id=request.project_id,
        name=request.name,
        description=request.description,
        requests=request.requests,
        variables=request.variables or {},
        stop_on_failure=request.stop_on_failure,
        parallel_execution=request.parallel_execution
    )
    
    db.add(chain)
    db.commit()
    db.refresh(chain)
    
    return {
        "success": True,
        "chain": {
            "id": chain.id,
            "name": chain.name,
            "description": chain.description,
            "request_count": len(chain.requests),
            "created_at": chain.created_at
        }
    }

@router.get("/list")
async def list_request_chains(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all request chains for the current user"""
    
    query = db.query(RequestChain).filter(RequestChain.user_id == current_user.id)
    
    if project_id:
        query = query.filter(RequestChain.project_id == project_id)
    
    chains = query.all()
    
    return {
        "success": True,
        "chains": [
            {
                "id": chain.id,
                "name": chain.name,
                "description": chain.description,
                "request_count": len(chain.requests),
                "last_run": chain.last_run,
                "last_status": chain.last_status,
                "created_at": chain.created_at
            }
            for chain in chains
        ]
    }

@router.get("/{chain_id}")
async def get_request_chain(
    chain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get details of a specific request chain"""
    
    chain = db.query(RequestChain).filter(
        RequestChain.id == chain_id,
        RequestChain.user_id == current_user.id
    ).first()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    return {
        "success": True,
        "chain": {
            "id": chain.id,
            "name": chain.name,
            "description": chain.description,
            "requests": chain.requests,
            "variables": chain.variables,
            "stop_on_failure": chain.stop_on_failure,
            "parallel_execution": chain.parallel_execution,
            "last_run": chain.last_run,
            "last_status": chain.last_status,
            "last_duration_ms": chain.last_duration_ms,
            "created_at": chain.created_at
        }
    }

@router.post("/{chain_id}/execute")
async def execute_request_chain(
    chain_id: int,
    request: ExecuteChainRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Execute a request chain"""
    
    chain = db.query(RequestChain).filter(
        RequestChain.id == chain_id,
        RequestChain.user_id == current_user.id
    ).first()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # Update environment if provided
    if request.environment_id:
        chain.environment_id = request.environment_id
    
    # Execute chain
    executor = ChainExecutor(db)
    
    # For long-running chains, we could use background tasks
    # For now, execute synchronously with async/await
    try:
        result = await executor.execute_chain(chain, request.variables)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.put("/{chain_id}")
async def update_request_chain(
    chain_id: int,
    request: CreateChainRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update a request chain"""
    
    chain = db.query(RequestChain).filter(
        RequestChain.id == chain_id,
        RequestChain.user_id == current_user.id
    ).first()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # Validate requests
    try:
        for req in request.requests:
            ChainedRequest(**req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")
    
    # Update chain
    chain.name = request.name
    chain.description = request.description
    chain.requests = request.requests
    chain.variables = request.variables or {}
    chain.stop_on_failure = request.stop_on_failure
    chain.parallel_execution = request.parallel_execution
    
    db.commit()
    
    return {
        "success": True,
        "message": "Chain updated successfully"
    }

@router.delete("/{chain_id}")
async def delete_request_chain(
    chain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a request chain"""
    
    chain = db.query(RequestChain).filter(
        RequestChain.id == chain_id,
        RequestChain.user_id == current_user.id
    ).first()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    db.delete(chain)
    db.commit()
    
    return {
        "success": True,
        "message": "Chain deleted successfully"
    }

@router.post("/{chain_id}/duplicate")
async def duplicate_request_chain(
    chain_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Duplicate a request chain"""
    
    chain = db.query(RequestChain).filter(
        RequestChain.id == chain_id,
        RequestChain.user_id == current_user.id
    ).first()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # Create duplicate
    new_chain = RequestChain(
        user_id=current_user.id,
        project_id=chain.project_id,
        name=f"{chain.name} (Copy)",
        description=chain.description,
        requests=chain.requests,
        variables=chain.variables,
        stop_on_failure=chain.stop_on_failure,
        parallel_execution=chain.parallel_execution
    )
    
    db.add(new_chain)
    db.commit()
    db.refresh(new_chain)
    
    return {
        "success": True,
        "chain": {
            "id": new_chain.id,
            "name": new_chain.name
        }
    }

@router.get("/{chain_id}/history")
async def get_chain_execution_history(
    chain_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get execution history for a chain (placeholder for future implementation)"""
    
    chain = db.query(RequestChain).filter(
        RequestChain.id == chain_id,
        RequestChain.user_id == current_user.id
    ).first()
    
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    
    # In a full implementation, we would have a ChainExecutionHistory table
    # For now, return last execution info
    history = []
    if chain.last_run:
        history.append({
            "executed_at": chain.last_run,
            "status": chain.last_status,
            "duration_ms": chain.last_duration_ms
        })
    
    return {
        "success": True,
        "history": history
    }

@router.post("/test-extraction")
async def test_value_extraction(
    response_data: Dict[str, Any],
    extraction_path: str
):
    """Test value extraction from a sample response"""
    
    # Test the extraction logic
    parts = extraction_path.split('.')
    value = response_data
    
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit():
            index = int(part)
            if index < len(value):
                value = value[index]
            else:
                value = None
        else:
            value = None
            break
    
    return {
        "success": True,
        "path": extraction_path,
        "extracted_value": value,
        "type": type(value).__name__ if value is not None else "null"
    }