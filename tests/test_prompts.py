"""
Pruebas unitarias para el paquete modular de prompts de JullEditor v4.0.
Verifica la generación de prompts para blog_writer, sentencia_tsj, critic y researcher.
"""

from backend.prompts import (
    build_critic_prompt,
    build_generation_prompt,
    build_researcher_prompt,
    build_sentencia_tsj_prompt,
)
from backend.prompts.base import SYSTEM_BASE_PROMPT, THEMATIC_PROMPTS


def test_build_generation_prompt_structure():
    prompt = build_generation_prompt(
        article_source_text="Texto fuente sobre ciberseguridad forense.",
        source_title="Auditoría Forense en Redes",
        source_url="https://ejemplo.com/articulo",
        theme="cybersecurity",
        tone="jull",
        target_words=1000,
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
        legal_rag_context=legal_ctx,
    )
    assert "Corpus Legal Inyectado: Art. 28 CRBV" in prompt
    assert "Mensajes de Datos" in prompt or "DERECHO DIGITAL" in prompt


def test_build_generation_prompt_optimal_seo_rules():
    """Verifica que el prompt base incorpore mandatos para SEO 2026, Answer-First y descargo ético."""
    prompt = build_generation_prompt(
        article_source_text="Prueba de redacción legaltech.",
        theme="legal_tech",
        tone="abogado_ve_doctrinal",
        target_words=1000,
    )
    assert "40 a 60 palabras" in prompt
    assert "no constituye asesoría legal" in prompt
    assert "AL MENOS EL 50% DE LOS ENCABEZADOS H2 DEBEN ESTAR FORMULADOS COMO PREGUNTAS" in prompt
    assert "PERFIL DE VOZ PROFESIONAL: Abogado Venezolano — Doctrinal" in prompt


def test_build_generation_prompt_magazine_mode():
    """Verifica que el modo revista inyecte el bloque interpretativo y la sección de lectura editorial."""
    prompt = build_generation_prompt(
        article_source_text="Estudio sobre amenazas en la nube.",
        editorial_mode="magazine",
    )
    assert "ENFOQUE EDITORIAL INTERPRETATIVO-EXPLICATIVO (MODO REVISTA DIGITAL 2026)" in prompt
    assert "## 🔎 Nuestra Lectura del Artículo {#nuestra-lectura}" in prompt
    assert "PULL-QUOTE / CITA DESTACADA DE REVISTA" in prompt


def test_build_generation_prompt_classic_mode():
    """Verifica que el modo clásico omita el bloque interpretativo de revista."""
    prompt = build_generation_prompt(
        article_source_text="Estudio sobre amenazas en la nube.",
        editorial_mode="classic",
    )
    assert "ENFOQUE EDITORIAL INTERPRETATIVO-EXPLICATIVO (MODO REVISTA DIGITAL 2026)" not in prompt
    assert "7b. (MODO REVISTA OBLIGATORIO)" not in prompt


def test_build_generation_prompt_academic_review_structure():
    """Verifica que el tono académico universitario inyecte abstract bilingüe y ScholarlyArticle."""
    prompt = build_generation_prompt(
        article_source_text="Investigación sobre evidencia digital y hash SHA-256.",
        theme="cybersecurity",
        tone="revista_cientifica_law_tech",
        target_words=1800,
    )
    assert "DIRECTRICES ESPECÍFICAS DE REVISTA CIENTÍFICA ARBITRADA" in prompt
    assert "RESUMEN ESTRUCTURADO (ABSTRACT)" in prompt
    assert "ScholarlyArticle" in prompt
    assert "ISO/IEC 27037" in prompt


def test_build_sentencia_tsj_prompt_basic():
    """Verifica que el prompt de sentencias TSJ incluya la ficha técnica y principios de inmutabilidad."""
    sample_text = "La Sala de Casación Penal del TSJ dicta sentencia en expediente AA30-P-2024-000123."
    prompt = build_sentencia_tsj_prompt(
        article_source_text=sample_text,
        source_title="Sentencia Penal TSJ",
        target_words=1200,
    )
    assert "Analista Jurisprudencial Senior" in prompt
    assert "Ficha Técnica de la Sentencia" in prompt
    assert "INMUTABILIDAD DEL DISPOSITIVO" in prompt
    assert "Tribunal Supremo de Justicia" in prompt
    assert len(prompt) > 500


def test_build_sentencia_tsj_prompt_with_custom_metadata():
    """Verifica que los metadatos suministrados se inyecten fielmente en el prompt TSJ."""
    custom_meta = {
        "sala": "Sala Constitucional",
        "numero_sentencia": 999,
        "expediente": "24-0555",
        "ponente": "Dra. Gladys Gutiérrez",
        "fecha_decision": "15 de mayo de 2025",
        "decision_tipo": "Con Lugar",
        "caracter_vinculante": True,
    }
    prompt = build_sentencia_tsj_prompt(
        article_source_text="Texto breve de recurso de amparo.",
        source_title="Amparo Constitucional",
        sentencia_metadata=custom_meta,
        target_words=1500,
    )
    assert "Sala Constitucional" in prompt
    assert "999" in prompt
    assert "24-0555" in prompt
    assert "Dra. Gladys Gutiérrez" in prompt
    assert "Criterio Vinculante Art. 335 CRBV" in prompt


def test_build_critic_prompt():
    """Verifica que el prompt del agente crítico contenga las instrucciones de auditoría y formato JSON."""
    dossier = "Dossier verificado: Autor Juan Pérez, fecha 2026-05-10, norma Art. 60 CRBV."
    draft = "# Ciberseguridad\n\nArtículo sobre privacidad y datos..."
    prompt = build_critic_prompt(
        draft_article=draft,
        source_dossier=dossier,
        target_jurisdiction="ve",
    )
    assert "Auditor Legal Pericial Senior" in prompt
    assert "Dossier verificado: Autor Juan Pérez" in prompt
    assert "JURISDICCIÓN OBJETIVO: VE" in prompt
    assert '"score": Número de 0 a 100' in prompt
    assert '"hallucinations"' in prompt


def test_build_researcher_prompt():
    """Verifica que el prompt del agente investigador contenga instrucciones de extracción documental."""
    raw_text = "El malware LockBit 3.0 infectó 50 servidores corporativos en febrero de 2026."
    rag_ctx = "Ley Especial contra los Delitos Informáticos: Art. 6 (Acceso indebido)."
    prompt = build_researcher_prompt(
        raw_source_text=raw_text,
        rag_context=rag_ctx,
        theme="cybersecurity",
    )
    assert "Investigador Documental" in prompt
    assert "TEMÁTICA: cybersecurity" in prompt
    assert "LockBit 3.0" in prompt
    assert "Art. 6 (Acceso indebido)" in prompt
    assert "Dossier Fáctico Estructurado" in prompt


def test_package_exports():
    """Verifica que las constantes y diccionarios base sigan accesibles."""
    assert len(SYSTEM_BASE_PROMPT) > 100
    assert "cybersecurity" in THEMATIC_PROMPTS
    assert "legal_tech" in THEMATIC_PROMPTS
