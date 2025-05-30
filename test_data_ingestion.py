#!/usr/bin/env python3
"""Test script for data ingestion modules."""

import os
import sys
sys.path.append('.')

from data_ingestion.news_feed import NewsFeed
from data_ingestion.price_feed import PriceFeed
from data_ingestion.account_status import AccountStatus

def test_news_feed():
    """Test the news feed functionality."""
    print("Testing NewsFeed...")
    try:
        news_feed = NewsFeed()
        print("✓ NewsFeed initialized successfully")
        
        # Test getting general news (last 30 articles)
        print("Fetching general news...")
        news = news_feed.get_news(limit=30, hours_back=24)
        print(f"✓ Retrieved {len(news)} general news articles")
        
        if news:
            print("Sample article:")
            print(f"  Headline: {news[0]['headline'][:80]}...")
            print(f"  Source: {news[0]['source']}")
            print(f"  Symbols: {news[0]['symbols']}")
        
        # Test getting crypto-specific news
        print("\nFetching crypto-specific news...")
        crypto_news = news_feed.get_news(symbols=['BTC/USD', 'ETH/USD'], limit=10)
        print(f"✓ Retrieved {len(crypto_news)} crypto news articles")
        
    except Exception as e:
        print(f"✗ NewsFeed error: {e}")

def test_price_feed():
    """Test the price feed functionality."""
    print("\nTesting PriceFeed...")
    try:
        price_feed = PriceFeed()
        print("✓ PriceFeed initialized successfully")
        
        # Test getting current price for BTC
        print("Fetching current BTC/USD price...")
        price = price_feed.get_current_price('BTC/USD')
        if price:
            print(f"✓ Current BTC/USD price: ${price}")
        else:
            print("✗ Failed to get current price")
        
        # Test historical data
        print("Fetching historical data...")
        historical = price_feed.get_historical_data('BTC/USD', timeframe='1D', limit=5)
        if historical:
            print(f"✓ Retrieved {len(historical)} historical data points")
            if len(historical) > 0:
                latest = historical[0]
                print(f"  Latest close: ${latest['close']}")
                print(f"  Timestamp: {latest['timestamp']}")
        else:
            print("✗ Failed to get historical data")
            
    except Exception as e:
        print(f"✗ PriceFeed error: {e}")

def test_account_status():
    """Test the account status ingestion functionality."""
    print("\nTesting AccountStatus...")
    try:
        account_status = AccountStatus()
        print("✓ AccountStatus initialized successfully")
        print("Fetching account status...")
        status = account_status.get_status()
        if status:
            print("✓ Retrieved account status:")
            for k, v in status.items():
                print(f"  {k}: {v}")
        else:
            print("✗ Failed to get account status or no data returned")
    except Exception as e:
        print(f"✗ AccountStatus error: {e}")

if __name__ == "__main__":
    print("Testing Data Ingestion Module\n" + "="*40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found. Please create one based on .env.example")
        print("Make sure to set your APCA_API_KEY_ID and APCA_API_SECRET_KEY")
        print()
    
    test_news_feed()
    test_price_feed()
    test_account_status()