# Product Requirements Document (PRD)

## 1. Problem Statement

A lightweight, local-first agent that monitors selected stocks and explains *why* meaningful price movements occurred, without relying on cloud infrastructure or real-time systems.

Most stock alerts only report **what** happened (price up/down), not **why**.
This project focuses on generating concise, human-readable explanations that connect price movement to recent news or market context.

The system is designed for **personal use**, low cost, and clarity — not prediction, trading, or automation.

---

## 2. Goals

* Detect meaningful stock price movements based on configurable thresholds
* Generate short, factual explanations for those movements
* Run entirely on a local machine by default (Mac mini M2, 8GB RAM)
* Execute periodically and exit (no long-running services)
* Produce deterministic, readable output suitable for SMS or email

---

## 3. Non-Goals (Explicit)

This project will **not**:

* Predict future stock prices
* Provide trading or investment advice
* Perform portfolio optimization
* Use machine learning for price prediction
* Require cloud infrastructure to function
* Include a web UI (v0.x)
* Optimize for low-latency or high concurrency

---

## 4. Core User Flow

1. Scheduler triggers execution (cron / launchd)
2. System fetches latest stock prices
3. System compares prices against prior reference point
4. If threshold is exceeded:
   * Gather relevant recent news (optional but preferred)
   * Generate a short explanation using a local LLM
5. Send notification via configured channel
6. Persist minimal execution metadata
7. Exit

---

## 5. Inputs

* List of stock symbols (e.g., AAPL, NVDA)
* Percentage change threshold (e.g., ±1.5%)
* Notification channel:
  * SMS
  * Email
  * Console output (fallback)
* Execution schedule (external to application)
* Environment configuration via environment variables

---

## 6. Outputs

* A short natural-language explanation:
  * Maximum 2–3 sentences
  * Plain, factual tone
  * No speculation or prediction
* Notification payload containing:
  * Stock symbol
  * Percentage change
  * Explanation text
  * Timestamp

---

## 7. Success Criteria

The system is considered successful if:

* It runs locally without cloud dependencies
* A single execution completes in under 30 seconds
* It produces clear, non-hallucinatory explanations
* It triggers notifications only when thresholds are crossed
* Core logic is covered by automated tests
* Behavior aligns strictly with defined non-goals

---

## 8. Engineering Constraints

* Implementation must comply with rules defined in `.cursor/rules/`
* Test-driven development is required for core logic
* Local-first execution is the default posture
* Cloud portability is allowed but not required for v0.x

---

## 9. MVP Scope (v0.1)

Included:

* Single-user configuration
* One or more tracked stock symbols
* Threshold-based alerts
* Local LLM integration (Ollama)
* One notification channel (console/email)

Excluded:

* User accounts
* Historical dashboards
* Real-time streaming
* Multi-user support

---

## 10. Open Questions (Deferred)

* Which news sources provide the best signal-to-noise ratio?
* Should explanations cite sources explicitly?
* Should alerts be batched or always immediate?

These are intentionally deferred until after v0.1 is functional.
