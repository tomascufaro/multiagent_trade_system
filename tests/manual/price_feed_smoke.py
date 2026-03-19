#!/usr/bin/env python3
"""Manual price feed check (live API)."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data_module.api_clients.price_feed import PriceFeed


def main(symbol: str = "AAPL"):
    feed = PriceFeed()
    bars = feed.get_historical_data(symbol, timeframe="1D", limit=250, days_back=365)
    print(f"Symbol: {symbol}")
    print(f"Bars returned: {len(bars)}")
    if not bars:
        print("No data returned.")
        return
    latest = bars[0]
    print(f"Latest bar: {latest}")
    print("OK")


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    main(symbol)
