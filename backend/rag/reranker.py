"""
Reranker Híbrido para Búsqueda Jurídica en JullEditor v4.0.
Combina puntuaciones BM25 (léxicas) y similitud de coseno/semántica.
"""

from __future__ import annotations

from typing import Any


def min_max_normalize(scores: list[float]) -> list[float]:
    """Normaliza una lista de puntuaciones al rango [0, 1]."""
    if not scores:
        return []
    min_v = min(scores)
    max_v = max(scores)
    if max_v == min_v:
        return [1.0 if max_v > 0 else 0.0 for _ in scores]
    return [(s - min_v) / (max_v - min_v) for s in scores]


class HybridReranker:
    """Reranker con combinación lineal ponderada."""

    def __init__(self, bm25_weight: float = 0.4, semantic_weight: float = 0.6):
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight

    def rerank(
        self,
        candidates: list[dict[str, Any]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Acepta candidatos con 'bm25_score' y 'semantic_score',

        calcula el score final ponderado y devuelve los top_k ordenados.
        """
        if not candidates:
            return []

        bm25_raw = [float(c.get("bm25_score", 0.0)) for c in candidates]
        sem_raw = [float(c.get("semantic_score", 0.0)) for c in candidates]

        bm25_norm = min_max_normalize(bm25_raw)
        sem_norm = min_max_normalize(sem_raw)

        for i, cand in enumerate(candidates):
            final_score = (self.bm25_weight * bm25_norm[i]) + (self.semantic_weight * sem_norm[i])
            cand["hybrid_score"] = round(final_score, 4)

        ranked = sorted(candidates, key=lambda x: x.get("hybrid_score", 0.0), reverse=True)
        return ranked[:top_k]
