#!/bin/bash
# Uninstall Stock Tracker launchd service

set -e

PLIST_NAME="com.ramonbnuezjr.stocktracker"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "🗑️  Uninstalling Stock Tracker Service..."
echo ""

# Unload service if running
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "Stopping service..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    echo "✅ Service stopped"
fi

# Remove plist file
if [ -f "$PLIST_FILE" ]; then
    rm "$PLIST_FILE"
    echo "✅ Removed plist file"
fi

echo ""
echo "✅ Stock Tracker service uninstalled"
echo ""
