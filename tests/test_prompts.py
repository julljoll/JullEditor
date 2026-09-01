import pytest
from backend.prompts import build_generation_prompt

def test_build_generation_prompt_structure():
    prompt = build_generation_prompt(
        article_source_text="Texto fuente sobre ciberseguridad forense.",
        source_title="Auditoría Forense en Redes",
        source_url="https://ejemplo.com/articulo",
        theme="cybersecurity",
        tone="jull",
        target_words=1000
    )
    assert "OBJETIVO PRINCIPAL DE REDACCIÓN:" in prompt
    assert "FORMATO MARKDOWN ESTÁNDAR" in prompt
    assert "DIRECTRICES ESPECÍFICAS DE ESTRUCTURA Y TONO JULL" in prompt
    assert "Auditoría Forense en Redes" in prompt
    assert "Texto fuente sobre ciberseguridad forense." in prompt
    assert "https://ejemplo.com/articulo" in prompt
    assert "TechArticle" in prompt
    assert "FAQPage" in prompt

def test_build_generation_prompt_with_legal_context():
    legal_ctx = "Corpus Legal Inyectado: Art. 28 CRBV"
    prompt = build_generation_prompt(
        article_source_text="Texto de prueba legal.",
        theme="legal_tech",
        tone="conversational",
        legal_rag_context=legal_ctx
    )
    assert "Corpus Legal Inyectado: Art. 28 CRBV" in prompt
    assert "Mensajes de Datos" in prompt or "DERECHO DIGITAL" in prompt
