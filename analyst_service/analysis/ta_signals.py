import os
from typing import Dict, Any

import pandas as pd
import yaml


class TechnicalAnalysis:
    def __init__(self, config_path: str = "analyst_service/config/settings.yaml"):
        """
        Initialize technical analysis settings.

        If a YAML config exists at config_path and contains a `technical` section,
        those values are used. Otherwise, sensible defaults are applied so that
        no external config file is required.
        """
        # Default parameters (no config dependency)
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ema_short = 20
        self.ema_long = 50

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as config_file:
                    settings = yaml.safe_load(config_file) or {}

                ta_settings = settings.get("technical", {})
                self.rsi_period = ta_settings.get("rsi", {}).get("period", self.rsi_period)
                self.macd_fast = ta_settings.get("macd", {}).get("fast_period", self.macd_fast)
                self.macd_slow = ta_settings.get("macd", {}).get("slow_period", self.macd_slow)
                self.macd_signal = ta_settings.get("macd", {}).get("signal_period", self.macd_signal)
                self.ema_short = ta_settings.get("ema", {}).get("short_period", self.ema_short)
                self.ema_long = ta_settings.get("ema", {}).get("long_period", self.ema_long)
            except Exception:
                # On any config error, fall back to defaults without failing.
                pass

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
