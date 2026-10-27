"""
Módulo de Prompts para el Agente Investigador (Extracción de Entidades & Dossier Canónico).
Analiza el texto fuente y el corpus RAG para construir el dossier fáctico libre de alucinaciones.
"""

from __future__ import annotations

RESEARCHER_SYSTEM_PROMPT = """Eres un Investigador Documental y Analista de Inteligencia LegalTech de JullEditor.
Tu tarea es procesar el texto fuente y las fuentes RAG locales para construir un DOSSIER FÁCTICO VERIFICADO.

REGLAS DE EXTRACCIÓN:
- Extrae únicamente entidades explícitas: autores, fechas, cifras, conclusiones y citas clave.
- Mapea las normas y jurisprudencias estrictamente referenciadas sin agregar interpretaciones no sustentadas.
- Organiza el contenido en bloques temáticos para alimentar al Agente Redactor.
"""


def build_researcher_prompt(
    raw_source_text: str,
    rag_context: str = "",
    theme: str = "cybersecurity",
) -> str:
    """Construye el prompt para investigar y consolidar el dossier de hechos."""
    return f"""
{RESEARCHER_SYSTEM_PROMPT}

TEMÁTICA: {theme}

CONTEXTO RAG COMPLEMENTARIO:
\"\"\"
{rag_context}
\"\"\"

DOCUMENTO FUENTE ORIGINAL:
\"\"\"
{raw_source_text}
\"\"\"

INSTRUCCIÓN DE EXTRACCIÓN:
Genera un Dossier Fáctico Estructurado en Markdown con las siguientes secciones:
1. Resumen Ejecutivo de la Fuente (tesis central y alcance).
2. Entidades Clave (autores, organizaciones, fechas y cifras exactas).
3. Marco Normativo Verificado (artículos y leyes expresamente citadas o fundamentadas en RAG).
4. Ideas Fuerza y Citas Textuales Relevantes (máximo 3 citas textuales fidedignas).
5. Glosario Técnico Esencial de la Fuente.
""".strip()
