"""
API Orchestrator - FastAPI Server
Main application server with WebSocket support for real-time updates
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
import time
import traceback
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import io
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import stripe

# Sentry error tracking
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from src.config import settings

# Initialize Sentry if enabled
if settings.SENTRY_ENABLED and settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=0.1,
    )

# Import our orchestrator components
from src.core.orchestrator import APIOrchestrator, AgentType
from src.agents.discovery_agent import DiscoveryAgent
from src.agents.spec_agent import SpecGeneratorAgent
from src.agents.test_agent import TestGeneratorAgent

from src.agents.ai_agent import AIIntelligenceAgent
from src.agents.mock_server_agent import MockServerAgent
from src.database import init_db, SessionLocal, DatabaseManager, get_db, User
from sqlalchemy.orm import Session

# Import authentication
from src.auth import (
    AuthManager, UserCreate, UserLogin, Token, UserResponse,
    get_current_user, get_current_active_user, check_api_limit,
    check_subscription_feature, pwd_context
)

# Import export/import functionality
from src.export_import import ExportManager, ImportManager

# Import billing (moved here to avoid circular imports)
from src.billing import (
    BillingManager, 
    SubscriptionRequest, 
    SubscriptionResponse,
    UsageEventRequest,
    UsageResponse,
    BillingInfoResponse,
    PaymentMethodRequest
)

# Import project management
from src.project_manager import (
    ProjectManager, ProjectCreate, ProjectUpdate, 
    ProjectResponse, ProjectListResponse, ProjectStats
)

# Import password reset functionality
from src.password_reset import (
    PasswordResetRequest, PasswordResetConfirm, PasswordChangeRequest,
    request_password_reset, confirm_password_reset, change_password,
    PasswordResetToken  # Import model to ensure it's registered
)


# Initialize FastAPI app with enhanced documentation
app = FastAPI(
    title="API Orchestrator",
    description="""
## 🚀 AI-Powered API Orchestration Platform

A multi-agent system that automatically discovers, documents, tests, and analyzes APIs using AI.

### Key Features:
- 🔍 **Auto-Discovery**: Scans codebases to find API endpoints
- 📝 **Spec Generation**: Creates OpenAPI 3.0 documentation
- 🧪 **Test Creation**: Generates comprehensive test suites
- 🤖 **AI Analysis**: Security scoring and optimization recommendations
- 🎭 **Mock Servers**: Instant API mocking from specifications
- 🔄 **Real-time Updates**: WebSocket support for live progress tracking

### Authentication:
All endpoints except `/docs`, `/redoc`, and `/health` require JWT authentication.
Use `/auth/login` to obtain access tokens.

### Rate Limiting:
- Standard API endpoints: 10 requests/second
- Authentication endpoints: 5 requests/minute
- Based on subscription tier (Free/Pro/Enterprise)
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User registration, login, and token management"
        },
        {
            "name": "Orchestration",
            "description": "API discovery and orchestration pipeline"
        },
        {
            "name": "Projects",
            "description": "Project management and organization"
        },
        {
            "name": "AI Analysis",
            "description": "AI-powered security and optimization analysis"
        },
        {
            "name": "Mock Servers",
            "description": "Mock server generation and management"
        },
        {
            "name": "Export/Import",
            "description": "Data export and import functionality"
        },
        {
            "name": "User Management",
            "description": "User profile and settings"
        },
        {
            "name": "Health",
            "description": "System health and status"
        }
    ],
    servers=[
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api-orchestrator.com", "description": "Production server"},
        {"url": "https://staging.api-orchestrator.com", "description": "Staging server"}
    ],
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    contact={
        "name": "API Orchestrator Support",
        "email": "support@api-orchestrator.com",
        "url": "https://github.com/api-orchestrator/api-orchestrator"
    }
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    init_db()

# Import configuration
from src.config import settings

# Import structured logging
from src.utils.logger import logger, log_request

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    start_time = time.time()
    request_info = log_request(request)
    request_info["request_id"] = request_id
    
    logger.info(f"Request started: {request.method} {request.url.path}", extra=request_info)
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.performance.log_api_call(
            endpoint=str(request.url.path),
            method=request.method,
            duration_ms=duration_ms,
            status_code=response.status_code
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            exc_info=True,
            extra={**request_info, "duration_ms": duration_ms}
        )
        raise

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

# Root endpoint - only for API calls
@app.get("/api")
async def api_root():
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
@app.get("/health", tags=["Health"], summary="Check system health", description="Returns the health status of the API and its dependencies")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Authentication"], summary="Register new user", description="Create a new user account with email and password")
@limiter.limit("3/minute")  # Limit to 3 registrations per minute per IP
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    new_user = AuthManager.create_user(db, user_data)
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        is_active=new_user.is_active,
        subscription_tier=new_user.subscription_tier,
        api_calls_remaining=new_user.api_calls_limit - new_user.api_calls_this_month,
        created_at=new_user.created_at.isoformat()
    )

@app.post("/auth/login", response_model=Token)
@limiter.limit("5/minute")  # Limit to 5 login attempts per minute
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email and password to get JWT tokens"""
    user = AuthManager.authenticate_user(db, form_data.username, form_data.password)  # username field contains email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=30)
    access_token = AuthManager.create_access_token(
        data={"email": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = AuthManager.create_refresh_token(
        data={"email": user.email, "user_id": user.id}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@app.post("/auth/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = AuthManager.decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    email = payload.get("email")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=30)
    new_access_token = AuthManager.create_access_token(
        data={"email": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=new_access_token)

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        subscription_tier=current_user.subscription_tier,
        api_calls_remaining=current_user.api_calls_limit - current_user.api_calls_this_month,
        created_at=current_user.created_at.isoformat()
    )

@app.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client should discard tokens)"""
    return {"message": "Successfully logged out"}

# ==================== END AUTHENTICATION ENDPOINTS ====================

# ==================== PASSWORD RESET ENDPOINTS ====================

@app.post("/auth/forgot-password")
@limiter.limit("3/hour")  # Limit to 3 password reset requests per hour per IP
async def forgot_password(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset email"""
    result = await request_password_reset(db, reset_request.email)
    return result

@app.post("/auth/reset-password")
@limiter.limit("5/hour")  # Limit to 5 reset attempts per hour per IP
async def reset_password(
    request: Request,
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using token from email"""
    result = await confirm_password_reset(db, reset_data.token, reset_data.new_password)
    return result

@app.post("/auth/change-password")
async def change_password_endpoint(
    change_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    result = await change_password(
        db, 
        current_user.id, 
        change_data.current_password, 
        change_data.new_password
    )
    return result

# ==================== END PASSWORD RESET ENDPOINTS ====================

# ==================== USER PROFILE ENDPOINTS ====================
@app.get("/api/users/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information"""
    # Get user's API usage stats (simplified for now) 
    # Note: Project model not implemented yet, using 0 as placeholder
    total_projects = 0  # db.query(Project).filter(Project.user_id == current_user.id).count()
    
    return {
        "id": current_user.id,
        "name": current_user.username,
        "email": current_user.email,
        "company": getattr(current_user, "company", ""),
        "api_key": getattr(current_user, "api_key", f"sk_{current_user.id}_demo"),
        "subscription_tier": current_user.subscription_tier,
        "created_at": current_user.created_at.isoformat(),
        "last_login": datetime.utcnow().isoformat(),
        "api_calls_made": getattr(current_user, "api_calls_made", 0),
        "api_calls_limit": 10000 if current_user.subscription_tier == "enterprise" else 1000 if current_user.subscription_tier == "pro" else 100,
        "total_projects": total_projects
    }

@app.put("/api/users/profile")
async def update_user_profile(
    profile_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    # Only allow updating certain fields
    allowed_fields = ["username", "company"]
    
    for field in allowed_fields:
        if field in profile_data:
            setattr(current_user, field, profile_data[field])
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Profile updated successfully"}

@app.post("/api/users/change-password")
async def change_user_password(
    password_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user's password"""
    # Verify current password
    if not pwd_context.verify(password_data.get("current_password"), current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.hashed_password = pwd_context.hash(password_data.get("new_password"))
    current_user.password_changed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Password changed successfully"}

@app.post("/api/users/regenerate-api-key")
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate user's API key"""
    import secrets
    new_api_key = f"sk_{secrets.token_urlsafe(32)}"
    
    current_user.api_key = new_api_key
    db.commit()
    db.refresh(current_user)
    
    return {"api_key": new_api_key}
# ==================== END USER PROFILE ENDPOINTS ====================

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

# Main orchestration endpoint (protected)
@app.post("/api/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(
    request: OrchestrationRequest,
    current_user: User = Depends(check_api_limit),
    db: Session = Depends(get_db)
):
    """Start the orchestration process"""
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create project with current user
    project = DatabaseManager.create_project(
        db, 
        "Auto-Project", 
        source_path=request.source_path,
        source_type=request.source_type,
        user_id=current_user.id
    )
    task = DatabaseManager.create_task(db, task_id, project.id)
    
    # Validate source path
    if request.source_type == "directory":
        source_path = Path(request.source_path)
        if not source_path.exists():
            raise HTTPException(status_code=400, detail=f"Path {request.source_path} does not exist")
        
        # Validate path is within allowed directories (prevent path traversal)
        if not settings.validate_path(source_path):
            raise HTTPException(
                status_code=403, 
                detail="Access denied: Path is outside allowed directories"
            )
    
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
        
        # Step 4: AI Analysis
        await manager.broadcast({
            "type": "progress",
            "task_id": task_id,
            "stage": "ai_analysis",
            "message": "Running AI-powered analysis..."
        })
        
        ai_agent = orchestrator.agents[AgentType.AI_INTELLIGENCE]
        ai_analysis = await ai_agent.analyze(apis, specs)
        
        await manager.broadcast({
            "type": "ai_complete",
            "task_id": task_id,
            "security_score": ai_analysis.get("security_score", 0),
            "vulnerabilities": ai_analysis.get("vulnerabilities", []),
            "optimizations": ai_analysis.get("optimizations", []),
            "compliance": ai_analysis.get("compliance", {}),
            "executive_summary": ai_analysis.get("executive_summary", "")
        })
        
        # Step 5: Generate Mock Server
        await manager.broadcast({
            "type": "progress",
            "task_id": task_id,
            "stage": "mock_server",
            "message": "Generating mock server..."
        })
        
        mock_agent = orchestrator.agents[AgentType.MOCK_SERVER]
        mock_config = await mock_agent.generate(specs)
        
        await manager.broadcast({
            "type": "mock_complete",
            "task_id": task_id,
            "mock_port": mock_config.get("port", 9000),
            "mock_endpoints": len(mock_config.get("endpoints", [])),
            "mock_status": "ready"
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
        
        # Save AI analysis
        ai_file = output_dir / "ai_analysis.json"
        with open(ai_file, 'w') as f:
            json.dump(ai_analysis, f, indent=2)
        
        # Save mock server config
        mock_file = output_dir / "mock_server_config.json"
        with open(mock_file, 'w') as f:
            json.dump(mock_config, f, indent=2)
        
        # Update task status
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["completed_at"] = datetime.now().isoformat()
        active_tasks[task_id]["results"] = {
            "apis": len(apis),
            "specs": len(specs.get('paths', {})),
            "tests": len(tests),
            "security_score": ai_analysis.get("security_score", 0),
            "vulnerabilities_found": len(ai_analysis.get("vulnerabilities", [])),
            "mock_server_port": mock_config.get("port", 9000),
            "ai_summary": ai_analysis.get("executive_summary", "")
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

# Get AI analysis results
@app.get("/api/ai-analysis/{task_id}")
async def get_ai_analysis(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get AI analysis results for a task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        output_dir = Path("output") / task_id
        ai_file = output_dir / "ai_analysis.json"
        
        if not ai_file.exists():
            raise HTTPException(status_code=404, detail="AI analysis not found")
        
        with open(ai_file, 'r') as f:
            return json.load(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading AI analysis: {str(e)}")

# Get mock server configuration
@app.get("/api/mock-server/{task_id}")
async def get_mock_server_config(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get mock server configuration for a task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        output_dir = Path("output") / task_id
        mock_file = output_dir / "mock_server_config.json"
        
        if not mock_file.exists():
            raise HTTPException(status_code=404, detail="Mock server config not found")
        
        with open(mock_file, 'r') as f:
            return json.load(f)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading mock config: {str(e)}")

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

# ==================== EXPORT/IMPORT ENDPOINTS ====================

@app.get("/api/export/{task_id}")
async def export_artifacts(
    task_id: str,
    format: str = "zip",
    current_user: User = Depends(get_current_user)
):
    """Export orchestration artifacts in various formats"""
    
    # Check if format is allowed for user's subscription
    if not check_subscription_feature(current_user, "export_formats", format):
        allowed_formats = {
            "free": ["json"],
            "starter": ["json", "yaml"],
            "growth": ["json", "yaml", "postman", "openapi"],
            "enterprise": ["json", "yaml", "postman", "openapi", "markdown", "zip"]
        }
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Export format '{format}' not available in {current_user.subscription_tier} tier. "
                   f"Available formats: {allowed_formats[current_user.subscription_tier]}"
        )
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    output_dir = Path("output") / task_id
    spec_file = output_dir / "openapi.json"
    
    if not spec_file.exists():
        raise HTTPException(status_code=404, detail="OpenAPI spec not found for this task")
    
    # Load the OpenAPI spec
    with open(spec_file, 'r') as f:
        spec = json.load(f)
    
    # Load tests if available
    tests = []
    test_dir = output_dir / "tests"
    if test_dir.exists():
        for test_file in test_dir.glob("*.py"):
            with open(test_file, 'r') as f:
                tests.append({
                    "name": test_file.stem,
                    "framework": "pytest",
                    "code": f.read()
                })
    
    # Export based on format
    if format == "json":
        return JSONResponse(content=spec)
    
    elif format == "yaml":
        content = ExportManager.export_openapi_spec(spec, "yaml")
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/yaml",
            headers={"Content-Disposition": f"attachment; filename=openapi_{task_id}.yaml"}
        )
    
    elif format == "postman":
        content = ExportManager.export_openapi_spec(spec, "postman")
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=postman_collection_{task_id}.json"}
        )
    
    elif format == "markdown":
        content = ExportManager.export_openapi_spec(spec, "markdown")
        return StreamingResponse(
            io.BytesIO(content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=api_docs_{task_id}.md"}
        )
    
    elif format == "zip":
        # Create comprehensive ZIP bundle
        zip_content = ExportManager._create_zip_bundle(spec, tests)
        return StreamingResponse(
            io.BytesIO(zip_content),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=api_bundle_{task_id}.zip"}
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format: {format}"
        )

# Mock server management endpoints
@app.post("/api/mock-server/{task_id}/start")
async def start_mock_server(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Start the mock server for a task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get mock server config
    output_dir = Path("output") / task_id
    mock_file = output_dir / "mock_server_config.json"
    
    if not mock_file.exists():
        raise HTTPException(status_code=404, detail="Mock server configuration not found")
    
    with open(mock_file, 'r') as f:
        mock_config = json.load(f)
    
    # Start the mock server (simplified - in production you'd actually start a server process)
    mock_config["status"] = "running"
    mock_config["base_url"] = f"http://localhost:{mock_config.get('port', 9000)}"
    
    # Save updated config
    with open(mock_file, 'w') as f:
        json.dump(mock_config, f, indent=2)
    
    return {"success": True, "config": mock_config}

@app.post("/api/mock-server/{task_id}/stop")
async def stop_mock_server(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stop the mock server for a task"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get mock server config
    output_dir = Path("output") / task_id
    mock_file = output_dir / "mock_server_config.json"
    
    if not mock_file.exists():
        raise HTTPException(status_code=404, detail="Mock server configuration not found")
    
    with open(mock_file, 'r') as f:
        mock_config = json.load(f)
    
    # Stop the mock server
    mock_config["status"] = "stopped"
    
    # Save updated config
    with open(mock_file, 'w') as f:
        json.dump(mock_config, f, indent=2)
    
    return {"success": True}

@app.post("/api/mock-server/start")
async def start_mock_server_direct(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Start a mock server directly from OpenAPI spec"""
    spec = request.get("spec")
    if not spec:
        raise HTTPException(status_code=400, detail="OpenAPI spec required")
    
    # For demo purposes, return a mock response
    # In production, this would actually start a mock server
    port = 9000 + hash(str(spec)) % 1000  # Generate a port based on spec
    
    return {
        "success": True,
        "port": port,
        "message": f"Mock server started on port {port}",
        "endpoints": list(spec.get("paths", {}).keys()) if isinstance(spec, dict) else []
    }

@app.post("/api/import")
async def import_specification(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import an existing OpenAPI specification or Postman collection"""
    
    # Read file content
    content = await file.read()
    
    # Determine content type
    content_type = file.content_type
    if not content_type:
        # Try to guess from filename
        if file.filename.endswith(".json"):
            content_type = "application/json"
        elif file.filename.endswith((".yaml", ".yml")):
            content_type = "application/yaml"
        elif file.filename.endswith(".zip"):
            content_type = "application/zip"
    
    # Check if it's a Postman collection
    is_postman = False
    if content_type == "application/json":
        try:
            data = json.loads(content)
            if "info" in data and "schema" in data.get("info", {}) and "postman" in data["info"]["schema"]:
                is_postman = True
        except:
            pass
    
    # Import the specification
    if is_postman:
        spec = ImportManager.import_postman_collection(content)
    else:
        spec = ImportManager.import_openapi_spec(content, content_type)
    
    # Validate the specification
    ImportManager.validate_openapi_spec(spec)
    
    # Create a new task for the imported spec
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = {
        "status": "completed",
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "source": "import",
        "filename": file.filename
    }
    
    # Save the imported spec
    output_dir = Path("output") / task_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    spec_file = output_dir / "openapi.json"
    with open(spec_file, 'w') as f:
        json.dump(spec, f, indent=2)
    
    # Create database entry
    task = DatabaseManager.create_task(db, task_id)
    DatabaseManager.update_task(
        db, task_id,
        status="completed",
        stage="import",
        progress=100,
        specs_generated=1
    )
    
    return {
        "task_id": task_id,
        "status": "success",
        "message": f"Successfully imported {file.filename}",
        "endpoints": len(spec.get("paths", {})),
        "schemas": len(spec.get("components", {}).get("schemas", {}))
    }

@app.get("/api/export/formats")
async def get_export_formats(current_user: User = Depends(get_current_user)):
    """Get available export formats for current user's subscription tier"""
    
    tier_formats = {
        "free": ["json"],
        "starter": ["json", "yaml"],
        "growth": ["json", "yaml", "postman", "markdown"],
        "enterprise": ["json", "yaml", "postman", "markdown", "zip"]
    }
    
    return {
        "subscription_tier": current_user.subscription_tier,
        "available_formats": tier_formats.get(current_user.subscription_tier, ["json"]),
        "all_formats": {
            "json": "OpenAPI JSON specification",
            "yaml": "OpenAPI YAML specification",
            "postman": "Postman collection",
            "markdown": "Markdown documentation",
            "zip": "Complete bundle with all formats"
        }
    }

# ==================== END EXPORT/IMPORT ENDPOINTS ====================

# ==================== PROJECT MANAGEMENT ENDPOINTS ====================

@app.post("/api/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    project = ProjectManager.create_project(db, current_user.id, project_data)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        source_path=project.source_path,
        github_url=project.github_url,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        api_count=len(project.apis),
        task_count=len(project.tasks)
    )

@app.get("/api/projects", response_model=ProjectListResponse)
async def list_projects(
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all projects for the current user"""
    result = ProjectManager.list_projects(db, current_user.id, page, per_page, search)
    
    projects = [
        ProjectResponse(
            id=p["id"],
            name=p["name"],
            description=p["description"],
            source_type=p["source_type"],
            source_path=p["source_path"],
            github_url=p["github_url"],
            created_at=p["created_at"],
            updated_at=p["updated_at"],
            api_count=p["api_count"],
            task_count=p["task_count"]
        )
        for p in result["projects"]
    ]
    
    return ProjectListResponse(
        projects=projects,
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"]
    )

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    project = ProjectManager.get_project(db, current_user.id, project_id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        source_path=project.source_path,
        github_url=project.github_url,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        api_count=len(project.apis),
        task_count=len(project.tasks)
    )

@app.put("/api/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = ProjectManager.update_project(db, current_user.id, project_id, update_data)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        source_path=project.source_path,
        github_url=project.github_url,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        api_count=len(project.apis),
        task_count=len(project.tasks)
    )

@app.delete("/api/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project and all associated data"""
    ProjectManager.delete_project(db, current_user.id, project_id)
    return None

@app.get("/api/projects/stats/overview", response_model=ProjectStats)
async def get_project_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics for all user projects"""
    return ProjectManager.get_project_stats(db, current_user.id)

@app.post("/api/projects/{project_id}/clone", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def clone_project(
    project_id: int,
    new_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clone an existing project"""
    project = ProjectManager.clone_project(db, current_user.id, project_id, new_name)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        source_type=project.source_type,
        source_path=project.source_path,
        github_url=project.github_url,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        api_count=len(project.apis),
        task_count=len(project.tasks)
    )

@app.post("/api/projects/{project_id}/orchestrate", response_model=OrchestrationResponse)
async def orchestrate_project(
    project_id: int,
    current_user: User = Depends(check_api_limit),
    db: Session = Depends(get_db)
):
    """Start orchestration for a specific project"""
    
    # Get the project
    project = ProjectManager.get_project(db, current_user.id, project_id)
    
    # Create task
    task = ProjectManager.start_orchestration(db, current_user.id, project_id)
    
    # Store in active tasks
    active_tasks[task.id] = {
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "project_id": project_id,
        "source_path": project.source_path
    }
    
    # Start orchestration in background
    asyncio.create_task(run_orchestration(task.id, project.source_path or "/"))
    
    return OrchestrationResponse(
        task_id=task.id,
        status="started",
        message=f"Orchestration started for project '{project.name}'"
    )

# ==================== END PROJECT MANAGEMENT ENDPOINTS ====================

# ==================== BILLING ENDPOINTS ====================

from fastapi import Request, Header

@app.post("/api/billing/subscription", response_model=SubscriptionResponse)
async def create_or_update_subscription(
    subscription: SubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update user subscription"""
    billing = BillingManager(db)
    result = billing.create_subscription(
        user_id=current_user.id,
        tier=subscription.tier,
        payment_method_id=subscription.payment_method_id
    )
    
    return SubscriptionResponse(**result)

@app.delete("/api/billing/subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel user subscription"""
    billing = BillingManager(db)
    return billing.cancel_subscription(current_user.id)

@app.get("/api/billing/info", response_model=BillingInfoResponse)
async def get_billing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing information and usage for current user"""
    billing = BillingManager(db)
    return billing.get_billing_info(current_user.id)

@app.post("/api/billing/usage", response_model=UsageResponse)
async def track_usage(
    usage: UsageEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track usage event for billing"""
    billing = BillingManager(db)
    result = billing.track_usage(
        user_id=current_user.id,
        event_type=usage.event_type,
        quantity=usage.quantity,
        metadata=usage.metadata
    )
    
    return UsageResponse(**result)

@app.post("/api/billing/payment-method")
async def add_payment_method(
    payment_method: PaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a payment method to user account"""
    billing = BillingManager(db)
    
    if not current_user.stripe_customer_id:
        billing.create_customer(current_user.id, current_user.email, current_user.full_name)
    
    stripe.PaymentMethod.attach(
        payment_method.payment_method_id,
        customer=current_user.stripe_customer_id
    )
    
    return {"message": "Payment method added successfully"}

@app.post("/api/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    billing = BillingManager(db)
    
    return billing.process_webhook(payload, stripe_signature)

@app.get("/api/billing/pricing")
async def get_pricing_tiers():
    """Get available pricing tiers"""
    from src.billing import PRICING_TIERS
    
    return {
        "tiers": PRICING_TIERS,
        "usage_pricing": {
            "api_call": 0.001,
            "ai_analysis": 0.10,
            "mock_server_hour": 0.05,
            "export_operation": 0.01
        }
    }

@app.post("/api/billing/upgrade-to-enterprise")
async def request_enterprise_upgrade(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request enterprise tier upgrade (manual approval required)"""
    # Send notification to sales team
    logger.info(f"Enterprise upgrade requested by user {current_user.email}")
    
    # TODO: Integrate with CRM/sales system
    # TODO: Send email to sales team
    
    return {
        "message": "Enterprise upgrade request submitted. Our sales team will contact you within 24 hours.",
        "email": "enterprise@api-orchestrator.com"
    }

# ==================== END BILLING ENDPOINTS ====================

# Upload file for processing
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a file for processing"""
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Sanitize filename
    safe_filename = settings.sanitize_filename(file.filename)
    
    # Create secure upload directory
    upload_dir = settings.BASE_OUTPUT_DIR / "uploads" / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save uploaded file with sanitized name
    file_path = upload_dir / safe_filename
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Start orchestration on uploaded file
    request = OrchestrationRequest(
        source_type="upload",
        source_path=str(file_path)
    )
    
    return await orchestrate(request)

# Serve frontend static files
# The path needs to work both locally and in Docker
import os
frontend_paths = [
    "/app/frontend/dist",  # Docker path
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"),  # Local path
    "./frontend/dist",  # Relative path
]

frontend_found = False
for frontend_path in frontend_paths:
    if os.path.exists(frontend_path):
        logger.info(f"Serving frontend from: {frontend_path}")
        # Mount frontend at root, but only for non-API routes
        from fastapi.responses import HTMLResponse
        
        # Serve index.html for root
        @app.get("/", response_class=HTMLResponse)
        async def serve_frontend():
            index_path = os.path.join(frontend_path, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "r") as f:
                    return f.read()
            return "<h1>Frontend not found</h1>"
        
        # Mount static files for assets if they exist
        assets_path = os.path.join(frontend_path, "assets")
        if os.path.exists(assets_path):
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        
        # Also mount the entire dist directory for other static files
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        frontend_found = True
        break

if not frontend_found:
    logger.warning("Frontend not found in any expected location")

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Initialize database tables
    init_db()
    
    # Get port from environment variable (Railway provides this)
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting API Orchestrator Server...")
    print(f"📡 WebSocket: ws://0.0.0.0:{port}/ws")
    print(f"🌐 API: http://0.0.0.0:{port}")
    print(f"📚 Docs: http://0.0.0.0:{port}/docs")
    
    # Fixed: Use string import for reload to work
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    )