# Cursor Sandbox Execution

## Overview

Cursor has **two execution modes**, and only one has real network access.

### 1️⃣ Cursor Sandboxed Execution

This is used when:
- Cursor runs code inline
- Cursor executes snippets
- Cursor runs tests internally
- Cursor does "AI-powered execution"

**Characteristics:**
- ❌ No DNS resolution
- ❌ No outbound network access
- ❌ No exceptions or overrides
- ❌ Cannot be disabled

This is intentional for:
- Safety
- Determinism
- Reproducibility

**You cannot disable this. Full stop.**

### 2️⃣ Local Mac Execution

This is:
- Your shell
- Your venv
- Your OS networking stack
- Your DNS resolver
- Your API keys
- Your Twilio connectivity

This is where **real integrations must run**.

---

## Key Insight

> **Cursor is a coding environment, not a runtime environment.**

Cursor helps you **write and reason about code**, but:
- It does *not* replace your local runtime
- It does *not* simulate the internet
- It does *not* allow outbound connectivity

---

## The Correct Way to Run Smoke Tests

### ✅ Method 1: Cursor Integrated Terminal (Recommended)

1. Open **Cursor**
2. Open the **Terminal panel** (bottom)
3. Run your command **there**

```bash
cd ~/AI\ Projects/stock_tracker
./venv/bin/python -m src.main check
```

This runs:
- Outside the sandbox
- On your Mac
- With full DNS + internet
- With Twilio access

Cursor is just acting as a **terminal UI**, not an executor.

### ✅ Method 2: Dedicated Script

Create a script and run from Cursor terminal:

```bash
./venv/bin/python scripts/smoke_test_market_data.py
```

---

## What Will Never Work

These will **always** fail with DNS errors:
- Running smoke tests via Cursor "Run" buttons
- Running tests via Cursor inline execution
- Asking Cursor to "execute this code"
- Running tests from AI-assisted execution

No configuration can change this.

---

## Preflight Check

The application includes a preflight check that detects sandboxed environments:

```python
try:
    socket.gethostbyname("google.com")
    logger.info("Network connectivity: OK")
except Exception:
    logger.warning(
        "Network unavailable. Running in sandboxed environment. "
        "Live market data will fail. Use terminal to run smoke tests."
    )
```

This turns a mystery into a clear signal.

---

## Final Answer

- ❌ You cannot take Cursor out of the sandbox
- ❌ There is no exception list
- ❌ This is not misconfiguration
- ✅ This is expected behavior
- ✅ Use Cursor's **terminal** to run smoke tests
- ✅ That *is* running "from Cursor" in the correct sense

You didn't hit a limitation in *your project*.
You hit a **boundary between code authoring and code execution**.

Once you run the smoke test from the terminal, your provider fallback + Twilio + Finnhub logic will behave exactly as designed.
