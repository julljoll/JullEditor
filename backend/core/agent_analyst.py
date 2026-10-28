"""
Agente Analista (Etapa 1 del Pipeline Agéntico de JullEditor v4.0).
Extrae entidades, tesis central, términos normativos y palabras clave candidatas.
"""

from __future__ import annotations

import re
from typing import Any

from backend.sentencia_extractor import extract_sentencia_metadata


class AnalystAgent:
    """Analiza minuciosamente el documento fuente o notas suministradas."""

    def __init__(self):
        pass

    async def analyze(
        self,
        source_text: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cfg = config or {}
        title = cfg.get("title", "")

        # 1. Detección de idioma básico
        is_english = bool(re.search(r"\b(the|and|in|of|to|is|for|with|cybersecurity|data|breach)\b", source_text, re.I))
        detected_lang = "en" if is_english else "es"

        # 2. Detección de sentencia TSJ
        is_sentencia = bool(re.search(r"\b(tribunal supremo de justicia|sala de casaci[oó]n|expediente|magistrad[oa]|recurso)\b", source_text, re.I))
        sentencia_meta = {}
        if is_sentencia:
            sentencia_meta = extract_sentencia_metadata(source_text, title)

        # 3. Extracción de candidatos a palabras clave
        words = re.findall(r"\b[A-Za-zÁ-ÿ]{4,}\b", source_text.lower())
        freq: dict[str, int] = {}
        stop = {"este", "esta", "para", "como", "sobre", "entre", "tiene", "desde", "todos", "puede", "hacer", "cada", "debe", "será"}
        for w in words:
            if w not in stop:
                freq[w] = freq.get(w, 0) + 1
        sorted_kws = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        top_kws = [k for k, _ in sorted_kws[:6]]

        primary_kw = cfg.get("primary_keyword") or (top_kws[0] if top_kws else "ciberseguridad y derecho digital")

        # 4. Tesis o resumen de entrada (primeros enunciados relevantes)
        sentences = [s.strip() for s in re.split(r"[\.\n]+", source_text) if len(s.strip()) > 30]
        lead_summary = " ".join(sentences[:2]) if sentences else source_text[:200]

        return {
            "title": title or "Artículo Técnico-Legal",
            "detected_lang": detected_lang,
            "is_sentencia": is_sentencia,
            "sentencia_metadata": sentencia_meta,
            "primary_keyword": primary_kw,
            "lsi_keywords": top_kws[1:5],
            "lead_summary": lead_summary,
            "theme": cfg.get("theme", "cybersecurity"),
            "tone": cfg.get("tone", "conversational"),
            "jurisdiction": cfg.get("jurisdiction", "ve"),
            "word_count_raw": len(source_text.split()),
        }
