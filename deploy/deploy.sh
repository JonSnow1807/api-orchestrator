#!/bin/bash
# Automated deployment script for API Orchestrator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_USER=${DEPLOY_USER:-deploy}
APP_NAME="api-orchestrator"
DEPLOY_PATH="/opt/${APP_NAME}"
GITHUB_REPO="https://github.com/JonSnow1807/api-orchestrator.git"
BRANCH=${BRANCH:-main}

echo -e "${GREEN}🚀 API Orchestrator Automated Deployment${NC}"
echo "================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Docker
install_docker() {
    echo -e "${YELLOW}📦 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}✅ Docker installed${NC}"
}

# Function to install Docker Compose
install_docker_compose() {
    echo -e "${YELLOW}📦 Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✅ Docker Compose installed${NC}"
}

# Function to setup SSL with Let's Encrypt
setup_ssl() {
    local domain=$1
    echo -e "${YELLOW}🔒 Setting up SSL for ${domain}...${NC}"
    
    # Install certbot
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
    
    # Get SSL certificate
    sudo certbot certonly --standalone -d ${domain} --non-interactive --agree-tos --email admin@${domain}
    
    # Create SSL directory
    sudo mkdir -p ${DEPLOY_PATH}/nginx/ssl
    
    # Copy certificates
    sudo cp /etc/letsencrypt/live/${domain}/fullchain.pem ${DEPLOY_PATH}/nginx/ssl/cert.pem
    sudo cp /etc/letsencrypt/live/${domain}/privkey.pem ${DEPLOY_PATH}/nginx/ssl/key.pem
    
    echo -e "${GREEN}✅ SSL certificates configured${NC}"
}

# Function to setup firewall
setup_firewall() {
    echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    echo -e "${GREEN}✅ Firewall configured${NC}"
}

# Function to create deploy user
create_deploy_user() {
    echo -e "${YELLOW}👤 Creating deployment user...${NC}"
    if ! id -u ${DEPLOY_USER} > /dev/null 2>&1; then
        sudo useradd -m -s /bin/bash ${DEPLOY_USER}
        sudo usermod -aG docker ${DEPLOY_USER}
        echo -e "${GREEN}✅ Deploy user created${NC}"
    else
        echo -e "${GREEN}✅ Deploy user already exists${NC}"
    fi
}

# Function to clone/update repository
setup_repository() {
    echo -e "${YELLOW}📥 Setting up repository...${NC}"
    
    sudo mkdir -p ${DEPLOY_PATH}
    sudo chown -R ${DEPLOY_USER}:${DEPLOY_USER} ${DEPLOY_PATH}
    
    if [ -d "${DEPLOY_PATH}/.git" ]; then
        echo "Updating existing repository..."
        cd ${DEPLOY_PATH}
        git fetch origin
        git checkout ${BRANCH}
        git pull origin ${BRANCH}
    else
        echo "Cloning repository..."
        git clone -b ${BRANCH} ${GITHUB_REPO} ${DEPLOY_PATH}
    fi
    
    echo -e "${GREEN}✅ Repository ready${NC}"
}

# Function to setup environment
setup_environment() {
    echo -e "${YELLOW}⚙️ Setting up environment...${NC}"
    
    if [ ! -f "${DEPLOY_PATH}/.env" ]; then
        cp ${DEPLOY_PATH}/.env.example ${DEPLOY_PATH}/.env
        
        # Generate secure secrets
        SECRET_KEY=$(openssl rand -hex 32)
        POSTGRES_PASSWORD=$(openssl rand -hex 16)
        REDIS_PASSWORD=$(openssl rand -hex 16)
        
        # Update .env file
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=${SECRET_KEY}/" ${DEPLOY_PATH}/.env
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" ${DEPLOY_PATH}/.env
        sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASSWORD}/" ${DEPLOY_PATH}/.env
        
        echo -e "${YELLOW}⚠️  Please edit ${DEPLOY_PATH}/.env to add your API keys${NC}"
    fi
    
    echo -e "${GREEN}✅ Environment configured${NC}"
}

# Function to build and start services
deploy_application() {
    echo -e "${YELLOW}🚀 Deploying application...${NC}"
    
    cd ${DEPLOY_PATH}
    
    # Build frontend
    echo "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Start services
    echo "Starting services..."
    docker-compose -f deploy/docker-compose.prod.yml pull
    docker-compose -f deploy/docker-compose.prod.yml up -d
    
    echo -e "${GREEN}✅ Application deployed${NC}"
}

# Function to setup monitoring
setup_monitoring() {
    echo -e "${YELLOW}📊 Setting up monitoring...${NC}"
    
    # Create monitoring script
    cat > ${DEPLOY_PATH}/monitor.sh << 'EOF'
#!/bin/bash
# Health check script

check_service() {
    local service=$1
    if docker-compose -f deploy/docker-compose.prod.yml ps | grep $service | grep -q "Up"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is down"
        # Restart service
        docker-compose -f deploy/docker-compose.prod.yml restart $service
    fi
}

check_service postgres
check_service redis
check_service backend
check_service nginx
EOF
    
    chmod +x ${DEPLOY_PATH}/monitor.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * ${DEPLOY_PATH}/monitor.sh") | crontab -
    
    echo -e "${GREEN}✅ Monitoring configured${NC}"
}

# Function to setup automatic backups
setup_backups() {
    echo -e "${YELLOW}💾 Setting up backups...${NC}"
    
    # Create backup script
    cat > ${DEPLOY_PATH}/backup.sh << 'EOF'
#!/bin/bash
# Backup script for API Orchestrator

BACKUP_DIR="/backups/api-orchestrator"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

# Backup database
docker exec $(docker ps -qf "name=postgres") pg_dump -U postgres api_orchestrator | gzip > ${BACKUP_DIR}/db_${TIMESTAMP}.sql.gz

# Backup uploaded files
tar -czf ${BACKUP_DIR}/files_${TIMESTAMP}.tar.gz /opt/api-orchestrator/output

# Keep only last 7 days of backups
find ${BACKUP_DIR} -type f -mtime +7 -delete

echo "Backup completed: ${TIMESTAMP}"
EOF
    
    chmod +x ${DEPLOY_PATH}/backup.sh
    
    # Add to crontab (daily at 2 AM)
    (crontab -l 2>/dev/null; echo "0 2 * * * ${DEPLOY_PATH}/backup.sh") | crontab -
    
    echo -e "${GREEN}✅ Backups configured${NC}"
}

# Main deployment flow
main() {
    echo -e "${GREEN}Starting automated deployment...${NC}"
    
    # Check for required tools
    if ! command_exists docker; then
        install_docker
    fi
    
    if ! command_exists docker-compose; then
        install_docker_compose
    fi
    
    # Setup environment
    create_deploy_user
    setup_repository
    setup_environment
    
    # Optional: Setup domain and SSL
    if [ ! -z "$DOMAIN" ]; then
        setup_ssl $DOMAIN
    fi
    
    # Setup security
    setup_firewall
    
    # Deploy application
    deploy_application
    
    # Setup monitoring and backups
    setup_monitoring
    setup_backups
    
    echo ""
    echo -e "${GREEN}🎉 Deployment complete!${NC}"
    echo ""
    echo "Access your application at:"
    if [ ! -z "$DOMAIN" ]; then
        echo "  https://${DOMAIN}"
    else
        echo "  http://$(curl -s ifconfig.me)"
    fi
    echo ""
    echo "Useful commands:"
    echo "  cd ${DEPLOY_PATH}"
    echo "  docker-compose -f deploy/docker-compose.prod.yml logs -f"
    echo "  docker-compose -f deploy/docker-compose.prod.yml restart"
    echo ""
}

# Run main function
main "$@"