import argparse
import logging
import os
import sys
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from scrape_documents import scrape_documents

from opendiscourse.services.entity_extractor import process_document

# Set up logging with better configuration
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("populate_database.log"), logging.StreamHandler()],
)

# Load environment variables
load_dotenv()


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Context manager for database connections with automatic cleanup.
    
    Yields:
        A PostgreSQL database connection
        
    Raises:
        psycopg2.OperationalError: If connection fails
    """
    connection = None
    try:
        # Validate required environment variables
        required_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        connection = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
        )
        logger.debug("Database connection established successfully")
        yield connection
        
    except psycopg2.Error as e:
        logger.error("Database connection error: %s", str(e))
        if connection:
            connection.rollback()
        raise
    except Exception as e:
        logger.error("Unexpected error establishing database connection: %s", str(e))
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            try:
                connection.close()
                logger.debug("Database connection closed successfully")
            except Exception as e:
                logger.warning("Error closing database connection: %s", str(e))


def create_tables() -> None:
    """Create necessary database tables with proper error handling and transactions."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create documents table with IF NOT EXISTS
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS documents (
                        id SERIAL PRIMARY KEY,
                        content TEXT,
                        title TEXT,
                        source_url TEXT,
                        source_id TEXT,
                        source_type TEXT,
                        source_date TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(source_id, source_type)
                    )
                """
                )

                # Create entities table with IF NOT EXISTS
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS entities (
                        id SERIAL PRIMARY KEY,
                        text TEXT NOT NULL,
                        entity_type TEXT NOT NULL,
                        confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(text, entity_type)
                    )
                """
                )

                # Create entity_mentions table with IF NOT EXISTS
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS entity_mentions (
                        id SERIAL PRIMARY KEY,
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                        entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        start_index INTEGER CHECK (start_index >= 0),
                        end_index INTEGER CHECK (end_index >= start_index),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create entity_relationships table with IF NOT EXISTS
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS entity_relationships (
                        id SERIAL PRIMARY KEY,
                        entity1_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        entity2_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
                        relationship_type TEXT NOT NULL,
                        confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CHECK (entity1_id != entity2_id)
                    )
                """
                )

                # Create indexes for better performance
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_documents_source_type_id 
                    ON documents(source_type, source_id)
                """
                )
                
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_entity_mentions_document_id 
                    ON entity_mentions(document_id)
                """
                )

                conn.commit()
                logger.info("Database tables created successfully")

    except psycopg2.Error as e:
        logger.error("Database error creating tables: %s", str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error creating tables: %s", str(e))
        raise


def populate_database(scrape_only: bool = False, process_only: bool = False) -> None:
    """Scrape documents and process them for entities.
    
    Args:
        scrape_only: If True, only scrape documents without processing
        process_only: If True, only process existing documents without scraping
    """
    try:
        # Scrape documents unless process_only is specified
        if not process_only:
            logger.info("Starting document scraping...")
            scrape_documents()
            logger.info("Document scraping completed")
        
        # Process documents unless scrape_only is specified
        if not scrape_only:
            logger.info("Starting document processing for entities...")
            
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get all documents with parameterized query
                    cursor.execute(
                        """
                        SELECT id, content, title, source_url, source_id, source_type, source_date 
                        FROM documents 
                        WHERE content IS NOT NULL AND content != ''
                        ORDER BY id
                        """
                    )
                    documents = cursor.fetchall()
                    total_docs = len(documents)
                    logger.info("Found %d documents to process", total_docs)

                    for idx, doc in enumerate(documents, 1):
                        doc_id = doc["id"]
                        title = doc["title"] or "Untitled"
                        
                        logger.info(
                            "Processing document %d/%d (ID: %s): %s", 
                            idx, total_docs, doc_id, title[:50] + "..." if len(title) > 50 else title
                        )
                        
                        try:
                            # Process document for entities
                            process_document(
                                document_id=doc_id,
                                content=doc["content"],
                                metadata={
                                    "title": title,
                                    "source_url": doc["source_url"],
                                    "source_id": doc["source_id"],
                                    "source_type": doc["source_type"],
                                    "source_date": doc["source_date"],
                                },
                            )
                            logger.debug("Successfully processed document ID: %s", doc_id)
                            
                        except Exception as e:
                            logger.error(
                                "Error processing document %s (ID: %s): %s", 
                                title[:50] + "..." if len(title) > 50 else title,
                                doc_id, 
                                str(e),
                                exc_info=True
                            )
                            continue

            logger.info("Database population completed successfully")

    except Exception as e:
        logger.error("Error during database population: %s", str(e), exc_info=True)
        raise


def main() -> None:
    """Main function with command-line argument support."""
    parser = argparse.ArgumentParser(description="Populate database with documents and entities")
    parser.add_argument(
        "--scrape-only", 
        action="store_true", 
        help="Only scrape documents, don't process for entities"
    )
    parser.add_argument(
        "--process-only", 
        action="store_true", 
        help="Only process existing documents for entities, don't scrape new ones"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.scrape_only and args.process_only:
        logger.error("Cannot specify both --scrape-only and --process-only")
        sys.exit(1)
    
    try:
        # Create tables first
        logger.info("Creating database tables...")
        create_tables()
        
        # Populate database based on arguments
        populate_database(scrape_only=args.scrape_only, process_only=args.process_only)
        
        logger.info("Database population script completed successfully")
        
    except Exception as e:
        logger.error("Database population script failed: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
