import importlib
import os

import httpx
import pytest


def _load_app(tmp_path):
    db_path = tmp_path / "api_analysis_test.db"
    os.environ["PORTFOLIO_DB_PATH"] = str(db_path)

    import backend.api.main as main_module
    importlib.reload(main_module)
    return main_module


@pytest.fixture()
async def client(tmp_path):
    module = _load_app(tmp_path)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=module.app),
        base_url="http://test",
    ) as http_client:
        yield http_client, module


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_post_analysis_endpoint_returns_analysis_payload(client):
    http_client, module = client
    module._dm.analyze_stock = lambda symbol: {
        "symbol": symbol,
        "analysis_date": "2026-01-01T00:00:00",
        "recommendation": "BUY",
        "confidence_score": 0.7,
        "current_price": 100.0,
        "analyst_notes": "Mocked analysis response",
        "bull_case": "Bull case",
        "bear_case": "Bear case",
        "technical_signals": "{}",
    }

    response = await http_client.post("/api/analysis/aapl")

    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["recommendation"] == "BUY"
    assert "analyst_notes" in payload
