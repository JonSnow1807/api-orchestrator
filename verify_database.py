#!/usr/bin/env python3
"""
Verify database can be initialized without errors
"""

import sys
import os
import tempfile

# Add paths
sys.path.insert(0, 'backend')
sys.path.insert(0, 'backend/src')

def test_database_init():
    """Test if database can be initialized properly"""
    print("=" * 60)
    print("TESTING DATABASE INITIALIZATION")
    print("=" * 60)

    # Use a temporary database for testing
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    try:
        # Set temporary database
        os.environ['DATABASE_URL'] = f'sqlite:///{temp_db_path}'
        print(f"📁 Using temporary database: {temp_db_path}")

        # Clear any cached imports
        modules_to_clear = [
            'backend.src.database',
            'backend.src.models.workspace',
            'backend.src.models.ai_keys',
            'backend.src.models.webhook'
        ]

        import sys
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        # Now import fresh
        from backend.src.database import Base, engine, init_db
        print("✅ Step 1: Database module imported")

        # Initialize database
        init_db()
        print("✅ Step 2: init_db() executed")

        # Check tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\n📊 Created {len(tables)} tables:")
        important_tables = [
            'users', 'projects', 'workspaces', 'ai_keys',
            'workspace_webhooks', 'workspace_members'
        ]

        for table in important_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (missing)")

        # Test relationships by creating objects
        from sqlalchemy.orm import Session
        from backend.src.database import User, Project

        session = Session(engine)

        # Create test user
        test_user = User(
            email='test@example.com',
            username='testuser',
            hashed_password='dummy',
            api_calls_this_month=0
        )
        session.add(test_user)
        session.commit()
        print("\n✅ Step 3: Created test user")

        # Create test project
        test_project = Project(
            user_id=test_user.id,
            name='Test Project',
            description='Test'
        )
        session.add(test_project)
        session.commit()
        print("✅ Step 4: Created test project with user relationship")

        # Test workspace models
        from backend.src.models.workspace import Workspace
        test_workspace = Workspace(
            name='Test Workspace',
            slug='test-workspace',
            created_by=test_user.id
        )
        session.add(test_workspace)
        session.commit()
        print("✅ Step 5: Created test workspace")

        # Test AI keys model
        from backend.src.models.ai_keys import AIKey
        test_key = AIKey(
            workspace_id=test_workspace.id,
            provider='openai',
            key_name='test-key',
            encrypted_key='encrypted',
            key_hash='hash123',
            created_by=test_user.id
        )
        session.add(test_key)
        session.commit()
        print("✅ Step 6: Created AI key with workspace relationship")

        session.close()

        return True

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
            print(f"\n🗑️  Cleaned up temporary database")

        # Reset environment
        if 'DATABASE_URL' in os.environ:
            del os.environ['DATABASE_URL']

if __name__ == "__main__":
    success = test_database_init()

    print("\n" + "=" * 60)
    if success:
        print("✅ DATABASE INITIALIZATION WORKS")
    else:
        print("❌ DATABASE HAS ISSUES")
    print("=" * 60)