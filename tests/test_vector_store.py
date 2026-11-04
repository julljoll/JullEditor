"""
Pruebas unitarias para el subsistema RAG Vectorial e Híbrido de JullEditor v4.0.
Verifica Chunker, Reranker, LegalVectorStore e integración con rag_manager.
"""

from pathlib import Path
from unittest import mock

import pytest
from backend.rag.chunker import LegalChunker, parse_frontmatter
from backend.rag.reranker import HybridReranker, min_max_normalize
from backend.rag.vector_store import LegalVectorStore, tokenize
from backend.rag_manager import retrieve_legal_context


def test_parse_frontmatter():
    text = '---\nnombre_oficial: "Ley de Prueba"\ncategoria: "Informatica"\n---\n# Titulo\nCuerpo de la ley.'
    meta, body = parse_frontmatter(text)
    assert meta.get("nombre_oficial") == "Ley de Prueba"
    assert meta.get("categoria") == "Informatica"
    assert "Cuerpo de la ley" in body


def test_chunker_detects_articles():
    chunker = LegalChunker()
    sample = """
    ###### Articulo 28
    Toda persona tiene derecho a acceder a la información sobre sí misma en registros oficiales.
    ###### Articulo 60
    Toda persona tiene derecho a la protección de su honor, vida privada e intimidad.
    """
    chunks = chunker.chunk_text(sample, source="crbv.md", category="Constitucion", law_name="CRBV")
    assert len(chunks) == 2
    assert chunks[0]["metadata"]["article_number"] == "28"
    assert "información" in chunks[0]["text"]
    assert chunks[1]["metadata"]["article_number"] == "60"
    assert "intimidad" in chunks[1]["text"]


def test_chunker_fallback_on_unstructured_text():
    chunker = LegalChunker(fallback_chunk_size=10, overlap=2)
    sample = "Esta es una exposición de motivos muy extensa sobre una ley de ciberseguridad sin artículos explícitos en su texto inicial."
    chunks = chunker.chunk_text(sample, source="motivos.md", category="Penal")
    assert len(chunks) >= 1
    assert chunks[0]["metadata"]["article_number"] == "N/A"


def test_reranker_normalization_and_order():
    scores = [10.0, 20.0, 30.0]
    norm = min_max_normalize(scores)
    assert norm == [0.0, 0.5, 1.0]

    reranker = HybridReranker(bm25_weight=0.5, semantic_weight=0.5)
    candidates = [
        {"id": 1, "bm25_score": 10.0, "semantic_score": 0.2},
        {"id": 2, "bm25_score": 30.0, "semantic_score": 0.8},
    ]
    ranked = reranker.rerank(candidates, top_k=2)
    assert ranked[0]["id"] == 2
    assert "hybrid_score" in ranked[0]


def test_vector_store_tokenize():
    tokens = tokenize("¿Qué establece la Constitución sobre los Delitos Informáticos?")
    assert "constitucion" in tokens or "constitución" in tokens
    assert "delitos" in tokens
    assert "informaticos" in tokens or "informáticos" in tokens
    assert "de" not in tokens
    assert "la" not in tokens


def test_vector_store_search_returns_relevant_article(tmp_path):
    vs = LegalVectorStore(persist_dir=tmp_path)
    sample_text = """
    ###### Articulo 49
    El debido proceso se aplicará a todas las actuaciones judiciales y administrativas; la defensa es un derecho inviolable.
    ###### Articulo 6
    Acceso indebido. Toda persona que sin la debida autorización acceda a un sistema informático.
    """
    vs.chunks = vs.chunker.chunk_text(sample_text, source="leyes.md", category="Penal", law_name="Código Penal")
    vs._init_bm25()

    results = vs.search("debido proceso y derecho a la defensa", top_k=1)
    assert len(results) == 1
    assert "49" in results[0]["metadata"]["article_number"] or "debido proceso" in results[0]["text"].lower()


def test_vector_store_is_indexed_check(tmp_path):
    vs = LegalVectorStore(persist_dir=tmp_path)
    assert vs.is_indexed() is False
    vs.chunks = [{"text": "texto", "metadata": {}}]
    vs.chunks_file.write_text("[]", encoding="utf-8")
    assert vs.is_indexed() is True


def test_retrieve_legal_context_integration():
    """Verifica que retrieve_legal_context devuelva un corpus legal estructurado y con advertencias."""
    output = retrieve_legal_context("acceso indebido a sistemas y evidencia forense", theme="cybersecurity")
    assert "CORPUS JURÍDICO VENEZOLANO AUTORIZADO" in output
    assert "ADVERTENCIA ESTRICTA CONTRA ALUCINACIÓN DE LEYES" in output
    assert "Delitos Informáticos" in output or "CRBV" in output
