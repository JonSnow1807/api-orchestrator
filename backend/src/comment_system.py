"""
Comment System - Collaborative discussions on APIs
Inline and global comments with mentions and notifications
"""

import uuid
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import re
from dataclasses import dataclass

class CommentType(Enum):
    """Types of comments"""
    GLOBAL = "global"  # General comment on entire resource
    INLINE = "inline"  # Specific line/field comment
    REVIEW = "review"  # Code review comment
    SUGGESTION = "suggestion"  # Improvement suggestion
    ISSUE = "issue"  # Problem report
    QUESTION = "question"  # Question/clarification

class CommentStatus(Enum):
    """Comment status"""
    OPEN = "open"
    RESOLVED = "resolved"
    PENDING = "pending"
    ARCHIVED = "archived"

class CommentContext(Enum):
    """Where comments can be attached"""
    API_DESIGN = "api_design"
    COLLECTION = "collection"
    REQUEST = "request"
    TEST_RESULT = "test_result"
    DOCUMENTATION = "documentation"
    CODE = "code"
    SCHEMA = "schema"
    ENVIRONMENT = "environment"

class NotificationType(Enum):
    """Notification types"""
    MENTION = "mention"
    REPLY = "reply"
    RESOLVE = "resolve"
    NEW_COMMENT = "new_comment"
    STATUS_CHANGE = "status_change"

class Comment(BaseModel):
    """Comment model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None  # For nested replies
    
    # Context
    context: CommentContext
    resource_id: str  # ID of the resource being commented on
    resource_name: str
    
    # Comment details
    type: CommentType
    content: str
    author_id: str
    author_name: str
    author_avatar: Optional[str] = None
    
    # Location for inline comments
    location: Optional[Dict[str, Any]] = None  # line number, field path, etc.
    
    # Metadata
    status: CommentStatus = CommentStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    # Interactions
    mentions: List[str] = []  # User IDs mentioned
    reactions: Dict[str, List[str]] = {}  # emoji -> list of user IDs
    attachments: List[str] = []  # File URLs
    
    # Threading
    replies_count: int = 0
    participants: Set[str] = Field(default_factory=set)
    
    # Visibility
    is_private: bool = False
    visible_to_teams: List[str] = []

class CommentThread(BaseModel):
    """Comment thread grouping"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context: CommentContext
    resource_id: str
    title: str
    
    # Thread metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    
    # Participants
    participants: Set[str] = Field(default_factory=set)
    watchers: Set[str] = Field(default_factory=set)
    
    # Status
    status: CommentStatus = CommentStatus.OPEN
    priority: str = "normal"  # low, normal, high, critical
    labels: List[str] = []
    
    # Statistics
    total_comments: int = 0
    unresolved_count: int = 0
    
class Notification(BaseModel):
    """Notification for comment activity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType
    recipient_id: str
    
    # Notification details
    title: str
    message: str
    comment_id: str
    thread_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    read: bool = False
    read_at: Optional[datetime] = None
    
    # Actions
    action_url: Optional[str] = None
    action_text: Optional[str] = None

class CommentSystem:
    """Manage comments and discussions"""
    
    def __init__(self):
        self.comments: Dict[str, Comment] = {}
        self.threads: Dict[str, CommentThread] = {}
        self.notifications: Dict[str, List[Notification]] = {}
        
        # Indexes for fast lookup
        self.comments_by_resource: Dict[str, List[str]] = {}
        self.comments_by_author: Dict[str, List[str]] = {}
        self.threads_by_resource: Dict[str, List[str]] = {}
        
        # Notification settings
        self.notification_preferences: Dict[str, Dict[str, bool]] = {}
        
    async def create_comment(
        self,
        context: CommentContext,
        resource_id: str,
        resource_name: str,
        content: str,
        author_id: str,
        author_name: str,
        type: CommentType = CommentType.GLOBAL,
        location: Optional[Dict[str, Any]] = None,
        parent_id: Optional[str] = None
    ) -> Comment:
        """Create a new comment"""
        
        # Extract mentions from content
        mentions = self._extract_mentions(content)
        
        # Create comment
        comment = Comment(
            context=context,
            resource_id=resource_id,
            resource_name=resource_name,
            type=type,
            content=content,
            author_id=author_id,
            author_name=author_name,
            location=location,
            parent_id=parent_id,
            mentions=mentions,
            participants={author_id}
        )
        
        # Store comment
        self.comments[comment.id] = comment
        
        # Update indexes
        if resource_id not in self.comments_by_resource:
            self.comments_by_resource[resource_id] = []
        self.comments_by_resource[resource_id].append(comment.id)
        
        if author_id not in self.comments_by_author:
            self.comments_by_author[author_id] = []
        self.comments_by_author[author_id].append(comment.id)
        
        # Handle threading
        thread_id = await self._handle_threading(comment)
        
        # Update parent comment if it's a reply
        if parent_id and parent_id in self.comments:
            parent = self.comments[parent_id]
            parent.replies_count += 1
            parent.participants.add(author_id)
        
        # Send notifications
        await self._send_notifications(comment, thread_id)
        
        return comment
    
    async def update_comment(
        self,
        comment_id: str,
        content: str,
        editor_id: str
    ) -> Comment:
        """Update a comment"""
        
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        
        # Check permissions
        if comment.author_id != editor_id:
            raise ValueError("Only the author can edit the comment")
        
        # Update content
        comment.content = content
        comment.updated_at = datetime.now()
        
        # Re-extract mentions
        new_mentions = self._extract_mentions(content)
        added_mentions = set(new_mentions) - set(comment.mentions)
        comment.mentions = new_mentions
        
        # Notify newly mentioned users
        for user_id in added_mentions:
            await self._create_notification(
                type=NotificationType.MENTION,
                recipient_id=user_id,
                comment=comment,
                title=f"{comment.author_name} mentioned you",
                message=f"You were mentioned in a comment on {comment.resource_name}"
            )
        
        return comment
    
    async def resolve_comment(
        self,
        comment_id: str,
        resolver_id: str,
        resolver_name: str
    ) -> Comment:
        """Resolve a comment"""
        
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        
        # Update status
        comment.status = CommentStatus.RESOLVED
        comment.resolved_at = datetime.now()
        comment.resolved_by = resolver_id
        
        # Update thread if exists
        thread_id = self._find_thread_for_comment(comment_id)
        if thread_id:
            thread = self.threads[thread_id]
            thread.unresolved_count = max(0, thread.unresolved_count - 1)
            if thread.unresolved_count == 0:
                thread.status = CommentStatus.RESOLVED
        
        # Notify participants
        for participant_id in comment.participants:
            if participant_id != resolver_id:
                await self._create_notification(
                    type=NotificationType.RESOLVE,
                    recipient_id=participant_id,
                    comment=comment,
                    title=f"{resolver_name} resolved a comment",
                    message=f"Comment on {comment.resource_name} has been resolved"
                )
        
        return comment
    
    async def add_reaction(
        self,
        comment_id: str,
        user_id: str,
        emoji: str
    ) -> Comment:
        """Add reaction to comment"""
        
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        
        if emoji not in comment.reactions:
            comment.reactions[emoji] = []
        
        if user_id not in comment.reactions[emoji]:
            comment.reactions[emoji].append(user_id)
        
        return comment
    
    async def remove_reaction(
        self,
        comment_id: str,
        user_id: str,
        emoji: str
    ) -> Comment:
        """Remove reaction from comment"""
        
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        
        if emoji in comment.reactions and user_id in comment.reactions[emoji]:
            comment.reactions[emoji].remove(user_id)
            if not comment.reactions[emoji]:
                del comment.reactions[emoji]
        
        return comment
    
    async def get_comments(
        self,
        resource_id: Optional[str] = None,
        context: Optional[CommentContext] = None,
        author_id: Optional[str] = None,
        status: Optional[CommentStatus] = None,
        type: Optional[CommentType] = None,
        include_resolved: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Comment]:
        """Get comments with filters"""
        
        comments = []
        
        # Start with resource filter if provided
        if resource_id and resource_id in self.comments_by_resource:
            comment_ids = self.comments_by_resource[resource_id]
            comments = [self.comments[cid] for cid in comment_ids]
        elif author_id and author_id in self.comments_by_author:
            comment_ids = self.comments_by_author[author_id]
            comments = [self.comments[cid] for cid in comment_ids]
        else:
            comments = list(self.comments.values())
        
        # Apply filters
        if context:
            comments = [c for c in comments if c.context == context]
        
        if status:
            comments = [c for c in comments if c.status == status]
        elif not include_resolved:
            comments = [c for c in comments if c.status != CommentStatus.RESOLVED]
        
        if type:
            comments = [c for c in comments if c.type == type]
        
        # Sort by creation time (newest first)
        comments.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        return comments[offset:offset + limit]
    
    async def get_comment_thread(
        self,
        comment_id: str
    ) -> Dict[str, Any]:
        """Get full comment thread"""
        
        if comment_id not in self.comments:
            raise ValueError(f"Comment {comment_id} not found")
        
        comment = self.comments[comment_id]
        
        # Find root comment
        root_comment = comment
        while root_comment.parent_id:
            if root_comment.parent_id in self.comments:
                root_comment = self.comments[root_comment.parent_id]
            else:
                break
        
        # Build thread tree
        thread = self._build_comment_tree(root_comment.id)
        
        return {
            "root": root_comment.dict(),
            "thread": thread,
            "total_comments": self._count_comments_in_tree(thread),
            "participants": list(self._get_thread_participants(root_comment.id))
        }
    
    async def search_comments(
        self,
        query: str,
        user_id: str,
        limit: int = 20
    ) -> List[Comment]:
        """Search comments"""
        
        results = []
        query_lower = query.lower()
        
        for comment in self.comments.values():
            # Check if user has access
            if comment.is_private and user_id not in comment.visible_to_teams:
                continue
            
            # Search in content and author name
            if (query_lower in comment.content.lower() or
                query_lower in comment.author_name.lower() or
                query_lower in comment.resource_name.lower()):
                results.append(comment)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Notification]:
        """Get user notifications"""
        
        if user_id not in self.notifications:
            return []
        
        notifications = self.notifications[user_id]
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        # Sort by creation time (newest first)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        return notifications[:limit]
    
    async def mark_notification_read(
        self,
        notification_id: str,
        user_id: str
    ):
        """Mark notification as read"""
        
        if user_id in self.notifications:
            for notification in self.notifications[user_id]:
                if notification.id == notification_id:
                    notification.read = True
                    notification.read_at = datetime.now()
                    break
    
    async def update_notification_preferences(
        self,
        user_id: str,
        preferences: Dict[str, bool]
    ):
        """Update user notification preferences"""
        
        self.notification_preferences[user_id] = preferences
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from content"""
        
        # Pattern to match @username or @user_id
        pattern = r'@([a-zA-Z0-9_-]+)'
        matches = re.findall(pattern, content)
        
        # In real implementation, would validate these are real user IDs
        return list(set(matches))
    
    async def _handle_threading(self, comment: Comment) -> Optional[str]:
        """Handle comment threading"""
        
        # Find or create thread
        thread_key = f"{comment.context.value}:{comment.resource_id}"
        
        # Look for existing thread
        thread_id = None
        if comment.resource_id in self.threads_by_resource:
            for tid in self.threads_by_resource[comment.resource_id]:
                thread = self.threads[tid]
                if thread.context == comment.context:
                    thread_id = tid
                    break
        
        if not thread_id:
            # Create new thread
            thread = CommentThread(
                context=comment.context,
                resource_id=comment.resource_id,
                title=f"Discussion on {comment.resource_name}",
                participants={comment.author_id}
            )
            
            thread_id = thread.id
            self.threads[thread_id] = thread
            
            if comment.resource_id not in self.threads_by_resource:
                self.threads_by_resource[comment.resource_id] = []
            self.threads_by_resource[comment.resource_id].append(thread_id)
        else:
            # Update existing thread
            thread = self.threads[thread_id]
            thread.participants.add(comment.author_id)
            thread.last_activity = datetime.now()
        
        # Update thread statistics
        thread.total_comments += 1
        if comment.status == CommentStatus.OPEN:
            thread.unresolved_count += 1
        
        return thread_id
    
    async def _send_notifications(self, comment: Comment, thread_id: Optional[str]):
        """Send notifications for comment activity"""
        
        # Notify mentioned users
        for user_id in comment.mentions:
            await self._create_notification(
                type=NotificationType.MENTION,
                recipient_id=user_id,
                comment=comment,
                thread_id=thread_id,
                title=f"{comment.author_name} mentioned you",
                message=f"You were mentioned in a comment on {comment.resource_name}"
            )
        
        # Notify parent comment author if it's a reply
        if comment.parent_id and comment.parent_id in self.comments:
            parent = self.comments[comment.parent_id]
            if parent.author_id != comment.author_id:
                await self._create_notification(
                    type=NotificationType.REPLY,
                    recipient_id=parent.author_id,
                    comment=comment,
                    thread_id=thread_id,
                    title=f"{comment.author_name} replied to your comment",
                    message=f"New reply on {comment.resource_name}"
                )
        
        # Notify thread watchers
        if thread_id and thread_id in self.threads:
            thread = self.threads[thread_id]
            for watcher_id in thread.watchers:
                if watcher_id != comment.author_id:
                    await self._create_notification(
                        type=NotificationType.NEW_COMMENT,
                        recipient_id=watcher_id,
                        comment=comment,
                        thread_id=thread_id,
                        title=f"New comment in watched thread",
                        message=f"{comment.author_name} commented on {comment.resource_name}"
                    )
    
    async def _create_notification(
        self,
        type: NotificationType,
        recipient_id: str,
        comment: Comment,
        title: str,
        message: str,
        thread_id: Optional[str] = None
    ):
        """Create and store notification"""
        
        # Check user preferences
        if recipient_id in self.notification_preferences:
            prefs = self.notification_preferences[recipient_id]
            if not prefs.get(type.value, True):
                return
        
        notification = Notification(
            type=type,
            recipient_id=recipient_id,
            title=title,
            message=message,
            comment_id=comment.id,
            thread_id=thread_id,
            action_url=f"/api/{comment.context.value}/{comment.resource_id}#comment-{comment.id}",
            action_text="View Comment"
        )
        
        if recipient_id not in self.notifications:
            self.notifications[recipient_id] = []
        
        self.notifications[recipient_id].append(notification)
    
    def _find_thread_for_comment(self, comment_id: str) -> Optional[str]:
        """Find thread containing comment"""
        
        comment = self.comments.get(comment_id)
        if not comment:
            return None
        
        if comment.resource_id in self.threads_by_resource:
            for thread_id in self.threads_by_resource[comment.resource_id]:
                thread = self.threads[thread_id]
                if thread.context == comment.context:
                    return thread_id
        
        return None
    
    def _build_comment_tree(self, root_id: str) -> Dict[str, Any]:
        """Build hierarchical comment tree"""
        
        if root_id not in self.comments:
            return {}
        
        root = self.comments[root_id]
        tree = {
            "comment": root.dict(),
            "replies": []
        }
        
        # Find direct replies
        for comment_id, comment in self.comments.items():
            if comment.parent_id == root_id:
                tree["replies"].append(self._build_comment_tree(comment_id))
        
        return tree
    
    def _count_comments_in_tree(self, tree: Dict[str, Any]) -> int:
        """Count total comments in tree"""
        
        if not tree:
            return 0
        
        count = 1  # Count this comment
        for reply in tree.get("replies", []):
            count += self._count_comments_in_tree(reply)
        
        return count
    
    def _get_thread_participants(self, root_id: str) -> Set[str]:
        """Get all participants in a thread"""
        
        participants = set()
        
        def collect_participants(comment_id: str):
            if comment_id in self.comments:
                comment = self.comments[comment_id]
                participants.update(comment.participants)
                
                # Check replies
                for cid, c in self.comments.items():
                    if c.parent_id == comment_id:
                        collect_participants(cid)
        
        collect_participants(root_id)
        return participants

# Global comment system instance
comment_system = CommentSystem()