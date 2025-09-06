# Sentry Error Tracking Setup for StreamAPI

## Overview
Sentry provides real-time error tracking and performance monitoring for your production application.

## Quick Setup (5 minutes)

### Step 1: Create Sentry Account
1. **Sign up** at https://sentry.io (free tier: 5,000 errors/month)
2. **Create a new project**:
   - Platform: Python
   - Framework: FastAPI
   - Project name: streamapi-backend

### Step 2: Get Your DSN
1. Go to **Settings → Projects → streamapi-backend**
2. Click **Client Keys (DSN)**
3. Copy the **DSN** - looks like:
   ```
   https://abc123@o123456.ingest.sentry.io/1234567
   ```

### Step 3: Add to Railway
1. **Go to your Railway project**
2. **Click on your web service**
3. **Go to Variables tab**
4. **Add these variables**:
   ```
   SENTRY_DSN=your-dsn-from-step-2
   SENTRY_ENVIRONMENT=production
   SENTRY_ENABLED=true
   SENTRY_TRACES_SAMPLE_RATE=0.1
   ```
5. **Railway will auto-redeploy**

## What Sentry Monitors

Once configured, Sentry will automatically track:

### Errors
- Unhandled exceptions
- API endpoint failures
- Database connection issues
- Authentication errors
- WebSocket disconnections

### Performance
- Slow API endpoints
- Database query performance
- External API call latency
- WebSocket message processing time

### User Context
- Which user triggered the error
- User's subscription tier
- Request parameters
- Browser/client information

## Testing Sentry Integration

### Create a test error:
```python
# Add this temporary endpoint to test Sentry
@app.get("/test-sentry")
def test_sentry():
    raise Exception("This is a test error for Sentry!")
```

Then visit: https://streamapi.dev/test-sentry

Check your Sentry dashboard - you should see the error within seconds.

## Sentry Dashboard Features

### Alerts
Set up alerts for:
- Error rate spikes
- New error types
- Performance degradation
- Specific user issues

### Release Tracking
Track errors by deployment:
```
SENTRY_RELEASE=v1.0.0
```

### Issue Assignment
- Assign errors to team members
- Track resolution status
- Link to GitHub issues

## Advanced Configuration

### Custom Error Context
```python
import sentry_sdk

# Add custom context to errors
sentry_sdk.set_context("api_operation", {
    "endpoint": "/api/orchestrate",
    "user_tier": "premium",
    "api_count": 150
})
```

### Performance Monitoring
```python
# Monitor specific operations
with sentry_sdk.start_transaction(op="api.discovery", name="API Discovery"):
    # Your code here
    pass
```

### User Feedback
Enable user feedback widget:
```javascript
// In frontend
Sentry.showReportDialog({
    eventId: error.eventId,
    user: {
        email: currentUser.email,
        name: currentUser.username
    }
});
```

## Best Practices

1. **Don't log sensitive data**:
   - Passwords
   - API keys
   - Credit card numbers
   - Personal information

2. **Use environments**:
   - `production` for live site
   - `staging` for testing
   - `development` for local

3. **Set sample rates**:
   - Start with 10% (0.1) for performance
   - Adjust based on volume

4. **Create alerts**:
   - Error rate > 1% 
   - New error types
   - Performance regression

## Current Status

⚠️ **Sentry is currently DISABLED**

To enable:
1. Create account at sentry.io
2. Get your DSN
3. Add to Railway environment variables
4. Set SENTRY_ENABLED=true

## Free Tier Limits

Sentry free tier includes:
- 5,000 errors/month
- 10,000 performance events
- 1GB attachments
- 30-day data retention
- Unlimited users

For StreamAPI's current scale, the free tier should be sufficient.