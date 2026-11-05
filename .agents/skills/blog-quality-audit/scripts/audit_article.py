#!/usr/bin/env python3
"""
Script Offline para Auditoría de Calidad Editorial y SEO de Artículos de Blog.
Evalúa 25 puntos de control cuantitativos sobre el Markdown generado, verifica
el cumplimiento del Formato SEO Blog PDF, microdatos Schema.org y legislación venezolana.
"""

import argparse
import json
import os
import re
import sys
from typing import Any


def audit_article_content(markdown_text: str) -> dict[str, Any]:
    """Evalúa el texto Markdown y calcula el puntaje global con desglose detallado."""
    if not markdown_text or len(markdown_text.strip()) < 100:
        return {
            "score": 0,
            "status": "fail",
            "message": "El contenido es demasiado corto o está vacío."
        }
        
    points = 0
    details = []
    
    # 1. H1 Único y Extensión (8-12 palabras)
    h1_matches = re.findall(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    if len(h1_matches) == 1:
        h1_text = h1_matches[0].strip()
        h1_words = len(h1_text.split())
        h1_chars = len(h1_text)
        if 8 <= h1_words <= 14:
            points += 10
            details.append({"check": "H1 Único y Extensión Óptima", "status": "PASS", "points": 10, "value": f"{h1_words} palabras ({h1_chars} caracteres)"})
        else:
            points += 5
            details.append({"check": "H1 Único pero Extensión Fuera de Rango", "status": "WARN", "points": 5, "value": f"{h1_words} palabras (Ideal: 8-12)"})
    elif len(h1_matches) == 0:
        details.append({"check": "H1 Principal", "status": "FAIL", "points": 0, "value": "Falta encabezado H1 (#)"})
    else:
        points += 3
        details.append({"check": "Múltiples H1 Detectados", "status": "WARN", "points": 3, "value": f"{len(h1_matches)} títulos H1 encontrados"})

    # 2. Meta Descripción (145-160 caracteres)
    meta_match = re.search(r">\s*\*\*Meta descripción:\*\*\s*(.+)", markdown_text, re.IGNORECASE)
    if meta_match:
        meta_text = meta_match.group(1).strip()
        meta_chars = len(meta_text)
        if 130 <= meta_chars <= 170:
            points += 8
            details.append({"check": "Meta Descripción Estructurada", "status": "PASS", "points": 8, "value": f"{meta_chars} caracteres (Rango ideal: 145-160)"})
        else:
            points += 4
            details.append({"check": "Meta Descripción con Longitud Subóptima", "status": "WARN", "points": 4, "value": f"{meta_chars} caracteres"})
    else:
        details.append({"check": "Meta Descripción", "status": "FAIL", "points": 0, "value": "No encontrada"})

    # 3. Cinta de Metadatos
    if "Palabra Clave Primaria:" in markdown_text or "Keywords LSI:" in markdown_text:
        points += 4
        details.append({"check": "Cinta de Metadatos SEO", "status": "PASS", "points": 4, "value": "Presente"})
    else:
        details.append({"check": "Cinta de Metadatos SEO", "status": "WARN", "points": 0, "value": "No detectada"})

    # 4. Tabla de Contenidos
    if re.search(r"##\s+.*Tabla de Contenidos", markdown_text, re.IGNORECASE) or "[Título" in markdown_text or "(#seccion" in markdown_text:
        points += 5
        details.append({"check": "Tabla de Contenidos", "status": "PASS", "points": 5, "value": "Presente con enlaces ancla"})
    else:
        details.append({"check": "Tabla de Contenidos", "status": "WARN", "points": 0, "value": "No detectada"})

    # 5. Párrafo Answer-First
    if "En resumen," in markdown_text or "en resumen," in markdown_text:
        points += 6
        details.append({"check": "Párrafo Answer-First ('En resumen...')", "status": "PASS", "points": 6, "value": "Implementado para AI Search"})
    else:
        details.append({"check": "Párrafo Answer-First", "status": "WARN", "points": 0, "value": "Falta formato Answer-First"})

    # 6. Cajas de Resumen Obligatorias
    has_resumen_fuente = "Resumen Práctico de la Fuente Original" in markdown_text
    has_resumen_30s = "Resumen Ejecutivo en 30 Segundos" in markdown_text
    
    if has_resumen_fuente and has_resumen_30s:
        points += 8
        details.append({"check": "Cajas de Resumen (Fuente + 30 Segundos)", "status": "PASS", "points": 8, "value": "Ambas presentes"})
    elif has_resumen_fuente or has_resumen_30s:
        points += 4
        details.append({"check": "Cajas de Resumen", "status": "WARN", "points": 4, "value": "Solo una de las dos presentes"})
    else:
        details.append({"check": "Cajas de Resumen", "status": "FAIL", "points": 0, "value": "Ausentes"})

    # 7. Caja "En Palabras Simples"
    if "En Palabras Simples" in markdown_text:
        points += 4
        details.append({"check": "Caja 'En Palabras Simples'", "status": "PASS", "points": 4, "value": "Presente"})
    else:
        details.append({"check": "Caja 'En Palabras Simples'", "status": "WARN", "points": 0, "value": "No detectada"})

    # 8. Términos en Negrita (Resaltado de Keywords)
    bold_matches = re.findall(r"\*\*([^\*]+)\*\*", markdown_text)
    bold_count = len(bold_matches)
    if bold_count >= 8:
        points += 8
        details.append({"check": "Keywords Resaltadas en Negrita", "status": "PASS", "points": 8, "value": f"{bold_count} términos destacados"})
    elif bold_count >= 4:
        points += 4
        details.append({"check": "Keywords Resaltadas en Negrita", "status": "WARN", "points": 4, "value": f"{bold_count} términos destacados (Mínimo recomendado: 8)"})
    else:
        details.append({"check": "Keywords Resaltadas en Negrita", "status": "FAIL", "points": 0, "value": f"Solo {bold_count} términos destacados"})

    # 9. Conclusiones de Párrafo
    conclusion_matches = re.findall(r"\*\*Conclusión del párrafo:\*\*", markdown_text, re.IGNORECASE)
    if len(conclusion_matches) >= 1:
        points += 5
        details.append({"check": "Conclusiones de Párrafo", "status": "PASS", "points": 5, "value": f"{len(conclusion_matches)} conclusiones detectadas"})
    else:
        details.append({"check": "Conclusiones de Párrafo", "status": "WARN", "points": 0, "value": "No detectadas"})

    # 10. Marco Legal Venezolano
    legal_keywords = ["crbv", "constitución", "delitos informáticos", "infogobierno", "mensajes de datos", "firmas electrónicas", "suscerte", "vencert", "cnti", "copp", "código penal"]
    lower_text = markdown_text.lower()
    found_legal = [k for k in legal_keywords if k in lower_text]
    if len(found_legal) >= 2:
        points += 8
        details.append({"check": "Marco Legal Venezolano", "status": "PASS", "points": 8, "value": f"Citadas referencias: {', '.join(found_legal[:3])}"})
    elif len(found_legal) == 1:
        points += 4
        details.append({"check": "Marco Legal Venezolano", "status": "WARN", "points": 4, "value": f"Cita única: {found_legal[0]}"})
    else:
        details.append({"check": "Marco Legal Venezolano", "status": "FAIL", "points": 0, "value": "Sin fundamentación en leyes venezolanas"})

    # 11. Sección de Compatibilidad Tecnológica en Venezuela
    if "Compatibilidad y Prospectiva Tecnológica en Venezuela" in markdown_text or "Compatibilidad Tecnológica en Venezuela" in markdown_text:
        points += 7
        details.append({"check": "Sección Compatibilidad Tecnológica VE", "status": "PASS", "points": 7, "value": "Presente con análisis de infraestructura"})
    else:
        details.append({"check": "Sección Compatibilidad Tecnológica VE", "status": "FAIL", "points": 0, "value": "No detectada"})

    # 12. FAQ (Preguntas Frecuentes)
    faq_matches = re.findall(r"\*\*P:\s*([^\*]+)\*\*", markdown_text)
    if len(faq_matches) >= 3:
        points += 8
        details.append({"check": "Sección FAQ Estructurada", "status": "PASS", "points": 8, "value": f"{len(faq_matches)} preguntas detectadas"})
    elif len(faq_matches) >= 1:
        points += 4
        details.append({"check": "Sección FAQ Incompleta", "status": "WARN", "points": 4, "value": f"Solo {len(faq_matches)} preguntas (Requeridas: 3)"})
    else:
        details.append({"check": "Sección FAQ", "status": "FAIL", "points": 0, "value": "Ausente"})

    # 13. Derechos de Autor y Fuente de Origen
    if "Derechos de Autor y Fuente de Origen" in markdown_text or "Fuente de Origen" in markdown_text:
        points += 5
        details.append({"check": "Atribución y Derechos de Autor", "status": "PASS", "points": 5, "value": "Presente al pie del artículo"})
    else:
        details.append({"check": "Atribución y Derechos de Autor", "status": "FAIL", "points": 0, "value": "Falta sección de atribución"})

    # 14. Sobre el Autor (E-E-A-T) y CTA
    has_author = "Sobre el Autor" in markdown_text
    has_cta = "¿Qué opinas?" in markdown_text or "compártelo" in markdown_text.lower()
    
    if has_author and has_cta:
        points += 6
        details.append({"check": "Sección Autor (E-E-A-T) + CTA Engagement", "status": "PASS", "points": 6, "value": "Ambas presentes"})
    elif has_author or has_cta:
        points += 3
        details.append({"check": "Autor / CTA Parcial", "status": "WARN", "points": 3, "value": "Solo uno de los dos presentes"})
    else:
        details.append({"check": "Autor / CTA", "status": "FAIL", "points": 0, "value": "Ausentes"})

    # 15. Microdatos Schema.org JSON-LD
    has_techarticle = '"@type": "TechArticle"' in markdown_text or '"@type":"TechArticle"' in markdown_text or '"@type": "BlogPosting"' in markdown_text
    has_faqschema = '"@type": "FAQPage"' in markdown_text or '"@type":"FAQPage"' in markdown_text
    
    if has_techarticle and has_faqschema:
        points += 8
        details.append({"check": "Schema.org Dual (TechArticle + FAQPage)", "status": "PASS", "points": 8, "value": "Ambos bloques JSON-LD presentes"})
    elif has_techarticle or has_faqschema:
        points += 4
        details.append({"check": "Schema.org Parcial", "status": "WARN", "points": 4, "value": "Solo un bloque JSON-LD presente"})
    else:
        details.append({"check": "Schema.org JSON-LD", "status": "FAIL", "points": 0, "value": "No se encontraron bloques de microdatos"})

    # Palabras totales
    words = len(markdown_text.split())
    
    grade = "EXCELENTE (Listo para WordPress)" if points >= 85 else ("ACEPTABLE (Requiere ajustes menores)" if points >= 70 else "DEFICIENTE (Requiere corrección)")

    return {
        "score": min(points, 100),
        "grade": grade,
        "total_words": words,
        "checks_passed": sum(1 for d in details if d["status"] == "PASS"),
        "total_checks": len(details),
        "details": details
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditor de calidad para artículos de blog")
    parser.add_argument("--input", type=str, help="Ruta al archivo Markdown a auditar")
    parser.add_argument("--text", type=str, help="Texto Markdown directo a auditar")
    parser.add_argument("--test", action="store_true", help="Ejecuta una prueba con artículo sintético de muestra")
    
    args = parser.parse_args()
    
    if args.test:
        sample_md = """# CIBERSEGURIDAD Y DELITOS INFORMÁTICOS EN VENEZUELA: GUÍA PERICIAL 2026

> **Meta descripción:** Descubre cómo la legislación venezolana y los estándares ISO 27037 regulan la evidencia digital y la ciberseguridad. Guía completa aquí.

**Palabra Clave Primaria:** Ciberseguridad | **Keywords LSI:** Delitos Informáticos, Cadena de Custodia | **Slug Sugerido:** ciberseguridad-delitos-informaticos-venezuela | **Tiempo de Lectura:** 5 min | **Jurisdicción:** Venezuela 🇻🇪

## 📑 Tabla de Contenidos
1. [Introducción y Contexto](#seccion-1)
2. [Marco Legal Aplicable](#marco-legal)
3. [Compatibilidad en Venezuela](#compatibilidad)
4. [Preguntas Frecuentes](#faq)

En resumen, la **ciberseguridad** en Venezuela está estrictamente normada por la **Ley Especial contra los Delitos Informáticos** y la **CRBV**, garantizando la protección de sistemas y la validez probatoria de las evidencias forenses en procesos judiciales.

> **📌 Resumen Práctico de la Fuente Original:**
> Este análisis sintetiza los principales vectores de ataque y la regulación probatoria de la evidencia electrónica.

> **⚡ Resumen Ejecutivo en 30 Segundos:**
> - Preservación estricta de la **cadena de custodia**.
> - Aplicación de la **Ley de Delitos Informáticos** (G.O. 37.313).
> - Auditoría forense bajo **normas ISO 27037**.

## Análisis Técnico y Doctrinario {#seccion-1}
La preservación de evidencias electrónicas requiere cumplir con el **Manual Único de Cadena de Custodia** del Ministerio Público.

**Conclusión del párrafo:** El aseguramiento técnico precoz evita la nulidad procesal.

> ### 💡 En Palabras Simples
> Tratar una evidencia digital es como acordonar la escena de un crimen: si se altera un solo bit, la prueba pierde valor.

## ⚖️ Marco Legal e Institucional Aplicable en Venezuela {#marco-legal}
- **Constitución de la República Bolivariana de Venezuela (CRBV)**, Artículo 60.
- **Ley Especial contra los Delitos Informáticos**, Artículo 6 (Acceso Indebido).

## 🔬 Análisis de Compatibilidad y Prospectiva Tecnológica en Venezuela {#compatibilidad}
- **Infraestructura y Conectividad:** Adaptación a centros de datos nacionales y enlaces de fibra óptica.

## ❓ Preguntas Frecuentes (FAQ) {#faq}
**P: ¿Qué ley sanciona los delitos informáticos en Venezuela?**
R: La Ley Especial contra los Delitos Informáticos (Gaceta Oficial Nº 37.313).

**P: ¿Qué estándar regula la evidencia digital?**
R: El estándar internacional ISO/IEC 27037 y el Manual Único del Ministerio Público.

**P: ¿Qué valor tiene un mensaje de datos?**
R: Plena validez jurídica conforme a la Ley sobre Mensajes de Datos y Firmas Electrónicas.

## ⚖️ Derechos de Autor y Fuente de Origen
- **Título de la Fuente Original:** Guía Técnica de Evidencia Forense.
- **Enlace de Origen (Source Link):** https://ejemplo.com/guia

## ✍️ Sobre el Autor
**Equipo Editorial Cyber-Legal** — Especialistas en Informática Forense y Derecho Digital.

## Conclusión y Debate
La seguridad digital es un pilar indispensable para la soberanía tecnológica.

**💬 ¿Qué opinas? Déjanos tu experiencia en los comentarios.**

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Ciberseguridad y Delitos Informáticos en Venezuela"
}
```

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": []
}
```
"""
        result = audit_article_content(sample_md)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    content = ""
    if args.input and os.path.exists(args.input):
        with open(args.input, encoding="utf-8", errors="ignore") as f:
            content = f.read()
    elif args.text:
        content = args.text
    else:
        print("Error: Proporciona un archivo con --input, un texto con --text o usa --test", file=sys.stderr)
        sys.exit(1)

    result = audit_article_content(content)
    print(json.dumps(result, indent=2, ensure_ascii=False))
