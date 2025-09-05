# 🚀 API Orchestrator - Automated Deployment Guide

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Automated CI/CD](#automated-cicd)
- [Cloud Providers](#cloud-providers)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🎯 Quick Start

### One-Click Deployment

```bash
# Make script executable
chmod +x deploy/one-click-deploy.sh

# Run the deployment wizard
./deploy/one-click-deploy.sh
```

This will guide you through deploying to:
- DigitalOcean
- AWS EC2
- Railway (Easiest - No server needed)
- Render (Free tier available)
- Local Docker
- And more!

## 🔄 Automated CI/CD

### GitHub Actions Setup

1. **Fork/Clone the repository**
2. **Enable GitHub Actions** in your repository
3. **Add secrets** to your repository:

```bash
# Required secrets for automated deployment
gh secret set VPS_HOST        # Your server IP
gh secret set VPS_USER        # SSH username (usually 'root' or 'ubuntu')
gh secret set VPS_SSH_KEY     # Private SSH key
gh secret set ANTHROPIC_API_KEY  # For AI features
gh secret set SECRET_KEY      # Django secret key (auto-generated)
```

4. **Push to main branch** - Deployment happens automatically!

## 🌐 Deployment Options

### 1. Railway (Easiest - Recommended for beginners)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up

# Your app is live! 🎉
```

**Pros:**
- No server management
- Automatic SSL
- Built-in database
- GitHub integration
- $5 free credits

### 2. DigitalOcean ($6/month)

```bash
# Using our script
./deploy/one-click-deploy.sh
# Select option 1

# Or manually
doctl compute droplet create api-orchestrator \
  --image docker-20-04 \
  --size s-1vcpu-1gb \
  --region nyc1
```

### 3. AWS EC2 (Free tier eligible)

```bash
# Using our script
./deploy/one-click-deploy.sh
# Select option 2

# Or use AWS CLI
aws ec2 run-instances \
  --image-id ami-0c94855ba95c574c8 \
  --instance-type t2.micro
```

### 4. Render (Free tier)

```bash
# Create account at render.com
# Connect GitHub repo
# Render auto-deploys on push!
```

### 5. Local Docker

```bash
# Simple local deployment
docker-compose up -d

# Production deployment
docker-compose -f deploy/docker-compose.prod.yml up -d
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```env
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Optional (for AI features)
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# Email (for password reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Domain (for production)
DOMAIN=api-orchestrator.com
CORS_ORIGINS=https://api-orchestrator.com
```

### SSL Setup (Automatic)

```bash
# Our deploy script handles SSL automatically
DOMAIN=yourdomain.com ./deploy/deploy.sh

# Or manually with certbot
certbot --nginx -d yourdomain.com
```

## 📊 Monitoring

### Health Checks

```bash
# Check service status
curl https://your-domain.com/health

# View logs
docker-compose logs -f

# Monitor resources
docker stats
```

### Automated Monitoring

The deployment script sets up:
- Health checks every 5 minutes
- Auto-restart on failure
- Daily backups at 2 AM
- Log rotation

### Monitoring Dashboard

```bash
# Grafana + Prometheus (optional)
docker-compose -f deploy/docker-compose.monitoring.yml up -d
# Access at http://your-domain:3000
```

## 🔧 Common Tasks

### Update Application

```bash
# Automated via CI/CD (just push to main)
git push origin main

# Or manually
ssh user@your-server
cd /opt/api-orchestrator
git pull
docker-compose -f deploy/docker-compose.prod.yml up -d --build
```

### Backup Database

```bash
# Automated daily backups
# Or manually
docker exec postgres pg_dump -U postgres api_orchestrator > backup.sql
```

### Scale Application

```bash
# Increase workers
docker-compose -f deploy/docker-compose.prod.yml up -d --scale backend=3
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100
```

## 🚨 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs backend

# Common fixes
docker-compose down
docker system prune -a
docker-compose up -d
```

### Database connection issues

```bash
# Check PostgreSQL
docker exec -it postgres psql -U postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

### Port already in use

```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### SSL certificate issues

```bash
# Renew certificate
certbot renew --nginx

# Force renewal
certbot renew --nginx --force-renewal
```

## 🔐 Security

### Firewall Setup

```bash
# Allow only necessary ports
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### Secure Headers

Already configured in nginx.conf:
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Content-Security-Policy

### Regular Updates

```bash
# Auto-updates enabled in deployment
# Manual update
apt update && apt upgrade -y
docker pull ghcr.io/jonsnow1807/api-orchestrator:latest
```

## 📈 Performance Optimization

### Caching

Redis is automatically configured for:
- Session storage
- API response caching
- Task queue

### CDN Setup (Optional)

```bash
# Cloudflare (recommended)
# 1. Add site to Cloudflare
# 2. Update DNS
# 3. Enable proxy
```

### Database Optimization

```sql
-- Auto-created indexes
-- Additional indexes for performance
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_project_user ON projects(user_id);
```

## 🆘 Support

### Getting Help

1. Check logs: `docker-compose logs`
2. Review this guide
3. Check [GitHub Issues](https://github.com/JonSnow1807/api-orchestrator/issues)
4. Create new issue if needed

### Quick Fixes

```bash
# Reset everything
docker-compose down -v
docker system prune -a
./deploy/deploy.sh

# Check disk space
df -h

# Check memory
free -h

# Restart services
docker-compose restart
```

## 🎉 Success Checklist

- [ ] Application accessible at your domain
- [ ] SSL certificate active (https://)
- [ ] Can register/login
- [ ] Can create projects
- [ ] WebSocket real-time updates working
- [ ] API documentation at /docs
- [ ] Monitoring active
- [ ] Backups configured

---

## 📝 Notes

- **First deployment** takes ~5-10 minutes
- **Subsequent deployments** via CI/CD take ~2-3 minutes
- **Free tier options**: Railway ($5 credits), Render (free plan)
- **Production recommended**: DigitalOcean ($6/mo) or AWS EC2

## 🚀 Ready to Deploy?

```bash
chmod +x deploy/one-click-deploy.sh
./deploy/one-click-deploy.sh
```

**That's it!** Your API Orchestrator will be live in minutes! 🎊