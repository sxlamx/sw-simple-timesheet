# Simple Timesheet Application

A comprehensive React frontend and FastAPI backend application for recording timesheets for small teams with supervisor approval workflow and Google Sheets integration.

## 🚀 Features

### ✅ **Completed Core Features:**
- **Google OAuth Authentication** - Secure login with Gmail accounts
- **React Frontend** - Built with Vite.js, Material-UI, and JSX
- **FastAPI Backend** - RESTful API with SQLAlchemy and SQLite
- **Google Sheets Integration** - Individual timesheet storage in user's Google account
- **Docker Support** - Development and staging environments
- **Shell Scripts** - Complete container management automation
- **User Management** - Staff and supervisor role-based access
- **Database Models** - User profiles, timesheet submissions, approval workflow

### 🔧 **Architecture:**
- **Frontend**: React 18 + Vite.js + Material-UI + Axios
- **Backend**: FastAPI + SQLAlchemy + SQLite + Google APIs
- **Authentication**: Google OAuth 2.0 + JWT tokens
- **Storage**: SQLite database + Google Sheets API
- **Deployment**: Docker + Docker Compose

## 📋 **Prerequisites**

1. **Docker & Docker Compose** - For container management
2. **Google Cloud Platform Account** - For OAuth and Sheets API
3. **Google Service Account** - For server-side Google Sheets access

## 🛠️ **Setup Instructions**

### 1. **Google Cloud Platform Setup**

#### Create Google OAuth Credentials:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google+ API** and **Google Sheets API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client IDs**
5. Set **Authorized redirect URIs**:
   - Development: `http://localhost:8095/api/v1/auth/callback`
   - Staging: `http://your-staging-domain:8095/api/v1/auth/callback`

#### Create Service Account for Sheets API:
1. Go to **Credentials** → **Create Credentials** → **Service Account**
2. Download the JSON key file
3. Save as `credentials/dev-credentials.json` (development)
4. Save as `credentials/staging-credentials.json` (staging)

### 2. **Environment Configuration**

```bash
# Copy environment templates
cp backend/.env.template backend/.env.development
cp backend/.env.template backend/.env.staging
mkdir -p credentials
```

#### Update Environment Files:

**backend/.env.development:**
```env
GOOGLE_CLIENT_ID=your_dev_google_client_id_here
GOOGLE_CLIENT_SECRET=your_dev_google_client_secret_here
GOOGLE_SHEETS_CREDENTIALS_FILE=/app/credentials/dev-credentials.json
SECRET_KEY=your-secure-secret-key-here
CORS_ORIGINS=http://localhost:5185
```

**frontend/.env.development:**
```env
VITE_API_URL=http://localhost:8095
VITE_GOOGLE_CLIENT_ID=your_dev_google_client_id_here
```

### 3. **Launch the Application**

#### Development Environment:
```bash
# Start development (hot-reload enabled)
./scripts/dev-start.sh

# Access the application:
# Frontend: http://localhost:5185
# Backend:  http://localhost:8095
# API Docs: http://localhost:8095/docs
```

#### Staging Environment:
```bash
# Start staging (production-ready)
./scripts/staging-start.sh

# Access the application:
# Frontend: http://localhost:5185
# Backend:  http://localhost:8095
```

#### Run Both Environments:
```bash
# Start both (different ports)
./scripts/all-start.sh

# Development: Frontend 5185, Backend 8095
# Staging:     Frontend 5186, Backend 8096
```

## 📊 **Application Workflow**

### **Staff User Journey:**
1. **Login** → Google OAuth authentication
2. **Create Timesheet** → Generates Google Sheet for specific month
3. **Fill Timesheet** → Edit Google Sheet with daily hours
4. **Submit for Approval** → Changes status to "pending"
5. **Track Status** → Monitor approval/rejection status
6. **Export Data** → Download Excel format

### **Supervisor User Journey:**
1. **Login** → Google OAuth authentication (supervisor role)
2. **Review Pending** → See all staff submissions awaiting approval
3. **View Details** → Access individual Google Sheets
4. **Approve/Reject** → With optional review notes
5. **Team Management** → View all team members and their timesheets
6. **Export Reports** → Download team data in Excel format

### **Data Flow:**
```
User → Google OAuth → JWT Token → API Access
     ↓
Create Timesheet → Google Sheets API → Individual Sheet Created
     ↓
Fill Hours → Google Sheet → User Interface
     ↓
Submit → Update Database Status → Notify Supervisor
     ↓
Review → Supervisor Dashboard → Approve/Reject
     ↓
Final Status → Update Google Sheet & Database
```

## 🐳 **Docker Management**

### **Available Scripts:**
```bash
# Development Environment
./scripts/dev-start.sh     # Start with hot-reload
./scripts/dev-stop.sh      # Stop development
./scripts/dev-restart.sh   # Restart development
./scripts/dev-build.sh     # Build dev images

# Staging Environment  
./scripts/staging-start.sh # Start production-ready
./scripts/staging-stop.sh  # Stop staging
./scripts/staging-restart.sh # Restart staging
./scripts/staging-build.sh # Build staging images

# All Environments
./scripts/all-start.sh     # Start both (different ports)
./scripts/all-stop.sh      # Stop everything
./scripts/all-build.sh     # Build all images

# Utilities
./scripts/logs.sh [dev|staging|all]  # View logs
./scripts/status.sh        # Show environment status
./scripts/clean.sh         # Interactive Docker cleanup
```

### **Port Configuration:**
- **Development**: Frontend `5185`, Backend `8095`
- **Staging**: Frontend `5185`, Backend `8095`
- **Both Running**: Dev (`5185`/`8095`), Staging (`5186`/`8096`)

## 🔑 **API Endpoints**

### **Authentication:**
- `POST /api/v1/auth/google` - Authenticate with Google token
- `GET /api/v1/auth/google` - Redirect to Google OAuth
- `GET /api/v1/auth/callback` - Handle OAuth callback
- `GET /api/v1/auth/me` - Get current user info

### **Users:**
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/` - Get all users (supervisor only)
- `GET /api/v1/users/staff` - Get staff members (supervisor only)

### **Timesheets:**
- `POST /api/v1/timesheets/create` - Create new timesheet
- `GET /api/v1/timesheets/` - Get user's timesheets
- `GET /api/v1/timesheets/{id}` - Get specific timesheet
- `POST /api/v1/timesheets/{id}/submit` - Submit for approval
- `POST /api/v1/timesheets/{id}/approve` - Approve (supervisor)
- `POST /api/v1/timesheets/{id}/reject` - Reject (supervisor)
- `GET /api/v1/timesheets/pending/review` - Get pending (supervisor)

## 🛡️ **Security Features**

- **Google OAuth 2.0** - Secure authentication
- **JWT Tokens** - Stateless session management  
- **CORS Protection** - Environment-specific origins
- **Role-based Access** - Staff vs Supervisor permissions
- **Input Validation** - Pydantic schemas
- **SQL Injection Protection** - SQLAlchemy ORM
- **Service Account Auth** - Google API access

## 📱 **Frontend Features**

### **Staff Dashboard:**
- Timesheet creation and management
- Status tracking (draft/pending/approved/rejected)
- Google Sheets integration
- Excel export functionality
- Performance metrics

### **Supervisor Dashboard:**
- Team member overview
- Pending approvals queue
- Individual timesheet review
- Approval/rejection with notes
- Team analytics and reporting

### **Responsive Design:**
- Material-UI components
- Mobile-friendly interface
- Dark/light theme support
- Accessible navigation
- Professional styling

## 🔧 **Development**

### **Backend Development:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8095
```

### **Frontend Development:**
```bash
cd frontend
npm install
npm run dev
```

### **Database Management:**
```bash
# View database
sqlite3 db/timesheet.db
```

## 🧪 **Testing**

### **API Testing:**
- Visit `http://localhost:8095/docs` for interactive API documentation
- Use Swagger UI to test all endpoints
- Authentication required for protected endpoints

### **Frontend Testing:**
- React development server with hot-reload
- Browser developer tools for debugging
- Material-UI component testing

## 🚀 **Production Deployment**

1. **Update Environment Variables** - Production values
2. **Configure HTTPS** - SSL certificates
3. **Set up Domain** - DNS and reverse proxy
4. **Update CORS** - Production frontend URL
5. **Deploy with Docker** - Use staging configuration
6. **Monitor Logs** - Use `./scripts/logs.sh` for monitoring

## 📁 **Project Structure**

```
simple-timesheet/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration & auth
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas  
│   │   ├── crud/         # Database operations
│   │   └── services/     # Business logic
│   ├── db/               # SQLite database
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Route pages
│   │   ├── contexts/     # React contexts
│   │   └── services/     # API services
│   └── package.json
├── scripts/              # Docker management scripts
├── credentials/          # Google service accounts
└── docker-compose.*.yml
```

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **Port Conflicts:**
   ```bash
   ./scripts/all-stop.sh
   lsof -i :5185  # Check what's using the port
   ```

2. **Google OAuth Issues:**
   - Check redirect URI configuration
   - Verify client ID/secret in environment files
   - Ensure APIs are enabled in Google Cloud Console

3. **Database Issues:**
   ```bash
   # Reset database by removing the file
   rm -f db/timesheet.db
   ```

4. **Docker Issues:**
   ```bash
   ./scripts/clean.sh     # Interactive cleanup
   ./scripts/status.sh    # Check container status
   ```

### **Getting Help:**
- Check the logs: `./scripts/logs.sh all`
- View API docs: `http://localhost:8095/docs`
- Check container status: `./scripts/status.sh`

---

🎉 **Congratulations!** You now have a fully functional timesheet management system with Google OAuth, Google Sheets integration, and professional Docker deployment setup!