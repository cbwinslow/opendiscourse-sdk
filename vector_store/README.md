# Vector Store Implementations

This package provides a unified interface for interacting with various vector store backends. The implementation includes support for:

- ChromaDB
- Elasticsearch
- Pinecone
- Weaviate
- OpenSearch
- ClickHouse

## Architecture

The package is organized around three main components:

1. `VectorStoreBase` - Abstract base class defining the interface for vector stores
2. Store implementations - Concrete implementations for each supported vector store
3. `VectorStoreFactory` - Factory class for instantiating vector stores

### VectorStoreBase Interface

```python
class VectorStoreBase(ABC):
    @abstractmethod
    def add_document(self, doc_id: str, content: str, metadata: Dict) -> None:
        """Add a document to the vector store."""
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[DocumentScore]:
        """Search for similar documents in the vector store."""
        pass
    
    @abstractmethod
    def delete(self, doc_ids: List[str]) -> None:
        """Delete documents from the vector store."""
        pass
```

## Usage

To use a vector store, first instantiate it through the factory:

```python
from vector_store import VectorStoreFactory

# Create a ChromaDB store
store = VectorStoreFactory.create("chromadb")

# Create an Elasticsearch store with custom configuration
es_store = VectorStoreFactory.create(
    "elasticsearch",
    hosts=["localhost:9200"],
    http_auth=("user", "pass")
)
```

Then use the store's methods to add, search, and delete documents:

```python
# Add a document
store.add_document(
    doc_id="doc1",
    content="This is a sample document.",
    metadata={"author": "John Doe", "date": "2023-01-01"}
)

# Search for similar documents
results = store.search("sample document", k=5)
for doc in results:
    print(f"Document {doc.doc_id}: {doc.content} (score: {doc.score})")

# Delete documents
store.delete(["doc1"])
```

## Implementation Details

Each vector store implementation handles the following responsibilities:

1. Connection management and initialization
2. Converting between text and vector representations (via `_encode_text`)
3. Document storage and retrieval
4. Vector similarity search
5. Metadata management

Note: The vector encoding implementation (`_encode_text`) is left as a placeholder in the base implementations. You'll need to implement this method using your chosen embedding model.

## Dependencies

Each vector store implementation requires its corresponding client library:

- ChromaDB: `chromadb`
- Elasticsearch: `elasticsearch`
- Pinecone: `pinecone-client`
- Weaviate: `weaviate-client`
- OpenSearch: `opensearch-py`
- ClickHouse: `clickhouse-driver`

## Configuration

Each store type accepts different configuration options through the factory's `create` method. Refer to each store's client library documentation for available options.
