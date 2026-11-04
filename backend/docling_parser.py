"""
Módulo de Procesamiento y Parseo de Archivos Markdown (.md) de Docling.
Permite ingestar documentos procesados por Docling (PDFs, normativas, peritajes, artículos),
extrayendo títulos, secciones, metadatos y detectando automáticamente la especialidad temática.
"""

import json
import re
from typing import Any

from backend.logger_config import get_logger

logger = get_logger("docling_parser")

def parse_docling_markdown(md_content: str, filename: str = "") -> dict[str, Any]:
    """
    Parsea el contenido de un archivo Markdown o JSON de Docling o texto estructurado.
    Extrae título, elimina ruido de escaneo/paginación, calcula métricas y detecta el tema.
    """
    if not md_content or not md_content.strip():
        logger.warning(f"Intento de parsear documento vacío: {filename}")
        return {
            "status": "error",
            "message": "El archivo está vacío",
            "title": "",
            "text": "",
            "word_count": 0,
            "theme": "cybersecurity"
        }

    text = md_content.strip()
    frontmatter_meta = {}
    extracted_title = ""

    # Si el archivo es JSON o empieza con { o [
    if filename.lower().endswith(".json") or (text.startswith("{") and text.endswith("}")):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                extracted_title = data.get("title") or data.get("name") or data.get("document_title") or ""
                if "markdown" in data and isinstance(data["markdown"], str):
                    text = data["markdown"]
                elif "text" in data and isinstance(data["text"], str):
                    text = data["text"]
                elif "content" in data and isinstance(data["content"], str):
                    text = data["content"]
                elif "body" in data and isinstance(data["body"], str):
                    text = data["body"]
                elif "main_text" in data and isinstance(data["main_text"], str):
                    text = data["main_text"]
                elif "nodes" in data and isinstance(data["nodes"], list):
                    node_texts = [n.get("text", "") for n in data["nodes"] if isinstance(n, dict) and "text" in n]
                    text = "\n\n".join(node_texts)
                else:
                    text = json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Error parseando JSON en {filename}: {e}")

    # 1. Extraer y limpiar YAML frontmatter si existe
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            text = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter_meta[k.strip().lower()] = v.strip().strip('"').strip("'")

    # 2. Extraer Título Principal
    if not extracted_title:
        extracted_title = frontmatter_meta.get("title", "")
    if not extracted_title:
        h1_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if h1_match:
            extracted_title = h1_match.group(1).strip()
        else:
            h2_match = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
            if h2_match:
                extracted_title = h2_match.group(1).strip()
            else:
                bold_match = re.search(r"^\*\*([^\*]+)\*\*", text, re.MULTILINE)
                if bold_match:
                    extracted_title = bold_match.group(1).strip()
                elif filename:
                    clean_fname = re.sub(r"\.(md|markdown|txt|json)$", "", filename, flags=re.IGNORECASE)
                    clean_fname = clean_fname.replace("_", " ").replace("-", " ").strip()
                    extracted_title = clean_fname.title()
                else:
                    extracted_title = "Documento Docling"

    extracted_title = re.sub(r"[\*\_\[\]\#]", "", extracted_title).strip()

    # 3. Limpiar artefactos comunes de Docling / OCR / PDF
    text = re.sub(r"<!--\s*image\s*-->", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(?i)\b(página|page)\s+\d+(\s+de\s+\d+)?\b", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    # 4. Calcular métricas
    words = text.split()
    word_count = len(words)

    # 5. Detección automática del tema
    text_lower = text.lower()
    theme_scores = {
        "cybersecurity": sum(text_lower.count(w) for w in ["ciberseguridad", "delito", "informático", "forense", "custodia", "evidencia", "vencert", "suscerte", "incidente", "vulnerabilidad", "ransomware", "hacker", "pericial"]),
        "ai_data": sum(text_lower.count(w) for w in ["inteligencia artificial", "modelo", "datos", "algoritmo", "machine learning", "ia", "soberanía", "cnti", "automatización", "llm", "redes neuronales", "prompt"]),
        "legal_tech": sum(text_lower.count(w) for w in ["crbv", "constitución", "firma electrónica", "mensaje de datos", "tsj", "tribunal", "ley", "gaceta", "jurídico", "derecho", "copp", "notaría", "saren", "sentencia"]),
        "science_tech": sum(text_lower.count(w) for w in ["telecomunicaciones", "conatel", "lotel", "fibra óptica", "redes", "satelital", "innovación", "tecnología", "infraestructura", "servidor", "nube", "hardware"])
    }

    detected_theme = max(theme_scores, key=theme_scores.get)
    if theme_scores[detected_theme] == 0:
        detected_theme = "cybersecurity"

    logger.info(f"Docling parseado: '{extracted_title}' ({word_count} palabras, tema: {detected_theme})")

    return {
        "status": "success",
        "title": extracted_title,
        "text": text,
        "word_count": word_count,
        "detected_theme": detected_theme,
        "filename": filename,
        "frontmatter": frontmatter_meta
    }
