#!/usr/bin/env python3
"""Create demo user for testing"""

from src.database import SessionLocal, init_db
from src.auth import AuthManager, UserCreate

def create_demo_user():
    """Create a demo user for testing"""
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Check if demo user exists
        from src.database import User
        existing = db.query(User).filter(User.email == "demo@streamapi.dev").first()
        
        if existing:
            print(f"Demo user already exists: {existing.email}")
            return existing
        
        # Create demo user
        demo_data = UserCreate(
            email="demo@streamapi.dev",
            username="demo",
            password="Demo123!",
            full_name="Demo User"
        )
        
        user = AuthManager.create_user(db, demo_data)
        print(f"✅ Demo user created:")
        print(f"   Email: demo@streamapi.dev")
        print(f"   Password: Demo123!")
        print(f"   Username: demo")
        
        # Give demo user premium features
        user.subscription_tier = "professional"
        user.api_calls_limit = 100000
        db.commit()
        print(f"   Subscription: Professional (100,000 API calls)")
        
        # Create access token
        token = AuthManager.create_access_token({"email": user.email})
        print(f"\n📋 Demo Token (for testing):")
        print(f"   {token[:50]}...")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating demo user: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_demo_user()
    print("\n✅ Demo user ready for testing!")
    print("You can now login with:")
    print("   Email: demo@streamapi.dev")
    print("   Password: Demo123!")