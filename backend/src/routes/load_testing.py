"""
Load Testing API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import uuid

from src.database import get_db
from src.auth import get_current_user
from src.load_testing import LoadTester, LoadTestType

router = APIRouter(prefix="/api/load-testing", tags=["Load Testing"])

# Store active load tests
active_tests: Dict[str, LoadTester] = {}

class LoadTestRequest(BaseModel):
    """Request model for load testing"""
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

@router.post("/start")
async def start_load_test(
    request: LoadTestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Start a new load test"""
    
    # Validate test type
    try:
        test_type = LoadTestType[request.test_type.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid test type: {request.test_type}")
    
    # Generate test ID
    test_id = str(uuid.uuid4())
    
    # Create load tester instance
    tester = LoadTester()
    active_tests[test_id] = tester
    
    # Run test in background
    async def run_test():
        try:
            summary = await tester.run_load_test(
                url=request.url,
                method=request.method,
                headers=request.headers,
                body=request.body,
                test_type=test_type,
                duration_seconds=request.duration_seconds,
                target_rps=request.target_rps,
                concurrent_users=request.concurrent_users,
                ramp_up_seconds=request.ramp_up_seconds
            )
            
            # Store results if requested
            if request.save_results and request.project_id:
                # TODO: Save to database
                pass
                
        except Exception as e:
            print(f"Load test error: {e}")
        finally:
            # Clean up after 5 minutes
            await asyncio.sleep(300)
            if test_id in active_tests:
                del active_tests[test_id]
    
    background_tasks.add_task(run_test)
    
    return {
        "success": True,
        "test_id": test_id,
        "message": "Load test started",
        "config": {
            "url": request.url,
            "test_type": request.test_type,
            "duration": request.duration_seconds,
            "target_rps": request.target_rps
        }
    }

@router.get("/status/{test_id}")
async def get_test_status(
    test_id: str,
    current_user = Depends(get_current_user)
):
    """Get current status of a load test"""
    
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

@router.post("/stop/{test_id}")
async def stop_load_test(
    test_id: str,
    current_user = Depends(get_current_user)
):
    """Stop a running load test"""
    
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