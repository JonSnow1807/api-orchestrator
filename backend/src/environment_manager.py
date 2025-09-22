"""
Environment Variable Management with Inheritance
Supports global -> workspace -> collection -> request variable inheritance
"""

from typing import Dict, Optional, Any
from datetime import datetime
import re
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.database import Base


class VariableScope:
    """Variable scope levels"""

    GLOBAL = "global"
    WORKSPACE = "workspace"
    COLLECTION = "collection"
    REQUEST = "request"


class EnvironmentVariable(Base):
    """Environment variables with hierarchical inheritance"""

    __tablename__ = "environment_variables"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workspace_id = Column(Integer, nullable=True)  # Optional workspace reference

    # Variable details
    name = Column(String(255), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    value = Column(Text)
    initial_value = Column(Text)  # Original value before resolution
    type = Column(String(50), default="string")  # string, number, boolean, secret

    # Scope and inheritance
    scope = Column(
        String(50), default="workspace"
    )  # global, workspace, collection, request
    parent_id = Column(Integer, ForeignKey("environment_variables.id"), nullable=True)
    collection_id = Column(String(36), nullable=True)

    # Dynamic variables
    is_dynamic = Column(Boolean, default=False)
    dynamic_type = Column(String(50))  # timestamp, uuid, random, date

    # Security
    is_secret = Column(Boolean, default=False)
    is_masked = Column(Boolean, default=False)

    # Metadata
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", backref="environment_variables")
    children = relationship("EnvironmentVariable", remote_side=[id], backref="parent")


class EnvironmentManager:
    """Manages environment variables with inheritance and dynamic resolution"""

    # Dynamic variable generators
    DYNAMIC_GENERATORS = {
        "timestamp": lambda: str(int(datetime.utcnow().timestamp())),
        "timestamp_ms": lambda: str(int(datetime.utcnow().timestamp() * 1000)),
        "uuid": lambda: __import__("uuid").uuid4().hex,
        "uuid_v4": lambda: str(__import__("uuid").uuid4()),
        "date": lambda: datetime.utcnow().strftime("%Y-%m-%d"),
        "datetime": lambda: datetime.utcnow().isoformat(),
        "random_int": lambda: str(__import__("random").randint(1, 1000000)),
        "random_email": lambda: f"test_{__import__('uuid').uuid4().hex[:8]}@example.com",
    }

    @staticmethod
    def create_environment(
        db: Session,
        user_id: int,
        name: str,
        variables: Dict[str, Any],
        scope: str = "workspace",
        workspace_id: Optional[int] = None,
        parent_id: Optional[int] = None,
    ) -> Dict:
        """Create a new environment with variables"""

        environment_vars = []

        for key, value in variables.items():
            # Detect variable type
            var_type = "string"
            is_secret = False
            is_dynamic = False
            dynamic_type = None

            # Check if it's a secret (contains password, token, key, secret)
            if any(
                word in key.lower()
                for word in ["password", "token", "key", "secret", "api_key"]
            ):
                is_secret = True

            # Check if it's a dynamic variable (wrapped in double curly braces)
            if (
                isinstance(value, str)
                and value.startswith("{{")
                and value.endswith("}}")
            ):
                is_dynamic = True
                dynamic_type = value[2:-2].strip().lower()

            # Detect type
            if isinstance(value, bool):
                var_type = "boolean"
            elif isinstance(value, (int, float)):
                var_type = "number"

            env_var = EnvironmentVariable(
                user_id=user_id,
                workspace_id=workspace_id,
                name=name,
                key=key,
                value=str(value) if not is_dynamic else None,
                initial_value=str(value),
                type=var_type,
                scope=scope,
                parent_id=parent_id,
                is_dynamic=is_dynamic,
                dynamic_type=dynamic_type,
                is_secret=is_secret,
                is_masked=is_secret,
            )

            db.add(env_var)
            environment_vars.append(env_var)

        db.commit()

        return {
            "name": name,
            "scope": scope,
            "variables": [
                EnvironmentManager._variable_to_dict(var) for var in environment_vars
            ],
        }

    @staticmethod
    def resolve_variables(
        db: Session,
        user_id: int,
        text: str,
        workspace_id: Optional[int] = None,
        collection_id: Optional[str] = None,
        request_scope_vars: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Resolve variables in text with inheritance:
        Global -> Workspace -> Collection -> Request
        """

        # Build the variable hierarchy
        all_vars = {}

        # 1. Global variables
        global_vars = (
            db.query(EnvironmentVariable)
            .filter(
                EnvironmentVariable.user_id == user_id,
                EnvironmentVariable.scope == "global",
                EnvironmentVariable.is_active == True,
            )
            .all()
        )

        for var in global_vars:
            all_vars[var.key] = EnvironmentManager._get_variable_value(var)

        # 2. Workspace variables (override global)
        if workspace_id:
            workspace_vars = (
                db.query(EnvironmentVariable)
                .filter(
                    EnvironmentVariable.workspace_id == workspace_id,
                    EnvironmentVariable.scope == "workspace",
                    EnvironmentVariable.is_active == True,
                )
                .all()
            )

            for var in workspace_vars:
                all_vars[var.key] = EnvironmentManager._get_variable_value(var)

        # 3. Collection variables (override workspace)
        if collection_id:
            collection_vars = (
                db.query(EnvironmentVariable)
                .filter(
                    EnvironmentVariable.collection_id == collection_id,
                    EnvironmentVariable.scope == "collection",
                    EnvironmentVariable.is_active == True,
                )
                .all()
            )

            for var in collection_vars:
                all_vars[var.key] = EnvironmentManager._get_variable_value(var)

        # 4. Request-scoped variables (override all)
        if request_scope_vars:
            all_vars.update(request_scope_vars)

        # Replace variables in text
        # Support both {{variable}} and ${variable} syntax
        result = text

        # Replace {{variable}} syntax
        for match in re.finditer(r"\{\{(\w+)\}\}", text):
            var_name = match.group(1)
            if var_name in all_vars:
                result = result.replace(match.group(0), str(all_vars[var_name]))

        # Replace ${variable} syntax
        for match in re.finditer(r"\$\{(\w+)\}", text):
            var_name = match.group(1)
            if var_name in all_vars:
                result = result.replace(match.group(0), str(all_vars[var_name]))

        return result

    @staticmethod
    def _get_variable_value(var: EnvironmentVariable) -> Any:
        """Get the actual value of a variable (resolve if dynamic)"""

        if var.is_dynamic and var.dynamic_type:
            # Generate dynamic value
            generator = EnvironmentManager.DYNAMIC_GENERATORS.get(var.dynamic_type)
            if generator:
                return generator()
            return var.initial_value

        # Return masked value for secrets in response
        if var.is_secret and var.is_masked:
            return "********"

        return var.value

    @staticmethod
    def _variable_to_dict(var: EnvironmentVariable) -> Dict:
        """Convert variable to dictionary for response"""

        value = var.value
        if var.is_secret and var.is_masked:
            # Show only first and last 2 characters for secrets
            if value and len(value) > 4:
                value = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                value = "********"

        return {
            "id": var.id,
            "key": var.key,
            "value": value,
            "type": var.type,
            "scope": var.scope,
            "is_secret": var.is_secret,
            "is_dynamic": var.is_dynamic,
            "dynamic_type": var.dynamic_type,
            "description": var.description,
        }

    @staticmethod
    def get_environment_tree(
        db: Session, user_id: int, workspace_id: Optional[int] = None
    ) -> Dict:
        """Get the complete environment variable tree with inheritance"""

        tree = {"global": [], "workspace": [], "collections": {}}

        # Global variables
        global_vars = (
            db.query(EnvironmentVariable)
            .filter(
                EnvironmentVariable.user_id == user_id,
                EnvironmentVariable.scope == "global",
                EnvironmentVariable.is_active == True,
            )
            .all()
        )
        tree["global"] = [
            EnvironmentManager._variable_to_dict(var) for var in global_vars
        ]

        # Workspace variables
        if workspace_id:
            workspace_vars = (
                db.query(EnvironmentVariable)
                .filter(
                    EnvironmentVariable.workspace_id == workspace_id,
                    EnvironmentVariable.scope == "workspace",
                    EnvironmentVariable.is_active == True,
                )
                .all()
            )
            tree["workspace"] = [
                EnvironmentManager._variable_to_dict(var) for var in workspace_vars
            ]

            # Collection variables
            collection_vars = (
                db.query(EnvironmentVariable)
                .filter(
                    EnvironmentVariable.workspace_id == workspace_id,
                    EnvironmentVariable.scope == "collection",
                    EnvironmentVariable.is_active == True,
                )
                .all()
            )

            for var in collection_vars:
                if var.collection_id not in tree["collections"]:
                    tree["collections"][var.collection_id] = []
                tree["collections"][var.collection_id].append(
                    EnvironmentManager._variable_to_dict(var)
                )

        return tree

    @staticmethod
    def update_variable(
        db: Session,
        user_id: int,
        variable_id: int,
        key: Optional[str] = None,
        value: Optional[str] = None,
        is_secret: Optional[bool] = None,
    ) -> Dict:
        """Update an environment variable"""

        var = (
            db.query(EnvironmentVariable)
            .filter(
                EnvironmentVariable.id == variable_id,
                EnvironmentVariable.user_id == user_id,
            )
            .first()
        )

        if not var:
            raise ValueError("Variable not found")

        if key is not None:
            var.key = key
        if value is not None:
            var.value = value
            var.initial_value = value
        if is_secret is not None:
            var.is_secret = is_secret
            var.is_masked = is_secret

        var.updated_at = datetime.utcnow()
        db.commit()

        return EnvironmentManager._variable_to_dict(var)

    @staticmethod
    def delete_variable(db: Session, user_id: int, variable_id: int) -> bool:
        """Delete an environment variable"""

        var = (
            db.query(EnvironmentVariable)
            .filter(
                EnvironmentVariable.id == variable_id,
                EnvironmentVariable.user_id == user_id,
            )
            .first()
        )

        if not var:
            return False

        db.delete(var)
        db.commit()

        return True
