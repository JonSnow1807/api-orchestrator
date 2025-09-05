#!/bin/bash

# Professional AWS Deployment Script
# This deploys your API Orchestrator to production-grade AWS infrastructure

set -e

echo "🚀 API Orchestrator - Professional AWS Deployment"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found. Installing...${NC}"
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform not found. Installing...${NC}"
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All prerequisites installed${NC}"
}

# Configure AWS credentials
configure_aws() {
    echo -e "${YELLOW}Configuring AWS credentials...${NC}"
    
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        read -p "Enter your AWS Access Key ID: " AWS_ACCESS_KEY_ID
        export AWS_ACCESS_KEY_ID
    fi
    
    if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
        read -sp "Enter your AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
        export AWS_SECRET_ACCESS_KEY
        echo
    fi
    
    if [ -z "$AWS_REGION" ]; then
        read -p "Enter your AWS Region (default: us-east-1): " AWS_REGION
        AWS_REGION=${AWS_REGION:-us-east-1}
        export AWS_REGION
    fi
    
    # Test AWS credentials
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "${GREEN}✅ AWS credentials configured successfully${NC}"
    else
        echo -e "${RED}❌ Invalid AWS credentials${NC}"
        exit 1
    fi
}

# Get domain name
get_domain() {
    echo -e "${YELLOW}Domain Configuration${NC}"
    read -p "Enter your domain name (e.g., api-orchestrator.com): " DOMAIN_NAME
    export TF_VAR_domain_name=$DOMAIN_NAME
}

# Build Docker images
build_docker() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    
    # Build backend
    docker build -t api-orchestrator-backend:latest -f docker/Dockerfile .
    
    # Get ECR login
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Create ECR repository if it doesn't exist
    aws ecr create-repository --repository-name api-orchestrator-backend --region $AWS_REGION 2>/dev/null || true
    
    # Tag and push
    ECR_URI=$(aws ecr describe-repositories --repository-names api-orchestrator-backend --query 'repositories[0].repositoryUri' --output text)
    docker tag api-orchestrator-backend:latest $ECR_URI:latest
    docker push $ECR_URI:latest
    
    echo -e "${GREEN}✅ Docker images built and pushed${NC}"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    echo -e "${YELLOW}Deploying AWS infrastructure...${NC}"
    
    cd infrastructure/terraform
    
    # Initialize Terraform
    terraform init
    
    # Plan deployment
    terraform plan -out=tfplan
    
    # Apply deployment
    terraform apply tfplan
    
    # Get outputs
    export ALB_URL=$(terraform output -raw load_balancer_url)
    export DB_ENDPOINT=$(terraform output -raw database_endpoint)
    export REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
    
    cd ../..
    
    echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
}

# Deploy frontend to S3/CloudFront
deploy_frontend() {
    echo -e "${YELLOW}Deploying frontend...${NC}"
    
    # Build frontend
    cd frontend
    npm install
    npm run build
    
    # Create S3 bucket
    aws s3 mb s3://$DOMAIN_NAME-frontend --region $AWS_REGION 2>/dev/null || true
    
    # Upload to S3
    aws s3 sync dist/ s3://$DOMAIN_NAME-frontend --delete
    
    # Set bucket policy for CloudFront
    aws s3api put-bucket-policy --bucket $DOMAIN_NAME-frontend --policy '{
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowCloudFrontAccess",
            "Effect": "Allow",
            "Principal": {"Service": "cloudfront.amazonaws.com"},
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::'$DOMAIN_NAME'-frontend/*"
        }]
    }'
    
    cd ..
    
    echo -e "${GREEN}✅ Frontend deployed${NC}"
}

# Configure secrets
configure_secrets() {
    echo -e "${YELLOW}Configuring secrets...${NC}"
    
    # Stripe keys
    read -sp "Enter your Stripe Secret Key: " STRIPE_SECRET_KEY
    echo
    aws secretsmanager create-secret --name stripe-secret-key --secret-string "$STRIPE_SECRET_KEY" --region $AWS_REGION 2>/dev/null || \
    aws secretsmanager update-secret --secret-id stripe-secret-key --secret-string "$STRIPE_SECRET_KEY" --region $AWS_REGION
    
    # Anthropic API key
    read -sp "Enter your Anthropic API Key: " ANTHROPIC_API_KEY
    echo
    aws secretsmanager create-secret --name anthropic-api-key --secret-string "$ANTHROPIC_API_KEY" --region $AWS_REGION 2>/dev/null || \
    aws secretsmanager update-secret --secret-id anthropic-api-key --secret-string "$ANTHROPIC_API_KEY" --region $AWS_REGION
    
    # Generate JWT secret
    JWT_SECRET=$(openssl rand -base64 32)
    aws secretsmanager create-secret --name jwt-secret-key --secret-string "$JWT_SECRET" --region $AWS_REGION 2>/dev/null || \
    aws secretsmanager update-secret --secret-id jwt-secret-key --secret-string "$JWT_SECRET" --region $AWS_REGION
    
    echo -e "${GREEN}✅ Secrets configured${NC}"
}

# Setup monitoring
setup_monitoring() {
    echo -e "${YELLOW}Setting up monitoring...${NC}"
    
    # Create CloudWatch alarms
    aws cloudwatch put-metric-alarm \
        --alarm-name "api-orchestrator-high-cpu" \
        --alarm-description "Alarm when CPU exceeds 80%" \
        --metric-name CPUUtilization \
        --namespace AWS/ECS \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2
    
    # Setup SNS notifications
    aws sns create-topic --name api-orchestrator-alerts
    aws sns subscribe --topic-arn arn:aws:sns:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):api-orchestrator-alerts \
        --protocol email --notification-endpoint your-email@example.com
    
    echo -e "${GREEN}✅ Monitoring configured${NC}"
}

# Main deployment
main() {
    echo -e "${GREEN}Starting professional AWS deployment...${NC}\n"
    
    check_prerequisites
    configure_aws
    get_domain
    build_docker
    deploy_infrastructure
    deploy_frontend
    configure_secrets
    setup_monitoring
    
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
    echo -e "================================================"
    echo -e "🌐 Your application is live at: https://$DOMAIN_NAME"
    echo -e "📊 Load Balancer URL: $ALB_URL"
    echo -e "🗄️ Database Endpoint: $DB_ENDPOINT"
    echo -e "💾 Redis Endpoint: $REDIS_ENDPOINT"
    echo -e "\nNext steps:"
    echo -e "1. Update your DNS nameservers to point to Route53"
    echo -e "2. Verify SSL certificate in AWS Certificate Manager"
    echo -e "3. Monitor your application in CloudWatch"
    echo -e "4. Set up your Stripe webhook to: https://$DOMAIN_NAME/api/billing/webhook"
}

# Run main function
main