# Email Configuration Guide for StreamAPI

## Overview
StreamAPI uses SMTP for sending transactional emails like password resets and welcome messages.

## Quick Setup Options

### Option 1: Gmail (Recommended for Testing)
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and generate a password
3. **Add to Railway**:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAIL_FROM=your-email@gmail.com
   EMAIL_FROM_NAME=StreamAPI
   EMAIL_ENABLED=true
   ```

### Option 2: SendGrid (Production Ready)
1. **Sign up** at https://sendgrid.com (free tier: 100 emails/day)
2. **Create API Key** in Settings → API Keys
3. **Add to Railway**:
   ```
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   EMAIL_FROM=noreply@streamapi.dev
   EMAIL_FROM_NAME=StreamAPI
   EMAIL_ENABLED=true
   ```

### Option 3: Postmark (Best Deliverability)
1. **Sign up** at https://postmarkapp.com
2. **Get SMTP credentials** from Servers → Default → SMTP
3. **Add to Railway**:
   ```
   SMTP_HOST=smtp.postmarkapp.com
   SMTP_PORT=587
   SMTP_USERNAME=your-postmark-token
   SMTP_PASSWORD=your-postmark-token
   EMAIL_FROM=noreply@streamapi.dev
   EMAIL_FROM_NAME=StreamAPI
   EMAIL_ENABLED=true
   ```

### Option 4: Amazon SES (Scalable)
1. **Set up SES** in AWS Console
2. **Create SMTP credentials**
3. **Add to Railway**:
   ```
   SMTP_HOST=email-smtp.us-east-1.amazonaws.com
   SMTP_PORT=587
   SMTP_USERNAME=your-ses-username
   SMTP_PASSWORD=your-ses-password
   EMAIL_FROM=noreply@streamapi.dev
   EMAIL_FROM_NAME=StreamAPI
   EMAIL_ENABLED=true
   ```

## Railway Configuration Steps

1. **Go to your Railway project**
2. **Click on your web service**
3. **Go to Variables tab**
4. **Add the email variables** from your chosen provider above
5. **Railway will auto-redeploy**

## Testing Email Setup

Once configured, test the email system:

1. **Go to the login page**
2. **Click "Forgot Password"**
3. **Enter a registered email**
4. **Check if you receive the reset email**

## Troubleshooting

### Emails not sending?
- Check Railway logs for error messages
- Verify EMAIL_ENABLED=true
- Ensure all SMTP variables are set correctly
- For Gmail: Make sure you're using App Password, not regular password

### Gmail specific issues:
- Enable "Less secure app access" (not recommended for production)
- Or better: Use App Passwords with 2FA

### SendGrid/Postmark issues:
- Verify your domain if using custom FROM address
- Check if you're within rate limits

## Production Recommendations

For production, we recommend:
1. **SendGrid** or **Postmark** for reliability
2. **Verify your domain** for better deliverability
3. **Set up SPF/DKIM records** in your DNS
4. **Monitor bounce rates** and adjust

## Current Status

⚠️ **Email is currently DISABLED** 

To enable, add the SMTP configuration to Railway environment variables as shown above.