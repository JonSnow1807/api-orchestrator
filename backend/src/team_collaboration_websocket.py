"""
Real-time Collaboration WebSocket System
Handles real-time collaboration features, presence updates, and live notifications
"""

import asyncio
import json
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
import uuid

from src.database import get_db, User
from src.auth import get_current_user_from_token
from src.team_collaboration_models import (
    ActiveSession,
    CollaborationEvent,
    WorkspaceActivityLog,
)
from src.team_collaboration_rbac import PermissionChecker

logger = logging.getLogger(__name__)

# =============================================================================
# CONNECTION MANAGER
# =============================================================================


class CollaborationManager:
    """Manages WebSocket connections and real-time collaboration"""

    def __init__(self):
        # Active connections: {workspace_id: {user_id: [websocket_connections]}}
        self.active_connections: Dict[int, Dict[int, List[WebSocket]]] = {}

        # User presence: {workspace_id: {user_id: presence_data}}
        self.user_presence: Dict[int, Dict[int, Dict]] = {}

        # Active sessions: {session_token: session_data}
        self.active_sessions: Dict[str, Dict] = {}

        # Resource locks: {workspace_id: {resource_id: user_id}}
        self.resource_locks: Dict[int, Dict[str, int]] = {}

        # Collaboration cursors: {workspace_id: {resource_id: {user_id: cursor_data}}}
        self.collaboration_cursors: Dict[int, Dict[str, Dict[int, Dict]]] = {}

    async def connect(
        self, websocket: WebSocket, user: User, workspace_id: int, db: Session
    ):
        """Handle new WebSocket connection"""
        # Check workspace access
        checker = PermissionChecker(db)
        if not checker.is_workspace_member(user.id, workspace_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False

        await websocket.accept()

        # Add to active connections
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = {}
        if user.id not in self.active_connections[workspace_id]:
            self.active_connections[workspace_id][user.id] = []

        self.active_connections[workspace_id][user.id].append(websocket)

        # Generate session token
        session_token = f"sess_{uuid.uuid4().hex}"

        # Create active session in database
        session = ActiveSession(
            workspace_id=workspace_id,
            user_id=user.id,
            session_token=session_token,
            connection_id=str(id(websocket)),
            status="active",
        )
        db.add(session)

        # Store session data
        self.active_sessions[session_token] = {
            "workspace_id": workspace_id,
            "user_id": user.id,
            "websocket": websocket,
            "session_token": session_token,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }

        # Update user presence
        if workspace_id not in self.user_presence:
            self.user_presence[workspace_id] = {}

        self.user_presence[workspace_id][user.id] = {
            "status": "active",
            "last_seen": datetime.utcnow().isoformat(),
            "current_resource": None,
            "user_name": user.full_name or user.username,
            "user_email": user.email,
        }

        db.commit()

        # Notify other users about presence
        await self.broadcast_presence_update(
            workspace_id, user.id, exclude_user=user.id
        )

        # Send initial data to connected user
        await self.send_initial_data(websocket, workspace_id, user.id, db)

        logger.info(f"User {user.id} connected to workspace {workspace_id}")
        return True

    async def disconnect(
        self, websocket: WebSocket, workspace_id: int, user_id: int, db: Session
    ):
        """Handle WebSocket disconnection"""
        try:
            # Remove from active connections
            if (
                workspace_id in self.active_connections
                and user_id in self.active_connections[workspace_id]
            ):
                if websocket in self.active_connections[workspace_id][user_id]:
                    self.active_connections[workspace_id][user_id].remove(websocket)

                # If no more connections for this user
                if not self.active_connections[workspace_id][user_id]:
                    del self.active_connections[workspace_id][user_id]

                    # Update presence to away
                    if (
                        workspace_id in self.user_presence
                        and user_id in self.user_presence[workspace_id]
                    ):
                        self.user_presence[workspace_id][user_id]["status"] = "away"
                        self.user_presence[workspace_id][user_id][
                            "last_seen"
                        ] = datetime.utcnow().isoformat()

                    # Release any resource locks
                    await self.release_user_locks(workspace_id, user_id)

                    # Notify other users
                    await self.broadcast_presence_update(
                        workspace_id, user_id, exclude_user=user_id
                    )

            # Clean up sessions
            sessions_to_remove = []
            for token, session_data in self.active_sessions.items():
                if (
                    session_data["workspace_id"] == workspace_id
                    and session_data["user_id"] == user_id
                    and session_data["websocket"] == websocket
                ):
                    sessions_to_remove.append(token)

            for token in sessions_to_remove:
                del self.active_sessions[token]

            # Update database session
            db.query(ActiveSession).filter(
                ActiveSession.workspace_id == workspace_id,
                ActiveSession.user_id == user_id,
                ActiveSession.connection_id == str(id(websocket)),
            ).delete()

            db.commit()

            logger.info(f"User {user_id} disconnected from workspace {workspace_id}")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def send_initial_data(
        self, websocket: WebSocket, workspace_id: int, user_id: int, db: Session
    ):
        """Send initial collaboration data to newly connected user"""
        try:
            # Get current presence data
            presence = self.user_presence.get(workspace_id, {})

            # Get recent activity
            recent_activity = (
                db.query(WorkspaceActivityLog)
                .filter(
                    WorkspaceActivityLog.workspace_id == workspace_id,
                    WorkspaceActivityLog.created_at
                    > datetime.utcnow() - timedelta(hours=1),
                )
                .order_by(WorkspaceActivityLog.created_at.desc())
                .limit(10)
                .all()
            )

            # Send initial data
            await self.send_personal_message(
                websocket,
                {
                    "type": "initial_data",
                    "data": {
                        "presence": {
                            uid: data
                            for uid, data in presence.items()
                            if uid != user_id
                        },
                        "recent_activity": [
                            activity.to_dict() for activity in recent_activity
                        ],
                        "active_collaborators": len(presence),
                        "your_session": self.get_user_session_info(
                            workspace_id, user_id
                        ),
                    },
                },
            )

        except Exception as e:
            logger.error(f"Error sending initial data: {e}")

    async def handle_message(
        self,
        websocket: WebSocket,
        message: str,
        workspace_id: int,
        user_id: int,
        db: Session,
    ):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            payload = data.get("data", {})

            # Update last activity
            await self.update_user_activity(workspace_id, user_id)

            # Handle different message types
            if message_type == "presence_update":
                await self.handle_presence_update(workspace_id, user_id, payload, db)

            elif message_type == "cursor_update":
                await self.handle_cursor_update(workspace_id, user_id, payload)

            elif message_type == "resource_lock":
                await self.handle_resource_lock(
                    websocket, workspace_id, user_id, payload
                )

            elif message_type == "resource_unlock":
                await self.handle_resource_unlock(
                    websocket, workspace_id, user_id, payload
                )

            elif message_type == "collaboration_event":
                await self.handle_collaboration_event(
                    workspace_id, user_id, payload, db
                )

            elif message_type == "typing_indicator":
                await self.handle_typing_indicator(workspace_id, user_id, payload)

            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON in WebSocket message")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_presence_update(
        self, workspace_id: int, user_id: int, payload: dict, db: Session
    ):
        """Handle user presence updates"""
        if workspace_id not in self.user_presence:
            self.user_presence[workspace_id] = {}

        if user_id not in self.user_presence[workspace_id]:
            return

        # Update presence data
        presence = self.user_presence[workspace_id][user_id]
        presence.update(
            {
                "status": payload.get("status", "active"),
                "current_resource": payload.get("current_resource"),
                "resource_type": payload.get("resource_type"),
                "last_seen": datetime.utcnow().isoformat(),
            }
        )

        # Update database session
        if payload.get("current_resource"):
            db.query(ActiveSession).filter(
                ActiveSession.workspace_id == workspace_id,
                ActiveSession.user_id == user_id,
            ).update(
                {
                    "current_resource_type": payload.get("resource_type"),
                    "current_resource_id": str(payload.get("current_resource")),
                    "last_activity_at": datetime.utcnow(),
                }
            )
            db.commit()

        # Broadcast presence update
        await self.broadcast_presence_update(
            workspace_id, user_id, exclude_user=user_id
        )

    async def handle_cursor_update(
        self, workspace_id: int, user_id: int, payload: dict
    ):
        """Handle cursor position updates for collaborative editing"""
        resource_id = payload.get("resource_id")
        if not resource_id:
            return

        # Initialize cursors structure
        if workspace_id not in self.collaboration_cursors:
            self.collaboration_cursors[workspace_id] = {}
        if resource_id not in self.collaboration_cursors[workspace_id]:
            self.collaboration_cursors[workspace_id][resource_id] = {}

        # Update cursor position
        self.collaboration_cursors[workspace_id][resource_id][user_id] = {
            "position": payload.get("position", 0),
            "selection": payload.get("selection"),
            "timestamp": datetime.utcnow().isoformat(),
            "user_name": self.user_presence[workspace_id][user_id]["user_name"],
        }

        # Broadcast cursor update to other users viewing same resource
        await self.broadcast_to_resource(
            workspace_id,
            resource_id,
            {
                "type": "cursor_update",
                "data": {
                    "user_id": user_id,
                    "resource_id": resource_id,
                    "cursor": self.collaboration_cursors[workspace_id][resource_id][
                        user_id
                    ],
                },
            },
            exclude_user=user_id,
        )

    async def handle_resource_lock(
        self, websocket: WebSocket, workspace_id: int, user_id: int, payload: dict
    ):
        """Handle resource locking for exclusive editing"""
        resource_id = payload.get("resource_id")
        if not resource_id:
            return

        # Initialize locks structure
        if workspace_id not in self.resource_locks:
            self.resource_locks[workspace_id] = {}

        # Check if resource is already locked
        current_lock = self.resource_locks[workspace_id].get(resource_id)
        if current_lock and current_lock != user_id:
            # Resource is locked by another user
            await self.send_personal_message(
                websocket,
                {
                    "type": "lock_denied",
                    "data": {
                        "resource_id": resource_id,
                        "locked_by": current_lock,
                        "reason": "Resource is currently being edited by another user",
                    },
                },
            )
            return

        # Grant lock
        self.resource_locks[workspace_id][resource_id] = user_id

        # Notify user
        await self.send_personal_message(
            websocket,
            {
                "type": "lock_granted",
                "data": {
                    "resource_id": resource_id,
                    "expires_at": (
                        datetime.utcnow() + timedelta(minutes=30)
                    ).isoformat(),
                },
            },
        )

        # Notify other users
        await self.broadcast_to_workspace(
            workspace_id,
            {
                "type": "resource_locked",
                "data": {
                    "resource_id": resource_id,
                    "locked_by": user_id,
                    "user_name": self.user_presence[workspace_id][user_id]["user_name"],
                },
            },
            exclude_user=user_id,
        )

    async def handle_resource_unlock(
        self, websocket: WebSocket, workspace_id: int, user_id: int, payload: dict
    ):
        """Handle resource unlocking"""
        resource_id = payload.get("resource_id")
        if not resource_id:
            return

        # Check if user has the lock
        if (
            workspace_id in self.resource_locks
            and self.resource_locks[workspace_id].get(resource_id) == user_id
        ):
            del self.resource_locks[workspace_id][resource_id]

            # Notify all users
            await self.broadcast_to_workspace(
                workspace_id,
                {
                    "type": "resource_unlocked",
                    "data": {"resource_id": resource_id, "unlocked_by": user_id},
                },
            )

    async def handle_collaboration_event(
        self, workspace_id: int, user_id: int, payload: dict, db: Session
    ):
        """Handle and store collaboration events"""
        event_type = payload.get("event_type")
        resource_type = payload.get("resource_type")
        resource_id = payload.get("resource_id")
        event_data = payload.get("event_data", {})

        if not all([event_type, resource_type, resource_id]):
            return

        # Store collaboration event in database
        collab_event = CollaborationEvent(
            workspace_id=workspace_id,
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=str(resource_id),
            event_data=event_data,
        )
        db.add(collab_event)
        db.commit()

        # Broadcast to relevant users
        await self.broadcast_to_resource(
            workspace_id,
            str(resource_id),
            {
                "type": "collaboration_event",
                "data": {
                    "event_type": event_type,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "event_data": event_data,
                    "user_id": user_id,
                    "user_name": self.user_presence[workspace_id][user_id]["user_name"],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            exclude_user=user_id,
        )

    async def handle_typing_indicator(
        self, workspace_id: int, user_id: int, payload: dict
    ):
        """Handle typing indicators for real-time collaboration"""
        resource_id = payload.get("resource_id")
        is_typing = payload.get("is_typing", False)

        if not resource_id:
            return

        # Broadcast typing indicator
        await self.broadcast_to_resource(
            workspace_id,
            resource_id,
            {
                "type": "typing_indicator",
                "data": {
                    "user_id": user_id,
                    "user_name": self.user_presence[workspace_id][user_id]["user_name"],
                    "resource_id": resource_id,
                    "is_typing": is_typing,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
            exclude_user=user_id,
        )

    # Broadcast methods
    async def broadcast_to_workspace(
        self, workspace_id: int, message: dict, exclude_user: int = None
    ):
        """Broadcast message to all users in workspace"""
        if workspace_id not in self.active_connections:
            return

        for user_id, connections in self.active_connections[workspace_id].items():
            if exclude_user and user_id == exclude_user:
                continue

            for websocket in connections[
                :
            ]:  # Create copy to avoid modification during iteration
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    connections.remove(websocket)

    async def broadcast_to_resource(
        self,
        workspace_id: int,
        resource_id: str,
        message: dict,
        exclude_user: int = None,
    ):
        """Broadcast message to users viewing specific resource"""
        if workspace_id not in self.user_presence:
            return

        # Find users viewing this resource
        viewing_users = []
        for user_id, presence in self.user_presence[workspace_id].items():
            if (
                presence.get("current_resource") == resource_id
                and user_id != exclude_user
            ):
                viewing_users.append(user_id)

        # Send to viewing users
        for user_id in viewing_users:
            if (
                workspace_id in self.active_connections
                and user_id in self.active_connections[workspace_id]
            ):
                for websocket in self.active_connections[workspace_id][user_id][:]:
                    try:
                        await websocket.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(
                            f"Error sending resource message to user {user_id}: {e}"
                        )
                        self.active_connections[workspace_id][user_id].remove(websocket)

    async def broadcast_presence_update(
        self, workspace_id: int, user_id: int, exclude_user: int = None
    ):
        """Broadcast presence update to workspace"""
        if (
            workspace_id not in self.user_presence
            or user_id not in self.user_presence[workspace_id]
        ):
            return

        presence_data = self.user_presence[workspace_id][user_id]

        await self.broadcast_to_workspace(
            workspace_id,
            {
                "type": "presence_update",
                "data": {"user_id": user_id, "presence": presence_data},
            },
            exclude_user=exclude_user,
        )

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    # Utility methods
    async def update_user_activity(self, workspace_id: int, user_id: int):
        """Update user's last activity timestamp"""
        if (
            workspace_id in self.user_presence
            and user_id in self.user_presence[workspace_id]
        ):
            self.user_presence[workspace_id][user_id][
                "last_seen"
            ] = datetime.utcnow().isoformat()

    async def release_user_locks(self, workspace_id: int, user_id: int):
        """Release all resource locks held by user"""
        if workspace_id not in self.resource_locks:
            return

        locks_to_release = []
        for resource_id, lock_user_id in self.resource_locks[workspace_id].items():
            if lock_user_id == user_id:
                locks_to_release.append(resource_id)

        for resource_id in locks_to_release:
            del self.resource_locks[workspace_id][resource_id]

            # Notify workspace
            await self.broadcast_to_workspace(
                workspace_id,
                {
                    "type": "resource_unlocked",
                    "data": {
                        "resource_id": resource_id,
                        "unlocked_by": user_id,
                        "reason": "User disconnected",
                    },
                },
            )

    def get_workspace_presence(self, workspace_id: int) -> dict:
        """Get presence data for workspace"""
        return self.user_presence.get(workspace_id, {})

    def get_active_users(self, workspace_id: int) -> List[int]:
        """Get list of active user IDs in workspace"""
        return list(self.active_connections.get(workspace_id, {}).keys())

    def get_user_session_info(self, workspace_id: int, user_id: int) -> dict:
        """Get session info for user"""
        for session_data in self.active_sessions.values():
            if (
                session_data["workspace_id"] == workspace_id
                and session_data["user_id"] == user_id
            ):
                return {
                    "session_token": session_data["session_token"],
                    "connected_at": session_data["connected_at"].isoformat(),
                    "last_activity": session_data["last_activity"].isoformat(),
                }
        return {}

    # Cleanup methods
    async def cleanup_stale_sessions(self, db: Session):
        """Clean up stale sessions and presence data"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)

        # Remove stale database sessions
        db.query(ActiveSession).filter(
            ActiveSession.last_activity_at < cutoff_time
        ).delete()

        # Clean up memory structures
        for workspace_id in list(self.user_presence.keys()):
            for user_id in list(self.user_presence[workspace_id].keys()):
                last_seen = self.user_presence[workspace_id][user_id].get("last_seen")
                if last_seen:
                    try:
                        last_seen_dt = datetime.fromisoformat(
                            last_seen.replace("Z", "+00:00")
                        )
                        if last_seen_dt < cutoff_time:
                            del self.user_presence[workspace_id][user_id]
                    except Exception:
                        pass

        db.commit()


# Global collaboration manager instance
collaboration_manager = CollaborationManager()

# =============================================================================
# WEBSOCKET ENDPOINT HANDLER
# =============================================================================


async def websocket_collaboration_handler(
    websocket: WebSocket, workspace_id: int, token: str, db: Session = Depends(get_db)
):
    """Main WebSocket handler for collaboration features"""
    try:
        # Authenticate user from token
        user = await get_current_user_from_token(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect user
        connected = await collaboration_manager.connect(
            websocket, user, workspace_id, db
        )
        if not connected:
            return

        try:
            # Handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await collaboration_manager.handle_message(
                        websocket, message, workspace_id, user.id, db
                    )
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {e}")
                    # Send error message to client
                    await collaboration_manager.send_personal_message(
                        websocket,
                        {
                            "type": "error",
                            "data": {
                                "message": "An error occurred while processing your request"
                            },
                        },
                    )

        except WebSocketDisconnect:
            pass
        finally:
            await collaboration_manager.disconnect(websocket, workspace_id, user.id, db)

    except Exception as e:
        logger.error(f"WebSocket collaboration error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass


# =============================================================================
# BACKGROUND TASKS
# =============================================================================


async def cleanup_collaboration_task():
    """Background task to clean up stale sessions"""
    while True:
        try:
            from src.database import SessionLocal

            db = SessionLocal()
            try:
                await collaboration_manager.cleanup_stale_sessions(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

        # Run cleanup every 5 minutes
        await asyncio.sleep(300)


# Start background cleanup task
asyncio.create_task(cleanup_collaboration_task())
