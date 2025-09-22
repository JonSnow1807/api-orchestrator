"""
API Routes for v5.0 Features
Exposes all POSTMAN KILLER features via REST API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime

from ..database import get_db, User
from ..auth import get_current_user
from ..natural_language_testing import NaturalLanguageTestGenerator
from ..data_visualization import DataVisualizationEngine, VisualizationType
from ..enhanced_variables import EnhancedVariableManager, VariableScope
from ..privacy_ai import PrivacyFirstAI, AIMode, DataClassification
from ..offline_mode import OfflineManager, StorageFormat, OfflineCollection
from ..service_virtualization import ServiceVirtualizer, MockBehavior

# Initialize feature engines (lazy initialization for those requiring DB)
nl_test_generator = NaturalLanguageTestGenerator()
data_viz_engine = DataVisualizationEngine()
variable_manager = None  # Will be initialized with DB session
privacy_ai = PrivacyFirstAI()
offline_manager = OfflineManager()
service_virtualizer = ServiceVirtualizer()


def get_variable_manager(db: Session):
    """Get or create variable manager with DB session"""
    global variable_manager
    if variable_manager is None:
        variable_manager = EnhancedVariableManager(db)
    return variable_manager


router = APIRouter(prefix="/api/v5", tags=["v5.0 Features"])

# ============= Natural Language Testing Routes =============


@router.post("/natural-language/generate-test")
async def generate_test_from_natural_language(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Generate test code from natural language description
    """
    try:
        natural_language = request.get("description", "")
        context = request.get("context", {})

        result = nl_test_generator.generate_test(natural_language, context)

        return {
            "success": True,
            "tests": result.get("tests", []),
            "suggestions": result.get("suggestions", []),
            "patterns_matched": result.get("patterns_matched", []),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/natural-language/generate-from-response")
async def generate_tests_from_response(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Generate comprehensive test suite from API response
    """
    try:
        response_data = request.get("response", {})
        test_types = request.get("test_types", ["status", "schema", "data"])

        result = nl_test_generator.generate_from_response(response_data, test_types)

        return {"success": True, "test_suite": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/natural-language/suggestions")
async def get_test_suggestions(
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Get AI-powered test suggestions for different categories
    """
    try:
        suggestions = nl_test_generator.get_ai_suggestions(category)
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Data Visualization Routes =============


@router.post("/visualization/analyze")
async def analyze_data_for_visualization(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Analyze data and recommend best visualization types
    """
    try:
        data = request.get("data")
        analysis = data_viz_engine.analyze_data(data)
        insights = data_viz_engine.get_insights(data)

        return {"success": True, "analysis": analysis, "insights": insights}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/visualization/transform")
async def transform_data_for_chart(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Transform data for specific visualization type
    """
    try:
        data = request.get("data")
        viz_type = request.get("type", "table")
        options = request.get("options", {})

        viz_enum = VisualizationType(viz_type)
        transformed = data_viz_engine.transform_for_visualization(
            data, viz_enum, options
        )

        return {"success": True, "visualization": transformed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/visualization/query")
async def process_natural_language_query(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Process natural language query on data (e.g., "Group by category", "Sum amounts")
    """
    try:
        data = request.get("data")
        query = request.get("query", "")

        result = data_viz_engine.process_natural_language_query(data, query)

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Enhanced Variables Routes =============


@router.post("/variables/create")
async def create_variable(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new variable with specified scope
    """
    try:
        key = request.get("key")
        value = request.get("value")
        scope = request.get("scope", "LOCAL")
        workspace_id = request.get("workspace_id")
        collection_id = request.get("collection_id")
        environment_id = request.get("environment_id")

        manager = get_variable_manager(db)
        variable = await manager.create_variable(
            key=key,
            value=value,
            user_id=str(current_user.id),
            scope=VariableScope[scope],
            workspace_id=workspace_id,
            collection_id=collection_id,
            environment_id=environment_id,
            db=db,
        )

        return {"success": True, "variable": variable}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/variables/list")
async def list_variables(
    scope: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List variables accessible to the user
    """
    try:
        scope_enum = VariableScope[scope] if scope else None
        manager = get_variable_manager(db)
        variables = await manager.get_variables(
            user_id=str(current_user.id),
            scope=scope_enum,
            workspace_id=workspace_id,
            db=db,
        )

        return {"success": True, "variables": variables}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/variables/share")
async def share_variable(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Share a variable with specific users or teams
    """
    try:
        variable_id = request.get("variable_id")
        user_ids = request.get("user_ids", [])
        team_ids = request.get("team_ids", [])
        expiration = request.get("expiration")

        manager = get_variable_manager(db)
        result = await manager.share_variable(
            variable_id=variable_id,
            owner_id=str(current_user.id),
            user_ids=user_ids,
            team_ids=team_ids,
            expiration=expiration,
            db=db,
        )

        return {"success": True, "shared": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/variables/detect-sensitive")
async def detect_sensitive_data(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Detect if a value contains sensitive data
    """
    try:
        value = request.get("value", "")
        manager = EnhancedVariableManager(None)  # Static method, no DB needed
        is_sensitive = manager.detect_sensitive_data(str(value))

        return {"success": True, "is_sensitive": is_sensitive}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Privacy-First AI Routes =============


@router.post("/privacy-ai/process")
async def process_with_privacy_ai(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Process data with privacy-first AI
    """
    try:
        prompt = request.get("prompt", "")
        data = request.get("data")
        mode = request.get("mode", "HYBRID")
        classification = request.get("classification", "INTERNAL")

        result = await privacy_ai.process_request(
            prompt=prompt,
            data=data,
            context={"user_id": str(current_user.id)},
            classification=DataClassification[classification],
            mode=AIMode[mode],
        )

        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/privacy-ai/anonymize")
async def anonymize_data(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Anonymize sensitive data before processing
    """
    try:
        data = request.get("data")
        anonymized = privacy_ai.anonymize_data(data)

        return {"success": True, "anonymized": anonymized}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/privacy-ai/compliance-check")
async def check_compliance(
    regulation: str = Query(..., description="GDPR, HIPAA, SOC2, or PCI_DSS"),
    current_user: User = Depends(get_current_user),
):
    """
    Check compliance status for specific regulation
    """
    try:
        compliant = privacy_ai.check_compliance(regulation)

        return {"success": True, "regulation": regulation, "compliant": compliant}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Offline Mode Routes =============


@router.post("/offline/save-collection")
async def save_collection_offline(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Save collection in offline-friendly format
    """
    try:
        collection_data = request.get("collection")
        format_type = request.get("format", "BRU")
        path = request.get("path", f"./collections/{current_user.id}")

        collection = OfflineCollection(**collection_data)
        file_path = await offline_manager.save_collection(
            collection=collection, format=StorageFormat[format_type], path=path
        )

        return {"success": True, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/offline/load-collection")
async def load_collection_offline(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Load collection from offline storage
    """
    try:
        file_path = request.get("file_path")
        format_type = request.get("format", "BRU")

        collection = await offline_manager.load_collection(
            path=file_path, format=StorageFormat[format_type]
        )

        return {
            "success": True,
            "collection": collection.dict() if collection else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/offline/sync")
async def sync_offline_collections(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sync offline collections with cloud
    """
    try:
        local_path = request.get("path", f"./collections/{current_user.id}")

        result = await offline_manager.sync_with_cloud(
            local_path=local_path, user_id=str(current_user.id), db=db
        )

        return {"success": True, "synced": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/offline/watch")
async def watch_offline_directory(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Start watching directory for offline collection changes
    """
    try:
        directory = request.get("directory")

        await offline_manager.watch_directory(
            directory=directory, callback=lambda path: print(f"File changed: {path}")
        )

        return {"success": True, "watching": directory}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Service Virtualization Routes =============


@router.post("/virtualization/create-service")
async def create_virtual_service(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new virtual service
    """
    try:
        name = request.get("name")
        openapi_spec = request.get("openapi_spec")
        behavior = request.get("behavior", "STATIC")

        service = await service_virtualizer.create_virtual_service(
            name=name, openapi_spec=openapi_spec, user_id=str(current_user.id), db=db
        )

        # Set behavior
        service_virtualizer.set_behavior(service["id"], MockBehavior[behavior])

        return {"success": True, "service": service}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/virtualization/add-mock")
async def add_mock_endpoint(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Add mock endpoint to virtual service
    """
    try:
        service_id = request.get("service_id")
        method = request.get("method")
        path = request.get("path")
        response = request.get("response")
        status_code = request.get("status_code", 200)

        service_virtualizer.add_mock_endpoint(
            service_id=service_id,
            method=method,
            path=path,
            response=response,
            status_code=status_code,
        )

        return {
            "success": True,
            "endpoint": {"method": method, "path": path, "status_code": status_code},
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/virtualization/set-behavior")
async def set_service_behavior(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Set behavior for virtual service
    """
    try:
        service_id = request.get("service_id")
        behavior = request.get("behavior")
        options = request.get("options", {})

        service_virtualizer.set_behavior(
            service_id=service_id, behavior=MockBehavior[behavior], options=options
        )

        return {"success": True, "behavior": behavior}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/virtualization/record")
async def start_recording(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Start recording real API responses
    """
    try:
        service_id = request.get("service_id")
        target_url = request.get("target_url")

        await service_virtualizer.start_recording(service_id, target_url)

        return {"success": True, "recording": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/virtualization/replay")
async def replay_recording(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Replay recorded responses
    """
    try:
        service_id = request.get("service_id")
        recording_id = request.get("recording_id")

        await service_virtualizer.replay_recording(service_id, recording_id)

        return {"success": True, "replaying": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/virtualization/chaos")
async def configure_chaos_engineering(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Configure chaos engineering for testing failure scenarios
    """
    try:
        service_id = request.get("service_id")
        failure_rate = request.get("failure_rate", 0.1)
        latency_min = request.get("latency_min", 0)
        latency_max = request.get("latency_max", 5000)
        error_codes = request.get("error_codes", [500, 502, 503])

        service_virtualizer.configure_chaos(
            service_id=service_id,
            failure_rate=failure_rate,
            latency_range=(latency_min, latency_max),
            error_codes=error_codes,
        )

        return {
            "success": True,
            "chaos_config": {
                "failure_rate": failure_rate,
                "latency_range": [latency_min, latency_max],
                "error_codes": error_codes,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/virtualization/services")
async def list_virtual_services(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    List all virtual services for the user
    """
    try:
        services = await service_virtualizer.list_services(
            user_id=str(current_user.id), db=db
        )

        return {"success": True, "services": services}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= VS Code Extension Support Routes =============


@router.post("/vscode/discover")
async def discover_apis_for_vscode(
    request: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_user)
):
    """
    Discover APIs in workspace for VS Code extension
    """
    try:
        request.get("workspace_path")
        request.get("patterns", ["**/*.py", "**/*.js", "**/*.ts"])

        # This would integrate with discovery_agent
        # For now, return mock data
        return {
            "success": True,
            "apis": [
                {
                    "file": "src/api/users.py",
                    "endpoints": [
                        {"method": "GET", "path": "/users", "line": 45},
                        {"method": "POST", "path": "/users", "line": 67},
                    ],
                }
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/vscode/sync")
async def sync_with_vscode(current_user: User = Depends(get_current_user)):
    """
    Sync collections and environments with VS Code extension
    """
    try:
        # Return user's collections and environments
        return {
            "success": True,
            "collections": [],  # Would fetch from database
            "environments": [],  # Would fetch from database
            "last_sync": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
