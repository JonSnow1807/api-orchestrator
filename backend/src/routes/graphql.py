"""
GraphQL API Routes
Provides GraphQL introspection, query building, and execution
"""

from fastapi import APIRouter, Depends, HTTPException, Query as QueryParam
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json

from src.database import get_db
from src.auth import get_current_user
from src.graphql_handler import (
    GraphQLSchema,
    GraphQLQueryBuilder,
    GraphQLIntrospector,
    GraphQLExecutor,
    GraphQLTestGenerator,
)

router = APIRouter(prefix="/api/graphql", tags=["GraphQL"])


class IntrospectRequest(BaseModel):
    """Request model for GraphQL introspection"""

    endpoint_url: str
    headers: Optional[Dict[str, str]] = None
    project_id: Optional[int] = None


class BuildQueryRequest(BaseModel):
    """Request model for building GraphQL queries"""

    operation_type: str  # query, mutation, subscription
    operation_name: str
    fields: List[Any]
    arguments: Optional[Dict[str, Any]] = None
    variables: Optional[Dict[str, Any]] = None
    fragments: Optional[List[str]] = None


class ExecuteRequest(BaseModel):
    """Request model for executing GraphQL queries"""

    endpoint_url: str
    query: str
    variables: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    operation_name: Optional[str] = None


class GenerateTestsRequest(BaseModel):
    """Request model for generating GraphQL tests"""

    schema_id: int
    test_framework: str = "pytest"
    include_negative: bool = True
    include_performance: bool = False


@router.post("/introspect")
async def introspect_graphql_endpoint(
    request: IntrospectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Introspect a GraphQL endpoint to discover its schema"""

    try:
        # Perform introspection
        schema_data = await GraphQLIntrospector.introspect(
            request.endpoint_url, request.headers
        )

        # Extract operations
        operations = GraphQLIntrospector.extract_operations(schema_data)

        # Store schema in database
        schema = GraphQLSchema(
            project_id=request.project_id,
            endpoint_url=request.endpoint_url,
            introspection_result=schema_data,
            types=schema_data.get("types", []),
            queries=[q["name"] for q in operations["queries"]],
            mutations=[m["name"] for m in operations["mutations"]],
            subscriptions=[s["name"] for s in operations["subscriptions"]],
        )

        db.add(schema)
        db.commit()
        db.refresh(schema)

        return {
            "success": True,
            "schema_id": schema.id,
            "operations": {
                "queries": len(operations["queries"]),
                "mutations": len(operations["mutations"]),
                "subscriptions": len(operations["subscriptions"]),
            },
            "types": len(schema_data.get("types", [])),
            "details": operations,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Introspection failed: {str(e)}")


@router.post("/build-query")
async def build_graphql_query(
    request: BuildQueryRequest, current_user=Depends(get_current_user)
):
    """Build a GraphQL query from components"""

    try:
        query = GraphQLQueryBuilder.build_query(
            operation_type=request.operation_type,
            operation_name=request.operation_name,
            fields=request.fields,
            arguments=request.arguments,
            variables=request.variables,
            fragments=request.fragments,
        )

        return {"success": True, "query": query, "variables": request.variables}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query building failed: {str(e)}")


@router.post("/execute")
async def execute_graphql_query(
    request: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Execute a GraphQL query against an endpoint"""

    try:
        # Execute the query
        result = await GraphQLExecutor.execute(
            endpoint_url=request.endpoint_url,
            query=request.query,
            variables=request.variables,
            headers=request.headers,
            operation_name=request.operation_name,
        )

        # Validate response
        errors = GraphQLExecutor.validate_response(result)

        # Save to request history
        from src.database import RequestHistory

        history = RequestHistory(
            user_id=current_user.id,
            method="POST",
            url=request.endpoint_url,
            headers=request.headers or {},
            body=json.dumps({"query": request.query, "variables": request.variables}),
            body_type="graphql",
            status_code=result["status_code"],
            response_headers=result["headers"],
            response_body=json.dumps(result.get("data", {})),
            success=len(errors) == 0,
            error_message="; ".join(errors) if errors else None,
        )

        db.add(history)
        db.commit()

        return {
            "success": len(errors) == 0,
            "result": result,
            "validation_errors": errors,
            "history_id": history.id,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution failed: {str(e)}")


@router.get("/schemas")
async def list_graphql_schemas(
    project_id: Optional[int] = QueryParam(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all GraphQL schemas for the user"""

    query = db.query(GraphQLSchema)

    if project_id:
        query = query.filter(GraphQLSchema.project_id == project_id)

    schemas = query.all()

    return {
        "success": True,
        "schemas": [
            {
                "id": s.id,
                "endpoint_url": s.endpoint_url,
                "project_id": s.project_id,
                "queries": s.queries,
                "mutations": s.mutations,
                "subscriptions": s.subscriptions,
                "last_introspected": s.last_introspected,
            }
            for s in schemas
        ],
    }


@router.get("/schema/{schema_id}")
async def get_graphql_schema(
    schema_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get detailed information about a GraphQL schema"""

    schema = db.query(GraphQLSchema).filter(GraphQLSchema.id == schema_id).first()

    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    # Extract operations with full details
    operations = GraphQLIntrospector.extract_operations(schema.introspection_result)

    return {
        "success": True,
        "schema": {
            "id": schema.id,
            "endpoint_url": schema.endpoint_url,
            "operations": operations,
            "types": schema.types,
            "last_introspected": schema.last_introspected,
        },
    }


@router.post("/generate-tests")
async def generate_graphql_tests(
    request: GenerateTestsRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate test cases for a GraphQL schema"""

    schema = (
        db.query(GraphQLSchema).filter(GraphQLSchema.id == request.schema_id).first()
    )

    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    # Extract operations
    operations = GraphQLIntrospector.extract_operations(schema.introspection_result)

    # Generate tests
    tests = GraphQLTestGenerator.generate_tests(
        schema=schema.introspection_result,
        operations=operations,
        test_framework=request.test_framework,
    )

    return {"success": True, "tests": tests}


@router.post("/suggest-query")
async def suggest_graphql_query(
    schema_id: int,
    operation_type: str,
    operation_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Suggest a GraphQL query based on schema"""

    schema = db.query(GraphQLSchema).filter(GraphQLSchema.id == schema_id).first()

    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    # Extract operations
    operations = GraphQLIntrospector.extract_operations(schema.introspection_result)

    # Find the specific operation
    operation_list = operations.get(f"{operation_type}s", [])
    operation = next(
        (op for op in operation_list if op["name"] == operation_name), None
    )

    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")

    # Build a suggested query
    fields = ["id", "__typename"]  # Basic fields
    arguments = {}

    # Add arguments if they exist
    for arg in operation.get("args", []):
        if "!" in arg["type"]:  # Required argument
            arguments[arg["name"]] = f"${arg['name']}"

    suggested_query = GraphQLQueryBuilder.build_query(
        operation_type=operation_type,
        operation_name=operation_name,
        fields=fields,
        arguments=arguments if arguments else None,
    )

    return {"success": True, "query": suggested_query, "operation": operation}


@router.delete("/schema/{schema_id}")
async def delete_graphql_schema(
    schema_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a GraphQL schema"""

    schema = db.query(GraphQLSchema).filter(GraphQLSchema.id == schema_id).first()

    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    db.delete(schema)
    db.commit()

    return {"success": True, "message": "Schema deleted successfully"}
