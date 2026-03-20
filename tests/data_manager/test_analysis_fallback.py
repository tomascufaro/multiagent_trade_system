from data_module.data_manager import DataManager
from data_module.repositories import PortfolioRepository


def test_analyze_stock_falls_back_when_ai_service_fails(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    repo = PortfolioRepository()
    repo.create_holding({"symbol": "AAPL", "quantity": 2, "avg_entry_price": 100})

    dm = DataManager()
    dm.price_feed.get_current_price = lambda symbol: 120.0
    dm.price_feed.get_historical_data = lambda symbol, **kwargs: [
        {"close": 100.0},
        {"close": 101.0},
        {"close": 102.0},
        {"close": 103.0},
        {"close": 104.0},
        {"close": 105.0},
        {"close": 106.0},
        {"close": 107.0},
        {"close": 108.0},
        {"close": 109.0},
        {"close": 110.0},
        {"close": 111.0},
        {"close": 112.0},
        {"close": 113.0},
        {"close": 114.0},
        {"close": 115.0},
        {"close": 116.0},
        {"close": 117.0},
        {"close": 118.0},
        {"close": 119.0},
        {"close": 120.0},
    ]
    monkeypatch.setattr(
        "analyst_service.analysis.analyst_service.AnalystService.analyze",
        lambda self, symbol: (_ for _ in ()).throw(RuntimeError("LLM unavailable")),
    )

    analysis = dm.analyze_stock("aapl")

    assert analysis["symbol"] == "AAPL"
    assert analysis["recommendation"] in {"BUY", "SELL", "HOLD"}
    assert "Fallback analysis generated" in analysis["analyst_notes"]
