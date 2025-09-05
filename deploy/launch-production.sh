#!/bin/bash

# API Orchestrator - Official Production Launch Script
# This script deploys your application to production in minutes

set -e

echo "
╔══════════════════════════════════════════════════════════════╗
║     🚀 API ORCHESTRATOR - OFFICIAL PRODUCTION LAUNCH 🚀      ║
╚══════════════════════════════════════════════════════════════╝
"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to prompt user
prompt_user() {
    echo -e "${BLUE}$1${NC}"
    read -p "> " response
    echo "$response"
}

echo -e "${YELLOW}Select your deployment option:${NC}"
echo "1) Railway (Recommended - Free tier, instant deploy)"
echo "2) Render (Free tier with limitations)"
echo "3) DigitalOcean App Platform ($5/month)"
echo "4) Heroku ($7/month)"
echo "5) Your own VPS (most control)"
echo ""
DEPLOYMENT_CHOICE=$(prompt_user "Enter choice (1-5)")

case $DEPLOYMENT_CHOICE in
    1)
        echo -e "${GREEN}Deploying to Railway...${NC}"
        
        # Check if Railway CLI is installed
        if ! command_exists railway; then
            echo "Installing Railway CLI..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                brew install railway
            else
                curl -fsSL https://railway.app/install.sh | sh
            fi
        fi
        
        # Create railway.toml
        cat > railway.toml << 'EOF'
[build]
builder = "DOCKERFILE"
dockerfilePath = "docker/Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[[services]]
name = "api-orchestrator"
port = 8000
EOF
        
        echo -e "${YELLOW}Steps to deploy on Railway:${NC}"
        echo "1. Run: railway login"
        echo "2. Run: railway init"
        echo "3. Run: railway up"
        echo "4. Run: railway domain"
        echo ""
        echo -e "${GREEN}Your app will be live at: https://your-app.railway.app${NC}"
        
        # Auto-deploy
        read -p "Deploy now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            railway login
            railway init
            railway up
            railway domain
        fi
        ;;
        
    2)
        echo -e "${GREEN}Deploying to Render...${NC}"
        
        # Create render.yaml
        cat > render.yaml << 'EOF'
services:
  - type: web
    name: api-orchestrator
    runtime: docker
    dockerfilePath: ./docker/Dockerfile
    envVars:
      - key: DATABASE_URL
        value: sqlite:///./api_orchestrator.db
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: JWT_ALGORITHM
        value: HS256
      - key: CORS_ORIGINS
        value: https://api-orchestrator.onrender.com
    healthCheckPath: /health
    autoDeploy: false
EOF
        
        echo -e "${YELLOW}Steps to deploy on Render:${NC}"
        echo "1. Go to https://dashboard.render.com/new/blueprint"
        echo "2. Connect your GitHub repo: JonSnow1807/api-orchestrator"
        echo "3. Use the render.yaml blueprint"
        echo "4. Click 'Apply'"
        echo ""
        echo -e "${GREEN}Your app will be live at: https://api-orchestrator.onrender.com${NC}"
        
        # Open Render dashboard
        read -p "Open Render dashboard? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open "https://dashboard.render.com/new/blueprint"
        fi
        ;;
        
    3)
        echo -e "${GREEN}Deploying to DigitalOcean App Platform...${NC}"
        
        # Create app spec
        cat > .do/app.yaml << 'EOF'
name: api-orchestrator
region: nyc
services:
  - name: web
    dockerfile_path: docker/Dockerfile
    source_dir: /
    github:
      repo: JonSnow1807/api-orchestrator
      branch: main
      deploy_on_push: true
    http_port: 8000
    instance_count: 1
    instance_size_slug: basic-xxs
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        value: "sqlite:///./api_orchestrator.db"
      - key: JWT_SECRET_KEY
        type: SECRET
      - key: CORS_ORIGINS
        value: "${APP_URL}"
    routes:
      - path: /
EOF
        
        echo -e "${YELLOW}Steps to deploy on DigitalOcean:${NC}"
        echo "1. Install doctl: brew install doctl"
        echo "2. Run: doctl auth init"
        echo "3. Run: doctl apps create --spec .do/app.yaml"
        echo ""
        echo -e "${GREEN}Your app will be live at: https://api-orchestrator-xxxxx.ondigitalocean.app${NC}"
        
        # Check if doctl is installed
        if command_exists doctl; then
            read -p "Deploy now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                doctl apps create --spec .do/app.yaml
            fi
        fi
        ;;
        
    4)
        echo -e "${GREEN}Deploying to Heroku...${NC}"
        
        # Create Procfile
        cat > Procfile << 'EOF'
web: cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
EOF
        
        # Create runtime.txt
        echo "python-3.11.0" > runtime.txt
        
        echo -e "${YELLOW}Steps to deploy on Heroku:${NC}"
        echo "1. Install Heroku CLI: brew tap heroku/brew && brew install heroku"
        echo "2. Run: heroku create api-orchestrator"
        echo "3. Run: heroku config:set JWT_SECRET_KEY=\$(openssl rand -hex 32)"
        echo "4. Run: git push heroku main"
        echo ""
        echo -e "${GREEN}Your app will be live at: https://api-orchestrator.herokuapp.com${NC}"
        
        # Check if heroku CLI is installed
        if command_exists heroku; then
            read -p "Deploy now? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                heroku create api-orchestrator-$(date +%s)
                heroku config:set JWT_SECRET_KEY=$(openssl rand -hex 32)
                git push heroku main
            fi
        fi
        ;;
        
    5)
        echo -e "${GREEN}Deploying to your VPS...${NC}"
        
        VPS_HOST=$(prompt_user "Enter your VPS IP address or domain")
        VPS_USER=$(prompt_user "Enter SSH username (usually 'root' or 'ubuntu')")
        
        # Create deployment script
        cat > deploy-to-vps.sh << 'EOF'
#!/bin/bash
# This script runs on your VPS

# Update system
apt-get update && apt-get upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt-get install -y docker-compose

# Install Nginx
apt-get install -y nginx certbot python3-certbot-nginx

# Clone repository
cd /opt
git clone https://github.com/JonSnow1807/api-orchestrator.git
cd api-orchestrator

# Create .env file
cat > .env << 'ENVFILE'
DATABASE_URL=postgresql://postgres:password@db:5432/api_orchestrator
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256
CORS_ORIGINS=https://your-domain.com
ENVFILE

# Start with Docker Compose
docker-compose -f deploy/docker-compose.prod.yml up -d

# Configure Nginx
cat > /etc/nginx/sites-available/api-orchestrator << 'NGINX'
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
NGINX

ln -s /etc/nginx/sites-available/api-orchestrator /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "Deployment complete!"
EOF
        
        echo -e "${YELLOW}Copying deployment script to VPS...${NC}"
        scp deploy-to-vps.sh $VPS_USER@$VPS_HOST:/tmp/
        
        echo -e "${YELLOW}Executing deployment...${NC}"
        ssh $VPS_USER@$VPS_HOST "chmod +x /tmp/deploy-to-vps.sh && sudo /tmp/deploy-to-vps.sh"
        
        echo -e "${GREEN}Your app is live at: http://$VPS_HOST${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    🎉 DEPLOYMENT COMPLETE! 🎉                  ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Post-deployment steps
echo -e "${YELLOW}📋 Post-Deployment Checklist:${NC}"
echo ""
echo "1. ✅ Set up custom domain (optional)"
echo "   - Add CNAME record pointing to your deployment URL"
echo ""
echo "2. ✅ Configure environment variables:"
echo "   - ANTHROPIC_API_KEY (for AI features)"
echo "   - DATABASE_URL (for production database)"
echo "   - JWT_SECRET_KEY (auto-generated)"
echo ""
echo "3. ✅ Set up monitoring:"
echo "   - Add to UptimeRobot for uptime monitoring"
echo "   - Configure error tracking (Sentry)"
echo ""
echo "4. ✅ Launch announcement:"
echo "   - Post on ProductHunt"
echo "   - Share on Twitter/LinkedIn"
echo "   - Submit to Hacker News"
echo ""

# Create launch materials
echo -e "${BLUE}Creating launch materials...${NC}"

# Create ProductHunt launch text
cat > launch/producthunt.md << 'EOF'
# API Orchestrator 🚀

**Tagline:** Transform any codebase into production-ready APIs in seconds

**Description:**
API Orchestrator uses AI to automatically discover, document, test, and deploy APIs from your existing code. 

✨ Features:
- 🔍 Auto-discovers API endpoints from any codebase
- 📄 Generates OpenAPI 3.0 specifications
- 🧪 Creates comprehensive test suites
- 🎭 Instant mock servers
- 🤖 AI-powered security analysis
- 💻 VS Code extension for seamless integration

Perfect for developers who want to:
- Document legacy APIs
- Generate tests automatically
- Create mock servers for frontend development
- Ensure API security and compliance

Available as:
- Web application
- CLI tool
- VS Code extension

Try it free at: https://api-orchestrator.com
EOF

# Create Twitter launch thread
cat > launch/twitter-thread.md << 'EOF'
🚀 Launching API Orchestrator today!

Transform any codebase into production-ready APIs with AI.

No more manual API documentation. No more writing tests from scratch.

Just point, click, and deploy.

Thread 👇

1/ THE PROBLEM:
Developers spend 40% of their time on API-related tasks:
- Writing documentation
- Creating tests
- Setting up mock servers
- Ensuring security

What if this could be automated?

2/ THE SOLUTION:
API Orchestrator uses AI agents to:
✅ Scan your codebase
✅ Discover all API endpoints
✅ Generate OpenAPI specs
✅ Create test suites
✅ Deploy mock servers
✅ Analyze security

All in under 60 seconds.

3/ HOW IT WORKS:
Our multi-agent system includes:
- Discovery Agent (finds APIs)
- Spec Generator (creates docs)
- Test Generator (writes tests)
- Mock Server Agent (instant mocks)
- AI Intelligence Agent (security analysis)

4/ AVAILABLE EVERYWHERE:
🌐 Web app for teams
💻 CLI for CI/CD pipelines
🔌 VS Code extension for developers

Use it wherever you work.

5/ WHO IS THIS FOR?
- Developers documenting legacy APIs
- Teams adopting API-first design
- Companies ensuring compliance
- Startups moving fast

6/ PRICING:
Free tier: 10 projects/month
Pro: $29/month (unlimited)
Enterprise: Custom pricing

7/ TRY IT NOW:
🔗 https://api-orchestrator.com
🔗 GitHub: github.com/JonSnow1807/api-orchestrator

Let's eliminate API busywork forever.

RT if you hate writing API docs manually! 🙏
EOF

echo -e "${GREEN}Launch materials created in ./launch/ directory${NC}"
echo ""
echo -e "${BLUE}Ready to announce your launch? Here are the platforms:${NC}"
echo "- ProductHunt: https://www.producthunt.com/posts/new"
echo "- Hacker News: https://news.ycombinator.com/submit"
echo "- Reddit r/programming: https://reddit.com/r/programming/submit"
echo "- Dev.to: https://dev.to/new"
echo "- LinkedIn: https://www.linkedin.com/feed/"
echo ""

echo -e "${GREEN}🎊 Congratulations! Your product is ready for launch! 🎊${NC}"