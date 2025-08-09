#!/bin/bash

# Simple Timesheet - Build Development Images
# This script builds all development Docker images without starting containers

set -e

echo "🔨 Building Simple Timesheet Development Images..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🐳 Building Docker images for development..."

# Build development images
docker-compose -f docker-compose.dev.yml build --no-cache

echo ""
echo "✅ Development images built successfully!"
echo "   Use ./scripts/dev-start.sh to start the development environment"