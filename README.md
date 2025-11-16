# Portfolio Analyst Service

A data-driven portfolio analysis system that ingests external market data and personal portfolio information to provide comprehensive market analysis and insights.

## Overview

This is an **analyst service**, not a trading bot. It collects data from external APIs, tracks your personal portfolio, stores everything in a database, and uses AI agents to analyze the information and provide insights.

## Architecture

### Data Module

The data module handles all data operations through a three-layer architecture:

1. **API Clients** (`data_module/api_clients/`)
   - `PriceFeed` - Fetches current and historical price data from Alpaca
   - `NewsFeed` - Fetches news articles from Alpaca
   - `AccountStatus` - Retrieves account information (equity, cash, etc.)
   - `OpenPositions` - Gets current open positions

2. **Repositories** (`data_module/repositories/`)
   - `PortfolioRepository` - Manages portfolio snapshots, positions, trades, and performance metrics
   - `NewsRepository` - Stores and queries news articles linked to symbols
   - `UniverseRepository` - Tracks symbols in your portfolio (current and historical)

3. **Data Manager** (`data_module/data_manager.py`)
   - Orchestrates data operations between API clients and repositories
   - Contains business logic for calculations (PnL, returns, metrics)
   - Provides unified interface for data access

### Database

SQLite database (`data/portfolio.db`) stores:
- **Portfolio snapshots** - Daily portfolio performance metrics
- **Positions** - Historical position data with P&L tracking
- **Trades** - Complete trade history with reasons and confidence
- **Performance metrics** - Calculated returns, Sharpe ratio, drawdown
- **News articles** - News linked to trading symbols
- **Portfolio universe** - Symbol tracking and metadata

See `data_module/database_diagram.md` for the complete schema.

## External APIs

### Alpaca Markets API

- **Paper Trading Endpoint**: `https://paper-api.alpaca.markets`
- **Data Endpoint**: `https://data.alpaca.markets`
- **Endpoints Used**:
  - `/v2/account` - Account status and equity
  - `/v2/positions` - Open positions
  - `/v1beta1/news` - News articles
  - `/v1beta3/crypto/us/bars` - Price data (crypto)

## Main Functionality

### Automated Data Collection

**Daily Portfolio Snapshots** (`scripts/daily_snapshot.py`)
- Runs twice daily (market open and close)
- Fetches current portfolio state from Alpaca
- Calculates performance metrics
- Saves snapshots and positions to database
- Updates portfolio universe

**News Collection** (`scripts/collect_news.py`)
- Fetches news for all tracked symbols
- Saves articles to database with symbol relationships
- Runs via GitHub Actions

### Analysis Service

**Analyst Service** (`analyst_service/`)
- Uses CrewAI agents (bull and bear analysts) for portfolio-level analysis
- Combines database-backed portfolio context (positions, performance, news) and optional technical analysis
- Produces portfolio-focused insights and risk stance instead of direct trading instructions

**Components**:
- `AnalystService` - Main analysis orchestrator (symbol-level and portfolio-level flows)
- `BullAgent` / `BearAgent` - AI agents for bullish/bearish analysis and debates
- `TechnicalAnalysis` - RSI, MACD, EMA signals (used primarily for symbol-level TA)

## Setup

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Configure environment**:
   Create a `.env` file with:
   ```
   APCA_API_KEY_ID=your_key
   APCA_API_SECRET_KEY=your_secret
   OPENAI_API_KEY=your_openai_key
   ```

3. **Run daily snapshot**:
   ```bash
   poetry run python scripts/daily_snapshot.py
   ```

4. **Run analysis**:
   ```bash
   poetry run python analyst_service/main.py
   ```

## Project Structure

```
├── data_module/          # Data ingestion and storage
│   ├── api_clients/       # External API integrations
│   ├── repositories/      # Database access layer
│   └── data_manager.py    # Orchestration layer
├── analyst_service/       # Analysis and AI agents
│   ├── agents/            # CrewAI agents (bull/bear)
│   ├── analysis/          # Analysis tools (sentiment, TA)
│   └── main.py            # Entry point
├── scripts/               # Automated scripts
│   ├── daily_snapshot.py  # Portfolio snapshot automation
│   └── collect_news.py   # News collection automation
└── data/                  # Database and exports
    └── portfolio.db       # SQLite database
```

## Documentation

- `data_module/database_diagram.md` - Database schema (Mermaid ER diagram)
- `data_module/data_manager_flowchart.md` - DataManager class flowchart
- `analyst_service/IMPLEMENTATION_PLAN.md` - Future enhancements

## Key Features

✅ **Data Ingestion**: Automated collection of portfolio and market data  
✅ **Database Storage**: Persistent storage of all portfolio and market data  
✅ **Performance Tracking**: Historical performance metrics and analysis  
✅ **News Integration**: News articles linked to trading symbols  
✅ **AI Analysis**: CrewAI-powered market analysis with bull/bear perspectives  
✅ **Automated Workflows**: GitHub Actions for daily data collection  
