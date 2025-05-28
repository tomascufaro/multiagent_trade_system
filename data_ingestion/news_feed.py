import requests
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv


class NewsFeed:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = "https://data.alpaca.markets/v1beta1/news"

    def get_news(
        self, symbols: List[str] = None, limit: int = 30, hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """Fetch news articles from Alpaca news API."""
        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
            }

            start_time = (datetime.now() - timedelta(hours=hours_back)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

            params = {
                "start": start_time,
                "end": end_time,
                "sort": "desc",
                "limit": limit,
                "include_content": True,
                "exclude_contentless": True,
            }

            if symbols:
                params["symbols"] = ",".join(symbols)

            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()

            news_data = response.json()
            return [
                {
                    "id": article["id"],
                    "headline": article["headline"],
                    "author": article["author"],
                    "summary": article["summary"],
                    "content": article.get("content", ""),
                    "url": article.get("url"),
                    "created_at": article["created_at"],
                    "updated_at": article["updated_at"],
                    "symbols": article["symbols"],
                    "source": article["source"],
                }
                for article in news_data.get("news", [])
            ]
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
                print(f"Response content: {e.response.text}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching news: {e}")
            return []


def main():
    """Test function to run the news feed."""
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_saver import save_data
    
    print("Testing NewsFeed...")

    news_feed = NewsFeed()

    # Test general news (no specific symbols)
    print("\n1. Testing general news:")
    general_news = news_feed.get_news(limit=5)
    if general_news:
        print(f"Found {len(general_news)} articles")
        for i, article in enumerate(general_news[:2], 1):
            print(f"\nArticle {i}:")
            print(f"  Headline: {article['headline']}")
            print(f"  Source: {article['source']}")
            print(f"  Symbols: {article['symbols']}")
            print(f"  Created: {article['created_at']}")
    else:
        print("No general news found")

    # Test symbol-specific news
    print("\n2. Testing symbol-specific news (AAPL):")
    symbol_news = news_feed.get_news(["AAPL"], limit=3)
    if symbol_news:
        print(f"Found {len(symbol_news)} AAPL articles")
        for article in symbol_news:
            print(f"  - {article['headline'][:100]}...")
    else:
        print("No AAPL news found")
    
    # Save data
    data = {
        'general_news': general_news,
        'symbol_news': symbol_news
    }
    filepath = save_data('news_feed', data)
    print(f"\nData saved to: {filepath}")


if __name__ == "__main__":
    main()
