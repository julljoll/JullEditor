#!/usr/bin/env python3
"""
Script Offline para Preprocesamiento y Limpieza de Texto Fuente.
Limpia ruido de copiado/pegado, normaliza caracteres, extrae palabras clave potenciales,
estima métricas y prepara el payload estructurado para IBM Granite sin requerir conexión a internet.
"""

import argparse
import json
import os
import re
import sys
from typing import Any


def clean_source_text(raw_text: str) -> str:
    """Elimina etiquetas HTML residuales, enlaces rotos, exceso de espacios y ruido común."""
    if not raw_text:
        return ""
    
    # Eliminar posibles tags HTML residuales
    text = re.sub(r"<[^>]+>", " ", raw_text)
    
    # Eliminar patrones de cookies o suscripciones comunes
    noise_patterns = [
        r"(?i)accept all cookies.*?(?=\n|\Z)",
        r"(?i)subscribe to our newsletter.*?(?=\n|\Z)",
        r"(?i)todos los derechos reservados.*?(?=\n|\Z)",
        r"(?i)política de privacidad.*?(?=\n|\Z)",
        r"(?i)share on (facebook|twitter|linkedin|whatsapp).*?(?=\n|\Z)",
        r"(?i)advertisement.*?(?=\n|\Z)",
        r"(?i)read also:.*?(?=\n|\Z)",
        r"(?i)lea también:.*?(?=\n|\Z)"
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, " ", text)

    # Normalizar saltos de línea y espacios
    lines = [line.strip() for line in text.splitlines()]
    clean_lines = [line for line in lines if len(line) > 10]
    
    return "\n\n".join(clean_lines)

def extract_metadata(text: str) -> dict[str, Any]:
    """Calcula métricas estadísticas y posibles keywords clave de la fuente."""
    words = re.findall(r"\b\w+\b", text.lower())
    word_count = len(words)
    
    # Palabras vacías en español e inglés
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
    
    # Detección básica de idioma
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
        "is_ready_for_generation": word_count >= 50
    }

def process_input(text_or_path: str) -> dict[str, Any]:
    """Procesa una cadena de texto directa o una ruta a archivo de texto."""
    if os.path.exists(text_or_path):
        with open(text_or_path, encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()
    else:
        raw_content = text_or_path
        
    cleaned_content = clean_source_text(raw_content)
    meta = extract_metadata(cleaned_content)
    
    return {
        "status": "success",
        "cleaned_text": cleaned_content,
        "metadata": meta
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocesador de texto fuente para IBM Granite")
    parser.add_argument("--input", type=str, help="Texto o ruta de archivo a procesar")
    parser.add_argument("--test", action="store_true", help="Ejecuta una prueba con texto sintético")
    
    args = parser.parse_args()
    
    if args.test:
        sample_text = """
        CYBERSECURITY ALERT: Ransomware targeting critical infrastructure and supply chains in 2026.
        Organizations must implement zero trust architecture, multi-factor authentication, and strict incident response protocols.
        According to recent reports, forensic evidence preservation under ISO/IEC 27037 standards is crucial for legal admissibility.
        Subscribe to our newsletter! Accept all cookies to continue reading.
        """
        result = process_input(sample_text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
        
    if not args.input:
        print("Error: Proporciona un texto o ruta con --input o usa --test", file=sys.stderr)
        sys.exit(1)
        
    result = process_input(args.input)
    print(json.dumps(result, indent=2, ensure_ascii=False))
