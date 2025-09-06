#!/usr/bin/env python3
"""
Migration script from SQLite to PostgreSQL
Preserves all existing data during migration
"""

import os
import sys
import logging
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Get database URLs
    postgres_url = os.getenv("DATABASE_URL", "")
    
    # Fix Railway PostgreSQL URL format
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    
    if not postgres_url or "postgresql" not in postgres_url:
        logger.error("PostgreSQL DATABASE_URL not found or invalid")
        logger.info("Please add PostgreSQL to Railway and set DATABASE_URL environment variable")
        return False
    
    # SQLite database path
    if os.path.exists('/app'):
        sqlite_path = "sqlite:////app/data/api_orchestrator.db"
    else:
        sqlite_path = "sqlite:///./api_orchestrator.db"
    
    # Check if SQLite database exists
    sqlite_file = sqlite_path.replace("sqlite:///", "")
    if not os.path.exists(sqlite_file):
        logger.info("No SQLite database found. Starting fresh with PostgreSQL.")
        return True
    
    try:
        # Create engines
        logger.info("Connecting to databases...")
        sqlite_engine = create_engine(sqlite_path)
        postgres_engine = create_engine(postgres_url)
        
        # Create all tables in PostgreSQL first
        logger.info("Creating tables in PostgreSQL...")
        from backend.src.database import Base
        Base.metadata.create_all(postgres_engine)
        
        # Get all tables
        metadata = MetaData()
        metadata.reflect(bind=sqlite_engine)
        
        # Tables to migrate in order (respecting foreign keys)
        table_order = [
            'users',
            'projects', 
            'apis',
            'api_endpoints',
            'api_tests',
            'tasks',
            'mock_servers',
            'api_keys',
            'usage_events',
            'invoices',
            'password_reset_tokens'
        ]
        
        # Migrate each table
        for table_name in table_order:
            if table_name not in metadata.tables:
                logger.warning(f"Table {table_name} not found in SQLite, skipping...")
                continue
                
            logger.info(f"Migrating table: {table_name}")
            
            # Get table
            table = metadata.tables[table_name]
            
            # Read all data from SQLite
            with sqlite_engine.connect() as sqlite_conn:
                rows = sqlite_conn.execute(table.select()).fetchall()
                
                if not rows:
                    logger.info(f"  No data in {table_name}")
                    continue
                
                # Insert into PostgreSQL
                with postgres_engine.connect() as pg_conn:
                    # Convert rows to dictionaries
                    data = [dict(row._mapping) for row in rows]
                    
                    # Insert data
                    pg_conn.execute(table.insert(), data)
                    pg_conn.commit()
                    
                    logger.info(f"  Migrated {len(rows)} rows from {table_name}")
        
        logger.info("✅ Migration completed successfully!")
        
        # Verify migration
        logger.info("Verifying migration...")
        with postgres_engine.connect() as pg_conn:
            for table_name in table_order:
                if table_name not in metadata.tables:
                    continue
                table = metadata.tables[table_name]
                count = pg_conn.execute(f"SELECT COUNT(*) FROM {table_name}").scalar()
                logger.info(f"  {table_name}: {count} rows")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        logger.exception("Full error:")
        return False

def test_postgres_connection():
    """Test PostgreSQL connection"""
    postgres_url = os.getenv("DATABASE_URL", "")
    
    # Fix Railway PostgreSQL URL format
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)
    
    if not postgres_url or "postgresql" not in postgres_url:
        logger.error("PostgreSQL DATABASE_URL not configured")
        return False
    
    try:
        engine = create_engine(postgres_url)
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.scalar()
            logger.info(f"✅ PostgreSQL connected successfully!")
            logger.info(f"   Version: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== StreamAPI Database Migration Tool ===")
    
    # Test PostgreSQL connection first
    if not test_postgres_connection():
        logger.error("\n⚠️  PostgreSQL not available. Please:")
        logger.error("1. Add PostgreSQL to your Railway project")
        logger.error("2. Copy the DATABASE_URL from PostgreSQL service")
        logger.error("3. Add it to your web service environment variables")
        sys.exit(1)
    
    # Perform migration
    if migrate_database():
        logger.info("\n🎉 Database migration successful!")
        logger.info("Your app is now using PostgreSQL")
    else:
        logger.error("\n❌ Migration failed. Please check the logs above.")
        sys.exit(1)