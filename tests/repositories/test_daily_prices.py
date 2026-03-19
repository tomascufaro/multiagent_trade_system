import os

from data_module.repositories import PortfolioRepository


def test_daily_prices_insert_and_query(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    repo = PortfolioRepository()

    rows = [
        {"symbol": "AAPL", "date": "2026-02-01", "close": 150.0},
        {"symbol": "AAPL", "date": "2026-02-02", "close": 155.0},
    ]
    inserted = repo.save_daily_prices(rows)
    assert inserted >= 1

    prices = repo.get_daily_prices(["AAPL"], "2026-02-01", "2026-02-02")
    assert "AAPL" in prices
    assert len(prices["AAPL"]) == 2

    # Idempotent insert
    inserted_again = repo.save_daily_prices(rows)
    assert inserted_again == 0
