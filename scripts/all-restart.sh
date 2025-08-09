#!/bin/bash

# Simple Timesheet - Restart All Environments
# This script restarts both development and staging environments

set -e

echo "🔄 Restarting All Simple Timesheet Environments..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Navigate to project root
cd "$(dirname "$0")/.."

echo "🛑 Stopping all environments first..."
./scripts/all-stop.sh

echo ""
echo "⏳ Waiting a moment for complete shutdown..."
sleep 5

echo ""
echo "🚀 Starting all environments..."
./scripts/all-start.sh

echo ""
echo "✅ All environments restarted successfully!"