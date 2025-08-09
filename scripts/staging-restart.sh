#!/bin/bash

# Simple Timesheet - Restart Staging Environment
# This script restarts the staging environment

set -e

echo "🔄 Restarting Simple Timesheet Staging Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.staging.yml down

echo ""
echo "🚀 Starting staging environment..."
echo "   Frontend: http://localhost:5185"
echo "   Backend:  http://localhost:8095"
echo "   API Docs: http://localhost:8095/docs"
echo ""

# Restart the staging environment
docker-compose -f docker-compose.staging.yml up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✅ Staging environment restarted successfully!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.staging.yml ps