"""Collect news for tracked symbols and save to MongoDB"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_module.data_manager import DataManager
from data_module.news_feed import NewsFeed
from data_module.news_storage import NewsStorage
from datetime import datetime


def main():
    print(f"Starting news collection - {datetime.now().isoformat()}")

    data_manager = DataManager()
    news_feed = NewsFeed()
    news_storage = NewsStorage()

    # Get tracked symbols from portfolio universe
    symbols = data_manager.get_all_tracking_symbols()
    print(f"Tracking {len(symbols)} symbols: {', '.join(sorted(symbols))}")

    # Fetch news for all symbols
    articles = news_feed.get_news(list(symbols), limit=10)

    if articles:
        saved_count = news_storage.save_articles(articles)
        print(f"Saved {saved_count} new articles (total fetched: {len(articles)})")
    else:
        print("No articles found")

    print("✓ News collection completed")


if __name__ == "__main__":
    main()
