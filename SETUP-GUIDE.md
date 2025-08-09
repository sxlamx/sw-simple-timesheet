# 🚀 Simple Timesheet - Service Provider Setup Guide

This guide will help you configure the Simple Timesheet application as a service provider with Google API integration.

## 🔑 Required Google API Setup

### Prerequisites
- Google Account with Google Cloud Console access
- Domain name (for production deployment)
- SMTP server access (for email notifications)

## Step 1: Google Cloud Console Configuration

### 1.1 Create Google Cloud Project
```bash
1. Go to https://console.cloud.google.com/
2. Create new project: "Simple Timesheet"
3. Note your PROJECT_ID
```

### 1.2 Enable Required APIs
Go to **APIs & Services** → **Library** and enable:
- ✅ **Google Sheets API**
- ✅ **Google Drive API**
- ✅ **Gmail API** (optional, for notifications)
- ✅ **Google OAuth2 API** (automatically enabled)

### 1.3 Create OAuth 2.0 Web Client
1. **APIs & Services** → **Credentials** → **+ CREATE CREDENTIALS** → **OAuth 2.0 Client IDs**
2. **Application type**: Web application
3. **Name**: `Simple Timesheet Web Client`
4. **Authorized JavaScript origins**:
   ```
   Development: http://localhost:5185
   Production:  https://yourdomain.com
   ```
5. **Authorized redirect URIs**:
   ```
   Development: http://localhost:5185/auth/callback
   Production:  https://yourdomain.com/auth/callback
   ```
6. **Save and copy the Client ID** → Use in frontend `.env`

### 1.4 Create Service Account
1. **APIs & Services** → **Credentials** → **+ CREATE CREDENTIALS** → **Service account**
2. **Name**: `simple-timesheet-service`
3. **Role**: Editor (or custom role with Sheets/Drive access)
4. **Create Key** → **JSON** → Download the file
5. **Rename** downloaded file to `service-account-key.json`

## Step 2: Configure Application Environment

### 2.1 Backend Configuration
Update `/backend/.env.development`:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_oauth_client_id_from_step_1.3
GOOGLE_CLIENT_SECRET=your_oauth_client_secret_from_step_1.3
GOOGLE_REDIRECT_URI=http://localhost:8095/api/v1/auth/callback

# Google Sheets API
GOOGLE_SHEETS_CREDENTIALS_FILE=/app/credentials/service-account-key.json

# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL=sqlite:///./db/timesheet.db

# CORS Settings
CORS_ORIGINS=http://localhost:5185,https://yourdomain.com

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Debug
DEBUG=True
```

### 2.2 Frontend Configuration  
Update `/frontend/.env.development`:

```env
VITE_API_URL=http://localhost:8095
VITE_APP_NAME=Simple Timesheet
VITE_GOOGLE_CLIENT_ID=your_oauth_client_id_from_step_1.3
```

### 2.3 Place Service Account Key
```bash
# Copy your downloaded JSON key file to:
cp ~/Downloads/service-account-key.json /path/to/simple-timesheet/backend/credentials/
```

## Step 3: Google Sheets Template Setup

### 3.1 Create Master Template Sheet
1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new sheet named: "Timesheet Template"
3. Set up columns:
   ```
   A: Date | B: Start Time | C: End Time | D: Break (hrs) | E: Total Hours | F: Task/Project | G: Notes
   ```
4. **Share with service account email** (from your JSON key file):
   - Click **Share** 
   - Add the service account email (e.g., `simple-timesheet-service@yourproject.iam.gserviceaccount.com`)
   - Give **Editor** permissions

### 3.2 Configure Sheet Permissions
The service account needs access to:
- Create new Google Sheets
- Read/write to user's Google Drive (with user consent)
- Access shared template sheets

## Step 4: User Account Setup

### 4.1 Create Supervisor Account
1. Start the application: `./scripts/dev-start.sh`
2. Go to `http://localhost:5185`
3. Login with Google using a supervisor account
4. **Manually update database** to set supervisor role:
   ```sql
   -- Connect to SQLite database
   sqlite3 backend/db/timesheet.db
   
   -- Update user to supervisor
   UPDATE users SET is_supervisor = 1 WHERE email = 'supervisor@yourdomain.com';
   
   -- Verify
   SELECT * FROM users;
   ```

### 4.2 Create Staff Accounts
Staff members can self-register by:
1. Going to `http://localhost:5185`
2. Clicking "Login with Google"
3. Completing OAuth flow
4. They will be automatically created as staff users

## Step 5: Production Deployment Setup

### 5.1 Production Environment Files
Create production environment files:

**`/backend/.env.production`:**
```env
GOOGLE_CLIENT_ID=your_prod_oauth_client_id
GOOGLE_CLIENT_SECRET=your_prod_oauth_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/auth/callback
GOOGLE_SHEETS_CREDENTIALS_FILE=/app/credentials/prod-service-account-key.json
SECRET_KEY=your-super-secure-production-secret-key
DATABASE_URL=postgresql://user:pass@localhost/timesheet_prod  # or SQLite
CORS_ORIGINS=https://yourdomain.com
DEBUG=False
```

**`/frontend/.env.production`:**
```env
VITE_API_URL=https://yourdomain.com/api
VITE_APP_NAME=Simple Timesheet
VITE_GOOGLE_CLIENT_ID=your_prod_oauth_client_id
```

### 5.2 Deploy with Docker
```bash
# Build and start production
./scripts/staging-start.sh

# Or manually:
docker-compose -f docker-compose.staging.yml up -d
```

## Step 6: Testing Setup

### 6.1 Test Authentication
```bash
# Run test suite
npm install axios
node run-tests.js
```

### 6.2 Test Google Sheets Integration
1. Login as staff user
2. Create a timesheet for current month
3. Add some time entries
4. Submit for approval
5. Check that Google Sheet is created in user's Drive

### 6.3 Test Supervisor Functions
1. Login as supervisor
2. Review pending timesheets
3. Approve/reject timesheets
4. View team analytics
5. Export team data

## 🔧 Troubleshooting

### Common Issues:

**❌ "Access blocked" during OAuth**
- Check redirect URIs in Google Console
- Ensure JavaScript origins are correct
- Verify OAuth client type is "Web application"

**❌ "Service account not found"**
- Check service account JSON file path
- Verify file permissions in Docker container
- Ensure service account has required API access

**❌ "Insufficient permissions for Google Sheets"**
- Share template sheet with service account email
- Grant Editor permissions to service account
- Check Google Sheets API is enabled

**❌ "CORS errors in browser"**
- Update CORS_ORIGINS in backend .env
- Restart backend container after changes
- Check frontend URL matches CORS settings

### Debug Commands:
```bash
# Check container logs
docker-compose -f docker-compose.dev.yml logs

# Test API endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8095/api/v1/users/me

# Check database
sqlite3 backend/db/timesheet.db ".tables"
```

## 🚀 Go Live Checklist

Before deploying to production:

- ✅ Google APIs enabled and configured
- ✅ OAuth client configured with production URLs
- ✅ Service account created with proper permissions
- ✅ Production environment files created
- ✅ SSL certificate configured for HTTPS
- ✅ Domain DNS pointed to your server
- ✅ Backup strategy for database
- ✅ Monitoring and logging configured
- ✅ Email notifications tested
- ✅ All test scripts passing

## 📞 Support

For additional help:
1. Check the main README.md file
2. Review test scripts output: `node run-tests.js`
3. Check application logs: `docker-compose logs`
4. Verify Google Cloud Console API quotas and usage

---

**🎉 Congratulations!** Your Simple Timesheet service is now configured and ready for users!