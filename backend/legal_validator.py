"""
Validador de calidad jurídica y SEO/GEO 2026 para artículos de abogado (VE/CO).
Complementa a seo_validator.py con reglas de exactitud, léxico, ética y E-E-A-T.
"""

import re
from typing import Dict, Any, List

from backend.legal_profiles import (
    GLOSSARY,
    ANTI_CALCO,
    PROMISE_PATTERNS,
    FOREIGN_MARKERS,
    DISCLAIMER_PATTERN,
)

_WORD = re.compile(r"\w+", re.UNICODE)


def _first_block_after_h1(markdown: str) -> str:
    """Primer párrafo de prosa tras el H1 (omite meta, callouts, badges y encabezados)."""
    clean_md = re.sub(r"^---[\s\S]*?---\s*", "", markdown or "")
    lines = clean_md.splitlines()
    seen_h1 = False
    for line in lines:
        s = line.strip()
        if not seen_h1:
            if s.startswith("# ") or re.match(r"^#{1,3}\s*(?:\*{0,2}T[ií]tulo(?:\s*H1)?:\s*)", s, re.IGNORECASE):
                seen_h1 = True
            continue
        if not s or s.startswith(("#", ">", "|", "-", "*", "<", "`", "!", "[")) or s.startswith("**") or re.search(r"Meta Descripci[oó]n", s, re.I):
            continue
        return re.sub(r"[*_`\[\]()]", "", s).strip()
    return ""


def audit_legal_quality(markdown: str, jurisdiction: str = "ve") -> Dict[str, Any]:
    """Audita un artículo. Devuelve score 0-100, incidencias y métricas."""
    j = jurisdiction if jurisdiction in ("ve", "co") else "intl"
    text = markdown or ""
    low = text.lower()
    issues: List[Dict[str, str]] = []
    penalty = 0

    # 1. Léxico de glosario del país
    term_hits = 0
    if j in GLOSSARY:
        for entry in GLOSSARY[j]:
            base = re.sub(r"\s*\(.*?\)", "", entry["term"]).lower()
            alternatives = [a.strip() for a in base.split("/")]
            if any(a and a in low for a in alternatives):
                term_hits += 1
        if term_hits < 8:
            issues.append({"level": "warning", "rule": "lexico", "message": f"Solo {term_hits} términos jurídicos del glosario ({j.upper()}); se recomiendan ≥ 8."})
            penalty += min(15, (8 - term_hits) * 2)

    # 2. Calcos
    for c in ANTI_CALCO:
        if re.search(c["bad"], text, re.I):
            issues.append({"level": "warning", "rule": "calco", "message": f"Calco detectado: «{c['bad'].replace(chr(92), '')}». Preferir: {c['good']}."})
            penalty += 3

    # 3. Promesas de resultado (ética del abogado)
    for p in PROMISE_PATTERNS:
        m = re.search(p, text, re.I)
        if m:
            issues.append({"level": "error", "rule": "etica", "message": f"Promesa de resultado no permitida: «{m.group(0)}»."})
            penalty += 10

    # 4. Descargo legal
    if not DISCLAIMER_PATTERN.search(text):
        issues.append({"level": "error", "rule": "descargo", "message": "Falta el descargo: «no constituye asesoría legal»."})
        penalty += 10

    # 5. Contaminación jurisdiccional
    for pattern in FOREIGN_MARKERS.get(j, []):
        m = re.search(pattern, text)
        if m:
            issues.append({"level": "warning", "rule": "jurisdiccion", "message": f"Mención de otra jurisdicción: «{m.group(0)}»."})
            penalty += 5

    # 6. Respuesta directa 40-60 palabras (GEO)
    answer = _first_block_after_h1(text)
    answer_words = len(_WORD.findall(answer))
    if answer_words and not (40 <= answer_words <= 70):
        issues.append({"level": "warning", "rule": "respuesta_directa", "message": f"El primer párrafo tiene {answer_words} palabras; la respuesta directa ideal es de 40 a 60."})
        penalty += 4
    elif not answer_words:
        issues.append({"level": "warning", "rule": "respuesta_directa", "message": "No se detectó un párrafo de respuesta directa tras el H1."})
        penalty += 4

    # 7. H2 como pregunta (≥ 50 %)
    h2s = re.findall(r"^##\s+(.+)$", text, re.M)
    if not h2s:
        # Fallback si el modelo pequeño usó ### para las secciones
        h2s = re.findall(r"^###\s+(?!T[ií]tulo)(.+)$", text, re.M)
    if h2s:
        question_h2 = sum(1 for h in h2s if "?" in h or h.lower().startswith(("qué", "que ", "cómo", "como ", "cuándo", "cuando", "cuál", "cual", "por qué", "quién", "dónde")))
        ratio = question_h2 / len(h2s)
        if ratio < 0.5:
            issues.append({"level": "info", "rule": "h2_pregunta", "message": f"Solo {question_h2}/{len(h2s)} H2 están formulados como pregunta."})
            penalty += 3

    # 8. Autoría E-E-A-T y fuentes oficiales
    if not re.search(r"sobre el autor", low):
        issues.append({"level": "warning", "rule": "autor", "message": "Falta la sección «Sobre el Autor» (E-E-A-T)."})
        penalty += 5
    links = re.findall(r"\]\((https?://[^)\s]+)\)", text)
    if len(links) < 2:
        issues.append({"level": "info", "rule": "fuentes", "message": f"{len(links)} enlace(s) externo(s); se recomiendan ≥ 2 a fuentes oficiales."})
        penalty += 3

    # 9. Citas sin número verificable (artículos huérfanos)
    if re.search(r"sentencia\s+(?:n[º°o.]*\s*)?\d{1,4}\s+de\s+\d{4}", low) and not re.search(r"(?:corte|sala|tribunal)", low):
        issues.append({"level": "warning", "rule": "cita", "message": "Sentencia citada sin órgano emisor identificado."})
        penalty += 4

    score = max(0, 100 - penalty)
    return {
        "score": score,
        "jurisdiction": j,
        "term_hits": term_hits,
        "answer_words": answer_words,
        "issues": issues,
        "passed": score >= 85 and not any(i["level"] == "error" for i in issues),
    }
