"""
API Orchestrator - FastAPI Server
Main application server with WebSocket support for real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime
from pathlib import Path
import uuid

# Import our orchestrator components
from src.core.orchestrator import APIOrchestrator, AgentType
from src.agents.discovery_agent import DiscoveryAgent
from src.agents.spec_agent import SpecGeneratorAgent
from src.agents.test_agent import TestGeneratorAgent

from src.agents.ai_agent import AIIntelligenceAgent
from src.agents.mock_server_agent import MockServerAgent
from src.database import init_db, SessionLocal, DatabaseManager


# Initialize FastAPI app
app = FastAPI(
    title="API Orchestrator",
    description="Multi-agent AI orchestrator for API development & testing",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = APIOrchestrator()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
        
    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients"""
        message_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                # Connection might be closed
                pass

manager = ConnectionManager()

# Request/Response models
class OrchestrationRequest(BaseModel):
    source_type: str = "directory"  # "directory", "github", "upload"
    source_path: str
    options: Optional[Dict] = None

class OrchestrationResponse(BaseModel):
    task_id: str
    status: str
    message: str
    
class StatusResponse(BaseModel):
    is_running: bool
    registered_agents: List[str]
    discovered_apis: int
    active_connections: int

# Active orchestration tasks
active_tasks = {}

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "API Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "orchestrate": "/api/orchestrate",
            "status": "/api/status",
            "websocket": "/ws",
            "health": "/health"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "Connected to API Orchestrator"
            }),
            websocket
        )
        
        # Keep connection alive
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    websocket
                )
            elif message.get("type") == "get_status":
                status = orchestrator.get_status()
                await manager.send_personal_message(
                    json.dumps({"type": "status", "data": status}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Main orchestration endpoint
@app.post("/api/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(request: OrchestrationRequest):
    """Start the orchestration process"""
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    db = SessionLocal()
    project = DatabaseManager.create_project(db, "Auto-Project", source_path=request.source_path)
    task = DatabaseManager.create_task(db, task_id, project.id)
    db.close()
    
    # Validate source path
    if request.source_type == "directory":
        source_path = Path(request.source_path)
        if not source_path.exists():
            raise HTTPException(status_code=400, detail=f"Path {request.source_path} does not exist")
    
    # Initialize orchestrator if not already done
    if not orchestrator.agents:
        await initialize_orchestrator()
    
    # Start orchestration in background
    asyncio.create_task(run_orchestration(task_id, request.source_path))
    
    # Store task
    active_tasks[task_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "source_path": request.source_path
    }
    
    return OrchestrationResponse(
        task_id=task_id,
        status="started",
        message=f"Orchestration started for {request.source_path}"
    )

async def initialize_orchestrator():
    """Initialize the orchestrator with all agents"""
    print("🔧 Initializing orchestrator...")
    
    # Register agents
    orchestrator.register_agent(AgentType.DISCOVERY, DiscoveryAgent())
    orchestrator.register_agent(AgentType.SPEC_GENERATOR, SpecGeneratorAgent())
    orchestrator.register_agent(AgentType.TEST_GENERATOR, TestGeneratorAgent())
    orchestrator.register_agent(AgentType.AI_INTELLIGENCE, AIIntelligenceAgent())
    orchestrator.register_agent(AgentType.MOCK_SERVER, MockServerAgent())
    
    # Broadcast initialization status
    await manager.broadcast({
        "type": "system",
        "message": "Orchestrator initialized with all agents",
        "timestamp": datetime.now().isoformat()
    })

async def run_orchestration(task_id: str, source_path: str):
    """Run the orchestration process with real-time updates"""
    
    try:
        # Broadcast start
        await manager.broadcast({
            "type": "orchestration_start",
            "task_id": task_id,
            "source_path": source_path,
            "timestamp": datetime.now().isoformat()
        })
        
        # Step 1: Discovery
        await manager.broadcast({
            "type": "progress",
            "task_id": task_id,
            "stage": "discovery",
            "message": "Discovering API endpoints..."
        })
        
        apis = await orchestrator.discover_apis(source_path)
        
        await manager.broadcast({
            "type": "discovery_complete",
            "task_id": task_id,
            "apis_found": len(apis),
            "endpoints": [{"method": api.method, "path": api.path} for api in apis]
        })
        
        # Step 2: Generate Specs
        await manager.broadcast({
            "type": "progress",
            "task_id": task_id,
            "stage": "spec_generation",
            "message": "Generating OpenAPI specifications..."
        })
        
        specs = await orchestrator.generate_specs(apis)
        
        await manager.broadcast({
            "type": "spec_complete",
            "task_id": task_id,
            "paths": len(specs.get('paths', {})),
            "schemas": len(specs.get('components', {}).get('schemas', {}))
        })
        
        # Step 3: Generate Tests
        await manager.broadcast({
            "type": "progress",
            "task_id": task_id,
            "stage": "test_generation",
            "message": "Generating test suites..."
        })
        
        tests = await orchestrator.generate_tests(specs)
        
        await manager.broadcast({
            "type": "tests_complete",
            "task_id": task_id,
            "tests_generated": len(tests),
            "frameworks": list(set(test.get('framework') for test in tests))
        })
        
        # Save results
        output_dir = Path("output") / task_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save OpenAPI spec
        spec_file = output_dir / "openapi.json"
        with open(spec_file, 'w') as f:
            json.dump(specs, f, indent=2)
        
        # Save tests
        test_agent = orchestrator.agents[AgentType.TEST_GENERATOR]
        test_agent.export_tests(str(output_dir / "tests"))
        
        # Update task status
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["completed_at"] = datetime.now().isoformat()
        active_tasks[task_id]["results"] = {
            "apis": len(apis),
            "specs": len(specs.get('paths', {})),
            "tests": len(tests)
        }
        
        # Broadcast completion
        await manager.broadcast({
            "type": "orchestration_complete",
            "task_id": task_id,
            "results": active_tasks[task_id]["results"],
            "output_dir": str(output_dir)
        })
        
    except Exception as e:
        # Update task status
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["error"] = str(e)
        
        # Broadcast error
        await manager.broadcast({
            "type": "error",
            "task_id": task_id,
            "error": str(e)
        })

# Get orchestrator status
@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get the current status of the orchestrator"""
    status = orchestrator.get_status()
    
    return StatusResponse(
        is_running=status["is_running"],
        registered_agents=[agent.value for agent in status["registered_agents"]],
        discovered_apis=status["discovered_apis"],
        active_connections=len(manager.active_connections)
    )

# Get task status
@app.get("/api/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return active_tasks[task_id]

# List all tasks
@app.get("/api/tasks")
async def list_tasks():
    """List all orchestration tasks"""
    return {"tasks": active_tasks}

# Download generated files
@app.get("/api/download/{task_id}/{file_type}")
async def download_file(task_id: str, file_type: str):
    """Download generated files (spec, tests, etc.)"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    output_dir = Path("output") / task_id
    
    if file_type == "spec":
        file_path = output_dir / "openapi.json"
    elif file_type == "tests":
        # Create a zip file of all tests
        import zipfile
        zip_path = output_dir / "tests.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            test_dir = output_dir / "tests"
            for file in test_dir.rglob("*"):
                if file.is_file():
                    zipf.write(file, file.relative_to(test_dir))
        file_path = zip_path
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type='application/octet-stream'
    )

# Upload file for processing
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing"""
    
    # Create upload directory
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Start orchestration on uploaded file
    request = OrchestrationRequest(
        source_type="upload",
        source_path=str(file_path)
    )
    
    return await orchestrate(request)

# Serve static files (for frontend later)
# Uncomment when frontend is ready
# app.mount("/static", StaticFiles(directory="frontend/build"), name="static")

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting API Orchestrator Server...")
    print("📡 WebSocket: ws://localhost:8000/ws")
    print("🌐 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    
    # Fixed: Use string import for reload to work
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )