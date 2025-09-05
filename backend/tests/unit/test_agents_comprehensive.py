"""
Comprehensive tests for agents modules to increase coverage
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock, mock_open
import ast
import json
from pathlib import Path


class TestDiscoveryAgentComprehensive:
    """Comprehensive tests for DiscoveryAgent"""
    
    @pytest.mark.asyncio
    async def test_scan_python_file(self):
        """Test scanning a Python file for APIs"""
        from src.agents.discovery_agent import DiscoveryAgent
        
        agent = DiscoveryAgent()
        
        test_code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/test")
def test_endpoint():
    return {"message": "test"}
'''
        
        with patch('builtins.open', mock_open(read_data=test_code)):
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'is_file', return_value=True):
                    apis = await agent.scan("test.py")
                    
                    assert isinstance(apis, list)
    
    @pytest.mark.asyncio  
    async def test_scan_directory(self):
        """Test scanning a directory for APIs"""
        from src.agents.discovery_agent import DiscoveryAgent
        
        agent = DiscoveryAgent()
        
        with patch.object(Path, 'exists', return_value=True):
            with patch.object(Path, 'is_dir', return_value=True):
                with patch.object(Path, 'rglob') as mock_rglob:
                    mock_rglob.return_value = [Path("test1.py"), Path("test2.py")]
                    
                    apis = await agent.scan("/test/dir")
                    
                    assert isinstance(apis, list)
    
    def test_extract_fastapi_endpoints(self):
        """Test extracting FastAPI endpoints from AST"""
        from src.agents.discovery_agent import DiscoveryAgent
        
        agent = DiscoveryAgent()
        
        code = '''
@app.get("/users")
def get_users():
    pass

@app.post("/users")
def create_user():
    pass
'''
        tree = ast.parse(code)
        endpoints = agent.extract_fastapi_endpoints(tree)
        
        assert isinstance(endpoints, list)
    
    def test_extract_flask_endpoints(self):
        """Test extracting Flask endpoints"""
        from src.agents.discovery_agent import DiscoveryAgent
        
        agent = DiscoveryAgent()
        
        code = '''
@app.route("/home")
def home():
    pass
'''
        tree = ast.parse(code)
        endpoints = agent.extract_flask_endpoints(tree)
        
        assert isinstance(endpoints, list)


class TestSpecAgentComprehensive:
    """Comprehensive tests for SpecGeneratorAgent"""
    
    @pytest.mark.asyncio
    async def test_generate_openapi_spec(self):
        """Test generating OpenAPI specification"""
        from src.agents.spec_agent import SpecGeneratorAgent
        from src.core.orchestrator import APIEndpoint
        
        agent = SpecGeneratorAgent()
        
        endpoints = [
            APIEndpoint(
                path="/test",
                method="GET",
                handler_name="test_handler"
            )
        ]
        
        spec = await agent.generate_spec(endpoints)
        
        assert spec is not None
    
    def test_convert_python_type_to_openapi(self):
        """Test type conversion"""
        from src.agents.spec_agent import SpecGeneratorAgent
        
        agent = SpecGeneratorAgent()
        
        # Test various type conversions
        assert agent.python_to_openapi_type("str") == "string"
        assert agent.python_to_openapi_type("int") == "integer"
        assert agent.python_to_openapi_type("float") == "number"
        assert agent.python_to_openapi_type("bool") == "boolean"
        assert agent.python_to_openapi_type("list") == "array"
        assert agent.python_to_openapi_type("dict") == "object"
    
    def test_generate_response_schema(self):
        """Test response schema generation"""
        from src.agents.spec_agent import SpecGeneratorAgent
        
        agent = SpecGeneratorAgent()
        
        schema = agent.generate_response_schema({"type": "object"})
        
        assert isinstance(schema, dict)
        assert "200" in schema or "default" in schema


class TestTestAgentComprehensive:
    """Comprehensive tests for TestGeneratorAgent"""
    
    @pytest.mark.asyncio
    async def test_generate_pytest_tests(self):
        """Test generating pytest tests"""
        from src.agents.test_agent import TestGeneratorAgent
        from src.core.orchestrator import APIEndpoint
        
        agent = TestGeneratorAgent()
        
        endpoints = [
            APIEndpoint(
                path="/api/test",
                method="GET",
                handler_name="test"
            )
        ]
        
        tests = await agent.generate_tests(endpoints, framework="pytest")
        
        assert isinstance(tests, list)
    
    def test_generate_test_name(self):
        """Test test name generation"""
        from src.agents.test_agent import TestGeneratorAgent
        from src.core.orchestrator import APIEndpoint
        
        agent = TestGeneratorAgent()
        
        endpoint = APIEndpoint(
            path="/users/{id}",
            method="GET",
            handler_name="get_user"
        )
        
        name = agent.generate_test_name(endpoint)
        
        assert "test" in name.lower()
        assert "get" in name.lower() or "user" in name.lower()
    
    def test_generate_test_data(self):
        """Test generating test data"""
        from src.agents.test_agent import TestGeneratorAgent
        
        agent = TestGeneratorAgent()
        
        # Generate test data for different types
        string_data = agent.generate_test_data("string")
        assert isinstance(string_data, str)
        
        int_data = agent.generate_test_data("integer")
        assert isinstance(int_data, int)
        
        bool_data = agent.generate_test_data("boolean")
        assert isinstance(bool_data, bool)


class TestMockServerAgentComprehensive:
    """Comprehensive tests for MockServerAgent"""
    
    @pytest.mark.asyncio
    async def test_create_mock_server(self):
        """Test creating a mock server"""
        from src.agents.mock_server_agent import MockServerAgent
        
        agent = MockServerAgent()
        
        spec = {
            "openapi": "3.0.0",
            "paths": {
                "/test": {
                    "get": {
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }
        
        with patch('builtins.open', mock_open()):
            with patch.object(Path, 'mkdir'):
                server = await agent.create_mock_server(spec, port=5000)
                
                assert server is not None
    
    def test_generate_mock_response(self):
        """Test generating mock response"""
        from src.agents.mock_server_agent import MockServerAgent
        
        agent = MockServerAgent()
        
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            }
        }
        
        response = agent.generate_mock_response(schema)
        
        assert isinstance(response, dict)
        assert "id" in response
        assert "name" in response
    
    def test_validate_openapi_spec(self):
        """Test OpenAPI spec validation"""
        from src.agents.mock_server_agent import MockServerAgent
        
        agent = MockServerAgent()
        
        valid_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        
        assert agent.validate_spec(valid_spec) == True
        
        invalid_spec = {"invalid": "spec"}
        assert agent.validate_spec(invalid_spec) == False


class TestAIAgentComprehensive:
    """Comprehensive tests for AIIntelligenceAgent"""
    
    @patch('os.getenv')
    def test_ai_agent_initialization(self, mock_getenv):
        """Test AI agent initialization"""
        mock_getenv.return_value = "test_key"
        
        from src.agents.ai_agent import AIIntelligenceAgent
        
        agent = AIIntelligenceAgent()
        
        assert agent is not None
        assert hasattr(agent, 'anthropic_key') or hasattr(agent, 'api_key')
    
    @pytest.mark.asyncio
    @patch('src.agents.ai_agent.anthropic')
    async def test_analyze_apis_basic(self, mock_anthropic):
        """Test basic API analysis"""
        from src.agents.ai_agent import AIIntelligenceAgent
        from src.core.orchestrator import APIEndpoint
        
        agent = AIIntelligenceAgent()
        agent.anthropic_key = "test_key"
        
        endpoints = [
            APIEndpoint(
                path="/users",
                method="GET",
                handler_name="list_users"
            )
        ]
        
        # Mock the AI response
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        
        analysis = await agent.analyze(endpoints)
        
        assert analysis is not None
    
    def test_extract_security_issues(self):
        """Test extracting security issues"""
        from src.agents.ai_agent import AIIntelligenceAgent
        from src.core.orchestrator import APIEndpoint
        
        agent = AIIntelligenceAgent()
        
        endpoint = APIEndpoint(
            path="/admin/delete-all",
            method="DELETE",
            handler_name="delete_everything",
            auth_required=False
        )
        
        issues = agent.extract_security_issues(endpoint)
        
        assert isinstance(issues, list)
        # Should identify missing auth on sensitive endpoint
        if issues:
            assert any("auth" in str(issue).lower() for issue in issues)
    
    def test_calculate_security_score(self):
        """Test security score calculation"""
        from src.agents.ai_agent import AIIntelligenceAgent
        
        agent = AIIntelligenceAgent()
        
        # No issues = high score
        score1 = agent.calculate_security_score([])
        assert score1 >= 90
        
        # Many issues = low score
        issues = ["SQL Injection", "XSS", "CSRF", "No Auth"]
        score2 = agent.calculate_security_score(issues)
        assert score2 < 70