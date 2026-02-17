"""FastAPI application for Phase 2 MVP."""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from data_module.data_manager import DataManager

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="Portfolio MVP API", version="2.0.0")

# Single DataManager instance to reuse repositories and clients
_dm = DataManager()


class TradeCreate(BaseModel):
    action: str = Field(..., min_length=3, max_length=4)
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fees: float = Field(0.0, ge=0)
    notes: Optional[str] = None

    @field_validator("symbol")
    @classmethod
    def _symbol_upper(cls, value: str) -> str:
        return value.upper()

    @field_validator("action")
    @classmethod
    def _action_upper(cls, value: str) -> str:
        return value.upper()


class CapitalFlowCreate(BaseModel):
    amount: float = Field(..., gt=0)
    notes: Optional[str] = None


@app.get("/")
def root() -> FileResponse:
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.get("/api/portfolio/summary")
def portfolio_summary():
    return _dm.get_portfolio_value()


@app.get("/api/positions")
def positions():
    return _dm.get_open_positions()


@app.get("/api/trades")
def trades(days: int = 30, symbol: Optional[str] = None):
    return _dm.portfolio_repo.get_trade_history(days=days, symbol=symbol)


@app.post("/api/trades")
def create_trade(trade: TradeCreate):
    if trade.action == "BUY":
        return _dm.record_buy(trade.symbol, trade.quantity, trade.price, trade.fees, trade.notes)
    if trade.action == "SELL":
        return _dm.record_sell(trade.symbol, trade.quantity, trade.price, trade.fees, trade.notes)
    raise HTTPException(status_code=400, detail="Invalid action; use BUY or SELL")


@app.post("/api/deposit")
def deposit(flow: CapitalFlowCreate):
    return _dm.record_deposit(flow.amount, flow.notes)


@app.post("/api/withdraw")
def withdraw(flow: CapitalFlowCreate):
    return _dm.record_withdrawal(flow.amount, flow.notes)


@app.post("/api/analysis/{symbol}")
def analyze(symbol: str):
    return _dm.analyze_stock(symbol)


# Static assets (JS/CSS)
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
