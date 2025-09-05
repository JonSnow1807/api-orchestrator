# 🚀 API Orchestrator - Production Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ SSD
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Python**: 3.11+ (for manual deployment)
- **Node.js**: 20+ (for frontend builds)
- **PostgreSQL**: 16+ (for production database)

### Required API Keys
- **Anthropic API Key**: For AI analysis features
- **OpenAI API Key** (optional): Alternative AI provider
- **SMTP Credentials**: For email notifications

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/api-orchestrator.git
cd api-orchestrator
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit with your configuration
nano .env
```

### 3. Deploy with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create admin user (optional)
docker-compose exec backend python scripts/create_admin.py
```

### 5. Access the Application
- Frontend: http://localhost
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Environment Configuration

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/api_orchestrator

# Security
SECRET_KEY=your-secret-key-min-32-chars  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...  # Optional

# Email Service
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=noreply@api-orchestrator.com

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourdomain.com"]

# Redis Cache
REDIS_URL=redis://:password@redis:6379/0
```

### Generate Secure Keys
```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate database password
openssl rand -base64 32

# Generate Redis password
openssl rand -base64 24
```

## Database Setup

### PostgreSQL with Docker
```bash
# Start PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_DB=api_orchestrator \
  -e POSTGRES_USER=orchestrator \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:16-alpine
```

### Manual PostgreSQL Setup
```sql
-- Create database and user
CREATE DATABASE api_orchestrator;
CREATE USER orchestrator WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE api_orchestrator TO orchestrator;

-- Enable required extensions
\c api_orchestrator
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Run Migrations
```bash
# Using Alembic
alembic upgrade head

# Generate new migration (after model changes)
alembic revision --autogenerate -m "Description of changes"
```

## Docker Deployment

### Production Build
```bash
# Build optimized images
docker-compose -f docker-compose.yml build --no-cache

# Start services
docker-compose up -d

# Scale backend workers
docker-compose up -d --scale backend=3
```

### Docker Swarm Deployment
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-stack.yml api-orchestrator

# Check services
docker service ls
docker service logs api-orchestrator_backend
```

### Kubernetes Deployment
```bash
# Apply configurations
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl apply -f k8s/ingress.yml

# Check deployment
kubectl get pods -n api-orchestrator
kubectl logs -f deployment/backend -n api-orchestrator
```

## Manual Deployment

### Backend Setup
```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend with Gunicorn
gunicorn src.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### Frontend Build
```bash
cd frontend
npm install
npm run build

# Serve with Nginx
cp -r dist/* /var/www/html/
```

### Supervisor Configuration
```ini
# /etc/supervisor/conf.d/api-orchestrator.conf
[program:api-orchestrator]
command=/opt/api-orchestrator/venv/bin/gunicorn src.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/opt/api-orchestrator
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/api-orchestrator/app.log
environment=PATH="/opt/api-orchestrator/venv/bin",DATABASE_URL="postgresql://..."
```

## SSL/TLS Configuration

### Using Let's Encrypt with Certbot
```bash
# Install Certbot
apt-get update
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d api-orchestrator.com -d www.api-orchestrator.com

# Auto-renewal
certbot renew --dry-run
```

### Manual SSL Configuration
```nginx
# /etc/nginx/sites-available/api-orchestrator
server {
    listen 443 ssl http2;
    server_name api-orchestrator.com;

    ssl_certificate /etc/ssl/certs/api-orchestrator.crt;
    ssl_certificate_key /etc/ssl/private/api-orchestrator.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring & Logging

### Prometheus Metrics
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'api-orchestrator'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### ELK Stack Integration
```bash
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/api-orchestrator/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
```

### Health Monitoring
```bash
# Health check script
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $response -eq 200 ]; then
    echo "API is healthy"
else
    echo "API is unhealthy"
    # Send alert
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
      -H 'Content-Type: application/json' \
      -d '{"text":"API Orchestrator is down!"}'
fi
```

## Backup & Recovery

### Database Backup
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="api_orchestrator"

# Create backup
docker-compose exec -T postgres pg_dump -U orchestrator $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql.gz s3://your-bucket/backups/
```

### Restore from Backup
```bash
# Restore database
gunzip < backup_20240101_120000.sql.gz | docker-compose exec -T postgres psql -U orchestrator api_orchestrator
```

## Scaling

### Horizontal Scaling
```bash
# Scale backend workers
docker-compose up -d --scale backend=5

# Load balancer configuration (nginx)
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

### Vertical Scaling
```yaml
# docker-compose.yml resource limits
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Redis Cluster
```bash
# Setup Redis cluster for caching
docker run -d --name redis-master redis:7-alpine
docker run -d --name redis-slave1 redis:7-alpine redis-server --slaveof redis-master 6379
docker run -d --name redis-slave2 redis:7-alpine redis-server --slaveof redis-master 6379
```

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Test connection
docker-compose exec backend python -c "from src.database import engine; engine.connect()"
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart backend

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL
```

#### Slow Performance
```bash
# Enable query logging
export DB_ECHO=true
docker-compose restart backend

# Check slow queries
docker-compose exec postgres psql -U orchestrator -d api_orchestrator -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DB_ECHO=true
docker-compose up
```

### Container Logs
```bash
# View all logs
docker-compose logs

# Follow specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Enable rate limiting
- [ ] Setup CORS properly
- [ ] Regular security updates
- [ ] Enable audit logging
- [ ] Implement backup strategy
- [ ] Monitor for suspicious activity

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/api-orchestrator/issues
- Email: support@api-orchestrator.com
- Documentation: https://docs.api-orchestrator.com

## License

MIT License - See LICENSE file for details