"""Integration tests for the OpenDiscourse system."""

import os
import pytest
import psycopg2
from uuid import uuid4

from api.routes.task_inference_endpoints import insert_task, insert_inference


@pytest.fixture
def test_db_url():
    """Provide test database URL."""
    return os.environ.get(
        "TEST_RAG_DB_URL",
        "postgresql://postgres:password@localhost:5432/opendiscourse_test"
    )


@pytest.fixture
def setup_test_db(test_db_url):
    """Set up test database with required tables."""
    try:
        conn = psycopg2.connect(test_db_url)
        cur = conn.cursor()
        
        # Create test tables if they don't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title TEXT,
                description TEXT,
                status TEXT CHECK(status IN ('todo', 'in-progress', 'completed', 'cancelled')),
                priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')),
                assignee TEXT,
                due_date TIMESTAMP WITH TIME ZONE,
                metadata JSONB,
                entity_ids UUID[],
                document_ids UUID[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                confidence FLOAT CHECK(confidence >= 0 AND confidence <= 1),
                source_document_id UUID,
                source_task_id UUID,
                metadata JSONB,
                entity_ids UUID[],
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cur.close()
        conn.close()
        
        yield test_db_url
        
        # Cleanup
        conn = psycopg2.connect(test_db_url)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS tasks CASCADE;")
        cur.execute("DROP TABLE IF EXISTS inferences CASCADE;")
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


def test_task_insertion(setup_test_db):
    """Test task insertion into database."""
    # Set environment variable for the function to use
    os.environ["RAG_DB_URL"] = setup_test_db
    
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": "todo",
        "priority": "high",
        "assignee": "test_user",
        "metadata": {"category": "testing"}
    }
    
    task_id = insert_task(task_data)
    
    assert task_id is not None
    assert isinstance(task_id, str)
    
    # Verify task was inserted
    conn = psycopg2.connect(setup_test_db)
    cur = conn.cursor()
    cur.execute("SELECT title, status, priority FROM tasks WHERE id = %s", (task_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    assert result is not None
    assert result[0] == "Test Task"
    assert result[1] == "todo"
    assert result[2] == "high"


def test_inference_insertion(setup_test_db):
    """Test inference insertion into database."""
    # Set environment variable for the function to use
    os.environ["RAG_DB_URL"] = setup_test_db
    
    inference_data = {
        "type": "classification",
        "content": "This is a positive sentiment inference",
        "confidence": 0.95,
        "metadata": {"model": "test_model"}
    }
    
    inference_id = insert_inference(inference_data)
    
    assert inference_id is not None
    assert isinstance(inference_id, str)
    
    # Verify inference was inserted
    conn = psycopg2.connect(setup_test_db)
    cur = conn.cursor()
    cur.execute("SELECT type, content, confidence FROM inferences WHERE id = %s", (inference_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    assert result is not None
    assert result[0] == "classification"
    assert result[1] == "This is a positive sentiment inference"
    assert result[2] == 0.95


def test_task_with_relationships(setup_test_db):
    """Test task insertion with entity and document relationships."""
    # Set environment variable for the function to use
    os.environ["RAG_DB_URL"] = setup_test_db
    
    entity_id = str(uuid4())
    document_id = str(uuid4())
    
    task_data = {
        "title": "Task with Relations",
        "description": "Task linked to entities and documents",
        "status": "in-progress",
        "priority": "medium",
        "entity_ids": [entity_id],
        "document_ids": [document_id],
        "metadata": {"linked": True}
    }
    
    task_id = insert_task(task_data)
    assert task_id is not None
    
    # Verify relationships were stored
    conn = psycopg2.connect(setup_test_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT entity_ids, document_ids FROM tasks WHERE id = %s", 
        (task_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    assert result is not None
    assert entity_id in result[0]
    assert document_id in result[1]


def test_inference_with_source_references(setup_test_db):
    """Test inference insertion with source document and task references."""
    # Set environment variable for the function to use
    os.environ["RAG_DB_URL"] = setup_test_db
    
    # First create a task to reference
    task_data = {
        "title": "Source Task",
        "description": "Task that generates inference",
        "status": "completed"
    }
    source_task_id = insert_task(task_data)
    
    # Create inference referencing the task
    inference_data = {
        "type": "summary",
        "content": "Task completed successfully",
        "confidence": 0.9,
        "source_task_id": source_task_id,
        "metadata": {"auto_generated": True}
    }
    
    inference_id = insert_inference(inference_data)
    assert inference_id is not None
    
    # Verify source reference was stored
    conn = psycopg2.connect(setup_test_db)
    cur = conn.cursor()
    cur.execute(
        "SELECT source_task_id FROM inferences WHERE id = %s", 
        (inference_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    assert result is not None
    assert result[0] == source_task_id


def test_multiple_task_insertion(setup_test_db):
    """Test inserting multiple tasks and verify they're all stored."""
    # Set environment variable for the function to use
    os.environ["RAG_DB_URL"] = setup_test_db
    
    task_data_list = [
        {
            "title": f"Batch Task {i}",
            "description": f"Description for task {i}",
            "status": "todo",
            "priority": "low"
        }
        for i in range(5)
    ]
    
    task_ids = []
    for task_data in task_data_list:
        task_id = insert_task(task_data)
        task_ids.append(task_id)
    
    assert len(task_ids) == 5
    assert all(task_id is not None for task_id in task_ids)
    assert len(set(task_ids)) == 5  # All IDs should be unique
    
    # Verify all tasks were inserted
    conn = psycopg2.connect(setup_test_db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks WHERE title LIKE 'Batch Task%'")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    assert count == 5
