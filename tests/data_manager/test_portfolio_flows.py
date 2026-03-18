import pytest

from data_module.data_manager import DataManager


def test_core_flow(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    dm = DataManager()
    monkeypatch.setattr(dm.price_feed, "get_current_price", lambda symbol: 100.0)

    dm.record_deposit(1000.0, notes="seed")
    dm.record_buy("AAPL", 2, 100.0)

    portfolio = dm.get_portfolio_value()
    assert portfolio["total_equity"] == pytest.approx(200.0)
    assert portfolio["net_contributed"] == pytest.approx(1000.0)

    dm.record_sell("AAPL", 1, 120.0, fees=0.0)

    holdings = dm.get_open_positions()
    assert len(holdings) == 1
    assert holdings[0]["quantity"] == pytest.approx(1.0)
