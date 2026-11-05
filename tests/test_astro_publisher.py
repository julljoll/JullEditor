"""
Tests del publicador Astro (Fase 1/4 del plan):
- Contrato frontmatter ↔ esquema del blog.
- /api/export/publish: copiado, idempotencia, rechazo de inválidos y path traversal.
- /api/export/drafts: estados de publicación.
"""

import os

import pytest
from fastapi.testclient import TestClient

import backend.astro_publisher as pub
from backend.app import app
from backend.exporters.astro_exporter import export_as_astro_md
from backend.rag_manager import ASTRO_READY_DIR

client = TestClient(app)

VALID_MD = """---
title: "Artículo de Prueba para el Blog Astro"
description: "Descripción de prueba dentro del límite de ciento sesenta caracteres permitidos."
pubDate: 2026-11-05
updatedDate: 2026-11-05
author: "Jull Editor"
slug: "articulo-de-prueba"
tags: ["ciberseguridad", "pruebas"]
category: "cybersecurity"
heroImage: ""
seoKeyword: "ciberseguridad"
readingTime: 3
featured: false
draft: false
---

# Artículo de Prueba

Contenido de prueba con **negritas** y párrafos suficientes.
"""


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Directorios astro_ready y blog temporales para aislar el sistema de archivos."""
    ready = tmp_path / "astro_ready"
    ready.mkdir()
    blog = tmp_path / "blog"
    (blog / "src" / "content" / "blog").mkdir(parents=True)
    monkeypatch.setattr(pub, "ASTRO_READY_DIR", str(ready))
    monkeypatch.setattr(pub, "BLOG_DIR", str(blog))
    monkeypatch.setattr(pub, "BLOG_CONTENT_DIR", str(blog / "src" / "content" / "blog"))
    monkeypatch.setattr(pub, "BLOG_IMAGES_DIR", str(blog / "public" / "images" / "articles"))
    return ready, blog


def _write_draft(ready_dir, slug, content=VALID_MD):
    p = os.path.join(str(ready_dir), f"{slug}.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p


class TestFrontmatterContract:
    def test_valid_frontmatter_parses(self):
        meta = pub.parse_frontmatter(VALID_MD)
        assert meta is not None
        assert meta["title"].startswith("Artículo")
        assert isinstance(meta["tags"], list)
        assert pub.validate_frontmatter(meta) == []

    def test_missing_required_fields_detected(self):
        bad = "---\ntitle: 'Solo título'\n---\n\nCuerpo.\n"
        meta = pub.parse_frontmatter(bad)
        errors = pub.validate_frontmatter(meta)
        assert any("description" in e for e in errors)
        assert any("pubDate" in e for e in errors)

    def test_long_description_rejected(self):
        meta = pub.parse_frontmatter(VALID_MD)
        meta["description"] = "x" * 200
        assert any("170" in e for e in pub.validate_frontmatter(meta))

    def test_exporter_output_matches_contract(self):
        """Contrato: todo lo que emite export_as_astro_md debe validar en el blog."""
        article = "# Guía de Cadena de Custodia Digital\n\n> **Meta descripción:** Explora la cadena de custodia digital según el marco legal venezolano.\n\n## Introducción\nLa evidencia digital requiere hash SHA-256."
        out = export_as_astro_md(
            title="Guía de Cadena de Custodia Digital",
            markdown_content=article,
            metadata={"theme": "forensic_law"},
            editorial_layout=False,
        )
        meta = pub.parse_frontmatter(out)
        assert meta is not None, "El exporter no emite frontmatter YAML válido"
        assert pub.validate_frontmatter(meta) == []


class TestPublishFlow:
    def test_publish_creates_file(self, sandbox):
        ready, blog = sandbox
        _write_draft(ready, "articulo-de-prueba")
        res = pub.publish_article("articulo-de-prueba")
        assert res["status"] == "success"
        assert res["action"] == "created"
        dest = os.path.join(str(blog), "src", "content", "blog", "articulo-de-prueba.md")
        assert os.path.isfile(dest)

    def test_publish_is_idempotent(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "articulo-de-prueba")
        first = pub.publish_article("articulo-de-prueba")
        second = pub.publish_article("articulo-de-prueba")
        assert first["status"] == "success"
        assert second["action"] == "unchanged"

    def test_publish_updates_when_changed(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "articulo-de-prueba")
        pub.publish_article("articulo-de-prueba")
        _write_draft(ready, "articulo-de-prueba", content=VALID_MD + "\nEdición nueva.\n")
        res = pub.publish_article("articulo-de-prueba")
        assert res["action"] == "updated"

    def test_publish_rejects_invalid_frontmatter(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "malo", content='---\ntitle: "Sin campos"\n---\n\nCuerpo.\n')
        res = pub.publish_article("malo")
        assert res["status"] == "error"
        assert res.get("errors")

    def test_path_traversal_blocked(self, sandbox):
        _, blog = sandbox
        secret = os.path.join(str(blog.parent), "evil.md")
        with open(secret, "w") as f:
            f.write("---\ntitle: x\n---\n")
        res = pub.publish_article("../../evil")
        assert res["status"] == "error"

    def test_unknown_slug_errors(self, sandbox):
        res = pub.publish_article("no-existe")
        assert res["status"] == "error"

    def test_publication_status_states(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "uno")
        _write_draft(ready, "dos")
        pub.publish_article("uno")
        statuses = {d["slug"]: d["state"] for d in pub.get_publication_status()}
        assert statuses["uno"] == "synced"
        assert statuses["dos"] == "unpublished"


class TestApiEndpoints:
    def test_publish_endpoint_success(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "articulo-de-prueba")
        res = client.post("/api/export/publish", json={"slug": "articulo-de-prueba"})
        assert res.status_code == 200
        assert res.json()["status"] == "success"

    def test_publish_endpoint_rejects_invalid(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "malo", content='---\ntitle: "Sin campos"\n---\n\nCuerpo.\n')
        res = client.post("/api/export/publish", json={"slug": "malo"})
        assert res.status_code == 400

    def test_drafts_endpoint_lists_states(self, sandbox):
        ready, _ = sandbox
        _write_draft(ready, "uno")
        res = client.get("/api/export/drafts")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert any(d["slug"] == "uno" for d in data["drafts"])

    def test_root_is_api_info_not_vanilla_html(self):
        res = client.get("/")
        assert res.status_code == 200
        body = res.json()
        assert body["app"] == "JullEditor API"
        assert "studio" in body
