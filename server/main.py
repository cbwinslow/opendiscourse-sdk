from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import tempfile
import textract
import psycopg2
from psycopg2.extras import Json
from .diagnostics import router as diagnostics_router

app = FastAPI(title="OpenDiscourse API", version="0.1.0")

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection config (customize as needed)
DB_URL = os.environ.get("RAG_DB_URL", "postgresql://user:password@localhost:5432/opendiscourse")

# Include the diagnostics router
app.include_router(diagnostics_router)

def insert_document_to_db(title, content, doc_type, metadata):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO documents (title, content, doc_type, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (title, content, doc_type, Json(metadata))
        )
        doc_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return doc_id
    except Exception as e:
        print(f"DB insert error: {e}")
        return None

def get_media(media_id: int):
    # Placeholder: fetch media appearance by ID
    return {"media_id": media_id, "media": None}

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    # Placeholder: fetch task by ID
    return {"task_id": task_id, "task": None}

@app.get("/inference/{inference_id}")
def get_inference(inference_id: int):
    # Placeholder: fetch inference by ID
    return {"inference_id": inference_id, "inference": None}

@app.get("/status")
def status():
    # General status endpoint
    return {"status": "running", "version": app.version}

@app.post("/ingest/document")
def ingest_document(file: UploadFile = File(...)):
    # Validate file type
    allowed_types = [
        "application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
    # Save file to temp location
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        # Extract text using textract (handles PDF, DOCX, TXT, HTML, etc.)
        text = textract.process(tmp_path).decode("utf-8", errors="replace")
        metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": os.path.getsize(tmp_path)
        }
        doc_id = insert_document_to_db(
            title=file.filename,
            content=text,
            doc_type=file.content_type,
            metadata=metadata
        )
        if doc_id is None:
            raise HTTPException(status_code=500, detail="Failed to insert document into DB")
        result = {
            "doc_id": doc_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": os.path.getsize(tmp_path),
            "extracted_text_sample": text[:500],
            "status": "ingested into DB"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text or insert: {str(e)}")
    finally:
        os.remove(tmp_path)
    return result

def insert_entity_to_db(name, type_, contact_info, social_handles, bio):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO entities (name, type, contact_info, social_handles, bio)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (name, type_, Json(contact_info), Json(social_handles), bio)
        )
        entity_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return entity_id
    except Exception as e:
        print(f"DB insert error: {e}")
        return None

@app.post("/ingest/entity")
def ingest_entity(entity: dict):
    # Validate required fields
    required = ["name"]
    for field in required:
        if field not in entity:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    entity_id = insert_entity_to_db(
        name=entity["name"],
        type_=entity.get("type"),
        contact_info=entity.get("contact_info", {}),
        social_handles=entity.get("social_handles", {}),
        bio=entity.get("bio")
    )
    if entity_id is None:
        raise HTTPException(status_code=500, detail="Failed to insert entity into DB")
    return {"entity_id": entity_id, "status": "ingested into DB"}

def insert_media_to_db(entity_id, platform, title, transcript, date, url):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO media_appearances (entity_id, platform, title, transcript, date, url)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (entity_id, platform, title, transcript, date, url)
        )
        media_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return media_id
    except Exception as e:
        print(f"DB insert error: {e}")
        return None

@app.post("/ingest/media")
def ingest_media(media: dict):
    required = ["entity_id", "platform", "title"]
    for field in required:
        if field not in media:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    media_id = insert_media_to_db(
        entity_id=media["entity_id"],
        platform=media["platform"],
        title=media["title"],
        transcript=media.get("transcript"),
        date=media.get("date"),
        url=media.get("url")
    )
    if media_id is None:
        raise HTTPException(status_code=500, detail="Failed to insert media appearance into DB")
    return {"media_id": media_id, "status": "ingested into DB"}

@app.post("/ingest/task")
def ingest_task(task: dict):
    # Placeholder: ingest a new task
    return {"status": "received", "task": task}

@app.post("/ingest/inference")
def ingest_inference(inference: dict):
    # Placeholder: ingest a new inference
    return {"status": "received", "inference": inference}
