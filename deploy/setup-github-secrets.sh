#!/bin/bash
# Script to help set up GitHub secrets for CI/CD

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
║     🔐 GitHub Secrets Setup Wizard 🔐        ║
║                                               ║
║     Configure CI/CD deployment secrets        ║
║                                               ║
╚═══════════════════════════════════════════════╝
${NC}"

# Check for GitHub CLI
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI not found. Installing...${NC}"
    
    # Detect OS and install accordingly
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install gh
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update
        sudo apt install gh
    else
        echo -e "${RED}Please install GitHub CLI manually: https://cli.github.com/${NC}"
        exit 1
    fi
fi

# Authenticate with GitHub
echo -e "${YELLOW}Authenticating with GitHub...${NC}"
gh auth status &>/dev/null || gh auth login

# Get repository information
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    read -p "Enter your GitHub repository (e.g., username/repo): " REPO
fi

echo -e "${GREEN}Setting up secrets for: $REPO${NC}"

# Function to set a secret
set_secret() {
    local name=$1
    local description=$2
    local required=$3
    local multiline=$4
    
    echo ""
    echo -e "${BLUE}$name${NC}"
    echo -e "${YELLOW}$description${NC}"
    
    if [ "$required" == "true" ]; then
        echo -e "${RED}(Required)${NC}"
    else
        echo -e "${GREEN}(Optional)${NC}"
    fi
    
    if [ "$multiline" == "true" ]; then
        echo "Enter value (press Ctrl+D when done):"
        value=$(cat)
    else
        read -s -p "Enter value (hidden): " value
        echo ""
    fi
    
    if [ ! -z "$value" ]; then
        echo "$value" | gh secret set $name -R $REPO
        echo -e "${GREEN}✅ $name configured${NC}"
    else
        if [ "$required" == "true" ]; then
            echo -e "${RED}⚠️  $name is required but was skipped${NC}"
        else
            echo -e "${YELLOW}⏭  $name skipped${NC}"
        fi
    fi
}

# Menu for deployment type
echo -e "${YELLOW}
Select your deployment type:${NC}
1) VPS/Server deployment
2) Railway deployment
3) Render deployment
4) AWS deployment
5) DigitalOcean deployment
6) All (configure everything)
"
read -p "Enter choice [1-6]: " deployment_type

echo -e "${BLUE}
═══════════════════════════════════════════════
Setting up GitHub Secrets
═══════════════════════════════════════════════${NC}"

# Common secrets (always needed)
echo -e "${YELLOW}
──────────────────────────────────────────────
Common Secrets (Required for all deployments)
──────────────────────────────────────────────${NC}"

set_secret "SECRET_KEY" "Django/FastAPI secret key (32+ characters)" "true" "false"
set_secret "ANTHROPIC_API_KEY" "Anthropic Claude API key for AI features" "false" "false"

# Deployment-specific secrets
case $deployment_type in
    1|6) # VPS/Server
        echo -e "${YELLOW}
──────────────────────────────────────────────
VPS/Server Deployment Secrets
──────────────────────────────────────────────${NC}"
        
        set_secret "VPS_HOST" "Your server IP address (e.g., 192.168.1.100)" "true" "false"
        set_secret "VPS_USER" "SSH username (usually 'root' or 'ubuntu')" "true" "false"
        
        echo -e "${YELLOW}
For VPS_SSH_KEY, provide your private SSH key.
You can get it with: cat ~/.ssh/id_rsa${NC}"
        set_secret "VPS_SSH_KEY" "Private SSH key for server access" "true" "true"
        ;;&  # Continue to next cases if 6 was selected
        
    2|6) # Railway
        echo -e "${YELLOW}
──────────────────────────────────────────────
Railway Deployment Secrets
──────────────────────────────────────────────${NC}"
        
        echo -e "${YELLOW}
To get your Railway token:
1. Go to https://railway.app/account/tokens
2. Generate a new token
3. Copy and paste it here${NC}"
        
        set_secret "RAILWAY_TOKEN" "Railway deployment token" "true" "false"
        ;;&
        
    3|6) # Render
        echo -e "${YELLOW}
──────────────────────────────────────────────
Render Deployment Secrets
──────────────────────────────────────────────${NC}"
        
        echo -e "${YELLOW}
To get your Render deploy hook:
1. Go to your Render dashboard
2. Select your service
3. Go to Settings → Deploy Hook
4. Copy the URL${NC}"
        
        set_secret "RENDER_DEPLOY_HOOK" "Render deploy webhook URL" "true" "false"
        ;;&
        
    4|6) # AWS
        echo -e "${YELLOW}
──────────────────────────────────────────────
AWS Deployment Secrets
──────────────────────────────────────────────${NC}"
        
        set_secret "AWS_ACCESS_KEY_ID" "AWS Access Key ID" "true" "false"
        set_secret "AWS_SECRET_ACCESS_KEY" "AWS Secret Access Key" "true" "false"
        set_secret "AWS_REGION" "AWS Region (e.g., us-east-1)" "true" "false"
        ;;&
        
    5|6) # DigitalOcean
        echo -e "${YELLOW}
──────────────────────────────────────────────
DigitalOcean Deployment Secrets
──────────────────────────────────────────────${NC}"
        
        echo -e "${YELLOW}
To get your DigitalOcean token:
1. Go to https://cloud.digitalocean.com/account/api/tokens
2. Generate a new token
3. Copy and paste it here${NC}"
        
        set_secret "DO_TOKEN" "DigitalOcean API token" "true" "false"
        ;;
esac

# Optional monitoring secrets
echo -e "${YELLOW}
──────────────────────────────────────────────
Optional Monitoring & Notifications
──────────────────────────────────────────────${NC}"

set_secret "SLACK_WEBHOOK_URL" "Slack webhook for deployment notifications" "false" "false"
set_secret "SENTRY_DSN" "Sentry DSN for error tracking" "false" "false"

# Summary
echo -e "${GREEN}
═══════════════════════════════════════════════
✅ GitHub Secrets Configuration Complete!
═══════════════════════════════════════════════${NC}"

echo -e "${BLUE}
You can verify your secrets at:
https://github.com/$REPO/settings/secrets/actions

To trigger a deployment:
1. Push to the main branch (auto-deploy)
2. Or manually trigger from Actions tab

Next steps:
1. Copy .env.template to .env and configure
2. Run: ./deploy/one-click-deploy.sh
3. Monitor deployment in GitHub Actions
${NC}"

# Test the workflow
read -p "Would you like to test the deployment workflow? (y/N): " test_deploy
if [[ $test_deploy =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Triggering test deployment...${NC}"
    gh workflow run auto-deploy.yml -R $REPO
    echo -e "${GREEN}Deployment triggered! Check: https://github.com/$REPO/actions${NC}"
fi