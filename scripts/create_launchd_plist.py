#!/usr/bin/env python3
"""Generate launchd plist for Stock Tracker on macOS.

This creates a launchd service that runs the stock tracker
every 30 minutes during market hours (9am-4pm ET, Mon-Fri).
"""

from __future__ import annotations

import os
from pathlib import Path

# Get project directory
PROJECT_DIR = Path(__file__).parent.parent
VENV_PYTHON = PROJECT_DIR / "venv" / "bin" / "python"
MAIN_MODULE = "src.main"
LOG_DIR = PROJECT_DIR / "logs"
LOG_FILE = LOG_DIR / "stock_tracker.log"

# Ensure log directory exists
LOG_DIR.mkdir(exist_ok=True)

# Create plist content
PLIST_NAME = "com.ramonbnuezjr.stocktracker"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"

plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{VENV_PYTHON}</string>
        <string>-m</string>
        <string>{MAIN_MODULE}</string>
        <string>check</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>{PROJECT_DIR}</string>
    
    <key>StandardOutPath</key>
    <string>{LOG_FILE}</string>
    
    <key>StandardErrorPath</key>
    <string>{LOG_FILE}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    
    <!-- Run every 30 minutes (1800 seconds) -->
    <!-- Note: This runs continuously. For market hours only, use cron instead. -->
    <key>StartInterval</key>
    <integer>1800</integer>
    
    <!-- Alternative: Run at specific times during market hours -->
    <!-- Uncomment this and remove StartInterval for market-hours-only schedule -->
    <!--
    <key>StartCalendarInterval</key>
    <array>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>9</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>10</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>11</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>11</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>12</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>12</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>13</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>13</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>14</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>15</integer><key>Minute</key><integer>0</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>15</integer><key>Minute</key><integer>30</integer></dict>
        <dict><key>Weekday</key><integer>1</integer><key>Hour</key><integer>16</integer><key>Minute</key><integer>0</integer></dict>
        <!-- Repeat for Tuesday-Friday (Weekday 2-5) -->
    </array>
    -->
    
    <!-- Run once when service is loaded, then every 30 min -->
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
"""

# Write plist file
PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
PLIST_PATH.write_text(plist_content)

print(f"✅ Created launchd plist: {PLIST_PATH}")
print()
print("To install and start the service:")
print(f"  launchctl load {PLIST_PATH}")
print()
print("To stop the service:")
print(f"  launchctl unload {PLIST_PATH}")
print()
print("To check status:")
print(f"  launchctl list | grep {PLIST_NAME}")
print()
print("To view logs:")
print(f"  tail -f {LOG_FILE}")
print()
