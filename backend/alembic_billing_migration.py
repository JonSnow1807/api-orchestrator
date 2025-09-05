"""
Database migration script for billing features
Run this to add billing-related columns to existing database
"""

from sqlalchemy import create_engine, text
import os
from datetime import datetime

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./api_orchestrator.db")

def run_migration():
    """Add billing-related columns to the database"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Check if columns already exist (for SQLite)
            result = conn.execute(text("PRAGMA table_info(users)"))
            existing_columns = [row[1] for row in result]
            
            # Add billing columns to users table if they don't exist
            billing_columns = [
                ("stripe_customer_id", "VARCHAR(255)"),
                ("stripe_subscription_id", "VARCHAR(255)"),
                ("stripe_payment_method_id", "VARCHAR(255)"),
                ("subscription_id", "VARCHAR(255)"),
                ("subscription_item_id", "VARCHAR(255)"),
                ("subscription_status", "VARCHAR(50) DEFAULT 'active'"),
                ("subscription_end_date", "DATETIME"),
                ("trial_end_date", "DATETIME"),
                ("ai_analyses_this_month", "INTEGER DEFAULT 0"),
                ("mock_server_hours_this_month", "FLOAT DEFAULT 0.0"),
                ("exports_this_month", "INTEGER DEFAULT 0"),
                ("full_name", "VARCHAR(255)"),
                ("company_name", "VARCHAR(255)"),
                ("phone_number", "VARCHAR(50)"),
                ("country", "VARCHAR(100)"),
                ("api_key", "VARCHAR(255)"),
                ("api_key_created_at", "DATETIME")
            ]
            
            for column_name, column_type in billing_columns:
                if column_name not in existing_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                        print(f"✅ Added column: {column_name}")
                    except Exception as e:
                        print(f"⚠️  Column {column_name} might already exist: {e}")
            
            # Create usage_events table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    unit_price FLOAT,
                    total_price FLOAT,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    billing_period VARCHAR(20),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """))
            print("✅ Created usage_events table")
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_usage_events_user_id ON usage_events(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_usage_events_created_at ON usage_events(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_usage_events_billing_period ON usage_events(billing_period)",
                "CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier)"
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    print(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                except Exception as e:
                    print(f"⚠️  Index might already exist: {e}")
            
            # Update existing users to have proper default values
            conn.execute(text("""
                UPDATE users 
                SET subscription_tier = 'free',
                    subscription_status = 'active',
                    api_calls_limit = 1000,
                    api_calls_this_month = COALESCE(api_calls_this_month, 0),
                    ai_analyses_this_month = 0,
                    mock_server_hours_this_month = 0.0,
                    exports_this_month = 0
                WHERE subscription_tier IS NULL
            """))
            print("✅ Updated existing users with default values")
            
            # Commit transaction
            trans.commit()
            print("\n🎉 Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    print("Starting billing migration...")
    run_migration()