from openai import OpenAI
import yaml
from typing import List, Dict, Any
import os
from dotenv import load_dotenv


class SentimentAgent:
    def __init__(self, config_path='analyst_service/config/settings.yaml'):
        # Load environment variables
        load_dotenv()

        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        print(
            f"Using OpenAI API key: {api_key}"
        )  # Debugging line to check if API key is loaded
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4.1-nano"
        self.min_confidence = 0.7  # You can adjust this or load from config if needed

    def analyze_single_article(self, article: Dict[str, str]) -> Dict[str, Any]:
        """Analyze sentiment for a single news article."""
        prompt = f"Analyze market sentiment from this article and respond with:\nsentiment_score: [number between -1 and 1]\nconfidence: [number between 0 and 1]\nsummary: [brief summary]\n\nHeadline: {article['headline']}\nSummary: {article['summary']}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst. Provide sentiment analysis in the exact format requested.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            analysis = response.choices[0].message.content
            sentiment_score = float(analysis.split("sentiment_score:")[1].split()[0])
            confidence = float(analysis.split("confidence:")[1].split()[0])
            summary = analysis.split("summary:")[1].strip()

            return {
                "article_id": article.get("id", "unknown"),
                "headline": article["headline"],
                "sentiment": "bullish" if sentiment_score > 0 else "bearish",
                "sentiment_score": sentiment_score,
                "confidence": confidence,
                "summary": summary,
            }

        except Exception as e:
            print(f"Error analyzing article '{article['headline']}': {e}")
            return {
                "article_id": article.get("id", "unknown"),
                "headline": article["headline"],
                "sentiment": "neutral",
                "sentiment_score": 0,
                "confidence": 0,
                "summary": f"Error: {str(e)}",
            }

    def analyze_news(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Analyze sentiment for multiple articles individually."""
        if not articles:
            return {
                "articles_analyzed": [],
                "overall_sentiment": "neutral",
                "overall_confidence": 0,
                "summary": "No news articles available",
            }

        analyzed_articles = []
        total_sentiment = 0
        total_confidence = 0
        successful_analyses = 0

        for article in articles:
            result = self.analyze_single_article(article)
            analyzed_articles.append(result)

            if result["confidence"] > 0:
                total_sentiment += result["sentiment_score"] * result["confidence"]
                total_confidence += result["confidence"]
                successful_analyses += 1

        if successful_analyses > 0:
            weighted_sentiment = total_sentiment / total_confidence
            avg_confidence = total_confidence / successful_analyses
            overall_sentiment = "bullish" if weighted_sentiment > 0 else "bearish"
        else:
            weighted_sentiment = 0
            avg_confidence = 0
            overall_sentiment = "neutral"

        return {
            "articles_analyzed": analyzed_articles,
            "overall_sentiment": overall_sentiment,
            "overall_sentiment_score": weighted_sentiment,
            "overall_confidence": avg_confidence,
            "summary": f"Analyzed {len(analyzed_articles)} articles, {successful_analyses} successful",
        }


def main():
    import sys
    import os

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from data_ingestion.news_feed import NewsFeed
    from utils.data_saver import load_latest_data, save_data

    # Load latest news feed data
    news_data = load_latest_data("news_feed")
    if not news_data:
        print("No news feed data found. Fetching new data...")
        news_feed = NewsFeed()
        articles = news_feed.get_news(limit=5)
    else:
        print("Using latest news feed data...")
        articles = news_data.get("general_news", [])

    # Create sentiment agent instance
    agent = SentimentAgent()

    # Analyze articles
    result = agent.analyze_news(articles)

    # Save sentiment analysis results
    filepath = save_data("sentiment_analysis", result)
    print(f"\nSentiment analysis saved to: {filepath}")

    # Print results
    print("\nSentiment Analysis Results:")
    print(f"Overall Sentiment: {result['overall_sentiment']}")
    print(f"Overall Score: {result.get('overall_sentiment_score', 'N/A'):.3f}")
    print(f"Overall Confidence: {result['overall_confidence']:.3f}")
    print(f"Summary: {result['summary']}")

    print(
        f"\nIndividual Article Analysis ({len(result['articles_analyzed'])} articles):"
    )
    for i, article_result in enumerate(result["articles_analyzed"], 1):
        print(f"\n{i}. {article_result['headline'][:80]}...")
        print(
            f"   Sentiment: {article_result['sentiment']} ({article_result['sentiment_score']:.3f})"
        )
        print(f"   Confidence: {article_result['confidence']:.3f}")


if __name__ == "__main__":
    main()
