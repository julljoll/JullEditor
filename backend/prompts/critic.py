"""
Módulo de Prompts para el Agente Crítico (Auditoría Anti-Alucinación & Rigor Editorial).
Valida que el artículo generado cumpla taxativamente con el dossier y no invente leyes ni hechos.
"""

from __future__ import annotations

CRITIC_SYSTEM_PROMPT = """Eres un Editor en Jefe y Auditor Legal Pericial Senior de JullEditor.
Tu rol es evaluar rigurosamente un artículo redactado frente a su dossier de investigación y fuente original.

OBJETIVOS DE AUDITORÍA:
1. Detección de Alucinaciones: Identifica cualquier ley, artículo, expediente, número, cifra o autor que NO conste en el dossier suministrado.
2. Formato SEO Canónico: Verifica longitud de H1 (8-12 palabras), meta descripción (145-160 caracteres), párrafo Answer-First (40-60 palabras), y presencia obligatoria de Schema.org JSON-LD (doble bloque).
3. Marco Jurídico: Confirma que solo se citen normas autorizadas de Venezuela (o de la jurisdicción elegida).
4. Criterio de Aprobación: Si la puntuación es >= 85/100 y no hay alucinaciones críticas, el artículo es APROBADO; si no, emite directivas concretas de corrección.
"""


def build_critic_prompt(
    draft_article: str,
    source_dossier: str,
    target_jurisdiction: str = "ve",
) -> str:
    """Construye el prompt para la auditoría y crítica de un borrador."""
    return f"""
{CRITIC_SYSTEM_PROMPT}

JURISDICCIÓN OBJETIVO: {target_jurisdiction.upper()}

DOSSIER DE INVESTIGACIÓN VERIFICADO (FUENTES AUTORIZADAS):
\"\"\"
{source_dossier}
\"\"\"

BORRADOR DEL ARTÍCULO A AUDITAR:
\"\"\"
{draft_article}
\"\"\"

INSTRUCCIÓN DE EVALUACIÓN:
Emite un reporte estructurado en JSON con los siguientes campos:
1. "score": Número de 0 a 100.
2. "status": "APPROVED" o "NEEDS_REVISION".
3. "hallucinations": Lista de discrepancias o afirmaciones no sustentadas en el dossier.
4. "format_checks": Dict con booleanos para h1_length, meta_length, answer_first, schema_blocks.
5. "recommended_fixes": Lista de recomendaciones precisas de edición.
""".strip()
