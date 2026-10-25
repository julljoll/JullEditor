from backend.docling_parser import parse_docling_markdown


def test_parse_docling_markdown_with_frontmatter():
    md = """---
title: "Análisis Pericial de Ciberseguridad"
author: "Perito Forense"
---

# Título Principal

Texto de prueba sobre delitos informáticos, evidencia digital y cadena de custodia en Venezuela.
"""
    res = parse_docling_markdown(md, "test_doc.md")
    assert res["status"] == "success"
    assert res["title"] == "Análisis Pericial de Ciberseguridad"
    assert res["detected_theme"] == "cybersecurity"
    assert res["word_count"] > 0
    assert res["frontmatter"]["author"] == "Perito Forense"

def test_parse_docling_empty():
    res = parse_docling_markdown("", "")
    assert res["status"] == "error"
    assert res["word_count"] == 0

def test_parse_docling_json():
    json_str = '{"title": "Inteligencia Artificial y Modelos LLM", "markdown": "Contenido sobre inteligencia artificial, datos y algoritmos en Venezuela."}'
    res = parse_docling_markdown(json_str, "data.json")
    assert res["status"] == "success"
    assert res["title"] == "Inteligencia Artificial y Modelos LLM"
    assert res["detected_theme"] == "ai_data"

def test_parse_docling_cleaning_artifacts():
    md = """# Título Limpio

<!-- image -->
Página 1 de 10
Párrafo con información forense y cibernética.
"""
    res = parse_docling_markdown(md, "doc.md")
    assert "<!-- image -->" not in res["text"]
    assert "Página 1 de 10" not in res["text"]
    assert "Párrafo con información" in res["text"]
