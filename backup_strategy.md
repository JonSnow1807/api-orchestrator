# StreamAPI Backup Strategy

## Overview
Comprehensive backup strategy for StreamAPI production data and configurations.

## What Needs Backing Up

### 1. PostgreSQL Database (Critical)
- User accounts and authentication
- Projects and API configurations
- Test results and history
- Mock server configurations
- Subscription and billing data

### 2. Environment Variables (Critical)
- API keys (Anthropic, OpenAI)
- JWT secret keys
- Stripe keys
- Database URLs
- SMTP credentials

### 3. Generated Content (Important)
- OpenAPI specifications
- Test suites
- Mock server data
- Export files

## Backup Solutions

### Option 1: Railway Built-in (Automatic)
Railway provides automatic backups for PostgreSQL:

**Features:**
- Daily automatic backups
- 7-day retention
- Point-in-time recovery
- One-click restore

**How to Access:**
1. Go to Railway dashboard
2. Click on PostgreSQL service
3. Go to "Backups" tab
4. View/restore backups

**Status:** ✅ Already Active (if using Railway PostgreSQL)

### Option 2: Manual Database Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
# Database Backup Script

# Configuration
BACKUP_DIR="/app/backups"
DB_URL="${DATABASE_URL}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE}.sql"

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Perform backup
pg_dump ${DB_URL} > ${BACKUP_FILE}

# Compress backup
gzip ${BACKUP_FILE}

# Upload to cloud storage (optional)
# aws s3 cp ${BACKUP_FILE}.gz s3://streamapi-backups/

# Keep only last 7 days of local backups
find ${BACKUP_DIR} -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Option 3: Automated Cloud Backup

**Using GitHub Actions for daily backups:**

Create `.github/workflows/backup.yml`:
```yaml
name: Daily Backup

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Install PostgreSQL client
      run: sudo apt-get install -y postgresql-client
    
    - name: Backup database
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
      run: |
        DATE=$(date +%Y%m%d_%H%M%S)
        pg_dump $DATABASE_URL > backup_${DATE}.sql
        gzip backup_${DATE}.sql
    
    - name: Upload to GitHub Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: database-backup-${{ github.run_number }}
        path: backup_*.sql.gz
        retention-days: 30
    
    - name: Upload to S3 (optional)
      env:
        AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
        AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      run: |
        aws s3 cp backup_*.sql.gz s3://streamapi-backups/
```

## Restore Procedures

### Restore from Railway Backup
1. Go to PostgreSQL service in Railway
2. Click "Backups" tab
3. Select backup to restore
4. Click "Restore"
5. Confirm restoration

### Restore from Manual Backup
```bash
# Decompress backup
gunzip backup_20240101_120000.sql.gz

# Restore to database
psql $DATABASE_URL < backup_20240101_120000.sql
```

### Restore Environment Variables
1. Keep a secure copy of `.env.production` file
2. Store in password manager or secure vault
3. Never commit to git repository

## Backup Schedule

| Component | Frequency | Method | Retention |
|-----------|-----------|---------|-----------|
| PostgreSQL | Daily | Railway Auto | 7 days |
| PostgreSQL | Weekly | GitHub Actions | 30 days |
| Environment Vars | On Change | Manual | Forever |
| Code | On Commit | Git | Forever |

## Disaster Recovery Plan

### Scenario 1: Database Corruption
1. Stop application to prevent further damage
2. Restore from most recent Railway backup
3. If Railway backup fails, restore from GitHub Actions backup
4. Verify data integrity
5. Resume service

### Scenario 2: Complete Railway Failure
1. Deploy to alternative platform (Render, Heroku, DigitalOcean)
2. Restore database from GitHub Actions backup
3. Apply environment variables from secure storage
4. Update DNS to point to new deployment
5. Resume service

### Scenario 3: Security Breach
1. Immediately rotate all API keys and secrets
2. Reset all user passwords
3. Review audit logs for breach extent
4. Restore clean database backup from before breach
5. Notify affected users
6. Implement additional security measures

## Testing Backups

**Monthly Backup Test Procedure:**
1. Create test database instance
2. Restore latest backup to test instance
3. Verify data integrity:
   - User count matches
   - Recent projects present
   - API configurations intact
4. Document test results
5. Delete test instance

## Monitoring

### Set up alerts for:
- Backup failure (GitHub Actions)
- Database size > 80% of limit
- Backup age > 24 hours
- Storage space low

### Use monitoring tools:
- Railway dashboard for database metrics
- GitHub Actions for backup job status
- Sentry for application errors during backup

## Implementation Checklist

- [ ] Enable Railway PostgreSQL backups (automatic)
- [ ] Set up GitHub Actions backup workflow
- [ ] Create secure storage for environment variables
- [ ] Document restore procedures
- [ ] Test backup restoration
- [ ] Set up monitoring alerts
- [ ] Schedule monthly backup tests

## Cost Considerations

### Free/Included:
- Railway daily backups (included with PostgreSQL)
- GitHub Actions (2000 minutes/month free)
- GitHub Artifacts (500MB free)

### Potential Costs:
- S3 storage: ~$0.023/GB/month
- Extended retention: varies by provider
- Additional backup destinations

## Recommendations

For StreamAPI production:
1. **Use Railway's built-in backups** as primary
2. **Add GitHub Actions backup** as secondary
3. **Store env vars in password manager**
4. **Test restoration monthly**
5. **Monitor backup success daily**

## Current Status

⚠️ **Partial Coverage**

- ✅ Railway PostgreSQL backups (if using PostgreSQL)
- ⚠️ GitHub Actions backup (needs setup)
- ⚠️ Environment variable backup (manual)
- ✅ Code backup (via Git)

**Next Steps:**
1. Confirm Railway PostgreSQL backups are active
2. Set up GitHub Actions workflow
3. Document environment variables securely
4. Schedule first backup test