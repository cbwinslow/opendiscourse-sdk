from datetime import datetime
from typing import Optional

# Import the new endpoints
from api.routes.task_inference_endpoints import router as task_inference_router
from api.routes.llm_endpoints import router as llm_router
from api.routes.auth_endpoints import router as auth_router
from ..config.settings import Settings
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.models.models import ConfigurationRequest, DocumentRequest, SearchRequest
from models.response_models import (DocumentResponse, HealthCheckResponse,
                                    MetricsResponse, SearchResponse)
from services.health_check import HealthCheckService
from services.monitoring import MonitoringService
from services.vector_store import VectorStoreService

app = FastAPI(
    title="Vector Store API",
    description="API for vector store operations with monitoring and health checks",
    version="1.0.0"
)

# Register routers
app.include_router(task_inference_router)
app.include_router(llm_router)
app.include_router(auth_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = Settings()
vector_store_service = VectorStoreService(settings)
monitoring_service = MonitoringService(settings)
health_check_service = HealthCheckService(settings)


@app.get("/health")
async def health_check() -> HealthCheckResponse:
    """Check the health status of all system components."""
    try:
        health_status = await health_check_service.check_health()
        return HealthCheckResponse(
            status="healthy" if health_status.is_healthy else "unhealthy",
            details=health_status.details,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search(
    request: SearchRequest,
    background_tasks: BackgroundTasks
) -> SearchResponse:
    """Search across vector stores with query."""
    try:
        # Record operation start
        operation_id = monitoring_service.start_operation("search")

        # Perform search
        results = await vector_store_service.search(
            query=request.query,
            k=request.k,
            filters=request.filters
        )

        # Record metrics in background
        background_tasks.add_task(
            monitoring_service.record_operation_complete,
            operation_id=operation_id,
            status="success"
        )

        return SearchResponse(
            results=results,
            metadata={
                "total_results": len(results),
                "query_time": monitoring_service.get_operation_duration(operation_id)
            }
        )

    except Exception as e:
        # Record error in background
        background_tasks.add_task(
            monitoring_service.record_operation_complete,
            operation_id=operation_id,
            status="error",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/documents")
async def add_documents(
    request: DocumentRequest,
    background_tasks: BackgroundTasks
) -> DocumentResponse:
    """Add documents to vector stores."""
    try:
        operation_id = monitoring_service.start_operation("add_documents")

        # Process and add documents
        results = await vector_store_service.add_documents(
            documents=request.documents,
            metadata=request.metadata
        )

        # Record success in background
        background_tasks.add_task(
            monitoring_service.record_operation_complete,
            operation_id=operation_id,
            status="success"
        )

        return DocumentResponse(
            success=True,
            document_ids=results.document_ids,
            metadata=results.metadata
        )

    except Exception as e:
        background_tasks.add_task(
            monitoring_service.record_operation_complete,
            operation_id=operation_id,
            status="error",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """Delete a document from vector stores."""
    try:
        operation_id = monitoring_service.start_operation("delete_document")

        await vector_store_service.delete_document(document_id)

        background_tasks.add_task(
            monitoring_service.record_operation_complete,
            operation_id=operation_id,
            status="success"
        )

        return JSONResponse(
            content={"success": True, "document_id": document_id},
            status_code=200
        )

    except Exception as e:
        background_tasks.add_task(
            monitoring_service.record_operation_complete,
            operation_id=operation_id,
            status="error",
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> MetricsResponse:
    """Get system metrics and statistics."""
    try:
        metrics = await monitoring_service.get_metrics(start_time, end_time)
        return MetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config")
async def update_configuration(
    request: ConfigurationRequest
) -> JSONResponse:
    """Update system configuration."""
    try:
        await vector_store_service.update_configuration(request.settings)
        return JSONResponse(
            content={"success": True, "message": "Configuration updated"},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies")
async def get_anomalies(
    lookback_hours: Optional[int] = 24
) -> JSONResponse:
    """Get detected anomalies in system performance."""
    try:
        anomalies = await monitoring_service.get_anomalies(lookback_hours)
        return JSONResponse(
            content={"anomalies": anomalies},
            status_code=200
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
