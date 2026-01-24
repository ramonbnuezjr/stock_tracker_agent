# Activity Log

## 2026-01-24

### Session 1: Project Bootstrap
- Project initialized via Master Cursor Bootstrap Prompt
- Created `.cursor/` directory structure
- Established coding standards (standards.mdc)
- Established security rules (security.mdc)
- Established workflow rules (workflow.mdc)
- Created control documents (instructions.md, architecture.md, roadmap.md)
- Created root documentation (PRD.md, README.md)

### Session 2: v0.1 MVP Implementation
- Created project configuration (pyproject.toml, requirements.txt)
- Implemented Pydantic models (Stock, PricePoint, PriceChange, Alert, Explanation)
- Implemented config.py with pydantic-settings
- Implemented storage adapter (SQLite)
- Implemented yfinance adapter for stock prices
- Implemented news adapter (Google News RSS)
- Implemented Ollama adapter for LLM explanations
- Implemented email adapter for notifications
- Implemented all four services:
  - PriceService: Fetch prices, detect threshold breaches
  - NewsService: Fetch headlines for context
  - ExplanationService: Generate LLM explanations
  - NotificationService: Route alerts to channels
- Implemented CLI entry point (main.py)
- Created comprehensive unit tests
- Created integration tests
- Updated all documentation

### Session 3: v0.2 SMS & Messaging Implementation
- Implemented Twilio SMS adapter with full API integration
- Implemented Apple Messages adapter using AppleScript (macOS)
- Implemented Email-to-SMS adapter via carrier gateways (MMS)
- Added automatic channel selection with fallback logic
- Added `ENABLE_TWILIO` configuration flag
- Added `NOTIFICATION_CHANNEL=auto` option
- Updated notification service with fallback chain: Twilio → Apple Messages → Console
- Added test suite for notification channels
- Tested Apple Messages successfully on local Mac
- Twilio A2P registration pending (deferred)

### Next Steps
- Complete Twilio A2P registration when available
- Set up cron job for periodic execution
- Consider batch notification mode for v1.0
