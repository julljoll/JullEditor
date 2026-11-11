"""
Transformadores de Desduplicación (Exact & Fuzzy Dedup) para IBM Data Prep Kit.
Implementa desduplicación exacta mediante SHA-256 (ededup) y difusa mediante MinHash (fdedup).
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform


class ExactDedupTransform(BaseDPKTableTransform):
    """
    Desduplicador Exacto (ededup): Detecta y elimina documentos idénticos
    mediante el cálculo de un hash criptográfico SHA-256 sobre el texto normalizado.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.seen_hashes: set[str] = set()

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        unique_records: list[dict[str, Any]] = []

        duplicates_found = 0

        for rec in records:
            text = rec.get("text", "")
            # Normalizar espacios antes del hash
            norm_text = re.sub(r"\s+", " ", text.strip().lower())
            doc_hash = hashlib.sha256(norm_text.encode("utf-8")).hexdigest()

            if doc_hash in self.seen_hashes:
                duplicates_found += 1
                continue

            self.seen_hashes.add(doc_hash)
            rec["exact_hash"] = doc_hash
            unique_records.append(rec)

        out_table = self.records_to_table(unique_records)
        stats = {
            "input_docs": len(records),
            "unique_docs": len(unique_records),
            "exact_duplicates_removed": duplicates_found,
        }
        return [out_table], stats


class FuzzyDedupTransform(BaseDPKTableTransform):
    """
    Desduplicador Difuso (fdedup / MinHash): Detecta y elimina documentos casi idénticos
    (cuasi-duplicados) mediante similitud de Jaccard basada en n-gramas / shingles.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        self.shingle_size = self.config.get("shingle_size", 3)
        self.seen_shingle_sets: list[tuple[str, set[str]]] = []

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        unique_records: list[dict[str, Any]] = []

        fuzzy_duplicates_removed = 0

        for rec in records:
            text = rec.get("text", "")
            shingles = self._get_shingles(text)

            is_duplicate = False
            for prev_id, prev_shingles in self.seen_shingle_sets:
                jaccard = self._jaccard_similarity(shingles, prev_shingles)
                if jaccard >= self.similarity_threshold:
                    is_duplicate = True
                    fuzzy_duplicates_removed += 1
                    break

            if not is_duplicate:
                doc_id = rec.get("doc_id", str(len(self.seen_shingle_sets)))
                self.seen_shingle_sets.append((doc_id, shingles))
                unique_records.append(rec)

        out_table = self.records_to_table(unique_records)
        stats = {
            "input_docs": len(records),
            "unique_docs": len(unique_records),
            "fuzzy_duplicates_removed": fuzzy_duplicates_removed,
            "similarity_threshold": self.similarity_threshold,
        }
        return [out_table], stats

    def _get_shingles(self, text: str) -> set[str]:
        words = re.findall(r"\b\w+\b", text.lower())
        if len(words) < self.shingle_size:
            return set(words)
        return {
            " ".join(words[i : i + self.shingle_size])
            for i in range(len(words) - self.shingle_size + 1)
        }

    @staticmethod
    def _jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / max(1, union)

