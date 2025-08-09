#!/bin/bash

# Simple Timesheet - Start All Environments
# This script starts both development and staging environments on different ports

set -e

echo "🚀 Starting All Simple Timesheet Environments..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

echo "📋 This will start both environments:"
echo "   🔧 Development: Frontend http://localhost:5185, Backend http://localhost:8095"
echo "   🏭 Staging:     Frontend http://localhost:5186, Backend http://localhost:8096"
echo ""

read -p "❓ Do you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled by user"
    exit 1
fi

# Update staging ports to avoid conflicts
echo "🔧 Updating staging configuration for port separation..."

# Create temporary staging docker-compose with different ports
cat > docker-compose.all-staging.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.staging
    container_name: all-staging-api
    ports:
      - "8096:8095"
    volumes:
      - ./backend/db:/app/db
      - ./credentials:/app/credentials:ro
    env_file:
      - ./backend/.env.staging
    restart: unless-stopped
    networks:
      - timesheet-staging-network
    environment:
      - CORS_ORIGINS=http://localhost:5186
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8095/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.staging
    container_name: all-staging-frontend
    ports:
      - "5186:5185"
    env_file:
      - ./frontend/.env.staging
    environment:
      - VITE_API_URL=http://localhost:8096
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - timesheet-staging-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5185"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  timesheet-staging-network:
    driver: bridge

volumes:
  db_data:
    driver: local
EOF

echo "🚀 Starting Development Environment..."
docker-compose -f docker-compose.dev.yml up -d --build

echo ""
echo "🏭 Starting Staging Environment (on alternate ports)..."
docker-compose -f docker-compose.all-staging.yml up -d --build

echo ""
echo "⏳ Waiting for all services to be ready..."
sleep 15

echo ""
echo "📊 Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Development Environment:"
docker-compose -f docker-compose.dev.yml ps
echo ""
echo "🏭 Staging Environment:"
docker-compose -f docker-compose.all-staging.yml ps

echo ""
echo "✅ All environments started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   🔧 Development Frontend: http://localhost:5185"
echo "   🔧 Development Backend:  http://localhost:8095"
echo "   🔧 Development API Docs: http://localhost:8095/docs"
echo ""
echo "   🏭 Staging Frontend:     http://localhost:5186"
echo "   🏭 Staging Backend:      http://localhost:8096"
echo "   🏭 Staging API Docs:     http://localhost:8096/docs"
echo ""
echo "📋 Management commands:"
echo "   View logs: ./scripts/all-logs.sh"
echo "   Stop all:  ./scripts/all-stop.sh"