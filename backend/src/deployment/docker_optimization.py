"""
Docker Optimization and Multi-stage Build Configuration
Advanced Docker optimization for production deployments
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DockerConfig:
    """Docker build configuration"""
    app_name: str = "api-orchestrator"
    python_version: str = "3.11"
    node_version: str = "18"
    base_image: str = "python:3.11-slim"
    final_image: str = "gcr.io/distroless/python3"

    # Build optimizations
    use_multi_stage: bool = True
    use_distroless: bool = True
    use_buildkit: bool = True

    # Security options
    run_as_non_root: bool = True
    user_id: int = 1000
    group_id: int = 1000

class DockerfileGenerator:
    """Generate optimized Dockerfiles for different environments"""

    def __init__(self, config: DockerConfig):
        self.config = config

    def generate_production_dockerfile(self) -> str:
        """Generate production-optimized Dockerfile"""
        if self.config.use_multi_stage and self.config.use_distroless:
            return self._generate_distroless_multistage()
        elif self.config.use_multi_stage:
            return self._generate_multistage()
        else:
            return self._generate_simple()

    def _generate_distroless_multistage(self) -> str:
        """Generate multi-stage Dockerfile with distroless final image"""
        return f'''# syntax=docker/dockerfile:1.4
# Build stage
FROM {self.config.base_image} AS builder

# Set build arguments
ARG BUILDKIT_INLINE_CACHE=1
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g {self.config.group_id} appgroup && \\
    useradd -u {self.config.user_id} -g appgroup -m appuser

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .

# Build application (if needed)
RUN python -m compileall . -b && \\
    find . -name "*.py" -delete && \\
    find . -name "__pycache__" -exec rm -rf {{}} + || true

# Production stage
FROM {self.config.final_image}

# Install runtime dependencies
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy Python packages and application
COPY --from=builder --chown={self.config.user_id}:{self.config.group_id} /root/.local /home/appuser/.local
COPY --from=builder --chown={self.config.user_id}:{self.config.group_id} /app /app

# Set environment variables
ENV PATH="/home/appuser/.local/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PORT=8000

# Switch to non-root user
USER {self.config.user_id}:{self.config.group_id}

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE $PORT

# Run application
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
'''

    def _generate_multistage(self) -> str:
        """Generate multi-stage Dockerfile with slim final image"""
        return f'''# syntax=docker/dockerfile:1.4
# Build stage
FROM {self.config.base_image} AS builder

ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir --target /app/dependencies -r requirements.txt

# Copy and prepare application
COPY . .
RUN python -m compileall . -b

# Production stage
FROM {self.config.base_image}

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get autoremove -y \\
    && apt-get clean

# Create non-root user
RUN groupadd -g {self.config.group_id} appgroup && \\
    useradd -u {self.config.user_id} -g appgroup -m -s /bin/bash appuser

# Copy dependencies and application
COPY --from=builder --chown=appuser:appgroup /app/dependencies /app/dependencies
COPY --from=builder --chown=appuser:appgroup /app /app

# Set environment variables
ENV PYTHONPATH="/app:/app/dependencies"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Switch to non-root user
USER appuser

# Set working directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE $PORT

# Run application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    def _generate_simple(self) -> str:
        """Generate simple optimized Dockerfile"""
        return f'''# syntax=docker/dockerfile:1.4
FROM {self.config.base_image}

ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Create non-root user
RUN groupadd -g {self.config.group_id} appgroup && \\
    useradd -u {self.config.user_id} -g appgroup -m appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appgroup . .

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE $PORT

# Run application
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    def generate_frontend_dockerfile(self) -> str:
        """Generate optimized Dockerfile for frontend"""
        return f'''# syntax=docker/dockerfile:1.4
# Build stage
FROM node:{self.config.node_version}-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g {self.config.group_id} appgroup && \\
    adduser -D -u {self.config.user_id} -G appgroup appuser

# Set ownership
RUN chown -R appuser:appgroup /usr/share/nginx/html /var/cache/nginx /var/run /var/log/nginx

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
'''

    def generate_dockerignore(self) -> str:
        """Generate .dockerignore file"""
        return '''# Git
.git
.gitignore
.gitattributes

# Documentation
README.md
*.md
docs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Testing
.coverage
.pytest_cache/
.tox/
.nox/
htmlcov/
.coverage.*
coverage.xml
*.cover
*.py,cover
.hypothesis/

# Jupyter
.ipynb_checkpoints

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Frontend build
frontend/dist/
frontend/.next/
frontend/out/

# Logs
logs/
*.log

# Database
*.db
*.sqlite

# Temporary files
tmp/
temp/
.tmp

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# Kubernetes
k8s-manifests*/
*.yaml
*.yml

# CI/CD
.github/
.gitlab-ci.yml
.travis.yml

# Misc
.cache/
.sass-cache/
'''

class DockerComposeGenerator:
    """Generate Docker Compose configurations"""

    def __init__(self, config: DockerConfig):
        self.config = config

    def generate_production_compose(self) -> str:
        """Generate production Docker Compose configuration"""
        return f'''version: '3.8'

services:
  {self.config.app_name}:
    build:
      context: .
      dockerfile: Dockerfile.prod
      cache_from:
        - {self.config.app_name}:latest
    image: {self.config.app_name}:latest
    container_name: {self.config.app_name}
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${{DATABASE_URL}}
      - REDIS_URL=${{REDIS_URL}}
      - SECRET_KEY=${{SECRET_KEY}}
      - ENVIRONMENT=production
    depends_on:
      - postgres
      - redis
    networks:
      - app-network
    volumes:
      - app-logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID

  postgres:
    image: postgres:15-alpine
    container_name: {self.config.app_name}-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=api_orchestrator
      - POSTGRES_USER=${{POSTGRES_USER}}
      - POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - app-network
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER}} -d api_orchestrator"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: {self.config.app_name}-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - app-network
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M

  nginx:
    image: nginx:alpine
    container_name: {self.config.app_name}-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - nginx-cache:/var/cache/nginx
    depends_on:
      - {self.config.app_name}
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: {self.config.app_name}-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    container_name: {self.config.app_name}-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${{GRAFANA_PASSWORD}}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  app-logs:
    driver: local
  nginx-cache:
    driver: local
  prometheus-data:
    driver: local
  grafana-data:
    driver: local
'''

    def generate_development_compose(self) -> str:
        """Generate development Docker Compose configuration"""
        return f'''version: '3.8'

services:
  {self.config.app_name}:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: {self.config.app_name}-dev
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/api_orchestrator
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=dev-secret-key
      - ENVIRONMENT=development
      - DEBUG=true
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - dev-network
    command: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    container_name: {self.config.app_name}-postgres-dev
    environment:
      - POSTGRES_DB=api_orchestrator
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres-dev-data:/var/lib/postgresql/data
    networks:
      - dev-network
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: {self.config.app_name}-redis-dev
    networks:
      - dev-network
    ports:
      - "6379:6379"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: {self.config.app_name}-frontend-dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - dev-network
    command: npm run dev

networks:
  dev-network:
    driver: bridge

volumes:
  postgres-dev-data:
    driver: local
'''

def generate_nginx_config() -> str:
    """Generate optimized Nginx configuration"""
    return '''worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Buffer settings
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_comp_level 6;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_types
        application/atom+xml
        application/javascript
        application/json
        application/ld+json
        application/manifest+json
        application/rss+xml
        application/vnd.geo+json
        application/vnd.ms-fontobject
        application/x-font-ttf
        application/x-web-app-manifest+json
        application/xhtml+xml
        application/xml
        font/opentype
        image/bmp
        image/svg+xml
        image/x-icon
        text/cache-manifest
        text/css
        text/plain
        text/vcard
        text/vnd.rim.location.xloc
        text/vtt
        text/x-component
        text/x-cross-domain-policy;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # API server
    upstream api_backend {
        least_conn;
        server api-orchestrator:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Main server block
    server {
        listen 80;
        server_name _;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Auth routes with stricter rate limiting
        location /auth/ {
            limit_req zone=login burst=5 nodelay;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            proxy_pass http://api_backend;
            access_log off;
        }

        # Static files (if serving frontend)
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;

            # Cache static assets
            location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }
    }
}'''

def main():
    """Generate all deployment configurations"""
    config = DockerConfig(
        app_name="api-orchestrator",
        use_multi_stage=True,
        use_distroless=True,
        run_as_non_root=True
    )

    # Create output directory
    output_dir = Path("deployment-configs")
    output_dir.mkdir(exist_ok=True)

    # Generate Dockerfiles
    dockerfile_generator = DockerfileGenerator(config)

    # Production Dockerfile
    with open(output_dir / "Dockerfile.prod", "w") as f:
        f.write(dockerfile_generator.generate_production_dockerfile())

    # Frontend Dockerfile
    with open(output_dir / "Dockerfile.frontend", "w") as f:
        f.write(dockerfile_generator.generate_frontend_dockerfile())

    # .dockerignore
    with open(output_dir / ".dockerignore", "w") as f:
        f.write(dockerfile_generator.generate_dockerignore())

    # Generate Docker Compose files
    compose_generator = DockerComposeGenerator(config)

    # Production compose
    with open(output_dir / "docker-compose.prod.yml", "w") as f:
        f.write(compose_generator.generate_production_compose())

    # Development compose
    with open(output_dir / "docker-compose.dev.yml", "w") as f:
        f.write(compose_generator.generate_development_compose())

    # Generate Nginx config
    with open(output_dir / "nginx.conf", "w") as f:
        f.write(generate_nginx_config())

    print("✅ Docker deployment configurations generated successfully!")
    print(f"📁 Files saved to: {output_dir}")
    print("\nGenerated files:")
    print("  - Dockerfile.prod (Production optimized)")
    print("  - Dockerfile.frontend (Frontend optimized)")
    print("  - docker-compose.prod.yml (Production stack)")
    print("  - docker-compose.dev.yml (Development stack)")
    print("  - nginx.conf (Optimized Nginx configuration)")
    print("  - .dockerignore (Build optimization)")

if __name__ == "__main__":
    main()