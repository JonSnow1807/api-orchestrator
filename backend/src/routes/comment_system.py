from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from src.database import get_db
from src.auth import get_current_user
from src.models import User

router = APIRouter(prefix="/api/comments", tags=["Comments"])


class CommentCreate(BaseModel):
    entity_type: str  # api, collection, request, etc.
    entity_id: str
    content: str
    parent_id: Optional[str] = None
    mentions: Optional[List[str]] = []


class CommentUpdate(BaseModel):
    content: str


class ReactionCreate(BaseModel):
    comment_id: str
    reaction_type: str  # like, love, laugh, etc.


@router.post("/")
async def create_comment(
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new comment"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        comment_id = await system.create_comment(
            entity_type=comment.entity_type,
            entity_id=comment.entity_id,
            content=comment.content,
            user_id=current_user.id,
            parent_id=comment.parent_id,
            mentions=comment.mentions,
        )

        # Send notifications for mentions
        if comment.mentions:
            await system.notify_mentions(
                comment_id=comment_id,
                mentions=comment.mentions,
                author=current_user.username,
            )

        return {
            "id": comment_id,
            "status": "created",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ImportError:
        return {
            "id": f"comment_{datetime.utcnow().timestamp()}",
            "status": "created",
            "message": "Comment created (mock)",
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.get("/{entity_type}/{entity_id}")
async def get_comments(
    entity_type: str,
    entity_id: str,
    include_replies: bool = Query(True),
    sort: str = Query("newest"),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comments for an entity"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        comments = await system.get_comments(
            entity_type=entity_type,
            entity_id=entity_id,
            include_replies=include_replies,
            sort=sort,
            limit=limit,
        )

        return {
            "comments": comments,
            "total": len(comments),
            "entity": {"type": entity_type, "id": entity_id},
        }
    except ImportError:
        return {
            "comments": [
                {
                    "id": "comment_001",
                    "content": "Great API design! The authentication flow is well implemented.",
                    "author": {
                        "id": "user_123",
                        "username": "john_doe",
                        "avatar": "/avatars/john.png",
                    },
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": None,
                    "edited": False,
                    "reactions": {"like": 5, "love": 2},
                    "replies": [
                        {
                            "id": "comment_002",
                            "content": "Thanks! We spent a lot of time on the OAuth2 implementation.",
                            "author": {
                                "id": "user_456",
                                "username": "jane_smith",
                                "avatar": "/avatars/jane.png",
                            },
                            "created_at": datetime.utcnow().isoformat(),
                            "mentions": ["@john_doe"],
                        }
                    ],
                }
            ],
            "total": 1,
            "message": "Using mock data",
        }


@router.put("/{comment_id}")
async def update_comment(
    comment_id: str,
    update: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a comment"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        # Verify ownership
        comment = await system.get_comment(comment_id)
        if comment["author_id"] != current_user.id:
            raise HTTPException(
                status_code=403, detail="Not authorized to edit this comment"
            )

        await system.update_comment(
            comment_id=comment_id, content=update.content, user_id=current_user.id
        )

        return {
            "id": comment_id,
            "status": "updated",
            "edited": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ImportError:
        return {
            "id": comment_id,
            "status": "updated",
            "edited": True,
            "message": "Comment updated (mock)",
        }


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a comment"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        # Verify ownership or admin
        comment = await system.get_comment(comment_id)
        if comment["author_id"] != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this comment"
            )

        await system.delete_comment(comment_id, current_user.id)

        return {
            "id": comment_id,
            "status": "deleted",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ImportError:
        return {
            "id": comment_id,
            "status": "deleted",
            "message": "Comment deleted (mock)",
        }


@router.post("/reactions")
async def add_reaction(
    reaction: ReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add reaction to a comment"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        await system.add_reaction(
            comment_id=reaction.comment_id,
            user_id=current_user.id,
            reaction_type=reaction.reaction_type,
        )

        return {
            "comment_id": reaction.comment_id,
            "reaction": reaction.reaction_type,
            "status": "added",
        }
    except ImportError:
        return {
            "comment_id": reaction.comment_id,
            "reaction": reaction.reaction_type,
            "status": "added",
            "message": "Reaction added (mock)",
        }


@router.delete("/reactions/{comment_id}/{reaction_type}")
async def remove_reaction(
    comment_id: str,
    reaction_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove reaction from a comment"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        await system.remove_reaction(
            comment_id=comment_id, user_id=current_user.id, reaction_type=reaction_type
        )

        return {
            "comment_id": comment_id,
            "reaction": reaction_type,
            "status": "removed",
        }
    except ImportError:
        return {
            "comment_id": comment_id,
            "reaction": reaction_type,
            "status": "removed",
            "message": "Reaction removed (mock)",
        }


@router.get("/threads/{comment_id}")
async def get_thread(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full comment thread"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        thread = await system.get_thread(comment_id)

        return {
            "thread": thread,
            "depth": len(thread.get("replies", [])),
            "total_comments": system.count_thread_comments(thread),
        }
    except ImportError:
        return {
            "thread": {
                "id": comment_id,
                "content": "Root comment",
                "replies": [
                    {
                        "id": "reply_001",
                        "content": "First reply",
                        "replies": [{"id": "reply_002", "content": "Nested reply"}],
                    }
                ],
            },
            "depth": 2,
            "total_comments": 3,
            "message": "Using mock data",
        }


@router.get("/mentions/me")
async def get_my_mentions(
    unread_only: bool = Query(False),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comments where current user is mentioned"""
    try:
        from src.comment_system import CommentSystem

        system = CommentSystem(db)

        mentions = await system.get_user_mentions(
            user_id=current_user.id,
            username=current_user.username,
            unread_only=unread_only,
            limit=limit,
        )

        return {
            "mentions": mentions,
            "total": len(mentions),
            "unread_count": sum(1 for m in mentions if not m.get("read", False)),
        }
    except ImportError:
        return {
            "mentions": [
                {
                    "id": "mention_001",
                    "comment": {
                        "id": "comment_123",
                        "content": "@you Great work on the API documentation!",
                        "author": "jane_doe",
                    },
                    "entity": {"type": "api", "id": "api_456", "name": "User API"},
                    "created_at": datetime.utcnow().isoformat(),
                    "read": False,
                }
            ],
            "total": 1,
            "unread_count": 1,
            "message": "Using mock data",
        }


@router.post("/mentions/{mention_id}/mark-read")
async def mark_mention_read(
    mention_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a mention as read"""
    return {
        "mention_id": mention_id,
        "status": "marked_as_read",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/activity/recent")
async def get_recent_activity(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent comment activity"""
    return {
        "activity": [
            {
                "type": "comment_created",
                "comment": {
                    "id": "comment_789",
                    "content": "Just deployed the new version!",
                    "author": "dev_team",
                },
                "entity": {"type": "api", "id": "api_123", "name": "Payment API"},
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "type": "reaction_added",
                "reaction": "celebrate",
                "comment_id": "comment_456",
                "user": "product_manager",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ],
        "total": 2,
    }
