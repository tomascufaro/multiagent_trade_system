import os
import importlib

import httpx
import pytest


def _load_app(tmp_path):
    db_path = tmp_path / "phase2_test.db"
    os.environ["PORTFOLIO_DB_PATH"] = str(db_path)

    import backend.api.main as main_module
    importlib.reload(main_module)

    # Mock external price feed calls
    main_module._dm.price_feed.get_current_price = lambda symbol: 100.0

    transport = httpx.ASGITransport(app=main_module.app)
    return transport


@pytest.fixture()
async def client(tmp_path):
    transport = _load_app(tmp_path)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_core_api_flow(client):
    # Deposit
    resp = await client.post("/api/deposit", json={"amount": 1000, "notes": "test"})
    assert resp.status_code == 200

    # Buy trade
    resp = await client.post(
        "/api/trades",
        json={
            "action": "BUY",
            "symbol": "AAPL",
            "quantity": 10,
            "price": 50,
            "fees": 1.0,
            "notes": "buy",
        },
    )
    assert resp.status_code == 200

    # Positions
    resp = await client.get("/api/positions")
    assert resp.status_code == 200
    positions = resp.json()
    assert len(positions) == 1
    assert positions[0]["symbol"] == "AAPL"

    # Sell trade
    resp = await client.post(
        "/api/trades",
        json={
            "action": "SELL",
            "symbol": "AAPL",
            "quantity": 5,
            "price": 60,
            "fees": 1.0,
            "notes": "sell",
        },
    )
    assert resp.status_code == 200

    # Trades history
    resp = await client.get("/api/trades")
    assert resp.status_code == 200
    trades = resp.json()
    assert len(trades) >= 2

    # Summary
    resp = await client.get("/api/portfolio/summary")
    assert resp.status_code == 200
    summary = resp.json()
    assert "total_equity" in summary
    assert "net_contributed" in summary
    assert "positions" in summary
