#!/bin/bash

# Simple Timesheet - Stop Staging Environment
# This script stops all staging containers and cleans up

set -e

echo "🛑 Stopping Simple Timesheet Staging Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed."
    exit 1
fi

echo "🐳 Stopping Docker containers..."

# Stop the staging environment
docker-compose -f docker-compose.staging.yml down

echo ""
echo "✅ Staging environment stopped successfully!"
echo "   All containers have been stopped and removed."
echo "   Volumes and networks have been preserved."