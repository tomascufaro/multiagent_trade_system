import importlib
import os
from datetime import datetime, timedelta

import httpx
import pytest


def _load_app(tmp_path):
    db_path = tmp_path / "api_test.db"
    os.environ["PORTFOLIO_DB_PATH"] = str(db_path)

    import backend.api.main as main_module
    importlib.reload(main_module)

    # Mock price feed
    main_module._dm.price_feed.get_current_price = lambda symbol: 100.0

    # Seed minimal data
    repo = main_module._dm.portfolio_repo
    repo.create_holding({"symbol": "AAPL", "quantity": 10, "avg_entry_price": 90})
    day1 = datetime.now().date() - timedelta(days=1)
    repo.save_daily_prices([
        {"symbol": "AAPL", "date": day1.isoformat(), "close": 100.0}
    ])
    repo.save_asset_analysis(
        {
            "symbol": "AAPL",
            "analysis_date": datetime.now().isoformat(),
            "recommendation": "BUY",
            "confidence_score": 0.7,
            "current_price": 100.0,
            "analyst_notes": "Cached analysis",
            "bull_case": "Bull case",
            "bear_case": "Bear case",
            "technical_signals": "{}",
        }
    )

    return httpx.ASGITransport(app=main_module.app)


@pytest.fixture()
async def client(tmp_path):
    transport = _load_app(tmp_path)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_asset_metrics_endpoint(client):
    resp = await client.get("/api/portfolio/asset-metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_equity_curve_endpoint(client):
    resp = await client.get("/api/portfolio/equity-curve")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.anyio
async def test_performance_endpoint(client):
    resp = await client.get("/api/portfolio/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


@pytest.mark.anyio
async def test_latest_analysis_endpoint(client):
    resp = await client.get("/api/analysis/latest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["AAPL"]["recommendation"] == "BUY"
