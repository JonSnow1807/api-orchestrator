"""
Enhanced Variable Management System
Local-by-default variables with selective sharing and auto-save
Competitive with Postman's latest variable management features
"""

import json
import hashlib
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
import asyncio
from sqlalchemy import Column, String, JSON, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship, Session
from src.database import Base
import secrets

class VariableScope(Enum):
    """Variable scope levels"""
    LOCAL = "local"  # User's local variables (not shared)
    SHARED = "shared"  # Explicitly shared with team
    WORKSPACE = "workspace"  # Workspace-level variables
    COLLECTION = "collection"  # Collection-level variables
    ENVIRONMENT = "environment"  # Environment-specific variables
    GLOBAL = "global"  # Global variables

class VariableVisibility(Enum):
    """Variable visibility levels"""
    PRIVATE = "private"  # Only visible to owner
    TEAM = "team"  # Visible to team members
    PUBLIC = "public"  # Visible to all workspace members

class Variable(Base):
    """Enhanced variable model"""
    __tablename__ = "enhanced_variables"
    
    id = Column(String, primary_key=True, default=lambda: f"var_{secrets.token_urlsafe(16)}")
    key = Column(String, nullable=False, index=True)
    value = Column(Text)  # Actual value (encrypted for sensitive data)
    initial_value = Column(Text)  # Initial/default value
    current_value = Column(Text)  # Current runtime value
    
    # Scope and visibility
    scope = Column(String, default=VariableScope.LOCAL.value)
    visibility = Column(String, default=VariableVisibility.PRIVATE.value)
    
    # Metadata
    description = Column(Text)
    type = Column(String)  # string, number, boolean, secret, etc.
    is_sensitive = Column(Boolean, default=False)
    is_masked = Column(Boolean, default=False)
    mask_pattern = Column(String)  # e.g., "****-****-****-{last4}"
    
    # Sharing settings
    shared_with_users = Column(JSON, default=list)  # List of user IDs
    shared_with_teams = Column(JSON, default=list)  # List of team IDs
    share_expires_at = Column(DateTime)
    
    # Auto-save and versioning
    auto_save = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    last_modified = Column(DateTime, default=datetime.utcnow)
    last_modified_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"))
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    collection_id = Column(Integer, ForeignKey("collections.id"))
    environment_id = Column(Integer, ForeignKey("environments.id"))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    change_history = Column(JSON, default=list)  # Track all changes

class VariableHistory(Base):
    """Track variable change history"""
    __tablename__ = "variable_history"
    
    id = Column(String, primary_key=True, default=lambda: f"vh_{secrets.token_urlsafe(16)}")
    variable_id = Column(String, ForeignKey("enhanced_variables.id"))
    old_value = Column(Text)
    new_value = Column(Text)
    changed_by = Column(String, ForeignKey("users.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(Text)

class EnhancedVariableManager:
    """Manage enhanced variables with advanced features"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_key = None  # Set from environment
        self.auto_save_queue = []
        self.auto_save_task = None
        
    async def create_variable(
        self,
        key: str,
        value: Any,
        user_id: str,
        scope: VariableScope = VariableScope.LOCAL,
        **kwargs
    ) -> Variable:
        """Create a new variable with local-by-default behavior"""
        
        # Detect if value is sensitive
        is_sensitive = self._detect_sensitive_value(key, str(value))
        
        # Create variable
        variable = Variable(
            key=key,
            value=self._encrypt_if_sensitive(value, is_sensitive),
            initial_value=value,
            current_value=value,
            scope=scope.value,
            visibility=VariableVisibility.PRIVATE.value if scope == VariableScope.LOCAL else VariableVisibility.TEAM.value,
            is_sensitive=is_sensitive,
            is_masked=is_sensitive,
            owner_id=user_id,
            created_by=user_id,
            type=self._detect_type(value),
            **kwargs
        )
        
        # Apply masking if sensitive
        if is_sensitive:
            variable.mask_pattern = self._get_mask_pattern(key, value)
        
        self.db.add(variable)
        
        # Auto-save if enabled
        if variable.auto_save:
            await self._queue_auto_save(variable)
        
        return variable
    
    async def get_variable_value(
        self,
        key: str,
        user_id: str,
        context: Optional[Dict] = None
    ) -> Any:
        """Get variable value with proper scope resolution"""
        
        # Variable resolution order (most specific to least specific)
        scopes_order = [
            VariableScope.LOCAL,
            VariableScope.ENVIRONMENT,
            VariableScope.COLLECTION,
            VariableScope.WORKSPACE,
            VariableScope.SHARED,
            VariableScope.GLOBAL
        ]
        
        for scope in scopes_order:
            variable = self._find_variable(key, user_id, scope, context)
            if variable:
                # Check permissions
                if self._has_access(variable, user_id):
                    value = variable.current_value or variable.value
                    
                    # Decrypt if sensitive
                    if variable.is_sensitive:
                        value = self._decrypt_value(value)
                    
                    # Apply masking for display if needed
                    if variable.is_masked and not self._is_owner(variable, user_id):
                        value = self._apply_mask(value, variable.mask_pattern)
                    
                    return value
        
        return None
    
    async def update_variable(
        self,
        variable_id: str,
        new_value: Any,
        user_id: str,
        reason: Optional[str] = None
    ) -> Variable:
        """Update variable with history tracking"""
        
        variable = self.db.query(Variable).filter_by(id=variable_id).first()
        if not variable:
            raise ValueError(f"Variable {variable_id} not found")
        
        # Check permissions
        if not self._can_modify(variable, user_id):
            raise PermissionError("Not authorized to modify this variable")
        
        # Track history
        history = VariableHistory(
            variable_id=variable_id,
            old_value=variable.current_value,
            new_value=str(new_value),
            changed_by=user_id,
            change_reason=reason
        )
        self.db.add(history)
        
        # Update variable
        old_value = variable.current_value
        variable.current_value = self._encrypt_if_sensitive(new_value, variable.is_sensitive)
        variable.version += 1
        variable.last_modified = datetime.utcnow()
        variable.last_modified_by = user_id
        
        # Add to change history
        if not variable.change_history:
            variable.change_history = []
        
        variable.change_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_id,
            "old_value": self._mask_for_history(old_value, variable.is_sensitive),
            "new_value": self._mask_for_history(new_value, variable.is_sensitive),
            "reason": reason
        })
        
        # Auto-save if enabled
        if variable.auto_save:
            await self._queue_auto_save(variable)
        
        return variable
    
    async def share_variable(
        self,
        variable_id: str,
        user_id: str,
        share_with: Dict[str, List[str]],
        expires_in_hours: Optional[int] = None
    ) -> Variable:
        """Selectively share a variable with users or teams"""
        
        variable = self.db.query(Variable).filter_by(id=variable_id).first()
        if not variable:
            raise ValueError(f"Variable {variable_id} not found")
        
        # Only owner can share
        if not self._is_owner(variable, user_id):
            raise PermissionError("Only the owner can share this variable")
        
        # Update sharing settings
        if "users" in share_with:
            variable.shared_with_users = list(set(variable.shared_with_users + share_with["users"]))
        
        if "teams" in share_with:
            variable.shared_with_teams = list(set(variable.shared_with_teams + share_with["teams"]))
        
        # Set expiration if specified
        if expires_in_hours:
            from datetime import timedelta
            variable.share_expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        # Change visibility if sharing
        if variable.shared_with_users or variable.shared_with_teams:
            variable.visibility = VariableVisibility.TEAM.value
        
        self.db.commit()
        return variable
    
    async def unshare_variable(
        self,
        variable_id: str,
        user_id: str,
        unshare_from: Optional[Dict[str, List[str]]] = None
    ) -> Variable:
        """Stop sharing a variable"""
        
        variable = self.db.query(Variable).filter_by(id=variable_id).first()
        if not variable:
            raise ValueError(f"Variable {variable_id} not found")
        
        # Only owner can unshare
        if not self._is_owner(variable, user_id):
            raise PermissionError("Only the owner can unshare this variable")
        
        if unshare_from:
            # Selective unsharing
            if "users" in unshare_from:
                variable.shared_with_users = [
                    u for u in variable.shared_with_users 
                    if u not in unshare_from["users"]
                ]
            
            if "teams" in unshare_from:
                variable.shared_with_teams = [
                    t for t in variable.shared_with_teams 
                    if t not in unshare_from["teams"]
                ]
        else:
            # Unshare from all
            variable.shared_with_users = []
            variable.shared_with_teams = []
            variable.share_expires_at = None
            variable.visibility = VariableVisibility.PRIVATE.value
        
        self.db.commit()
        return variable
    
    async def set_masking(
        self,
        variable_id: str,
        user_id: str,
        mask_enabled: bool,
        mask_pattern: Optional[str] = None
    ) -> Variable:
        """Configure masking for sensitive variables"""
        
        variable = self.db.query(Variable).filter_by(id=variable_id).first()
        if not variable:
            raise ValueError(f"Variable {variable_id} not found")
        
        # Check permissions
        if not self._is_owner(variable, user_id):
            raise PermissionError("Only the owner can configure masking")
        
        variable.is_masked = mask_enabled
        
        if mask_enabled and mask_pattern:
            variable.mask_pattern = mask_pattern
        elif mask_enabled:
            # Auto-detect mask pattern
            variable.mask_pattern = self._get_mask_pattern(variable.key, variable.value)
        
        self.db.commit()
        return variable
    
    async def bulk_update_variables(
        self,
        updates: List[Dict[str, Any]],
        user_id: str
    ) -> List[Variable]:
        """Bulk update multiple variables with auto-save"""
        
        updated_variables = []
        
        for update in updates:
            try:
                variable = await self.update_variable(
                    variable_id=update["id"],
                    new_value=update["value"],
                    user_id=user_id,
                    reason=update.get("reason", "Bulk update")
                )
                updated_variables.append(variable)
            except Exception as e:
                print(f"Failed to update variable {update.get('id')}: {e}")
        
        # Trigger single auto-save for all
        if updated_variables:
            await self._perform_auto_save()
        
        return updated_variables
    
    def _detect_sensitive_value(self, key: str, value: str) -> bool:
        """Detect if a value is sensitive based on patterns"""
        
        sensitive_patterns = [
            r"api[_-]?key",
            r"secret",
            r"password",
            r"token",
            r"auth",
            r"credential",
            r"private[_-]?key",
            r"access[_-]?key"
        ]
        
        # Check key name
        for pattern in sensitive_patterns:
            if re.search(pattern, key.lower()):
                return True
        
        # Check value patterns
        value_patterns = [
            r"^sk_[a-zA-Z0-9]{32,}$",  # Stripe-like keys
            r"^[a-f0-9]{40}$",  # SHA-1 hash
            r"^[a-f0-9]{64}$",  # SHA-256 hash
            r"^Bearer\s+",  # Bearer tokens
            r"^Basic\s+"  # Basic auth
        ]
        
        for pattern in value_patterns:
            if re.search(pattern, value):
                return True
        
        return False
    
    def _detect_type(self, value: Any) -> str:
        """Detect variable type"""
        
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, dict):
            return "object"
        elif isinstance(value, list):
            return "array"
        else:
            # Check string patterns
            str_value = str(value)
            if re.match(r"^https?://", str_value):
                return "url"
            elif re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", str_value):
                return "email"
            elif re.match(r"^\d{4}-\d{2}-\d{2}", str_value):
                return "date"
            else:
                return "string"
    
    def _get_mask_pattern(self, key: str, value: str) -> str:
        """Generate appropriate mask pattern for value"""
        
        if "token" in key.lower() or "key" in key.lower():
            # Show first 4 and last 4 characters
            if len(value) > 8:
                return "{first4}...{last4}"
            else:
                return "****"
        elif "password" in key.lower():
            # Fully mask passwords
            return "********"
        elif "email" in key.lower():
            # Mask email but show domain
            return "****@{domain}"
        elif re.match(r"^\d{4}-\d{4}-\d{4}-\d{4}$", value):
            # Credit card pattern
            return "****-****-****-{last4}"
        else:
            # Default: show first 2 and last 2
            return "{first2}***{last2}"
    
    def _apply_mask(self, value: str, pattern: str) -> str:
        """Apply mask pattern to value"""
        
        if not pattern or not value:
            return "****"
        
        masked = pattern
        
        # Replace placeholders
        if "{first4}" in pattern and len(value) >= 4:
            masked = masked.replace("{first4}", value[:4])
        if "{last4}" in pattern and len(value) >= 4:
            masked = masked.replace("{last4}", value[-4:])
        if "{first2}" in pattern and len(value) >= 2:
            masked = masked.replace("{first2}", value[:2])
        if "{last2}" in pattern and len(value) >= 2:
            masked = masked.replace("{last2}", value[-2:])
        if "{domain}" in pattern and "@" in value:
            domain = value.split("@")[1] if "@" in value else "****"
            masked = masked.replace("{domain}", domain)
        
        return masked
    
    def _encrypt_if_sensitive(self, value: Any, is_sensitive: bool) -> str:
        """Encrypt value if sensitive"""
        
        if not is_sensitive:
            return str(value)
        
        # Simple encryption (in production, use proper encryption)
        from base64 import b64encode
        encoded = b64encode(str(value).encode()).decode()
        return f"encrypted:{encoded}"
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt sensitive value"""
        
        if not encrypted_value.startswith("encrypted:"):
            return encrypted_value
        
        # Simple decryption (in production, use proper decryption)
        from base64 import b64decode
        encoded = encrypted_value.replace("encrypted:", "")
        return b64decode(encoded).decode()
    
    def _mask_for_history(self, value: Any, is_sensitive: bool) -> str:
        """Mask value for history tracking"""
        
        if not is_sensitive:
            return str(value)
        
        # Return a hash for comparison without exposing value
        return f"sha256:{hashlib.sha256(str(value).encode()).hexdigest()[:8]}"
    
    def _find_variable(
        self,
        key: str,
        user_id: str,
        scope: VariableScope,
        context: Optional[Dict] = None
    ) -> Optional[Variable]:
        """Find variable by key and scope"""
        
        query = self.db.query(Variable).filter_by(key=key, scope=scope.value)
        
        # Apply context filters
        if context:
            if scope == VariableScope.ENVIRONMENT and "environment_id" in context:
                query = query.filter_by(environment_id=context["environment_id"])
            elif scope == VariableScope.COLLECTION and "collection_id" in context:
                query = query.filter_by(collection_id=context["collection_id"])
            elif scope == VariableScope.WORKSPACE and "workspace_id" in context:
                query = query.filter_by(workspace_id=context["workspace_id"])
        
        # For local scope, only return user's own variables
        if scope == VariableScope.LOCAL:
            query = query.filter_by(owner_id=user_id)
        
        return query.first()
    
    def _has_access(self, variable: Variable, user_id: str) -> bool:
        """Check if user has access to variable"""
        
        # Owner always has access
        if self._is_owner(variable, user_id):
            return True
        
        # Check if shared with user
        if user_id in variable.shared_with_users:
            # Check expiration
            if variable.share_expires_at and variable.share_expires_at < datetime.utcnow():
                return False
            return True
        
        # Check team membership (would need team service)
        # For now, simplified check
        if variable.visibility == VariableVisibility.PUBLIC.value:
            return True
        
        return False
    
    def _is_owner(self, variable: Variable, user_id: str) -> bool:
        """Check if user is the owner of variable"""
        return variable.owner_id == user_id
    
    def _can_modify(self, variable: Variable, user_id: str) -> bool:
        """Check if user can modify variable"""
        
        # Only owner can modify local variables
        if variable.scope == VariableScope.LOCAL.value:
            return self._is_owner(variable, user_id)
        
        # For other scopes, check permissions (simplified)
        return self._is_owner(variable, user_id) or user_id in variable.shared_with_users
    
    async def _queue_auto_save(self, variable: Variable):
        """Queue variable for auto-save"""
        
        self.auto_save_queue.append(variable)
        
        # Start auto-save task if not running
        if not self.auto_save_task:
            self.auto_save_task = asyncio.create_task(self._auto_save_worker())
    
    async def _auto_save_worker(self):
        """Background worker for auto-saving variables"""
        
        while True:
            await asyncio.sleep(1)  # Save every second
            
            if self.auto_save_queue:
                await self._perform_auto_save()
    
    async def _perform_auto_save(self):
        """Perform auto-save of queued variables"""
        
        if not self.auto_save_queue:
            return
        
        variables_to_save = self.auto_save_queue.copy()
        self.auto_save_queue.clear()
        
        try:
            # Batch save to database
            self.db.commit()
            
            # Log auto-save
            print(f"Auto-saved {len(variables_to_save)} variables")
        except Exception as e:
            print(f"Auto-save failed: {e}")
            # Re-queue failed saves
            self.auto_save_queue.extend(variables_to_save)

# Export for use
__all__ = ['EnhancedVariableManager', 'Variable', 'VariableScope', 'VariableVisibility']