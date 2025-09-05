"""
Unit tests for API Orchestrator
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from dataclasses import asdict
from src.core.orchestrator import (
    APIOrchestrator, 
    AgentType, 
    AgentMessage,
    APIEndpoint
)


class TestAPIOrchestrator:
    """Test cases for API Orchestrator"""

    def setup_method(self):
        """Setup for each test"""
        self.orchestrator = APIOrchestrator()

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes with correct attributes"""
        assert hasattr(self.orchestrator, 'agents')
        assert hasattr(self.orchestrator, 'message_queue')
        assert hasattr(self.orchestrator, 'results')
        assert isinstance(self.orchestrator.agents, dict)
        assert isinstance(self.orchestrator.message_queue, asyncio.Queue)
        assert isinstance(self.orchestrator.results, dict)

    def test_register_agent(self):
        """Test agent registration"""
        mock_agent = Mock()
        mock_agent.name = "test_agent"
        
        self.orchestrator.register_agent(AgentType.DISCOVERY, mock_agent)
        
        assert AgentType.DISCOVERY in self.orchestrator.agents
        assert self.orchestrator.agents[AgentType.DISCOVERY] == mock_agent

    @pytest.mark.asyncio
    async def test_send_message(self):
        """Test sending message to queue"""
        message = AgentMessage(
            type=AgentType.DISCOVERY,
            action="scan",
            data={"path": "/test"}
        )
        
        await self.orchestrator.send_message(message)
        
        # Check message was added to queue
        queued_message = await self.orchestrator.message_queue.get()
        assert queued_message.type == AgentType.DISCOVERY
        assert queued_message.action == "scan"
        assert queued_message.data == {"path": "/test"}

    @pytest.mark.asyncio
    async def test_process_messages_with_registered_agent(self):
        """Test processing messages with registered agent"""
        mock_agent = Mock()
        mock_agent.process_message = AsyncMock(return_value={"status": "success"})
        
        self.orchestrator.register_agent(AgentType.DISCOVERY, mock_agent)
        
        message = AgentMessage(
            type=AgentType.DISCOVERY,
            action="scan",
            data={"path": "/test"}
        )
        
        await self.orchestrator.send_message(message)
        
        # Process one message
        await self.orchestrator._process_single_message()
        
        mock_agent.process_message.assert_called_once_with(message)
        assert AgentType.DISCOVERY in self.orchestrator.results
        assert self.orchestrator.results[AgentType.DISCOVERY] == {"status": "success"}

    @pytest.mark.asyncio
    async def test_process_messages_without_registered_agent(self):
        """Test processing messages without registered agent"""
        message = AgentMessage(
            type=AgentType.DISCOVERY,
            action="scan",
            data={"path": "/test"}
        )
        
        await self.orchestrator.send_message(message)
        
        # Should handle gracefully
        await self.orchestrator._process_single_message()
        
        # No results should be stored
        assert AgentType.DISCOVERY not in self.orchestrator.results

    @pytest.mark.asyncio
    async def test_orchestrate_api_discovery(self):
        """Test full orchestration flow"""
        source_path = "/test/path"
        
        # Mock all agents
        mock_discovery = Mock()
        mock_discovery.scan = AsyncMock(return_value=[
            APIEndpoint(
                path="/users",
                method="GET",
                handler_name="get_users",
                parameters=[],
                description="Get all users"
            )
        ])
        
        mock_spec = Mock()
        mock_spec.generate = AsyncMock(return_value={"openapi": "3.0.0"})
        
        mock_test = Mock()
        mock_test.generate = AsyncMock(return_value={"tests": []})
        
        mock_ai = Mock()
        mock_ai.analyze = AsyncMock(return_value={"analysis": "complete"})
        
        mock_mock = Mock()
        mock_mock.create = AsyncMock(return_value={"server": "http://localhost:3000"})
        
        # Register all agents
        self.orchestrator.agents = {
            AgentType.DISCOVERY: mock_discovery,
            AgentType.SPEC_GENERATOR: mock_spec,
            AgentType.TEST_GENERATOR: mock_test,
            AgentType.AI_INTELLIGENCE: mock_ai,
            AgentType.MOCK_SERVER: mock_mock
        }
        
        result = await self.orchestrator.orchestrate(source_path)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "endpoints" in result
        assert len(result["endpoints"]) == 1
        assert result["spec"] == {"openapi": "3.0.0"}
        assert result["tests"] == {"tests": []}
        assert result["analysis"] == {"analysis": "complete"}
        assert result["mock_server"] == {"server": "http://localhost:3000"}

    @pytest.mark.asyncio
    async def test_orchestrate_with_websocket_updates(self):
        """Test orchestration with WebSocket status updates"""
        mock_websocket = Mock()
        mock_websocket.send_json = AsyncMock()
        
        source_path = "/test/path"
        
        # Mock discovery agent
        mock_discovery = Mock()
        mock_discovery.scan = AsyncMock(return_value=[])
        
        self.orchestrator.agents = {
            AgentType.DISCOVERY: mock_discovery
        }
        
        result = await self.orchestrator.orchestrate(source_path, mock_websocket)
        
        # Check that status updates were sent
        assert mock_websocket.send_json.called
        
        # Verify at least one status update was sent
        calls = mock_websocket.send_json.call_args_list
        assert any("Discovering APIs" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_orchestrate_error_handling(self):
        """Test orchestration handles errors gracefully"""
        source_path = "/test/path"
        
        # Mock discovery agent that raises error
        mock_discovery = Mock()
        mock_discovery.scan = AsyncMock(side_effect=Exception("Discovery failed"))
        
        self.orchestrator.agents = {
            AgentType.DISCOVERY: mock_discovery
        }
        
        mock_websocket = Mock()
        mock_websocket.send_json = AsyncMock()
        
        result = await self.orchestrator.orchestrate(source_path, mock_websocket)
        
        # Should return result even with error
        assert result is not None
        assert isinstance(result, dict)
        
        # Should send error message
        calls = mock_websocket.send_json.call_args_list
        assert any("error" in str(call).lower() for call in calls)

    @pytest.mark.asyncio
    async def test_message_queue_ordering(self):
        """Test that messages are processed in order"""
        messages = [
            AgentMessage(type=AgentType.DISCOVERY, action="scan", data={"id": 1}),
            AgentMessage(type=AgentType.SPEC_GENERATOR, action="generate", data={"id": 2}),
            AgentMessage(type=AgentType.TEST_GENERATOR, action="generate", data={"id": 3})
        ]
        
        for msg in messages:
            await self.orchestrator.send_message(msg)
        
        # Retrieve messages
        retrieved = []
        for _ in range(3):
            msg = await self.orchestrator.message_queue.get()
            retrieved.append(msg.data["id"])
        
        assert retrieved == [1, 2, 3]

    def test_agent_type_enum(self):
        """Test AgentType enum values"""
        assert AgentType.DISCOVERY
        assert AgentType.SPEC_GENERATOR
        assert AgentType.TEST_GENERATOR
        assert AgentType.AI_INTELLIGENCE
        assert AgentType.MOCK_SERVER
        
        # Test string representation
        assert str(AgentType.DISCOVERY) == "AgentType.DISCOVERY"

    def test_api_endpoint_dataclass(self):
        """Test APIEndpoint dataclass"""
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
        
        # Test conversion to dict
        endpoint_dict = asdict(endpoint)
        assert endpoint_dict["path"] == "/users/{id}"
        assert endpoint_dict["auth_required"] is True

    def test_agent_message_dataclass(self):
        """Test AgentMessage dataclass"""
        message = AgentMessage(
            type=AgentType.DISCOVERY,
            action="scan",
            data={"path": "/test"}
        )
        
        assert message.type == AgentType.DISCOVERY
        assert message.action == "scan"
        assert message.data == {"path": "/test"}
        
        # Test conversion to dict
        message_dict = asdict(message)
        assert message_dict["action"] == "scan"

    @pytest.mark.asyncio
    async def test_process_single_message_exception_handling(self):
        """Test that _process_single_message handles exceptions"""
        mock_agent = Mock()
        mock_agent.process_message = AsyncMock(side_effect=Exception("Agent error"))
        
        self.orchestrator.register_agent(AgentType.DISCOVERY, mock_agent)
        
        message = AgentMessage(
            type=AgentType.DISCOVERY,
            action="scan",
            data={"path": "/test"}
        )
        
        await self.orchestrator.send_message(message)
        
        # Should not raise exception
        await self.orchestrator._process_single_message()
        
        # No results should be stored due to error
        assert AgentType.DISCOVERY not in self.orchestrator.results

    @pytest.mark.asyncio
    async def test_orchestrate_with_partial_agents(self):
        """Test orchestration with only some agents available"""
        source_path = "/test/path"
        
        # Only register discovery and spec agents
        mock_discovery = Mock()
        mock_discovery.scan = AsyncMock(return_value=[
            APIEndpoint(
                path="/api/test",
                method="POST",
                handler_name="test_handler",
                parameters=[]
            )
        ])
        
        mock_spec = Mock()
        mock_spec.generate = AsyncMock(return_value={"openapi": "3.0.0"})
        
        self.orchestrator.agents = {
            AgentType.DISCOVERY: mock_discovery,
            AgentType.SPEC_GENERATOR: mock_spec
        }
        
        result = await self.orchestrator.orchestrate(source_path)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "endpoints" in result
        assert "spec" in result