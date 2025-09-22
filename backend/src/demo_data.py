"""
Demo Data Generator
Creates sample projects, APIs, and tests for new users
"""

import json
from datetime import datetime

SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
        "description": "A sample Pet Store API to demonstrate API Orchestrator features",
    },
    "servers": [
        {"url": "https://petstore.api-orchestrator.demo", "description": "Demo server"}
    ],
    "paths": {
        "/pets": {
            "get": {
                "summary": "List all pets",
                "operationId": "listPets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return",
                        "required": False,
                        "schema": {"type": "integer", "format": "int32"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A paged array of pets",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Pet"},
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": "Create a pet",
                "operationId": "createPet",
                "tags": ["pets"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Pet"}
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "201": {
                        "description": "Pet created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        },
                    }
                },
            },
        },
        "/pets/{petId}": {
            "get": {
                "summary": "Get a pet by ID",
                "operationId": "getPetById",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "The id of the pet",
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Expected response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        },
                    },
                    "404": {"description": "Pet not found"},
                },
            },
            "put": {
                "summary": "Update a pet",
                "operationId": "updatePet",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Pet"}
                        }
                    }
                },
                "responses": {"200": {"description": "Pet updated"}},
            },
            "delete": {
                "summary": "Delete a pet",
                "operationId": "deletePet",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"204": {"description": "Pet deleted"}},
            },
        },
        "/users": {
            "get": {
                "summary": "List users",
                "operationId": "listUsers",
                "tags": ["users"],
                "responses": {
                    "200": {
                        "description": "List of users",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/User"},
                                }
                            }
                        },
                    }
                },
            }
        },
        "/users/login": {
            "post": {
                "summary": "User login",
                "operationId": "loginUser",
                "tags": ["users"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string"},
                                    "password": {"type": "string"},
                                },
                                "required": ["username", "password"],
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "token": {"type": "string"},
                                        "user": {"$ref": "#/components/schemas/User"},
                                    },
                                }
                            }
                        },
                    },
                    "401": {"description": "Invalid credentials"},
                },
            }
        },
    },
    "components": {
        "schemas": {
            "Pet": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["available", "pending", "sold"],
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                },
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "firstName": {"type": "string"},
                    "lastName": {"type": "string"},
                    "phone": {"type": "string"},
                },
            },
            "Error": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {"type": "integer", "format": "int32"},
                    "message": {"type": "string"},
                },
            },
        }
    },
}

SAMPLE_TESTS = [
    {
        "name": "Test GET /pets - List all pets",
        "endpoint": "/pets",
        "method": "GET",
        "assertions": [
            {"type": "STATUS_CODE", "expected": 200, "operator": "equals"},
            {"type": "RESPONSE_TIME", "expected": 1000, "operator": "less_than"},
            {"type": "IS_JSON", "expected": True},
        ],
    },
    {
        "name": "Test POST /pets - Create a pet",
        "endpoint": "/pets",
        "method": "POST",
        "body": {
            "name": "Fluffy",
            "category": "cat",
            "status": "available",
            "tags": ["cute", "fluffy"],
        },
        "assertions": [
            {"type": "STATUS_CODE", "expected": 201, "operator": "equals"},
            {
                "type": "BODY_JSON_PATH",
                "expected": {"path": "$.name", "value": "Fluffy"},
            },
            {"type": "HEADER_EXISTS", "expected": "Content-Type"},
        ],
    },
    {
        "name": "Test GET /pets/{id} - Get pet by ID",
        "endpoint": "/pets/123",
        "method": "GET",
        "assertions": [
            {"type": "STATUS_CODE", "expected": 200, "operator": "equals"},
            {"type": "BODY_JSON_PATH", "expected": {"path": "$.id", "value": 123}},
        ],
    },
    {
        "name": "Test DELETE /pets/{id} - Delete pet",
        "endpoint": "/pets/123",
        "method": "DELETE",
        "assertions": [
            {"type": "STATUS_CODE", "expected": 204, "operator": "equals"},
            {"type": "RESPONSE_TIME", "expected": 500, "operator": "less_than"},
        ],
    },
    {
        "name": "Test User Login",
        "endpoint": "/users/login",
        "method": "POST",
        "body": {"username": "testuser", "password": "testpass123"},
        "assertions": [
            {"type": "STATUS_CODE", "expected": 200, "operator": "equals"},
            {
                "type": "BODY_JSON_PATH",
                "expected": {"path": "$.token"},
                "operator": "exists",
            },
            {
                "type": "BODY_JSON_PATH",
                "expected": {"path": "$.user.username", "value": "testuser"},
            },
        ],
    },
]

SAMPLE_COLLECTIONS = [
    {
        "name": "Pet Management",
        "description": "Collection for managing pet resources",
        "requests": [
            {
                "name": "List Pets",
                "method": "GET",
                "url": "{{base_url}}/pets",
                "headers": {"Accept": "application/json"},
            },
            {
                "name": "Create Pet",
                "method": "POST",
                "url": "{{base_url}}/pets",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {{token}}",
                },
                "body": {
                    "name": "{{pet_name}}",
                    "category": "dog",
                    "status": "available",
                },
            },
            {
                "name": "Get Pet Details",
                "method": "GET",
                "url": "{{base_url}}/pets/{{pet_id}}",
                "headers": {"Accept": "application/json"},
            },
            {
                "name": "Update Pet",
                "method": "PUT",
                "url": "{{base_url}}/pets/{{pet_id}}",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {{token}}",
                },
                "body": {"name": "{{pet_name}}", "status": "sold"},
            },
        ],
    },
    {
        "name": "User Authentication",
        "description": "User authentication flows",
        "requests": [
            {
                "name": "User Login",
                "method": "POST",
                "url": "{{base_url}}/users/login",
                "headers": {"Content-Type": "application/json"},
                "body": {"username": "{{username}}", "password": "{{password}}"},
            },
            {
                "name": "Get User Profile",
                "method": "GET",
                "url": "{{base_url}}/users/me",
                "headers": {"Authorization": "Bearer {{token}}"},
            },
        ],
    },
]

SAMPLE_ENVIRONMENTS = [
    {
        "name": "Development",
        "variables": {
            "base_url": "http://localhost:3000",
            "token": "dev_token_123",
            "pet_id": "1",
            "pet_name": "Max",
            "username": "devuser",
            "password": "devpass123",
        },
    },
    {
        "name": "Staging",
        "variables": {
            "base_url": "https://staging.petstore.api-orchestrator.demo",
            "token": "",
            "pet_id": "",
            "pet_name": "Buddy",
            "username": "testuser",
            "password": "testpass123",
        },
    },
    {
        "name": "Production",
        "variables": {
            "base_url": "https://api.petstore.api-orchestrator.demo",
            "token": "",
            "pet_id": "",
            "pet_name": "",
            "username": "",
            "password": "",
        },
    },
]


def create_demo_project(db, user_id: int):
    """Create a demo project with sample data"""
    from src.database import Project, API, Test, MockServer, Collection, Environment

    # Create demo project
    project = Project(
        user_id=user_id,
        name="Pet Store API Demo",
        description="A sample Pet Store API to explore API Orchestrator features. This demo includes endpoints for managing pets and users, complete with tests and mock servers.",
        source_type="openapi",
        github_url="https://github.com/api-orchestrator/petstore-demo",
    )
    db.add(project)
    db.flush()

    # Create APIs from OpenAPI spec
    api_count = 0
    for path, methods in SAMPLE_OPENAPI_SPEC["paths"].items():
        for method, operation in methods.items():
            api = API(
                project_id=project.id,
                path=path,
                method=method.upper(),
                handler_name=operation.get("operationId", ""),
                description=operation.get("summary", ""),
                parameters=operation.get("parameters", []),
                response_schema=operation.get("responses", {}),
                auth_required="security" in operation,
            )
            db.add(api)
            api_count += 1

    db.flush()

    # Create sample tests
    apis = db.query(API).filter(API.project_id == project.id).all()
    test_count = 0
    for test_data in SAMPLE_TESTS:
        # Find matching API
        api = next(
            (
                a
                for a in apis
                if a.path == test_data["endpoint"] and a.method == test_data["method"]
            ),
            None,
        )
        if api:
            test = Test(
                api_id=api.id,
                name=test_data["name"],
                test_type="functional",
                framework="api-orchestrator",
                code=json.dumps(
                    {
                        "url": test_data["endpoint"],
                        "method": test_data["method"],
                        "body": test_data.get("body"),
                        "assertions": test_data["assertions"],
                    }
                ),
                description=f"Automated test for {test_data['method']} {test_data['endpoint']}",
                severity="medium",
                status="pending",
            )
            db.add(test)
            test_count += 1

    # Create mock server
    mock_server = MockServer(
        project_id=project.id,
        name="Pet Store Mock Server",
        port=3001,
        host="localhost",
        status="stopped",
        config={"spec": SAMPLE_OPENAPI_SPEC, "delay": 0, "error_rate": 0},
        created_at=datetime.utcnow(),
    )
    db.add(mock_server)

    # Create collections
    collection_count = 0
    for coll_data in SAMPLE_COLLECTIONS:
        collection = Collection(
            project_id=project.id,
            name=coll_data["name"],
            description=coll_data["description"],
            requests=coll_data["requests"],
            structure={
                "folders": [],
                "requests": [req["name"] for req in coll_data["requests"]],
            },
            variables={},
            created_by=user_id,
        )
        db.add(collection)
        collection_count += 1

    # Create environments
    environment_count = 0
    for env_data in SAMPLE_ENVIRONMENTS:
        environment = Environment(
            project_id=project.id,
            name=env_data["name"],
            variables=env_data["variables"],
            initial_variables=env_data["variables"],
            current_variables=env_data["variables"],
            is_default=env_data["name"] == "Development",
            created_by=user_id,
        )
        db.add(environment)
        environment_count += 1

    db.commit()

    return {
        "project": project,
        "stats": {
            "apis": api_count,
            "tests": test_count,
            "collections": collection_count,
            "environments": environment_count,
        },
    }


def create_demo_workspace(db, user_id: int):
    """Create a demo workspace with sample data"""
    from src.models.workspace import Workspace

    workspace = Workspace(
        name="Demo Workspace",
        slug="demo-workspace",
        description="A demo workspace to explore team collaboration features",
        created_by=user_id,
        subscription_tier="professional",
        max_members=10,
        max_projects=50,
        max_api_calls=10000,
    )
    db.add(workspace)
    db.flush()

    # Add the user as owner
    workspace.add_member(user_id, "owner")

    db.commit()
    return workspace


def initialize_demo_for_user(db, user_id: int):
    """Initialize demo data for a new user"""
    try:
        # Create demo workspace
        workspace = create_demo_workspace(db, user_id)

        # Create demo project
        result = create_demo_project(db, user_id)

        # Note: Project doesn't have workspace_id field yet
        # This would need to be added to the Project model
        db.commit()

        return {
            "success": True,
            "workspace": workspace,
            "project": result["project"],
            "stats": result["stats"],
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
