"""
CATÁLOGO EDITORIAL UNIFICADO — Fuente única de verdad (100% Python).

Este módulo centraliza TODOS los menús y opciones del flujo editorial de
JullEditor (espejo exacto de los selects de frontend/index.html):
especialidad temática, estilo editorial, voces/tonos VE, jurisdicciones,
modelos Granite y extensiones objetivo. Lo consumen:

  * backend/cli_generator.py  -> asistente interactivo del .bat (modo texto)
  * backend/tui_app.py        -> interfaz TUI Textual (interfaz canónica v3.3+)
  * backend/app.py            -> validación de payloads de la API web

Principio rector del PLAN_OPTIMIZACION.md (Fase 1): ninguna opción vive en
otro lenguaje; JS solo presenta lo que Python define aquí.
"""


# ---------------------------------------------------------------------------
# PASO 2 — Especialidad temática (radio-group "themeGroup" de index.html)
# ---------------------------------------------------------------------------
THEMES: list[tuple[str, str, str]] = [
    ("sentencia_tsj", "🏛️", "Sentencia TSJ / Forense & Jurisprudencia"),
    ("legal_tech", "⚖️", "Derecho Digital & LegalTech"),
    ("cybersecurity", "🛡️", "Ciberseguridad & Evidencia Informática"),
    ("ai_data", "🧠", "Inteligencia Artificial & Datos"),
    ("science_tech", "🔬", "Ciencia & Tecnología"),
]

# ---------------------------------------------------------------------------
# PASO 3 — Estilo editorial (botones segmentados Magazine/Clásico)
# ---------------------------------------------------------------------------
EDITORIAL_MODES: list[tuple[str, str]] = [
    ("magazine", "📰 Revista Digital (3 Col. Interpretativo-Explicativo 2026)"),
    ("classic", "📝 Resumen Clásico Fiel (Síntesis Directa)"),
]

# ---------------------------------------------------------------------------
# PASO 4 — Perfiles de voz / tono (select "toneSelect", Venezuela exclusiva
# en la UX; el motor conserva jurisdicciones latentes sin exponerlas)
# ---------------------------------------------------------------------------
TONES: list[tuple[str, str]] = [
    # -- Jurídicos Venezuela --
    ("analista_tsj_revista", "📰 Analista Jurisprudencial TSJ — Revista Digital Educativa"),
    ("revista_cientifica_law_tech", "🎓 Revista Científica Arbitrada (Derecho & Computación Forense)"),
    ("abogado_ve_doctrinal", "⚖️ Abogado VE — Doctrinal (Forense / TSJ · Recomendado 2026)"),
    ("abogado_ve_litigante", "⚖️ Abogado VE — Litigante (Ruta Procesal / Lapsos)"),
    ("abogado_ve_explicativo", "⚖️ Abogado VE — Explicativo (Claro / Divulgación)"),
    ("jull", "👤 Jull (Venezolano Técnico-Científico)"),
    ("jull_explicativo", "👤 Jull (Venezolano Explicativo)"),
    # -- Genéricos --
    ("consultor_corporativo", "🏢 Consultor Jurídico Corporativo (Compliance / Riesgos)"),
    ("conversational", "💬 Conversacional Ágil"),
    ("analytical", "🔬 Analítico Pericial"),
    ("didactic", "📚 Didáctico / Pedagógico"),
    ("executive", "💼 Ejecutivo / Directivo"),
]

DEFAULT_TONE = "analista_tsj_revista"

# ---------------------------------------------------------------------------
# PASO 5 — Jurisdicción (select "jurisdictionSelect": Venezuela exclusiva)
# ---------------------------------------------------------------------------
JURISDICTIONS: list[tuple[str, str]] = [
    ("auto", "🔄 Auto (Detectar por fuente y notas · Enfoque Venezuela)"),
    ("venezuela", "🇻🇪 Venezuela (CRBV, Delitos Informáticos, Infogobierno, TSJ)"),
    ("international", "🌐 Internacional / Global (ISO, NIST, UE)"),
]

DEFAULT_JURISDICTION = "auto"

# ---------------------------------------------------------------------------
# PASO 6 — Parámetros técnicos de inferencia (Ajustes Avanzados)
# ---------------------------------------------------------------------------
MODELS: list[tuple[str, str]] = [
    ("granite3.3:8b", "IBM Granite 3.3 8B (Recomendado 16GB RAM)"),
    ("granite3.3:2b", "IBM Granite 3.3 2B (Rápido · CPU baja RAM)"),
]

WORD_COUNT_TARGETS: list[tuple[int, str]] = [
    (600, "~600 palabras (Corto / Nota rápida)"),
    (1000, "~1000 palabras (Pilar SEO 2026 · Recomendado)"),
    (1500, "~1500 palabras (Largo / Análisis profundo)"),
    (2000, "~2000 palabras (Pilar Extenso / Revista)"),
]

DEFAULT_TEMPERATURE = 0.0      # Cero alucinación / rigor factual TSJ
TEMPERATURE_RANGE: tuple[float, float] = (0.0, 1.0)
DEFAULT_MODEL = "granite3.3:8b"
DEFAULT_WORD_COUNT = 1000


def theme_options() -> list[str]:
    return [f"{icon} {label}" for _code, icon, label in THEMES]


def tone_options() -> list[str]:
    return [label for _code, label in TONES]


def jurisdiction_options() -> list[str]:
    return [label for _code, label in JURISDICTIONS]


def theme_codes() -> list[str]:
    return [code for code, _icon, _label in THEMES]


def tone_codes() -> list[str]:
    return [code for code, _label in TONES]


def jurisdiction_codes() -> list[str]:
    return [code for code, _label in JURISDICTIONS]


def validate_config(config: dict[str, object]) -> list[str]:
    """Devuelve la lista de errores de un dict de configuración editorial.

    Vacía == configuración válida. Compartida por CLI, TUI y API para
    garantizar paridad 1:1 entre todas las interfaces.
    """
    errors: list[str] = []
    if config.get("theme") not in theme_codes():
        errors.append(f"Tema inválido: {config.get('theme')!r}")
    if config.get("editorial_mode") not in ("magazine", "classic"):
        errors.append(f"Estilo editorial inválido: {config.get('editorial_mode')!r}")
    if config.get("tone") not in tone_codes():
        errors.append(f"Tono inválido: {config.get('tone')!r}")
    if config.get("jurisdiction") not in jurisdiction_codes():
        errors.append(f"Jurisdicción inválida: {config.get('jurisdiction')!r}")
    temp = config.get("temperature")
    if not isinstance(temp, (int, float)) or not (TEMPERATURE_RANGE[0] <= temp <= TEMPERATURE_RANGE[1]):
        errors.append(f"Temperatura fuera de rango: {temp!r}")
    if config.get("model") not in [m for m, _l in MODELS]:
        errors.append(f"Modelo no soportado: {config.get('model')!r}")
    words = config.get("target_words")
    if words not in [w for w, _l in WORD_COUNT_TARGETS]:
        errors.append(f"Extensión no soportada: {words!r}")
    ci = config.get("custom_instructions", "")
    if not isinstance(ci, str):
        errors.append("Instrucciones personalizadas deben ser texto")
    return errors
