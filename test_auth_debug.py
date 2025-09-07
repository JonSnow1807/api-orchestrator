#!/usr/bin/env python3
"""Debug authentication issues"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test direct database and auth functionality
def test_auth_directly():
    """Test auth without HTTP"""
    from backend.src.database import SessionLocal, init_db
    from backend.src.auth import AuthManager, UserCreate
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    try:
        # Create test user data
        user_data = UserCreate(
            email="direct@test.com",
            username="directtest",
            password="Direct123!",
            full_name="Direct Test"
        )
        
        print("Creating user directly...")
        user = AuthManager.create_user(db, user_data)
        print(f"✅ User created: {user.email}")
        
        # Test authentication
        print("Testing authentication...")
        auth_user = AuthManager.authenticate_user(db, "direct@test.com", "Direct123!")
        if auth_user:
            print(f"✅ Authentication successful: {auth_user.email}")
            
            # Create token
            token = AuthManager.create_access_token({"email": auth_user.email})
            print(f"✅ Token created: {token[:20]}...")
        else:
            print("❌ Authentication failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_auth_directly()