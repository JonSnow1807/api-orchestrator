#!/bin/bash
# One-click deployment script for API Orchestrator
# Supports: DigitalOcean, AWS EC2, Google Cloud, Azure, Linode, Vultr

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}
╔═══════════════════════════════════════════════╗
║                                               ║
║     🚀 API ORCHESTRATOR AUTO-DEPLOY 🚀        ║
║                                               ║
║     One-Click Cloud Deployment Script         ║
║                                               ║
╚═══════════════════════════════════════════════╝
${NC}"

# Function to display menu
show_menu() {
    echo -e "${YELLOW}Select your deployment platform:${NC}"
    echo ""
    echo "  1) DigitalOcean Droplet"
    echo "  2) AWS EC2"
    echo "  3) Google Cloud Platform"
    echo "  4) Microsoft Azure"
    echo "  5) Linode"
    echo "  6) Vultr"
    echo "  7) Railway (Easiest - No server needed)"
    echo "  8) Render (Free tier available)"
    echo "  9) Fly.io"
    echo "  10) Local Docker"
    echo ""
    read -p "Enter choice [1-10]: " choice
}

# Function to deploy to DigitalOcean
deploy_digitalocean() {
    echo -e "${BLUE}Deploying to DigitalOcean...${NC}"
    
    # Check for doctl
    if ! command -v doctl &> /dev/null; then
        echo "Installing DigitalOcean CLI..."
        brew install doctl || sudo snap install doctl
    fi
    
    # Authenticate
    echo "Please authenticate with DigitalOcean:"
    doctl auth init
    
    # Create droplet
    echo "Creating Droplet..."
    DROPLET_ID=$(doctl compute droplet create api-orchestrator \
        --image docker-20-04 \
        --size s-2vcpu-4gb \
        --region nyc1 \
        --ssh-keys $(doctl compute ssh-key list --format ID --no-header | head -n1) \
        --user-data-file ./deploy/cloud-init.yml \
        --wait \
        --format ID \
        --no-header)
    
    # Get IP address
    IP=$(doctl compute droplet get $DROPLET_ID --format PublicIPv4 --no-header)
    
    echo -e "${GREEN}✅ Droplet created at: ${IP}${NC}"
    
    # Wait for initialization
    echo "Waiting for server initialization..."
    sleep 60
    
    # Deploy application
    ssh root@$IP "bash -s" < ./deploy/deploy.sh
    
    echo -e "${GREEN}✅ Application deployed at http://${IP}${NC}"
}

# Function to deploy to AWS EC2
deploy_aws() {
    echo -e "${BLUE}Deploying to AWS EC2...${NC}"
    
    # Check for AWS CLI
    if ! command -v aws &> /dev/null; then
        echo "Please install AWS CLI first:"
        echo "pip install awscli"
        exit 1
    fi
    
    # Create EC2 instance
    echo "Creating EC2 instance..."
    
    # Create key pair
    aws ec2 create-key-pair --key-name api-orchestrator --query 'KeyMaterial' --output text > api-orchestrator.pem
    chmod 400 api-orchestrator.pem
    
    # Launch instance
    INSTANCE_ID=$(aws ec2 run-instances \
        --image-id ami-0c94855ba95c574c8 \
        --instance-type t3.medium \
        --key-name api-orchestrator \
        --security-group-ids $(aws ec2 create-security-group \
            --group-name api-orchestrator \
            --description "API Orchestrator Security Group" \
            --output text) \
        --user-data file://./deploy/cloud-init.yml \
        --output text \
        --query 'Instances[0].InstanceId')
    
    # Wait for instance
    aws ec2 wait instance-running --instance-ids $INSTANCE_ID
    
    # Get public IP
    IP=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    echo -e "${GREEN}✅ EC2 instance created at: ${IP}${NC}"
    
    # Deploy application
    sleep 60
    ssh -i api-orchestrator.pem ubuntu@$IP "bash -s" < ./deploy/deploy.sh
    
    echo -e "${GREEN}✅ Application deployed at http://${IP}${NC}"
}

# Function to deploy to Railway (Easiest)
deploy_railway() {
    echo -e "${BLUE}Deploying to Railway (Easiest option)...${NC}"
    
    # Install Railway CLI
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    # Login to Railway
    echo "Logging into Railway..."
    railway login
    
    # Create new project
    railway init
    
    # Add PostgreSQL
    railway add postgresql
    
    # Add Redis
    railway add redis
    
    # Deploy
    railway up
    
    # Get URL
    URL=$(railway open --url)
    
    echo -e "${GREEN}✅ Application deployed at ${URL}${NC}"
}

# Function to deploy to Render
deploy_render() {
    echo -e "${BLUE}Deploying to Render...${NC}"
    
    # Create render.yaml
    cat > render.yaml << 'EOF'
services:
  - type: web
    name: api-orchestrator
    env: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: api-orchestrator-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: api-orchestrator-redis
          property: connectionString

databases:
  - name: api-orchestrator-db
    plan: starter

services:
  - type: redis
    name: api-orchestrator-redis
    plan: starter
EOF
    
    echo "Please:"
    echo "1. Create account at https://render.com"
    echo "2. Connect your GitHub repository"
    echo "3. Create new Blueprint"
    echo "4. Select this repository"
    echo ""
    echo "Render will automatically deploy your application!"
    
    open https://dashboard.render.com/blueprints
}

# Function to deploy locally with Docker
deploy_local() {
    echo -e "${BLUE}Deploying locally with Docker...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
    fi
    
    # Build and run
    docker-compose up -d --build
    
    echo -e "${GREEN}✅ Application running at http://localhost:8000${NC}"
}

# Function to setup GitHub Secrets for CI/CD
setup_github_secrets() {
    echo -e "${YELLOW}Setting up GitHub Secrets...${NC}"
    
    # Install GitHub CLI if needed
    if ! command -v gh &> /dev/null; then
        echo "Installing GitHub CLI..."
        brew install gh || sudo apt install gh
    fi
    
    # Authenticate
    gh auth login
    
    # Set secrets based on deployment choice
    case $1 in
        1) # DigitalOcean
            gh secret set DO_TOKEN
            gh secret set VPS_HOST
            gh secret set VPS_USER
            gh secret set VPS_SSH_KEY
            ;;
        2) # AWS
            gh secret set AWS_ACCESS_KEY_ID
            gh secret set AWS_SECRET_ACCESS_KEY
            gh secret set AWS_REGION
            ;;
        7) # Railway
            gh secret set RAILWAY_TOKEN
            ;;
        8) # Render
            gh secret set RENDER_DEPLOY_HOOK
            ;;
    esac
    
    # Common secrets
    gh secret set ANTHROPIC_API_KEY
    gh secret set SECRET_KEY
    
    echo -e "${GREEN}✅ GitHub Secrets configured${NC}"
}

# Function to create cloud-init script
create_cloud_init() {
    cat > ./deploy/cloud-init.yml << 'EOF'
#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose
  - git
  - nginx
  - certbot
  - python3-certbot-nginx

runcmd:
  - systemctl start docker
  - systemctl enable docker
  - git clone https://github.com/JonSnow1807/api-orchestrator.git /opt/api-orchestrator
  - cd /opt/api-orchestrator
  - docker-compose -f deploy/docker-compose.prod.yml up -d
EOF
}

# Main execution
main() {
    show_menu
    
    # Create cloud-init if needed
    if [[ $choice -ge 1 && $choice -le 6 ]]; then
        create_cloud_init
    fi
    
    case $choice in
        1)
            deploy_digitalocean
            setup_github_secrets 1
            ;;
        2)
            deploy_aws
            setup_github_secrets 2
            ;;
        3)
            echo "Google Cloud deployment coming soon..."
            ;;
        4)
            echo "Azure deployment coming soon..."
            ;;
        5)
            echo "Linode deployment coming soon..."
            ;;
        6)
            echo "Vultr deployment coming soon..."
            ;;
        7)
            deploy_railway
            setup_github_secrets 7
            ;;
        8)
            deploy_render
            setup_github_secrets 8
            ;;
        9)
            echo "Fly.io deployment coming soon..."
            ;;
        10)
            deploy_local
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            exit 1
            ;;
    esac
    
    echo ""
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Check the application at the provided URL"
    echo "2. Configure environment variables if needed"
    echo "3. Set up your domain name (optional)"
    echo "4. Monitor logs with: docker-compose logs -f"
    echo ""
    echo -e "${BLUE}Thank you for using API Orchestrator!${NC}"
}

# Run main
main