# API Orchestrator - Complete Knowledge Transfer Document

## Project Overview
**Product**: API Orchestrator v2.2.0 - Enterprise API Development Platform competing with Postman
**Status**: Production-ready, preparing for Y Combinator pitch
**Tech Stack**: 
- Frontend: React + Vite + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + SQLite
- Authentication: JWT with refresh tokens
- Payments: Stripe integration
- AI: Claude/OpenAI APIs
- Deployment: Railway (production), Local development

## Critical Information

### Demo Credentials
```
Email: demo@example.com
Password: Demo123!
```

### Stripe Keys (Test Mode Locally)
- Frontend: `pk_test_51S48yyPWjc2GvwDdJ6GJHdKYj1SKGCxVXhzzEYqvgq0BuECVzuq2OfrdlMOwRoqzhJmN0y1KXaM2XHO3COs2FNou00wBQ2bmOd`
- Backend: Configure in `.env` file
- Production (Railway): Uses live keys

### Running the Application
```bash
# Backend
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev
```

## Architecture Overview

### Backend Structure (`/backend/src/`)
```
src/
├── main.py                 # FastAPI app, routes, CORS, SPA handler
├── auth.py                 # JWT authentication, password hashing
├── database.py             # SQLAlchemy models, database connection
├── agents/
│   ├── discovery_agent.py  # API discovery from OpenAPI specs
│   ├── test_agent.py       # API testing automation
│   ├── mock_agent.py       # Mock server generation
│   └── ai_intelligence_agent.py # AI analysis (security, performance)
├── routes/
│   ├── webhooks.py         # Webhook management (currently disabled)
│   └── ai_keys.py          # AI API key management (currently disabled)
└── utils/
    └── logger.py           # Logging configuration
```

### Frontend Structure (`/frontend/src/`)
```
src/
├── components/
│   ├── Dashboard.jsx           # Main dashboard with project list
│   ├── ProjectDetails.jsx      # API testing interface
│   ├── OrchestrationHub.jsx    # Central orchestration panel
│   ├── CollectionsManager.jsx  # Request collections
│   ├── EnvironmentManager.jsx  # Environment variables
│   ├── GraphQLBuilder.jsx      # GraphQL query builder
│   ├── RequestHistory.jsx      # Request history tracking
│   ├── CodeGenerator/          # Enterprise code generation
│   ├── AIAssistant.jsx         # AI chat interface
│   ├── MockServerManager.jsx   # Mock server controls
│   ├── Billing.jsx             # Stripe billing page
│   ├── PricingPage.jsx         # Pricing tiers
│   ├── UserProfile.jsx         # User settings
│   └── WorkspaceSwitcherFixed.jsx # Workspace selector (Portal-based)
├── contexts/
│   └── AuthContext.jsx         # Authentication state management
└── App.jsx                      # Main app with routing
```

## Key Features Implemented

### 1. **Core API Testing** ✅
- REST API testing with all HTTP methods
- GraphQL support with schema introspection
- WebSocket testing and monitoring
- Request history and collections
- Environment variables management
- Response visualization with syntax highlighting

### 2. **AI-Powered Intelligence** ✅ (Unique Advantage)
- Security vulnerability detection with OWASP scanning
- Performance optimization recommendations
- Compliance checks (GDPR, HIPAA, SOC2, PCI-DSS)
- Executive summaries with business value estimation
- Rate limiting and caching suggestions

### 3. **Mock Server Generation** ✅ (Unique Advantage)
- Instant mock servers from OpenAPI specs
- Start/stop controls with status monitoring
- Endpoint visualization with response examples
- Automatic response generation

### 4. **Enterprise Code Generation** ✅ (Unique Advantage)
- Full SDK generation for multiple languages
- Type-safe client libraries
- Documentation generation
- Package publishing support
- Custom code templates

### 5. **Authentication & Authorization** ✅
- JWT with access/refresh tokens
- Email/password registration
- Protected routes
- Workspace management (partial)

### 6. **Billing & Subscriptions** ✅
- Stripe integration with checkout
- Subscription tiers (Free, Pro, Team, Enterprise)
- Usage tracking
- Webhook handling for payment events

### 7. **Real-time Features** ✅
- WebSocket connections for live updates
- Auto-reconnection logic
- Real-time API monitoring
- Live collaboration (partial)

## Critical Issues & Solutions Applied

### 1. **Authentication Crisis (Y Combinator Pitch)**
**Problem**: Login/registration completely broken before pitch
**Solution**: 
- Created `fix_auth.py` emergency script
- Fixed `api_calls_this_month` initialization
- Added demo account for quick access
- Fixed SQLAlchemy relationship issues

### 2. **Workspace Dropdown Z-Index Issue**
**Problem**: Dropdown hidden behind dashboard
**Solution**: Created `WorkspaceSwitcherFixed.jsx` using React Portals
```javascript
ReactDOM.createPortal(<dropdown/>, document.body)
```

### 3. **SPA Routing Issues**
**Problem**: Pricing page returning 404
**Solution**: Added catch-all route in FastAPI
```python
@app.get("/{path:path}")
async def serve_spa(path: str):
    # Serve index.html for non-API routes
```

### 4. **Theme Consistency**
**Problem**: Billing page had white cards (unprofessional)
**Solution**: Updated all components to dark theme (`bg-gray-800/50`)

### 5. **SQLAlchemy Relationship Errors**
**Problem**: Ambiguous foreign keys in Workspace model
**Temporary Solution**: Disabled webhooks/AI keys routes
**Proper Fix Needed**: Specify primaryjoin/foreignkeys in relationships

## Features Missing vs Postman

### Critical Gaps:
1. **Test Runner & Assertions** - No automated testing
2. **Pre/Post Request Scripts** - No dynamic scripting
3. **Newman CLI Equivalent** - No CI/CD integration
4. **Import Capabilities** - Can't import Postman collections
5. **Team Collaboration** - Limited sharing/permissions

### Already Better Than Postman:
1. **AI Intelligence** - Security/performance analysis
2. **Mock Servers** - Instant generation from specs
3. **Code Generation** - Full SDK creation
4. **Compliance Checks** - Built-in GDPR/HIPAA/SOC2
5. **Modern UI** - Cleaner, faster interface

## Database Schema

### Key Tables:
- **users**: Authentication, subscriptions
- **projects**: API projects with OpenAPI specs
- **api_endpoints**: Discovered endpoints
- **test_results**: Test execution history
- **collections**: Saved request collections
- **workspaces**: Team workspaces (partial)
- **webhook_endpoints**: Webhook configs (disabled)
- **ai_api_keys**: AI service keys (disabled)

## Environment Variables

### Backend (.env):
```
JWT_SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///./api_orchestrator.db
STRIPE_SECRET_KEY=sk_test_your_stripe_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

### Frontend (.env):
```
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Known Issues & TODOs

### High Priority:
1. **Re-enable Webhooks & AI Keys Routes** - Fix SQLAlchemy relationships
2. **Implement Test Runner** - Add assertions and test suites
3. **Add Postman Import** - Migration path for users
4. **Fix Performance** - Frontend bundle is 2.2MB

### Medium Priority:
1. Complete workspace functionality
2. Add team collaboration features
3. Implement CLI tool for CI/CD
4. Add pre/post request scripts

### Low Priority:
1. Add more import formats (HAR, cURL)
2. Implement scheduled monitoring
3. Add response validation
4. Enhance documentation generation

## Deployment

### Local Development:
```bash
# Start both servers
cd backend && uvicorn src.main:app --reload &
cd frontend && npm run dev
```

### Production (Railway):
- Auto-deploys from GitHub main branch
- Uses production Stripe keys
- PostgreSQL instead of SQLite
- Environment variables configured in Railway

## Testing the Application

### Key User Flows:
1. **Registration → Dashboard → Create Project**
2. **Import OpenAPI → Discover APIs → Test Endpoints**
3. **Generate Mock Server → Test Against Mock**
4. **Run AI Analysis → View Security Report**
5. **Create Collection → Save Requests → Share**
6. **Upgrade Plan → Stripe Checkout → Pro Features**

### Critical Components to Test:
- Authentication (login/register/refresh)
- API discovery from OpenAPI specs
- Request execution with environments
- Mock server generation
- AI analysis features
- Billing integration

## Business Context

### Target Users:
- Individual developers
- API development teams
- Enterprise engineering teams
- DevOps/QA engineers

### Competitive Position:
- Main competitor: Postman
- Unique value: AI-powered intelligence + code generation
- Price advantage: More features at lower cost
- Modern tech stack and UI

### Revenue Model:
- Freemium with usage limits
- Pro tier ($19/month)
- Team tier ($39/user/month)
- Enterprise (custom pricing)

## Support & Maintenance

### Common Issues:
1. **"Can't login"** → Check JWT tokens, run fix_auth.py
2. **"Dropdown hidden"** → Use WorkspaceSwitcherFixed component
3. **"404 on routes"** → Check SPA catch-all handler
4. **"White theme"** → Update to bg-gray-800/50
5. **"Stripe not working"** → Check webhook secret

### Debug Commands:
```python
# List all users
python fix_auth.py --list-users

# Reset password
python fix_auth.py --reset-password user@email.com

# Create admin
python fix_auth.py --create-admin admin@example.com
```

## Quick Wins for Next Session

1. **Enable Test Runner** (1 day)
   - Add assertions to request system
   - Create test suite runner
   - Add pass/fail reporting

2. **Import Postman Collections** (4 hours)
   - Parse Postman JSON format
   - Convert to internal format
   - Migration wizard UI

3. **Add CLI Tool** (1 day)
   - Create Python CLI package
   - Add to CI/CD pipelines
   - Publish to PyPI

4. **Fix Workspace Routes** (2 hours)
   - Fix SQLAlchemy relationships
   - Re-enable webhook routes
   - Re-enable AI keys routes

## Contact & Resources

- Production: https://streamapi.dev (Railway)
- Repository: [GitHub - API Orchestrator]
- Support: sales@streamapi.dev
- Documentation: Built-in API docs at /docs

## Final Notes

The application is production-ready with some known issues. The Y Combinator pitch was saved by emergency fixes. The product has unique AI advantages over Postman but needs test automation features for complete parity. The codebase is well-structured with clear separation of concerns. Focus on test runner and import capabilities to remove adoption barriers.

---
*Last Updated: During Y Combinator pitch preparation*
*Critical Context: User was stressed about pitch, needed immediate fixes*
*Status: All critical issues resolved, product demo-ready*