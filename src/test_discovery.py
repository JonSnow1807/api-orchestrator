import asyncio
from pathlib import Path
from src.agents.discovery_agent import DiscoveryAgent

# Create a sample FastAPI file to test
test_content = '''
from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hello World"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get a specific user by ID"""
    return {"user_id": user_id}

@app.post("/users")
async def create_user(name: str, email: str):
    """Create a new user"""
    return {"name": name, "email": email}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    return {"deleted": user_id}
'''

async def test_discovery():
    # Create test file
    test_file = Path("test_api.py")
    test_file.write_text(test_content)
    
    # Test discovery
    agent = DiscoveryAgent()
    apis = await agent.scan("test_api.py")
    
    print("\n🔍 Discovered APIs:")
    print("-" * 50)
    for api in apis:
        print(f"{api.method:6} {api.path:20} -> {api.handler_name}")
        if api.description:
            print(f"       Description: {api.description}")
    
    # Cleanup
    test_file.unlink()
    
    return apis

if __name__ == "__main__":
    apis = asyncio.run(test_discovery())
    print(f"\n✓ Total endpoints found: {len(apis)}")