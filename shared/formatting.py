import logging
from datetime import datetime
import os

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    # File handler
    fh = logging.FileHandler(
        f"logs/trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
    )
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def format_price(price: float, decimals: int = 2) -> str:
    """Format price with specified decimal places."""
    return f"{price:.{decimals}f}"

def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value * 100:.2f}%"

def calculate_returns(entry_price: float, 
                     current_price: float, 
                     is_long: bool = True) -> float:
    """Calculate returns for a position."""
    if is_long:
        return (current_price - entry_price) / entry_price
    return (entry_price - current_price) / entry_price
