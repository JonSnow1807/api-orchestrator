# API Orchestrator 🚀

> Transform any codebase into production-ready APIs with AI-powered automation

An intelligent multi-agent system that automatically discovers, documents, tests, and manages APIs. Transform your codebase into production-ready APIs with comprehensive documentation and test suites in minutes.

![CI/CD Pipeline](https://github.com/JonSnow1807/api-orchestrator/actions/workflows/ci-cd.yml/badge.svg)
![Auto Deploy](https://github.com/JonSnow1807/api-orchestrator/actions/workflows/auto-deploy.yml/badge.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Node](https://img.shields.io/badge/node-20%2B-green)
![Tests](https://img.shields.io/badge/tests-97%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-48%25-yellow)
![License](https://img.shields.io/badge/license-MIT-green)

## 🚀 Features

### Core Capabilities
- **Automatic API Discovery** - Scans codebases to identify API endpoints across FastAPI, Flask, Express, and Django
- **OpenAPI Specification Generation** - Creates comprehensive OpenAPI 3.0 specifications
- **Multi-Framework Test Generation** - Generates tests for pytest, Jest, Mocha, and Postman
- **Instant Mock Servers** - Creates deployable mock servers with realistic data
- **AI-Powered Analysis** - Security scanning and optimization recommendations using Claude AI
- **Real-Time Processing** - WebSocket-based live updates during orchestration
- **Business Value Analytics** - Calculates time saved, cost reduction, and ROI metrics

### New Features (v1.0.0)
- **💳 Usage-Based Billing** - Stripe integration with 4 subscription tiers
- **CLI Tool** - Command-line interface for CI/CD integration
- **VS Code Extension** - Direct IDE integration with real-time API discovery
- **Enhanced Dashboard** - Statistics, task management, file upload, export/import
- **Password Reset** - Secure password recovery system
- **User Profiles** - Account management with API keys and usage tracking
- **Team Collaboration** - Project sharing and team workspaces (coming soon)

### Technical Architecture
- **Multi-Agent System** - Five specialized agents working in coordination
- **Modern Tech Stack** - FastAPI backend, React frontend, SQLAlchemy ORM
- **Secure Authentication** - JWT-based auth with subscription tier support
- **Export/Import Support** - JSON, YAML, Markdown, and ZIP formats
- **Database Persistence** - SQLite/PostgreSQL compatible data layer
- **WebSocket Integration** - Real-time updates and progress tracking

## 📁 Project Structure

```
api-orchestrator/
├── backend/
│   └── src/
│       ├── agents/              # Multi-agent orchestration system
│       │   ├── discovery_agent.py
│       │   ├── spec_agent.py
│       │   ├── test_agent.py
│       │   ├── ai_agent.py
│       │   └── mock_server_agent.py
│       ├── core/
│       │   ├── orchestrator.py  # Agent coordination
│       │   └── config.py
│       ├── main.py              # FastAPI server
│       ├── database.py          # SQLAlchemy models
│       ├── auth.py              # JWT authentication
│       └── export_import.py     # Export/Import functionality
├── frontend/
│   └── src/
│       ├── components/          # React components
│       ├── pages/              # Application pages
│       ├── contexts/           # React contexts
│       └── services/           # API services
├── cli/                        # Command-line interface
│   ├── api-orchestrator.py
│   └── setup.py
├── vscode-extension/           # VS Code extension
│   ├── src/
│   └── package.json
├── deploy/                     # Deployment scripts
│   ├── one-click-deploy.sh
│   ├── aws-production-deploy.sh
│   └── docker-compose.prod.yml
├── mock_servers/               # Generated mock servers
└── output/                     # Generated artifacts
```

## 🛠️ Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 20 or higher
- Git

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/JonSnow1807/api-orchestrator.git
cd api-orchestrator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies
pip install "python-jose[cryptography]" passlib python-multipart bcrypt

# Initialize database
python -c "from src.database import init_db; init_db()"

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:${PWD}"
export ANTHROPIC_API_KEY="your-api-key"  # Optional for AI features
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🚀 Deployment

### One-Click Deployment

```bash
# Run the automated deployment wizard
chmod +x deploy/one-click-deploy.sh
./deploy/one-click-deploy.sh
```

Supports deployment to:
- **Railway** (FREE tier available - Recommended for starters)
- **Render** (FREE tier with auto-sleep)
- **DigitalOcean** ($6/month)
- **AWS ECS Fargate** (Production-grade, ~$150/month)
- **Heroku** ($7/month)
- **Docker** (Local deployment)

### Low-Budget Options

For FREE hosting:
```bash
# Deploy to Railway (best free option)
cd deploy
./launch-production.sh
# Choose option 1
```

### Production Deployment

```bash
# Using Docker Compose
docker-compose -f deploy/docker-compose.prod.yml up -d

# Or deploy to your VPS
DOMAIN=yourdomain.com ./deploy/deploy.sh
```

### CI/CD Pipeline

The repository includes automated CI/CD:
- Automatic testing on every push
- Docker image building and pushing to GitHub Container Registry
- Automated deployment to production on main branch merge
- Multi-environment support (production, staging, development)

See [deployment documentation](deploy/README.md) for detailed instructions.

## 💻 Development Usage

### Start the Application

```bash
# Terminal 1: Start backend
cd api-orchestrator
python -m src.main

# Terminal 2: Start frontend
cd api-orchestrator/frontend
npm run dev
```

Access the application at `http://localhost:5173`

### Quick Start Guide

1. **Register/Login** - Create an account or login
2. **Navigate to Orchestrate** - Click "Orchestrate" in the sidebar
3. **Enter Source Path** - Specify the directory containing your code
4. **Start Orchestration** - Click "Start Orchestration" button
5. **View Results** - Watch real-time progress and download artifacts

### Supported Frameworks

The system automatically detects and processes:
- **Python**: FastAPI, Flask, Django
- **JavaScript/TypeScript**: Express.js
- More frameworks coming soon

## 📊 Generated Artifacts

### OpenAPI Specification
Complete API documentation following OpenAPI 3.0 standards with:
- Endpoint definitions
- Request/response schemas
- Authentication requirements
- Parameter specifications

### Test Suites
Comprehensive test coverage including:
- **Unit Tests** - pytest, unittest for Python; Jest, Mocha for JavaScript
- **Integration Tests** - End-to-end workflow testing
- **Load Tests** - Locust scripts for performance testing
- **API Collections** - Postman collections for manual testing

### Mock Servers
Fully functional mock servers with:
- Realistic data generation using Faker
- Configurable response delays
- Error simulation
- Docker support
- Stateful operations

## 💰 Business Value Metrics

The system calculates and displays:
- **Hours Saved** - Time reduction in API development
- **Cost Savings** - Monetary value based on developer hourly rates
- **ROI** - Return on investment calculations
- **Time to Market** - Acceleration in deployment timeline

## 🔧 Configuration

### Database Configuration
```python
# Default: SQLite
DATABASE_URL = "sqlite:///./api_orchestrator.db"

# PostgreSQL (optional)
DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

### Authentication Settings
```python
SECRET_KEY = "your-secret-key"  # Change in production
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

## 🧪 Testing

```bash
# Run backend tests
pytest tests/

# Test API discovery
python test_real_ai.py

# Test authentication
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "testpass123"}'
```

## 📈 Performance

- Processes 100+ endpoints in under 30 seconds
- Generates comprehensive test suites in minutes
- Real-time WebSocket updates with minimal latency
- Supports concurrent orchestration tasks

## 🔒 Security

- JWT-based authentication
- Bcrypt password hashing
- CORS protection
- Input validation and sanitization
- Rate limiting ready

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI, React, and SQLAlchemy
- AI capabilities powered by Anthropic Claude
- Inspired by modern API development workflows

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Email: cshrivastava2000@gmail.com

## 🛠️ Available Tools

### CLI Tool
```bash
cd cli
pip install -e .
api-orchestrator scan ./my-project
api-orchestrator mock ./openapi.json --port 3000
```

### VS Code Extension
- Scan projects with `Cmd/Ctrl+Shift+A`
- View discovered APIs in sidebar
- Generate specs and tests directly from IDE
- Real-time WebSocket updates

### Web Dashboard
- Project management
- Real-time orchestration
- Statistics and analytics
- Team collaboration (coming soon)

## 👨‍💻 Author

**Chinmay Shrivastava**
- GitHub: [@JonSnow1807](https://github.com/JonSnow1807)
- Email: cshrivastava2000@gmail.com

---

**Built with ❤️ by Chinmay Shrivastava for developers who value their time**
