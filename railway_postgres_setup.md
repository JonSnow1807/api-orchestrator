# PostgreSQL Setup Instructions for Railway

## Step 1: Add PostgreSQL to Railway

### 🔴 ACTION REQUIRED FROM YOU:

1. **Go to your Railway project dashboard**
2. **Click "New" → "Database" → "Add PostgreSQL"**
3. **Wait for PostgreSQL to provision** (takes ~30 seconds)
4. **Click on the PostgreSQL service**
5. **Go to "Variables" tab**
6. **Copy the `DATABASE_URL`** - it looks like:
   ```
   postgresql://postgres:PASSWORD@HOST.railway.app:PORT/railway
   ```

## Step 2: Add Database URL to Your App

7. **Go back to your web service** (web-production-056c)
8. **Click "Variables" tab**
9. **Add the DATABASE_URL** you copied
10. **Railway will auto-redeploy**

## Step 3: Verify Connection

Once you've added the DATABASE_URL, the app will:
- Automatically detect PostgreSQL
- Create all tables
- Migrate from SQLite

## That's it! 

Your app will now use PostgreSQL instead of SQLite.

---

## Benefits You'll Get:
✅ Concurrent users supported
✅ Automatic backups by Railway
✅ Better performance
✅ No data corruption risk
✅ Scales with your app

## Important Notes:
- Keep SQLite as fallback (already configured)
- Old data will be preserved
- Zero downtime migration