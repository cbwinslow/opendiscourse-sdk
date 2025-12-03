from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, NamedTuple

class DocumentScore(NamedTuple):
    """Represents a document and its similarity score."""
    doc_id: str
    score: float
    content: str
    metadata: Dict

class VectorStoreBase(ABC):
    """Abstract base class for vector store operations."""
    
    @abstractmethod
    def add_document(self, doc_id: str, content: str, metadata: Dict) -> None:
        """Add a document to the vector store.
        
        Args:
            doc_id: Unique identifier for the document
            content: Text content of the document
            metadata: Additional metadata for the document
        """
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 5) -> List[DocumentScore]:
        """Search for similar documents in the vector store.
        
        Args:
            query: Query text to search for
            k: Number of results to return (default: 5)
            
        Returns:
            List of DocumentScore containing matched documents and their scores
        """
        pass
    
    @abstractmethod
    def delete(self, doc_ids: List[str]) -> None:
        """Delete documents from the vector store.
        
        Args:
            doc_ids: List of document IDs to delete
        """
        pass
