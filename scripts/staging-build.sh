#!/bin/bash

# Simple Timesheet - Build Staging Images
# This script builds all staging Docker images without starting containers

set -e

echo "🔨 Building Simple Timesheet Staging Images..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🐳 Building Docker images for staging..."

# Build staging images
docker-compose -f docker-compose.staging.yml build --no-cache

echo ""
echo "✅ Staging images built successfully!"
echo "   Use ./scripts/staging-start.sh to start the staging environment"