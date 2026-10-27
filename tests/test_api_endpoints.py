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
    # Versión de script con cache-busting
    assert 'js/app.js?v=' in response.text


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

def test_index_preserves_required_ids():
    """Garantiza que ningún ID del contrato de interfaz JS fue eliminado o renombrado."""
    html = client.get("/").text
    for i in REQUIRED_IDS:
        assert f'id="{i}"' in html, f"Falta id={i}"

def test_index_is_dark_only_and_offline():
    """Verifica meta color-scheme dark, ausencia de CDNs externos y presencia de elementos de live preview."""
    html = client.get("/").text
    assert 'name="color-scheme" content="dark"' in html
    assert "fonts.googleapis.com" not in html
    assert "css/fonts.css" in html
    for i in ["liveStructureList", "btnFollowStream", "livePreviewMarkdown", "livePreviewWp"]:
        assert f'id="{i}"' in html, f"Falta componente live preview id={i}"

def test_new_ui_modules_served():
    """Verifica que los nuevos módulos ES6 sean servidos correctamente por FastAPI."""
    for m in ["live-preview.js", "toolbar-menu.js", "creation-flow.js"]:
        res = client.get(f"/js/modules/{m}")
        assert res.status_code == 200, f"Error cargando módulo {m}"

def test_dark_tokens_in_css():
    """Verifica tokens dark-only y container queries para el modo revista responsive."""
    css = client.get("/css/style.css").text
    assert "color-scheme: dark" in css
    assert "--bg-app" in css
    assert "@container article" in css

def test_frontend_index_has_academic_law_tech_option():
    """Verifica que index.html incluya la opción de Revista Científica Arbitrada y el tema forense."""
    html = client.get("/").text
    assert '<option value="revista_cientifica_law_tech">' in html
    assert 'data-theme="forensic_law"' in html

def test_style_css_has_academic_abstract_and_print_rules():
    """Verifica que style.css contenga las tarjetas académicas y las reglas de impresión @media print."""
    css = client.get("/css/style.css").text
    assert ".academic-abstract-card" in css
    assert "@media print" in css
    assert ".no-print" in css

def test_html_export_modules_contain_inline_styles():
    """Verifica que los módulos de exportación inyecten estilos inline para WordPress y Sitejet."""
    wp_js = client.get("/js/modules/wordpress-exporter.js").text
    assert "btnCopyRawHtml" in wp_js
    assert ".academic-abstract-card" in wp_js
    assert "granite-article-wrapper" in wp_js
    assert "border-collapse" in wp_js

    sj_js = client.get("/js/modules/sitejet-exporter.js").text
    assert ".academic-abstract-card" in sj_js
    assert "border-collapse" in sj_js

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


def test_frontend_ingest_tabs_structure():
    """Verifica que el HTML contenga las 3 opciones de ingesta con sus IDs y atributos correctos."""
    from bs4 import BeautifulSoup
    with open("frontend/index.html", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    tabs = soup.select(".ingest-tab")
    assert len(tabs) == 3, f"Se esperaban 3 pestañas de ingesta, se encontraron {len(tabs)}"
    modes = [t.get("data-mode") for t in tabs]
    assert modes == ["docling", "text", "url"], f"Modos inesperados: {modes}"

    assert soup.select_one("#doclingUploadSection") is not None
    assert soup.select_one("#urlSection") is not None
    assert soup.select_one("#sourceTitle") is not None
    assert soup.select_one("#sourceText") is not None
    assert soup.select_one("#urlInput") is not None
    assert soup.select_one("#btnScrape") is not None
    assert soup.select_one("#fileDoclingInput") is not None
    assert soup.select_one("#doclingDropzone") is not None


def test_javascript_modules_syntax():
    """Verifica que ningún archivo JS tenga errores de sintaxis o variables redeclaradas."""
    import glob
    import subprocess
    js_files = glob.glob("frontend/js/**/*.js", recursive=True) + glob.glob("frontend/js/*.js")
    assert len(js_files) > 5, "Deben existir archivos JavaScript en el frontend"
    for js_path in js_files:
        proc = subprocess.run(["node", "--check", js_path], capture_output=True, text=True)
        assert proc.returncode == 0, f"Error de sintaxis en {js_path}: {proc.stderr}"
