#!/bin/bash

# Simple Timesheet - Clean Up Docker Resources
# This script cleans up Docker containers, images, and volumes

set -e

echo "🧹 Simple Timesheet - Docker Cleanup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

# Function to show cleanup options
show_options() {
    echo "Choose cleanup level:"
    echo "  1) Light cleanup - Remove stopped containers and unused networks"
    echo "  2) Medium cleanup - Also remove unused images" 
    echo "  3) Deep cleanup - Remove everything including volumes (⚠️  DATA LOSS)"
    echo "  4) Nuclear cleanup - Complete Docker system cleanup (⚠️  ALL DOCKER DATA LOSS)"
    echo "  q) Quit"
    echo ""
}

# Show current Docker usage
echo "📊 Current Docker Usage:"
echo "   Containers: $(docker ps -a -q | wc -l | xargs)"
echo "   Images: $(docker images -q | wc -l | xargs)"
echo "   Volumes: $(docker volume ls -q | wc -l | xargs)"
echo "   Networks: $(docker network ls --format "table {{.Name}}" | grep -v NETWORK | wc -l | xargs)"
echo ""

show_options
read -p "❓ Select option (1-4 or q): " -n 1 -r
echo ""

case $REPLY in
    1)
        echo "🧹 Light cleanup - Removing stopped containers and unused networks..."
        
        # Stop all timesheet environments first
        echo "🛑 Stopping all timesheet environments..."
        ./scripts/all-stop.sh 2>/dev/null || true
        
        # Remove stopped containers
        echo "📦 Removing stopped containers..."
        docker container prune -f
        
        # Remove unused networks
        echo "🌐 Removing unused networks..."
        docker network prune -f
        
        echo "✅ Light cleanup completed!"
        ;;
        
    2)
        echo "🧹 Medium cleanup - Removing containers, networks, and unused images..."
        
        # Stop all timesheet environments first
        echo "🛑 Stopping all timesheet environments..."
        ./scripts/all-stop.sh 2>/dev/null || true
        
        # Remove stopped containers
        echo "📦 Removing stopped containers..."
        docker container prune -f
        
        # Remove unused networks
        echo "🌐 Removing unused networks..."
        docker network prune -f
        
        # Remove unused images
        echo "🖼️  Removing unused images..."
        docker image prune -f
        
        echo "✅ Medium cleanup completed!"
        ;;
        
    3)
        echo "⚠️  Deep cleanup - This will remove ALL project data including databases!"
        read -p "❓ Are you absolutely sure? (type 'yes' to continue): " confirmation
        
        if [ "$confirmation" = "yes" ]; then
            echo "🧹 Deep cleanup - Removing everything including volumes..."
            
            # Stop all timesheet environments
            echo "🛑 Stopping all timesheet environments..."
            ./scripts/all-stop.sh 2>/dev/null || true
            
            # Remove all timesheet containers
            echo "📦 Removing all timesheet containers..."
            docker ps -a --format "table {{.Names}}" | grep timesheet | xargs -r docker rm -f 2>/dev/null || true
            
            # Remove timesheet images
            echo "🖼️  Removing timesheet images..."
            docker images --format "table {{.Repository}}:{{.Tag}}" | grep timesheet | awk '{print $1":"$2}' | xargs -r docker rmi -f 2>/dev/null || true
            
            # Remove timesheet volumes
            echo "💾 Removing timesheet volumes..."
            docker volume ls --format "table {{.Name}}" | grep timesheet | xargs -r docker volume rm -f 2>/dev/null || true
            
            # Remove timesheet networks
            echo "🌐 Removing timesheet networks..."
            docker network ls --format "table {{.Name}}" | grep timesheet | xargs -r docker network rm 2>/dev/null || true
            
            # Clean up temporary files
            echo "📁 Cleaning up temporary files..."
            rm -f docker-compose.all-staging.yml
            
            # General cleanup
            docker system prune -f --volumes
            
            echo "✅ Deep cleanup completed!"
            echo "⚠️  All project data has been removed. You'll need to rebuild everything."
        else
            echo "❌ Deep cleanup cancelled."
        fi
        ;;
        
    4)
        echo "☢️  Nuclear cleanup - This will remove EVERYTHING from Docker!"
        echo "   This includes containers, images, volumes, and networks from ALL projects!"
        read -p "❓ Are you absolutely sure? (type 'NUCLEAR' to continue): " confirmation
        
        if [ "$confirmation" = "NUCLEAR" ]; then
            echo "☢️  Nuclear cleanup - Removing everything..."
            
            # Stop everything
            echo "🛑 Stopping all Docker containers..."
            docker stop $(docker ps -q) 2>/dev/null || true
            
            # Remove everything
            echo "💥 Removing all containers, images, volumes, and networks..."
            docker system prune -a -f --volumes
            
            echo "✅ Nuclear cleanup completed!"
            echo "☢️  Docker has been completely cleaned. All data from all projects is gone."
        else
            echo "❌ Nuclear cleanup cancelled."
        fi
        ;;
        
    q|Q)
        echo "👋 Cleanup cancelled."
        exit 0
        ;;
        
    *)
        echo "❌ Invalid option: $REPLY"
        exit 1
        ;;
esac

echo ""
echo "📊 Docker Usage After Cleanup:"
echo "   Containers: $(docker ps -a -q | wc -l | xargs)"
echo "   Images: $(docker images -q | wc -l | xargs)" 
echo "   Volumes: $(docker volume ls -q | wc -l | xargs)"
echo "   Networks: $(docker network ls --format "table {{.Name}}" | grep -v NETWORK | wc -l | xargs)"