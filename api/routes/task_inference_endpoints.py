import os
import uuid
from datetime import datetime
from typing import Dict

import psycopg2
import psycopg2.extras
from api.models.task_inference_models import (InferenceIngestionRequest,
                                              InferenceIngestionResponse,
                                              TaskIngestionRequest,
                                              TaskIngestionResponse)
from fastapi import APIRouter, BackgroundTasks, HTTPException

router = APIRouter(prefix="/v1", tags=["Task & Inference Ingestion"])

DB_URL = os.environ.get(
    "RAG_DB_URL", "postgresql://user:password@localhost:5432/opendiscourse"
)


def insert_task(task_data: Dict) -> str:
    """Insert a task into the database and return the generated ID."""
    task_id = str(uuid.uuid4())
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO tasks (id, title, description, status, priority, assignee, 
                             due_date, metadata, entity_ids, document_ids)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task_id,
                task_data.get("title"),
                task_data.get("description"), 
                task_data.get("status", "todo"),
                task_data.get("priority", "medium"),
                task_data.get("assignee"),
                task_data.get("due_date"),
                psycopg2.extras.Json(task_data.get("metadata", {})),
                task_data.get("entity_ids", []),
                task_data.get("document_ids", [])
            )
        )
        conn.commit()
        return task_id
    finally:
        cur.close()
        conn.close()


def insert_inference(inference_data: Dict) -> str:
    """Insert an inference into the database and return the generated ID."""
    inference_id = str(uuid.uuid4())
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    try:
        cur.execute(
            """
            INSERT INTO inferences (id, type, content, confidence, source_document_id,
                                  source_task_id, metadata, entity_ids)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                inference_id,
                inference_data.get("type"),
                inference_data.get("content"),
                inference_data.get("confidence"),
                inference_data.get("source_document_id"),
                inference_data.get("source_task_id"),
                psycopg2.extras.Json(inference_data.get("metadata", {})),
                inference_data.get("entity_ids", [])
            )
        )
        conn.commit()
        return inference_id
    finally:
        cur.close()
        conn.close()


@router.post("/ingest/tasks", response_model=TaskIngestionResponse)
async def ingest_tasks(request: TaskIngestionRequest, background_tasks: BackgroundTasks) -> TaskIngestionResponse:
    """Ingest tasks into the system."""
    try:
        task_ids = []
        for task_data in request.tasks:
            task_id = insert_task(task_data)
            task_ids.append(task_id)
        
        return TaskIngestionResponse(success=True, task_ids=task_ids, metadata=request.metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/inferences", response_model=InferenceIngestionResponse)
async def ingest_inferences(request: InferenceIngestionRequest, background_tasks: BackgroundTasks) -> InferenceIngestionResponse:
    """Ingest inferences into the system."""
    try:
        inference_ids = []
        for inference_data in request.inferences:
            inference_id = insert_inference(inference_data)
            inference_ids.append(inference_id)
        
        return InferenceIngestionResponse(success=True, inference_ids=inference_ids, metadata=request.metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
