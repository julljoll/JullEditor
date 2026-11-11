#!/usr/bin/env python3
"""
Script Offline para Preprocesamiento y Limpieza de Texto Fuente.
Integra IBM Data Prep Kit (DPK) con Apache Arrow para anonimización PII,
limpieza de cabeceras, evaluación de calidad y preparación de payloads para IBM Granite.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any

# Intentar importar IBM Data Prep Kit desde el backend
DPK_AVAILABLE = False
try:
    # Añadir workspace root a sys.path
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)

    from backend.data_prep import preprocess_source_dpk
    DPK_AVAILABLE = True
except Exception:
    DPK_AVAILABLE = False


def clean_source_text(raw_text: str) -> str:
    """Elimina etiquetas HTML residuales, enlaces rotos, exceso de espacios y ruido común."""
    if not raw_text:
        return ""

    text = re.sub(r"<[^>]+>", " ", raw_text)

    noise_patterns = [
        r"(?i)accept all cookies.*?(?=\n|\Z)",
        r"(?i)subscribe to our newsletter.*?(?=\n|\Z)",
        r"(?i)todos los derechos reservados.*?(?=\n|\Z)",
        r"(?i)política de privacidad.*?(?=\n|\Z)",
        r"(?i)share on (facebook|twitter|linkedin|whatsapp).*?(?=\n|\Z)",
        r"(?i)advertisement.*?(?=\n|\Z)",
        r"(?i)read also:.*?(?=\n|\Z)",
        r"(?i)lea también:.*?(?=\n|\Z)",
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)

    lines = [line.strip() for line in text.splitlines()]
    clean_lines = [line for line in lines if len(line) > 10]

    return "\n\n".join(clean_lines)


def extract_metadata(text: str) -> dict[str, Any]:
    """Calcula métricas estadísticas y posibles keywords clave de la fuente."""
    words = re.findall(r"\b\w+\b", text.lower())
    word_count = len(words)

    stopwords = {
        "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para", "con", "no", "una",
        "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este", "sí", "porque", "esta", "son", "entre",
        "the", "and", "to", "of", "in", "is", "that", "for", "it", "as", "was", "with", "on", "are", "by", "this"
    }

    frequency = {}
    for w in words:
        if len(w) > 3 and w not in stopwords:
            frequency[w] = frequency.get(w, 0) + 1

    sorted_keywords = sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:8]
    suggested_keywords = [k[0] for k in sorted_keywords]

    es_indicators = {"que", "los", "del", "las", "para", "con", "una", "este"}
    en_indicators = {"the", "and", "that", "with", "this", "from", "which"}
    es_count = sum(1 for w in words if w in es_indicators)
    en_count = sum(1 for w in words if w in en_indicators)
    detected_lang = "es" if es_count >= en_count else "en"

    return {
        "word_count": word_count,
        "char_count": len(text),
        "detected_lang": detected_lang,
        "suggested_keywords": suggested_keywords,
        "is_ready_for_generation": word_count >= 50,
    }


def process_input(
    text_or_path: str,
    use_dpk: bool = True,
    redact_pii: bool = True,
    filename: str = "",
) -> dict[str, Any]:
    """Procesa una cadena de texto directa o una ruta a archivo con IBM DPK o fallback."""
    if os.path.exists(text_or_path):
        filename = filename or os.path.basename(text_or_path)
        with open(text_or_path, encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()
    else:
        raw_content = text_or_path

    # Modo IBM Data Prep Kit
    if use_dpk and DPK_AVAILABLE:
        try:
            dpk_res = preprocess_source_dpk(
                text_or_path=raw_content,
                filename=filename or "source.md",
                redact_pii=redact_pii,
                min_words=20,
            )
            if dpk_res.get("status") == "success":
                dpk_res["engine"] = "ibm-data-prep-kit"
                return dpk_res
        except Exception as e:
            sys.stderr.write(f"Aviso DPK: error en pipeline, usando fallback clásico ({e})\n")

    # Fallback clásico
    cleaned_content = clean_source_text(raw_content)
    meta = extract_metadata(cleaned_content)

    return {
        "status": "success",
        "engine": "classic-regex",
        "cleaned_text": cleaned_content,
        "metadata": meta,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocesador de texto fuente con IBM Data Prep Kit")
    parser.add_argument("--input", type=str, help="Texto o ruta de archivo a procesar")
    parser.add_argument("--test", action="store_true", help="Ejecuta una prueba con texto sintético y PII")
    parser.add_argument("--no-dpk", action="store_true", help="Desactiva IBM Data Prep Kit y usa fallback")
    parser.add_argument("--no-pii", action="store_true", help="No redactar PII sensible")

    args = parser.parse_args()

    if args.test:
        sample_text = """
        CYBERSECURITY & LEGALTECH ALERT: Ransomware targeting critical infrastructure in 2026.
        El perito informático con C.I. V-18.765.432 y RIF J-31234567-0 levantó la evidencia forense.
        Contacto pericial: auditoria.seguridad@tribunal.gob.ve o al teléfono 0414-1234567.
        Organizations must implement zero trust architecture, multi-factor authentication, and strict incident response protocols.
        According to recent reports, forensic evidence preservation under ISO/IEC 27037 standards is crucial for legal admissibility.
        Subscribe to our newsletter! Accept all cookies to continue reading.
        """
        result = process_input(
            sample_text,
            use_dpk=not args.no_dpk,
            redact_pii=not args.no_pii,
            filename="sample_test.md",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if not args.input:
        print("Error: Proporciona un texto o ruta con --input o usa --test", file=sys.stderr)
        sys.exit(1)

    result = process_input(
        args.input,
        use_dpk=not args.no_dpk,
        redact_pii=not args.no_pii,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
