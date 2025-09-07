#!/usr/bin/env python3
"""Test registration directly"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.database import SessionLocal, init_db
from backend.src.auth import AuthManager
from backend.src.models import User

def test_registration():
    """Test user registration"""
    
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == "test@example.com").first()
        if existing:
            print(f"User already exists: {existing.email}")
            db.delete(existing)
            db.commit()
            print("Deleted existing user")
        
        # Create new user
        auth_manager = AuthManager()
        user = auth_manager.register_user(
            db=db,
            username="testuser",
            email="test@example.com",
            password="Test123!",
            full_name="Test User"
        )
        
        print(f"✅ User created: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Username: {user.username}")
        
        # Test login
        token = auth_manager.authenticate_user(db, "test@example.com", "Test123!")
        if token:
            print(f"✅ Login successful")
            print(f"   Token: {token[:20]}...")
        else:
            print("❌ Login failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_registration()