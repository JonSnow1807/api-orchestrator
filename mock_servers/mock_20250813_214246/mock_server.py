#!/usr/bin/env python3
"""
Auto-generated Mock Server
Generated from OpenAPI specification
Timestamp: 2025-08-13T21:42:46.036963
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import random
import time
import uuid
from datetime import datetime, timedelta
from faker import Faker

# Initialize FastAPI app
app = FastAPI(
    title="Mock API",
    description="Mock server auto-generated from OpenAPI spec",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Faker for realistic data
fake = Faker()

# In-memory data store
data_store = {}

# Configuration
RESPONSE_DELAY = 0 / 1000  # Convert ms to seconds
ERROR_RATE = 0 / 100  # Convert percentage to decimal

# Load sample data
try:
    with open('mock_data.json', 'r') as f:
        sample_data = json.load(f)
except:
    sample_data = {}

def should_return_error():
    """Randomly return error based on configured error rate"""
    return random.random() < ERROR_RATE

def add_delay():
    """Add configured response delay"""
    if RESPONSE_DELAY > 0:
        time.sleep(RESPONSE_DELAY)


@app.get("/users")
async def get_users(
    limit: int = 10,
    offset: int = 0,
    sort: str = "created_at",
    order: str = "desc"
):
    """
    GET /users
    Mock implementation - returns list of fake data
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Generate fake list
    items = []
    for i in range(limit):
        items.append({
            "id": str(uuid.uuid4()),
            "name": fake.name(),
            "email": fake.email(),
            "created_at": fake.date_time().isoformat(),
            "description": fake.text(max_nb_chars=200),
            "status": random.choice(["active", "inactive", "pending"]),
            "value": random.randint(100, 10000)
        })
    
    return JSONResponse(content={
        "items": items,
        "total": 100,  # Fake total
        "limit": limit,
        "offset": offset
    })



@app.post("/users")
async def post_users(request: Request):
    """
    POST /users
    Mock implementation - creates fake resource
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Get request body
    try:
        body = await request.json()
    except:
        body = {}
    
    # Create fake resource
    new_id = str(uuid.uuid4())
    created_item = {
        "id": new_id,
        **body,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Store if stateful
    if "/users" not in data_store:
        data_store["/users"] = {}
    data_store["/users"][new_id] = created_item
    
    return JSONResponse(
        content=created_item,
        status_code=201
    )



@app.get("/users/{id:path}")
async def get_users_id(request: Request):
    """
    GET /users/{id}
    Mock implementation - returns fake data
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Extract ID from path
    path_params = request.path_params
    item_id = path_params.get(list(path_params.keys())[0]) if path_params else str(uuid.uuid4())
    
    # Return from store if exists (stateful), otherwise generate
    if "/users/{id}" in data_store and item_id in data_store["/users/{id}"]:
        return data_store["/users/{id}"][item_id]
    
    # Generate fake data
    fake_item = {
        "id": item_id,
        "name": fake.name(),
        "email": fake.email(),
        "created_at": fake.date_time().isoformat(),
        "description": fake.text(max_nb_chars=200),
        "status": random.choice(["active", "inactive", "pending"]),
        "value": random.randint(100, 10000)
    }
    
    return JSONResponse(content=fake_item)



@app.delete("/users/{id:path}")
async def delete_users_id(request: Request):
    """
    DELETE /users/{id}
    Mock implementation - deletes fake resource
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Extract ID
    path_params = request.path_params
    item_id = path_params.get(list(path_params.keys())[0]) if path_params else None
    
    # Remove from store if exists
    if "/users/{id}" in data_store and item_id in data_store["/users/{id}"]:
        del data_store["/users/{id}"][item_id]
    
    return Response(status_code=204)



if __name__ == "__main__":
    import uvicorn
    print("🎭 Starting Mock Server...")
    print(f"📡 API Documentation: http://localhost:8001/docs")
    print(f"🔗 Mock Server URL: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
