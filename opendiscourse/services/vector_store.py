"""Vector database implementation using ChromaDB and sentence-transformers."""

from __future__ import annotations

import atexit
import logging
import os
from pathlib import Path
from typing import TypeVar, cast, final

try:
    import torch
except ImportError:
    torch = None

from dotenv import load_dotenv

try:
    from langchain_community.vectorstores import Chroma
    from langchain_core.embeddings import Embeddings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logging.warning(f"LangChain or sentence-transformers not available: {e}")
    Chroma = None
    Embeddings = None
    RecursiveCharacterTextSplitter = None
    SentenceTransformer = None

from typing_extensions import NotRequired, TypedDict, override  # noqa: F401

# Load environment variables early
load_dotenv()

# Type aliases
DocumentScore = tuple[dict[str, str], float]
DocumentMetadata = dict[str, str]  # Enforce string values for metadata

# Get logger for this module
logger = logging.getLogger(__name__)


if Embeddings is not None:
    @final
    class SentenceTransformerEmbeddings(Embeddings):
        """Wrapper around SentenceTransformer models for use with LangChain."""

        def __init__(
            self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
        ) -> None:
            """Initialize with model name."""
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is required for this class")
            
            device = "cpu"
            if torch is not None and torch.cuda.is_available():
                device = "cuda"
                
            self.model: SentenceTransformer = SentenceTransformer(
                model_name, device=device
            )



    @override
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed search docs.

        Args:
            texts: List of text documents to embed.

        Returns:
            List of embeddings, one for each input text.
        """
        return cast(
            "list[list[float]]",
            self.model.encode(texts, convert_to_numpy=True).tolist(),
        )

    @override
    def embed_query(self, text: str) -> list[float]:
        """Embed query text.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector for the input text.
        """
        return cast(
            "list[float]", self.model.encode(text, convert_to_numpy=True).tolist()
        )


T = TypeVar("T")

# Configuration from environment variables
DEFAULT_STORAGE_DIRECTORY = os.getenv("VECTOR_DB_STORAGE_DIR", "./chroma_db")
DEFAULT_EMBEDDING_MODEL = os.getenv("VECTOR_DB_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
DEFAULT_COLLECTION_NAME = os.getenv("VECTOR_DB_COLLECTION_NAME", "documents")
DEFAULT_CHUNK_SIZE = int(os.getenv("VECTOR_DB_CHUNK_SIZE", "1000"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("VECTOR_DB_CHUNK_OVERLAP", "200"))


class VectorDatabaseError(Exception):
    """Base exception for vector database errors."""


class VectorDatabaseInitializationError(VectorDatabaseError):
    """Raised when vector database initialization fails."""


class VectorDatabaseOperationError(VectorDatabaseError):
    """Raised when vector database operations fail."""


class VectorDatabase:
    """A vector database implementation using ChromaDB for document storage.

    This class provides methods to add, search, and manage documents with their
    vector embeddings. It uses sentence-transformers for generating embeddings
    and ChromaDB for efficient similarity search.
    
    Configuration can be provided via environment variables:
    - VECTOR_DB_STORAGE_DIR: Directory to persist the database
    - VECTOR_DB_EMBEDDING_MODEL: Name of the sentence transformer model
    - VECTOR_DB_COLLECTION_NAME: Name of the collection to store documents
    - VECTOR_DB_CHUNK_SIZE: Size of text chunks for processing
    - VECTOR_DB_CHUNK_OVERLAP: Overlap between text chunks
    """

    persist_directory: Path
    embeddings: SentenceTransformerEmbeddings
    collection_name: str
    chunk_size: int
    chunk_overlap: int
    _vector_store: Chroma | None = None
    _shutdown_registered: bool = False

    @property
    def vector_store(self) -> Chroma:
        """Lazily initialize and return the vector store."""
        if self._vector_store is None:

            self._vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(self.persist_directory),
            )
            logger.info("Vector store initialized successfully")
            
            # Register shutdown handler if not already done
            if not self._shutdown_registered:
                atexit.register(self._shutdown)
                self._shutdown_registered = True
                
        return cast("Chroma", self._vector_store)

    def __init__(
        self,
        embeddings_model: str | None = None,
        collection_name: str | None = None,
        persist_directory: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> None:
        """Initialize the VectorDatabase.

        Args:
            embeddings_model: Name of the sentence transformer model to use for
                embeddings. If None, uses environment variable or default.
            collection_name: Name of the collection to store documents in.
                If None, uses environment variable or default.
            persist_directory: Directory to persist the database to.
                If None, uses environment variable or default.
            chunk_size: Size of text chunks for processing.
                If None, uses environment variable or default.
            chunk_overlap: Overlap between text chunks.
                If None, uses environment variable or default.
        """


    def _shutdown(self) -> None:
        """Graceful shutdown to flush or close resources."""
        logger.info("Shutting down VectorDatabase...")
        try:
            if self._vector_store is not None:
                # Force persistence of any pending changes
                self._vector_store.persist()
                logger.info("Vector store persisted successfully")
        except Exception as e:
            logger.warning("Error during vector store shutdown: %s", str(e))
        
        try:
            # Clear model from memory if loaded
            if hasattr(self.embeddings, '_model') and self.embeddings._model is not None:
                del self.embeddings._model
                logger.debug("Embedding model cleared from memory")
        except Exception as e:
            logger.warning("Error clearing embedding model: %s", str(e))
            
        logger.info("VectorDatabase shutdown completed")

    def _ensure_initialized(self) -> None:
        """Ensure the vector store is initialized.

        Creates the persist directory if it doesn't exist.
        The vector store itself is lazily initialized when accessed.
        """
        try:
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            logger.debug("Storage directory ensured: %s", self.persist_directory)
        except Exception as e:
            logger.error("Failed to create storage directory: %s", str(e))
            raise VectorDatabaseInitializationError(
                f"Failed to create storage directory {self.persist_directory}: {e}"
            ) from e

    def _chunk_text(self, content: str) -> list[str]:
        """Split text into chunks.

        Args:
            content: The text content to split.

        Returns:
            List of chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )
        return text_splitter.split_text(content)

    def add_document(
        self, document_id: int, content: str, metadata: dict[str, str]
    ) -> None:
        """Add a document to the vector database.

        Args:
            document_id: Unique identifier for the document
            content: The text content of the document
            metadata: Additional metadata for the document

        Raises:
            VectorDatabaseOperationError: If adding the document fails
        """
        if not content.strip():
            error_msg = "Document content cannot be empty"
            raise VectorDatabaseOperationError(error_msg)

        try:
            # Split the content into chunks
            chunks = self._chunk_text(content)

            # Add chunks to the vector store
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_{i}"
                chunk_metadata = {
                    **metadata,
                    "chunk_index": str(i),  # Ensure string type for metadata
                    "document_id": str(document_id),
                    "total_chunks": str(len(chunks)),
                }
                self.vector_store.add_texts(
                    texts=[chunk], metadatas=[chunk_metadata], ids=[chunk_id]
                )

            logger.info("Added document %s with %d chunks", document_id, len(chunks))

        except Exception as e:
            error_msg = f"Failed to add document {document_id}: {e!s}"
            logger.error(error_msg)
            raise VectorDatabaseOperationError(error_msg) from e

    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: dict[str, str] | None = None,
    ) -> list[tuple[dict[str, str], float]]:
        """Search for similar documents.

        Args:
            query: The search query string.
            k: Number of results to return.
            filter_dict: Optional dictionary of filters to apply to the search.

        Returns:
            List of tuples containing (document_metadata, score) pairs.

        Raises:
            VectorDatabaseOperationError: If the search fails.
        """
        if not query.strip():
            error_msg = "Query cannot be empty"
            raise VectorDatabaseOperationError(error_msg)

        try:
            # Convert filter_dict to Chroma's filter format if provided
            filter_condition = None
            if filter_dict:
                filter_condition = {
                    "$and": [{k: {"$eq": v}} for k, v in filter_dict.items()]
                }

            results = self.vector_store.similarity_search_with_score(
                query=query, k=k, filter=filter_condition
            )

            # Convert Document objects to metadata dictionaries
            return [
                ({"text": doc.page_content, **doc.metadata}, score)
                for doc, score in results
            ]

        except Exception as e:
            error_msg = f"Search failed: {e!s}"
            logger.exception("Search operation failed")
            raise VectorDatabaseOperationError(error_msg) from e

    def get_document_chunks(
        self, document_id: int
    ) -> list[tuple[int, str, dict[str, str]]]:
        """Retrieve all chunks for a specific document.

        Args:
            document_id: ID of the document to retrieve.

        Returns:
            List of tuples containing (chunk_index, chunk_text, metadata).

        Raises:
            VectorDatabaseOperationError: If retrieval fails.
        """
        try:
            # Query for all chunks of the document
            results = self.vector_store.similarity_search(
                query="",  # Empty query to get all documents
                filter={"document_id": str(document_id)},
                k=1000,  # Arbitrary large number to get all chunks
            )

            # Extract and sort chunks by chunk_index
            chunks = []
            for doc in results:
                try:
                    chunk_index = int(doc.metadata.get("chunk_index", "0"))
                    chunks.append((chunk_index, doc.page_content, doc.metadata))
                except (ValueError, AttributeError) as e:
                    logging.warning("Invalid chunk metadata: %s", str(e))
                    continue

            # Sort by chunk_index
            chunks.sort(key=lambda x: x[0])
            return chunks

        except Exception as e:
            error_msg = f"Failed to retrieve chunks for document {document_id}: {e!s}"
            logging.exception("Failed to retrieve document chunks")
            raise VectorDatabaseOperationError(error_msg) from e

    def delete_documents(self, ids: list[str] | None = None) -> None:
        """Delete documents from the vector store.

        Args:
            ids: Optional list of document IDs to delete. If None, all documents
                will be deleted.

        Raises:
            VectorDatabaseOperationError: If the deletion fails.
        """
        try:
            if ids is None:
                # Delete all documents by getting all document IDs first
                all_docs = self.vector_store.get(include=[])
                doc_ids: list[str] = all_docs.get("ids", [])  # type: ignore[assignment]
                if doc_ids:
                    self.vector_store.delete(ids=doc_ids)
                    logging.info(
                        "Deleted all %d documents from the vector store.", len(doc_ids)
                    )
                else:
                    logging.info("No documents to delete.")
            elif ids:
                self.vector_store.delete(ids=ids)
                logging.info("Deleted %d documents from the vector store.", len(ids))
        except Exception as e:
            error_msg = f"Failed to delete documents: {e!s}"
            logging.exception("Failed to delete documents")
            raise VectorDatabaseOperationError(error_msg) from e

    def persist(self) -> None:
        """Persist the vector database to disk.

        This ensures all pending changes are written to disk.

        Raises:
            VectorDatabaseOperationError: If persisting fails.
        """
        try:
            if self._vector_store is not None:
                self._vector_store.persist()
                logging.info("Vector database persisted to disk")
        except Exception as e:
            error_msg = f"Failed to persist vector database: {e!s}"
            logging.exception("Failed to persist vector database")
            raise VectorDatabaseOperationError(error_msg) from e


# Initialize vector database
vector_db = VectorDatabase()
