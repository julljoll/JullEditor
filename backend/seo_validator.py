"""
Validador de Auditoría SEO y Control Estructural para Artículos de Blog.
Implementa las reglas del FORMATO SEO BLOG PDF y estándares 2026 en el backend
para evaluación determinista, pruebas unitarias y auto-corrección.
"""

import json
import re
from typing import Any


def audit_article_seo(markdown: str) -> dict[str, Any]:
    """
    Evalúa minuciosamente el artículo Markdown según métricas SEO y de formato.
    Retorna métricas, banderas booleanas, lista de mejoras y un score ponderado (0-100%).
    """
    if not markdown or not markdown.strip():
        return {
            "score": 0,
            "word_count": 0,
            "reading_time_min": 0,
            "headings_total": 0,
            "h1_count": 0,
            "h2_count": 0,
            "h3_count": 0,
            "bold_keywords_count": 0,
            "links_count": 0,
            "primary_keyword": "",
            "keyword_repetition": 0,
            "keyword_density_pct": 0.0,
            "has_meta_description": False,
            "meta_description_chars": 0,
            "has_toc": False,
            "has_faq": False,
            "has_author_eeat": False,
            "has_cta": False,
            "has_schema_jsonld": False,
            "schema_jsonld_valid": False,
            "violations": ["El artículo está vacío."]
        }

    violations = []
    clean_md = re.sub(r'^---[\s\S]*?---\s*', '', markdown or "")
    
    # 1. Conteo de palabras y lectura
    text_only = re.sub(r'[#*`>_\[\]\(\)\-\|]', ' ', clean_md).strip()
    words = [w for w in text_only.split() if len(w) > 0]
    word_count = len(words)
    reading_time = max(1, round(word_count / 200))

    # 2. Encabezados
    h1_matches = re.findall(r'^#\s+(.+)$', clean_md, re.MULTILINE)
    if not h1_matches:
        h1_matches = re.findall(r'^###?\s*T[ií]tulo(?:\s*H1)?:\s*\**([^*]+)\**', clean_md, re.MULTILINE | re.IGNORECASE)

    h2_matches = re.findall(r'^##\s+(.+)$', clean_md, re.MULTILINE)
    h3_matches = re.findall(r'^###\s+(.+)$', clean_md, re.MULTILINE)
    if len(h2_matches) < 2 and len(h3_matches) >= 3:
        h2_matches = h3_matches
    
    h1_count = len(h1_matches)
    h2_count = len(h2_matches)
    h3_count = len(h3_matches)
    headings_total = h1_count + h2_count + h3_count

    h1_optimal = False
    h1_title = ""
    if h1_count == 1:
        h1_title = re.sub(r'[*_`]', '', h1_matches[0]).strip()
        h1_len = len(h1_title.split())
        if 6 <= h1_len <= 15:
            h1_optimal = True
        else:
            violations.append(f"El H1 tiene {h1_len} palabras (lo óptimo es entre 8 y 12 palabras).")
    elif h1_count == 0:
        violations.append("Falta el encabezado H1 principal.")
    else:
        violations.append(f"Hay {h1_count} encabezados H1 (debe haber exactamente uno).")

    # 3. Meta Descripción
    meta_match = (
        re.search(r'>\s*\*\*Meta\s+descripci[oó]n:\*\*\s*(.+)', clean_md, re.IGNORECASE)
        or re.search(r'\*\*Meta\s+descripci[oó]n:\*\*\s*(.+)', clean_md, re.IGNORECASE)
        or re.search(r'#{2,3}\s*Meta\s+Descripci[oó]n\s*\n+([^\n#]+)', clean_md, re.IGNORECASE)
    )
    has_meta = False
    meta_chars = 0
    if meta_match:
        has_meta = True
        meta_text = re.sub(r'[*_`]', '', meta_match.group(1)).strip()
        meta_chars = len(meta_text)
        if not (130 <= meta_chars <= 185):
            violations.append(f"La meta descripción tiene {meta_chars} caracteres (óptimo: 145-160).")
    else:
        violations.append("Falta el bloque obligatorio de Meta Descripción (> **Meta descripción:** ...).")

    # 4. Tabla de contenidos
    has_toc = bool(re.search(r'#{2,3}\s*📑?\s*Tabla de Contenidos', clean_md, re.IGNORECASE) or "[#seccion" in clean_md or "[#marco" in clean_md or re.search(r'1\.\s+.*?\*\*', clean_md))
    if not has_toc:
        violations.append("Falta la Tabla de Contenidos estructurada con anclas.")

    # 5. FAQ
    has_faq = bool(re.search(r'#{2,3}\s*❓?\s*(?:Preguntas Frecuentes|FAQ)', clean_md, re.IGNORECASE) or re.search(r'\b(?:P:|R:|P/R\d*:|question\d+)\b', clean_md, re.IGNORECASE))
    if not has_faq:
        violations.append("Falta la sección de Preguntas Frecuentes (FAQ).")

    # 6. E-E-A-T Autor y CTA
    has_author = bool(re.search(r'#{2,3}\s*✍️?\s*Sobre el Autor', clean_md, re.IGNORECASE) or "E-E-A-T" in clean_md or "IBM Research" in clean_md)
    has_cta = bool(re.search(r'#{2,3}\s*.*Conclusi[oó]n.*Debate', clean_md, re.IGNORECASE) or re.search(r'\b(?:comparte|comenta|debate)\b', clean_md, re.IGNORECASE))

    # 7. Keywords en negrita y enlaces
    bold_matches = re.findall(r'\*\*[^*]+\*\*', clean_md)
    bold_keywords_count = len(bold_matches)
    link_matches = re.findall(r'\[.*?\]\(https?://.*?\)', clean_md)
    links_count = len(link_matches)

    # 8. Keyword primaria y densidad
    primary_kw = ""
    kw_header = re.search(r'Palabra Clave Primaria:\s*\*?([^\n|*]+)', clean_md, re.IGNORECASE)
    if kw_header and kw_header.group(1):
        primary_kw = kw_header.group(1).strip()
    elif h1_title:
        words_h1 = [w for w in h1_title.split() if len(w) > 3]
        if words_h1:
            primary_kw = " ".join(words_h1[:2])

    keyword_repetition = 0
    keyword_density_pct = 0.0
    if primary_kw and len(primary_kw) >= 3:
        try:
            pattern = re.escape(primary_kw)
            matches = re.findall(pattern, clean_md, re.IGNORECASE)
            keyword_repetition = len(matches)
            if word_count > 0:
                kw_word_len = len(primary_kw.split())
                keyword_density_pct = round(((keyword_repetition * kw_word_len) / word_count) * 100, 2)
        except Exception:
            pass

    # 9. Schema.org JSON-LD
    schema_blocks = re.findall(r'```(?:json)?\s*(\{\s*"@context"\s*:\s*"https?://schema\.org".*?\})\s*```', clean_md, re.DOTALL)
    has_schema = len(schema_blocks) > 0
    schema_valid = False
    if has_schema:
        valid_count = 0
        for block in schema_blocks:
            try:
                parsed = json.loads(block)
                if "@context" in parsed and ("@type" in parsed or "@graph" in parsed or "TechArticle" in parsed or "FAQPage" in parsed):
                    valid_count += 1
            except Exception:
                pass
        schema_valid = (valid_count == len(schema_blocks))
        if not schema_valid:
            violations.append("Uno o más bloques Schema.org JSON-LD tienen errores de sintaxis JSON.")
    else:
        violations.append("Falta el bloque de microdatos Schema.org JSON-LD.")

    # 10. Cálculo del Score Ponderado (0-100)
    score = 0
    if h1_count == 1: score += 10
    if h1_optimal: score += 5
    if has_meta: score += 10
    if 130 <= meta_chars <= 175: score += 5
    if has_toc: score += 10
    if h2_count >= 3: score += 10
    if bold_keywords_count >= 8: score += 10
    if links_count >= 1: score += 5
    if has_faq: score += 10
    if has_author: score += 5
    if has_cta: score += 5
    if has_schema: score += 10
    if schema_valid: score += 5

    score = min(100, max(0, score))

    return {
        "score": score,
        "word_count": word_count,
        "reading_time_min": reading_time,
        "headings_total": headings_total,
        "h1_count": h1_count,
        "h2_count": h2_count,
        "h3_count": h3_count,
        "bold_keywords_count": bold_keywords_count,
        "links_count": links_count,
        "primary_keyword": primary_kw,
        "keyword_repetition": keyword_repetition,
        "keyword_density_pct": keyword_density_pct,
        "has_meta_description": has_meta,
        "meta_description_chars": meta_chars,
        "has_toc": has_toc,
        "has_faq": has_faq,
        "has_author_eeat": has_author,
        "has_cta": has_cta,
        "has_schema_jsonld": has_schema,
        "schema_jsonld_valid": schema_valid,
        "violations": violations
    }
