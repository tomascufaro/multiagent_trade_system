#!/usr/bin/env python3
"""Manual AI analysis check (live LLM + data)."""
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data_module.data_manager import DataManager


def main(symbol: str = "AAPL"):
    dm = DataManager()
    analysis = dm.analyze_stock(symbol)
    print(f"Symbol: {analysis.get('symbol')}")
    print(f"Recommendation: {analysis.get('recommendation')}")
    print(f"Summary: {analysis.get('analyst_notes')}")
    if not analysis.get('analyst_notes'):
        raise SystemExit("Analysis summary missing")
    print("OK")


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    main(symbol)
