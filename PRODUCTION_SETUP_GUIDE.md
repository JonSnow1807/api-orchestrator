# 🚀 StreamAPI Production Setup Guide

## ✅ DNS Status: ACTIVE
Your domains are properly configured and working:
- ✅ `streamapi.dev` → Railway app
- ✅ `www.streamapi.dev` → Railway app

## 📋 Required Environment Variables Setup

### Step 1: Add Core Security Variables (REQUIRED)

Go to Railway → Your Project → Web Service → Variables tab and add:

```bash
# CRITICAL - Add this first!
JWT_SECRET_KEY=gs9oxClUK-bZnBKGuoQKQvp2vr5FTOurwe4MiKdOh02IHfIzCruaDCwlfDSmGhM5RD8OUqYbsbKqbBcq9ZaRKQ

# Frontend URL (for email links)
FRONTEND_URL=https://streamapi.dev
```

### Step 2: Choose Email Provider (OPTIONAL but Recommended)

Pick ONE option below:

#### Option A: Gmail (Easiest for Testing)
```bash
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password  # NOT your regular password!
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=StreamAPI
```

**To get Gmail App Password:**
1. Enable 2FA on your Gmail account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"

#### Option B: SendGrid (Production Ready)
```bash
EMAIL_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your-sendgrid-api-key
EMAIL_FROM=noreply@streamapi.dev
EMAIL_FROM_NAME=StreamAPI
```

**To get SendGrid API Key:**
1. Sign up at https://sendgrid.com (100 emails/day free)
2. Settings → API Keys → Create API Key

### Step 3: Add Error Tracking (OPTIONAL but Recommended)

```bash
SENTRY_ENABLED=true
SENTRY_DSN=https://your-key@oXXXXXX.ingest.sentry.io/XXXXXXX
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**To get Sentry DSN:**
1. Sign up at https://sentry.io (5000 errors/month free)
2. Create new project (Python/FastAPI)
3. Settings → Projects → Client Keys (DSN)

### Step 4: AI API Keys (If Not Already Set)

```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
OPENAI_API_KEY=sk-xxxxx  # Optional, for GPT models
```

### Step 5: Stripe Configuration (For Payments)

```bash
STRIPE_SECRET_KEY=sk_live_xxxxx  # Or sk_test_xxxxx for testing
STRIPE_WEBHOOK_SECRET=whsec_xxxxx
STRIPE_PRICE_PREMIUM=price_xxxxx
STRIPE_PRICE_ENTERPRISE=price_xxxxx
```

## 🔄 After Adding Variables

Railway will automatically redeploy your app after adding variables.

## ✅ Verification Checklist

### 1. Test Website Access
- [ ] Visit https://streamapi.dev - Should load the app
- [ ] Visit https://www.streamapi.dev - Should also work

### 2. Test Core Features
- [ ] Register a new account
- [ ] Login with the account
- [ ] Create a test project
- [ ] Try API discovery on sample code

### 3. Test Email (if configured)
- [ ] Click "Forgot Password" on login page
- [ ] Enter your email
- [ ] Check if reset email arrives

### 4. Test Error Tracking (if configured)
- [ ] Check Sentry dashboard for any errors
- [ ] Errors should appear within seconds

## 🎯 Priority Order

1. **MUST DO NOW:**
   - Add `JWT_SECRET_KEY` (security critical!)
   - Add `FRONTEND_URL`

2. **SHOULD DO SOON:**
   - Configure email (for password resets)
   - Add Sentry (to catch errors)

3. **CAN DO LATER:**
   - Set up Stripe (when ready for payments)
   - Configure backups (Railway has auto-backups)

## 📊 Current Status

| Component | Status | Action Required |
|-----------|--------|-----------------|
| Domain (streamapi.dev) | ✅ Working | None |
| PostgreSQL | ✅ Connected | None |
| JWT Security | ⚠️ Needs Key | Add JWT_SECRET_KEY |
| Email System | ⚠️ Disabled | Add SMTP settings |
| Error Tracking | ⚠️ Disabled | Add Sentry DSN |
| AI Features | ❓ Check | Verify API keys set |
| Backups | ✅ Auto (Railway) | None |

## 🆘 Troubleshooting

### Site not loading?
- Check Railway logs for errors
- Verify all required variables are set
- Ensure PostgreSQL is running

### Email not working?
- Check EMAIL_ENABLED=true
- Verify SMTP credentials
- For Gmail: Must use App Password, not regular password

### Errors not in Sentry?
- Check SENTRY_ENABLED=true
- Verify SENTRY_DSN is correct
- Check Sentry dashboard filters

## 📞 Next Steps

1. **Add the required environment variables** (Step 1 above)
2. **Test the site** at https://streamapi.dev
3. **Configure email** for password resets
4. **Set up Sentry** to monitor errors
5. **Start using StreamAPI!**

---

**Need the individual guides?**
- Email setup: `email_setup_guide.md`
- Sentry setup: `sentry_setup_guide.md`
- Backup info: `backup_strategy.md`
- PostgreSQL: `railway_postgres_setup.md`