# Setting Up Stock Tracker on macOS

This guide will help you set up Stock Tracker to run automatically on your Mac Mini.

## Option 1: Launchd Service (Recommended for macOS)

Launchd is macOS's native service manager. It's more reliable than cron on macOS.

### Quick Install

From **Terminal.app** (not from inside Cursor/IDE, so launchd loads in your user session):

```bash
cd ~/AI\ Projects/stock_tracker
./scripts/install_service.sh
```

If you see **Load failed: 5** or **Unload failed: 5** (common on Sonoma+), use **bootstrap** and **bootout** with the GUI domain instead of `load`/`unload`:

**Load the service:**
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist
```

**Unload the service (when you need to stop or reinstall):**
```bash
launchctl bootout gui/$(id -u)/com.ramonbnuezjr.stocktracker
```
(Use the service **label** here, not the plist path.)

**Check status** (use plain `list`; `list gui/$(id -u)` can fail on some macOS):
```bash
launchctl list | grep stocktracker
```

If bootstrap still fails, check: `plutil -lint ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist` and ensure the file is owned by you (`ls -la`).

**If bootstrap fails with "5: Input/output error" on macOS 26 beta** (even from Terminal.app), launchd may be broken or stricter on the beta. Use **cron** instead (see Option 2 below) — it works regardless of launchd.

The install script will:
1. Create the launchd plist file
2. Install it to `~/Library/LaunchAgents/`
3. Start the service (or you run the `launchctl load` command above)

### Service Details

- **Runs**: Every 30 minutes (1800 seconds)
- **Logs**: `logs/stock_tracker.log`
- **Service Name**: `com.ramonbnuezjr.stocktracker`

### Managing the Service

```bash
# Check if service is running
launchctl list | grep stocktracker

# View logs
tail -f ~/AI\ Projects/stock_tracker/logs/stock_tracker.log

# Stop the service (use bootout if you started with bootstrap)
launchctl bootout gui/$(id -u)/com.ramonbnuezjr.stocktracker

# Start the service
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Uninstall
cd ~/AI\ Projects/stock_tracker && ./scripts/uninstall_service.sh
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

## Option 2: Cron (Alternative / Fallback if launchd fails)

Use cron if you prefer it, or **if launchd bootstrap fails** (e.g. on macOS 26 beta). Cron runs reliably regardless of launchd. **After a reboot**, cron is started automatically; your crontab runs once you’re logged in, so the stock tracker will run on schedule without any extra setup.

**One-time setup:**

```bash
# Ensure log directory exists
mkdir -p ~/AI\ Projects/stock_tracker/logs

# Edit your crontab
crontab -e
```

Add this line (runs every 30 minutes, 24/7):

```
*/30 * * * * cd ~/AI\ Projects/stock_tracker && ./venv/bin/python -m src.main check >> ~/AI\ Projects/stock_tracker/logs/stock_tracker.log 2>&1
```

To run only during market hours (e.g. 9am–4pm ET, Mon–Fri), use:

```
*/30 9-16 * * 1-5 cd ~/AI\ Projects/stock_tracker && ./venv/bin/python -m src.main check >> ~/AI\ Projects/stock_tracker/logs/stock_tracker.log 2>&1
```

Or use the helper script:

```bash
cd ~/AI\ Projects/stock_tracker
./scripts/create_cron_schedule.sh
```

---

## LLM (Phi-3 Mini) and Notifications

Before or after the service is installed:

1. **Download Phi-3 Mini** (one-time): `./venv/bin/python scripts/download_phi3_mini.py` — downloads the Q4 GGUF to `./models/` and sets `LLAMA_MODEL_PATH` in `.env`.
2. **Smoke test the LLM**: `./venv/bin/python scripts/smoke_test_llm.py` — generates explanations for all monitored stocks; use Stats to watch CPU/RAM.
3. **Test iMessage**: Set `NOTIFY_PHONE` in `.env`, then run `./venv/bin/python scripts/test_imessage_notification.py`. Messages must be signed in on the Mac; check the Messages app on the Mac if the iPhone does not receive.

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
# Load with bootstrap (use this if load/unload give "failed: 5"):
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist

# Check status (plain list works on all macOS):
launchctl list | grep stocktracker

# Stop service (bootout uses the label, not the path):
launchctl bootout gui/$(id -u)/com.ramonbnuezjr.stocktracker

# Check plist is valid
plutil -lint ~/Library/LaunchAgents/com.ramonbnuezjr.stocktracker.plist
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
6. ✅ Smoke test the LLM with Stats: run `./venv/bin/python scripts/smoke_test_llm.py` and watch CPU/RAM in Stats (see README > Development > Smoke tests).

The service will automatically:
- Fetch stock prices every 30 minutes
- Compare against previous prices
- Generate explanations when thresholds are exceeded
- Send notifications via your configured channel
