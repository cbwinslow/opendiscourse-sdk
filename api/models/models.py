from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


# Request Models
class SearchRequest(BaseModel):
    """Request model for search operations."""
    query: str = Field(..., description="Search query string")
    k: int = Field(10, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(
        None, description="Optional search filters"
    )

    class Config:
        schema_extra = {
            "example": {
                "query": "example search query",
                "k": 10,
                "filters": {"category": "technology"}
            }
        }


class DocumentRequest(BaseModel):
    """Request model for document operations."""
    documents: List[Dict[str, Any]] = Field(
        ..., description="List of documents to process"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Optional metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    {
                        "content": "Example document content",
                        "metadata": {"source": "web", "author": "John Doe"}
                    }
                ],
                "metadata": {"batch_id": "123", "timestamp": "2025-06-21T18:00:00Z"}
            }
        }


class ConfigurationRequest(BaseModel):
    """Request model for configuration updates."""
    settings: Dict[str, Any] = Field(
        ..., description="Configuration settings to update"
    )

    class Config:
        schema_extra = {
            "example": {
                "settings": {
                    "vector_dimension": 768,
                    "similarity_metric": "cosine",
                    "index_type": "hnsw"
                }
            }
        }


class HealthCheckRequest(BaseModel):
    """Request model for health checks."""
    components: Optional[List[str]] = Field(
        None, description="Specific components to check"
    )
    detailed: bool = Field(
        False, description="Whether to return detailed status"
    )

    class Config:
        schema_extra = {
            "example": {
                "components": ["elasticsearch", "chromadb", "pinecone"],
                "detailed": True
            }
        }


# Response Models
class SearchResult(BaseModel):
    """Model for individual search results."""
    id: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]]


class SearchResponse(BaseModel):
    """Response model for search operations."""
    results: List[SearchResult]
    metadata: Dict[str, Any]


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    success: bool
    document_ids: List[str]
    metadata: Optional[Dict[str, Any]]


class HealthStatus(BaseModel):
    """Model for component health status."""
    status: str
    latency_ms: float
    error_message: Optional[str]
    details: Optional[Dict[str, Any]]


class HealthCheckResponse(BaseModel):
    """Response model for health checks."""
    status: str
    details: Dict[str, HealthStatus]
    timestamp: str


class MetricValue(BaseModel):
    """Model for metric values."""
    current: float
    average: float
    peak: float
    timestamp: str


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    latency: MetricValue
    throughput: MetricValue
    error_rate: MetricValue
    system_metrics: Dict[str, MetricValue]
    store_metrics: Dict[str, Dict[str, MetricValue]]


class AnomalyResponse(BaseModel):
    """Response model for anomaly detection."""
    anomalies: List[Dict[str, Any]]
    summary: Dict[str, Any]
