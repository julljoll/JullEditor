import os

from backend.rag_manager import (
    load_legal_corpus,
    retrieve_legal_context,
    sanitize_filename,
    save_final_article,
    save_rag_source,
)


def test_sanitize_filename():
    assert sanitize_filename("Regulación de IA en Venezuela!") == "regulacion_de_ia_en_venezuela"
    assert sanitize_filename("Título con Árboles y Ñandúes") == "titulo_con_arboles_y_nandues"
    assert sanitize_filename("") == "documento_sin_titulo"

def test_load_legal_corpus():
    corpus = load_legal_corpus()
    assert isinstance(corpus, list)
    assert len(corpus) >= 5
    areas = [b["area"] for b in corpus]
    assert any("Constitucional" in a for a in areas)
    assert any("Ciberseguridad" in a for a in areas)

def test_retrieve_legal_context_zero_hallucination():
    context = retrieve_legal_context("acceso indebido a servidores y datos personales", theme="cybersecurity")
    assert "CORPUS JURÍDICO VENEZOLANO" in context
    assert "Ley Especial contra los Delitos Informáticos" in context
    assert "ADVERTENCIA ESTRICTA CONTRA ALUCINACIÓN" in context
    assert "NO EXISTE una 'Ley Orgánica de Protección de Datos Personales'" in context

def test_save_and_list_rag_source():
    res = save_rag_source("prueba_test.md", "# Contenido de Prueba")
    assert res["status"] == "success"
    assert os.path.exists(res["absolute_path"])
    # Cleanup
    if os.path.exists(res["absolute_path"]):
        os.remove(res["absolute_path"])

def test_save_final_article_with_yaml():
    md = "# Artículo de Prueba\n\nTexto de desarrollo del artículo."
    res = save_final_article("Artículo de Prueba", md, {"theme": "legal_tech", "model": "granite3.3:8b"})
    assert res["status"] == "success"
    assert os.path.exists(res["absolute_path"])
    assert "html_filename" in res
    assert os.path.exists(res["absolute_html_path"])
    assert res["filename"] == "Artículo de Prueba.md"
    assert res["html_filename"] == "Artículo de Prueba.html"
    
    with open(res["absolute_path"], encoding="utf-8") as f:
        saved_content = f.read()
    assert saved_content.startswith("---")
    assert "theme: \"legal_tech\"" in saved_content
    assert "word_count:" in saved_content
    
    # Cleanup
    if os.path.exists(res["absolute_path"]):
        os.remove(res["absolute_path"])
    if os.path.exists(res["absolute_html_path"]):
        os.remove(res["absolute_html_path"])


def test_save_article_both_md_and_html_named_after_title():
    """
    Verifica que cada artículo se guarde en 'Articulos Generados/' en ambos formatos (.md y .html)
    utilizando directamente el nombre del título (sin prefijo de fecha forzado).
    """
    from backend.rag_manager import sanitize_title_to_filename

    title = "Ciberseguridad y Delitos Informáticos en Venezuela: Análisis Pericial"
    md_content = """# Ciberseguridad y Delitos Informáticos en Venezuela: Análisis Pericial

> **Meta descripción:** Análisis pericial sobre ciberseguridad y delitos informáticos en Venezuela.

> **⚡ Resumen Ejecutivo en 30 Segundos:**
> Principios forenses para el tratamiento de evidencia digital y delitos informáticos.

## Evidencia Digital y Cadena de Custodia

La cadena de custodia es **esencial** para la admisibilidad judicial.

**Conclusión del párrafo:** El cumplimiento estricto de la ISO 27037 previene nulidades.
"""
    clean_title = sanitize_title_to_filename(title)
    assert clean_title == "Ciberseguridad y Delitos Informáticos en Venezuela - Análisis Pericial"

    res = save_final_article(title, md_content, {"theme": "cybersecurity", "tone": "analista_tsj_revista"})
    assert res["status"] == "success"
    assert res["filename"] == f"{clean_title}.md"
    assert res["html_filename"] == f"{clean_title}.html"
    assert "Articulos Generados" in res["path"]

    md_path = res["absolute_path"]
    html_path = res["absolute_html_path"]
    assert os.path.exists(md_path), f"El archivo .md debe existir en: {md_path}"
    assert os.path.exists(html_path), f"El archivo .html debe existir en: {html_path}"

    # Validar contenido HTML
    with open(html_path, encoding="utf-8") as f:
        html_text = f.read()
    assert "<!DOCTYPE html>" in html_text
    assert f"<title>{title}</title>" in html_text
    assert "<h1>" in html_text
    assert "callout-exec" in html_text
    assert "takeaway" in html_text

    # Cleanup
    if os.path.exists(md_path):
        os.remove(md_path)
    if os.path.exists(html_path):
        os.remove(html_path)

