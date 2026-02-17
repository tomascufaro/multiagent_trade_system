# Phase 2: Web MVP (Thin API + Thin UI)

## Overview
Provide a simple web wrapper around Phase 1 functionality so the MVP can be verified via a browser. Keep the architecture minimal, reuse Phase 1 data flow, and avoid new complexity (no multi-user, no auth, no new service layer).

## Principles
- Single user (user_id = 1), no authentication
- Reuse Phase 1 `DataManager` and `PortfolioRepository`
- Minimal API surface, minimal UI pages
- Keep objects testable and visible

## Goals
- Expose core Phase 1 actions via HTTP
- Provide a simple UI to perform manual verification
- Keep dependencies and moving parts minimal

---

## 1. Minimal Backend API (FastAPI)

### 1.1 Technology
- FastAPI (lightweight, quick to wire)
- No auth, no WebSockets, no background jobs

### 1.2 Structure
```
backend/
├── api/
│   ├── __init__.py
│   └── main.py
└── schemas.py
```

### 1.3 API Endpoints (MVP Only)
```
GET    /api/portfolio/summary
GET    /api/positions
GET    /api/trades
POST   /api/trades
POST   /api/deposit
POST   /api/withdraw
POST   /api/analysis/{symbol}
```

### 1.4 `backend/api/main.py`
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from data_module.data_manager import DataManager

app = FastAPI(title="Portfolio MVP API", version="2.0.0")

dm = DataManager()

class TradeCreate(BaseModel):
    action: str  # BUY or SELL
    symbol: str
    quantity: float
    price: float
    fees: float = 0.0
    notes: Optional[str] = None

class CapitalFlowCreate(BaseModel):
    amount: float
    notes: Optional[str] = None

@app.get("/api/portfolio/summary")
def portfolio_summary():
    return dm.get_portfolio_value()

@app.get("/api/positions")
def positions():
    return dm.get_open_positions()

@app.get("/api/trades")
def trades(days: int = 30, symbol: Optional[str] = None):
    return dm.portfolio_repo.get_trade_history(days=days, symbol=symbol)

@app.post("/api/trades")
def create_trade(trade: TradeCreate):
    if trade.action.upper() == "BUY":
        return dm.record_buy(trade.symbol, trade.quantity, trade.price, trade.fees, trade.notes)
    if trade.action.upper() == "SELL":
        return dm.record_sell(trade.symbol, trade.quantity, trade.price, trade.fees, trade.notes)
    raise HTTPException(status_code=400, detail="Invalid action")

@app.post("/api/deposit")
def deposit(flow: CapitalFlowCreate):
    return dm.record_deposit(flow.amount, flow.notes)

@app.post("/api/withdraw")
def withdraw(flow: CapitalFlowCreate):
    return dm.record_withdrawal(flow.amount, flow.notes)

@app.post("/api/analysis/{symbol}")
def analyze(symbol: str):
    return dm.analyze_stock(symbol)
```

---

## 2. Minimal Frontend (Simple React or HTML)

### Option A: Minimal React (recommended if you already use React)
Pages:
- Dashboard: summary + positions
- Trades: trade form + history
- Analysis: analyze symbol + show result

### Option B: Server-rendered HTML (fastest to verify)
- A single page with forms for deposit/withdraw/trade/analyze
- Simple tables for positions and trades

No state management, no charts, no auth, no routing beyond 2-3 pages.

---

## 3. Testing Strategy (MVP)

- API smoke tests (pytest + FastAPI test client)
- Manual UI testing flows:
  1. Deposit
  2. Buy
  3. Show positions
  4. Sell
  5. Analyze
  6. View trades

---

## 4. Non-Goals (Deferred)
- Multi-user support
- JWT authentication
- WebSockets / real-time updates
- Fundamental data integration
- Rebalancing engine
- Options trading
- Advanced charts / analytics dashboards

---

## 5. Success Criteria
Phase 2 is complete when:
1. ✅ All Phase 1 actions are reachable via HTTP
2. ✅ Web UI can perform deposit, trade, show positions, analyze
3. ✅ No new complex dependencies or services were added
4. ✅ You can manually verify every object and flow
