"""
Test Runner API Routes
Endpoints for executing tests with assertions
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from src.database import get_db, User, Project, Test
from src.auth import get_current_user
from src.models.test_runner import TestResult, TestSuite, TestSuiteResult
from src.agents.test_runner_agent import TestRunnerAgent
from src.postman_import import PostmanImporter
from pydantic import BaseModel

router = APIRouter(prefix="/api/test-runner", tags=["test-runner"])


# Pydantic models
class RunTestRequest(BaseModel):
    """Request to run a single test"""

    test_id: Optional[int] = None
    url: str
    method: str = "GET"
    headers: Dict[str, str] = {}
    body: Optional[Any] = None
    assertions: List[Dict[str, Any]] = []
    environment: Dict[str, str] = {}
    timeout: int = 30


class RunTestSuiteRequest(BaseModel):
    """Request to run a test suite"""

    suite_id: Optional[int] = None
    test_ids: List[int] = []
    environment: Dict[str, str] = {}
    parallel: bool = False
    stop_on_failure: bool = False


class ImportPostmanRequest(BaseModel):
    """Request to import Postman collection"""

    project_id: int
    collection_json: Dict[str, Any]
    environment_json: Optional[Dict[str, Any]] = None


class AssertionDefinition(BaseModel):
    """Assertion definition"""

    type: str
    expected: Any
    operator: str = "equals"
    description: str = ""


class TestDefinition(BaseModel):
    """Test definition"""

    name: str
    url: str
    method: str = "GET"
    headers: Dict[str, str] = {}
    body: Optional[Any] = None
    assertions: List[AssertionDefinition] = []
    setup_script: Optional[str] = None
    teardown_script: Optional[str] = None


# Global test runner instance
test_runner = TestRunnerAgent()


@router.post("/run-test")
async def run_single_test(
    request: RunTestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a single test with assertions"""

    # Create test case
    test_case = test_runner.create_test_from_request(
        name=f"Test {request.test_id or 'Ad-hoc'}",
        url=request.url,
        method=request.method,
        headers=request.headers,
        body=request.body,
        assertions=request.assertions,
    )

    # Run test
    result = await test_runner.run_single_test(test_case, request.environment)

    # Save result if test_id provided
    if request.test_id:
        test = db.query(Test).filter(Test.id == request.test_id).first()
        if test:
            test_result = TestResult(
                test_id=test.id,
                project_id=test.api.project_id,
                user_id=current_user.id,
                status=result["status"],
                response_time_ms=result.get("response_time_ms", 0),
                assertions_passed=sum(
                    1 for a in result.get("assertions", []) if a["passed"]
                ),
                assertions_failed=sum(
                    1 for a in result.get("assertions", []) if not a["passed"]
                ),
                request_url=request.url,
                request_method=request.method,
                request_headers=request.headers,
                request_body=str(request.body) if request.body else None,
                response_status=result.get("response", {}).get("status_code"),
                response_headers=result.get("response", {}).get("headers"),
                response_body=result.get("response", {}).get("body"),
                assertion_results=result.get("assertions", []),
                error_message=result.get("error"),
                duration_ms=result.get("duration_ms", 0),
            )
            db.add(test_result)

            # Update test status
            test.status = result["status"]
            test.last_run = datetime.utcnow()
            test.execution_time = result.get("duration_ms", 0)

            db.commit()

    return {"success": True, "result": result}


@router.post("/run-suite")
async def run_test_suite(
    request: RunTestSuiteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a test suite"""

    # Load suite or create from test IDs
    if request.suite_id:
        suite_model = (
            db.query(TestSuite).filter(TestSuite.id == request.suite_id).first()
        )
        if not suite_model:
            raise HTTPException(status_code=404, detail="Test suite not found")
        test_ids = suite_model.test_ids or request.test_ids
    else:
        test_ids = request.test_ids

    # Load tests
    tests = db.query(Test).filter(Test.id.in_(test_ids)).all()
    if not tests:
        raise HTTPException(status_code=404, detail="No tests found")

    # Create test cases
    test_cases = []
    for test in tests:
        # Parse test code/assertions
        assertions = []
        if test.code:
            try:
                test_def = json.loads(test.code)
                assertions = test_def.get("assertions", [])
            except Exception:
                pass

        test_case = test_runner.create_test_from_request(
            name=test.name,
            url=test.api.path,
            method=test.api.method,
            headers={},
            body=None,
            assertions=assertions,
        )
        test_cases.append(test_case)

    # Create suite
    suite = TestSuite(name=f"Suite {request.suite_id or 'Ad-hoc'}", tests=test_cases)

    # Run suite
    result = await suite.run(environment=request.environment, parallel=request.parallel)

    # Save results
    if request.suite_id:
        suite_result = TestSuiteResult(
            suite_id=request.suite_id,
            user_id=current_user.id,
            total_tests=result["total_tests"],
            passed=result["passed"],
            failed=result["failed"],
            errors=result["errors"],
            skipped=result["skipped"],
            pass_rate=result["pass_rate"],
            started_at=datetime.fromisoformat(result["start_time"])
            if result.get("start_time")
            else None,
            completed_at=datetime.fromisoformat(result["end_time"])
            if result.get("end_time")
            else None,
            duration_ms=result["duration_ms"],
            test_results=[t["name"] for t in result["tests"]],
            environment_snapshot=request.environment,
        )
        db.add(suite_result)
        db.commit()

    return {"success": True, "result": result}


@router.post("/import-postman")
async def import_postman_collection(
    request: ImportPostmanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import a Postman collection"""

    # Verify project access
    project = (
        db.query(Project)
        .filter(Project.id == request.project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Import collection
    importer = PostmanImporter()
    result = importer.import_collection(request.collection_json)

    if not result["success"]:
        raise HTTPException(
            status_code=400, detail=result.get("error", "Import failed")
        )

    # Import environment if provided
    env_vars = {}
    if request.environment_json:
        env_result = importer.import_environment(request.environment_json)
        if env_result["success"]:
            env_vars = env_result["environment"]["variables"]

    # Convert to internal format
    internal = importer.convert_to_internal_format(result["collection"])

    # Create tests in database
    created_tests = []
    for req in internal["requests"]:
        # Find or create API endpoint
        from src.database import API

        api = (
            db.query(API)
            .filter(
                API.project_id == project.id,
                API.path == req["url"],
                API.method == req["method"],
            )
            .first()
        )

        if not api:
            api = API(
                project_id=project.id,
                path=req["url"],
                method=req["method"],
                handler_name=req["name"],
                description=req.get("description", ""),
            )
            db.add(api)
            db.flush()

        # Create test
        test = Test(
            api_id=api.id,
            name=req["name"],
            test_type="functional",
            framework="postman",
            code=json.dumps(
                {
                    "url": req["url"],
                    "method": req["method"],
                    "headers": req.get("headers", {}),
                    "body": req.get("body"),
                    "assertions": req.get("assertions", []),
                }
            ),
            description=req.get("description", ""),
            severity="medium",
            status="pending",
        )
        db.add(test)
        created_tests.append(test)

    db.commit()

    return {
        "success": True,
        "stats": result["stats"],
        "tests_created": len(created_tests),
        "environment_variables": len(env_vars),
    }


@router.get("/test-history/{test_id}")
async def get_test_history(
    test_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get test execution history"""

    # Verify test access
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Get test results
    results = (
        db.query(TestResult)
        .filter(TestResult.test_id == test_id)
        .order_by(TestResult.executed_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "test": {
            "id": test.id,
            "name": test.name,
            "type": test.test_type,
            "status": test.status,
        },
        "history": [r.to_dict() for r in results],
    }


@router.get("/suite-history/{suite_id}")
async def get_suite_history(
    suite_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get test suite execution history"""

    # Verify suite access
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    # Get suite results
    results = (
        db.query(TestSuiteResult)
        .filter(TestSuiteResult.suite_id == suite_id)
        .order_by(TestSuiteResult.completed_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "suite": {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "test_count": len(suite.test_ids or []),
        },
        "history": [
            {
                "id": r.id,
                "total_tests": r.total_tests,
                "passed": r.passed,
                "failed": r.failed,
                "errors": r.errors,
                "pass_rate": r.pass_rate,
                "duration_ms": r.duration_ms,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in results
        ],
    }


@router.post("/create-suite")
async def create_test_suite(
    name: str,
    description: str,
    project_id: int,
    test_ids: List[int],
    parallel: bool = False,
    stop_on_failure: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new test suite"""

    # Verify project access
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create suite
    suite = TestSuite(
        project_id=project_id,
        name=name,
        description=description,
        test_ids=test_ids,
        parallel_execution=parallel,
        stop_on_failure=stop_on_failure,
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)

    return {
        "success": True,
        "suite": {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "test_count": len(test_ids),
        },
    }


@router.get("/assertions/types")
async def get_assertion_types():
    """Get available assertion types"""
    return {
        "types": [
            {
                "type": "STATUS_CODE",
                "description": "Check HTTP status code",
                "operators": ["equals", "not_equals", "in"],
                "example": {
                    "type": "STATUS_CODE",
                    "expected": 200,
                    "operator": "equals",
                },
            },
            {
                "type": "RESPONSE_TIME",
                "description": "Check response time in milliseconds",
                "operators": ["less_than", "greater_than", "equals"],
                "example": {
                    "type": "RESPONSE_TIME",
                    "expected": 1000,
                    "operator": "less_than",
                },
            },
            {
                "type": "BODY_CONTAINS",
                "description": "Check if response body contains text",
                "operators": ["contains"],
                "example": {
                    "type": "BODY_CONTAINS",
                    "expected": "success",
                    "operator": "contains",
                },
            },
            {
                "type": "BODY_JSON_PATH",
                "description": "Check JSON path value",
                "operators": ["equals", "not_equals", "exists"],
                "example": {
                    "type": "BODY_JSON_PATH",
                    "expected": {"path": "$.user.name", "value": "John"},
                },
            },
            {
                "type": "HEADER_EXISTS",
                "description": "Check if header exists",
                "operators": ["exists"],
                "example": {"type": "HEADER_EXISTS", "expected": "Content-Type"},
            },
            {
                "type": "HEADER_VALUE",
                "description": "Check header value",
                "operators": ["equals", "contains"],
                "example": {
                    "type": "HEADER_VALUE",
                    "expected": {"name": "Content-Type", "value": "application/json"},
                },
            },
            {
                "type": "BODY_REGEX",
                "description": "Match body against regex pattern",
                "operators": ["matches"],
                "example": {"type": "BODY_REGEX", "expected": "user_[0-9]+"},
            },
            {
                "type": "IS_JSON",
                "description": "Check if response is valid JSON",
                "operators": ["equals"],
                "example": {"type": "IS_JSON", "expected": true},
            },
        ]
    }
