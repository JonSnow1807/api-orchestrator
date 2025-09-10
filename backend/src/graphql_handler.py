"""
GraphQL Support for API Orchestrator
Provides GraphQL query building, introspection, and testing capabilities
"""

import json
import httpx
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey, Text

from src.database import Base

class GraphQLQuery(BaseModel):
    """GraphQL query model"""
    query: str
    variables: Optional[Dict[str, Any]] = None
    operation_name: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

class GraphQLSchema(Base):
    """Stores GraphQL schema information"""
    __tablename__ = "graphql_schemas"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    endpoint_url = Column(String(500), nullable=False)
    
    # Schema information
    schema_sdl = Column(Text)  # Schema Definition Language
    introspection_result = Column(JSON)  # Full introspection query result
    types = Column(JSON)  # Extracted types for quick access
    queries = Column(JSON)  # Available queries
    mutations = Column(JSON)  # Available mutations
    subscriptions = Column(JSON)  # Available subscriptions
    
    # Metadata
    last_introspected = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GraphQLQueryBuilder:
    """Interactive GraphQL query builder"""
    
    @staticmethod
    def build_query(
        operation_type: str,  # query, mutation, subscription
        operation_name: str,
        fields: List[Union[str, Dict]],
        arguments: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        fragments: Optional[List[str]] = None
    ) -> str:
        """
        Build a GraphQL query from components
        
        Example:
            build_query(
                'query',
                'getUser',
                ['id', 'name', {'posts': ['title', 'content']}],
                {'id': '$userId'},
                {'userId': 123}
            )
        """
        
        # Build variable definitions
        var_defs = []
        if variables:
            for var_name, var_value in variables.items():
                var_type = GraphQLQueryBuilder._infer_type(var_value)
                var_defs.append(f"${var_name}: {var_type}")
        
        # Build arguments string
        args_str = ""
        if arguments:
            args = []
            for key, value in arguments.items():
                if isinstance(value, str) and value.startswith('$'):
                    args.append(f"{key}: {value}")
                else:
                    args.append(f"{key}: {json.dumps(value)}")
            args_str = f"({', '.join(args)})"
        
        # Build fields selection
        fields_str = GraphQLQueryBuilder._build_fields(fields)
        
        # Build the complete query
        var_def_str = f"({', '.join(var_defs)})" if var_defs else ""
        
        query = f"""
{operation_type} {operation_name}{var_def_str} {{
  {operation_name}{args_str} {fields_str}
}}
"""
        
        # Add fragments if provided
        if fragments:
            query += "\n\n" + "\n\n".join(fragments)
        
        return query.strip()
    
    @staticmethod
    def _build_fields(fields: List[Union[str, Dict]], indent: int = 2) -> str:
        """Recursively build field selection"""
        
        if not fields:
            return ""
        
        result = "{\n"
        indent_str = "  " * indent
        
        for field in fields:
            if isinstance(field, str):
                result += f"{indent_str}{field}\n"
            elif isinstance(field, dict):
                for key, subfields in field.items():
                    if isinstance(subfields, list):
                        sub_selection = GraphQLQueryBuilder._build_fields(subfields, indent + 1)
                        result += f"{indent_str}{key} {sub_selection}\n"
                    else:
                        result += f"{indent_str}{key}\n"
        
        result += "  " * (indent - 1) + "}"
        return result
    
    @staticmethod
    def _infer_type(value: Any) -> str:
        """Infer GraphQL type from Python value"""
        
        if isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, list):
            if value:
                return f"[{GraphQLQueryBuilder._infer_type(value[0])}]"
            return "[String]"
        else:
            return "String"

class GraphQLIntrospector:
    """GraphQL schema introspection"""
    
    INTROSPECTION_QUERY = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          ...FullType
        }
        directives {
          name
          description
          locations
          args {
            ...InputValue
          }
        }
      }
    }

    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          ...InputValue
        }
        type {
          ...TypeRef
        }
        isDeprecated
        deprecationReason
      }
      inputFields {
        ...InputValue
      }
      interfaces {
        ...TypeRef
      }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        ...TypeRef
      }
    }

    fragment InputValue on __InputValue {
      name
      description
      type { ...TypeRef }
      defaultValue
    }

    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    @staticmethod
    async def introspect(endpoint_url: str, headers: Optional[Dict[str, str]] = None) -> Dict:
        """Perform introspection on a GraphQL endpoint"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint_url,
                json={"query": GraphQLIntrospector.INTROSPECTION_QUERY},
                headers=headers or {}
            )
            
            if response.status_code != 200:
                raise Exception(f"Introspection failed: {response.status_code}")
            
            data = response.json()
            
            if "errors" in data:
                raise Exception(f"Introspection errors: {data['errors']}")
            
            return data["data"]["__schema"]
    
    @staticmethod
    def extract_operations(schema: Dict) -> Dict[str, List[Dict]]:
        """Extract queries, mutations, and subscriptions from schema"""
        
        operations = {
            "queries": [],
            "mutations": [],
            "subscriptions": []
        }
        
        # Find the root types
        query_type = schema.get("queryType", {}).get("name")
        mutation_type = schema.get("mutationType", {}).get("name")
        subscription_type = schema.get("subscriptionType", {}).get("name")
        
        # Extract operations from types
        for type_def in schema.get("types", []):
            if type_def.get("name") == query_type:
                operations["queries"] = GraphQLIntrospector._extract_fields(type_def)
            elif type_def.get("name") == mutation_type:
                operations["mutations"] = GraphQLIntrospector._extract_fields(type_def)
            elif type_def.get("name") == subscription_type:
                operations["subscriptions"] = GraphQLIntrospector._extract_fields(type_def)
        
        return operations
    
    @staticmethod
    def _extract_fields(type_def: Dict) -> List[Dict]:
        """Extract fields from a type definition"""
        
        fields = []
        for field in type_def.get("fields", []):
            field_info = {
                "name": field["name"],
                "description": field.get("description", ""),
                "args": [
                    {
                        "name": arg["name"],
                        "type": GraphQLIntrospector._type_to_string(arg["type"]),
                        "description": arg.get("description", "")
                    }
                    for arg in field.get("args", [])
                ],
                "returnType": GraphQLIntrospector._type_to_string(field["type"]),
                "isDeprecated": field.get("isDeprecated", False),
                "deprecationReason": field.get("deprecationReason")
            }
            fields.append(field_info)
        
        return fields
    
    @staticmethod
    def _type_to_string(type_ref: Dict) -> str:
        """Convert type reference to string representation"""
        
        if not type_ref:
            return "Unknown"
        
        kind = type_ref.get("kind")
        name = type_ref.get("name")
        
        if kind == "NON_NULL":
            return f"{GraphQLIntrospector._type_to_string(type_ref['ofType'])}!"
        elif kind == "LIST":
            return f"[{GraphQLIntrospector._type_to_string(type_ref['ofType'])}]"
        else:
            return name or "Unknown"

class GraphQLExecutor:
    """Execute GraphQL queries and handle responses"""
    
    @staticmethod
    async def execute(
        endpoint_url: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        operation_name: Optional[str] = None
    ) -> Dict:
        """Execute a GraphQL query"""
        
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        if operation_name:
            payload["operationName"] = operation_name
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint_url,
                json=payload,
                headers=headers or {},
                timeout=30.0
            )
            
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": None,
                "errors": None,
                "extensions": None
            }
            
            if response.status_code == 200:
                body = response.json()
                result["data"] = body.get("data")
                result["errors"] = body.get("errors")
                result["extensions"] = body.get("extensions")
            else:
                result["errors"] = [{"message": f"HTTP {response.status_code}: {response.text}"}]
            
            return result
    
    @staticmethod
    def validate_response(response: Dict, expected_schema: Optional[Dict] = None) -> List[str]:
        """Validate GraphQL response"""
        
        errors = []
        
        # Check for GraphQL errors
        if response.get("errors"):
            for error in response["errors"]:
                errors.append(f"GraphQL Error: {error.get('message', 'Unknown error')}")
        
        # Check HTTP status
        if response.get("status_code") != 200:
            errors.append(f"HTTP Error: Status {response.get('status_code')}")
        
        # Validate against expected schema if provided
        if expected_schema and response.get("data"):
            schema_errors = GraphQLExecutor._validate_schema(
                response["data"], 
                expected_schema
            )
            errors.extend(schema_errors)
        
        return errors
    
    @staticmethod
    def _validate_schema(data: Any, schema: Dict, path: str = "") -> List[str]:
        """Recursively validate data against schema"""
        
        errors = []
        
        if schema.get("required") and data is None:
            errors.append(f"Missing required field at {path or 'root'}")
        
        if schema.get("type") == "object" and isinstance(data, dict):
            for field, field_schema in schema.get("properties", {}).items():
                field_path = f"{path}.{field}" if path else field
                if field in data:
                    errors.extend(
                        GraphQLExecutor._validate_schema(
                            data[field], 
                            field_schema, 
                            field_path
                        )
                    )
                elif field_schema.get("required"):
                    errors.append(f"Missing required field: {field_path}")
        
        return errors

class GraphQLTestGenerator:
    """Generate tests for GraphQL APIs"""
    
    @staticmethod
    def generate_tests(
        schema: Dict,
        operations: Dict[str, List[Dict]],
        test_framework: str = "pytest"
    ) -> List[Dict]:
        """Generate test cases for GraphQL operations"""
        
        tests = []
        
        if test_framework == "pytest":
            tests.extend(GraphQLTestGenerator._generate_pytest_tests(schema, operations))
        elif test_framework == "jest":
            tests.extend(GraphQLTestGenerator._generate_jest_tests(schema, operations))
        
        return tests
    
    @staticmethod
    def _generate_pytest_tests(schema: Dict, operations: Dict) -> List[Dict]:
        """Generate pytest test cases"""
        
        test_content = '''"""
GraphQL API Tests
Auto-generated test suite
"""

import pytest
import httpx
import json

class TestGraphQLAPI:
    """Test GraphQL API operations"""
    
    @pytest.fixture
    def client(self):
        """HTTP client fixture"""
        return httpx.Client()
    
    @pytest.fixture
    def graphql_url(self):
        """GraphQL endpoint URL"""
        return "http://localhost:4000/graphql"
    
'''
        
        # Generate tests for queries
        for query in operations.get("queries", []):
            test_name = f"test_query_{query['name']}"
            test_content += f'''    def {test_name}(self, client, graphql_url):
        """Test {query['name']} query"""
        
        query = """
        query {query['name']} {{
            {query['name']} {{
                id
                # Add more fields as needed
            }}
        }}
        """
        
        response = client.post(
            graphql_url,
            json={{"query": query}}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        assert "data" in data
        assert "{query['name']}" in data["data"]
        
'''
        
        # Generate tests for mutations
        for mutation in operations.get("mutations", []):
            test_name = f"test_mutation_{mutation['name']}"
            test_content += f'''    def {test_name}(self, client, graphql_url):
        """Test {mutation['name']} mutation"""
        
        mutation = """
        mutation {mutation['name']} {{
            {mutation['name']}(input: {{}}) {{
                success
                # Add more fields as needed
            }}
        }}
        """
        
        response = client.post(
            graphql_url,
            json={{"query": mutation}}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "errors" not in data
        
'''
        
        return [{
            "filename": "test_graphql.py",
            "content": test_content,
            "framework": "pytest"
        }]
    
    @staticmethod
    def _generate_jest_tests(schema: Dict, operations: Dict) -> List[Dict]:
        """Generate Jest test cases"""
        
        test_content = '''/**
 * GraphQL API Tests
 * Auto-generated test suite
 */

const { GraphQLClient } = require('graphql-request');

describe('GraphQL API', () => {
  let client;
  
  beforeAll(() => {
    client = new GraphQLClient('http://localhost:4000/graphql');
  });
  
'''
        
        # Generate tests for queries
        for query in operations.get("queries", []):
            test_content += f'''  test('{query["name"]} query', async () => {{
    const query = `
      query {query["name"]} {{
        {query["name"]} {{
          id
          // Add more fields
        }}
      }}
    `;
    
    const data = await client.request(query);
    expect(data).toBeDefined();
    expect(data.{query["name"]}).toBeDefined();
  }});
  
'''
        
        test_content += '});'
        
        return [{
            "filename": "graphql.test.js",
            "content": test_content,
            "framework": "jest"
        }]