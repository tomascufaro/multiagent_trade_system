import os
from typing import Dict, Any

import pandas as pd
import yaml


class TechnicalAnalysis:
    def __init__(self, config_path: str = "analyst_service/config/settings.yaml"):
        with open(config_path, "r") as config_file:
            settings = yaml.safe_load(config_file)

        ta_settings = settings["technical"]
        self.rsi_period = ta_settings["rsi"]["period"]
        self.macd_fast = ta_settings["macd"]["fast_period"]
        self.macd_slow = ta_settings["macd"]["slow_period"]
        self.macd_signal = ta_settings["macd"]["signal_period"]
        self.ema_short = ta_settings["ema"]["short_period"]
        self.ema_long = ta_settings["ema"]["long_period"]

    def calculate_rsi(self, prices: list, period: int | None = None) -> float:
        """Calculate Relative Strength Index."""
        if not prices:
            return 0.0

        period = period or self.rsi_period
        price_series = pd.Series(prices)
        delta = price_series.diff()

        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        if rsi.empty or pd.isna(rsi.iloc[-1]):
            return 0.0

        return float(rsi.iloc[-1])

    def calculate_macd(self, prices: list) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if not prices:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

        price_series = pd.Series(prices)

        exp1 = price_series.ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = price_series.ewm(span=self.macd_slow, adjust=False).mean()

        macd_series = exp1 - exp2
        signal_series = macd_series.ewm(span=self.macd_signal, adjust=False).mean()

        if macd_series.empty or signal_series.empty:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

        macd_value = float(macd_series.iloc[-1])
        signal_value = float(signal_series.iloc[-1])

        return {
            "macd": macd_value,
            "signal": signal_value,
            "histogram": macd_value - signal_value,
        }

    def calculate_ema(self, prices: list) -> Dict[str, float]:
        """Calculate Exponential Moving Averages."""
        if not prices:
            return {"short_ema": 0.0, "long_ema": 0.0, "crossover": 0.0}

        price_series = pd.Series(prices)

        short_ema_series = price_series.ewm(span=self.ema_short, adjust=False).mean()
        long_ema_series = price_series.ewm(span=self.ema_long, adjust=False).mean()

        if short_ema_series.empty or long_ema_series.empty:
            return {"short_ema": 0.0, "long_ema": 0.0, "crossover": 0.0}

        short_ema = float(short_ema_series.iloc[-1])
        long_ema = float(long_ema_series.iloc[-1])

        return {
            "short_ema": short_ema,
            "long_ema": long_ema,
            "crossover": short_ema - long_ema,
        }

    def get_signals(self, prices: list) -> Dict[str, Any]:
        """Get all technical signals."""
        return {
            "rsi": self.calculate_rsi(prices),
            "macd": self.calculate_macd(prices),
            "ema": self.calculate_ema(prices),
        }
