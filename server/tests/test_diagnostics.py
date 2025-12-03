import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_linux_diagnostics():
    response = client.get("/diagnostics/linux")
    assert response.status_code == 200
    data = response.json()
    assert "hardware" in data
    assert "network" in data
    assert "collection_errors" in data
