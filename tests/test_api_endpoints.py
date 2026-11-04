# NOTE (Plan Astro 2026): los tests del frontend vanilla (HTML/CSS/JS servido por
# FastAPI, laboratorio Sitejet, WordPress exporter JS e IDs de la UI antigua) fueron
# retirados junto con esa capa. La interfaz ahora es el Studio Astro (studio/) y el
# contrato de exportación se prueba en tests/test_astro_publisher.py.

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

def test_generate_request_editorial_mode_validation():
    """Verifica que el schema Pydantic de GenerateRequest valide editorial_mode."""
    invalid_payload = {
        "source_text": "Texto suficientemente largo para pasar validación mínima de diez caracteres.",
        "editorial_mode": "invalid_mode_not_supported"
    }
    response = client.post("/api/generate-stream", json=invalid_payload)
    assert response.status_code == 422

def test_stop_generation_endpoint():
    """Verifica que el endpoint /api/stop-generation responda con éxito."""
    response = client.post("/api/stop-generation")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "stopped"

REQUIRED_IDS = [
    "tabDocling", "tabText", "tabUrl", "sourceTitle", "sourceText", "toneSelect",
    "wordCountTarget", "editorialMode", "jurisdictionSelect", "modelSelect", "tempSlider",
    "customInstructions", "btnGenerate", "btnStop", "btnCopySitejet", "btnSitejetKit",
    "btnCopyWordPress", "btnCopyRawHtml", "btnCopy", "btnDownloadHtml", "btnPrint", "btnClear",
    "btnToggleColumns", "btnReadingMode", "articleContainer", "articleView",
    "seoScore", "combinedScoreBadge", "previewTitle", "terminalStatus"
]

def test_scraper_parse_html_resilience():
    """Verifica que el parser HTML no descomponga contenedores con clases como no-sidebar o has-sidebar."""
    from backend.scraper import parse_html_to_clean_article
    html = '''
    <html lang="es">
    <head><title>Título de Prueba Scraper</title></head>
    <body class="page-template no-sidebar has-comments">
      <div class="site-main sidebar-layout">
        <article class="entry-content">
          <h1>Análisis Forense y Cadena de Custodia Digital</h1>
          <p>La preservación de evidencia digital exige la fijación del hash SHA-256 desde la adquisición.</p>
          <p>El Manual Único de Cadena de Custodia del Ministerio Público venezolano establece el procedimiento técnico.</p>
        </article>
      </div>
    </body>
    </html>
    '''
    result = parse_html_to_clean_article(html, "https://noticias.example.com/articulo-forense")
    assert result["status"] == "success"
    assert "Análisis Forense" in result["title"]
    assert result["word_count"] > 15
    assert "SHA-256" in result["text"]
    assert "Cadena de Custodia" in result["text"]


