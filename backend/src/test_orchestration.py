import asyncio
import json
from pathlib import Path
from src.core.orchestrator import APIOrchestrator, AgentType
from src.agents.discovery_agent import DiscoveryAgent
from src.agents.spec_agent import SpecGeneratorAgent
from src.agents.test_agent import TestGeneratorAgent  # Add this import

# Test content remains the same...
test_content = '''
from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/users")
async def list_users(limit: int = Query(10), offset: int = Query(0)):
    """List all users with pagination"""
    return {"users": [], "total": 0, "limit": limit, "offset": offset}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    """Get a specific user by ID"""
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

@app.post("/users")
async def create_user(user: User):
    """Create a new user"""
    return {"id": "123", "message": "User created", "user": user}

@app.put("/users/{user_id}")
async def update_user(user_id: str, user: User):
    """Update an existing user"""
    return {"id": user_id, "message": "User updated", "user": user}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user"""
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {user_id} deleted"}

@app.get("/posts")
async def list_posts(user_id: Optional[str] = None):
    """List posts, optionally filtered by user"""
    return {"posts": [], "filter": {"user_id": user_id}}

@app.post("/posts")
async def create_post(title: str, content: str, user_id: str):
    """Create a new post"""
    return {"id": "456", "title": title, "content": content, "user_id": user_id}
'''

async def test_orchestration():
    # Create test file
    test_file = Path("test_api.py")
    test_file.write_text(test_content)  # noqa: F823
    
    try:
        # Initialize orchestrator
        orchestrator = APIOrchestrator()
        
        # Register agents
        discovery_agent = DiscoveryAgent()
        spec_agent = SpecGeneratorAgent()
        test_agent = TestGeneratorAgent()  # Add this
        
        orchestrator.register_agent(AgentType.DISCOVERY, discovery_agent)
        orchestrator.register_agent(AgentType.SPEC_GENERATOR, spec_agent)
        orchestrator.register_agent(AgentType.TEST_GENERATOR, test_agent)  # Add this
        
        # Run orchestration
        print("\n🚀 Starting API Orchestration...")
        print("=" * 60)
        
        results = await orchestrator.orchestrate("test_api.py")
        
        # Display results
        print("\n📊 Orchestration Results:")
        print("=" * 60)
        print(f"✓ Discovered {len(results['apis'])} endpoints")
        print(f"✓ Generated OpenAPI spec")
        print(f"✓ Generated {len(results.get('tests', []))} test files")
        
        # Save the spec
        if results['specs']:
            spec_file = Path("generated_spec.json")
            spec_file.write_text(json.dumps(results['specs'], indent=2))
            print(f"✓ Spec saved to {spec_file}")
        
        # Save the tests
        if results.get('tests'):
            # Export tests to file
            test_content = test_agent.export_tests(results['tests'], "file")
            test_file_path = Path("generated_tests.py")
            test_file_path.write_text(test_content)
            print(f"✓ Tests saved to {test_file_path}")
            
            # Show a preview
            print("\n📝 Generated Test Preview:")
            print("-" * 60)
            lines = test_content.split('\n')[:30]  # Show first 30 lines
            for line in lines:
                print(line)
            print("... (truncated)")
        
        # Show any errors
        if results['errors']:
            print("\n⚠️  Errors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        return results
        
    finally:
        # Cleanup
        test_file.unlink()

if __name__ == "__main__":
    results = asyncio.run(test_orchestration())
    print(f"\n✅ Orchestration completed successfully!")