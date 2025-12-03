"""
FastAPI RAG API for OpenDiscourse

This module provides REST API endpoints for the RAG (Retrieval-Augmented Generation) service,
allowing users to query government documents and legislative data through HTTP requests.

Based on LangChain RAG webapp example and adapted for OpenDiscourse.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Header, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from .rag_service import OpenDiscourseRAGService, RAGResult, DocumentMetadata
from ..core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OpenDiscourse RAG API",
    description="Retrieval-Augmented Generation API for government documents and legislative data",
    version="1.0.0",
    docs_url="/api/v1/rag/docs",
    redoc_url="/api/v1/rag/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG service instance
rag_service: Optional[OpenDiscourseRAGService] = None


def get_rag_service() -> OpenDiscourseRAGService:
    """Get or create the RAG service instance."""
    global rag_service
    if rag_service is None:
        rag_service = OpenDiscourseRAGService(
            vector_store_path=os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db"),
            embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            llm_provider=os.getenv("LLM_PROVIDER", "huggingface")
        )
    return rag_service


def verify_api_token(x_api_token: str = Header(None)) -> str:
    """Verify API token for protected endpoints."""
    expected_token = os.getenv("API_TOKEN")
    if expected_token and x_api_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token"
        )
    return x_api_token


# Request/Response models

class QueryRequest(BaseModel):
    """Request model for RAG queries."""
    question: str = Field(..., description="The question to ask", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")
    include_sources: bool = Field(True, description="Whether to include source documents")


class QueryResponse(BaseModel):
    """Response model for RAG queries."""
    answer: str
    query: str
    timestamp: datetime
    sources: Optional[List[Dict[str, Any]]] = None
    total_sources: int


class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str = Field(..., description="Search query", min_length=1)
    k: int = Field(5, description="Number of documents to return", ge=1, le=20)
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional metadata filters")


class SearchResponse(BaseModel):
    """Response model for document search."""
    documents: List[Dict[str, Any]]
    total_results: int
    query: str


class IngestionRequest(BaseModel):
    """Request model for document ingestion."""
    directory_path: str = Field(..., description="Path to directory containing documents")
    file_pattern: str = Field("**/*.txt", description="Glob pattern for files to include")
    document_type: str = Field("legislative", description="Type of documents being ingested")


class IngestionResponse(BaseModel):
    """Response model for document ingestion."""
    files_processed: Dict[str, int]
    total_files: int
    total_chunks: int
    message: str


class CollectionInfoResponse(BaseModel):
    """Response model for collection information."""
    total_documents: int
    document_types: List[str]
    sources: List[str]
    embedding_model: str
    llm_provider: str
    vector_store_path: str


class BillMetadataRequest(BaseModel):
    """Request model for bill metadata."""
    bill_number: str = Field(..., description="Bill number (e.g., 'H.R. 1234')")
    congress_session: str = Field(..., description="Congress session (e.g., '118th')")
    committee: Optional[str] = Field(None, description="Committee name")


class CommitteeMetadataRequest(BaseModel):
    """Request model for committee metadata."""
    committee_name: str = Field(..., description="Committee name")
    congress_session: str = Field(..., description="Congress session")


# API Endpoints

@app.get("/api/v1/rag/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "OpenDiscourse RAG API"
    }


@app.post("/api/v1/rag/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    service: OpenDiscourseRAGService = Depends(get_rag_service)
):
    """
    Query the RAG system with a question.
    
    This endpoint allows you to ask questions about the ingested documents
    and receive AI-generated answers based on the document content.
    """
    try:
        result = service.query(request.question, request.filters)
        
        sources = None
        if request.include_sources and result.source_documents:
            sources = [
                {
                    "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Unknown")
                }
                for doc in result.source_documents
            ]
        
        return QueryResponse(
            answer=result.answer,
            query=result.query,
            timestamp=result.timestamp,
            sources=sources,
            total_sources=len(result.source_documents)
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/api/v1/rag/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    service: OpenDiscourseRAGService = Depends(get_rag_service)
):
    """
    Search for similar documents without generating an answer.
    
    This endpoint performs similarity search to find documents
    relevant to your query.
    """
    try:
        documents = service.search_similar_documents(
            request.query,
            request.k,
            request.filters
        )
        
        formatted_docs = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "Unknown")
            }
            for doc in documents
        ]
        
        return SearchResponse(
            documents=formatted_docs,
            total_results=len(formatted_docs),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error searching documents: {str(e)}"
        )


@app.post("/api/v1/rag/ingest", response_model=IngestionResponse)
async def ingest_documents(
    request: IngestionRequest,
    service: OpenDiscourseRAGService = Depends(get_rag_service),
    _: str = Depends(verify_api_token)
):
    """
    Ingest documents from a directory into the RAG system.
    
    This endpoint requires API token authentication and allows you to
    add new documents to the searchable collection.
    """
    try:
        # Validate directory exists
        if not os.path.exists(request.directory_path):
            raise HTTPException(
                status_code=400,
                detail=f"Directory not found: {request.directory_path}"
            )
        
        # Perform ingestion
        results = service.ingest_directory(
            request.directory_path,
            request.file_pattern,
            request.document_type
        )
        
        total_chunks = sum(results.values())
        
        return IngestionResponse(
            files_processed=results,
            total_files=len(results),
            total_chunks=total_chunks,
            message=f"Successfully ingested {len(results)} files ({total_chunks} chunks)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting documents: {str(e)}"
        )


@app.post("/api/v1/rag/ingest/file")
async def ingest_single_file(
    file: UploadFile = File(...),
    bill_number: Optional[str] = None,
    congress_session: Optional[str] = None,
    committee: Optional[str] = None,
    document_type: str = "legislative",
    service: OpenDiscourseRAGService = Depends(get_rag_service),
    _: str = Depends(verify_api_token)
):
    """
    Upload and ingest a single document file.
    
    This endpoint allows you to upload a file directly through the API
    and have it processed by the RAG system.
    """
    try:
        # Create temporary file
        temp_dir = Path("./temp")
        temp_dir.mkdir(exist_ok=True)
        
        temp_file_path = temp_dir / file.filename
        
        # Save uploaded file
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create metadata if provided
        metadata = None
        if bill_number and congress_session:
            metadata = DocumentMetadata(
                source=f"Upload: {file.filename}",
                document_type=document_type,
                date_ingested=datetime.now(),
                bill_number=bill_number,
                congress_session=congress_session,
                committee=committee
            )
        
        # Ingest the file
        chunks = service.ingest_document(str(temp_file_path), metadata)
        
        # Clean up temporary file
        temp_file_path.unlink()
        
        return {
            "filename": file.filename,
            "chunks_created": chunks,
            "message": f"Successfully ingested {file.filename} ({chunks} chunks)"
        }
        
    except Exception as e:
        logger.error(f"Error ingesting file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting file: {str(e)}"
        )


@app.get("/api/v1/rag/collection", response_model=CollectionInfoResponse)
async def get_collection_info(
    service: OpenDiscourseRAGService = Depends(get_rag_service)
):
    """
    Get information about the current document collection.
    
    This endpoint provides statistics and metadata about the documents
    currently available in the RAG system.
    """
    try:
        info = service.get_collection_info()
        
        return CollectionInfoResponse(
            total_documents=info.get("total_documents", 0),
            document_types=info.get("document_types", []),
            sources=info.get("sources", []),
            embedding_model=info.get("embedding_model", ""),
            llm_provider=info.get("llm_provider", ""),
            vector_store_path=info.get("vector_store_path", "")
        )
        
    except Exception as e:
        logger.error(f"Error getting collection info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting collection info: {str(e)}"
        )


@app.delete("/api/v1/rag/collection")
async def clear_collection(
    service: OpenDiscourseRAGService = Depends(get_rag_service),
    _: str = Depends(verify_api_token)
):
    """
    Clear all documents from the collection.
    
    ⚠️ WARNING: This will permanently delete all ingested documents!
    This endpoint requires API token authentication.
    """
    try:
        service.clear_vector_store()
        return {
            "message": "Collection cleared successfully",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error clearing collection: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing collection: {str(e)}"
        )


# Specialized endpoints for government documents

@app.post("/api/v1/rag/query/bills")
async def query_bills(
    request: QueryRequest,
    congress_session: Optional[str] = None,
    service: OpenDiscourseRAGService = Depends(get_rag_service)
):
    """
    Query specifically for congressional bills.
    
    This endpoint filters the search to only include bills and
    optionally further filters by Congress session.
    """
    filters = {"document_type": "bill"}
    if congress_session:
        filters["congress_session"] = congress_session
    
    # Merge with any existing filters
    if request.filters:
        filters.update(request.filters)
    
    request.filters = filters
    return await query_documents(request, service)


@app.post("/api/v1/rag/query/committees")
async def query_committees(
    request: QueryRequest,
    committee_name: Optional[str] = None,
    service: OpenDiscourseRAGService = Depends(get_rag_service)
):
    """
    Query specifically for committee documents.
    
    This endpoint filters the search to only include committee documents
    and optionally further filters by committee name.
    """
    filters = {"document_type": "committee_document"}
    if committee_name:
        filters["committee"] = committee_name
    
    # Merge with any existing filters
    if request.filters:
        filters.update(request.filters)
    
    request.filters = filters
    return await query_documents(request, service)


# Utility endpoints

@app.get("/api/v1/rag/stats")
async def get_stats(
    service: OpenDiscourseRAGService = Depends(get_rag_service)
):
    """Get basic statistics about the RAG system."""
    try:
        info = service.get_collection_info()
        
        return {
            "status": "operational",
            "total_documents": info.get("total_documents", 0),
            "document_types": len(info.get("document_types", [])),
            "sources": len(info.get("sources", [])),
            "embedding_model": info.get("embedding_model", ""),
            "llm_provider": info.get("llm_provider", ""),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now()
        }


# Main application runner
def main():
    """Run the RAG API server."""
    uvicorn.run(
        "opendiscourse.langchain_integrations.rag_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()

