# Portfolio Analyst Service

Single-user portfolio tracking and analysis application built around manual trade entry, a FastAPI backend, a vanilla JS dashboard, and optional AI-generated analysis.

## What It Is

This project is not an automated trading bot. The current product is:

- A manual portfolio ledger for deposits, withdrawals, buys, and sells
- A local web dashboard with portfolio summary, asset metrics, equity curve, and transaction entry
- A data layer that stores portfolio facts in SQLite and derives views from them
- An optional AI analysis flow for symbol-level and portfolio-level commentary
- A weekly email reporting flow driven by GitHub Actions

## Current Product Surface

### Manual portfolio workflow

You manage the portfolio by recording:

- Deposits and withdrawals
- Buy and sell trades
- Optional notes and fees on trades

Holdings are derived from the recorded trade history and stored in SQLite for current-state reads.

### Web dashboard

The dashboard is served by the FastAPI app and currently provides:

- Summary cards for equity, P&L, net contributions, total return, and max drawdown
- Asset metrics table with deterministic metrics and technical signal summaries
- Expandable detail rows for RSI, MACD, SMA50/200, EMA20, EMA50, returns, volatility, drawdown, and realized P&L
- Equity curve chart derived from trades, capital flows, and stored daily prices
- Transaction modal for deposit, withdrawal, buy, and sell entry
- Analyze button for on-demand AI analysis per symbol
- Latest cached analysis is loaded from `asset_analysis` on page load when present

### CLI

The `portfolio` CLI is available through Poetry script entrypoints and supports:

- `portfolio deposit`
- `portfolio withdraw`
- `portfolio trade`
- `portfolio show`
- `portfolio analyze`
- `portfolio history`

### Automated workflows

- `scripts/daily_snapshot.py` updates the tracked universe, stores daily prices, saves a portfolio snapshot, and writes a JSON run summary
- `scripts/collect_news.py` fetches Alpaca news for tracked symbols and stores the results
- `scripts/backfill_prices.py` backfills `daily_prices` for held or previously traded symbols
- `scripts/generate_report.py` runs portfolio analysis, renders HTML, emails it, and saves artifacts under `data/reports/`

## Architecture

### Data layer

The application uses a small layered architecture:

1. API clients in `data_module/api_clients/`
   - `PriceFeed` fetches stock bar data from Alpaca
   - `NewsFeed` fetches news from Alpaca
2. Repositories in `data_module/repositories/`
   - `PortfolioRepository`
   - `NewsRepository`
   - `UniverseRepository`
3. `DataManager` in `data_module/data_manager.py`
   - orchestrates reads and writes
   - calculates derived metrics
   - coordinates price/news collection and portfolio analysis flows

### Storage

SQLite database: `data/portfolio.db`

Core tables:

- `holdings`
- `trades`
- `capital_flows`
- `daily_prices`
- `portfolio_snapshots`
- `asset_analysis`
- news and universe tracking tables

### Backend and frontend

- FastAPI backend: `backend/api/main.py`
- Frontend: `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`
- Static frontend assets are served by the FastAPI app

### AI analysis

AI analysis is optional and depends on `OPENAI_API_KEY` plus the CrewAI-based analysis stack under `analyst_service/`.

Current implemented flows:

- Symbol-level analysis on demand through `POST /api/analysis/{symbol}`
- Portfolio-level analysis used by the reporting script

## External Dependencies

### Alpaca

Implemented API usage:

- Stock bars endpoint via `https://data.alpaca.markets/v2/stocks/bars`
- News endpoint via `https://data.alpaca.markets/v1beta1/news`

### OpenAI / CrewAI

Required only for AI analysis and weekly portfolio reports.

## Setup

1. Install dependencies:

```bash
poetry install
```

2. Create `.env`:

```env
APCA_API_KEY_ID=your_key
APCA_API_SECRET_KEY=your_secret
OPENAI_API_KEY=your_openai_key
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
REPORT_FROM=reports@example.com
REPORT_TO=investor@example.com
```

3. Optional: seed or backfill price history for existing symbols:

```bash
poetry run python scripts/backfill_prices.py
```

## Running The App

### Web app

Start the server:

```bash
poetry run uvicorn backend.api.main:app --reload
```

Open:

- `http://localhost:8000`

### CLI examples

```bash
portfolio deposit 10000 --notes "Initial funding"
portfolio trade BUY AAPL 10 150.50 --fees 1.50 --notes "Entry"
portfolio show
portfolio history --days 30
```

### Snapshot and data collection

```bash
poetry run python scripts/daily_snapshot.py
poetry run python scripts/collect_news.py
```

### Run analysis directly

```bash
poetry run python analyst_service/main.py
```

### Demo seed for full UI testing

If you want a safe, non-production dataset with visible metrics, realized P&L, and an equity curve:

```bash
poetry run python scripts/seed_demo_portfolio.py
APCA_API_KEY_ID= APCA_API_SECRET_KEY= PORTFOLIO_DB_PATH=data/demo_portfolio.db poetry run uvicorn backend.api.main:app --reload
```

The demo database contains:

- 3 seeded stocks: `AAPL`, `MSFT`, `NVDA`
- 4 weeks of business-day close prices
- deposits, a withdrawal, buys, and partial sells
- current holdings plus realized and unrealized P&L
- cached analysis rows in `asset_analysis` that appear in the dashboard without running live AI

If you want to test live AI analysis on top of the seeded portfolio, launch the app with valid Alpaca and OpenAI credentials and then click `Analyze` in the UI.

### Generate weekly report locally

```bash
poetry run python scripts/generate_report.py
```

## API Surface

Implemented endpoints:

- `GET /`
- `GET /api/portfolio/summary`
- `GET /api/portfolio/asset-metrics`
- `GET /api/portfolio/equity-curve`
- `GET /api/portfolio/performance`
- `GET /api/positions`
- `GET /api/trades`
- `GET /api/analysis/latest`
- `POST /api/trades`
- `POST /api/deposit`
- `POST /api/withdraw`
- `POST /api/analysis/{symbol}`

## Testing

Run the automated suite:

```bash
poetry run pytest
```

Manual smoke checks for live integrations:

```bash
poetry run python tests/manual/api_smoke.py
poetry run python tests/manual/price_feed_smoke.py AAPL
poetry run python tests/manual/analysis_smoke.py AAPL
```

## Documentation

- `data_module/database_diagram.md` - SQLite schema and table relationships
- `data_module/data_architecture.md` - data flow across clients, repositories, and `DataManager`
- `backend/api_diagram.md` - FastAPI route map and request flow

## Known Gaps

- Live analysis and live price collection still depend on valid Alpaca, OpenAI, and SMTP credentials
- There is no authentication or multi-user support
- The app is optimized for a single local operator, not a hosted SaaS deployment
