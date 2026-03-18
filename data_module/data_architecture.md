# Data Architecture

```mermaid
flowchart TD
    UI["CLI / FastAPI / Scripts"] --> DM["DataManager"]

    subgraph External APIs
        PF["PriceFeed\nAlpaca stock bars"]
        NF["NewsFeed\nAlpaca news"]
    end

    subgraph Repositories
        PR["PortfolioRepository"]
        NR["NewsRepository"]
        UR["UniverseRepository"]
    end

    subgraph SQLite["SQLite: data/portfolio.db"]
        H["holdings"]
        T["trades"]
        CF["capital_flows"]
        DP["daily_prices"]
        AA["asset_analysis"]
        PS["portfolio_snapshots"]
        POS["positions"]
        NA["news_articles / news_symbols"]
        PU["portfolio_universe"]
    end

    DM --> PF
    DM --> NF

    DM --> PR
    DM --> NR
    DM --> UR

    PR --> H
    PR --> T
    PR --> CF
    PR --> DP
    PR --> AA
    PR --> PS
    PR --> POS
    NR --> NA
    UR --> PU

    DM -->|"record deposit / withdrawal"| CF
    DM -->|"record buy / sell"| T
    DM -->|"update current holdings"| H
    DM -->|"collect or backfill closes"| DP
    DM -->|"persist AI analysis"| AA
    DM -->|"save periodic snapshot"| PS
    DM -->|"save snapshot positions"| POS
    DM -->|"save fetched news"| NA
    DM -->|"update tracked symbols"| PU
```

## Runtime responsibilities

### `DataManager`

- Orchestrates reads and writes across the application
- Computes asset metrics, equity curve, and performance
- Coordinates price collection and analysis persistence

### `PortfolioRepository`

- Owns current holdings, trades, cash flows, daily prices, snapshots, and analysis storage

### `NewsRepository`

- Stores and queries normalized news article data and symbol links

### `UniverseRepository`

- Tracks current, historical, and watchlist symbols

## Primary data flows

### Transaction flow

```mermaid
sequenceDiagram
    participant User
    participant API as API/CLI
    participant DM as DataManager
    participant PR as PortfolioRepository
    participant DB as SQLite

    User->>API: record deposit or trade
    API->>DM: validate and dispatch
    DM->>PR: save event
    PR->>DB: insert capital_flow or trade
    DM->>PR: update holding state if trade
    PR->>DB: insert/update/delete holding
```

### Metrics flow

```mermaid
sequenceDiagram
    participant UI
    participant API as FastAPI
    participant DM as DataManager
    participant PR as PortfolioRepository
    participant PF as PriceFeed
    participant DB as SQLite

    UI->>API: GET asset metrics / equity curve / performance
    API->>DM: compute response
    DM->>PR: read holdings, trades, flows, daily prices
    alt missing recent price history
        DM->>PF: fetch current price fallback
    end
    PR->>DB: query stored facts
    DM-->>API: derived metrics
    API-->>UI: JSON response
```
