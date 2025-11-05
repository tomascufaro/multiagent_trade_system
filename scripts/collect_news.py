"""Collect news for tracked symbols and save to SQLite"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_module.data_manager import DataManager
from data_module.api_clients import NewsFeed
from datetime import datetime


def main():
    print(f"Starting news collection - {datetime.now().isoformat()}")

    data_manager = DataManager()
    news_feed = NewsFeed()

    # Get tracked symbols from portfolio universe
    symbols = data_manager.get_all_tracking_symbols()
    print(f"Tracking {len(symbols)} symbols: {', '.join(sorted(symbols))}")

    # Fetch news for all symbols
    articles = news_feed.get_news(list(symbols), limit=10)

    if articles:
        saved_count = data_manager.save_news(articles)
        print(f"Saved {saved_count} articles (total fetched: {len(articles)})")
    else:
        print("No articles found")

    print("✓ News collection completed")


if __name__ == "__main__":
    main()
