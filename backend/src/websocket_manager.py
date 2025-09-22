#!/usr/bin/env python3
"""
Real-time WebSocket Manager for AI Interactions
Handles streaming code generation, RAG queries, and live AI responses
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from fastapi import WebSocket
from dataclasses import dataclass


@dataclass
class WebSocketMessage:
    """Standard WebSocket message format"""

    id: str
    type: str
    data: Any
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ActiveConnection:
    """Active WebSocket connection info"""

    websocket: WebSocket
    user_id: str
    session_id: str
    connected_at: datetime
    last_activity: datetime
    subscriptions: List[str]


class WebSocketManager:
    """
    Manages WebSocket connections for real-time AI interactions
    Supports streaming code generation, RAG queries, and live updates
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Connection management
        self.active_connections: Dict[str, ActiveConnection] = {}
        self.user_connections: Dict[str, List[str]] = {}  # user_id -> connection_ids

        # Message routing
        self.message_handlers: Dict[str, Callable] = {}
        self.subscription_handlers: Dict[str, List[str]] = {}  # topic -> connection_ids

        # Performance tracking
        self.message_stats = {
            "total_messages": 0,
            "messages_per_type": {},
            "active_sessions": 0,
            "peak_connections": 0,
        }

        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Setup default message handlers"""
        self.message_handlers.update(
            {
                "code_generation_request": self._handle_code_generation,
                "rag_query": self._handle_rag_query,
                "subscribe": self._handle_subscription,
                "unsubscribe": self._handle_unsubscription,
                "ping": self._handle_ping,
                "get_stats": self._handle_get_stats,
            }
        )

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """Accept a new WebSocket connection"""
        await websocket.accept()

        connection_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        connection = ActiveConnection(
            websocket=websocket,
            user_id=user_id,
            session_id=session_id,
            connected_at=datetime.now(),
            last_activity=datetime.now(),
            subscriptions=[],
        )

        self.active_connections[connection_id] = connection

        # Track user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)

        # Update stats
        self.message_stats["active_sessions"] = len(self.active_connections)
        if len(self.active_connections) > self.message_stats["peak_connections"]:
            self.message_stats["peak_connections"] = len(self.active_connections)

        self.logger.info(f"✅ WebSocket connected: {connection_id} (user: {user_id})")

        # Send welcome message
        await self._send_message(
            connection_id,
            {
                "type": "connection_established",
                "data": {
                    "connection_id": connection_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "features": ["code_generation", "rag_queries", "live_updates"],
                },
            },
        )

        return connection_id

    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            user_id = connection.user_id

            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].remove(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from subscriptions
            for topic in connection.subscriptions:
                if topic in self.subscription_handlers:
                    if connection_id in self.subscription_handlers[topic]:
                        self.subscription_handlers[topic].remove(connection_id)

            # Remove connection
            del self.active_connections[connection_id]

            # Update stats
            self.message_stats["active_sessions"] = len(self.active_connections)

            self.logger.info(
                f"❌ WebSocket disconnected: {connection_id} (user: {user_id})"
            )

    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        try:
            if connection_id not in self.active_connections:
                return

            connection = self.active_connections[connection_id]
            connection.last_activity = datetime.now()

            # Parse message
            message_type = message.get("type")
            message_data = message.get("data", {})
            message_id = message.get("id", str(uuid.uuid4()))

            # Update stats
            self.message_stats["total_messages"] += 1
            if message_type not in self.message_stats["messages_per_type"]:
                self.message_stats["messages_per_type"][message_type] = 0
            self.message_stats["messages_per_type"][message_type] += 1

            # Route message to appropriate handler
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](
                    connection_id, message_data, message_id
                )
            else:
                await self._send_error(
                    connection_id, f"Unknown message type: {message_type}", message_id
                )

        except Exception as e:
            self.logger.error(f"Error handling message from {connection_id}: {e}")
            await self._send_error(
                connection_id, "Internal server error", message.get("id")
            )

    async def _handle_code_generation(
        self, connection_id: str, data: Dict[str, Any], message_id: str
    ):
        """Handle streaming code generation request"""
        try:
            from autonomous_code_generation import (
                AutonomousCodeGenerator,
                CodeLanguage,
                CodeType,
                QualityLevel,
            )

            description = data.get("description", "")
            language = data.get("language", "python")
            code_type = data.get("code_type", "utility_function")

            if not description:
                await self._send_error(
                    connection_id, "Description is required", message_id
                )
                return

            # Send acknowledgment
            await self._send_message(
                connection_id,
                {
                    "type": "code_generation_started",
                    "data": {"message_id": message_id, "description": description},
                    "id": message_id,
                },
            )

            # Initialize code generator
            generator = AutonomousCodeGenerator()

            # Generate code with streaming updates
            result = await generator.generate_code_from_description(
                description=description,
                language=CodeLanguage(language.lower()),
                code_type=CodeType(code_type.lower()),
                quality_level=QualityLevel.PRODUCTION,
            )

            # Send streaming updates (simulate streaming for now)
            progress_steps = [
                {"step": "analyzing_requirements", "progress": 20},
                {"step": "generating_structure", "progress": 40},
                {"step": "adding_business_logic", "progress": 60},
                {"step": "adding_error_handling", "progress": 80},
                {"step": "finalizing_code", "progress": 100},
            ]

            for step in progress_steps:
                await self._send_message(
                    connection_id,
                    {
                        "type": "code_generation_progress",
                        "data": step,
                        "id": message_id,
                    },
                )
                await asyncio.sleep(0.5)  # Simulate processing time

            # Send final result
            await self._send_message(
                connection_id,
                {
                    "type": "code_generation_complete",
                    "data": {
                        "code": result.generated_code,
                        "documentation": result.documentation,
                        "test_code": result.test_code,
                        "quality_score": result.quality_score,
                        "security_score": result.security_score,
                        "dependencies": result.dependencies,
                        "generation_time": result.generation_time,
                    },
                    "id": message_id,
                },
            )

        except Exception as e:
            self.logger.error(f"Code generation error: {e}")
            await self._send_error(
                connection_id, f"Code generation failed: {str(e)}", message_id
            )

    async def _handle_rag_query(
        self, connection_id: str, data: Dict[str, Any], message_id: str
    ):
        """Handle RAG knowledge query"""
        try:
            from rag_knowledge_system import EnhancedRAGKnowledgeSystem

            query = data.get("query", "")
            user_id = self.active_connections[connection_id].user_id

            if not query:
                await self._send_error(connection_id, "Query is required", message_id)
                return

            # Send acknowledgment
            await self._send_message(
                connection_id,
                {
                    "type": "rag_query_started",
                    "data": {"message_id": message_id, "query": query},
                    "id": message_id,
                },
            )

            # Initialize RAG system
            rag = EnhancedRAGKnowledgeSystem()

            # Update conversation memory
            rag.update_conversation_memory(user_id, query)

            # Perform semantic search
            results = await rag.get_industry_intelligence(
                query, {"endpoint": "/api/query"}, user_id
            )

            # Get conversation context
            context = rag.get_conversation_context(user_id)

            # Send results
            await self._send_message(
                connection_id,
                {
                    "type": "rag_query_complete",
                    "data": {"results": results, "context": context, "query": query},
                    "id": message_id,
                },
            )

        except Exception as e:
            self.logger.error(f"RAG query error: {e}")
            await self._send_error(
                connection_id, f"RAG query failed: {str(e)}", message_id
            )

    async def _handle_subscription(
        self, connection_id: str, data: Dict[str, Any], message_id: str
    ):
        """Handle topic subscription"""
        topic = data.get("topic")
        if not topic:
            await self._send_error(connection_id, "Topic is required", message_id)
            return

        connection = self.active_connections[connection_id]

        if topic not in connection.subscriptions:
            connection.subscriptions.append(topic)

        if topic not in self.subscription_handlers:
            self.subscription_handlers[topic] = []

        if connection_id not in self.subscription_handlers[topic]:
            self.subscription_handlers[topic].append(connection_id)

        await self._send_message(
            connection_id,
            {
                "type": "subscription_confirmed",
                "data": {"topic": topic},
                "id": message_id,
            },
        )

    async def _handle_unsubscription(
        self, connection_id: str, data: Dict[str, Any], message_id: str
    ):
        """Handle topic unsubscription"""
        topic = data.get("topic")
        if not topic:
            await self._send_error(connection_id, "Topic is required", message_id)
            return

        connection = self.active_connections[connection_id]

        if topic in connection.subscriptions:
            connection.subscriptions.remove(topic)

        if (
            topic in self.subscription_handlers
            and connection_id in self.subscription_handlers[topic]
        ):
            self.subscription_handlers[topic].remove(connection_id)

        await self._send_message(
            connection_id,
            {
                "type": "unsubscription_confirmed",
                "data": {"topic": topic},
                "id": message_id,
            },
        )

    async def _handle_ping(
        self, connection_id: str, data: Dict[str, Any], message_id: str
    ):
        """Handle ping message"""
        await self._send_message(
            connection_id,
            {
                "type": "pong",
                "data": {"timestamp": datetime.now().isoformat()},
                "id": message_id,
            },
        )

    async def _handle_get_stats(
        self, connection_id: str, data: Dict[str, Any], message_id: str
    ):
        """Handle stats request"""
        await self._send_message(
            connection_id,
            {"type": "stats", "data": self.message_stats.copy(), "id": message_id},
        )

    async def _send_message(self, connection_id: str, message: Dict[str, Any]):
        """Send message to specific connection"""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id].websocket
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                self.logger.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)

    async def _send_error(self, connection_id: str, error: str, message_id: str = None):
        """Send error message"""
        await self._send_message(
            connection_id, {"type": "error", "data": {"error": error}, "id": message_id}
        )

    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """Broadcast message to all subscribers of a topic"""
        if topic in self.subscription_handlers:
            for connection_id in self.subscription_handlers[topic].copy():
                await self._send_message(connection_id, message)

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast message to all connections of a user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self._send_message(connection_id, message)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics"""
        return {
            **self.message_stats,
            "current_connections": len(self.active_connections),
            "unique_users": len(self.user_connections),
            "topics": list(self.subscription_handlers.keys()),
            "timestamp": datetime.now().isoformat(),
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
