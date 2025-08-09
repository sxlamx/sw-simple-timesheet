#!/bin/bash

# Simple Timesheet - Build All Images
# This script builds all Docker images for both development and staging

set -e

echo "🔨 Building All Simple Timesheet Images..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🔧 Building Development Images..."
docker-compose -f docker-compose.dev.yml build --no-cache

echo ""
echo "🏭 Building Staging Images..."
docker-compose -f docker-compose.staging.yml build --no-cache

echo ""
echo "✅ All images built successfully!"
echo ""
echo "📋 Available commands:"
echo "   Start development: ./scripts/dev-start.sh"
echo "   Start staging:     ./scripts/staging-start.sh"
echo "   Start both:        ./scripts/all-start.sh"