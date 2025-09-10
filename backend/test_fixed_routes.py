#!/usr/bin/env python
"""
Test script to verify SQLAlchemy relationship fixes
Tests webhook and AI key routes functionality
"""

import sys
import json
from datetime import datetime

def test_imports():
    """Test if all models import without errors"""
    print("🔍 Testing model imports...")
    try:
        from src.database import Base, User, Project
        from src.models.workspace import (
            Workspace, WorkspaceInvitation, WorkspaceActivity,
            WorkspaceWebhook, ResourcePermission
        )
        from src.models.ai_keys import AIKey, AIKeyUsage
        print("✅ All models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_relationships():
    """Test if relationships are properly defined"""
    print("\n🔍 Testing model relationships...")
    try:
        from src.models.workspace import Workspace
        from src.models.ai_keys import AIKey
        
        # Check Workspace relationships
        workspace_rels = [
            'creator', 'members', 'invitations', 'projects',
            'activity_logs', 'webhooks', 'ai_keys'
        ]
        
        for rel in workspace_rels:
            if not hasattr(Workspace, rel):
                print(f"❌ Missing relationship: Workspace.{rel}")
                return False
        
        # Check AIKey relationships
        if not hasattr(AIKey, 'workspace'):
            print("❌ Missing relationship: AIKey.workspace")
            return False
            
        print("✅ All relationships are properly defined")
        return True
    except Exception as e:
        print(f"❌ Relationship test error: {e}")
        return False

def test_routes():
    """Test if routes are properly registered"""
    print("\n🔍 Testing route registration...")
    try:
        from src.main import app
        
        routes = [route for route in app.routes if hasattr(route, 'path')]
        webhook_routes = [r for r in routes if '/api/webhooks' in r.path]
        ai_key_routes = [r for r in routes if '/api/ai-keys' in r.path]
        
        if len(webhook_routes) == 0:
            print("❌ No webhook routes found")
            return False
        
        if len(ai_key_routes) == 0:
            print("❌ No AI key routes found")
            return False
            
        print(f"✅ Found {len(webhook_routes)} webhook routes")
        print(f"✅ Found {len(ai_key_routes)} AI key routes")
        
        # List some routes
        print("\n📋 Sample webhook routes:")
        for route in webhook_routes[:3]:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"  - {route.path} [{methods}]")
            
        print("\n📋 Sample AI key routes:")
        for route in ai_key_routes[:3]:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"  - {route.path} [{methods}]")
            
        return True
    except Exception as e:
        print(f"❌ Route test error: {e}")
        return False

def test_database_schema():
    """Test if database schema can be created without errors"""
    print("\n🔍 Testing database schema creation...")
    try:
        from sqlalchemy import create_engine
        from src.database import Base
        
        # Import all models to register them
        from src.database import User, Project
        from src.models.workspace import (
            Workspace, WorkspaceInvitation, WorkspaceActivity,
            WorkspaceWebhook, ResourcePermission
        )
        from src.models.ai_keys import AIKey, AIKeyUsage
        
        # Create in-memory database for testing
        engine = create_engine("sqlite:///:memory:")
        
        # Try to create all tables
        Base.metadata.create_all(bind=engine)
        
        # Check if tables were created
        tables = Base.metadata.tables.keys()
        expected_tables = [
            'users', 'projects', 'workspaces', 'workspace_invitations',
            'workspace_activity', 'workspace_webhooks', 'ai_keys', 'ai_key_usage'
        ]
        
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
            
        print(f"✅ All {len(tables)} tables created successfully")
        print(f"   Tables: {', '.join(sorted(tables))}")
        return True
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Testing SQLAlchemy Relationship Fixes")
    print("=" * 60)
    
    tests = [
        ("Model Imports", test_imports),
        ("Model Relationships", test_relationships),
        ("Route Registration", test_routes),
        ("Database Schema", test_database_schema)
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! SQLAlchemy relationships are fixed.")
        print("🔧 Webhook and AI Key routes are now operational.")
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()