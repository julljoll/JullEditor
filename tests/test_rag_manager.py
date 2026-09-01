import os
import pytest
from backend.rag_manager import (
    sanitize_filename,
    save_rag_source,
    save_final_article,
    retrieve_legal_context,
    load_legal_corpus,
    list_articles_history
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
    
    with open(res["absolute_path"], "r", encoding="utf-8") as f:
        saved_content = f.read()
    assert saved_content.startswith("---")
    assert "theme: \"legal_tech\"" in saved_content
    assert "word_count:" in saved_content
    
    # Cleanup
    if os.path.exists(res["absolute_path"]):
        os.remove(res["absolute_path"])
