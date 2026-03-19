from datetime import datetime, timedelta

from data_module.data_manager import DataManager
from data_module.repositories import PortfolioRepository


def test_equity_curve_simple(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    repo = PortfolioRepository()

    day1 = datetime.now().date() - timedelta(days=2)
    day2 = day1 + timedelta(days=1)

    repo.save_capital_flow({
        "timestamp": f"{day1}T10:00:00",
        "type": "DEPOSIT",
        "amount": 1000.0,
        "notes": "test",
    })

    trade = {
        "trade_id": "t1",
        "timestamp": f"{day1}T11:00:00",
        "symbol": "AAPL",
        "action": "BUY",
        "quantity": 5.0,
        "price": 100.0,
        "total_value": 500.0,
        "commission": 0.0,
        "net_amount": 500.0,
        "reason": "test",
        "analysis_confidence": None,
        "fees": 0.0,
        "notes": None,
        "realized_pnl": None,
    }
    repo.save_trade(trade)

    repo.save_daily_prices([
        {"symbol": "AAPL", "date": day1.isoformat(), "close": 100.0},
        {"symbol": "AAPL", "date": day2.isoformat(), "close": 110.0},
    ])

    dm = DataManager()
    curve = dm.compute_equity_curve(days=5)

    # Keep only the last two dates we inserted
    curve = [p for p in curve if p["date"] in {day1.isoformat(), day2.isoformat()}]
    assert len(curve) == 2

    values = {p["date"]: p["equity"] for p in curve}
    assert values[day1.isoformat()] == 1000.0
    assert values[day2.isoformat()] == 1050.0
