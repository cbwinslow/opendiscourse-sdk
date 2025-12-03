"""News article saving utilities.

This module provides functionality to save news articles to various formats.
"""

import argparse
import csv
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def save_articles_to_csv(
    articles: List[Dict[str, Any]], 
    filename: str = "news_articles.csv"
) -> bool:
    """Save articles to a CSV file.
    
    Args:
        articles: List of article dictionaries to save
        filename: Name of the output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    if not articles:
        logger.warning("No articles to save.")
        return False
        
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        
        keys = articles[0].keys()  # Assumes all articles have similar structure
        with open(filename, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(articles)
            
        logger.info("Successfully saved %d articles to %s", len(articles), filename)
        return True
        
    except Exception as e:
        logger.error("Error saving articles to CSV: %s", str(e))
        return False


def save_articles_to_json(
    articles: List[Dict[str, Any]], 
    filename: str = "news_articles.json"
) -> bool:
    """Save articles to a JSON file.
    
    Args:
        articles: List of article dictionaries to save
        filename: Name of the output JSON file
        
    Returns:
        True if successful, False otherwise
    """
    if not articles:
        logger.warning("No articles to save.")
        return False
        
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
        
        import json
        with open(filename, "w", encoding="utf-8") as output_file:
            json.dump(articles, output_file, indent=2, ensure_ascii=False)
            
        logger.info("Successfully saved %d articles to %s", len(articles), filename)
        return True
        
    except Exception as e:
        logger.error("Error saving articles to JSON: %s", str(e))
        return False


def main() -> None:
    """Command-line interface for saving articles."""
    parser = argparse.ArgumentParser(description="Save news articles to file")
    parser.add_argument("input_file", help="Input JSON file containing articles")
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--format", "-f", choices=["csv", "json"], default="csv", 
                       help="Output format (default: csv)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load articles from input file
        import json
        with open(args.input_file, "r", encoding="utf-8") as f:
            articles = json.load(f)
            
        if not isinstance(articles, list):
            logger.error("Input file must contain a list of articles")
            sys.exit(1)
            
        # Determine output filename
        if args.output:
            output_file = args.output
        else:
            base_name = os.path.splitext(os.path.basename(args.input_file))[0]
            output_file = f"{base_name}.{args.format}"
            
        # Save articles
        if args.format == "csv":
            success = save_articles_to_csv(articles, output_file)
        else:
            success = save_articles_to_json(articles, output_file)
            
        if not success:
            sys.exit(1)
            
    except FileNotFoundError:
        logger.error("Input file not found: %s", args.input_file)
        sys.exit(1)
    except Exception as e:
        logger.error("Error processing articles: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
