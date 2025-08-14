"""
Mock Server Agent - Instantly creates working mock servers from API specifications
This is a game-changer for API development - test before you build!
"""

import json
import random
import string
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from faker import Faker

from src.core.orchestrator import AgentMessage, AgentType

class MockServerAgent:
    """Agent that creates instant mock servers from OpenAPI specs"""
    
    def __init__(self):
        self.fake = Faker()
        self.mock_servers = {}  # Track running mock servers
        self.mock_data_store = {}  # In-memory data store for stateful mocks
        
    async def create_mock_server(self, api_spec: Dict, options: Dict = None) -> Dict:
        """
        Create a mock server from OpenAPI specification
        Returns mock server details including URL and generated code
        """
        
        print("🎭 Creating Mock Server...")
        
        # Default options
        config = {
            'port': options.get('port', 8001) if options else 8001,
            'host': options.get('host', '0.0.0.0') if options else '0.0.0.0',
            'delay': options.get('delay', 0) if options else 0,  # Response delay in ms
            'error_rate': options.get('error_rate', 0) if options else 0,  # Percentage of errors
            'stateful': options.get('stateful', True) if options else True,  # Remember state
            'realistic_data': options.get('realistic_data', True) if options else True
        }
        
        # Generate mock server code
        server_code = self._generate_mock_server_code(api_spec, config)
        
        # Generate sample data
        sample_data = self._generate_sample_data(api_spec)
        
        # Save mock server files
        mock_dir = Path("mock_servers") / f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        mock_dir.mkdir(parents=True, exist_ok=True)
        
        # Save server code
        server_file = mock_dir / "mock_server.py"
        server_file.write_text(server_code)
        
        # Save sample data
        data_file = mock_dir / "mock_data.json"
        with open(data_file, 'w') as f:
            json.dump(sample_data, f, indent=2)
        
        # Create Docker file for easy deployment
        dockerfile = self._generate_dockerfile(config['port'])
        (mock_dir / "Dockerfile").write_text(dockerfile)
        
        # Create docker-compose file
        docker_compose = self._generate_docker_compose(config['port'])
        (mock_dir / "docker-compose.yml").write_text(docker_compose)
        
        # Create README
        readme = self._generate_readme(api_spec, config)
        (mock_dir / "README.md").write_text(readme)
        
        result = {
            'status': 'created',
            'mock_server_url': f"http://localhost:{config['port']}",
            'mock_server_dir': str(mock_dir),
            'files_created': {
                'server': str(server_file),
                'data': str(data_file),
                'dockerfile': str(mock_dir / "Dockerfile"),
                'docker_compose': str(mock_dir / "docker-compose.yml"),
                'readme': str(mock_dir / "README.md")
            },
            'sample_endpoints': self._get_sample_endpoints(api_spec, config['port']),
            'instructions': f"""
Mock Server Created Successfully! 🎭

To run the mock server:

Option 1 - Direct Python:
  cd {mock_dir}
  pip install fastapi uvicorn faker
  python mock_server.py

Option 2 - Docker:
  cd {mock_dir}
  docker-compose up

The mock server will be available at: http://localhost:{config['port']}

Features:
- Realistic fake data using Faker
- Stateful operations (POST creates, GET retrieves, etc.)
- {config['error_rate']}% error rate simulation
- {config['delay']}ms response delay
- Swagger UI at http://localhost:{config['port']}/docs
            """
        }
        
        print(f"✅ Mock server created at: {mock_dir}")
        return result
    
    def _generate_mock_server_code(self, api_spec: Dict, config: Dict) -> str:
        """Generate FastAPI mock server code"""
        
        code = f'''#!/usr/bin/env python3
"""
Auto-generated Mock Server
Generated from OpenAPI specification
Timestamp: {datetime.now().isoformat()}
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
    title="{api_spec.get('info', {}).get('title', 'Mock API')}",
    description="Mock server auto-generated from OpenAPI spec",
    version="{api_spec.get('info', {}).get('version', '1.0.0')}"
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
data_store = {{}}

# Configuration
RESPONSE_DELAY = {config['delay']} / 1000  # Convert ms to seconds
ERROR_RATE = {config['error_rate']} / 100  # Convert percentage to decimal

# Load sample data
try:
    with open('mock_data.json', 'r') as f:
        sample_data = json.load(f)
except:
    sample_data = {{}}

def should_return_error():
    """Randomly return error based on configured error rate"""
    return random.random() < ERROR_RATE

def add_delay():
    """Add configured response delay"""
    if RESPONSE_DELAY > 0:
        time.sleep(RESPONSE_DELAY)

'''
        
        # Generate endpoint handlers
        paths = api_spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                handler_code = self._generate_endpoint_handler(
                    path, method, details, config['stateful']
                )
                code += handler_code + "\n\n"
        
        # Add main function
        code += f'''
if __name__ == "__main__":
    import uvicorn
    print("🎭 Starting Mock Server...")
    print(f"📡 API Documentation: http://localhost:{config['port']}/docs")
    print(f"🔗 Mock Server URL: http://localhost:{config['port']}")
    uvicorn.run(app, host="{config['host']}", port={config['port']})
'''
        
        return code
    
    def _generate_endpoint_handler(self, path: str, method: str, details: Dict, stateful: bool) -> str:
        """Generate handler code for a specific endpoint"""
        
        # Convert path parameters from {param} to {param:path}
        fastapi_path = path.replace('{', '{').replace('}', ':path}')
        
        # Extract operation details
        sanitized_path = path.replace('/', '_').replace('{', '').replace('}', '').replace('-', '_')
        operation_id = details.get('operationId', f"{method}{sanitized_path}")
        summary = details.get('summary', f"{method.upper()} {path}")
        
        # Generate handler based on method
        if method.lower() == 'get':
            if '{' in path:  # Has path parameters - single item
                handler = f'''
@app.get("{fastapi_path}")
async def {operation_id}(request: Request):
    """
    {summary}
    Mock implementation - returns fake data
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Extract ID from path
    path_params = request.path_params
    item_id = path_params.get(list(path_params.keys())[0]) if path_params else str(uuid.uuid4())
    
    # Return from store if exists (stateful), otherwise generate
    if "{path}" in data_store and item_id in data_store["{path}"]:
        return data_store["{path}"][item_id]
    
    # Generate fake data
    fake_item = {{
        "id": item_id,
        "name": fake.name(),
        "email": fake.email(),
        "created_at": fake.date_time().isoformat(),
        "description": fake.text(max_nb_chars=200),
        "status": random.choice(["active", "inactive", "pending"]),
        "value": random.randint(100, 10000)
    }}
    
    return JSONResponse(content=fake_item)
'''
            else:  # List endpoint
                handler = f'''
@app.get("{path}")
async def {operation_id}(
    limit: int = 10,
    offset: int = 0,
    sort: str = "created_at",
    order: str = "desc"
):
    """
    {summary}
    Mock implementation - returns list of fake data
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Generate fake list
    items = []
    for i in range(limit):
        items.append({{
            "id": str(uuid.uuid4()),
            "name": fake.name(),
            "email": fake.email(),
            "created_at": fake.date_time().isoformat(),
            "description": fake.text(max_nb_chars=200),
            "status": random.choice(["active", "inactive", "pending"]),
            "value": random.randint(100, 10000)
        }})
    
    return JSONResponse(content={{
        "items": items,
        "total": 100,  # Fake total
        "limit": limit,
        "offset": offset
    }})
'''
        
        elif method.lower() == 'post':
            handler = f'''
@app.post("{fastapi_path}")
async def {operation_id}(request: Request):
    """
    {summary}
    Mock implementation - creates fake resource
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Get request body
    try:
        body = await request.json()
    except:
        body = {{}}
    
    # Create fake resource
    new_id = str(uuid.uuid4())
    created_item = {{
        "id": new_id,
        **body,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }}
    
    # Store if stateful
    if "{path}" not in data_store:
        data_store["{path}"] = {{}}
    data_store["{path}"][new_id] = created_item
    
    return JSONResponse(
        content=created_item,
        status_code=201
    )
'''
        
        elif method.lower() == 'put' or method.lower() == 'patch':
            handler = f'''
@app.{method.lower()}("{fastapi_path}")
async def {operation_id}(request: Request):
    """
    {summary}
    Mock implementation - updates fake resource
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Get request body
    try:
        body = await request.json()
    except:
        body = {{}}
    
    # Extract ID
    path_params = request.path_params
    item_id = path_params.get(list(path_params.keys())[0]) if path_params else str(uuid.uuid4())
    
    # Update fake resource
    updated_item = {{
        "id": item_id,
        **body,
        "updated_at": datetime.now().isoformat()
    }}
    
    # Store if stateful
    if "{path}" not in data_store:
        data_store["{path}"] = {{}}
    data_store["{path}"][item_id] = updated_item
    
    return JSONResponse(content=updated_item)
'''
        
        elif method.lower() == 'delete':
            handler = f'''
@app.delete("{fastapi_path}")
async def {operation_id}(request: Request):
    """
    {summary}
    Mock implementation - deletes fake resource
    """
    add_delay()
    
    if should_return_error():
        raise HTTPException(status_code=500, detail="Simulated error")
    
    # Extract ID
    path_params = request.path_params
    item_id = path_params.get(list(path_params.keys())[0]) if path_params else None
    
    # Remove from store if exists
    if "{path}" in data_store and item_id in data_store["{path}"]:
        del data_store["{path}"][item_id]
    
    return Response(status_code=204)
'''
        
        else:
            handler = f'''
@app.{method.lower()}("{fastapi_path}")
async def {operation_id}():
    """
    {summary}
    Mock implementation
    """
    add_delay()
    return JSONResponse(content={{"message": "Mock response for {method.upper()} {path}"}})
'''
        
        return handler
    
    def _generate_sample_data(self, api_spec: Dict) -> Dict:
        """Generate sample data for the mock server"""
        
        sample_data = {}
        
        # Generate sample data for each endpoint
        for path, methods in api_spec.get('paths', {}).items():
            sample_data[path] = {}
            
            # Generate 10 sample items for each path
            for i in range(10):
                sample_id = str(uuid.uuid4())
                sample_data[path][sample_id] = {
                    "id": sample_id,
                    "name": self.fake.name(),
                    "email": self.fake.email(),
                    "phone": self.fake.phone_number(),
                    "address": self.fake.address(),
                    "company": self.fake.company(),
                    "job_title": self.fake.job(),
                    "description": self.fake.text(max_nb_chars=200),
                    "created_at": self.fake.date_time().isoformat(),
                    "updated_at": self.fake.date_time().isoformat(),
                    "status": random.choice(["active", "inactive", "pending", "archived"]),
                    "tags": [self.fake.word() for _ in range(random.randint(1, 5))],
                    "metadata": {
                        "source": "mock_server",
                        "version": "1.0.0",
                        "generated_at": datetime.now().isoformat()
                    }
                }
        
        return sample_data
    
    def _generate_dockerfile(self, port: int) -> str:
        """Generate Dockerfile for the mock server"""
        
        return f'''FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn faker

# Copy mock server files
COPY mock_server.py .
COPY mock_data.json .

# Expose port
EXPOSE {port}

# Run the mock server
CMD ["python", "mock_server.py"]
'''
    
    def _generate_docker_compose(self, port: int) -> str:
        """Generate docker-compose.yml for the mock server"""
        
        return f'''version: '3.8'

services:
  mock-server:
    build: .
    ports:
      - "{port}:{port}"
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./mock_data.json:/app/mock_data.json
    restart: unless-stopped
'''
    
    def _generate_readme(self, api_spec: Dict, config: Dict) -> str:
        """Generate README for the mock server"""
        
        title = api_spec.get('info', {}).get('title', 'Mock API')
        version = api_spec.get('info', {}).get('version', '1.0.0')
        
        return f'''# Mock Server - {title} v{version}

Auto-generated mock server from OpenAPI specification.

## 🚀 Quick Start

### Option 1: Python

```bash
pip install fastapi uvicorn faker
python mock_server.py
```

### Option 2: Docker

```bash
docker-compose up
```

## 📡 Access Points

- Mock Server: http://localhost:{config['port']}
- API Documentation: http://localhost:{config['port']}/docs
- OpenAPI Spec: http://localhost:{config['port']}/openapi.json

## ⚙️ Configuration

- **Port**: {config['port']}
- **Response Delay**: {config['delay']}ms
- **Error Rate**: {config['error_rate']}%
- **Stateful**: {config['stateful']}
- **Realistic Data**: {config['realistic_data']}

## 📚 Features

- ✅ Realistic fake data using Faker library
- ✅ Stateful operations (remembers created resources)
- ✅ Configurable error simulation
- ✅ Response delay simulation
- ✅ CORS enabled for frontend testing
- ✅ Swagger UI included
- ✅ Docker support

## 🧪 Testing

Test the mock server with curl:

```bash
# GET request
curl http://localhost:{config['port']}/api/items

# POST request
curl -X POST http://localhost:{config['port']}/api/items \\
  -H "Content-Type: application/json" \\
  -d '{{"name": "Test Item"}}'
```

## 📝 Sample Data

Sample data is stored in `mock_data.json` and loaded at startup.
The server maintains state during runtime for realistic testing.

---

Generated by API Orchestrator AI
'''
    
    def _get_sample_endpoints(self, api_spec: Dict, port: int) -> List[str]:
        """Get sample endpoint URLs for testing"""
        
        samples = []
        base_url = f"http://localhost:{port}"
        
        for path, methods in api_spec.get('paths', {}).items():
            for method in methods.keys():
                samples.append(f"{method.upper()} {base_url}{path}")
                if len(samples) >= 5:  # Limit to 5 samples
                    return samples
        
        return samples
    
    async def handle_message(self, message: AgentMessage):
        """Handle messages from other agents"""
        if message.action == "create_mock":
            spec = message.payload.get("spec")
            options = message.payload.get("options", {})
            await self.create_mock_server(spec, options)
        elif message.action == "stop_mock":
            # Stop a running mock server
            server_id = message.payload.get("server_id")
            # Implementation for stopping mock server
            pass