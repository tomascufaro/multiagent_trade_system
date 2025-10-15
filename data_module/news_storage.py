"""News Storage - MongoDB storage for news articles"""
from pymongo import MongoClient
from datetime import datetime
import os


class NewsStorage:
    def __init__(self):
        conn_str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        self.client = MongoClient(conn_str)
        self.db = self.client["trading_bot"]
        self.collection = self.db["news"]
        self.collection.create_index("id", unique=True)

    def save_articles(self, articles):
        """Save news articles (upsert to avoid duplicates)"""
        count = 0
        for article in articles:
            article["saved_at"] = datetime.now()
            result = self.collection.update_one(
                {"id": article["id"]},
                {"$set": article},
                upsert=True
            )
            if result.upserted_id or result.modified_count:
                count += 1
        return count
