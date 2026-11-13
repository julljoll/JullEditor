"""
Suite de pruebas unitarias y de integración para el exportador Astro Markdown.
Valida la compatibilidad con Astro Framework Content Collections,
la sanitización de slugs, extracción de meta descripciones SEO,
limpieza de cuerpos Markdown y los endpoints API correspondientes.
"""

import os
import re
import pytest
from fastapi.testclient import TestClient

from backend.app import app
import backend.astro_publisher as pub
from backend.exporters.astro_exporter import (
    clean_body_for_astro,
    export_as_astro_md,
    extract_description_from_body,
    extract_tags,
    slugify_astro,
)
from backend.rag_manager import (
    ARTICLES_GENERATED_DIR,
    ASTRO_READY_DIR,
    save_final_article,
)


class TestSlugifyAstro:
    def test_removes_accents_and_diacritics(self):
        slug = slugify_astro("Principio de Intervención Mínima y Casación")
        assert slug == "principio-de-intervencion-minima-y-casacion"

    def test_lowercase_conversion(self):
        slug = slugify_astro("CIBERSEGURIDAD Y HACKING ÉTICO")
        assert slug == "ciberseguridad-y-hacking-etico"

    def test_special_characters_removal(self):
        slug = slugify_astro("Art. 49: CRBV (2026) ¿Cómo Aplica?")
        assert slug == "art-49-crbv-2026-como-aplica"

    def test_length_limit_80_chars(self):
        long_title = "Esta es una oración extremadamente larga diseñada para probar la longitud máxima permitida en el slug de Astro"
        slug = slugify_astro(long_title)
        assert len(slug) <= 80
        assert not slug.endswith("-")

    def test_empty_or_whitespace_fallback(self):
        assert slugify_astro("") == "articulo-blog"
        assert slugify_astro("   ") == "articulo-blog"


class TestExtractDescription:
    def test_extracts_explicit_meta_desc_prefix(self):
        md = "META_DESC: Esta es una descripción explícita de alta calidad SEO.\n\n# Título Real\n\nCuerpo del artículo."
        desc, body = extract_description_from_body(md)
        assert desc == "Esta es una descripción explícita de alta calidad SEO."
        assert "META_DESC:" not in body
        assert "# Título Real" in body

    def test_extracts_blockquote_meta_desc(self):
        md = "# Título\n\n> **Meta descripción:** Analizamos el impacto de la sentencia en Venezuela.\n\n## Sección 1\nContenido."
        desc, body = extract_description_from_body(md)
        assert "Analizamos el impacto de la sentencia en Venezuela." in desc
        assert "Meta descripción:" not in body
        assert "## Sección 1" in body

    def test_extracts_heading_meta_desc(self):
        md = "# Título\n\n## Meta Descripción\n> Explora cómo los modelos de IA transforman la justicia digital.\n\n## Sección Real"
        desc, body = extract_description_from_body(md)
        assert "Explora cómo los modelos de IA" in desc
        assert "Meta Descripción" not in body
        assert "## Sección Real" in body

    def test_extracts_intro_quote(self):
        md = "# Título\n\n> Descubre las ventajas del framework Astro para blogs de alto rendimiento.\n\nTexto de desarrollo."
        desc, body = extract_description_from_body(md)
        assert "Descubre las ventajas del framework Astro" in desc
        assert "> Descubre" not in body

    def test_fallback_first_paragraph(self):
        md = "# Título Principal\n\nEl desarrollo pericial en informática requiere herramientas fiables.\n\nOtro párrafo."
        desc, body = extract_description_from_body(md)
        assert "El desarrollo pericial en informática requiere herramientas fiables." in desc

    def test_empty_text_returns_empty(self):
        desc, body = extract_description_from_body("")
        assert desc == ""
        assert body == ""


class TestCleanBodyForAstro:
    def test_removes_meta_desc_heading(self):
        md = "## Meta Descripción\n> Algo informativo\n\n## Sección Real\nTexto válido."
        cleaned = clean_body_for_astro(md)
        assert "Meta Descripción" not in cleaned
        assert "## Sección Real" in cleaned

    def test_removes_schema_json_from_markdown_body(self):
        md = '## Conclusiones\n\n```json\n{\n  "@context": "https://schema.org",\n  "@type": "TechArticle"\n}\n```\n\nFin.'
        cleaned = clean_body_for_astro(md)
        assert '"@context": "https://schema.org"' not in cleaned
        assert "```json" not in cleaned

    def test_replaces_windows_mojibake(self):
        md = "El cafǸ del perito fue de vanguardia y causǻ impacto."
        cleaned = clean_body_for_astro(md)
        assert "café" in cleaned
        assert "causó" in cleaned


class TestExtractTags:
    def test_default_tags_by_theme(self):
        tags = extract_tags("Texto de prueba", "cybersecurity")
        assert "ciberseguridad" in tags
        assert "venezuela" in tags

    def test_includes_custom_metadata_keywords(self):
        meta = {"keywords": ["inteligencia-artificial", "auditoría"]}
        tags = extract_tags("Texto de prueba", "legal_tech", meta)
        assert "inteligencia-artificial" in tags
        assert "auditoria" in tags or "auditoría" in tags or any("auditor" in t for t in tags)

    def test_extracts_bold_keywords_when_sparse(self):
        content = "El **criptoactivo** soberano y la **cadena de custodia** pericial."
        tags = extract_tags(content, "science_tech", {})
        assert len(tags) >= 2


class TestExportAsAstroMd:
    def test_generates_valid_astro_frontmatter(self):
        title = "Análisis Pericial de Ciberseguridad en Venezuela"
        content = (
            "META_DESC: Guía técnica completa para la recolección de evidencia digital en Venezuela.\n\n"
            "# Análisis Pericial de Ciberseguridad en Venezuela\n\n"
            "> **📌 Resumen:** Procedimientos forenses.\n\n"
            "## ¿Cómo Opera la Cadena de Custodia? {#cadena-custodia}\n\n"
            "La recolección de **evidencia digital** debe respetar el manual único.\n\n"
            '```json\n{"@context": "https://schema.org", "@type": "TechArticle"}\n```'
        )
        metadata = {
            "theme": "cybersecurity",
            "author": "Dr. Perito Forense",
        }
        astro_md = export_as_astro_md(title, content, metadata)

        assert astro_md.startswith("---")
        meta = pub.parse_frontmatter(astro_md)
        assert meta is not None
        assert meta["title"] == title
        assert meta["author"] == "Dr. Perito Forense"
        assert meta["pubDate"]
        assert meta["slug"] == "analisis-pericial-de-ciberseguridad-en-venezuela"
        assert 1 <= len(meta["tags"]) <= 6
        assert meta["category"] in {"Opinión Pericial", "cybersecurity"}
        assert meta["readingTime"] >= 1
        assert meta["draft"] is False
        assert meta["featured"] is False
        assert "# Análisis Pericial de Ciberseguridad en Venezuela" not in astro_md
        assert "<" not in astro_md
        assert "```json" not in astro_md

    def test_slug_in_frontmatter_is_valid_url(self):
        title = "Sentencia N° 123: ¿Es Válida la Prueba Digital en Venezuela?"
        content = "Cuerpo del artículo sobre la sentencia."
        astro_md = export_as_astro_md(title, content, {})
        meta = pub.parse_frontmatter(astro_md)
        assert meta is not None
        slug_val = meta["slug"]
        assert re.match(r"^[a-z0-9-]+$", slug_val)

    def test_rejects_html_body(self):
        with pytest.raises(ValueError, match="Markdown estándar"):
            export_as_astro_md("Artículo legal de prueba", "<div>Texto</div>")

    def test_omits_optional_fields_without_source_values(self):
        article = export_as_astro_md("Artículo legal de prueba", "Texto de análisis.")
        meta = pub.parse_frontmatter(article)
        assert meta is not None
        assert "updatedDate" not in meta
        assert "heroImage" not in meta
        assert "seoKeyword" not in meta


class TestAstroApiEndpoints:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_list_astro_articles_endpoint(self, client):
        response = client.get("/api/export/astro/list")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "articles" in data
        assert isinstance(data["articles"], list)

    def test_save_and_get_astro_article(self, client):
        title = "Prueba de Integración Astro Export 2026"
        content = (
            "META_DESC: Probando la exportación automatizada a Astro.\n\n"
            "# Prueba de Integración Astro Export 2026\n\n"
            "Contenido pericial de prueba."
        )
        # Guardar artículo
        save_res = save_final_article(
            title=title,
            markdown_content=content,
            metadata={"theme": "legal_tech", "tone": "conversational"},
        )
        assert save_res["status"] == "success"
        assert "astro_filename" in save_res

        # Consultar endpoint Astro
        slug = slugify_astro(title)
        res = client.get(f"/api/export/astro/{slug}")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "pubDate:" in data["content"]
        assert "slug:" in data["content"]

        # Consultar endpoint con descarga
        res_dl = client.get(f"/api/export/astro/{slug}?download=true")
        assert res_dl.status_code == 200
        assert "text/markdown" in res_dl.headers.get("content-type", "")
