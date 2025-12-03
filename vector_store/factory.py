from typing import Dict, Type

from .base import VectorStoreBase
from .stores import (
    ChromaDBStore,
    ElasticsearchStore,
    PineconeStore,
    WeaviateStore,
    OpenSearchStore,
    ClickHouseStore
)

class VectorStoreFactory:
    """Factory class for creating vector store instances."""
    
    # Map store type strings to their corresponding classes
    STORE_TYPES: Dict[str, Type[VectorStoreBase]] = {
        "chromadb": ChromaDBStore,
        "elasticsearch": ElasticsearchStore,
        "pinecone": PineconeStore,
        "weaviate": WeaviateStore,
        "opensearch": OpenSearchStore,
        "clickhouse": ClickHouseStore
    }
    
    @staticmethod
    def create(store_type: str, **kwargs) -> VectorStoreBase:
        """Create a vector store instance of the specified type.
        
        Args:
            store_type: The type of vector store to create (must be one of the supported types)
            **kwargs: Additional arguments passed to the store's constructor
            
        Returns:
            An instance of the specified vector store type
            
        Raises:
            ValueError: If the specified store type is not supported
        """
        store_class = VectorStoreFactory.STORE_TYPES.get(store_type.lower())
        if store_class is None:
            supported_types = ", ".join(VectorStoreFactory.STORE_TYPES.keys())
            raise ValueError(
                f"Unsupported vector store type: {store_type}. "
                f"Supported types are: {supported_types}"
            )
        
        return store_class(**kwargs)
