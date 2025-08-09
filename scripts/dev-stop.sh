#!/bin/bash

# Simple Timesheet - Stop Development Environment
# This script stops all development containers and cleans up

set -e

echo "🛑 Stopping Simple Timesheet Development Environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed."
    exit 1
fi

echo "🐳 Stopping Docker containers..."

# Stop the development environment
docker-compose -f docker-compose.dev.yml down

echo ""
echo "✅ Development environment stopped successfully!"
echo "   All containers have been stopped and removed."
echo "   Volumes and networks have been preserved."