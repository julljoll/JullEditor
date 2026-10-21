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
    assert "num_ctx" in data
    assert "num_thread" in data
    assert "keep_alive" in data

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

def test_scrape_ssrf_rejection():
    # Intento de SSRF a localhost / 127.0.0.1 debe ser rechazado
    response = client.post("/api/scrape", json={"url": "http://127.0.0.1:11434/api/tags"})
    assert response.status_code == 400
    assert "SSRF" in response.json().get("detail", "") or "seguridad" in response.json().get("detail", "")

def test_seo_audit_endpoint():
    markdown = """# Título del Artículo Optimizado para Ciberseguridad

> **Meta descripción:** Descubre las mejores prácticas de ciberseguridad forense y cómo aplicar el marco regulatorio para proteger los activos informáticos hoy mismo.

Palabra Clave Primaria: ciberseguridad forense | Jurisdicción: Venezuela 🇻🇪

## 📑 Tabla de Contenidos
1. [Introducción](#seccion-1)

## Sección de Análisis Forense Digital {#seccion-1}
La **ciberseguridad forense** permite determinar la causa raíz de incidentes.
La evidencia digital debe preservarse conforme a la cadena de custodia.

## ❓ Preguntas Frecuentes
P: ¿Qué es la ciberseguridad forense?
R: Es la disciplina técnica que recolecta y analiza evidencia digital.

## ✍️ Sobre el Autor
Perito en informática forense con certificación internacional.

## Conclusión y Debate
Comparte tus opiniones en los comentarios.

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Título del Artículo"
}
```
"""
    response = client.post("/api/seo-audit", json={"markdown": markdown})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    report = data["report"]
    assert report["score"] > 50
    assert report["has_meta_description"] is True
    assert report["has_toc"] is True
    assert report["has_faq"] is True
    assert report["has_schema_jsonld"] is True
    assert report["schema_jsonld_valid"] is True

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

def test_sitejet_lab_static_endpoint():
    response = client.get("/sitejet-lab.html")
    assert response.status_code == 200
    assert "Sitejet Builder" in response.text
    assert "Matriz de Calibración" in response.text

def test_sitejet_exporter_module_served():
    response = client.get("/js/modules/sitejet-exporter.js")
    assert response.status_code == 200
    assert "generateSitejetRichTextHtml" in response.text
    assert "convertSvgToPngDataUrl" in response.text

def test_frontend_index_has_sitejet_buttons():
    response = client.get("/")
    assert response.status_code == 200
    assert "btnCopySitejet" in response.text
    assert "btnSitejetKit" in response.text
    assert "sitejet-lab.html" in response.text

def test_frontend_index_has_seo_audit_2026_elements():
    response = client.get("/")
    assert response.status_code == 200
    assert "legalQualityScore" in response.text
    assert "combinedScoreBadge" in response.text
    assert "seoAnswerFirstDetected" in response.text
    assert "seoDisclaimerDetected" in response.text
    assert "seoLegalTermsDetected" in response.text
    assert "seoH2QuestionsDetected" in response.text
    assert "btnDeepAudit" in response.text
    assert "seoAuditIssuesContainer" in response.text
    assert "terminalJurisdiction" in response.text

def test_frontend_index_default_seo_ux_configuration():
    response = client.get("/")
    assert response.status_code == 200
    # Tema predeterminado: Derecho Digital (legal_tech)
    assert 'class="theme-pill active" data-theme="legal_tech"' in response.text
    # Tono predeterminado: Abogado VE Doctrinal
    assert '<option value="abogado_ve_doctrinal" selected>' in response.text
    # Longitud predeterminada: 1000 palabras (Pilar SEO)
    assert '<option value="1000" selected>' in response.text
    # Temperatura anti-alucinación: 0.2
    assert 'value="0.2"' in response.text
    assert '0.2 (Rigor Factual)' in response.text
    # Versión de script con cache-busting v=9.5
    assert 'js/app.js?v=9.5' in response.text

def test_frontend_index_has_magazine_mode_elements():
    """Verifica que index.html contenga los controles del modo revista y lectura."""
    response = client.get("/")
    assert response.status_code == 200
    assert "btnToggleColumns" in response.text
    assert "btnReadingMode" in response.text
    assert "editorialMode" in response.text
    assert 'value="magazine"' in response.text

def test_generate_request_editorial_mode_validation():
    """Verifica que el schema Pydantic de GenerateRequest valide editorial_mode."""
    # editorial_mode inválido debe arrojar error de validación 422
    invalid_payload = {
        "source_text": "Texto suficientemente largo para pasar validación mínima de diez caracteres.",
        "editorial_mode": "invalid_mode_not_supported"
    }
    response = client.post("/api/generate-stream", json=invalid_payload)
    assert response.status_code == 422



