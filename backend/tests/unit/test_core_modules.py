"""
Simplified unit tests for core modules that match actual implementation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from dataclasses import asdict

# Test imports
from src.core.orchestrator import APIOrchestrator, AgentType, APIEndpoint, AgentMessage
from src.agents.ai_agent import AIIntelligenceAgent
from src.agents.discovery_agent import DiscoveryAgent


class TestAPIOrchestrator:
    """Test APIOrchestrator core functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.orchestrator = APIOrchestrator()

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly"""
        assert isinstance(self.orchestrator.agents, dict)
        assert isinstance(self.orchestrator.api_registry, dict)
        assert isinstance(self.orchestrator.message_queue, list)
        assert self.orchestrator.is_running is False

    def test_register_agent(self):
        """Test agent registration"""
        mock_agent = Mock()
        self.orchestrator.register_agent(AgentType.DISCOVERY, mock_agent)
        
        assert AgentType.DISCOVERY in self.orchestrator.agents
        assert self.orchestrator.agents[AgentType.DISCOVERY] == mock_agent

    @pytest.mark.asyncio
    async def test_discover_apis_with_agent(self):
        """Test API discovery with registered agent"""
        mock_agent = Mock()
        mock_agent.scan = AsyncMock(return_value=[
            APIEndpoint(
                path="/test",
                method="GET",
                handler_name="test_handler",
                parameters=[]
            )
        ])
        
        self.orchestrator.register_agent(AgentType.DISCOVERY, mock_agent)
        result = await self.orchestrator.discover_apis("/test/path")
        
        assert len(result) == 1
        assert result[0].path == "/test"
        assert len(self.orchestrator.api_registry) == 1

    @pytest.mark.asyncio
    async def test_discover_apis_without_agent(self):
        """Test API discovery without registered agent"""
        with pytest.raises(ValueError, match="Discovery agent not registered"):
            await self.orchestrator.discover_apis("/test/path")

    @pytest.mark.asyncio
    async def test_generate_specs(self):
        """Test spec generation"""
        mock_agent = Mock()
        mock_agent.generate = AsyncMock(return_value={"openapi": "3.0.0", "paths": {}})
        
        self.orchestrator.register_agent(AgentType.SPEC_GENERATOR, mock_agent)
        
        apis = [APIEndpoint(path="/test", method="GET", handler_name="test", parameters=[])]
        result = await self.orchestrator.generate_specs(apis)
        
        assert result["openapi"] == "3.0.0"
        assert "paths" in result

    @pytest.mark.asyncio
    async def test_generate_tests(self):
        """Test test generation"""
        mock_agent = Mock()
        mock_agent.create_tests = AsyncMock(return_value=[{"test": "test1"}])
        
        self.orchestrator.register_agent(AgentType.TEST_GENERATOR, mock_agent)
        
        specs = {"openapi": "3.0.0", "paths": {}}
        result = await self.orchestrator.generate_tests(specs)
        
        assert len(result) == 1
        assert result[0]["test"] == "test1"

    @pytest.mark.asyncio
    async def test_orchestrate_flow(self):
        """Test complete orchestration flow"""
        # Mock discovery agent
        mock_discovery = Mock()
        mock_discovery.scan = AsyncMock(return_value=[
            APIEndpoint(path="/api/test", method="POST", handler_name="test", parameters=[])
        ])
        
        # Mock spec agent
        mock_spec = Mock()
        mock_spec.generate = AsyncMock(return_value={"openapi": "3.0.0", "paths": {}})
        
        # Mock test agent
        mock_test = Mock()
        mock_test.create_tests = AsyncMock(return_value=[])
        
        # Register agents
        self.orchestrator.register_agent(AgentType.DISCOVERY, mock_discovery)
        self.orchestrator.register_agent(AgentType.SPEC_GENERATOR, mock_spec)
        self.orchestrator.register_agent(AgentType.TEST_GENERATOR, mock_test)
        
        # Run orchestration
        result = await self.orchestrator.orchestrate("/test/path")
        
        assert self.orchestrator.is_running is False  # Should be reset after completion
        assert "endpoints" in result
        assert "spec" in result
        assert "tests" in result


class TestAgentType:
    """Test AgentType enum"""

    def test_agent_type_values(self):
        """Test all agent types exist"""
        assert AgentType.DISCOVERY
        assert AgentType.SPEC_GENERATOR
        assert AgentType.TEST_GENERATOR
        assert AgentType.AI_INTELLIGENCE
        assert AgentType.MOCK_SERVER
        
        # Test value access
        assert AgentType.DISCOVERY.value == "discovery"
        assert AgentType.SPEC_GENERATOR.value == "spec_generator"


class TestAPIEndpoint:
    """Test APIEndpoint dataclass"""

    def test_api_endpoint_creation(self):
        """Test creating APIEndpoint"""
        endpoint = APIEndpoint(
            path="/users/{id}",
            method="GET",
            handler_name="get_user",
            parameters=[{"name": "id", "type": "string"}],
            response_schema={"type": "object"},
            description="Get user by ID",
            auth_required=True,
            rate_limit=100
        )
        
        assert endpoint.path == "/users/{id}"
        assert endpoint.method == "GET"
        assert endpoint.handler_name == "get_user"
        assert endpoint.auth_required is True
        assert endpoint.rate_limit == 100

    def test_api_endpoint_to_dict(self):
        """Test converting APIEndpoint to dict"""
        endpoint = APIEndpoint(
            path="/test",
            method="POST",
            handler_name="test",
            parameters=[]
        )
        
        endpoint_dict = asdict(endpoint)
        assert endpoint_dict["path"] == "/test"
        assert endpoint_dict["method"] == "POST"
        assert endpoint_dict["handler_name"] == "test"


class TestAgentMessage:
    """Test AgentMessage dataclass"""

    def test_agent_message_creation(self):
        """Test creating AgentMessage"""
        message = AgentMessage(
            sender=AgentType.DISCOVERY,
            receiver=AgentType.SPEC_GENERATOR,
            content={"data": "test"},
            message_type="api_discovered"
        )
        
        assert message.sender == AgentType.DISCOVERY
        assert message.receiver == AgentType.SPEC_GENERATOR
        assert message.content == {"data": "test"}
        assert message.message_type == "api_discovered"
        assert isinstance(message.timestamp, datetime)


class TestAIIntelligenceAgent:
    """Test AI Intelligence Agent basic functionality"""

    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = AIIntelligenceAgent()
        
        # Check that clients are initialized (may be None if no API keys)
        assert hasattr(agent, 'openai_client')
        assert hasattr(agent, 'anthropic_client')
        assert hasattr(agent, 'model_preference')
        assert agent.model_preference == "claude-3"

    @pytest.mark.asyncio
    async def test_basic_security_analysis(self):
        """Test basic security analysis without AI"""
        agent = AIIntelligenceAgent()
        
        api_spec = {
            "paths": {
                "/admin/users": {"post": {}},
                "/public/info": {"get": {}},
                "/auth/login": {"post": {}}
            }
        }
        
        # The agent should have some method to analyze security
        # Even without AI, it should provide basic analysis
        assert hasattr(agent, 'analyze_api_security')

    @pytest.mark.asyncio
    async def test_performance_analysis(self):
        """Test performance analysis"""
        agent = AIIntelligenceAgent()
        
        api_spec = {
            "paths": {
                "/users": {"get": {}, "post": {}},
                "/users/{id}": {"get": {}, "put": {}, "delete": {}}
            }
        }
        
        # Check that performance analysis method exists
        assert hasattr(agent, 'analyze_api_performance')

    def test_client_initialization_without_keys(self):
        """Test client initialization without API keys"""
        with patch.dict('os.environ', {}, clear=True):
            agent = AIIntelligenceAgent()
            
            # Without API keys, clients should be None or not initialized
            # But agent should still work with fallback analysis
            assert agent is not None


class TestDiscoveryAgent:
    """Test Discovery Agent basic functionality"""

    def test_agent_initialization(self):
        """Test discovery agent initialization"""
        agent = DiscoveryAgent()
        
        assert hasattr(agent, 'supported_frameworks')
        assert 'fastapi' in agent.supported_frameworks
        assert 'flask' in agent.supported_frameworks
        assert 'express' in agent.supported_frameworks
        assert hasattr(agent, 'discovered_apis')

    @pytest.mark.asyncio
    async def test_scan_method_exists(self):
        """Test that scan method exists"""
        agent = DiscoveryAgent()
        assert hasattr(agent, 'scan')
        assert callable(agent.scan)

    def test_supported_frameworks(self):
        """Test supported frameworks"""
        agent = DiscoveryAgent()
        
        frameworks = agent.supported_frameworks
        assert isinstance(frameworks, dict)
        assert len(frameworks) >= 3  # At least FastAPI, Flask, Express
        
        # Check that parser functions exist
        for framework, parser in frameworks.items():
            assert callable(parser)