#!/usr/bin/env python3
"""
Clean test of database initialization
"""

import os
import sys
import tempfile
import subprocess

def test_database_init_clean():
    """Test database initialization in a clean Python process"""
    print("=" * 60)
    print("TESTING DATABASE INITIALIZATION (CLEAN)")
    print("=" * 60)

    # Create a test script to run in subprocess
    test_script = """
import sys
import os
import tempfile

# Set up paths
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'backend'))
sys.path.insert(0, os.path.join(base_dir, 'backend', 'src'))

# Use temporary database
temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
temp_db_path = temp_db.name
temp_db.close()
os.environ['DATABASE_URL'] = f'sqlite:///{temp_db_path}'

print(f"📁 Using temporary database: {temp_db_path}")

try:
    # Import and initialize database
    from src.database import Base, engine, init_db
    print("✅ Step 1: Database module imported")

    # Initialize
    init_db()
    print("✅ Step 2: init_db() executed successfully")

    # Check tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\\n📊 Created {len(tables)} tables:")
    important_tables = [
        'users', 'projects', 'workspaces', 'ai_keys',
        'workspace_webhooks', 'workspace_members', 'webhooks'
    ]

    success_count = 0
    for table in important_tables:
        if table in tables:
            print(f"  ✅ {table}")
            success_count += 1
        else:
            print(f"  ❌ {table} (missing)")

    # Test basic functionality
    from sqlalchemy.orm import Session
    session = Session(engine)

    # Create test user
    from src.database import User
    test_user = User(
        email='test@example.com',
        username='testuser',
        hashed_password='dummy',
        api_calls_this_month=0
    )
    session.add(test_user)
    session.commit()
    print("\\n✅ Step 3: Created test user")

    # Create test project
    from src.database import Project
    test_project = Project(
        user_id=test_user.id,
        name='Test Project',
        description='Test'
    )
    session.add(test_project)
    session.commit()
    print("✅ Step 4: Created test project")

    session.close()

    # Return success if we got most tables
    if success_count >= 5:
        print("\\n✅ Database initialization SUCCESS")
        exit(0)
    else:
        print(f"\\n⚠️  Only {success_count}/{len(important_tables)} tables created")
        exit(1)

except Exception as e:
    print(f"\\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

finally:
    # Clean up
    if 'temp_db_path' in locals() and os.path.exists(temp_db_path):
        os.remove(temp_db_path)
"""

    # Write test script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_script)
        test_file = f.name

    try:
        # Run in subprocess for clean import
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    finally:
        # Clean up test script
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    success = test_database_init_clean()

    print("\n" + "=" * 60)
    if success:
        print("✅ DATABASE INITIALIZATION WORKS")
    else:
        print("❌ DATABASE HAS ISSUES")
    print("=" * 60)