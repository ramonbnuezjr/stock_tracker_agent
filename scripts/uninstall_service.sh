#!/bin/bash
# Uninstall Stock Tracker launchd service

set -e

PLIST_NAME="com.ramonbnuezjr.stocktracker"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "🗑️  Uninstalling Stock Tracker Service..."
echo ""

# Unload service if running (bootstrap domain on Sonoma+, else legacy load)
GUI_DOMAIN="gui/$(id -u)"
if launchctl list "$GUI_DOMAIN" 2>/dev/null | grep -q "$PLIST_NAME"; then
    echo "Stopping service..."
    launchctl bootout "$GUI_DOMAIN/$PLIST_NAME" 2>/dev/null || true
    echo "✅ Service stopped"
elif launchctl list 2>/dev/null | grep -q "$PLIST_NAME"; then
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
