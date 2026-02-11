"""
PostgreSQL with pgvector vector database client for Open Discourse.

This module provides a client for storing and querying vector embeddings
using PostgreSQL with the pgvector extension, integrated with the congress schema.
"""

import json
import logging
from typing import Any, Dict, List

import psycopg2
from psycopg2.extras import RealDictCursor


class PGVectorClient:
    """Client for PostgreSQL with pgvector extension in the congress schema."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the pgvector client.

        Args:
            config: Configuration dictionary containing connection details
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Connection parameters - following the pattern from existing ingestion scripts
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'opendiscourse')
        self.user = config.get('user', 'cbwinslow')  # Default to existing user
        self.password = config.get('password', '')

        # Table configuration - using the congress schema
        self.schema_name = 'congress'
        self.table_name = 'document_vectors'
        self.collection_name = config['settings'].get('collection_name', 'document_vectors')

        # Connection pool (simplified for now)
        self.connection = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.logger.info("Successfully connected to PostgreSQL")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def health_check(self) -> bool:
        """Check if the database is healthy and responsive.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception as e:
            self.logger.error(f"PostgreSQL health check failed: {e}")
            return False

    def create_collection(self, collection_name: str = None, dimension: int = 768) -> bool:
        """Create a vector collection/table in the congress schema.

        Args:
            collection_name: Name of the collection (defaults to document_vectors)
            dimension: Vector dimension (defaults to 768)

        Returns:
            bool: True if successful, False otherwise
        """
        # Note: Table is created by initialization script, this is for compatibility
        try:
            with self.connection.cursor() as cursor:
                # Check if table exists
                check_sql = """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'congress'
                    AND table_name = %s
                );
                """
                cursor.execute(check_sql, (self.table_name,))
                exists = cursor.fetchone()[0]

                if not exists:
                    self.logger.warning(f"Table congress.{self.table_name} does not exist. Run initialization script.")
                    return False

                self.logger.info(f"Collection check passed: congress.{self.table_name}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to check collection {collection_name}: {e}")
            return False

    def insert_vectors(self,
                      vectors: List[List[float]],
                      metadatas: List[Dict[str, Any]],
                      collection_name: str = None) -> bool:
        """Insert vectors into the congress.document_vectors table.

        Args:
            vectors: List of vector embeddings
            metadatas: List of metadata dictionaries
            collection_name: Name of the collection (defaults to document_vectors)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = collection_name or self.table_name
            full_table_name = f"{self.schema_name}.{collection}"

            with self.connection.cursor() as cursor:
                insert_sql = f"""
                INSERT INTO {full_table_name} (document_hash, chunk_index, content, embedding, metadata, embedding_model)
                VALUES (%s, %s, %s, %s::vector, %s::jsonb, %s)
                """

                for i, (vector, metadata) in enumerate(zip(vectors, metadatas)):
                    # Convert numpy array to list if needed
                    vector_list = vector.tolist() if hasattr(vector, 'tolist') else vector

                    cursor.execute(insert_sql, (
                        metadata.get('document_hash'),
                        metadata.get('chunk_index', i),
                        metadata.get('content', ''),
                        json.dumps(vector_list),
                        json.dumps(metadata),
                        metadata.get('embedding_model', 'text-embedding-ada-002')
                    ))

                self.connection.commit()
                self.logger.info(f"Successfully inserted {len(vectors)} vectors into {full_table_name}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to insert vectors: {e}")
            return False

    def search_similar(self,
                      query_vector: List[float],
                      top_k: int = 10,
                      threshold: float = 0.8,
                      content_type_filter: str = None,
                      collection_name: str = None) -> List[Dict[str, Any]]:
        """Search for similar vectors using the congress schema function.

        Args:
            query_vector: Query vector embedding
            top_k: Number of results to return
            threshold: Similarity threshold (0-1)
            content_type_filter: Optional content type filter
            collection_name: Name of the collection (defaults to document_vectors)

        Returns:
            List of dictionaries containing similar vectors and metadata
        """
        try:
            # Use the stored function from the initialization script
            function_name = f"{self.schema_name}.search_similar_documents"

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Convert query vector to JSON format for pgvector
                query_vector_json = json.dumps(query_vector)

                cursor.execute(
                    f"SELECT * FROM {function_name}(%s::vector, %s, %s, %s)",
                    (query_vector_json, threshold, top_k, content_type_filter)
                )

                results = cursor.fetchall()

                # Convert results to list of dictionaries
                similar_vectors = []
                for row in results:
                    similar_vectors.append({
                        'id': str(row['id']),
                        'document_hash': str(row['document_hash']),
                        'chunk_index': row['chunk_index'],
                        'content': row['content'],
                        'metadata': row['metadata'],
                        'similarity': float(row['similarity'])
                    })

                self.logger.info(f"Found {len(similar_vectors)} similar vectors")
                return similar_vectors

        except Exception as e:
            self.logger.error(f"Failed to search similar vectors: {e}")
            # Fallback to manual search if function doesn't exist
            return self._manual_search_similar(query_vector, top_k, threshold, content_type_filter)

    def _manual_search_similar(self,
                              query_vector: List[float],
                              top_k: int = 10,
                              threshold: float = 0.8,
                              content_type_filter: str = None) -> List[Dict[str, Any]]:
        """Manual fallback search if the stored function is not available."""
        try:
            collection = self.table_name
            full_table_name = f"{self.schema_name}.{collection}"

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                search_sql = f"""
                SELECT
                    id,
                    document_hash,
                    chunk_index,
                    content,
                    metadata,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM {full_table_name}
                WHERE 1 - (embedding <=> %s::vector) > %s
                {("AND metadata->>'content_type' = %s" if content_type_filter else "")}
                ORDER BY similarity DESC
                LIMIT %s;
                """

                params = [json.dumps(query_vector), json.dumps(query_vector), threshold]
                if content_type_filter:
                    params.append(content_type_filter)
                params.append(top_k)

                cursor.execute(search_sql, params)
                results = cursor.fetchall()

                similar_vectors = []
                for row in results:
                    similar_vectors.append({
                        'id': str(row['id']),
                        'document_hash': str(row['document_hash']),
                        'chunk_index': row['chunk_index'],
                        'content': row['content'],
                        'metadata': row['metadata'],
                        'similarity': float(row['similarity'])
                    })

                self.logger.info(f"Found {len(similar_vectors)} similar vectors (manual search)")
                return similar_vectors

        except Exception as e:
            self.logger.error(f"Manual search failed: {e}")
            return []

    def get_collection_stats(self, document_hash: str = None, collection_name: str = None) -> Dict[str, Any]:
        """Get statistics about the collection using the stored function.

        Args:
            document_hash: Optional specific document hash to get stats for
            collection_name: Name of the collection (defaults to document_vectors)

        Returns:
            Dictionary containing collection statistics
        """
        try:
            function_name = f"{self.schema_name}.get_document_vector_stats"

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(f"SELECT * FROM {function_name}(%s)", (document_hash,))
                results = cursor.fetchall()

                if results:
                    stats = dict(results[0])
                    self.logger.info(f"Collection stats: {stats}")
                    return stats
                else:
                    return {
                        'total_vectors': 0,
                        'unique_documents': 0,
                        'avg_chunks_per_document': 0,
                        'document_hash': document_hash,
                        'vector_count': 0
                    }

        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            # Fallback to manual query
            return self._manual_get_stats(document_hash)

    def _manual_get_stats(self, document_hash: str = None) -> Dict[str, Any]:
        """Manual fallback stats query."""
        try:
            collection = self.table_name
            full_table_name = f"{self.schema_name}.{collection}"

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                if document_hash:
                    # Stats for specific document
                    sql = f"""
                    SELECT
                        COUNT(*) as vector_count,
                        %s as document_hash
                    FROM {full_table_name}
                    WHERE document_hash = %s
                    """
                    cursor.execute(sql, (document_hash, document_hash))
                else:
                    # Overall stats
                    sql = f"""
                    SELECT
                        COUNT(*) as total_vectors,
                        COUNT(DISTINCT document_hash) as unique_documents,
                        ROUND(COUNT(*)::numeric / NULLIF(COUNT(DISTINCT document_hash), 0), 2) as avg_chunks_per_document
                    FROM {full_table_name}
                    """
                    cursor.execute(sql)

                result = cursor.fetchone()
                if result:
                    stats = dict(result)
                    self.logger.info(f"Manual collection stats: {stats}")
                    return stats
                else:
                    return {}

        except Exception as e:
            self.logger.error(f"Manual stats query failed: {e}")
            return {}

    def delete_vectors(self, document_hash: str, collection_name: str = None) -> bool:
        """Delete vectors for a specific document.

        Args:
            document_hash: Hash of the document to delete
            collection_name: Name of the collection (defaults to document_vectors)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = collection_name or self.table_name
            full_table_name = f"{self.schema_name}.{collection}"

            with self.connection.cursor() as cursor:
                delete_sql = f"DELETE FROM {full_table_name} WHERE document_hash = %s;"
                cursor.execute(delete_sql, (document_hash,))

                rows_affected = cursor.rowcount
                self.connection.commit()

                self.logger.info(f"Deleted {rows_affected} vectors for document {document_hash}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to delete vectors for document {document_hash}: {e}")
            return False

    def get_existing_documents(self) -> List[Dict[str, Any]]:
        """Get list of existing documents from congress.documents table.

        Returns:
            List of document dictionaries
        """
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                sql = """
                SELECT document_hash, title, description, content_type, retrieved_at
                FROM congress.documents
                ORDER BY retrieved_at DESC
                LIMIT 100
                """
                cursor.execute(sql)
                results = cursor.fetchall()

                documents = []
                for row in results:
                    documents.append({
                        'document_hash': str(row['document_hash']),
                        'title': row['title'],
                        'description': row['description'],
                        'content_type': row['content_type'],
                        'retrieved_at': row['retrieved_at']
                    })

                return documents

        except Exception as e:
            self.logger.error(f"Failed to get existing documents: {e}")
            return []

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("PostgreSQL connection closed")


# Client factory function
def create_pgvector_client(config_path: str) -> PGVectorClient:
    """Create a pgvector client from configuration file.

    Args:
        config_path: Path to the configuration file

    Returns:
        PGVectorClient: Configured client instance
    """
    with open(config_path) as f:
        config = json.load(f)

    return PGVectorClient(config)
