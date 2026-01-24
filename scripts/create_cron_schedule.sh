#!/bin/bash
# Create a cron schedule for Stock Tracker (alternative to launchd)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

CRON_LINE="*/30 9-16 * * 1-5 cd $PROJECT_DIR && $PROJECT_DIR/venv/bin/python -m src.main check >> $PROJECT_DIR/logs/stock_tracker.log 2>&1"

echo "📅 Cron Schedule Setup"
echo ""
echo "Add this line to your crontab:"
echo ""
echo "$CRON_LINE"
echo ""
echo "To install:"
echo "  1. Run: crontab -e"
echo "  2. Paste the line above"
echo "  3. Save and exit"
echo ""
echo "This will run every 30 minutes during market hours (9am-4pm ET, Mon-Fri)"
echo ""
