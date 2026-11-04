"""
Auditor de Calidad Editorial para Artículos de Astro Framework (.md).
Verifica los 10 puntos de control canónicos de 'Formato Blog -Astro.md' (sha256.us).
"""

from __future__ import annotations

import re
import sys
from typing import Any


def audit_astro_content(content: str) -> dict[str, Any]:
    """
    Evalúa el cumplimiento de los 10 puntos canónicos del formato Astro:
    1. Frontmatter YAML delimitado por '---'
    2. 12 campos obligatorios en el frontmatter
    3. Ausencia de '# H1' en el cuerpo
    4. Contenedor principal 'editorial-container'
    5. Entradilla de impacto 'editorial-lead'
    6. Cita destacada 'editorial-quote'
    7. Letra capitular 'editorial-dropcap'
    8. Maquetación 3 columnas 'editorial-three-columns' y 'editorial-col'
    9. Cuadrícula de FAQ 'grid-row grid-gap-2'
    10. Caja de autor E-E-A-T 'editorial-author-box'
    """
    checks: list[dict[str, Any]] = []

    # 1. Frontmatter presente
    has_frontmatter = content.strip().startswith("---") and content.strip().count("---") >= 2
    checks.append({
        "rule": "1. Delimitadores Frontmatter YAML (---)",
        "passed": has_frontmatter,
        "weight": 10,
        "detail": "Frontmatter correctamente delimitado con '---'" if has_frontmatter else "Faltan delimitadores '---'",
    })

    # Extraer frontmatter
    fm_text = ""
    body_text = content
    if has_frontmatter:
        parts = content.strip().split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body_text = parts[2]

    # 2. Campos del Frontmatter
    required_fields = [
        "title", "description", "pubDate", "updatedDate", "author",
        "tags", "category", "heroImage", "seoKeyword", "readingTime",
        "featured", "draft"
    ]
    missing_fields = [f for f in required_fields if not re.search(rf"^{f}:", fm_text, re.MULTILINE)]
    passed_fields = len(missing_fields) == 0
    checks.append({
        "rule": "2. 12 Campos Obligatorios en Frontmatter",
        "passed": passed_fields,
        "weight": 10,
        "detail": "Todos los campos presentes" if passed_fields else f"Faltan campos: {', '.join(missing_fields)}",
    })

    # 3. Sin H1 en el cuerpo
    has_h1_in_body = bool(re.search(r"^#\s+[^\n]+", body_text, re.MULTILINE))
    checks.append({
        "rule": "3. Ausencia de '# H1' en el Cuerpo Markdown",
        "passed": not has_h1_in_body,
        "weight": 10,
        "detail": "Cuerpo sin # H1 (layout de Astro lo imprime)" if not has_h1_in_body else "Se detectó '# H1' en el cuerpo",
    })

    # 4. editorial-container
    has_container = "editorial-container" in body_text
    checks.append({
        "rule": "4. Contenedor Principal (<div class='editorial-container'>)",
        "passed": has_container,
        "weight": 10,
        "detail": "Contenedor principal presente" if has_container else "Falta clase 'editorial-container'",
    })

    # 5. editorial-lead
    has_lead = "editorial-lead" in body_text
    checks.append({
        "rule": "5. Entradilla de Impacto (<div class='editorial-lead'>)",
        "passed": has_lead,
        "weight": 10,
        "detail": "Entradilla de impacto presente" if has_lead else "Falta clase 'editorial-lead'",
    })

    # 6. editorial-quote
    has_quote = "editorial-quote" in body_text
    checks.append({
        "rule": "6. Cita Destacada (<div class='editorial-quote'>)",
        "passed": has_quote,
        "weight": 10,
        "detail": "Pull quote presente" if has_quote else "Falta clase 'editorial-quote'",
    })

    # 7. editorial-dropcap
    has_dropcap = "editorial-dropcap" in body_text
    checks.append({
        "rule": "7. Letra Capitular (<span class='editorial-dropcap'>)",
        "passed": has_dropcap,
        "weight": 10,
        "detail": "Dropcap presente en el desarrollo" if has_dropcap else "Falta clase 'editorial-dropcap'",
    })

    # 8. editorial-three-columns y editorial-col
    has_columns = "editorial-three-columns" in body_text and "editorial-col" in body_text
    checks.append({
        "rule": "8. Maquetación 3 Columnas (editorial-three-columns / editorial-col)",
        "passed": has_columns,
        "weight": 10,
        "detail": "Bloques de columnas presentes" if has_columns else "Faltan clases de columnas",
    })

    # 9. FAQ grid
    has_faq = "grid-row" in body_text and ("tablet:grid-col-6" in body_text or "grid-gap" in body_text)
    checks.append({
        "rule": "9. Cuadrícula Responsiva FAQ (grid-row / grid-gap)",
        "passed": has_faq,
        "weight": 10,
        "detail": "Grid de preguntas frecuentes presente" if has_faq else "Falta cuadrícula de FAQ",
    })

    # 10. editorial-author-box
    has_author = "editorial-author-box" in body_text
    checks.append({
        "rule": "10. Caja de Autor E-E-A-T (<div class='editorial-author-box'>)",
        "passed": has_author,
        "weight": 10,
        "detail": "Caja de autor institucional presente" if has_author else "Falta clase 'editorial-author-box'",
    })

    total_score = sum(c["weight"] for c in checks if c["passed"])
    max_score = sum(c["weight"] for c in checks)

    return {
        "score": total_score,
        "max_score": max_score,
        "passed_all": total_score == max_score,
        "checks": checks,
    }


def print_report(res: dict[str, Any]) -> None:
    print("=" * 70)
    print(" AUDITORÍA DE CALIDAD FORMATO ASTRO EDITORIAL (sha256.us)")
    print("=" * 70)
    for c in res["checks"]:
        status = "[OK]  " if c["passed"] else "[FAIL]"
        print(f"{status} {c['rule']} ({c['weight']} pts)")
        print(f"       -> {c['detail']}")
    print("-" * 70)
    print(f" PUNTUACIÓN TOTAL: {res['score']}/{res['max_score']} ({(res['score']/res['max_score'])*100:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python audit_astro_article.py <archivo.md>")
        sys.exit(1)

    file_path = sys.argv[1]
    with open(file_path, encoding="utf-8") as f:
        md_text = f.read()

    report = audit_astro_content(md_text)
    print_report(report)
    sys.exit(0 if report["passed_all"] else 1)

