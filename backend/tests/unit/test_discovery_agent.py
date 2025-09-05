"""
Unit tests for DiscoveryAgent
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from src.agents.discovery_agent import DiscoveryAgent
from src.core.orchestrator import APIEndpoint


class TestDiscoveryAgent:
    """Test cases for DiscoveryAgent"""

    def setup_method(self):
        """Setup for each test"""
        self.agent = DiscoveryAgent()

    def test_agent_initialization(self):
        """Test agent initializes with correct attributes"""
        assert hasattr(self.agent, 'supported_frameworks')
        assert 'fastapi' in self.agent.supported_frameworks
        assert 'flask' in self.agent.supported_frameworks
        assert 'express' in self.agent.supported_frameworks
        assert 'django' in self.agent.supported_frameworks
        assert hasattr(self.agent, 'discovered_apis')
        assert self.agent.discovered_apis == []

    @pytest.mark.asyncio
    async def test_scan_single_file(self):
        """Test scanning a single file"""
        test_content = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            # Mock the _scan_file method
            self.agent._scan_file = AsyncMock()
            
            result = await self.agent.scan(f.name)
            
            self.agent._scan_file.assert_called_once()
            assert isinstance(result, list)
            
            os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_scan_directory(self):
        """Test scanning a directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file1 = Path(tmpdir) / "test1.py"
            test_file1.write_text("from fastapi import FastAPI")
            
            test_file2 = Path(tmpdir) / "test2.js"
            test_file2.write_text("const express = require('express')")
            
            # Mock the _scan_directory method
            self.agent._scan_directory = AsyncMock()
            self.agent._scan_directory.return_value = []
            
            result = await self.agent.scan(tmpdir)
            
            self.agent._scan_directory.assert_called_once()
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_scan_invalid_path(self):
        """Test scanning with invalid path"""
        with pytest.raises(ValueError) as exc_info:
            await self.agent.scan("/nonexistent/path/to/file.py")
        
        assert "not found" in str(exc_info.value)

    def test_parse_fastapi_in_supported_frameworks(self):
        """Test that FastAPI parser is registered"""
        assert 'fastapi' in self.agent.supported_frameworks
        assert callable(self.agent.supported_frameworks['fastapi'])
        assert self.agent.supported_frameworks['fastapi'] == self.agent._parse_fastapi

    def test_parse_flask_in_supported_frameworks(self):
        """Test that Flask parser is registered"""
        assert 'flask' in self.agent.supported_frameworks
        assert callable(self.agent.supported_frameworks['flask'])
        assert self.agent.supported_frameworks['flask'] == self.agent._parse_flask

    def test_parse_express_in_supported_frameworks(self):
        """Test that Express parser is registered"""
        assert 'express' in self.agent.supported_frameworks
        assert callable(self.agent.supported_frameworks['express'])
        assert self.agent.supported_frameworks['express'] == self.agent._parse_express

    def test_parse_django_in_supported_frameworks(self):
        """Test that Django parser is registered"""
        assert 'django' in self.agent.supported_frameworks
        assert callable(self.agent.supported_frameworks['django'])
        assert self.agent.supported_frameworks['django'] == self.agent._parse_django

    @pytest.mark.asyncio
    async def test_scan_file_with_fastapi(self):
        """Test scanning a FastAPI file"""
        test_content = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
        '''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            f.flush()
            
            # Mock _scan_file to set discovered_apis
            mock_endpoint = APIEndpoint(
                path="/users/{user_id}",
                method="GET",
                handler_name="get_user",
                parameters=[{"name": "user_id", "type": "int"}],
                response_schema=None,
                description="Get user by ID",
                auth_required=False,
                rate_limit=None
            )
            
            # Mock _scan_file to add endpoint to discovered_apis
            async def mock_scan_file(file_path):
                self.agent.discovered_apis.append(mock_endpoint)
            
            self.agent._scan_file = mock_scan_file
            
            result = await self.agent.scan(f.name)
            
            assert len(result) == 1
            assert result[0].path == "/users/{user_id}"
            
            os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_scan_excludes_venv_and_node_modules(self):
        """Test that scan excludes venv and node_modules directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create directories that should be excluded
            venv_dir = Path(tmpdir) / "venv" / "lib"
            venv_dir.mkdir(parents=True)
            (venv_dir / "test.py").write_text("# Should be excluded")
            
            node_modules_dir = Path(tmpdir) / "node_modules"
            node_modules_dir.mkdir()
            (node_modules_dir / "test.js").write_text("// Should be excluded")
            
            # Create a file that should be included
            (Path(tmpdir) / "app.py").write_text("from fastapi import FastAPI")
            
            # Mock the _scan_file method to track calls
            self.agent._scan_file = AsyncMock()
            
            await self.agent.scan(tmpdir)
            
            # Check that _scan_file was called only for app.py
            called_paths = [call[0][0] for call in self.agent._scan_file.call_args_list]
            called_filenames = [p.name for p in called_paths]
            
            assert "app.py" in called_filenames
            assert "test.py" not in called_filenames
            assert "test.js" not in called_filenames

    @pytest.mark.asyncio
    async def test_discovered_apis_reset_on_scan(self):
        """Test that discovered_apis is reset when scan is called"""
        # Add some initial APIs
        mock_endpoint = APIEndpoint(
            path="/old",
            method="GET",
            handler_name="old_handler",
            parameters=[],
            response_schema=None,
            description="Old endpoint",
            auth_required=False,
            rate_limit=None
        )
        self.agent.discovered_apis = [mock_endpoint]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Empty file")
            f.flush()
            
            # Mock _scan_file to do nothing
            self.agent._scan_file = AsyncMock()
            
            result = await self.agent.scan(f.name)
            
            # discovered_apis should be reset (empty now since _scan_file is mocked)
            assert result == []
            
            os.unlink(f.name)

    def test_supported_frameworks_structure(self):
        """Test the structure of supported_frameworks dictionary"""
        assert isinstance(self.agent.supported_frameworks, dict)
        assert len(self.agent.supported_frameworks) >= 4  # At least 4 frameworks
        
        for framework_name, parser_func in self.agent.supported_frameworks.items():
            assert isinstance(framework_name, str)
            assert callable(parser_func)
            # Check that parser functions are methods of the agent
            assert hasattr(self.agent, parser_func.__name__)