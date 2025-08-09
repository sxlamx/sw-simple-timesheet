#!/bin/bash

# Simple Timesheet - Environment Status
# This script shows the status of all environments

set -e

echo "📊 Simple Timesheet - Environment Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Function to check if containers are running
check_environment() {
    local env_name="$1"
    local compose_file="$2"
    
    if [ ! -f "$compose_file" ]; then
        echo "   ❌ Configuration file not found: $compose_file"
        return
    fi
    
    echo "🔍 $env_name Environment:"
    
    if docker-compose -f "$compose_file" ps 2>/dev/null | grep -q "Up"; then
        echo "   ✅ Status: Running"
        docker-compose -f "$compose_file" ps | tail -n +2 | while read line; do
            if [ ! -z "$line" ]; then
                container=$(echo "$line" | awk '{print $1}')
                status=$(echo "$line" | awk '{print $4,$5,$6}' | sed 's/Up /✅ Up /')
                echo "      $container: $status"
            fi
        done
    else
        echo "   ❌ Status: Stopped"
    fi
    echo ""
}

# Check Development Environment
check_environment "🔧 Development" "docker-compose.dev.yml"

# Check Staging Environment  
check_environment "🏭 Staging" "docker-compose.staging.yml"

# Check All-Staging Environment (if exists)
if [ -f "docker-compose.all-staging.yml" ]; then
    check_environment "🏭 All-Staging" "docker-compose.all-staging.yml"
fi

# Show Docker system info
echo "🐳 Docker System Information:"
echo "   Images: $(docker images --format "table {{.Repository}}:{{.Tag}}" | grep -c timesheet || echo 0) timesheet images"
echo "   Containers: $(docker ps -a --format "table {{.Names}}" | grep -c timesheet || echo 0) timesheet containers"
echo "   Running: $(docker ps --format "table {{.Names}}" | grep -c timesheet || echo 0) timesheet containers"

# Show available URLs
echo ""
echo "🌐 Available URLs:"
if docker-compose -f docker-compose.dev.yml ps 2>/dev/null | grep -q "Up"; then
    echo "   🔧 Development Frontend: http://localhost:5185"
    echo "   🔧 Development Backend:  http://localhost:8095"
    echo "   🔧 Development API Docs: http://localhost:8095/docs"
fi

if docker-compose -f docker-compose.staging.yml ps 2>/dev/null | grep -q "Up"; then
    echo "   🏭 Staging Frontend:     http://localhost:5185"
    echo "   🏭 Staging Backend:      http://localhost:8095"
    echo "   🏭 Staging API Docs:     http://localhost:8095/docs"
fi

if [ -f "docker-compose.all-staging.yml" ] && docker-compose -f docker-compose.all-staging.yml ps 2>/dev/null | grep -q "Up"; then
    echo "   🏭 All-Staging Frontend: http://localhost:5186"
    echo "   🏭 All-Staging Backend:  http://localhost:8096"
    echo "   🏭 All-Staging API Docs: http://localhost:8096/docs"
fi

# Show quick commands
echo ""
echo "📋 Quick Commands:"
echo "   ./scripts/dev-start.sh      # Start development"
echo "   ./scripts/staging-start.sh  # Start staging"
echo "   ./scripts/all-start.sh      # Start both environments"
echo "   ./scripts/logs.sh all       # View logs"
echo "   ./scripts/all-stop.sh       # Stop everything"