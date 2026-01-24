#!/bin/bash
# Install Stock Tracker as a macOS launchd service

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLIST_NAME="com.ramonbnuezjr.stocktracker"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "📦 Installing Stock Tracker Service..."
echo ""

# Check if venv exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    cd "$PROJECT_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo "✅ Virtual environment created"
fi

# Generate plist using Python script
cd "$PROJECT_DIR"
python3 scripts/create_launchd_plist.py

# Check if service is already loaded
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "⚠️  Service already loaded. Unloading first..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# Load the service
echo "🚀 Loading service..."
launchctl load "$PLIST_FILE"

echo ""
echo "✅ Stock Tracker service installed and started!"
echo ""
echo "Service will run every 30 minutes during market hours (9am-4pm ET, Mon-Fri)"
echo ""
echo "Useful commands:"
echo "  Status:    launchctl list | grep $PLIST_NAME"
echo "  Stop:      launchctl unload $PLIST_FILE"
echo "  Start:     launchctl load $PLIST_FILE"
echo "  Logs:      tail -f $PROJECT_DIR/logs/stock_tracker.log"
echo "  Test run:  cd $PROJECT_DIR && ./venv/bin/python -m src.main check"
echo ""
