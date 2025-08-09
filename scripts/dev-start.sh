#!/bin/bash

# Simple Timesheet - Development Environment Launcher
# This script starts the development environment with hot-reload enabled

set -e

echo "🚀 Starting Simple Timesheet Development Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env files exist, if not copy templates
if [ ! -f "backend/.env.development" ]; then
    echo "📝 Creating backend/.env.development from template..."
    cp backend/.env.template backend/.env.development
    echo "⚠️  Please update backend/.env.development with your actual values"
fi

if [ ! -f "frontend/.env.development" ]; then
    echo "📝 Creating frontend/.env.development..."
    cat > frontend/.env.development << EOF
VITE_API_URL=http://localhost:8095
VITE_APP_NAME=Simple Timesheet (Development)
VITE_GOOGLE_CLIENT_ID=your_dev_google_client_id_here
EOF
    echo "⚠️  Please update frontend/.env.development with your actual values"
fi

# Create credentials directory if it doesn't exist
mkdir -p credentials

echo "🐳 Starting Docker containers..."
echo "   Frontend: http://localhost:5185"
echo "   Backend:  http://localhost:8095"
echo "   API Docs: http://localhost:8095/docs"
echo ""

# Start the development environment
docker-compose -f docker-compose.dev.yml up --build

echo ""
echo "✅ Development environment started successfully!"
echo "   Use Ctrl+C to stop all services"