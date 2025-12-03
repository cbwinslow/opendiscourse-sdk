"""
OpenDiscourse RAG (Retrieval-Augmented Generation) Service

This module implements a comprehensive RAG system for OpenDiscourse, 
integrating LangChain patterns for document retrieval and question answering
on government documents and legislative data.

Based on LangChain examples and adapted for OpenDiscourse use cases.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass

from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.llms import HuggingFaceHub
from langchain_core.documents import Document
from langchain_core.embeddings import FakeEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings

try:
    from langchain_ollama import OllamaLLM
except ImportError:
    OllamaLLM = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

from ..core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    """Result from RAG query."""
    answer: str
    source_documents: List[Document]
    query: str
    timestamp: datetime
    confidence_score: Optional[float] = None


@dataclass
class DocumentMetadata:
    """Metadata for documents in the RAG system."""
    source: str
    document_type: str
    date_ingested: datetime
    bill_number: Optional[str] = None
    congress_session: Optional[str] = None
    committee: Optional[str] = None


class OpenDiscourseRAGService:
    """
    RAG Service for OpenDiscourse that provides question-answering capabilities
    over government documents and legislative data.
    
    Features:
    - Document ingestion from various sources
    - Vector-based similarity search
    - Multiple LLM backends (OpenAI, Ollama, HuggingFace)
    - Legislative document metadata tracking
    """

    def __init__(
        self,
        vector_store_path: str = "./data/chroma_db",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_provider: str = "huggingface",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """Initialize the RAG service."""
        self.vector_store_path = vector_store_path
        self.embedding_model = embedding_model
        self.llm_provider = llm_provider
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize components
        self._setup_embeddings()
        self._setup_vector_store()
        self._setup_llm()
        self._setup_text_splitter()
        self._setup_qa_chain()
        
        logger.info(f"OpenDiscourse RAG Service initialized with {llm_provider} LLM")

    def _setup_embeddings(self):
        """Set up the embedding model."""
        if self.embedding_model == "fake":
            self.embeddings = FakeEmbeddings(size=384)
        else:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={"device": "cpu"}
            )

    def _setup_vector_store(self):
        """Set up the vector store."""
        os.makedirs(self.vector_store_path, exist_ok=True)
        self.vector_store = Chroma(
            persist_directory=self.vector_store_path,
            embedding_function=self.embeddings
        )

    def _setup_llm(self):
        """Set up the language model based on provider."""
        if self.llm_provider == "openai" and ChatOpenAI is not None:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        elif self.llm_provider == "ollama" and OllamaLLM is not None:
            self.llm = OllamaLLM(
                model=os.getenv("OLLAMA_MODEL", "llama3"),
                temperature=0.1
            )
        else:
            # Default to HuggingFace
            self.llm = HuggingFaceHub(
                repo_id="google/flan-t5-large",
                model_kwargs={"temperature": 0.1, "max_length": 512},
                huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_KEY")
            )

    def _setup_text_splitter(self):
        """Set up the text splitter for chunking documents."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )

    def _setup_qa_chain(self):
        """Set up the question-answering chain."""
        retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.5, "k": 4}
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=True
        )

    def ingest_document(
        self,
        file_path: str,
        metadata: Optional[DocumentMetadata] = None
    ) -> int:
        """
        Ingest a single document into the RAG system.
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata for the document
            
        Returns:
            Number of chunks created from the document
        """
        try:
            # Load document
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load()
            
            # Add metadata
            if metadata:
                for doc in documents:
                    doc.metadata.update({
                        "source": metadata.source,
                        "document_type": metadata.document_type,
                        "date_ingested": metadata.date_ingested.isoformat(),
                        "bill_number": metadata.bill_number,
                        "congress_session": metadata.congress_session,
                        "committee": metadata.committee,
                    })
            
            # Split documents
            chunks = self.text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(chunks)
            self.vector_store.persist()
            
            logger.info(f"Ingested {len(chunks)} chunks from {file_path}")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {e}")
            raise

    def ingest_directory(
        self,
        directory_path: str,
        file_pattern: str = "**/*.txt",
        document_type: str = "legislative"
    ) -> Dict[str, int]:
        """
        Ingest all documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            file_pattern: Glob pattern for files to include
            document_type: Type of documents being ingested
            
        Returns:
            Dictionary mapping file paths to number of chunks created
        """
        try:
            loader = DirectoryLoader(
                directory_path,
                glob=file_pattern,
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            
            documents = loader.load()
            
            # Add consistent metadata
            for doc in documents:
                doc.metadata.update({
                    "document_type": document_type,
                    "date_ingested": datetime.now().isoformat(),
                    "source": directory_path
                })
            
            # Split documents
            chunks = self.text_splitter.split_documents(documents)
            
            # Add to vector store
            self.vector_store.add_documents(chunks)
            self.vector_store.persist()
            
            # Create result mapping
            result = {}
            current_chunks = 0
            for doc in documents:
                doc_chunks = len(self.text_splitter.split_documents([doc]))
                result[doc.metadata.get("source", "unknown")] = doc_chunks
                current_chunks += doc_chunks
            
            logger.info(f"Ingested {len(documents)} documents ({current_chunks} chunks) from {directory_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error ingesting directory {directory_path}: {e}")
            raise

    def query(
        self,
        question: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGResult:
        """
        Query the RAG system with a question.
        
        Args:
            question: The question to ask
            filters: Optional metadata filters for retrieval
            
        Returns:
            RAGResult containing answer and source information
        """
        try:
            # If filters are provided, update retriever
            if filters:
                retriever = self.vector_store.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "score_threshold": 0.5,
                        "k": 4,
                        "filter": filters
                    }
                )
                # Update QA chain with filtered retriever
                self.qa_chain.retriever = retriever
            
            # Run the query
            result = self.qa_chain.invoke({"query": question})
            
            return RAGResult(
                answer=result["result"],
                source_documents=result.get("source_documents", []),
                query=question,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error processing query '{question}': {e}")
            raise

    def search_similar_documents(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Search for similar documents without generating an answer.
        
        Args:
            query: Search query
            k: Number of documents to return
            filters: Optional metadata filters
            
        Returns:
            List of similar documents
        """
        try:
            if filters:
                docs = self.vector_store.similarity_search(
                    query, k=k, filter=filters
                )
            else:
                docs = self.vector_store.similarity_search(query, k=k)
            
            return docs
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise

    def get_document_count(self) -> int:
        """Get the total number of documents in the vector store."""
        try:
            # This is a rough estimate since Chroma doesn't have a direct count method
            # We'll use a broad search to estimate
            test_docs = self.vector_store.similarity_search("", k=1000)
            return len(test_docs)
        except Exception:
            return 0

    def clear_vector_store(self):
        """Clear all documents from the vector store."""
        try:
            # Delete and recreate the vector store
            import shutil
            if os.path.exists(self.vector_store_path):
                shutil.rmtree(self.vector_store_path)
            self._setup_vector_store()
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current document collection."""
        try:
            doc_count = self.get_document_count()
            
            # Sample some documents to get metadata insights
            sample_docs = self.vector_store.similarity_search("", k=10)
            
            document_types = set()
            sources = set()
            
            for doc in sample_docs:
                if "document_type" in doc.metadata:
                    document_types.add(doc.metadata["document_type"])
                if "source" in doc.metadata:
                    sources.add(doc.metadata["source"])
            
            return {
                "total_documents": doc_count,
                "document_types": list(document_types),
                "sources": list(sources),
                "embedding_model": self.embedding_model,
                "llm_provider": self.llm_provider,
                "vector_store_path": self.vector_store_path
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}


# Utility functions for specialized government document processing

def create_bill_metadata(
    bill_number: str,
    congress_session: str,
    committee: Optional[str] = None
) -> DocumentMetadata:
    """Create metadata for a congressional bill."""
    return DocumentMetadata(
        source=f"Congress {congress_session}",
        document_type="bill",
        date_ingested=datetime.now(),
        bill_number=bill_number,
        congress_session=congress_session,
        committee=committee
    )


def create_committee_metadata(
    committee_name: str,
    congress_session: str
) -> DocumentMetadata:
    """Create metadata for committee documents."""
    return DocumentMetadata(
        source=f"Committee {committee_name}",
        document_type="committee_document",
        date_ingested=datetime.now(),
        congress_session=congress_session,
        committee=committee_name
    )


# Example usage and testing functions

def example_usage():
    """Example of how to use the OpenDiscourse RAG Service."""
    
    # Initialize service
    rag_service = OpenDiscourseRAGService(
        llm_provider="huggingface",  # or "openai", "ollama"
        embedding_model="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Ingest a directory of documents
    if os.path.exists("./data/documents"):
        results = rag_service.ingest_directory(
            "./data/documents",
            "**/*.txt",
            "legislative"
        )
        print(f"Ingested documents: {results}")
    
    # Query the system
    question = "What is the main purpose of this legislation?"
    result = rag_service.query(question)
    
    print(f"Question: {result.query}")
    print(f"Answer: {result.answer}")
    print(f"Sources: {len(result.source_documents)} documents")
    
    # Search for similar documents
    similar_docs = rag_service.search_similar_documents(
        "budget appropriations",
        k=3
    )
    
    for i, doc in enumerate(similar_docs):
        print(f"Document {i+1}: {doc.metadata.get('source', 'Unknown')}")
        print(f"Preview: {doc.page_content[:200]}...")
    
    # Get collection info
    info = rag_service.get_collection_info()
    print(f"Collection info: {info}")


if __name__ == "__main__":
    example_usage()

