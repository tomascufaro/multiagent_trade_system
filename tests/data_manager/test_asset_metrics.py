from datetime import datetime, timedelta

from data_module.data_manager import DataManager
from data_module.repositories import PortfolioRepository


def test_compute_asset_metrics(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    repo = PortfolioRepository()
    repo.create_holding({"symbol": "AAPL", "quantity": 10, "avg_entry_price": 100})

    start = datetime(2025, 12, 1)
    rows = []
    for i in range(120):
        day = start + timedelta(days=i)
        rows.append({"symbol": "AAPL", "date": day.date().isoformat(), "close": 100 + i})
    repo.save_daily_prices(rows)

    dm = DataManager()
    dm.price_feed.get_current_price = lambda symbol: 200.0

    metrics = dm.compute_asset_metrics(days=90)
    assert len(metrics) == 1
    asset = metrics[0]
    assert asset["symbol"] == "AAPL"
    assert "signals" in asset
    assert "rsi" in asset["signals"]
