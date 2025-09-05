# 📁 Repository Structure

## Overview
The API Orchestrator repository follows a clean, modular architecture separating backend, frontend, and infrastructure concerns.

```
api-orchestrator/
├── backend/                    # Python/FastAPI backend
│   ├── src/                   # Source code
│   │   ├── agents/            # Multi-agent system
│   │   ├── api/              # API endpoints
│   │   ├── core/             # Core business logic
│   │   ├── utils/            # Utility functions
│   │   └── main.py           # FastAPI application
│   ├── tests/                # Test suite
│   │   ├── unit/            # Unit tests
│   │   ├── integration/     # Integration tests
│   │   └── e2e/            # End-to-end tests
│   ├── alembic/             # Database migrations
│   ├── requirements.txt      # Python dependencies
│   └── setup.py             # Package configuration
│
├── frontend/                 # React/Vite frontend
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── contexts/        # Context providers
│   │   └── assets/         # Static assets
│   ├── public/             # Public assets
│   └── package.json        # Node dependencies
│
├── docker/                  # Docker configurations
│   ├── Dockerfile          # Multi-stage build
│   └── nginx.conf          # Nginx configuration
│
├── docs/                   # Documentation
│   ├── api/               # API documentation
│   ├── deployment/        # Deployment guides
│   └── development/       # Development guides
│
├── scripts/               # Utility scripts
│   └── verify_features.py # Feature verification
│
├── .github/               # GitHub configurations
│   └── workflows/         # CI/CD pipelines
│
├── docker-compose.yml     # Container orchestration
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
└── README.md            # Project overview
```

## Directory Descriptions

### `/backend`
Contains all Python backend code including the FastAPI application, multi-agent system, and business logic.

### `/frontend`
React application with Vite build system for the web UI.

### `/docker`
Docker and container-related configurations for production deployment.

### `/docs`
Comprehensive documentation organized by category.

### `/scripts`
Utility scripts for development, deployment, and maintenance.

## Key Files

- `backend/src/main.py` - Main FastAPI application entry point
- `frontend/src/App.jsx` - React application root
- `docker-compose.yml` - Multi-container orchestration
- `.github/workflows/ci-cd.yml` - Automated CI/CD pipeline

## Running the Application

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up -d
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Environment Setup

1. Copy `.env.example` to `.env`
2. Configure required API keys and database settings
3. Run database migrations: `cd backend && alembic upgrade head`