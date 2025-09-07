# API Orchestrator Platform - Complete Knowledge Transfer

## Project Overview
**API Orchestrator** is a Postman competitor with AI-powered features for API discovery, testing, documentation, and orchestration. It's built with FastAPI (backend) and React/Vite (frontend), deployed on Railway with custom domain streamapi.dev.

## Architecture

### Backend (FastAPI + Python)
- **Location**: `/backend/`
- **Main Entry**: `backend/src/main.py`
- **Port**: 8000 (development), automatic (production)
- **Database**: SQLite (dev), PostgreSQL (prod)

### Frontend (React + Vite)
- **Location**: `/frontend/`
- **Main Entry**: `frontend/src/App.jsx`
- **Port**: 5173 (development)
- **Build Output**: `frontend/dist/`

## Core Features

### 1. Multi-Agent AI System
Located in `backend/src/agents/`:

- **DiscoveryAgent** (`discovery_agent.py`): Discovers API endpoints from code/URLs
- **SpecGeneratorAgent** (`spec_agent.py`): Generates OpenAPI specifications
- **TestAgent** (`test_agent.py`): Creates and runs API tests
- **IntegrationAgent** (`integration_agent.py`): Handles API integrations
- **AIIntelligenceAgent** (`ai_agent.py`): Provides AI-powered analysis (security, performance, compliance)
- **MockServerAgent** (`mock_server_agent.py`): Generates mock servers from specs

### 2. Authentication System
- JWT-based authentication
- Located in `backend/src/auth.py`
- Features: Register, Login, Password Reset, Profile Management
- Demo credentials: `demo@example.com` / `Demo123!`

### 3. Subscription & Billing (Stripe)
- Located in `backend/src/billing.py`
- Tiers: Free, Starter ($19/mo), Professional ($49/mo), Enterprise ($99/mo)
- Stripe integration with webhooks
- Environment variables needed:
  ```
  STRIPE_SECRET_KEY=sk_live_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  STRIPE_PRICE_ID_STARTER=price_...
  STRIPE_PRICE_ID_PROFESSIONAL=price_...
  STRIPE_PRICE_ID_ENTERPRISE=price_...
  ```

### 4. WebSocket Real-time Updates
- Located in `backend/src/websocket_manager.py`
- Provides real-time orchestration progress
- Auto-reconnection logic in frontend

### 5. Project Management
- Located in `backend/src/projects.py`
- Organize APIs by projects
- Export/Import functionality

## Frontend Components

### Main Components
1. **Dashboard** (`frontend/src/components/Dashboard.jsx`)
   - Central hub with tabs for all features
   - Default tab: Orchestration

2. **OrchestrationHub** (`frontend/src/components/OrchestrationHub.jsx`)
   - Unified interface for all orchestration features
   - Tabs: URL Input, File Upload, Code Editor, GitHub Import

3. **CodeEditor** (`frontend/src/components/CodeEditor.jsx`)
   - Direct code input with syntax highlighting
   - Framework detection (FastAPI, Flask, Django)

4. **RealtimeMonitor** (`frontend/src/components/RealtimeMonitor.jsx`)
   - WebSocket-based real-time updates
   - Shows orchestration progress phases

5. **AIAnalysis** (`frontend/src/components/AIAnalysis.jsx`)
   - Displays AI-powered insights
   - Security scores, performance metrics, compliance checks

6. **MockServer** (`frontend/src/components/MockServer.jsx`)
   - Generate and manage mock servers
   - Start/stop controls with status monitoring

7. **UserProfile** (`frontend/src/components/UserProfile.jsx`)
   - Profile management
   - API key generation
   - Subscription management

## Deployment

### Production Environment (Railway)
- **URL**: https://streamapi.dev
- **Platform**: Railway
- **Database**: PostgreSQL (Railway-provided)
- **Docker Image**: ghcr.io/jonsnow1807/api-orchestrator:latest
- **Environment Variables** (set in Railway):
  ```
  DATABASE_URL=postgresql://...
  SECRET_KEY=your-secret-key-here
  ENVIRONMENT=production
  FRONTEND_URL=https://streamapi.dev
  BACKEND_URL=https://streamapi.dev
  STRIPE_SECRET_KEY=sk_live_...
  STRIPE_WEBHOOK_SECRET=whsec_...
  ANTHROPIC_API_KEY=sk-ant-...
  ```

### CI/CD Pipeline (GitHub Actions)
- **Location**: `.github/workflows/ci-cd-simple.yml`
- **Triggers**: Push to main/develop, Pull requests
- **Steps**:
  1. Run backend tests
  2. Build frontend
  3. Build and push Docker image to GitHub Container Registry
  4. Auto-deploys to Railway on main branch

### Docker Configuration
- **Dockerfile**: Multi-stage build
  - Stage 1: Build frontend
  - Stage 2: Setup backend with frontend static files
- **Image**: `ghcr.io/jonsnow1807/api-orchestrator:latest`

## Local Development Setup

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (Development)
Create `backend/.env`:
```
DATABASE_URL=sqlite:///./api_orchestrator.db
SECRET_KEY=your-dev-secret-key
ENVIRONMENT=development
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
ANTHROPIC_API_KEY=sk-ant-...
STRIPE_SECRET_KEY=sk_test_...
```

## Testing

### Unit Tests
```bash
cd backend
PYTHONPATH=. pytest tests/unit/ -v
```

### Integration Tests
```bash
cd backend
PYTHONPATH=. pytest tests/integration/ -v
```

### Production Testing
```bash
python test_production.py  # Tests streamapi.dev endpoints
```

## Project Structure
```
api-orchestrator/
├── backend/
│   ├── src/
│   │   ├── agents/          # AI agents
│   │   ├── auth.py          # Authentication
│   │   ├── billing.py       # Stripe integration
│   │   ├── database.py      # Database models
│   │   ├── main.py          # FastAPI app
│   │   ├── projects.py      # Project management
│   │   └── websocket_manager.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── Dockerfile
├── docker-compose.yml
└── .github/
    └── workflows/
        └── ci-cd-simple.yml
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /auth/refresh` - Refresh token
- `POST /auth/reset-password` - Password reset

### Orchestration
- `POST /api/orchestrate` - Start orchestration
- `GET /api/orchestration/{task_id}` - Get task status
- `POST /api/discover` - Discover APIs
- `POST /api/generate-spec` - Generate OpenAPI spec
- `POST /api/test` - Run tests
- `POST /api/mock-server` - Create mock server

### Billing
- `GET /api/billing/subscription` - Get subscription status
- `POST /api/billing/create-checkout-session` - Create Stripe checkout
- `POST /api/billing/cancel-subscription` - Cancel subscription
- `POST /webhook/stripe` - Stripe webhook endpoint

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

## WebSocket Events

### Client -> Server
```javascript
{
  "type": "auth",
  "token": "jwt_token_here"
}
```

### Server -> Client
```javascript
{
  "type": "orchestration_update",
  "task_id": "task_123",
  "phase": "discovery|generation|testing|integration",
  "status": "in_progress|completed|failed",
  "data": {...}
}
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

2. **Database Migration Issues**
   ```bash
   cd backend
   rm -f api_orchestrator.db
   python -c "from src.database import init_db; init_db()"
   ```

3. **Frontend Build Issues**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

4. **Docker Build Issues**
   - Ensure Docker daemon is running
   - Clear Docker cache: `docker system prune -a`

## Security Considerations

1. **API Keys**: Never commit to repository
2. **CORS**: Configured in `backend/src/main.py`
3. **Rate Limiting**: Implemented per user tier
4. **Input Validation**: All endpoints validate input
5. **SQL Injection**: Using SQLAlchemy ORM
6. **XSS Protection**: React handles escaping
7. **JWT Security**: Tokens expire after 24 hours

## Performance Optimization

1. **Database Indexes**: On user_id, project_id
2. **Caching**: Redis ready (not yet implemented)
3. **Async Operations**: All API endpoints are async
4. **Connection Pooling**: PostgreSQL in production
5. **Static File Serving**: Via FastAPI in production

## Monitoring & Logs

1. **Application Logs**: Structured JSON logging
2. **Error Tracking**: Console errors logged
3. **Health Check**: `/health` endpoint
4. **Metrics**: Basic metrics at `/metrics` (to be expanded)

## Future Enhancements (Planned)

1. **Team Collaboration**: Share projects with team members
2. **API Marketplace**: Share/sell API specs
3. **Advanced Testing**: Load testing, security scanning
4. **CI/CD Integration**: GitHub/GitLab webhooks
5. **API Versioning**: Track API changes over time
6. **Custom Domains**: For mock servers
7. **GraphQL Support**: Discovery and testing
8. **API Analytics**: Usage tracking and insights

## Support & Documentation

- **Production URL**: https://streamapi.dev
- **API Docs**: https://streamapi.dev/docs
- **GitHub**: https://github.com/JonSnow1807/api-orchestrator
- **Demo Login**: demo@example.com / Demo123!

## Quick Commands Reference

```bash
# Start development
cd backend && python -m uvicorn src.main:app --reload
cd frontend && npm run dev

# Run tests
cd backend && PYTHONPATH=. pytest tests/ -v

# Build Docker image
docker build -t api-orchestrator .

# Deploy to Railway
railway up

# Check production
curl https://streamapi.dev/health

# View logs
railway logs
```

## Contact & Maintenance

This platform was developed with Claude's assistance and is ready for production use. All core features are implemented and tested. The platform is currently live at streamapi.dev with Stripe payments fully integrated.

---

**Last Updated**: Current session
**Status**: ✅ Fully Operational
**Version**: 1.0.0