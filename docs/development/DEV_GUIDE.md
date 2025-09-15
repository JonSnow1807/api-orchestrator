# Development Guide

This file provides development guidance when working with code in this repository.

## Commands

### Backend (Python/FastAPI)
```bash
# Start backend server
python -m src.main

# Run tests
pytest tests/
python test_real_ai.py  # Test AI integration
python test_full_pipeline.py  # Test full orchestration pipeline

# Install dependencies
pip install -r requirements.txt
pip install "python-jose[cryptography]" passlib python-multipart bcrypt

# Initialize database
python -c "from src.database import init_db; init_db()"

# Environment setup
export PYTHONPATH="${PYTHONPATH}:${PWD}"
export ANTHROPIC_API_KEY="your-api-key"  # Required for AI features
```

### Frontend (React/Vite)
```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build production
npm run build

# Lint check
npm run lint

# Preview production build
npm run preview
```

## Architecture Overview

### Multi-Agent System
The core architecture is based on a multi-agent orchestration system where specialized agents handle different aspects of API development:

- **APIOrchestrator** (`src/core/orchestrator.py`): Coordinates all agents through a message queue system
- **DiscoveryAgent** (`src/agents/discovery_agent.py`): Scans codebases to identify API endpoints
- **SpecGeneratorAgent** (`src/agents/spec_agent.py`): Creates OpenAPI 3.0 specifications
- **TestGeneratorAgent** (`src/agents/test_agent.py`): Generates test suites (pytest, Jest, Postman)
- **AIIntelligenceAgent** (`src/agents/ai_agent.py`): Provides AI-powered analysis
- **MockServerAgent** (`src/agents/mock_server_agent.py`): Creates functional mock servers

### Backend Stack
- **FastAPI** server with WebSocket support for real-time updates
- **SQLAlchemy** ORM with SQLite/PostgreSQL support
- **JWT authentication** with subscription tiers
- **WebSocket ConnectionManager** for live progress updates

### Frontend Stack
- **React** with Vite bundler
- **Tailwind CSS** for styling
- **Socket.IO** for real-time WebSocket communication
- **Axios** for API calls
- **Framer Motion** for animations

### Key Data Flow
1. User initiates orchestration through React frontend
2. FastAPI receives request and creates orchestration task
3. APIOrchestrator coordinates agents via message queue
4. Agents process in sequence: Discovery → Spec → Tests → AI Analysis → Mock Server
5. Real-time updates sent via WebSocket to frontend
6. Generated artifacts saved to `output/` directory

## Testing Approach

- Unit tests use **pytest** for Python components
- Test files are prefixed with `test_` in root and `src/` directories
- Mock data generation uses **Faker** library
- No specific test runner configuration (pytest.ini, setup.cfg)

## Key API Endpoints

- `POST /orchestrate` - Start orchestration process
- `WebSocket /ws/{client_id}` - Real-time updates
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /results/{task_id}` - Retrieve orchestration results

## Generated Output Structure

```
output/{task_id}/
├── openapi_spec.json     # OpenAPI 3.0 specification
├── tests/                # Generated test suites
├── mock_server/          # Mock server implementation
└── ai_analysis.json      # AI-powered insights
```

## Development Notes

- Backend runs on `http://localhost:8000`
- Frontend runs on `http://localhost:5173`
- Database file: `api_orchestrator.db` (SQLite default)
- Mock servers saved to `mock_servers/` directory
- Supports FastAPI, Flask, Django (Python) and Express.js (JavaScript) frameworks