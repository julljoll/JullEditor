import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "jurisdiction" in data

def test_parse_docling_endpoint():
    payload = {
        "content": "# Documento de Prueba Endpoint\n\nTexto sobre ciberseguridad y leyes.",
        "filename": "test_endpoint.md"
    }
    response = client.post("/api/parse-docling-md", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["title"] == "Documento de Prueba Endpoint"

def test_scrape_validation():
    response = client.post("/api/scrape", json={"url": "not-a-valid-url"})
    assert response.status_code == 400

def test_articles_history_endpoint():
    response = client.get("/api/articles-history")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "articles" in data
    assert isinstance(data["articles"], list)

def test_generate_header_image_endpoint():
    payload = {
        "title": "Prueba de Banner Cyber-Legal",
        "theme": "cybersecurity"
    }
    response = client.post("/api/generate-header-image", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "url" in data
    assert data["aspect_ratio"] == "16:9"
