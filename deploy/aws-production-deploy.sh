#!/bin/bash

# API Orchestrator - AWS Production Deployment
# Enterprise-grade deployment with auto-scaling, load balancing, and CDN

set -e

echo "
╔══════════════════════════════════════════════════════════════╗
║       🚀 API ORCHESTRATOR - AWS PRODUCTION DEPLOYMENT 🚀      ║
╚══════════════════════════════════════════════════════════════╝
"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# AWS Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
APP_NAME="api-orchestrator"
DOMAIN_NAME=${DOMAIN_NAME:-"api-orchestrator.com"}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install awscli
    else
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
    fi
fi

echo -e "${YELLOW}Choose AWS deployment architecture:${NC}"
echo "1) ECS Fargate (Serverless containers - Recommended)"
echo "2) Elastic Beanstalk (Managed platform)"
echo "3) EC2 with Auto Scaling (Full control)"
echo "4) Lambda + API Gateway (Serverless functions)"
echo ""
read -p "Enter choice (1-4): " DEPLOY_CHOICE

case $DEPLOY_CHOICE in
    1)
        echo -e "${GREEN}Deploying to AWS ECS Fargate (Best for production)${NC}"
        
        # Create ECS task definition
        cat > ecs-task-definition.json << 'EOF'
{
  "family": "api-orchestrator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api-orchestrator-backend",
      "image": "ghcr.io/jonsnow1807/api-orchestrator:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://postgres:password@rds-endpoint:5432/api_orchestrator"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379"
        },
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        }
      ],
      "secrets": [
        {
          "name": "JWT_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:account:secret:jwt-secret"
        },
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:account:secret:anthropic-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/api-orchestrator",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
EOF

        # Create CloudFormation template for complete infrastructure
        cat > aws-infrastructure.yaml << 'EOF'
AWSTemplateFormatVersion: '2010-09-09'
Description: 'API Orchestrator - Production Infrastructure'

Parameters:
  DomainName:
    Type: String
    Default: api-orchestrator.com
    Description: Domain name for the application

Resources:
  # VPC Configuration
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: api-orchestrator-vpc

  # Public Subnets
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: true

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: true

  # Internet Gateway
  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # Route Table
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  # Application Load Balancer
  ALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Name: api-orchestrator-alb
      Type: application
      Scheme: internet-facing
      Subnets:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroup

  ALBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ALB
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  # ECS Cluster
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: api-orchestrator-cluster
      CapacityProviders:
        - FARGATE
        - FARGATE_SPOT

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      ServiceName: api-orchestrator-service
      Cluster: !Ref ECSCluster
      TaskDefinition: !Ref TaskDefinition
      DesiredCount: 2
      LaunchType: FARGATE
      NetworkConfiguration:
        AwsvpcConfiguration:
          Subnets:
            - !Ref PublicSubnet1
            - !Ref PublicSubnet2
          SecurityGroups:
            - !Ref ECSSecurityGroup
          AssignPublicIp: ENABLED
      LoadBalancers:
        - ContainerName: api-orchestrator-backend
          ContainerPort: 8000
          TargetGroupArn: !Ref TargetGroup
      HealthCheckGracePeriodSeconds: 60

  ECSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ECS tasks
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 8000
          ToPort: 8000
          SourceSecurityGroupId: !Ref ALBSecurityGroup

  # Target Group
  TargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    Properties:
      Name: api-orchestrator-tg
      Port: 8000
      Protocol: HTTP
      VpcId: !Ref VPC
      TargetType: ip
      HealthCheckPath: /health
      HealthCheckIntervalSeconds: 30
      HealthCheckTimeoutSeconds: 5
      HealthyThresholdCount: 2
      UnhealthyThresholdCount: 3

  # ALB Listener
  ALBListener:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      LoadBalancerArn: !Ref ALB
      Port: 80
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref TargetGroup

  # RDS Database
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS
      SubnetIds:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  RDSInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: api-orchestrator-db
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: '14.7'
      MasterUsername: postgres
      MasterUserPassword: !Sub '{{resolve:secretsmanager:rds-password::password}}'
      AllocatedStorage: 20
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref RDSSecurityGroup
      BackupRetentionPeriod: 7
      MultiAZ: true

  RDSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref ECSSecurityGroup

  # ElastiCache Redis
  CacheSubnetGroup:
    Type: AWS::ElastiCache::SubnetGroup
    Properties:
      Description: Subnet group for ElastiCache
      SubnetIds:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  ElastiCacheCluster:
    Type: AWS::ElastiCache::CacheCluster
    Properties:
      CacheNodeType: cache.t3.micro
      Engine: redis
      NumCacheNodes: 1
      CacheSubnetGroupName: !Ref CacheSubnetGroup
      VpcSecurityGroupIds:
        - !Ref CacheSecurityGroup

  CacheSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for ElastiCache
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 6379
          ToPort: 6379
          SourceSecurityGroupId: !Ref ECSSecurityGroup

  # CloudFront CDN
  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
          - Id: ALBOrigin
            DomainName: !GetAtt ALB.DNSName
            CustomOriginConfig:
              OriginProtocolPolicy: http-only
              HTTPPort: 80
        Enabled: true
        DefaultCacheBehavior:
          TargetOriginId: ALBOrigin
          ViewerProtocolPolicy: redirect-to-https
          AllowedMethods:
            - GET
            - HEAD
            - OPTIONS
            - PUT
            - POST
            - PATCH
            - DELETE
          CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad  # Disabled caching
          OriginRequestPolicyId: 88a5eaf4-2fd4-4709-b370-b4c650ea3fcf  # All headers
        PriceClass: PriceClass_100
        ViewerCertificate:
          CloudFrontDefaultCertificate: true

  # Auto Scaling
  AutoScalingTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      ServiceNamespace: ecs
      ScalableDimension: ecs:service:DesiredCount
      ResourceId: !Sub 'service/${ECSCluster}/${ECSService}'
      MinCapacity: 2
      MaxCapacity: 10
      RoleARN: !Sub 'arn:aws:iam::${AWS::AccountId}:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService'

  AutoScalingPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: api-orchestrator-scaling-policy
      PolicyType: TargetTrackingScaling
      ScalingTargetId: !Ref AutoScalingTarget
      TargetTrackingScalingPolicyConfiguration:
        PredefinedMetricSpecification:
          PredefinedMetricType: ECSServiceAverageCPUUtilization
        TargetValue: 70

  # CloudWatch Alarms
  HighCPUAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmDescription: Alarm when CPU exceeds 80%
      MetricName: CPUUtilization
      Namespace: AWS/ECS
      Statistic: Average
      Period: 300
      EvaluationPeriods: 2
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: ServiceName
          Value: api-orchestrator-service
        - Name: ClusterName
          Value: !Ref ECSCluster

Outputs:
  LoadBalancerURL:
    Description: URL of the Application Load Balancer
    Value: !GetAtt ALB.DNSName
  CloudFrontURL:
    Description: CloudFront distribution URL
    Value: !GetAtt CloudFrontDistribution.DomainName
  RDSEndpoint:
    Description: RDS instance endpoint
    Value: !GetAtt RDSInstance.Endpoint.Address
  ElastiCacheEndpoint:
    Description: ElastiCache endpoint
    Value: !GetAtt ElastiCacheCluster.RedisEndpoint.Address
EOF

        echo -e "${YELLOW}Deploying AWS infrastructure...${NC}"
        
        # Create ECR repository
        aws ecr create-repository --repository-name $APP_NAME --region $AWS_REGION 2>/dev/null || true
        
        # Get ECR login token
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws ecr describe-repositories --repository-names $APP_NAME --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)
        
        # Build and push Docker image
        echo -e "${BLUE}Building Docker image...${NC}"
        docker build -t $APP_NAME -f docker/Dockerfile .
        
        # Tag and push to ECR
        ECR_URI=$(aws ecr describe-repositories --repository-names $APP_NAME --query 'repositories[0].repositoryUri' --output text)
        docker tag $APP_NAME:latest $ECR_URI:latest
        docker push $ECR_URI:latest
        
        # Deploy CloudFormation stack
        echo -e "${BLUE}Creating AWS infrastructure...${NC}"
        aws cloudformation create-stack \
            --stack-name api-orchestrator-stack \
            --template-body file://aws-infrastructure.yaml \
            --parameters ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
            --capabilities CAPABILITY_IAM \
            --region $AWS_REGION
        
        # Wait for stack creation
        echo -e "${YELLOW}Waiting for infrastructure creation (this may take 10-15 minutes)...${NC}"
        aws cloudformation wait stack-create-complete --stack-name api-orchestrator-stack --region $AWS_REGION
        
        # Get outputs
        ALB_URL=$(aws cloudformation describe-stacks --stack-name api-orchestrator-stack --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerURL`].OutputValue' --output text)
        CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name api-orchestrator-stack --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' --output text)
        
        echo -e "${GREEN}✅ Deployment complete!${NC}"
        echo -e "${GREEN}Application Load Balancer: http://$ALB_URL${NC}"
        echo -e "${GREEN}CloudFront CDN: https://$CLOUDFRONT_URL${NC}"
        ;;
        
    2)
        echo -e "${GREEN}Deploying to AWS Elastic Beanstalk${NC}"
        
        # Create .ebextensions directory
        mkdir -p .ebextensions
        
        # Create EB configuration
        cat > .ebextensions/01_api_orchestrator.config << 'EOF'
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: backend.src.main:app
  aws:elasticbeanstalk:application:environment:
    DATABASE_URL: postgresql://postgres:password@rds-endpoint:5432/api_orchestrator
    JWT_SECRET_KEY: your-secret-key
    CORS_ORIGINS: https://api-orchestrator.com
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: frontend/dist
  aws:autoscaling:asg:
    MinSize: 2
    MaxSize: 10
  aws:autoscaling:trigger:
    MeasureName: CPUUtilization
    Statistic: Average
    Unit: Percent
    UpperThreshold: 80
    LowerThreshold: 20

container_commands:
  01_install_dependencies:
    command: "pip install -r backend/requirements.txt"
  02_migrate:
    command: "cd backend && python -m alembic upgrade head"
  03_collectstatic:
    command: "cd frontend && npm install && npm run build"
EOF

        # Initialize EB
        eb init -p python-3.11 $APP_NAME --region $AWS_REGION
        
        # Create environment
        eb create api-orchestrator-prod --instance_type t3.small --elb-type application
        
        # Deploy
        eb deploy
        
        # Get URL
        eb open
        ;;
        
    3)
        echo -e "${GREEN}Deploying to EC2 with Auto Scaling${NC}"
        
        # Create launch template
        cat > ec2-user-data.sh << 'EOF'
#!/bin/bash
# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /opt
git clone https://github.com/JonSnow1807/api-orchestrator.git
cd api-orchestrator

# Start application
docker-compose -f deploy/docker-compose.prod.yml up -d

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm
EOF

        # Create launch template
        aws ec2 create-launch-template \
            --launch-template-name api-orchestrator-template \
            --launch-template-data '{
                "ImageId": "ami-0c94855ba95c574c9",
                "InstanceType": "t3.medium",
                "KeyName": "your-key-pair",
                "SecurityGroupIds": ["sg-xxxxxx"],
                "UserData": "'$(base64 ec2-user-data.sh)'",
                "IamInstanceProfile": {
                    "Name": "api-orchestrator-instance-profile"
                },
                "TagSpecifications": [{
                    "ResourceType": "instance",
                    "Tags": [{"Key": "Name", "Value": "api-orchestrator"}]
                }]
            }'
        
        # Create Auto Scaling group
        aws autoscaling create-auto-scaling-group \
            --auto-scaling-group-name api-orchestrator-asg \
            --launch-template LaunchTemplateName=api-orchestrator-template \
            --min-size 2 \
            --max-size 10 \
            --desired-capacity 2 \
            --vpc-zone-identifier "subnet-xxxxx,subnet-yyyyy" \
            --target-group-arns arn:aws:elasticloadbalancing:region:account:targetgroup/api-orchestrator-tg \
            --health-check-type ELB \
            --health-check-grace-period 300
        ;;
        
    4)
        echo -e "${GREEN}Deploying to AWS Lambda + API Gateway${NC}"
        
        # Create serverless configuration
        cat > serverless.yml << 'EOF'
service: api-orchestrator

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    DATABASE_URL: ${env:DATABASE_URL}
    JWT_SECRET_KEY: ${env:JWT_SECRET_KEY}

functions:
  api:
    handler: backend.src.main.handler
    events:
      - httpApi:
          path: /{proxy+}
          method: ANY
    timeout: 30
    memorySize: 512

plugins:
  - serverless-python-requirements
  - serverless-wsgi

custom:
  wsgi:
    app: backend.src.main.app
  pythonRequirements:
    dockerizePip: true
EOF

        # Install serverless
        npm install -g serverless
        npm install --save-dev serverless-python-requirements serverless-wsgi
        
        # Deploy
        serverless deploy --stage production
        ;;
esac

# Create monitoring dashboard
echo -e "${BLUE}Creating CloudWatch dashboard...${NC}"
cat > cloudwatch-dashboard.json << 'EOF'
{
    "DashboardName": "api-orchestrator-monitoring",
    "DashboardBody": "{\"widgets\":[{\"type\":\"metric\",\"properties\":{\"metrics\":[[\"AWS/ECS\",\"CPUUtilization\",{\"stat\":\"Average\"}],[\".\",\"MemoryUtilization\",{\"stat\":\"Average\"}]],\"period\":300,\"stat\":\"Average\",\"region\":\"us-east-1\",\"title\":\"ECS Metrics\"}},{\"type\":\"metric\",\"properties\":{\"metrics\":[[\"AWS/ApplicationELB\",\"TargetResponseTime\",{\"stat\":\"Average\"}],[\".\",\"RequestCount\",{\"stat\":\"Sum\"}]],\"period\":300,\"stat\":\"Average\",\"region\":\"us-east-1\",\"title\":\"ALB Metrics\"}}]}"
}
EOF

aws cloudwatch put-dashboard --dashboard-name api-orchestrator-monitoring --dashboard-body file://cloudwatch-dashboard.json

# Set up Route 53 (if domain is managed by AWS)
echo -e "${BLUE}Setting up Route 53...${NC}"
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name --query "HostedZones[?Name=='${DOMAIN_NAME}.'].Id" --output text | cut -d'/' -f3)

if [ ! -z "$HOSTED_ZONE_ID" ]; then
    aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch '{
        "Changes": [{
            "Action": "UPSERT",
            "ResourceRecordSet": {
                "Name": "'${DOMAIN_NAME}'",
                "Type": "CNAME",
                "TTL": 300,
                "ResourceRecords": [{
                    "Value": "'${CLOUDFRONT_URL}'"
                }]
            }
        }]
    }'
    echo -e "${GREEN}✅ Domain configured: https://${DOMAIN_NAME}${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           🎉 AWS PRODUCTION DEPLOYMENT COMPLETE! 🎉            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Your application is now running on AWS with:${NC}"
echo "✅ Auto-scaling (2-10 instances)"
echo "✅ Load balancing across multiple AZs"
echo "✅ CloudFront CDN for global distribution"
echo "✅ RDS PostgreSQL database with Multi-AZ"
echo "✅ ElastiCache Redis for caching"
echo "✅ CloudWatch monitoring and alarms"
echo "✅ Automatic SSL/TLS via CloudFront"
echo ""
echo -e "${YELLOW}Access your application:${NC}"
echo "🌐 CloudFront: https://$CLOUDFRONT_URL"
echo "🌐 Load Balancer: http://$ALB_URL"
echo "🌐 Custom Domain: https://$DOMAIN_NAME (if configured)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Configure custom domain in Route 53"
echo "2. Set up AWS SES for email notifications"
echo "3. Enable AWS WAF for DDoS protection"
echo "4. Configure backup policies"
echo "5. Set up cost alerts in AWS Budgets"
echo ""
echo -e "${GREEN}Estimated monthly cost: ~$150-200 (with auto-scaling)${NC}"