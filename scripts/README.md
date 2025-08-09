# Simple Timesheet - Scripts Documentation

This directory contains shell scripts to manage Docker containers for the Simple Timesheet application.

## 📁 Available Scripts

### Development Environment
- **`dev-start.sh`** - Start development environment with hot-reload
- **`dev-stop.sh`** - Stop development environment
- **`dev-restart.sh`** - Restart development environment
- **`dev-build.sh`** - Build development Docker images

### Staging Environment
- **`staging-start.sh`** - Start staging environment (production-ready)
- **`staging-stop.sh`** - Stop staging environment
- **`staging-restart.sh`** - Restart staging environment
- **`staging-build.sh`** - Build staging Docker images

### All Environments
- **`all-start.sh`** - Start both development and staging (different ports)
- **`all-stop.sh`** - Stop all environments
- **`all-restart.sh`** - Restart all environments
- **`all-build.sh`** - Build all Docker images

### Utilities
- **`logs.sh`** - View logs (usage: `./logs.sh [dev|staging|all]`)
- **`status.sh`** - Show status of all environments
- **`clean.sh`** - Clean up Docker resources (interactive)

## 🚀 Quick Start

### Development
```bash
# Start development environment
./scripts/dev-start.sh

# View logs
./scripts/logs.sh dev

# Stop when done
./scripts/dev-stop.sh
```

### Staging
```bash
# Start staging environment
./scripts/staging-start.sh

# View logs
./scripts/logs.sh staging

# Stop when done
./scripts/staging-stop.sh
```

### Both Environments
```bash
# Start both environments (different ports)
./scripts/all-start.sh

# View status
./scripts/status.sh

# View all logs
./scripts/logs.sh all

# Stop everything
./scripts/all-stop.sh
```

## 🌐 Access URLs

### Development Environment
- **Frontend**: http://localhost:5185
- **Backend**: http://localhost:8095
- **API Documentation**: http://localhost:8095/docs

### Staging Environment (when run alone)
- **Frontend**: http://localhost:5185
- **Backend**: http://localhost:8095
- **API Documentation**: http://localhost:8095/docs

### When Both Environments Run Together
- **Development Frontend**: http://localhost:5185
- **Development Backend**: http://localhost:8095
- **Staging Frontend**: http://localhost:5186
- **Staging Backend**: http://localhost:8096

## 🔧 Environment Configuration

### First Time Setup
1. Copy environment templates:
   ```bash
   cp backend/.env.template backend/.env.development
   cp backend/.env.template backend/.env.staging
   ```

2. Update the environment files with your actual values:
   - Google OAuth credentials
   - Google Sheets API credentials
   - Secret keys
   - CORS origins

3. Create credentials directory:
   ```bash
   mkdir -p credentials
   ```

4. Add your Google service account JSON files to the credentials directory.

## 📋 Script Features

### Smart Environment Detection
- Scripts automatically detect which environments are running
- Prevents port conflicts when running multiple environments
- Shows clear status information

### Error Handling
- All scripts include proper error handling
- Check for required dependencies (docker-compose)
- Provide helpful error messages

### Interactive Features
- Confirmation prompts for destructive operations
- Colored output for better readability
- Progress indicators for long-running operations

### Logging
- Structured logging with timestamps
- Environment-specific log viewing
- Follow logs in real-time

## 🛠️ Troubleshooting

### Port Conflicts
If you get port conflicts:
```bash
# Stop all environments
./scripts/all-stop.sh

# Check what's using the ports
lsof -i :5185
lsof -i :8095

# Start individual environments
./scripts/dev-start.sh
# OR
./scripts/staging-start.sh
```

### Permission Issues
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Docker Issues
```bash
# Clean up Docker resources
./scripts/clean.sh

# Check Docker status
./scripts/status.sh
```

### Environment File Issues
Make sure your environment files exist and have correct values:
- `backend/.env.development`
- `backend/.env.staging`
- `frontend/.env.development`
- `frontend/.env.staging`

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Vite.js Documentation](https://vitejs.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Material-UI Documentation](https://mui.com/)