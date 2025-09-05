"""
Alembic environment configuration for API Orchestrator
Handles database migrations for both development and production
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import database models
from src.database import Base, DATABASE_URL
from src.database import User, Project, API, Task, MockServer, TestResult

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add model's MetaData object for autogenerate support
target_metadata = Base.metadata

# Override database URL from environment if available
def get_database_url():
    """Get database URL from environment or config"""
    return os.getenv("DATABASE_URL", DATABASE_URL)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get database URL
    database_url = get_database_url()
    
    # Configure connection based on database type
    if "postgresql" in database_url:
        configuration = {
            "sqlalchemy.url": database_url,
            "sqlalchemy.pool_size": 20,
            "sqlalchemy.max_overflow": 40,
            "sqlalchemy.pool_pre_ping": True,
            "sqlalchemy.pool_recycle": 3600,
        }
    elif "sqlite" in database_url:
        configuration = {
            "sqlalchemy.url": database_url,
            "sqlalchemy.connect_args": {"check_same_thread": False},
        }
    else:
        configuration = {
            "sqlalchemy.url": database_url,
        }
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()

# Run migrations based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()