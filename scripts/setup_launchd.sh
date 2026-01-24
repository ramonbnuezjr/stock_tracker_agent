#!/bin/bash
# Setup script for macOS launchd service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_NAME="com.ramonbnuezjr.stocktracker"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "Setting up Stock Tracker as a macOS launchd service..."
echo ""

# Get absolute paths
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
MAIN_SCRIPT="$PROJECT_DIR/src/main.py"
LOG_FILE="$PROJECT_DIR/logs/stock_tracker.log"

# Create logs directory
mkdir -p "$PROJECT_DIR/logs"

# Create plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PYTHON}</string>
        <string>-m</string>
        <string>src.main</string>
        <string>check</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    
    <key>StandardOutPath</key>
    <string>${LOG_FILE}</string>
    
    <key>StandardErrorPath</key>
    <string>${LOG_FILE}</string>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ Created plist file: $PLIST_FILE"
echo ""
echo "To start the service:"
echo "  launchctl load $PLIST_FILE"
echo ""
echo "To stop the service:"
echo "  launchctl unload $PLIST_FILE"
echo ""
echo "To check status:"
echo "  launchctl list | grep $PLIST_NAME"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_FILE"
echo ""
