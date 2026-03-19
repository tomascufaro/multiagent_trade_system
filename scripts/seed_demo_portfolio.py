#!/usr/bin/env python3
"""Seed a demo portfolio database with deterministic sample data."""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "demo_portfolio.db"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _business_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _timestamp(day: date, hour: int, minute: int = 0) -> str:
    return datetime.combine(day, time(hour=hour, minute=minute)).isoformat()


def _make_trade(
    *,
    day: date,
    symbol: str,
    action: str,
    quantity: float,
    price: float,
    fees: float,
    notes: str,
    realized_pnl: float | None = None,
) -> dict:
    total_value = quantity * price
    net_amount = total_value + fees if action == "BUY" else total_value - fees
    return {
        "trade_id": f"demo_{symbol}_{action.lower()}_{uuid4().hex[:8]}",
        "timestamp": _timestamp(day, 15, 30),
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "price": price,
        "total_value": total_value,
        "commission": 0.0,
        "net_amount": net_amount,
        "reason": notes,
        "analysis_confidence": None,
        "fees": fees,
        "notes": notes,
        "realized_pnl": realized_pnl,
    }


def _seed_price_rows(days: list[date]) -> list[dict]:
    aapl = [
        182.0, 183.5, 184.2, 185.1, 184.7,
        186.2, 187.0, 188.4, 187.9, 189.2,
        190.1, 191.6, 192.2, 191.4, 193.0,
        194.3, 195.1, 194.8, 196.4, 197.2,
    ]
    msft = [
        410.0, 412.0, 413.2, 411.7, 414.5,
        416.0, 417.8, 419.1, 418.3, 420.4,
        422.0, 421.2, 423.7, 425.1, 424.0,
        426.5, 427.2, 428.4, 427.9, 429.6,
    ]
    nvda = [
        118.0, 119.4, 121.1, 122.8, 121.5,
        123.2, 124.9, 126.1, 125.4, 127.6,
        128.2, 129.5, 130.7, 129.9, 131.3,
        132.8, 133.6, 132.9, 134.2, 135.1,
    ]

    rows: list[dict] = []
    for idx, day in enumerate(days):
        rows.extend(
            [
                {"symbol": "AAPL", "date": day.isoformat(), "close": aapl[idx]},
                {"symbol": "MSFT", "date": day.isoformat(), "close": msft[idx]},
                {"symbol": "NVDA", "date": day.isoformat(), "close": nvda[idx]},
            ]
        )
    return rows


def seed_demo_database(db_path: Path) -> Path:
    os.environ["PORTFOLIO_DB_PATH"] = str(db_path)

    from data_module.repositories import PortfolioRepository, UniverseRepository

    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    portfolio_repo = PortfolioRepository(str(db_path))
    universe_repo = UniverseRepository(str(db_path))

    end_day = date.today()
    start_day = end_day - timedelta(days=27)
    business_days = _business_days(start_day, end_day)
    if len(business_days) < 20:
        raise RuntimeError("Expected at least 20 business days for the demo dataset")
    business_days = business_days[-20:]

    portfolio_repo.save_daily_prices(_seed_price_rows(business_days))

    portfolio_repo.save_capital_flow(
        {
            "timestamp": _timestamp(business_days[0], 9, 0),
            "type": "DEPOSIT",
            "amount": 30000.0,
            "notes": "Initial funding",
        }
    )
    portfolio_repo.save_capital_flow(
        {
            "timestamp": _timestamp(business_days[10], 9, 15),
            "type": "DEPOSIT",
            "amount": 5000.0,
            "notes": "Added capital after paycheck",
        }
    )
    portfolio_repo.save_capital_flow(
        {
            "timestamp": _timestamp(business_days[17], 10, 0),
            "type": "WITHDRAWAL",
            "amount": 1000.0,
            "notes": "Small cash withdrawal",
        }
    )

    trades = [
        _make_trade(
            day=business_days[1],
            symbol="AAPL",
            action="BUY",
            quantity=25,
            price=184.0,
            fees=3.0,
            notes="Opened AAPL starter position",
        ),
        _make_trade(
            day=business_days[2],
            symbol="MSFT",
            action="BUY",
            quantity=12,
            price=412.0,
            fees=3.0,
            notes="Opened MSFT position",
        ),
        _make_trade(
            day=business_days[3],
            symbol="NVDA",
            action="BUY",
            quantity=40,
            price=120.0,
            fees=4.0,
            notes="Opened NVDA position",
        ),
        _make_trade(
            day=business_days[12],
            symbol="NVDA",
            action="SELL",
            quantity=10,
            price=129.0,
            fees=3.0,
            notes="Trimmed NVDA into strength",
            realized_pnl=87.0,
        ),
        _make_trade(
            day=business_days[13],
            symbol="AAPL",
            action="BUY",
            quantity=10,
            price=190.0,
            fees=2.0,
            notes="Added to AAPL after breakout",
        ),
        _make_trade(
            day=business_days[16],
            symbol="MSFT",
            action="SELL",
            quantity=4,
            price=426.0,
            fees=2.0,
            notes="Scaled out of part of MSFT",
            realized_pnl=54.0,
        ),
    ]

    for trade in trades:
        portfolio_repo.save_trade(trade)

    portfolio_repo.create_holding(
        {
            "symbol": "AAPL",
            "quantity": 35,
            "avg_entry_price": 185.7142857143,
            "notes": "Seeded demo holding",
        }
    )
    portfolio_repo.create_holding(
        {
            "symbol": "MSFT",
            "quantity": 8,
            "avg_entry_price": 412.0,
            "notes": "Seeded demo holding",
        }
    )
    portfolio_repo.create_holding(
        {
            "symbol": "NVDA",
            "quantity": 30,
            "avg_entry_price": 120.0,
            "notes": "Seeded demo holding",
        }
    )

    for symbol, status in (("AAPL", "current"), ("MSFT", "current"), ("NVDA", "current")):
        universe_repo.add_symbol(symbol, status=status, notes="Seeded demo symbol")

    analysis_date = _timestamp(business_days[-1], 18, 0)
    seeded_analysis = [
        {
            "symbol": "AAPL",
            "analysis_date": analysis_date,
            "recommendation": "BUY",
            "confidence_score": 0.76,
            "current_price": 197.2,
            "analyst_notes": "Momentum remains constructive and the position is in profit.",
            "bull_case": "Trend and price action remain supportive over the seeded period.",
            "bear_case": "Recent gains leave room for a short-term pullback.",
            "technical_signals": "{'demo': true}",
        },
        {
            "symbol": "MSFT",
            "analysis_date": analysis_date,
            "recommendation": "HOLD",
            "confidence_score": 0.64,
            "current_price": 429.6,
            "analyst_notes": "Position remains healthy after partial profit taking.",
            "bull_case": "Trend is still positive and drawdowns were shallow in the seeded series.",
            "bear_case": "Upside may be slower after the recent climb.",
            "technical_signals": "{'demo': true}",
        },
        {
            "symbol": "NVDA",
            "analysis_date": analysis_date,
            "recommendation": "BUY",
            "confidence_score": 0.81,
            "current_price": 135.1,
            "analyst_notes": "Strong relative momentum and positive realized gains after trimming.",
            "bull_case": "The seeded series shows persistent strength with limited pullbacks.",
            "bear_case": "Higher volatility than the other seeded names raises risk.",
            "technical_signals": "{'demo': true}",
        },
    ]
    for analysis in seeded_analysis:
        portfolio_repo.save_asset_analysis(analysis)

    conn = sqlite3.connect(str(db_path))
    conn.execute("VACUUM")
    conn.close()
    return db_path


def main():
    db_path = Path(os.getenv("PORTFOLIO_DB_PATH", DEFAULT_DB_PATH))
    seeded_path = seed_demo_database(db_path)
    print(f"Seeded demo portfolio database at: {seeded_path}")
    print("Use it with:")
    print(f"  PORTFOLIO_DB_PATH={seeded_path} poetry run uvicorn backend.api.main:app --reload")


if __name__ == "__main__":
    main()
