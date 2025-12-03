from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

from models.enhanced_models import (
    BulkSearchRequest,
    SemanticSearchRequest,
    IndexStatsRequest,
    ReindexRequest,
    OptimizeRequest,
    BackupRequest,
    TrainingRequest,
    EmbeddingRequest,
    ClusteringRequest,
    AnalyticsRequest
)

router = APIRouter(prefix="/v1", tags=["Enhanced Operations"])

# Advanced Search Operations
@router.post("/search/bulk")
async def bulk_search(request: BulkSearchRequest) -> Dict:
    """Perform bulk search operations across multiple queries."""
    try:
        results = await search_service.bulk_search(
            queries=request.queries,
            k=request.k,
            filters=request.filters
        )
        return {
            "success": True,
            "results": results,
            "metadata": {
                "total_queries": len(request.queries),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/semantic")
async def semantic_search(request: SemanticSearchRequest) -> Dict:
    """Perform semantic search with query expansion and context."""
    try:
        expanded_results = await search_service.semantic_search(
            query=request.query,
            context=request.context,
            k=request.k
        )
        return {
            "success": True,
            "results": expanded_results,
            "metadata": {
                "expanded_query": expanded_results.expanded_query,
                "context_score": expanded_results.context_score
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Index Management
@router.get("/index/stats")
async def get_index_stats(request: IndexStatsRequest) -> Dict:
    """Get detailed statistics about the vector indices."""
    try:
        stats = await index_service.get_stats(
            store_names=request.store_names,
            include_vectors=request.include_vectors
        )
        return {
            "success": True,
            "stats": stats,
            "metadata": {
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/reindex")
async def reindex(
    request: ReindexRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """Reindex documents with updated settings."""
    try:
        task_id = await index_service.start_reindex(
            store_names=request.store_names,
            settings=request.settings
        )
        
        background_tasks.add_task(
            index_service.monitor_reindex_task,
            task_id=task_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Reindex operation started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/optimize")
async def optimize_index(request: OptimizeRequest) -> Dict:
    """Optimize vector indices for better performance."""
    try:
        results = await index_service.optimize(
            store_names=request.store_names,
            optimization_type=request.optimization_type
        )
        return {
            "success": True,
            "results": results,
            "metadata": {
                "optimization_type": request.optimization_type,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Backup and Recovery
@router.post("/backup")
async def create_backup(request: BackupRequest) -> Dict:
    """Create a backup of vector stores."""
    try:
        backup_id = await backup_service.create_backup(
            store_names=request.store_names,
            backup_type=request.backup_type
        )
        return {
            "success": True,
            "backup_id": backup_id,
            "metadata": {
                "backup_type": request.backup_type,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    background_tasks: BackgroundTasks
) -> Dict:
    """Restore from a backup."""
    try:
        task_id = await backup_service.start_restore(backup_id)
        
        background_tasks.add_task(
            backup_service.monitor_restore_task,
            task_id=task_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Restore operation started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model Management
@router.post("/models/train")
async def train_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """Train or fine-tune embedding models."""
    try:
        task_id = await model_service.start_training(
            model_type=request.model_type,
            training_data=request.training_data,
            parameters=request.parameters
        )
        
        background_tasks.add_task(
            model_service.monitor_training_task,
            task_id=task_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Training started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/embed")
async def generate_embeddings(request: EmbeddingRequest) -> Dict:
    """Generate embeddings for input text."""
    try:
        embeddings = await model_service.generate_embeddings(
            texts=request.texts,
            model_name=request.model_name
        )
        return {
            "success": True,
            "embeddings": embeddings,
            "metadata": {
                "model_name": request.model_name,
                "dimension": len(embeddings[0])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Insights
@router.post("/analytics/cluster")
async def cluster_documents(request: ClusteringRequest) -> Dict:
    """Perform document clustering analysis."""
    try:
        clusters = await analytics_service.cluster_documents(
            store_names=request.store_names,
            n_clusters=request.n_clusters,
            algorithm=request.algorithm
        )
        return {
            "success": True,
            "clusters": clusters,
            "metadata": {
                "algorithm": request.algorithm,
                "n_clusters": request.n_clusters
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analytics/insights")
async def generate_insights(request: AnalyticsRequest) -> Dict:
    """Generate insights from vector store data."""
    try:
        insights = await analytics_service.generate_insights(
            store_names=request.store_names,
            analysis_type=request.analysis_type,
            parameters=request.parameters
        )
        return {
            "success": True,
            "insights": insights,
            "metadata": {
                "analysis_type": request.analysis_type,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# System Operations
@router.post("/system/vacuum")
async def vacuum_stores(store_names: Optional[List[str]] = None) -> Dict:
    """Clean up and optimize storage."""
    try:
        results = await system_service.vacuum_stores(store_names)
        return {
            "success": True,
            "results": results,
            "metadata": {
                "stores_affected": len(results),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/tasks")
async def get_running_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None
) -> Dict:
    """Get status of running background tasks."""
    try:
        tasks = await system_service.get_tasks(
            task_type=task_type,
            status=status
        )
        return {
            "success": True,
            "tasks": tasks,
            "metadata": {
                "total_tasks": len(tasks),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
