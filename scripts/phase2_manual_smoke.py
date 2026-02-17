"""Manual smoke test for Phase 2 web MVP.

Prerequisites:
- Run: poetry run uvicorn backend.api.main:app --reload
- Ensure .env contains API keys if you want real price/news calls

This script calls the local API endpoints and prints results.
"""
import json
import sys
from typing import Any, Dict

import requests

BASE_URL = "http://localhost:8000"


def _post(path: str, payload: Dict[str, Any]):
    resp = requests.post(f"{BASE_URL}{path}", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _get(path: str):
    resp = requests.get(f"{BASE_URL}{path}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    print("Phase 2 Manual Smoke Test")

    print("\n1) Deposit")
    print(_post("/api/deposit", {"amount": 1000, "notes": "manual smoke"}))

    print("\n2) Buy trade")
    print(
        _post(
            "/api/trades",
            {
                "action": "BUY",
                "symbol": "AAPL",
                "quantity": 5,
                "price": 150,
                "fees": 1.0,
                "notes": "manual buy",
            },
        )
    )

    print("\n3) Positions")
    print(json.dumps(_get("/api/positions"), indent=2))

    print("\n4) Sell trade")
    print(
        _post(
            "/api/trades",
            {
                "action": "SELL",
                "symbol": "AAPL",
                "quantity": 2,
                "price": 155,
                "fees": 1.0,
                "notes": "manual sell",
            },
        )
    )

    print("\n5) Trades")
    print(json.dumps(_get("/api/trades"), indent=2))

    print("\n6) Summary")
    print(json.dumps(_get("/api/portfolio/summary"), indent=2))

    print("\n7) Analyze")
    print(json.dumps(_post("/api/analysis/AAPL", {}), indent=2))

    print("\nDone")


if __name__ == "__main__":
    try:
        main()
    except requests.RequestException as exc:
        print(f"Error: {exc}")
        sys.exit(1)
