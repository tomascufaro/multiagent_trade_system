import pandas as pd
import numpy as np
from typing import Dict, Any
import yaml
import os


class TechnicalAnalysis:
    def __init__(self):
        # Load settings from yaml file
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml"
        )
        with open(config_path, "r") as f:
            settings = yaml.safe_load(f)

        # Get technical analysis parameters from settings
        ta_settings = settings["technical"]
        self.rsi_period = ta_settings["rsi"]["period"]
        self.macd_fast = ta_settings["macd"]["fast_period"]
        self.macd_slow = ta_settings["macd"]["slow_period"]
        self.macd_signal = ta_settings["macd"]["signal_period"]
        self.ema_short = ta_settings["ema"]["short_period"]
        self.ema_long = ta_settings["ema"]["long_period"]

    def calculate_rsi(self, prices: list, period: int = None) -> float:
        """Calculate Relative Strength Index."""
        period = period or self.rsi_period
        prices = pd.Series(prices)
        delta = prices.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def calculate_macd(self, prices: list) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        prices = pd.Series(prices)

        exp1 = prices.ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = prices.ewm(span=self.macd_slow, adjust=False).mean()

        macd = exp1 - exp2
        signal = macd.ewm(span=self.macd_signal, adjust=False).mean()

        return {
            "macd": macd.iloc[-1],
            "signal": signal.iloc[-1],
            "histogram": macd.iloc[-1] - signal.iloc[-1],
        }

    def calculate_ema(self, prices: list) -> Dict[str, float]:
        """Calculate Exponential Moving Averages."""
        prices = pd.Series(prices)

        short_ema = prices.ewm(span=self.ema_short, adjust=False).mean()
        long_ema = prices.ewm(span=self.ema_long, adjust=False).mean()

        return {
            "short_ema": short_ema.iloc[-1],
            "long_ema": long_ema.iloc[-1],
            "crossover": short_ema.iloc[-1] - long_ema.iloc[-1],
        }

    def get_signals(self, prices: list) -> Dict[str, Any]:
        """Get all technical signals."""
        return {
            "rsi": self.calculate_rsi(prices),
            "macd": self.calculate_macd(prices),
            "ema": self.calculate_ema(prices),
        }


def main():
    # Add project root to path
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_saver import load_latest_data

    # Load latest price data
    price_data = load_latest_data("price_feed")

    if not price_data or "historical_data" not in price_data:
        print("No price data found!")
        return

    # Extract closing prices
    prices = [bar["close"] for bar in price_data["historical_data"]]
    print(f"Analyzing {len(prices)} price points")

    # Calculate technical indicators
    ta = TechnicalAnalysis()
    signals = ta.get_signals(prices)

    # Print results
    print("\nTechnical Analysis Results:")
    print(f"RSI: {signals['rsi']:.2f}")
    print("\nMACD:")
    print(f"  MACD Line: {signals['macd']['macd']:.2f}")
    print(f"  Signal Line: {signals['macd']['signal']:.2f}")
    print(f"  Histogram: {signals['macd']['histogram']:.2f}")
    print("\nEMA:")
    print(f"  Short EMA: {signals['ema']['short_ema']:.2f}")
    print(f"  Long EMA: {signals['ema']['long_ema']:.2f}")
    print(f"  Crossover: {signals['ema']['crossover']:.2f}")


if __name__ == "__main__":
    main()
