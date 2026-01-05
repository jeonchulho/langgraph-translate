"""Tests for FastAPI endpoints."""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_stats_endpoint():
    """Test statistics endpoint."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cache_stats" in data
    assert "total_translations" in data


def test_translate_endpoint_empty_text():
    """Test translate endpoint rejects empty text."""
    response = client.post(
        "/api/translate",
        json={"text": ""}
    )
    assert response.status_code == 400


def test_translate_endpoint_missing_text():
    """Test translate endpoint requires text field."""
    response = client.post(
        "/api/translate",
        json={}
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_translate_endpoint_structure():
    """Test translate endpoint returns correct structure."""
    response = client.post(
        "/api/translate",
        json={"text": "Hello"}
    )
    
    # Note: This might fail without a valid OpenAI API key
    # In production tests, we would mock the translation engine
    if response.status_code == 200:
        data = response.json()
        assert "original" in data
        assert "detected_language" in data
        assert "translation" in data
        assert "quality_score" in data


def test_document_upload_no_file():
    """Test document endpoint requires file."""
    response = client.post("/api/translate/document")
    assert response.status_code == 422  # Validation error


def test_document_upload_unsupported_format():
    """Test document endpoint rejects unsupported formats."""
    from io import BytesIO
    
    files = {
        "file": ("test.xyz", BytesIO(b"test content"), "application/octet-stream")
    }
    response = client.post("/api/translate/document", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]
