import pandas as pd
import numpy as np
from typing import Dict, Any

class TechnicalAnalysis:
    def __init__(self, config_path: str = '../config/settings.yaml'):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Dict:
        import yaml
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)['technical']

    def calculate_rsi(self, prices: list, period: int = None) -> float:
        """Calculate Relative Strength Index."""
        if period is None:
            period = self.config['rsi']['period']
            
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
        
        exp1 = prices.ewm(span=self.config['macd']['fast_period'], adjust=False).mean()
        exp2 = prices.ewm(span=self.config['macd']['slow_period'], adjust=False).mean()
        
        macd = exp1 - exp2
        signal = macd.ewm(span=self.config['macd']['signal_period'], adjust=False).mean()
        
        return {
            'macd': macd.iloc[-1],
            'signal': signal.iloc[-1],
            'histogram': macd.iloc[-1] - signal.iloc[-1]
        }

    def calculate_ema(self, prices: list) -> Dict[str, float]:
        """Calculate Exponential Moving Averages."""
        prices = pd.Series(prices)
        
        short_ema = prices.ewm(span=self.config['ema']['short_period'], adjust=False).mean()
        long_ema = prices.ewm(span=self.config['ema']['long_period'], adjust=False).mean()
        
        return {
            'short_ema': short_ema.iloc[-1],
            'long_ema': long_ema.iloc[-1],
            'crossover': short_ema.iloc[-1] - long_ema.iloc[-1]
        }

    def get_signals(self, prices: list) -> Dict[str, Any]:
        """Get all technical signals."""
        return {
            'rsi': self.calculate_rsi(prices),
            'macd': self.calculate_macd(prices),
            'ema': self.calculate_ema(prices)
        }
