# System Architecture

## Overview

Stock Tracker follows a layered architecture with clear separation of concerns. The system is designed for local execution with no cloud dependencies.

---

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Presentation["Presentation Layer"]
        CLI[CLI Interface]
    end
    
    subgraph Application["Application Layer"]
        StockService[Stock Service]
        PortfolioService[Portfolio Service]
        ExportService[Export Service]
    end
    
    subgraph Domain["Domain Layer"]
        StockModel[Stock Model]
        PortfolioModel[Portfolio Model]
        TransactionModel[Transaction Model]
    end
    
    subgraph Infrastructure["Infrastructure Layer"]
        DataProvider[Data Provider]
        Cache[Local Cache]
        Storage[File Storage]
    end
    
    subgraph External["External"]
        YFinance[yfinance API]
    end
    
    CLI --> StockService
    CLI --> PortfolioService
    CLI --> ExportService
    
    StockService --> StockModel
    PortfolioService --> PortfolioModel
    PortfolioService --> TransactionModel
    
    StockService --> DataProvider
    StockService --> Cache
    PortfolioService --> Storage
    ExportService --> Storage
    
    DataProvider --> YFinance
```

---

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Service
    participant Cache
    participant Provider
    participant API as yfinance

    User->>CLI: Request stock price
    CLI->>Service: get_price(symbol)
    Service->>Cache: check_cache(symbol)
    
    alt Cache Hit
        Cache-->>Service: cached_price
    else Cache Miss
        Service->>Provider: fetch_price(symbol)
        Provider->>API: get_data(symbol)
        API-->>Provider: raw_data
        Provider-->>Service: parsed_price
        Service->>Cache: store(symbol, price)
    end
    
    Service-->>CLI: price_result
    CLI-->>User: Display price
```

---

## Component Responsibilities

### Presentation Layer
| Component | Responsibility |
|-----------|----------------|
| CLI Interface | Parse commands, format output, handle user interaction |

### Application Layer
| Component | Responsibility |
|-----------|----------------|
| Stock Service | Fetch and process stock data |
| Portfolio Service | Manage holdings, calculate performance |
| Export Service | Generate CSV/JSON exports |

### Domain Layer
| Component | Responsibility |
|-----------|----------------|
| Stock Model | Represent stock data with validation |
| Portfolio Model | Represent holdings and positions |
| Transaction Model | Represent buy/sell transactions |

### Infrastructure Layer
| Component | Responsibility |
|-----------|----------------|
| Data Provider | Abstract external API access |
| Local Cache | Cache responses to reduce API calls |
| File Storage | Persist portfolio data locally |

---

## Design Principles

### Dependency Rule
Dependencies point inward. Inner layers know nothing about outer layers.

```
Presentation → Application → Domain ← Infrastructure
```

### Interface Segregation
Services depend on abstractions, not concrete implementations.

```python
# Abstract interface
class DataProvider(Protocol):
    def fetch_price(self, symbol: str) -> float: ...

# Concrete implementation
class YFinanceProvider:
    def fetch_price(self, symbol: str) -> float:
        # Implementation details
```

### Single Responsibility
Each component has one reason to change.

---

## Error Handling Strategy

```mermaid
flowchart LR
    Error[Error Occurs] --> Catch[Catch at Boundary]
    Catch --> Log[Log with Context]
    Log --> Transform[Transform to User Error]
    Transform --> Return[Return Clean Message]
```

- Errors are caught at service boundaries
- Infrastructure errors are logged with full context
- User-facing errors are clean and actionable
- Stack traces never exposed to users

---

## Future Considerations

Areas identified for potential expansion (not current scope):

- Web interface (if needed)
- Database storage (if file storage becomes limiting)
- Background refresh (if real-time data needed)

These are documented for awareness, not implementation.
