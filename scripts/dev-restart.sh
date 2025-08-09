#!/bin/bash

# Simple Timesheet - Restart Development Environment
# This script restarts the development environment

set -e

echo "🔄 Restarting Simple Timesheet Development Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down

echo ""
echo "🚀 Starting development environment..."
echo "   Frontend: http://localhost:5185"
echo "   Backend:  http://localhost:8095"
echo "   API Docs: http://localhost:8095/docs"
echo ""

# Restart the development environment
docker-compose -f docker-compose.dev.yml up --build

echo ""
echo "✅ Development environment restarted successfully!"