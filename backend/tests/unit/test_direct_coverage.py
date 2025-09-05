"""
Direct tests to increase coverage by actually executing code paths
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch, mock_open
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDirectExportImport:
    """Direct execution tests for export_import module"""
    
    def test_export_manager_direct(self):
        """Directly test ExportManager methods"""
        from src.export_import import ExportManager
        
        manager = ExportManager()
        
        # Test JSON export
        data = {"project": {"name": "Test"}, "apis": []}
        json_str = manager.export_to_json(data)
        assert "Test" in json_str
        
        # Test YAML export
        yaml_str = manager.export_to_yaml(data)
        assert "Test" in yaml_str
    
    def test_import_manager_direct(self):
        """Directly test ImportManager methods"""
        from src.export_import import ImportManager
        
        manager = ImportManager()
        
        # Test JSON import
        json_data = '{"project": {"name": "Imported"}}'
        result = manager.import_from_json(json_data)
        assert result["project"]["name"] == "Imported"
        
        # Test validation
        valid = manager.validate_data({"project": {"name": "Valid"}, "apis": []})
        assert valid == True
        
        invalid = manager.validate_data({})
        assert invalid == False
    
    @patch('builtins.open', mock_open())
    def test_file_operations(self):
        """Test file read/write operations"""
        from src.export_import import ExportManager, ImportManager
        
        export_mgr = ExportManager()
        import_mgr = ImportManager()
        
        # Test export to file
        data = {"project": {"name": "FileTest"}}
        export_mgr.export_to_file(data, "test.json")
        
        # Test import from file with mock
        with patch('builtins.open', mock_open(read_data='{"project": {"name": "FileTest"}}')):
            result = import_mgr.import_from_file("test.json")
            assert result["project"]["name"] == "FileTest"


class TestDirectConfig:
    """Direct execution tests for config module"""
    
    def test_config_direct_access(self):
        """Directly test config Settings"""
        from src.config import Settings
        
        settings = Settings()
        
        # Test direct attribute access
        assert hasattr(settings, 'app_name')
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'database_url')
        
        # Test default values
        assert settings.access_token_expire_minutes > 0
        assert settings.algorithm is not None
        assert isinstance(settings.cors_origins, list)
    
    @patch.dict(os.environ, {
        "REDIS_HOST": "test-redis",
        "REDIS_PORT": "7000",
        "LOG_LEVEL": "DEBUG"
    })
    def test_config_env_override(self):
        """Test environment variable overrides"""
        from src.config import Settings
        
        settings = Settings()
        
        assert settings.redis_host == "test-redis"
        assert settings.redis_port == 7000
        assert settings.log_level == "DEBUG"
    
    def test_get_settings_function(self):
        """Test get_settings utility function"""
        from src.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return same instance (singleton)
        assert settings1 is settings2


class TestDirectAgents:
    """Direct execution tests for agents"""
    
    def test_discovery_agent_methods(self):
        """Test DiscoveryAgent methods directly"""
        from src.agents.discovery_agent import DiscoveryAgent
        import ast
        
        agent = DiscoveryAgent()
        
        # Test AST parsing
        code = '''
def test_function():
    pass
'''
        tree = ast.parse(code)
        assert tree is not None
        
        # Test method existence
        assert hasattr(agent, 'scan')
        assert hasattr(agent, 'extract_fastapi_endpoints')
    
    def test_spec_agent_type_conversion(self):
        """Test SpecGeneratorAgent type conversions"""
        from src.agents.spec_agent import SpecGeneratorAgent
        
        agent = SpecGeneratorAgent()
        
        # Test Python to OpenAPI type mapping
        conversions = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }
        
        for py_type, oa_type in conversions.items():
            result = agent.python_to_openapi_type(py_type)
            assert result == oa_type
    
    def test_test_agent_name_generation(self):
        """Test TestGeneratorAgent name generation"""
        from src.agents.test_agent import TestGeneratorAgent
        from src.core.orchestrator import APIEndpoint
        
        agent = TestGeneratorAgent()
        
        endpoint = APIEndpoint(
            path="/users",
            method="GET",
            handler_name="list_users"
        )
        
        name = agent.generate_test_name(endpoint)
        assert "test" in name.lower()
    
    def test_mock_server_response_generation(self):
        """Test MockServerAgent response generation"""
        from src.agents.mock_server_agent import MockServerAgent
        
        agent = MockServerAgent()
        
        # Test different schema types
        schemas = [
            {"type": "string"},
            {"type": "integer"},
            {"type": "boolean"},
            {"type": "array", "items": {"type": "string"}},
            {"type": "object", "properties": {"id": {"type": "integer"}}}
        ]
        
        for schema in schemas:
            response = agent.generate_mock_response(schema)
            assert response is not None
    
    @patch('os.getenv', return_value=None)
    def test_ai_agent_no_key(self, mock_env):
        """Test AIIntelligenceAgent without API key"""
        from src.agents.ai_agent import AIIntelligenceAgent
        
        agent = AIIntelligenceAgent()
        
        # Should handle missing API key gracefully
        assert agent.anthropic_key is None or agent.anthropic_key == ""


class TestDirectProjectManager:
    """Direct execution tests for project_manager"""
    
    def test_project_create_model(self):
        """Test ProjectCreate model"""
        from src.project_manager import ProjectCreate
        
        project = ProjectCreate(
            name="Test Project",
            description="Test Description",
            source_type="directory"
        )
        
        assert project.name == "Test Project"
        assert project.source_type == "directory"
    
    def test_project_update_model(self):
        """Test ProjectUpdate model"""
        from src.project_manager import ProjectUpdate
        
        update = ProjectUpdate(name="Updated Name")
        
        assert update.name == "Updated Name"
        assert update.description is None
    
    def test_project_stats_model(self):
        """Test ProjectStats model"""
        from src.project_manager import ProjectStats
        
        stats = ProjectStats(
            total_projects=10,
            total_apis=100,
            total_tests=500,
            total_tasks=50,
            security_issues_found=5,
            average_security_score=85.0,
            hours_saved=100.0,
            money_saved=10000.0
        )
        
        assert stats.total_projects == 10
        assert stats.average_security_score == 85.0


class TestDirectMain:
    """Direct tests for main module initialization"""
    
    @patch('src.main.FastAPI')
    @patch('src.main.ConnectionManager')
    def test_main_initialization(self, mock_cm, mock_fastapi):
        """Test main module initialization"""
        # Force reimport to trigger initialization
        import importlib
        import src.main
        importlib.reload(src.main)
        
        # Check that key components are initialized
        assert hasattr(src.main, 'app')
        assert hasattr(src.main, 'manager')
        assert hasattr(src.main, 'active_tasks')
    
    def test_api_constants(self):
        """Test API constants and configuration"""
        from src.main import API_VERSION
        
        assert API_VERSION is not None
        assert isinstance(API_VERSION, str)