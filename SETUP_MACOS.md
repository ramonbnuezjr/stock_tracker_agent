# Setting Up Stock Tracker on macOS

This guide will help you set up Stock Tracker to run automatically on your Mac Mini.

## Option 1: Launchd Service (Recommended for macOS)

Launchd is macOS's native service manager. It's more reliable than cron on macOS.

### Quick Install

```bash
cd ~/AI\ Projects/stock_tracker
./scripts/install_service.sh
```

This will:
1. Create the launchd plist file
2. Install it to `~/Library/LaunchAgents/`
3. Start the service

### Service Details

- **Runs**: Every 30 minutes (1800 seconds)
- **Logs**: `logs/stock_tracker.log`
- **Service Name**: `com.ramonbnuezjr.stocktracker`

### Managing the Service

```bash
# Check if service is running
launchctl list | grep com.ramonbnuezjr.stocktracker

# View logs
tail -f logs/stock_tracker.log

# Stop the service
launchctl unload ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Start the service
launchctl load ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Uninstall
./scripts/uninstall_service.sh
```

### Customizing Schedule

Edit the plist file:

```bash
nano ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist
```

Then reload:

```bash
launchctl unload ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist
launchctl load ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist
```

---

## Option 2: Cron (Alternative)

If you prefer cron, use this schedule:

```bash
# Edit crontab
crontab -e

# Add this line (runs every 30 minutes, 9am-4pm ET, Mon-Fri)
*/30 9-16 * * 1-5 cd ~/AI\ Projects/stock_tracker && ./venv/bin/python -m src.main check >> ~/AI\ Projects/stock_tracker/logs/stock_tracker.log 2>&1
```

Or use the helper script:

```bash
./scripts/create_cron_schedule.sh
```

---

## Verification

After installation, verify it's working:

```bash
# Check service status
launchctl list | grep stocktracker

# Run a manual test
cd ~/AI\ Projects/stock_tracker
./venv/bin/python -m src.main check

# Check logs
tail -f logs/stock_tracker.log
```

---

## Troubleshooting

### Service Not Running

```bash
# Check if plist is valid
plutil -lint ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Check service errors
launchctl list | grep stocktracker
```

### Logs Not Appearing

```bash
# Ensure logs directory exists
mkdir -p logs

# Check permissions
ls -la logs/
```

### Service Runs But No Alerts

- Check `.env` file is configured correctly
- Verify API keys are set (if using Finnhub, Twelve Data, etc.)
- Check threshold setting (default: 1.5%)
- First run stores prices but doesn't send alerts (expected behavior)

---

## Next Steps

1. ✅ Service installed and running
2. ✅ Configure your `.env` file with API keys
3. ✅ Test with: `./venv/bin/python -m src.main check`
4. ✅ Monitor logs: `tail -f logs/stock_tracker.log`
5. ✅ Wait for threshold breaches to see explanations!

The service will automatically:
- Fetch stock prices every 30 minutes
- Compare against previous prices
- Generate explanations when thresholds are exceeded
- Send notifications via your configured channel
