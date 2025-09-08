#!/usr/bin/env python3
"""
Emergency auth fix script - helps recover access and debug auth issues
"""

import os
import sys
sys.path.insert(0, 'backend')

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.src.database import User, Base
from backend.src.auth import pwd_context
import argparse

def main():
    parser = argparse.ArgumentParser(description='Fix authentication issues')
    parser.add_argument('--list-users', action='store_true', help='List all users')
    parser.add_argument('--reset-password', help='Reset password for email')
    parser.add_argument('--new-password', help='New password to set')
    parser.add_argument('--create-admin', help='Create admin user with email')
    parser.add_argument('--username', help='Username for new admin')
    
    args = parser.parse_args()
    
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'sqlite:///./api_orchestrator.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    print(f"Connecting to database: {database_url[:30]}...")
    
    # Create engine and session
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        if args.list_users:
            users = db.query(User).all()
            print(f"\n{'='*60}")
            print(f"Found {len(users)} users:")
            print(f"{'='*60}")
            for user in users:
                print(f"ID: {user.id}")
                print(f"Email: {user.email}")
                print(f"Username: {user.username}")
                print(f"Active: {user.is_active}")
                print(f"Subscription: {user.subscription_tier}")
                print(f"Created: {user.created_at}")
                print(f"{'-'*60}")
        
        elif args.reset_password and args.new_password:
            user = db.query(User).filter(User.email == args.reset_password).first()
            if not user:
                print(f"❌ User with email {args.reset_password} not found")
                return
            
            # Hash the new password
            hashed_password = pwd_context.hash(args.new_password)
            user.hashed_password = hashed_password
            db.commit()
            print(f"✅ Password reset successfully for {user.email}")
            print(f"   Username: {user.username}")
            print(f"   New password: {args.new_password}")
        
        elif args.create_admin and args.username and args.new_password:
            # Check if user exists
            existing = db.query(User).filter(
                (User.email == args.create_admin) | (User.username == args.username)
            ).first()
            
            if existing:
                print(f"❌ User already exists with that email or username")
                print(f"   Email: {existing.email}")
                print(f"   Username: {existing.username}")
                return
            
            # Create new admin user
            hashed_password = pwd_context.hash(args.new_password)
            new_user = User(
                email=args.create_admin,
                username=args.username,
                hashed_password=hashed_password,
                is_active=True,
                subscription_tier='enterprise',
                api_calls_limit=1000000
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"✅ Admin user created successfully!")
            print(f"   Email: {new_user.email}")
            print(f"   Username: {new_user.username}")
            print(f"   Password: {args.new_password}")
            print(f"   Subscription: {new_user.subscription_tier}")
        
        else:
            print("Usage examples:")
            print("  List all users:")
            print("    python fix_auth.py --list-users")
            print()
            print("  Reset password:")
            print("    python fix_auth.py --reset-password user@example.com --new-password NewPass123!")
            print()
            print("  Create admin user:")
            print("    python fix_auth.py --create-admin admin@example.com --username admin --new-password Admin123!")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()