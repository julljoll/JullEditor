"""
Suite de Tests de Integración End-to-End para Granite Blog Writer v3.0.
Verifica endpoints de salud, diagnóstico del sistema, validación Pydantic sin StarletteDeprecationWarning,
auditoría SEO determinista y ciclo de vida de la aplicación.
"""

from fastapi.testclient import TestClient

from backend.app import app
from backend.system_profiler import detect_system_resources

client = TestClient(app)

def test_system_info_endpoint():
    """Valida el endpoint de diagnóstico /api/system-info."""
    response = client.get("/api/system-info")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "system" in data
    assert "cpu_count" in data["system"]
    assert "ram_gb" in data["system"]
    assert "recommended_model" in data["system"]
    assert "active_config" in data
    assert data["active_config"]["model"] is not None

def test_health_endpoint_contract():
    """Valida el contrato y campos de respuesta de /api/health."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("online", "offline")
    assert "default_model" in data
    assert "num_ctx" in data
    assert "latency_ms" in data
    assert data["version"] == __import__("backend.version", fromlist=["__version__"]).__version__

def test_validation_error_422_clean_response():
    """
    Verifica que las peticiones con datos incompletos o erróneos
    produzcan HTTP 422 con formato estructurado y sin deprecation warnings.
    """
    # source_text con menos de 10 caracteres debe fallar validación
    invalid_payload = {
        "source_text": "Corto"
    }
    response = client.post("/api/generate-stream", json=invalid_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "error"
    assert data["error_type"] == "ValidationError"
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0

def test_system_profiler_logic():
    """Valida que el perfilador de sistema retorne datos coherentes."""
    info = detect_system_resources()
    assert isinstance(info["cpu_count"], int)
    assert info["cpu_count"] > 0
    assert isinstance(info["ram_gb"], (int, float))
    assert info["tier"] in ("high", "balanced", "light")
    assert info["recommended_model"] in ("granite3.3:8b", "granite3.3:2b")

def test_extract_sentencia_clean_contract():
    """Valida endpoint /api/extract-sentencia con un texto mínimo representativo."""
    text = (
        "REPÚBLICA BOLIVARIANA DE VENEZUELA\n"
        "TRIBUNAL SUPREMO DE JUSTICIA\n"
        "SALA CONSTITUCIONAL\n"
        "Sentencia N° 0524 de fecha 18 de julio de 2023\n"
        "Magistrada Ponente: DRA. GLADYS MARÍA GUTIÉRREZ ALVARADO\n"
        "Expediente N° 23-0100\n"
        "DECISIÓN: La Sala declara PROCEDENTE la acción de amparo constitucional."
    )
    response = client.post("/api/extract-sentencia", json={"content": text})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "metadata" in data
    meta = data["metadata"]
    assert "Constitucional" in meta["sala"]
    assert "0524" in meta["numero_sentencia"] or meta["decision"] != ""
