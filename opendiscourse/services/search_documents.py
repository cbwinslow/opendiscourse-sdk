import argparse
import logging
import os
import sys
import traceback
from typing import Any, Dict, List, Optional

import pinecone
from dotenv import load_dotenv
from langchain.embeddings import OpenAIEmbeddings

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def validate_environment_variables() -> Dict[str, str]:
    """Validate that required environment variables are set.
    
    Returns:
        Dict containing the validated environment variables.
        
    Raises:
        ValueError: If any required environment variables are missing.
    """
    required_vars = ["PINECONE_API_KEY", "PINECONE_ENVIRONMENT", "OPENAI_API_KEY"]
    env_vars = {}
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            env_vars[var] = value
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return env_vars


def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for documents similar to the given query.

    Args:
        query (str): Search query
        top_k (int): Number of results to return

    Returns:
        list: List of search results with scores and metadata
        
    Raises:
        ValueError: If query is empty or environment variables are missing
        pinecone.exceptions.PineconeException: If Pinecone operations fail
        Exception: For other embedding service errors
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Validate environment variables
        env_vars = validate_environment_variables()

        # Initialize Pinecone with error handling
        try:
            pinecone.init(
                api_key=env_vars["PINECONE_API_KEY"],
                environment=env_vars["PINECONE_ENVIRONMENT"],
            )
            logger.info("Successfully initialized Pinecone")
        except Exception as e:
            logger.error("Failed to initialize Pinecone: %s", str(e))
            raise

        # Initialize OpenAI embeddings with error handling
        try:
            embeddings = OpenAIEmbeddings(openai_api_key=env_vars["OPENAI_API_KEY"])
            logger.info("Successfully initialized OpenAI embeddings")
        except Exception as e:
            logger.error("Failed to initialize OpenAI embeddings: %s", str(e))
            raise

        # Get the Pinecone index with error handling
        try:
            index = pinecone.Index("opendiscourse-docs")
            logger.info("Successfully connected to Pinecone index")
        except Exception as e:
            logger.error("Failed to connect to Pinecone index: %s", str(e))
            raise

        # Get query embedding with error handling
        try:
            query_embedding = embeddings.embed_query(query)
            logger.info("Successfully generated query embedding")
        except Exception as e:
            logger.error("Failed to generate embedding for query '%s': %s", query, str(e))
            raise

        # Search for similar documents with error handling
        try:
            results = index.query(
                vector=query_embedding, top_k=top_k, include_metadata=True
            )
            logger.info("Successfully performed vector search")
        except Exception as e:
            logger.error("Failed to perform vector search: %s", str(e))
            raise

        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append(
                {
                    "score": match.score,
                    "title": match.metadata.get("title", ""),
                    "content": match.metadata.get("content", ""),
                    "document_id": match.metadata.get("document_id", ""),
                }
            )

        return formatted_results
    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        raise
    except Exception as e:
        logger.error("Error searching documents: %s", str(e))
        logger.error("Traceback: %s", traceback.format_exc())
        return []


def main() -> None:
    """Command-line interface for document search."""
    parser = argparse.ArgumentParser(description="Search for similar documents")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        results = search(args.query, args.top_k)
        
        if not results:
            print("No results found.")
            return
            
        print(f"\nFound {len(results)} results for query: '{args.query}'\n")
        
        for i, result in enumerate(results, 1):
            print(f"Result {i} (Score: {result['score']:.3f})")
            print(f"Title: {result['title']}")
            print(f"Content: {result['content'][:200]}..." if len(result['content']) > 200 else result['content'])
            print("-" * 50)
            
    except Exception as e:
        logger.error("Failed to perform search: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
