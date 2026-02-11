"""
Qdrant vector database client implementation.

This module provides a client for storing and querying vector embeddings
using Qdrant vector database.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        VectorParams,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class QdrantVectorClient:
    """Client for Qdrant vector database."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Qdrant client.

        Args:
            config: Configuration dictionary containing connection details
        """
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client library not installed. Install with: pip install qdrant-client")

        self.config = config
        self.logger = logging.getLogger(__name__)

        # Connection parameters
        self.host = config['host']
        self.port = config['port']
        self.grpc_port = config.get('grpc_port', 6334)
        self.api_key = config.get('api_key', None)

        # Collection settings
        self.collection_name = config['settings']['collection_name']
        self.vector_size = config['settings']['vector_size']
        self.distance_metric = config['settings']['distance_metric']

        # Initialize client
        self.client = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Qdrant."""
        try:
            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                grpc_port=self.grpc_port,
                api_key=self.api_key,
                prefer_grpc=self.config.get('prefer_grpc', True)
            )
            self.logger.info(f"Successfully connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Qdrant: {e}")
            raise

    def health_check(self) -> bool:
        """Check if the Qdrant service is healthy and responsive.

        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Try to get collections info
            collections = self.client.get_collections()
            return True
        except Exception as e:
            self.logger.error(f"Qdrant health check failed: {e}")
            return False

    def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Create a vector collection.

        Args:
            collection_name: Name of the collection
            dimension: Vector dimension

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert distance metric to Qdrant format
            distance_map = {
                'cosine': Distance.COSINE,
                'euclidean': Distance.EUCLID,
                'dot': Distance.DOT
            }
            distance = distance_map.get(self.distance_metric.lower(), Distance.COSINE)

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=distance)
            )

            self.logger.info(f"Successfully created collection: {collection_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create collection {collection_name}: {e}")
            return False

    def insert_vectors(self,
                      vectors: List[List[float]],
                      metadatas: List[Dict[str, Any]],
                      collection_name: str = None,
                      ids: Optional[List[str]] = None) -> bool:
        """Insert vectors into the collection.

        Args:
            vectors: List of vector embeddings
            metadatas: List of metadata dictionaries
            collection_name: Name of the collection (defaults to configured collection)
            ids: Optional list of point IDs

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = collection_name or self.collection_name

            # Prepare points
            points = []
            for i, (vector, metadata) in enumerate(zip(vectors, metadatas)):
                point_id = ids[i] if ids and i < len(ids) else i

                # Create payload
                payload = {
                    'document_hash': metadata.get('document_hash', ''),
                    'chunk_index': metadata.get('chunk_index', i),
                    'content': metadata.get('content', ''),
                    'created_at': datetime.now().isoformat(),
                    **{k: v for k, v in metadata.items()
                       if k not in ['document_hash', 'chunk_index', 'content']}
                }

                points.append(PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                ))

            # Upload points
            self.client.upsert(
                collection_name=collection,
                points=points
            )

            self.logger.info(f"Successfully inserted {len(vectors)} vectors into {collection}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to insert vectors: {e}")
            return False

    def search_similar(self,
                      query_vector: List[float],
                      top_k: int = 10,
                      threshold: float = 0.7,
                      collection_name: str = None,
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors.

        Args:
            query_vector: Query vector embedding
            top_k: Number of results to return
            threshold: Similarity threshold
            collection_name: Name of the collection (defaults to configured collection)
            filters: Optional filters to apply

        Returns:
            List of dictionaries containing similar vectors and metadata
        """
        try:
            collection = collection_name or self.collection_name

            # Prepare search filters
            search_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    ))
                search_filter = Filter(must=conditions)

            # Perform search
            search_results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=top_k,
                score_threshold=threshold,
                query_filter=search_filter
            )

            # Format results
            similar_vectors = []
            for result in search_results:
                similar_vectors.append({
                    'id': str(result.id),
                    'content': result.payload.get('content', ''),
                    'document_hash': result.payload.get('document_hash', ''),
                    'chunk_index': result.payload.get('chunk_index', 0),
                    'metadata': {k: v for k, v in result.payload.items()
                               if k not in ['content', 'document_hash', 'chunk_index']},
                    'similarity': float(result.score)
                })

            self.logger.info(f"Found {len(similar_vectors)} similar vectors in {collection}")
            return similar_vectors

        except Exception as e:
            self.logger.error(f"Failed to search similar vectors: {e}")
            return []

    def get_collection_stats(self, collection_name: str = None) -> Dict[str, Any]:
        """Get statistics about the collection.

        Args:
            collection_name: Name of the collection (defaults to configured collection)

        Returns:
            Dictionary containing collection statistics
        """
        try:
            collection = collection_name or self.collection_name

            collection_info = self.client.get_collection(collection_name=collection)

            stats = {
                'collection_name': collection,
                'vectors_count': collection_info.vectors_count,
                'segments_count': collection_info.segments_count,
                'status': collection_info.status,
                'vector_size': collection_info.config.params.vectors.size,
                'distance': collection_info.config.params.vectors.distance.value
            }

            self.logger.info(f"Collection stats for {collection}: {stats}")
            return stats

        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {}

    def delete_vectors(self,
                      document_hash: str,
                      collection_name: str = None,
                      filters: Optional[Dict[str, Any]] = None) -> bool:
        """Delete vectors for a specific document.

        Args:
            document_hash: Hash of the document to delete
            collection_name: Name of the collection (defaults to configured collection)
            filters: Additional filters for deletion

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = collection_name or self.collection_name

            # Create filter for document
            delete_filter = Filter(must=[
                FieldCondition(
                    key="document_hash",
                    match=MatchValue(value=document_hash)
                )
            ])

            # Apply additional filters if provided
            if filters:
                for key, value in filters.items():
                    delete_filter.must.append(FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    ))

            # Delete points
            result = self.client.delete(
                collection_name=collection,
                points_selector=delete_filter
            )

            self.logger.info(f"Deleted vectors for document {document_hash} in {collection}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete vectors for document {document_hash}: {e}")
            return False

    def create_payload_index(self,
                            field_name: str,
                            collection_name: str = None) -> bool:
        """Create a payload index for faster filtering.

        Args:
            field_name: Name of the field to index
            collection_name: Name of the collection (defaults to configured collection)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            collection = collection_name or self.collection_name

            self.client.create_payload_index(
                collection_name=collection,
                field_name=field_name
            )

            self.logger.info(f"Created payload index for field '{field_name}' in {collection}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create payload index for '{field_name}': {e}")
            return False

    def list_collections(self) -> List[str]:
        """List all collections in Qdrant.

        Returns:
            List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [collection.name for collection in collections.collections]
        except Exception as e:
            self.logger.error(f"Failed to list collections: {e}")
            return []

    def close(self) -> None:
        """Close the Qdrant client connection."""
        if self.client:
            # Qdrant client doesn't require explicit close for HTTP
            # but we can log the closure
            self.logger.info("Qdrant client connection closed")


# Client factory function
def create_qdrant_client(config_path: str) -> QdrantVectorClient:
    """Create a Qdrant client from configuration file.

    Args:
        config_path: Path to the configuration file

    Returns:
        QdrantVectorClient: Configured client instance
    """
    with open(config_path) as f:
        config = json.load(f)

    return QdrantVectorClient(config)
