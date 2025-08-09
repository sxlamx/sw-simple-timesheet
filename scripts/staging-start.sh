#!/bin/bash

# Simple Timesheet - Staging Environment Launcher
# This script starts the staging environment in production-ready mode

set -e

echo "🚀 Starting Simple Timesheet Staging Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env files exist, if not copy templates
if [ ! -f "backend/.env.staging" ]; then
    echo "📝 Creating backend/.env.staging from template..."
    cp backend/.env.template backend/.env.staging
    echo "⚠️  Please update backend/.env.staging with your actual staging values"
fi

if [ ! -f "frontend/.env.staging" ]; then
    echo "📝 Creating frontend/.env.staging..."
    cat > frontend/.env.staging << EOF
VITE_API_URL=http://staging-api:8095
VITE_APP_NAME=Simple Timesheet (Staging)
VITE_GOOGLE_CLIENT_ID=your_staging_google_client_id_here
EOF
    echo "⚠️  Please update frontend/.env.staging with your actual values"
fi

# Create credentials directory if it doesn't exist
mkdir -p credentials

echo "🐳 Starting Docker containers in detached mode..."
echo "   Frontend: http://localhost:5185"
echo "   Backend:  http://localhost:8095"
echo "   API Docs: http://localhost:8095/docs"
echo ""

# Start the staging environment in detached mode
docker-compose -f docker-compose.staging.yml up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are healthy
echo "🔍 Checking service health..."
if docker-compose -f docker-compose.staging.yml ps | grep -q "Up (healthy)"; then
    echo "✅ Staging environment started successfully!"
    echo ""
    echo "📊 Service Status:"
    docker-compose -f docker-compose.staging.yml ps
    echo ""
    echo "📋 To view logs: ./scripts/staging-logs.sh"
    echo "📋 To stop: ./scripts/staging-stop.sh"
else
    echo "⚠️  Some services may still be starting up."
    echo "📋 Check status with: docker-compose -f docker-compose.staging.yml ps"
    echo "📋 View logs with: ./scripts/staging-logs.sh"
fi