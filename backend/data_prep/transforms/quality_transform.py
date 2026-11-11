"""
Transformador de Calidad Documental y Legibilidad (Doc Quality) para IBM Data Prep Kit.
Calcula métricas estadísticas de texto, ratio de símbolos, legibilidad y evalúa
el grado de preparación (Granite Readiness Score) para el modelo IBM Granite 3.3.
"""

from __future__ import annotations

import re
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform

STOPWORDS_ES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "más", "pero", "sus", "le", "ya", "o", "este",
    "sí", "porque", "esta", "son", "entre", "cuando", "muy", "sin", "sobre", "ser", "tiene", "también",
}


class DocQualityTransform(BaseDPKTableTransform):
    """
    Evalúa la calidad textual según los estándares de preparación de datos de IBM Granite.
    Calcula métricas lingüísticas y descarta opcionalmente documentos con ruido excesivo o muy cortos.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.min_words = self.config.get("min_words", 20)
        self.max_symbol_ratio = self.config.get("max_symbol_ratio", 0.40)
        self.filter_low_quality = self.config.get("filter_low_quality", False)

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        passed_records: list[dict[str, Any]] = []

        total_docs = len(records)
        accepted_docs = 0
        rejected_docs = 0
        quality_scores: list[float] = []

        for rec in records:
            text = rec.get("text", "")
            metrics = self.calculate_metrics(text)

            rec["quality_metrics"] = metrics
            rec["quality_score"] = metrics["granite_readiness_score"]
            rec["is_ready_for_granite"] = metrics["is_ready"]

            is_acceptable = (
                metrics["word_count"] >= self.min_words
                and metrics["symbol_to_word_ratio"] <= self.max_symbol_ratio
            )

            if is_acceptable or not self.filter_low_quality:
                passed_records.append(rec)
                accepted_docs += 1
                quality_scores.append(metrics["granite_readiness_score"])
            else:
                rejected_docs += 1

        out_table = self.records_to_table(passed_records)
        stats = {
            "total_evaluated_docs": total_docs,
            "accepted_docs": accepted_docs,
            "rejected_docs": rejected_docs,
            "avg_quality_score": round(sum(quality_scores) / max(1, len(quality_scores)), 1) if quality_scores else 0.0,
        }
        return [out_table], stats

    @staticmethod
    def calculate_metrics(text: str) -> dict[str, Any]:
        """Calcula métricas de calidad y legibilidad de texto para IBM Granite."""
        if not text:
            return {
                "word_count": 0,
                "sentence_count": 0,
                "char_count": 0,
                "avg_word_length": 0.0,
                "symbol_to_word_ratio": 1.0,
                "stopword_ratio": 0.0,
                "granite_readiness_score": 0.0,
                "is_ready": False,
            }

        words = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9]+\b", text)
        word_count = len(words)
        char_count = len(text)

        # Contar oraciones
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 3]
        sentence_count = len(sentences)

        # Longitud promedio de palabra
        total_letters = sum(len(w) for w in words)
        avg_word_len = round(total_letters / max(1, word_count), 2)

        # Ratio de símbolos/puntuación respecto a palabras
        symbols = re.findall(r"[^\w\s]", text)
        symbol_ratio = round(len(symbols) / max(1, word_count), 3)

        # Densidad de stopwords (indica coherencia gramatical en español)
        words_lower = [w.lower() for w in words]
        stopwords_found = sum(1 for w in words_lower if w in STOPWORDS_ES)
        stopword_ratio = round(stopwords_found / max(1, word_count), 3)

        # Cálculo del Granite Readiness Score (0 a 100)
        # Factor 1: Longitud (hasta 500 palabras óptimo para RAG chunk) -> 35 pts
        score_length = min(35.0, (word_count / 150.0) * 35.0)

        # Factor 2: Riqueza gramatical / stopwords (debe estar entre 0.15 y 0.50) -> 25 pts
        if 0.15 <= stopword_ratio <= 0.55:
            score_grammar = 25.0
        elif stopword_ratio > 0.05:
            score_grammar = 15.0
        else:
            score_grammar = 5.0

        # Factor 3: Ratio de símbolos no destructivo (< 0.25) -> 25 pts
        if symbol_ratio <= 0.20:
            score_symbols = 25.0
        elif symbol_ratio <= 0.35:
            score_symbols = 15.0
        else:
            score_symbols = 5.0

        # Factor 4: Estructura de oraciones (párrafos de más de 1 oración) -> 15 pts
        score_structure = 15.0 if sentence_count >= 2 else (8.0 if sentence_count == 1 else 0.0)

        granite_score = round(score_length + score_grammar + score_symbols + score_structure, 1)
        is_ready = granite_score >= 50.0 and word_count >= 25

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "char_count": char_count,
            "avg_word_length": avg_word_len,
            "symbol_to_word_ratio": symbol_ratio,
            "stopword_ratio": stopword_ratio,
            "granite_readiness_score": granite_score,
            "is_ready": is_ready,
        }
