# 🚀 Simple Timesheet - Service Provider Setup Guide

This guide will help you configure the Simple Timesheet application as a service provider with Google API integration.

## 🔐 Understanding Google Authentication Types

### Two Types of Google Authentication

#### 1. **OAuth 2.0 Client (User Authentication)**
**Purpose**: Authenticates individual users who log into your timesheet application

**What it does**:
- Allows users to "Sign in with Google" 
- Grants access to user's Google account data (email, profile, Google Sheets in their Drive)
- Users see a consent screen asking for permissions
- Each user controls their own data

#### 2. **Service Account (Application Authentication)**  
**Purpose**: Authenticates your application itself to perform server-side operations

**What it does**:
- Allows your backend to access Google APIs without user interaction
- Used for creating shared templates, administrative tasks
- Operates with its own Google Drive account
- No user consent screens - operates automatically

### 🔄 Data Flow Architecture

#### User Authentication Flow:
```
Staff Member → OAuth Login → Google Consent → Access Token → Your App JWT
     ↓
Can create/edit their own Google Sheets
```

#### Service Account Flow:
```
Your Backend → Service Account Key → Google API Access → Administrative Operations
     ↓
Can create template sheets, send notifications, perform bulk operations
```

#### Timesheet Creation Flow:
```
1. Staff logs in (OAuth)
2. Clicks "Create Timesheet" 
3. Your backend (Service Account) copies template
4. New sheet created in staff member's Google Drive (using their OAuth token)
5. Staff fills out timesheet
6. Staff submits for approval
7. Supervisor reviews and approves/rejects
```

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

#### **Step-by-Step API Enabling Process:**

1. **Access Google Cloud Console**
   ```
   - Go to https://console.cloud.google.com/
   - Sign in with your Google account
   - Select your project
   ```

2. **Navigate to APIs & Services**
   ```
   Left sidebar → APIs & Services → Library
   OR
   Search "API Library" in the top search bar
   ```

3. **Enable Each Required API:**

   **Google Sheets API** (Essential):
   ```
   1. Search "Google Sheets API" in the library
   2. Click on "Google Sheets API"
   3. Click "ENABLE" button
   4. Wait for confirmation message
   ```

   **Google Drive API** (Essential):
   ```
   1. Search "Google Drive API"
   2. Click on "Google Drive API"
   3. Click "ENABLE"
   4. Wait for confirmation
   ```

   **Google OAuth2 API** (Usually auto-enabled):
   ```
   1. Search "People API" or "Google+ API"
   2. Click "ENABLE" if not already enabled
   ```

   **Gmail API** (Optional - for notifications):
   ```
   1. Search "Gmail API"
   2. Click "ENABLE"
   3. Only needed if sending email notifications
   ```

4. **Verify APIs are Enabled:**
   ```
   Go to APIs & Services → Dashboard
   You should see all enabled APIs listed with "Enabled" status
   ```

#### **API Quotas (Free Tier):**
```
Google Sheets API: 100 requests per 100 seconds per user
Google Drive API: 1,000 requests per 100 seconds per user  
Gmail API: 1,000,000,000 quota units per day
```

#### **Common API Enabling Errors:**

**❌ "API has not been used before or it is disabled"**
```bash
Solution:
1. Go to API Library
2. Search for the specific API mentioned in error
3. Click ENABLE
4. Wait 5-10 minutes for propagation
```

**❌ "The request cannot be identified with a user or service account"**
```bash
Solution:  
1. Check credentials are properly loaded
2. Verify service account JSON file path
3. Ensure OAuth client ID is correct
```

**❌ "Daily quota exceeded"**
```bash
Solution:
1. Check APIs & Services → Quotas
2. Request quota increase if needed
3. Optimize API calls in your application
```

### 1.3 Configure OAuth Consent Screen (Required First)
```bash
APIs & Services → OAuth consent screen

Configure:
- User Type: External (for public use) or Internal (G Workspace only)
- App name: "Simple Timesheet"
- User support email: your-email@domain.com
- Developer contact: your-email@domain.com

Scopes to add:
- ../auth/userinfo.email
- ../auth/userinfo.profile  
- ../auth/spreadsheets
- ../auth/drive.file

Test users (during development):
- Add your email addresses
- Add supervisor email addresses
```

### 1.4 Create OAuth 2.0 Web Client
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
   Development: http://localhost:8095/api/v1/auth/callback
   Production:  https://yourdomain.com/api/v1/auth/callback
   ```
6. **Save and copy the Client ID and Client Secret** → Use in backend and frontend `.env`

### 1.5 Create Service Account
1. **APIs & Services** → **Credentials** → **+ CREATE CREDENTIALS** → **Service account**
2. **Name**: `simple-timesheet-service`
3. **Service account ID**: `simple-timesheet-service` (auto-generated)
4. **Description**: `Backend service for timesheet application`
5. **Grant roles**: 
   - Basic → Editor (or create custom role with specific API permissions)
6. **Create Key** → **JSON** → Download the file
7. **Important**: Note the service account email from the JSON file (e.g., `simple-timesheet-service@yourproject.iam.gserviceaccount.com`)
8. **Rename** downloaded file to `service-account-key.json`

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

### API Enabling Issues:

**❌ "API has not been used before or it is disabled"**
```bash
Solution:
1. Go to APIs & Services → Library in Google Cloud Console
2. Search for the specific API mentioned in the error
3. Click on the API, then click "ENABLE" 
4. Wait 5-10 minutes for propagation
5. Test API access again
```

**❌ "Project does not exist or insufficient permissions"**
```bash
Solution:
1. Verify correct project is selected in Google Cloud Console
2. Check you have Editor/Owner role on the project
3. Ensure billing is enabled for production usage
4. Confirm project ID matches your configuration
```

### OAuth Authentication Issues:

**❌ "redirect_uri_mismatch" during OAuth**
```bash
Root Cause: Mismatch between configured and requested redirect URI
Solution:
1. In Google Cloud Console → APIs & Services → Credentials
2. Edit your OAuth 2.0 Client ID
3. Ensure exact match in Authorized redirect URIs:
   - Development: http://localhost:8095/api/v1/auth/callback
   - Production: https://yourdomain.com/api/v1/auth/callback
4. Check for trailing slashes and protocol (http vs https)
```

**❌ "access_denied" during OAuth**
```bash
Root Cause: User declined permissions or app not verified
Solution:
1. Check OAuth consent screen is properly configured
2. Ensure all required scopes are added:
   - ../auth/userinfo.email
   - ../auth/userinfo.profile
   - ../auth/spreadsheets
   - ../auth/drive.file
3. For development: Add user email to "Test users" list
4. For production: Submit app for verification
```

**❌ "invalid_client" error**
```bash
Root Cause: Incorrect client credentials
Solution:
1. Verify GOOGLE_CLIENT_ID matches Google Console
2. Verify GOOGLE_CLIENT_SECRET matches Google Console
3. Ensure OAuth client is configured as "Web application"
4. Check environment files are loaded correctly
```

### Service Account Issues:

**❌ "Service account not found" or "Invalid credentials"**
```bash
Root Cause: Service account configuration issues
Solution:
1. Check service account JSON file path: `/app/credentials/service-account-key.json`
2. Verify file exists and has proper permissions
3. Ensure JSON file is valid (not corrupted)
4. Confirm service account email in JSON matches error messages
5. Re-download service account key if necessary
```

**❌ "Insufficient permissions for Google Sheets"**
```bash
Root Cause: Service account lacks required permissions
Solution:
1. Share template sheet with service account email (from JSON file)
2. Grant "Editor" permissions to service account
3. Check Google Sheets API is enabled
4. Verify service account has correct IAM roles in Google Cloud Console
5. Ensure service account has these roles:
   - Basic → Editor (or custom role with Sheets/Drive access)
```

**❌ "Forbidden" or "403 Insufficient Permission"**
```bash
Root Cause: Service account lacks API access
Solution:
1. Go to IAM & Admin → Service accounts
2. Verify roles assigned to your service account
3. Ensure APIs are enabled for service account usage
4. Check Cloud Console audit logs for detailed error info
```

### Application Configuration Issues:

**❌ "CORS errors in browser"**
```bash
Root Cause: Frontend and backend CORS mismatch
Solution:
1. Update CORS_ORIGINS in backend .env file:
   CORS_ORIGINS=http://localhost:5185,https://yourdomain.com
2. Restart backend container after changes
3. Check frontend URL matches CORS settings exactly
4. Ensure no trailing slashes in CORS origins
```

**❌ "Connection refused" or "Network errors"**
```bash
Root Cause: Docker containers not running or port conflicts
Solution:
1. Check container status: docker-compose ps
2. Restart services: ./scripts/dev-restart.sh
3. Check port availability: lsof -i :8095
4. Review container logs: ./scripts/logs.sh
```

### Quota and Rate Limiting:

**❌ "Quota exceeded for quota metric"**
```bash
Root Cause: API usage exceeded free tier limits
Solution:
1. Check APIs & Services → Quotas in Google Cloud Console
2. Monitor current usage patterns
3. Implement caching to reduce API calls
4. Request quota increase for legitimate high usage
5. Consider upgrading to paid Google Cloud plan
```

### Debug Commands:

```bash
# Check all container status
docker-compose -f docker-compose.dev.yml ps

# View container logs
docker-compose -f docker-compose.dev.yml logs
docker-compose -f docker-compose.dev.yml logs backend
docker-compose -f docker-compose.dev.yml logs frontend

# Test API endpoints
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8095/api/v1/users/me
curl http://localhost:8095/health  # Health check endpoint

# Check database
sqlite3 backend/db/timesheet.db ".tables"
sqlite3 backend/db/timesheet.db "SELECT * FROM users;"

# Test Google API access
python3 -c "
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
credentials = Credentials.from_service_account_file('backend/credentials/service-account-key.json')
service = build('sheets', 'v4', credentials=credentials)
print('✅ Service account can access Google Sheets API')
"

# Check environment variables
docker-compose -f docker-compose.dev.yml exec backend printenv | grep GOOGLE

# Test frontend accessibility
curl http://localhost:5185

# Check port usage
lsof -i :5185  # Frontend port
lsof -i :8095  # Backend port
```

### Testing Checklist:

```bash
# 1. Test API Access
□ Google Sheets API enabled and accessible
□ Google Drive API enabled and accessible  
□ Service account credentials valid
□ OAuth client credentials valid

# 2. Test Authentication Flow
□ OAuth consent screen configured
□ User can login with Google
□ JWT tokens generated correctly
□ User roles assigned properly

# 3. Test Core Functionality
□ Staff can create timesheets
□ Google Sheets created in user's Drive
□ Supervisor can review submissions
□ Approval/rejection workflow works

# 4. Test API Endpoints
node run-tests.js  # Run comprehensive test suite
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