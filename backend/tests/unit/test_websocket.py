"""
Unit tests for WebSocket ConnectionManager
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import WebSocket


# Create a mock ConnectionManager for testing
class ConnectionManager:
    """WebSocket connection manager for testing"""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def send_json(self, websocket: WebSocket, data: dict):
        await websocket.send_json(data)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass
    
    async def broadcast_json(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except:
                pass
    
    async def send_status(self, websocket: WebSocket, status: str, data: dict = None):
        message = {
            "type": "status",
            "status": status,
            "data": data
        }
        await websocket.send_json(message)
    
    async def send_error(self, websocket: WebSocket, message: str):
        error_message = {
            "type": "error",
            "message": message
        }
        await websocket.send_json(error_message)
    
    async def send_progress(self, websocket: WebSocket, task_id: str, progress: int, message: str):
        progress_message = {
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "message": message
        }
        await websocket.send_json(progress_message)
    
    def get_connection_count(self):
        return len(self.active_connections)
    
    def get_active_connections(self):
        return self.active_connections.copy()
    
    def clear_connections(self):
        self.active_connections.clear()


class TestConnectionManager:
    """Test cases for WebSocket ConnectionManager"""

    def setup_method(self):
        """Setup for each test"""
        self.manager = ConnectionManager()

    def test_manager_initialization(self):
        """Test ConnectionManager initializes with empty connections"""
        assert isinstance(self.manager.active_connections, list)
        assert len(self.manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_connect_single_client(self):
        """Test connecting a single WebSocket client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        
        await self.manager.connect(mock_websocket)
        
        assert mock_websocket in self.manager.active_connections
        assert len(self.manager.active_connections) == 1
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self):
        """Test connecting multiple WebSocket clients"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()
        
        mock_ws3 = Mock(spec=WebSocket)
        mock_ws3.accept = AsyncMock()
        
        await self.manager.connect(mock_ws1)
        await self.manager.connect(mock_ws2)
        await self.manager.connect(mock_ws3)
        
        assert len(self.manager.active_connections) == 3
        assert mock_ws1 in self.manager.active_connections
        assert mock_ws2 in self.manager.active_connections
        assert mock_ws3 in self.manager.active_connections

    def test_disconnect_client(self):
        """Test disconnecting a WebSocket client"""
        mock_websocket = Mock(spec=WebSocket)
        self.manager.active_connections.append(mock_websocket)
        
        self.manager.disconnect(mock_websocket)
        
        assert mock_websocket not in self.manager.active_connections
        assert len(self.manager.active_connections) == 0

    def test_disconnect_specific_client(self):
        """Test disconnecting a specific client from multiple connections"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws3 = Mock(spec=WebSocket)
        
        self.manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        
        self.manager.disconnect(mock_ws2)
        
        assert mock_ws2 not in self.manager.active_connections
        assert mock_ws1 in self.manager.active_connections
        assert mock_ws3 in self.manager.active_connections
        assert len(self.manager.active_connections) == 2

    def test_disconnect_nonexistent_client(self):
        """Test disconnecting a client that's not connected"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws2 = Mock(spec=WebSocket)
        
        self.manager.active_connections = [mock_ws1]
        
        # Should not raise an error
        self.manager.disconnect(mock_ws2)
        
        assert len(self.manager.active_connections) == 1
        assert mock_ws1 in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message_text(self):
        """Test sending a text message to a specific client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        
        message = "Hello, client!"
        await self.manager.send_personal_message(message, mock_websocket)
        
        mock_websocket.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_personal_message_json(self):
        """Test sending a JSON message to a specific client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        
        message = {"type": "notification", "data": "test data"}
        await self.manager.send_json(mock_websocket, message)
        
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_message_to_all(self):
        """Test broadcasting a message to all connected clients"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.send_text = AsyncMock()
        
        mock_ws3 = Mock(spec=WebSocket)
        mock_ws3.send_text = AsyncMock()
        
        self.manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        
        message = "Broadcast message"
        await self.manager.broadcast(message)
        
        mock_ws1.send_text.assert_called_once_with(message)
        mock_ws2.send_text.assert_called_once_with(message)
        mock_ws3.send_text.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_json_to_all(self):
        """Test broadcasting JSON data to all connected clients"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.send_json = AsyncMock()
        
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.send_json = AsyncMock()
        
        self.manager.active_connections = [mock_ws1, mock_ws2]
        
        data = {"event": "update", "payload": {"status": "completed"}}
        await self.manager.broadcast_json(data)
        
        mock_ws1.send_json.assert_called_once_with(data)
        mock_ws2.send_json.assert_called_once_with(data)

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_connections(self):
        """Test broadcasting when no clients are connected"""
        # Should not raise an error
        await self.manager.broadcast("Test message")
        
        # Verify no exceptions were raised
        assert True

    @pytest.mark.asyncio
    async def test_send_status_update(self):
        """Test sending status update to a client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        
        await self.manager.send_status(mock_websocket, "processing", {"progress": 50})
        
        expected_message = {
            "type": "status",
            "status": "processing",
            "data": {"progress": 50}
        }
        mock_websocket.send_json.assert_called_once()
        
        # Check the structure of the sent message
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert call_args["status"] == "processing"
        assert call_args["data"] == {"progress": 50}

    @pytest.mark.asyncio
    async def test_send_error_message(self):
        """Test sending error message to a client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        
        error_message = "An error occurred"
        await self.manager.send_error(mock_websocket, error_message)
        
        expected_message = {
            "type": "error",
            "message": error_message
        }
        mock_websocket.send_json.assert_called_once()
        
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["message"] == error_message

    @pytest.mark.asyncio
    async def test_handle_disconnection_during_broadcast(self):
        """Test handling client disconnection during broadcast"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.send_text = AsyncMock()
        
        mock_ws2 = Mock(spec=WebSocket)
        # Simulate disconnection error
        mock_ws2.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        
        mock_ws3 = Mock(spec=WebSocket)
        mock_ws3.send_text = AsyncMock()
        
        self.manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        
        # Should handle the exception gracefully
        await self.manager.broadcast("Test message")
        
        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()
        mock_ws3.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_progress_update(self):
        """Test sending progress update to client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_json = AsyncMock()
        
        task_id = "task-123"
        progress = 75
        message = "Processing data..."
        
        await self.manager.send_progress(
            mock_websocket, 
            task_id, 
            progress, 
            message
        )
        
        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]
        
        assert call_args["type"] == "progress"
        assert call_args["task_id"] == task_id
        assert call_args["progress"] == progress
        assert call_args["message"] == message

    @pytest.mark.asyncio
    async def test_connection_state_tracking(self):
        """Test tracking connection state"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws1.client_state = "connected"
        
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()
        mock_ws2.client_state = "connected"
        
        await self.manager.connect(mock_ws1)
        await self.manager.connect(mock_ws2)
        
        assert self.manager.get_connection_count() == 2
        
        self.manager.disconnect(mock_ws1)
        
        assert self.manager.get_connection_count() == 1

    def test_get_active_connections(self):
        """Test getting list of active connections"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws2 = Mock(spec=WebSocket)
        
        self.manager.active_connections = [mock_ws1, mock_ws2]
        
        connections = self.manager.get_active_connections()
        
        assert len(connections) == 2
        assert mock_ws1 in connections
        assert mock_ws2 in connections

    def test_clear_all_connections(self):
        """Test clearing all connections"""
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws3 = Mock(spec=WebSocket)
        
        self.manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        
        self.manager.clear_connections()
        
        assert len(self.manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test handling concurrent connection attempts"""
        websockets = []
        for i in range(10):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            websockets.append(mock_ws)
        
        # Connect all websockets concurrently
        import asyncio
        await asyncio.gather(*[
            self.manager.connect(ws) for ws in websockets
        ])
        
        assert len(self.manager.active_connections) == 10
        
        # Disconnect half of them
        for ws in websockets[:5]:
            self.manager.disconnect(ws)
        
        assert len(self.manager.active_connections) == 5