#!/bin/bash

# Simple Timesheet - View Logs
# This script shows logs for development or staging environment

set -e

# Function to show usage
show_usage() {
    echo "Usage: $0 [dev|staging|all]"
    echo ""
    echo "Options:"
    echo "  dev      Show development environment logs"
    echo "  staging  Show staging environment logs"  
    echo "  all      Show logs from all running environments"
    echo ""
    echo "Examples:"
    echo "  $0 dev     # Show development logs"
    echo "  $0 staging # Show staging logs"
    echo "  $0 all     # Show all logs"
}

# Navigate to project root
cd "$(dirname "$0")/.."

# Check arguments
if [ $# -eq 0 ]; then
    echo "❓ No environment specified. Showing all available logs..."
    ENVIRONMENT="all"
else
    ENVIRONMENT="$1"
fi

echo "📋 Simple Timesheet - Viewing Logs ($ENVIRONMENT)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

case $ENVIRONMENT in
    "dev")
        echo "🔧 Development Environment Logs:"
        echo "   Press Ctrl+C to exit log viewing"
        echo ""
        docker-compose -f docker-compose.dev.yml logs -f
        ;;
    "staging")
        echo "🏭 Staging Environment Logs:"
        echo "   Press Ctrl+C to exit log viewing"
        echo ""
        docker-compose -f docker-compose.staging.yml logs -f
        ;;
    "all")
        echo "🔍 Checking for running environments..."
        
        DEV_RUNNING=false
        STAGING_RUNNING=false
        ALL_STAGING_RUNNING=false
        
        # Check if development is running
        if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
            DEV_RUNNING=true
            echo "   🔧 Development environment: Running"
        else
            echo "   🔧 Development environment: Stopped"
        fi
        
        # Check if staging is running
        if docker-compose -f docker-compose.staging.yml ps 2>/dev/null | grep -q "Up"; then
            STAGING_RUNNING=true
            echo "   🏭 Staging environment: Running"
        else
            echo "   🏭 Staging environment: Stopped"
        fi
        
        # Check if all-staging is running
        if [ -f "docker-compose.all-staging.yml" ] && docker-compose -f docker-compose.all-staging.yml ps 2>/dev/null | grep -q "Up"; then
            ALL_STAGING_RUNNING=true
            echo "   🏭 All-staging environment: Running"
        fi
        
        echo ""
        
        if [ "$DEV_RUNNING" = true ] && [ "$STAGING_RUNNING" = true ]; then
            echo "📋 Both environments are running. Choose which logs to view:"
            echo "   Press Ctrl+C to exit log viewing"
            echo ""
            echo "🔧 Development Logs:"
            docker-compose -f docker-compose.dev.yml logs --tail=20
            echo ""
            echo "🏭 Staging Logs:"
            docker-compose -f docker-compose.staging.yml logs --tail=20
            echo ""
            echo "🔄 Following all logs (press Ctrl+C to exit)..."
            docker-compose -f docker-compose.dev.yml logs -f &
            docker-compose -f docker-compose.staging.yml logs -f &
            wait
        elif [ "$DEV_RUNNING" = true ] && [ "$ALL_STAGING_RUNNING" = true ]; then
            echo "📋 Both environments are running (development + all-staging):"
            echo "   Press Ctrl+C to exit log viewing"
            echo ""
            docker-compose -f docker-compose.dev.yml logs -f &
            docker-compose -f docker-compose.all-staging.yml logs -f &
            wait
        elif [ "$DEV_RUNNING" = true ]; then
            echo "🔧 Showing Development logs:"
            docker-compose -f docker-compose.dev.yml logs -f
        elif [ "$STAGING_RUNNING" = true ]; then
            echo "🏭 Showing Staging logs:"
            docker-compose -f docker-compose.staging.yml logs -f
        elif [ "$ALL_STAGING_RUNNING" = true ]; then
            echo "🏭 Showing All-Staging logs:"
            docker-compose -f docker-compose.all-staging.yml logs -f
        else
            echo "❌ No environments are currently running."
            echo ""
            echo "📋 Start an environment first:"
            echo "   ./scripts/dev-start.sh     # Development"
            echo "   ./scripts/staging-start.sh # Staging"
            echo "   ./scripts/all-start.sh     # Both"
        fi
        ;;
    *)
        echo "❌ Invalid environment: $ENVIRONMENT"
        echo ""
        show_usage
        exit 1
        ;;
esac