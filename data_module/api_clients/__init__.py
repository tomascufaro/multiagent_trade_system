"""
API Clients - External service integrations

This module contains clients for external APIs (Alpaca, etc.)
that fetch data from remote services.
"""

from .price_feed import PriceFeed
from .news_feed import NewsFeed

__all__ = ['PriceFeed', 'NewsFeed']
