"""News Repository - Data access for news articles and symbol relationships"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any


class NewsRepository:
    def __init__(self, db_path: str = "data/portfolio.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize news-related tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id TEXT PRIMARY KEY,
                headline TEXT NOT NULL,
                author TEXT,
                summary TEXT,
                content TEXT,
                url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                source TEXT,
                saved_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_symbols (
                news_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                PRIMARY KEY (news_id, symbol),
                FOREIGN KEY (news_id) REFERENCES news_articles(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_created_at ON news_articles(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_symbols_symbol ON news_symbols(symbol)')

        conn.commit()
        conn.close()

    def save_articles(self, articles: List[Dict[str, Any]]) -> int:
        """Save news articles with symbol relationships"""
        if not articles:
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        saved_count = 0

        for article in articles:
            cursor.execute('''
                INSERT OR REPLACE INTO news_articles
                (id, headline, author, summary, content, url, created_at, updated_at, source, saved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['id'],
                article['headline'],
                article.get('author'),
                article.get('summary'),
                article.get('content'),
                article.get('url'),
                article['created_at'],
                article.get('updated_at'),
                article.get('source'),
                datetime.now().isoformat()
            ))

            for symbol in article.get('symbols', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO news_symbols (news_id, symbol)
                    VALUES (?, ?)
                ''', (article['id'], symbol))

            saved_count += 1

        conn.commit()
        conn.close()
        return saved_count

    def get_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news articles for a specific symbol"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT n.*
            FROM news_articles n
            JOIN news_symbols ns ON n.id = ns.news_id
            WHERE ns.symbol = ?
            ORDER BY n.created_at DESC
            LIMIT ?
        ''', (symbol, limit))

        columns = [desc[0] for desc in cursor.description]
        articles = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()

        return articles

