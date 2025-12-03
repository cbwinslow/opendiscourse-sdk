from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskIngestionRequest(BaseModel):
    """Request model for ingesting tasks."""
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks to ingest")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for tasks")

class InferenceIngestionRequest(BaseModel):
    """Request model for ingesting inferences."""
    inferences: List[Dict[str, Any]] = Field(..., description="List of inferences to ingest")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for inferences")

class TaskIngestionResponse(BaseModel):
    success: bool
    task_ids: List[str]
    metadata: Optional[Dict[str, Any]]

class InferenceIngestionResponse(BaseModel):
    success: bool
    inference_ids: List[str]
    metadata: Optional[Dict[str, Any]]
