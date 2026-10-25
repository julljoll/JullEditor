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

def test_build_generation_prompt_optimal_seo_rules():
    """Verifica que el prompt base incorpore mandatos para SEO 2026, Answer-First y descargo ético."""
    prompt = build_generation_prompt(
        article_source_text="Prueba de redacción legaltech.",
        theme="legal_tech",
        tone="abogado_ve_doctrinal",
        target_words=1000
    )
    assert "40 a 60 palabras" in prompt
    assert "no constituye asesoría legal" in prompt
    assert "AL MENOS EL 50% DE LOS ENCABEZADOS H2 DEBEN ESTAR FORMULADOS COMO PREGUNTAS" in prompt
    assert "PERFIL DE VOZ PROFESIONAL: Abogado Venezolano — Doctrinal" in prompt

def test_build_generation_prompt_magazine_mode():
    """Verifica que el modo revista inyecte el bloque interpretativo y la sección de lectura editorial."""
    prompt = build_generation_prompt(
        article_source_text="Estudio sobre amenazas en la nube.",
        editorial_mode="magazine"
    )
    assert "ENFOQUE EDITORIAL INTERPRETATIVO-EXPLICATIVO (MODO REVISTA DIGITAL 2026)" in prompt
    assert "## 🔎 Nuestra Lectura del Artículo {#nuestra-lectura}" in prompt
    assert "PULL-QUOTE / CITA DESTACADA DE REVISTA" in prompt

def test_build_generation_prompt_classic_mode():
    """Verifica que el modo clásico omita el bloque interpretativo de revista."""
    prompt = build_generation_prompt(
        article_source_text="Estudio sobre amenazas en la nube.",
        editorial_mode="classic"
    )
    assert "ENFOQUE EDITORIAL INTERPRETATIVO-EXPLICATIVO (MODO REVISTA DIGITAL 2026)" not in prompt
    assert "7b. (MODO REVISTA OBLIGATORIO)" not in prompt
