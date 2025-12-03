"""Tests for task and inference ingestion endpoints."""
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "title": "Test Task",
        "description": "A test task for validation",
        "status": "todo",
        "priority": "high",
        "assignee": "test_user",
        "metadata": {"source": "test"},
        "entity_ids": ["entity1", "entity2"],
        "document_ids": ["doc1", "doc2"]
    }

@pytest.fixture
def sample_inference_data():
    """Sample inference data for testing."""
    return {
        "type": "classification",
        "content": "This is a test inference",
        "confidence": 0.95,
        "source_document_id": "doc1",
        "metadata": {"model": "test_model"},
        "entity_ids": ["entity1"]
    }

@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cur
        yield mock_cur

class TestTaskIngestionEndpoint:
    """Test cases for task ingestion endpoint."""

    def test_ingest_tasks_success(self, mock_db_connection, sample_task_data):
        """Test successful task ingestion."""
        # Mock successful database insert
        mock_db_connection.execute.return_value = None

        request_data = {
            "tasks": [sample_task_data],
            "metadata": {"batch_id": "test_batch"}
        }

        with patch('uuid.uuid4', return_value=MagicMock(str=lambda: "test-task-id")):
            response = client.post("/v1/ingest/tasks", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["task_ids"] == ["test-task-id"]
        assert result["metadata"]["batch_id"] == "test_batch"

    def test_ingest_tasks_multiple(self, mock_db_connection, sample_task_data):
        """Test ingesting multiple tasks."""
        mock_db_connection.execute.return_value = None

        task_data_2 = sample_task_data.copy()
        task_data_2["title"] = "Test Task 2"

        request_data = {
            "tasks": [sample_task_data, task_data_2],
            "metadata": {"batch_id": "multi_test"}
        }

        with patch('uuid.uuid4', side_effect=[
            MagicMock(str=lambda: "task-id-1"),
            MagicMock(str=lambda: "task-id-2")
        ]):
            response = client.post("/v1/ingest/tasks", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["task_ids"]) == 2
        assert "task-id-1" in result["task_ids"]
        assert "task-id-2" in result["task_ids"]

    def test_ingest_tasks_database_error(self, mock_db_connection, sample_task_data):
        """Test task ingestion with database error."""
        # Mock database error
        mock_db_connection.execute.side_effect = Exception("Database connection failed")

        request_data = {
            "tasks": [sample_task_data]
        }

        response = client.post("/v1/ingest/tasks", json=request_data)
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_ingest_tasks_empty_list(self, mock_db_connection):
        """Test ingesting empty task list."""
        request_data = {
            "tasks": []
        }

        response = client.post("/v1/ingest/tasks", json=request_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["task_ids"] == []

    def test_ingest_tasks_validation_error(self):
        """Test task ingestion with validation error."""
        # Missing required 'tasks' field
        request_data = {
            "metadata": {"test": "data"}
        }

        response = client.post("/v1/ingest/tasks", json=request_data)
        assert response.status_code == 422  # Validation error


class TestInferenceIngestionEndpoint:
    """Test cases for inference ingestion endpoint."""

    def test_ingest_inferences_success(self, mock_db_connection, sample_inference_data):
        """Test successful inference ingestion."""
        mock_db_connection.execute.return_value = None

        request_data = {
            "inferences": [sample_inference_data],
            "metadata": {"model_version": "1.0"}
        }

        with patch('uuid.uuid4', return_value=MagicMock(str=lambda: "test-inference-id")):
            response = client.post("/v1/ingest/inferences", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["inference_ids"] == ["test-inference-id"]
        assert result["metadata"]["model_version"] == "1.0"

    def test_ingest_inferences_multiple(self, mock_db_connection, sample_inference_data):
        """Test ingesting multiple inferences."""
        mock_db_connection.execute.return_value = None

        inference_data_2 = sample_inference_data.copy()
        inference_data_2["content"] = "Second test inference"

        request_data = {
            "inferences": [sample_inference_data, inference_data_2]
        }

        with patch('uuid.uuid4', side_effect=[
            MagicMock(str=lambda: "inference-id-1"),
            MagicMock(str=lambda: "inference-id-2")
        ]):
            response = client.post("/v1/ingest/inferences", json=request_data)

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert len(result["inference_ids"]) == 2

    def test_ingest_inferences_database_error(self, mock_db_connection, sample_inference_data):
        """Test inference ingestion with database error."""
        mock_db_connection.execute.side_effect = Exception("Database error")

        request_data = {
            "inferences": [sample_inference_data]
        }

        response = client.post("/v1/ingest/inferences", json=request_data)
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_ingest_inferences_empty_list(self, mock_db_connection):
        """Test ingesting empty inference list."""
        request_data = {
            "inferences": []
        }

        response = client.post("/v1/ingest/inferences", json=request_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["inference_ids"] == []

    def test_ingest_inferences_validation_error(self):
        """Test inference ingestion with validation error."""
        # Missing required 'inferences' field
        request_data = {
            "metadata": {"test": "data"}
        }

        response = client.post("/v1/ingest/inferences", json=request_data)
        assert response.status_code == 422  # Validation error


class TestEndpointIntegration:
    """Integration tests for task and inference endpoints."""

    @pytest.mark.integration
    def test_task_inference_workflow(self, mock_db_connection, sample_task_data, sample_inference_data):
        """Test complete workflow of task and inference ingestion."""
        mock_db_connection.execute.return_value = None

        # First, ingest a task
        task_request = {
            "tasks": [sample_task_data],
            "metadata": {"workflow": "test"}
        }

        with patch('uuid.uuid4', return_value=MagicMock(str=lambda: "workflow-task-id")):
            task_response = client.post("/v1/ingest/tasks", json=task_request)

        assert task_response.status_code == 200
        task_result = task_response.json()
        task_id = task_result["task_ids"][0]

        # Then, ingest an inference related to the task
        inference_data_with_task = sample_inference_data.copy()
        inference_data_with_task["source_task_id"] = task_id

        inference_request = {
            "inferences": [inference_data_with_task],
            "metadata": {"workflow": "test"}
        }

        with patch('uuid.uuid4', return_value=MagicMock(str=lambda: "workflow-inference-id")):
            inference_response = client.post("/v1/ingest/inferences", json=inference_request)

        assert inference_response.status_code == 200
        inference_result = inference_response.json()
        assert len(inference_result["inference_ids"]) == 1

    def test_database_insert_calls(self, mock_db_connection, sample_task_data, sample_inference_data):
        """Test that database insert calls are made with correct parameters."""
        mock_db_connection.execute.return_value = None

        # Test task insertion
        task_request = {"tasks": [sample_task_data]}

        with patch('uuid.uuid4', return_value=MagicMock(str=lambda: "test-id")):
            client.post("/v1/ingest/tasks", json=task_request)

        # Verify INSERT was called for tasks table
        mock_db_connection.execute.assert_called()
        call_args = mock_db_connection.execute.call_args[0]
        assert "INSERT INTO tasks" in call_args[0]

        # Reset mock for inference test
        mock_db_connection.reset_mock()

        # Test inference insertion
        inference_request = {"inferences": [sample_inference_data]}

        with patch('uuid.uuid4', return_value=MagicMock(str=lambda: "test-inference-id")):
            client.post("/v1/ingest/inferences", json=inference_request)

        # Verify INSERT was called for inferences table
        mock_db_connection.execute.assert_called()
        call_args = mock_db_connection.execute.call_args[0]
        assert "INSERT INTO inferences" in call_args[0]


if __name__ == "__main__":
    pytest.main([__file__])
