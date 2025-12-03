"""News API integration for OpenDiscourse.

This module provides functionality to interact with the NewsAPI.org service
to fetch news articles related to government and political topics.
"""

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Configuration
NEWSAPI_BASE_URL = "https://newsapi.org/v2/"
DEFAULT_PAGE_SIZE = 20
REQUEST_TIMEOUT = 30


# --- Utility Functions ---


def get_api_key() -> str:
    """Get NewsAPI key from environment variables.
    
    Returns:
        The API key from environment variables
        
    Raises:
        ValueError: If API key is not found
    """
    api_key = os.getenv("NEWSAPI_KEY")
    if not api_key:
        raise ValueError(
            "NewsAPI key not found. Please set NEWSAPI_KEY environment variable."
        )
    return api_key


def make_api_request(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Makes a request to the NewsAPI.
    
    Args:
        endpoint: The API endpoint (e.g., 'top-headlines', 'everything').
        params: Dictionary of query parameters.
        
    Returns:
        JSON response from the API, or None if an error occurs.
        
    Raises:
        requests.exceptions.RequestException: If API request fails
    """
    if params is None:
        params = {}
        
    try:
        api_key = get_api_key()
        params["apiKey"] = api_key
        url = NEWSAPI_BASE_URL + endpoint

        logger.debug("Making API request to: %s", url)
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        
        result = response.json()
        logger.info("API request successful. Status: %s", result.get("status", "unknown"))
        return result
        
    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred: %s", http_err)
        if hasattr(http_err, 'response') and http_err.response is not None:
            logger.error("Response content: %s", http_err.response.content.decode())
        raise
    except requests.exceptions.RequestException as req_err:
        logger.error("Request error occurred: %s", req_err)
        raise
    except json.JSONDecodeError as json_err:
        logger.error("Failed to decode JSON response: %s", json_err)
        raise
    except ValueError as val_err:
        logger.error("Configuration error: %s", val_err)
        raise


def get_top_headlines(
    country: str = "us", 
    category: Optional[str] = None, 
    sources: Optional[str] = None, 
    query: Optional[str] = None, 
    page_size: int = DEFAULT_PAGE_SIZE
) -> Optional[Dict[str, Any]]:
    """
    Fetches top headlines from NewsAPI.
    
    Args:
        country: 2-letter ISO 3166-1 code of the country.
        category: Category (e.g., 'business', 'technology').
                 Cannot be mixed with 'sources' param.
        sources: Comma-separated string of identifiers for news sources.
                Cannot be mixed with 'country' or 'category'.
        query: Keywords or a phrase to search for.
        page_size: Number of results to return per page (max 100).
        
    Returns:
        JSON response containing headlines, or None if error occurs.
        
    Raises:
        ValueError: If invalid parameter combinations are provided
        requests.exceptions.RequestException: If API request fails
    """
    # Validate parameter combinations
    if sources and (country or category):
        raise ValueError("Cannot mix 'sources' parameter with 'country' or 'category'")
    
    if page_size > 100:
        raise ValueError("page_size cannot exceed 100")
    
    params = {"pageSize": page_size}
    
    if country:
        params["country"] = country
    if category:
        params["category"] = category
    if sources:
        params["sources"] = sources
    if query:
        params["q"] = query
    
    return make_api_request("top-headlines", params)


def search_everything(
    query: str,
    sources: Optional[str] = None,
    domains: Optional[str] = None,
    exclude_domains: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    language: str = "en",
    sort_by: str = "publishedAt",
    page_size: int = DEFAULT_PAGE_SIZE,
    page: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Search through millions of articles from over 80,000 large and small news sources and blogs.
    
    Args:
        query: Keywords or phrases to search for in the article title and body.
        sources: Comma-separated string of identifiers for news sources.
        domains: Comma-separated string of domains to restrict search to.
        exclude_domains: Comma-separated string of domains to exclude.
        from_date: Date to search from (ISO 8601 format, e.g., 2023-01-01).
        to_date: Date to search to (ISO 8601 format, e.g., 2023-12-31).
        language: Language to search for (e.g., 'en', 'es', 'fr').
        sort_by: Sort order ('relevancy', 'popularity', 'publishedAt').
        page_size: Number of results to return per page (max 100).
        page: Page number to retrieve.
        
    Returns:
        JSON response containing articles, or None if error occurs.
        
    Raises:
        ValueError: If invalid parameters are provided
        requests.exceptions.RequestException: If API request fails
    """
    if not query:
        raise ValueError("Query parameter is required for everything endpoint")
    
    if page_size > 100:
        raise ValueError("page_size cannot exceed 100")
    
    if sort_by not in ["relevancy", "popularity", "publishedAt"]:
        raise ValueError("sort_by must be one of: relevancy, popularity, publishedAt")
    
    params = {
        "q": query,
        "language": language,
        "sortBy": sort_by,
        "pageSize": page_size,
        "page": page
    }
    
    if sources:
        params["sources"] = sources
    if domains:
        params["domains"] = domains
    if exclude_domains:
        params["excludeDomains"] = exclude_domains
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date
    
    return make_api_request("everything", params)


def main() -> None:
    """Command-line interface for NewsAPI."""
    parser = argparse.ArgumentParser(description="Fetch news articles using NewsAPI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Top headlines command
    headlines_parser = subparsers.add_parser("headlines", help="Get top headlines")
    headlines_parser.add_argument("--country", default="us", help="Country code (default: us)")
    headlines_parser.add_argument("--category", help="News category")
    headlines_parser.add_argument("--sources", help="Comma-separated news sources")
    headlines_parser.add_argument("--query", help="Search query")
    headlines_parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE, 
                                help=f"Number of results (default: {DEFAULT_PAGE_SIZE})")
    
    # Search everything command
    search_parser = subparsers.add_parser("search", help="Search all articles")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--sources", help="Comma-separated news sources")
    search_parser.add_argument("--domains", help="Comma-separated domains")
    search_parser.add_argument("--exclude-domains", help="Comma-separated domains to exclude")
    search_parser.add_argument("--from-date", help="Start date (YYYY-MM-DD)")
    search_parser.add_argument("--to-date", help="End date (YYYY-MM-DD)")
    search_parser.add_argument("--language", default="en", help="Language code (default: en)")
    search_parser.add_argument("--sort-by", default="publishedAt", 
                              choices=["relevancy", "popularity", "publishedAt"],
                              help="Sort order (default: publishedAt)")
    search_parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE,
                              help=f"Number of results (default: {DEFAULT_PAGE_SIZE})")
    search_parser.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    
    # Global options
    parser.add_argument("--output", "-o", help="Output file (JSON format)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Execute command
        if args.command == "headlines":
            result = get_top_headlines(
                country=args.country,
                category=args.category,
                sources=args.sources,
                query=args.query,
                page_size=args.page_size
            )
        elif args.command == "search":
            result = search_everything(
                query=args.query,
                sources=args.sources,
                domains=args.domains,
                exclude_domains=args.exclude_domains,
                from_date=args.from_date,
                to_date=args.to_date,
                language=args.language,
                sort_by=args.sort_by,
                page_size=args.page_size,
                page=args.page
            )
        else:
            parser.print_help()
            return
        
        if not result:
            logger.error("No results returned from API")
            sys.exit(1)
        
        # Output results
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info("Results saved to %s", args.output)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
    except Exception as e:
        logger.error("Error executing command: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()