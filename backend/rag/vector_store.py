"""
Vector Store & Motor de Búsqueda Jurídica Híbrida para JullEditor v4.0.
Persistencia en .julleditor_db/ con BM25Okapi nativo y soporte ChromaDB opcional.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any

from backend.rag.chunker import LegalChunker
from backend.rag.reranker import HybridReranker
from backend.data_prep.base import BaseDPKTableTransform
from backend.data_prep.pipeline import create_rag_indexing_pipeline
from backend.data_prep.parquet_store import ParquetDatasetManager

logger = logging.getLogger("julleditor.rag.vector_store")

STOPWORDS_ES = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "mas", "más", "pero", "sus", "le", "ya",
    "o", "este", "si", "porque", "esta", "son", "entre", "esta", "cuando", "muy", "sin",
    "sobre", "ser", "tiene", "tambien", "también", "me", "hasta", "hay", "donde", "quien",
}


def tokenize(text: str) -> list[str]:
    """Tokenizador liviano en español para BM25 y similitud léxica."""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = cleaned.split()
    return [t for t in tokens if len(t) >= 2 and t not in STOPWORDS_ES]


class LegalVectorStore:
    """Almacén vectorial e híbrido local para el corpus jurídico venezolano."""

    def __init__(self, persist_dir: str | Path = ".julleditor_db"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_file = self.persist_dir / "legal_chunks.json"
        self.parquet_dir = self.persist_dir / "parquet"
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_file = self.parquet_dir / "legal_corpus.parquet"
        self.parquet_manager = ParquetDatasetManager(self.parquet_dir)

        self.chunks: list[dict[str, Any]] = []
        self.bm25: Any = None
        self.reranker = HybridReranker(bm25_weight=0.45, semantic_weight=0.55)
        self.chunker = LegalChunker()

        # Intentar cargar índice existente
        self._load_persisted()

    def _load_persisted(self) -> bool:
        if not self.chunks_file.exists():
            return False
        try:
            raw = self.chunks_file.read_text(encoding="utf-8")
            self.chunks = json.loads(raw)
            self._init_bm25()
            return True
        except Exception as e:
            logger.warning(f"No se pudo cargar el índice persistido: {e}")
            return False

    def _init_bm25(self) -> None:
        if not self.chunks:
            return
        try:
            from rank_bm25 import BM25Okapi
            corpus_tokens = [tokenize(c["text"]) for c in self.chunks]
            self.bm25 = BM25Okapi(corpus_tokens)
        except Exception as e:
            logger.debug(f"BM25Okapi no disponible o falló: {e}")
            self.bm25 = None

    def is_indexed(self) -> bool:
        return len(self.chunks) > 0 and self.chunks_file.exists()

    def index_corpus(self, corpus_dir: str | Path) -> int:
        """Indexa todos los archivos Markdown de Informacion_docling_rag/."""
        root = Path(corpus_dir)
        if not root.exists():
            raise FileNotFoundError(f"Directorio de corpus no encontrado: {root}")

        all_chunks: list[dict[str, Any]] = []
        md_files = list(root.rglob("*.md"))

        for file_path in md_files:
            rel = file_path.relative_to(root)
            category = rel.parts[0] if len(rel.parts) > 1 else "General"
            chunks = self.chunker.chunk_file(file_path, category=category)
            all_chunks.extend(chunks)

        if not all_chunks:
            return 0

        self.chunks = all_chunks

        # Persistir en JSON para arranque instantáneo con 0ms de latencia
        self.chunks_file.write_text(json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        self._init_bm25()

        return len(self.chunks)

    def index_corpus_dpk(
        self,
        corpus_dir: str | Path | None = None,
        save_parquet: bool = True,
        max_files: int | None = None,
    ) -> dict[str, Any]:
        """Indexa archivos Markdown/Docling usando el pipeline de IBM Data Prep Kit."""
        if corpus_dir is None:
            workspace_root = Path(__file__).resolve().parent.parent.parent
            corpus_dir = workspace_root / "Informacion_docling_rag"

        root = Path(corpus_dir)
        if not root.exists():
            raise FileNotFoundError(f"Directorio de corpus no encontrado: {root}")

        md_files = list(root.rglob("*.md")) + list(root.rglob("*.txt"))
        if max_files:
            md_files = md_files[:max_files]

        if not md_files:
            return {"status": "warning", "message": "No se encontraron archivos para indexar", "chunks_count": 0}

        raw_inputs: list[dict[str, Any]] = []
        for file_path in md_files:
            try:
                rel = file_path.relative_to(root)
                category = rel.parts[0] if len(rel.parts) > 1 else "General"
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                raw_inputs.append({
                    "text": text,
                    "filename": file_path.name,
                    "source": str(rel).replace("\\", "/"),
                    "category": category,
                })
            except Exception as e:
                logger.debug(f"Error leyendo {file_path}: {e}")

        if not raw_inputs:
            return {"status": "warning", "message": "No se pudo leer ningún archivo", "chunks_count": 0}

        pipeline = create_rag_indexing_pipeline()
        out_table, stats = pipeline.run(raw_inputs, file_name="informacion_docling_rag")

        parquet_path = None
        if save_parquet:
            saved_file = self.parquet_manager.save_table(out_table, "legal_corpus")
            parquet_path = str(saved_file)

        chunk_records = BaseDPKTableTransform.table_to_records(out_table)
        adapted_chunks: list[dict[str, Any]] = []
        for c in chunk_records:
            adapted_chunks.append({
                "text": c.get("chunk_text") or c.get("text", ""),
                "metadata": {
                    "law_title": c.get("law_title", ""),
                    "article_number": c.get("article_number", ""),
                    "category": c.get("category", ""),
                    "source": c.get("source", ""),
                    "word_count": c.get("word_count", 0),
                    "token_count_est": c.get("token_count_est", 0),
                    **(c.get("metadata") or {}),
                },
            })

        self.chunks = adapted_chunks
        self.chunks_file.write_text(json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        self._init_bm25()

        return {
            "status": "success",
            "chunks_count": len(self.chunks),
            "parquet_path": parquet_path,
            "pipeline_stats": stats,
        }

    def get_dpk_parquet_stats(self) -> dict[str, Any] | None:
        """Retorna estadísticas del dataset Parquet de corpus legal."""
        return self.parquet_manager.get_dataset_stats("legal_corpus")

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Búsqueda híbrida BM25 + similitud con reranking."""
        if not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return self.chunks[:top_k]

        # 1. Puntuación BM25 si está inicializado
        if self.bm25 is not None:
            raw_scores = self.bm25.get_scores(query_tokens)
        else:
            # Fallback a conteo de coincidencia de tokens
            raw_scores = []
            q_set = set(query_tokens)
            for c in self.chunks:
                c_set = set(tokenize(c["text"]))
                overlap = len(q_set & c_set)
                raw_scores.append(float(overlap))

        # 2. Filtrado y ensamble de candidatos
        candidates: list[dict[str, Any]] = []
        q_set = set(query_tokens)

        for i, score in enumerate(raw_scores):
            chunk = self.chunks[i]
            chunk_meta = chunk.get("metadata", {})
            if category and chunk_meta.get("category", "").lower() != category.lower():
                continue

            # Similitud semántica / de jaccard y longitud
            c_tokens = tokenize(chunk["text"])
            c_set = set(c_tokens)
            jaccard = len(q_set & c_set) / max(1, len(q_set | c_set))

            # Bonus si la consulta menciona el número exacto del artículo
            bonus = 0.0
            art_num = chunk_meta.get("article_number", "")
            if art_num and art_num in query:
                bonus += 0.5

            sem_score = jaccard + bonus

            candidates.append({
                "text": chunk["text"],
                "metadata": chunk_meta,
                "bm25_score": float(score),
                "semantic_score": float(sem_score),
            })

        # 3. Reranking con combinación lineal ponderada
        top_candidates = sorted(candidates, key=lambda x: x["bm25_score"], reverse=True)[: max(top_k * 4, 20)]
        return self.reranker.rerank(top_candidates, top_k=top_k)
