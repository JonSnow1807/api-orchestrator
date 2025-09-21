"""
Advanced Load Testing API Routes
Enterprise-grade load testing with distributed execution, AI test generation, and comprehensive metrics
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import json
import asyncio

from src.database import get_db, User
from src.auth import get_current_user
from src.advanced_load_testing import (
    LoadTestConfig, LoadTestType, LoadTestResult, LoadTestOrchestrator,
    AITestGenerator, load_test_orchestrator, create_performance_dashboard_data,
    quick_stress_test
)

router = APIRouter(prefix="/api/load-testing", tags=["Load Testing"])

# Legacy support - keep active_tests for backward compatibility
active_tests: Dict[str, Any] = {}

class CreateLoadTestRequest(BaseModel):
    test_name: str = Field(..., description="Name of the load test")
    test_type: LoadTestType = Field(..., description="Type of load test")
    target_url: str = Field(..., description="Target URL to test")
    duration_seconds: int = Field(default=300, ge=10, le=3600, description="Test duration in seconds")
    max_users: int = Field(default=100, ge=1, le=10000, description="Maximum concurrent users")
    ramp_up_seconds: int = Field(default=60, ge=0, le=600, description="Ramp up duration")
    ramp_down_seconds: int = Field(default=30, ge=0, le=300, description="Ramp down duration")
    think_time_seconds: float = Field(default=1.0, ge=0, le=30, description="Think time between requests")
    method: str = Field(default="GET", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    payload: Optional[Dict[str, Any]] = Field(None, description="Request payload")
    success_criteria: Dict[str, float] = Field(
        default_factory=lambda: {
            "max_response_time_p95": 2000,
            "max_error_rate": 0.05,
            "min_throughput": 100
        },
        description="Success criteria for the test"
    )
    geo_distribution: List[str] = Field(default_factory=lambda: ["us-east-1"], description="Geographic distribution")

class LoadTestResponse(BaseModel):
    test_id: str
    status: str
    message: str

class LoadTestMetrics(BaseModel):
    test_id: str
    test_name: str
    status: str
    performance_score: Optional[float]
    summary_metrics: Optional[Dict[str, Any]]
    recommendations: Optional[List[str]]
    start_time: str
    end_time: Optional[str]

class GenerateTestsRequest(BaseModel):
    api_spec: Dict[str, Any] = Field(..., description="OpenAPI specification")
    test_types: List[LoadTestType] = Field(default_factory=lambda: [LoadTestType.STRESS, LoadTestType.SPIKE])

# Legacy request model for backward compatibility
class LoadTestRequest(BaseModel):
    """Legacy request model for load testing"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None
    test_type: str = "load"  # load, stress, spike, soak
    duration_seconds: int = 60
    target_rps: int = 10
    concurrent_users: int = 10
    ramp_up_seconds: int = 10
    save_results: bool = False
    project_id: Optional[int] = None

@router.post("/create", response_model=LoadTestResponse)
async def create_load_test(
    request: CreateLoadTestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and start a new advanced load test"""

    # Validate user permissions
    if not hasattr(current_user, 'subscription_tier') or current_user.subscription_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Load testing requires a paid subscription"
        )

    # Create load test configuration
    config = LoadTestConfig(
        test_name=request.test_name,
        test_type=request.test_type,
        target_url=request.target_url,
        duration_seconds=request.duration_seconds,
        max_users=request.max_users,
        ramp_up_seconds=request.ramp_up_seconds,
        ramp_down_seconds=request.ramp_down_seconds,
        think_time_seconds=request.think_time_seconds,
        method=request.method,
        headers=request.headers,
        payload=request.payload,
        success_criteria=request.success_criteria,
        geo_distribution=request.geo_distribution
    )

    # Initialize orchestrator if needed
    if not load_test_orchestrator.workers:
        load_test_orchestrator.add_worker("local")

    # Start load test in background
    async def run_test():
        try:
            await load_test_orchestrator.run_load_test(config, db)
        except Exception as e:
            print(f"Load test failed: {e}")

    background_tasks.add_task(run_test)

    return LoadTestResponse(
        test_id=load_test_orchestrator.test_id or "unknown",
        status="starting",
        message="Load test has been queued and will start shortly"
    )

# Legacy endpoint for backward compatibility
@router.post("/start")
async def start_load_test(
    request: LoadTestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Legacy load test endpoint (backward compatibility)"""

    # Convert to new format
    new_request = CreateLoadTestRequest(
        test_name=f"Legacy Test - {request.url}",
        test_type=LoadTestType.STRESS if request.test_type == "stress" else LoadTestType.STRESS,
        target_url=request.url,
        duration_seconds=request.duration_seconds,
        max_users=request.concurrent_users,
        method=request.method,
        headers=request.headers or {},
        payload=request.body
    )

    # Use new implementation
    result = await create_load_test(new_request, background_tasks, db, current_user)

    return {
        "success": True,
        "test_id": result.test_id,
        "message": result.message,
        "config": {
            "url": request.url,
            "test_type": request.test_type,
            "duration": request.duration_seconds,
            "target_rps": request.target_rps
        }
    }

@router.get("/tests", response_model=List[LoadTestMetrics])
async def list_load_tests(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List load tests for the current user"""

    query = db.query(LoadTestResult)

    if status_filter:
        query = query.filter(LoadTestResult.status == status_filter)

    query = query.order_by(LoadTestResult.start_time.desc())
    query = query.offset(offset).limit(limit)

    tests = query.all()

    return [
        LoadTestMetrics(
            test_id=test.id,
            test_name=test.test_name,
            status=test.status,
            performance_score=test.performance_score,
            summary_metrics=test.summary_metrics,
            recommendations=test.recommendations,
            start_time=test.start_time.isoformat(),
            end_time=test.end_time.isoformat() if test.end_time else None
        )
        for test in tests
    ]

@router.get("/tests/{test_id}", response_model=LoadTestMetrics)
async def get_load_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed load test results"""

    test = db.query(LoadTestResult).filter(LoadTestResult.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Load test not found"
        )

    return LoadTestMetrics(
        test_id=test.id,
        test_name=test.test_name,
        status=test.status,
        performance_score=test.performance_score,
        summary_metrics=test.summary_metrics,
        recommendations=test.recommendations,
        start_time=test.start_time.isoformat(),
        end_time=test.end_time.isoformat() if test.end_time else None
    )

@router.get("/tests/{test_id}/dashboard")
async def get_test_dashboard(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard data for load test visualization"""

    dashboard_data = create_performance_dashboard_data(test_id, db)
    if not dashboard_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Load test not found"
        )

    return dashboard_data

@router.get("/tests/{test_id}/stream")
async def stream_test_metrics(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream real-time test metrics"""

    async def generate_metrics():
        while True:
            test = db.query(LoadTestResult).filter(LoadTestResult.id == test_id).first()
            if not test:
                break

            if test.status in ["completed", "failed", "cancelled"]:
                # Send final metrics and close stream
                yield f"data: {json.dumps({'status': test.status, 'final': True})}\\n\\n"
                break

            # Send current metrics
            dashboard_data = create_performance_dashboard_data(test_id, db)
            yield f"data: {json.dumps(dashboard_data)}\\n\\n"

            await asyncio.sleep(2)  # Update every 2 seconds

    return StreamingResponse(
        generate_metrics(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# Legacy endpoint for backward compatibility
@router.get("/status/{test_id}")
async def get_test_status(
    test_id: str,
    current_user = Depends(get_current_user)
):
    """Legacy status endpoint (backward compatibility)"""

    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    tester = active_tests[test_id]
    stats = tester.get_current_stats()

    return {
        "success": True,
        "test_id": test_id,
        "status": "running" if tester.is_running else "completed",
        "statistics": stats
    }

@router.delete("/tests/{test_id}")
async def cancel_load_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a running load test"""

    test = db.query(LoadTestResult).filter(LoadTestResult.id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Load test not found"
        )

    if test.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel running tests"
        )

    # Stop the test
    load_test_orchestrator.is_running = False
    test.status = "cancelled"
    db.commit()

    return {"message": "Load test cancelled successfully"}

@router.post("/generate-tests", response_model=List[Dict[str, Any]])
async def generate_ai_tests(
    request: GenerateTestsRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered load test scenarios from API specification"""

    if not hasattr(current_user, 'subscription_tier') or current_user.subscription_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI test generation requires a paid subscription"
        )

    try:
        scenarios = AITestGenerator.generate_realistic_test_scenarios(request.api_spec)

        # Filter by requested test types
        filtered_scenarios = [
            scenario for scenario in scenarios
            if scenario.test_type in request.test_types
        ]

        return [
            {
                "test_name": scenario.test_name,
                "test_type": scenario.test_type.value,
                "target_url": scenario.target_url,
                "duration_seconds": scenario.duration_seconds,
                "max_users": scenario.max_users,
                "method": scenario.method,
                "success_criteria": scenario.success_criteria
            }
            for scenario in filtered_scenarios[:20]  # Limit to 20 scenarios
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate test scenarios: {str(e)}"
        )

@router.post("/quick-test")
async def run_quick_stress_test(
    target_url: str,
    max_users: int = 50,
    duration: int = 60,
    current_user: User = Depends(get_current_user)
):
    """Run a quick stress test for immediate results"""

    if not hasattr(current_user, 'subscription_tier') or current_user.subscription_tier == "free":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Load testing requires a paid subscription"
        )

    try:
        # Validate inputs
        if max_users > 200:
            max_users = 200  # Limit for quick tests
        if duration > 300:
            duration = 300  # Max 5 minutes for quick tests

        metrics = await quick_stress_test(target_url, max_users, duration)

        return {
            "target_url": target_url,
            "test_duration": duration,
            "max_users": max_users,
            "metrics": metrics,
            "message": "Quick stress test completed successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quick test failed: {str(e)}"
        )

@router.get("/health")
async def load_testing_health():
    """Health check for load testing service"""

    workers_status = {
        "total_workers": len(load_test_orchestrator.workers),
        "active_tests": 1 if load_test_orchestrator.is_running else 0,
        "service_status": "healthy"
    }

    return {
        "status": "healthy",
        "service": "load_testing",
        "workers": workers_status,
        "features": [
            "stress_testing",
            "spike_testing",
            "volume_testing",
            "endurance_testing",
            "ai_test_generation",
            "real_time_metrics",
            "distributed_execution"
        ]
    }

@router.get("/templates")
async def get_test_templates():
    """Get predefined load test templates"""

    templates = {
        "api_stress_test": {
            "name": "API Stress Test",
            "description": "Standard stress test for API endpoints",
            "test_type": "stress",
            "duration_seconds": 300,
            "max_users": 100,
            "ramp_up_seconds": 60,
            "success_criteria": {
                "max_response_time_p95": 2000,
                "max_error_rate": 0.05,
                "min_throughput": 50
            }
        },
        "spike_test": {
            "name": "Spike Test",
            "description": "Test sudden traffic spikes",
            "test_type": "spike",
            "duration_seconds": 180,
            "max_users": 200,
            "ramp_up_seconds": 10,
            "success_criteria": {
                "max_response_time_p95": 3000,
                "max_error_rate": 0.10,
                "min_throughput": 30
            }
        },
        "endurance_test": {
            "name": "Endurance Test",
            "description": "Long-running stability test",
            "test_type": "endurance",
            "duration_seconds": 1800,  # 30 minutes
            "max_users": 50,
            "ramp_up_seconds": 120,
            "success_criteria": {
                "max_response_time_p95": 1500,
                "max_error_rate": 0.02,
                "min_throughput": 20
            }
        },
        "volume_test": {
            "name": "Volume Test",
            "description": "High volume throughput test",
            "test_type": "volume",
            "duration_seconds": 600,  # 10 minutes
            "max_users": 500,
            "ramp_up_seconds": 180,
            "success_criteria": {
                "max_response_time_p95": 2500,
                "max_error_rate": 0.08,
                "min_throughput": 200
            }
        }
    }

    return templates

# Legacy endpoint for backward compatibility
@router.post("/stop/{test_id}")
async def stop_load_test(
    test_id: str,
    current_user = Depends(get_current_user)
):
    """Legacy stop endpoint (backward compatibility)"""

    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")

    tester = active_tests[test_id]
    tester.is_running = False

    return {
        "success": True,
        "test_id": test_id,
        "message": "Load test stopped"
    }

@router.get("/results/{test_id}")
async def get_test_results(
    test_id: str,
    current_user = Depends(get_current_user)
):
    """Get results of a completed load test"""
    
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    tester = active_tests[test_id]
    
    if tester.is_running:
        return {
            "success": False,
            "message": "Test is still running",
            "test_id": test_id
        }
    
    # Generate summary
    summary = tester._generate_summary("load")
    
    return {
        "success": True,
        "test_id": test_id,
        "summary": {
            "test_type": summary.test_type,
            "total_requests": summary.total_requests,
            "successful_requests": summary.successful_requests,
            "failed_requests": summary.failed_requests,
            "duration_seconds": summary.total_duration_seconds,
            "requests_per_second": summary.requests_per_second,
            "response_times": {
                "min": summary.min_response_time,
                "max": summary.max_response_time,
                "mean": summary.mean_response_time,
                "median": summary.median_response_time,
                "p95": summary.p95_response_time,
                "p99": summary.p99_response_time
            },
            "error_rate": summary.error_rate,
            "status_codes": summary.status_code_distribution,
            "errors": summary.errors_by_type,
            "throughput": {
                "total_bytes": summary.total_bytes_received,
                "bytes_per_second": summary.avg_bytes_per_second
            },
            "time_series": {
                "response_times": summary.response_times_over_time,
                "requests_per_second": summary.requests_per_second_over_time
            }
        }
    }

@router.get("/active")
async def list_active_tests(
    current_user = Depends(get_current_user)
):
    """List all active load tests"""
    
    active = []
    for test_id, tester in active_tests.items():
        stats = tester.get_current_stats()
        active.append({
            "test_id": test_id,
            "is_running": tester.is_running,
            "statistics": stats
        })
    
    return {
        "success": True,
        "active_tests": active
    }

@router.get("/presets")
async def get_load_test_presets():
    """Get predefined load test configurations"""
    
    return {
        "success": True,
        "presets": [
            {
                "name": "Light Load",
                "description": "Low traffic simulation",
                "config": {
                    "test_type": "load",
                    "duration_seconds": 60,
                    "target_rps": 5,
                    "concurrent_users": 5,
                    "ramp_up_seconds": 10
                }
            },
            {
                "name": "Normal Load",
                "description": "Average traffic simulation",
                "config": {
                    "test_type": "load",
                    "duration_seconds": 120,
                    "target_rps": 20,
                    "concurrent_users": 20,
                    "ramp_up_seconds": 20
                }
            },
            {
                "name": "Heavy Load",
                "description": "High traffic simulation",
                "config": {
                    "test_type": "load",
                    "duration_seconds": 180,
                    "target_rps": 50,
                    "concurrent_users": 50,
                    "ramp_up_seconds": 30
                }
            },
            {
                "name": "Stress Test",
                "description": "Push system to limits",
                "config": {
                    "test_type": "stress",
                    "duration_seconds": 120,
                    "target_rps": 100,
                    "concurrent_users": 100,
                    "ramp_up_seconds": 10
                }
            },
            {
                "name": "Spike Test",
                "description": "Sudden traffic increase",
                "config": {
                    "test_type": "spike",
                    "duration_seconds": 90,
                    "target_rps": 30,
                    "concurrent_users": 30,
                    "ramp_up_seconds": 5
                }
            },
            {
                "name": "Soak Test",
                "description": "Extended duration test",
                "config": {
                    "test_type": "soak",
                    "duration_seconds": 600,
                    "target_rps": 10,
                    "concurrent_users": 10,
                    "ramp_up_seconds": 30
                }
            }
        ]
    }