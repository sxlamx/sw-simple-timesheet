#!/bin/bash

# Simple Timesheet - Stop All Environments
# This script stops both development and staging environments

set -e

echo "🛑 Stopping All Simple Timesheet Environments..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

echo "🔧 Stopping Development Environment..."
if [ -f "docker-compose.dev.yml" ]; then
    docker-compose -f docker-compose.dev.yml down
    echo "   ✅ Development environment stopped"
else
    echo "   ⚠️  Development docker-compose file not found"
fi

echo ""
echo "🏭 Stopping Staging Environment..."
if [ -f "docker-compose.staging.yml" ]; then
    docker-compose -f docker-compose.staging.yml down
    echo "   ✅ Regular staging environment stopped"
else
    echo "   ⚠️  Staging docker-compose file not found"
fi

# Stop the all-staging environment if it exists
if [ -f "docker-compose.all-staging.yml" ]; then
    echo ""
    echo "🏭 Stopping All-Staging Environment (alternate ports)..."
    docker-compose -f docker-compose.all-staging.yml down
    rm -f docker-compose.all-staging.yml
    echo "   ✅ All-staging environment stopped and cleaned up"
fi

echo ""
echo "🧹 Cleaning up unused resources..."
docker system prune -f --volumes 2>/dev/null || true

echo ""
echo "✅ All environments stopped successfully!"
echo "   All containers have been stopped and removed."
echo "   Temporary files have been cleaned up."