# StreamAPI (API Orchestrator) 🚀

> Transform any codebase into production-ready APIs with AI-powered automation

**Live at: [https://streamapi.dev](https://streamapi.dev)**

An intelligent SaaS platform that automatically discovers, documents, tests, and manages APIs. Transform your codebase into production-ready APIs with comprehensive documentation and test suites in minutes.

![CI/CD Pipeline](https://github.com/JonSnow1807/api-orchestrator/actions/workflows/ci-cd.yml/badge.svg)
![Auto Deploy](https://github.com/JonSnow1807/api-orchestrator/actions/workflows/auto-deploy.yml/badge.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Node](https://img.shields.io/badge/node-20%2B-green)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 Features

### Core Capabilities
- **🔍 Automatic API Discovery** - Scans codebases to identify API endpoints across FastAPI, Flask, Express, Django, and more
- **📄 OpenAPI Specification Generation** - Creates comprehensive OpenAPI 3.0 specifications
- **🧪 Multi-Framework Test Generation** - Generates tests for pytest, Jest, Mocha, and Postman
- **🎭 Instant Mock Servers** - Creates deployable mock servers with realistic data
- **🤖 AI-Powered Analysis** - Security scanning, performance optimization, and compliance checking using Claude AI
- **⚡ Real-Time Processing** - WebSocket-based live updates during orchestration
- **💼 Business Value Analytics** - Calculates time saved, cost reduction, and ROI metrics

### Production Features (v2.0.0)
- **💳 Stripe Billing Integration** - Production-ready payment processing with 4 subscription tiers
- **📧 Email System** - Password reset and transactional emails via SMTP
- **🔍 Error Tracking** - Sentry integration for real-time error monitoring
- **🔐 Enterprise Security** - JWT authentication, bcrypt hashing, CORS protection
- **🗄️ PostgreSQL Support** - Production database with automatic migrations
- **📊 User Dashboard** - Profile management, API keys, usage statistics
- **🔄 Export/Import** - Support for JSON, YAML, OpenAPI, Postman formats
- **🚀 Auto-scaling** - Deployed on Railway with automatic scaling

## 💰 Pricing Tiers

| Feature | Free | Starter ($49/mo) | Professional ($149/mo) | Enterprise ($499/mo) |
|---------|------|------------------|------------------------|---------------------|
| API Calls | 1,000/month | 10,000/month | 100,000/month | Unlimited |
| Projects | 3 | 10 | 50 | Unlimited |
| Team Members | 1 | 3 | 10 | Unlimited |
| AI Analysis | ❌ | ✅ | ✅ | ✅ |
| Mock Servers | ❌ | ✅ | ✅ | ✅ |
| Export Formats | JSON only | JSON, YAML | All formats | All formats |
| Support | Community | Email | Priority | Dedicated |
| Custom Models | ❌ | ❌ | ❌ | ✅ |
| SSO/SAML | ❌ | ❌ | ❌ | ✅ |

## 🏗️ Technical Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.11), SQLAlchemy, Pydantic
- **Frontend**: React 18, Vite, TailwindCSS, Lucide Icons
- **Database**: PostgreSQL (production) / SQLite (development)
- **AI**: Anthropic Claude API, OpenAI GPT-4 (optional)
- **Payments**: Stripe Checkout & Webhooks
- **Deployment**: Railway, Docker, GitHub Actions
- **Monitoring**: Sentry, Custom Analytics

### Multi-Agent System
1. **Discovery Agent** - Scans and identifies API endpoints
2. **Spec Generator Agent** - Creates OpenAPI specifications
3. **Test Generator Agent** - Produces comprehensive test suites
4. **AI Intelligence Agent** - Security & performance analysis
5. **Mock Server Agent** - Generates functional mock servers

## 🚀 Quick Start

### Use the Live Platform
Visit [https://streamapi.dev](https://streamapi.dev) to start using StreamAPI immediately.

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/JonSnow1807/api-orchestrator.git
cd api-orchestrator

# Backend setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configurations

# Initialize database
python -c "from backend.src.database import init_db; init_db()"

# Start backend
cd backend
python -m uvicorn src.main:app --reload

# In a new terminal - Frontend setup
cd frontend
npm install
npm run dev
```

Access the application at `http://localhost:5173`

## 🐳 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or use the pre-built image
docker run -p 8000:8000 \
  -e DATABASE_URL=your_database_url \
  -e STRIPE_SECRET_KEY=your_stripe_key \
  ghcr.io/jonsnow1807/api-orchestrator:latest
```

## 🌐 Production Deployment

### Railway (Recommended)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

### Environment Variables Required
```env
# Core
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=your-secure-key

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_STARTER_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_ENTERPRISE_PRICE_ID=price_...

# Email (Optional)
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-app-password

# Monitoring (Optional)
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production

# AI Features (Optional)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
```

## 📊 API Usage Examples

### Discover APIs in Your Codebase
```python
import requests

# Authenticate
response = requests.post("https://streamapi.dev/auth/login", 
    data={"username": "your-email", "password": "your-password"})
token = response.json()["access_token"]

# Start orchestration
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("https://streamapi.dev/api/orchestrate",
    json={
        "source_type": "code",
        "source_path": "https://github.com/your-repo",
        "code_content": "your_code_here"
    },
    headers=headers
)

task_id = response.json()["task_id"]
print(f"Task started: {task_id}")
```

### Generate Mock Server
```python
# After orchestration completes
response = requests.post(f"https://streamapi.dev/api/mock-server/{task_id}/start",
    headers=headers)
    
mock_url = response.json()["url"]
print(f"Mock server running at: {mock_url}")
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Test specific component
pytest tests/unit/test_discovery_agent.py

# Integration tests
pytest tests/integration/ -v

# Test Stripe integration
python test_complete_stripe_flow.py
```

## 📈 Performance Metrics

- **Processing Speed**: 100+ endpoints in under 30 seconds
- **Test Generation**: Complete test suite in 2-3 minutes
- **Mock Server Startup**: < 5 seconds
- **WebSocket Latency**: < 100ms
- **Concurrent Users**: 1000+ supported
- **API Rate Limits**: Configurable per tier

## 🔒 Security Features

- **Authentication**: JWT with refresh tokens
- **Password Security**: Bcrypt hashing with salt
- **API Rate Limiting**: Per-user and per-tier limits
- **CORS Protection**: Configurable origins
- **Input Validation**: Pydantic models
- **SQL Injection Protection**: SQLAlchemy ORM
- **XSS Prevention**: React's built-in escaping
- **HTTPS Only**: Enforced in production
- **Webhook Validation**: Stripe signature verification

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest tests/`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with FastAPI, React, and SQLAlchemy
- AI capabilities powered by Anthropic Claude
- Payment processing by Stripe
- Deployed on Railway
- Error tracking by Sentry

## 📞 Support

For issues, questions, or enterprise inquiries:
- **GitHub Issues**: [Create an issue](https://github.com/JonSnow1807/api-orchestrator/issues)
- **Email**: cshrivastava2000@gmail.com
- **Documentation**: [https://streamapi.dev/docs](https://streamapi.dev/docs)

## 🛣️ Roadmap

### Coming Soon
- [ ] Team collaboration features
- [ ] GitHub/GitLab integration
- [ ] Custom AI model training
- [ ] Kubernetes deployment support
- [ ] GraphQL support
- [ ] API versioning
- [ ] Advanced analytics dashboard
- [ ] Slack/Discord notifications
- [ ] CI/CD pipeline templates
- [ ] Multi-region deployment

## 📊 Status

- **Production URL**: [https://streamapi.dev](https://streamapi.dev)
- **API Status**: ✅ Operational
- **Database**: ✅ PostgreSQL on Railway
- **Payments**: ✅ Stripe Integration Active
- **Email**: ✅ SMTP Configured
- **Monitoring**: ✅ Sentry Active
- **SSL**: ✅ HTTPS Enabled

## 👨‍💻 Author

**Chinmay Shrivastava**
- GitHub: [@JonSnow1807](https://github.com/JonSnow1807)
- Email: cshrivastava2000@gmail.com
- LinkedIn: [Connect on LinkedIn](https://linkedin.com/in/chinmayshrivastava)

---

**Built with ❤️ for developers who value their time**

*Transform your APIs from concept to production in minutes, not months.*