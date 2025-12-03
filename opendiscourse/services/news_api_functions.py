import logging
import os
from datetime import date, datetime
from typing import Any, Optional, Union

from newsapi import NewsApiClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API key from environment variable
NEWSAPI_KEY = os.getenv("NEWS_API_KEY")
if not NEWSAPI_KEY:
    msg = "NEWS_API_KEY environment variable is not set"
    raise ValueError(msg)

# Initialize NewsAPI client
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)


def get_top_headlines_client(
    country: str = "us",
    category: Optional[str] = None,
    sources: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Fetches top headlines using the NewsAPI client.

    Args:
        country: Country code (e.g., 'us' for United States)
        category: News category (e.g., 'business', 'technology')
        sources: Specific news sources (comma-separated)
        query: Search query
        page_size: Number of articles to return

    Returns:
        List of article dictionaries
    """
    try:
        if sources:
            top_headlines_data = newsapi.get_top_headlines(
                q=query, sources=sources, page_size=page_size
            )
        elif category:
            top_headlines_data = newsapi.get_top_headlines(
                q=query, category=category, country=country, page_size=page_size
            )
        else:
            top_headlines_data = newsapi.get_top_headlines(
                q=query, country=country, page_size=page_size
            )

        # Log the number of articles found
        fetched_articles = top_headlines_data.get("articles", [])
        logger.info("Found %d articles", len(fetched_articles))
        return fetched_articles

    except Exception as e:
        logger.error("Error fetching top headlines: %s", str(e))
        return []


def search_articles_client(
    query: str,
    sources: Optional[str] = None,
    domains: Optional[str] = None,
    from_param: Optional[Union[str, date, datetime]] = None,
    to_param: Optional[Union[str, date, datetime]] = None,
    language: str = "en",
    sort_by: str = "publishedAt",
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Searches for articles using the NewsAPI client.

    Args:
        query: Search query (required)
        sources: Specific news sources (comma-separated)
        domains: Specific domains to search
        from_param: Start date for search
        to_param: End date for search
        language: Language of articles
        sort_by: Sort order ('publishedAt', 'relevancy', 'popularity')
        page_size: Number of articles to return

    Returns:
        List of article dictionaries
    """
    if not query:
        logger.error("Search query cannot be empty")
        return []

    try:
        # Convert dates to strings if they are date or datetime objects
        from_date = (
            from_param.isoformat()
            if isinstance(from_param, (date, datetime))
            else from_param
        )
        to_date = (
            to_param.isoformat() if isinstance(to_param, (date, datetime)) else to_param
        )

        # Make the API request
        all_articles_data = newsapi.get_everything(
            q=query,
            sources=sources,
            domains=domains,
            from_param=from_date,
            to=to_date,
            language=language,
            sort_by=sort_by,
            page_size=page_size,
        )

        # Log the number of articles found
        found_articles = all_articles_data.get("articles", [])
        logger.info("Found %d articles for query: %s", len(found_articles), query)
        return found_articles

    except Exception as e:
        logger.error("Error searching articles: %s", str(e))
        return []


def display_articles(articles: list[dict[str, Any]], max_articles: int = 5) -> None:
    """Display article details in a readable format.

    Args:
        articles: List of article dictionaries to display
        max_articles: Maximum number of articles to show
    """
    """Prints article details in a readable format.

    Args:
        articles: List of article dictionaries
        max_articles: Maximum number of articles to display
    """
    if not articles:
        print("No articles found.")
        return

    separator = "=" * 80
    print(f"\n{separator}")
    print(f"Found {len(articles)} articles. Displaying up to {max_articles}:")
    print(separator)

    for i, article in enumerate(articles[:max_articles], 1):
        title = article.get("title", "No title")
        source = article.get("source", {}).get("name", "Unknown")
        author = article.get("author", "Unknown")
        published = article.get("publishedAt", "Unknown")
        url = article.get("url", "No URL")

        print(f"\n{i}. {title}")
        print(f"   Source: {source}")
        print(f"   Author: {author}")
        print(f"   Published at: {published}")
        print(f"   URL: {url}")
        print("-" * 80)

        logger.info("\nArticle %d:", i)
        logger.info("Title: %s", title)
        logger.info("Source: %s", source)
        logger.info("Published: %s", published)


if __name__ == "__main__":
    # Example usage
    query = "AI technology"
    articles = search_articles_client(query, sort_by="publishedAt")
    display_articles(articles, max_articles=3)
