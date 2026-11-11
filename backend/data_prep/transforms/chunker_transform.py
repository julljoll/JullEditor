"""
Transformador de Segmentación Semántica y RAG (Doc Chunk) para IBM Data Prep Kit.
Divide documentos extensos y normativas legales respetando artículos normativos y
la ventana de contexto de IBM Granite 3.3.
"""

from __future__ import annotations

import re
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform


class SemanticLegalChunkTransform(BaseDPKTableTransform):
    """
    Segmentador de documentos de DPK para RAG:
    Detecta artículos normativos (Art. 28, Art. 60, etc.) o fragmentos semánticos
    con solapamiento controlado para RAG y contexto de Granite.
    """

    ARTICLE_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:#{1,6}\s*|\*{1,2})?Art[ií]culo\s+(\d+[A-Za-z0-9\-º°]*)[\.\:\s\n°]*",
        re.IGNORECASE,
    )

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.max_chunk_words = self.config.get("max_chunk_words", 450)
        self.chunk_overlap_words = self.config.get("chunk_overlap_words", 50)
        self.min_chunk_words = self.config.get("min_chunk_words", 8)

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        chunk_records: list[dict[str, Any]] = []

        total_chunks = 0
        total_tokens_est = 0

        for rec in records:
            doc_id = rec.get("doc_id", "doc")
            text = rec.get("text", "")
            title = rec.get("title", "")
            category = rec.get("category", "General")
            source = rec.get("source", file_name or "unknown.md")
            metadata = rec.get("metadata", {})

            chunks = self._chunk_document(text, doc_id, title, source, category, metadata)
            for c in chunks:
                chunk_records.append(c)
                total_chunks += 1
                total_tokens_est += c.get("token_count_est", 0)

        out_table = self.records_to_table(chunk_records)
        stats = {
            "input_docs": len(records),
            "generated_chunks": total_chunks,
            "avg_chunks_per_doc": round(total_chunks / max(1, len(records)), 1),
            "total_estimated_tokens": total_tokens_est,
        }
        return [out_table], stats

    def _chunk_document(
        self,
        text: str,
        doc_id: str,
        title: str,
        source: str,
        category: str,
        parent_meta: dict[str, Any],
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []

        matches = list(self.ARTICLE_PATTERN.finditer(text))
        if len(matches) >= 2:
            # Segmentación por artículo normativo
            for i, match in enumerate(matches):
                art_num = match.group(1).replace("°", "").replace("º", "").strip()
                start_idx = match.start()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                art_text = text[start_idx:end_idx].strip()
                art_text = re.sub(r"\n\s*°\s*\n", "\n", art_text)

                words = art_text.split()
                if len(words) >= self.min_chunk_words:
                    token_est = int(len(words) * 1.35)
                    chunk_id = f"{doc_id}_art_{art_num}_{i+1}"
                    chunks.append({
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "chunk_text": art_text,
                        "law_title": title,
                        "article_number": art_num,
                        "source": source,
                        "category": category,
                        "word_count": len(words),
                        "token_count_est": token_est,
                        "is_article": True,
                        "metadata": {**parent_meta, "article_number": art_num},
                    })
        else:
            # Segmentación semántica por bloques con solapamiento
            words = text.split()
            step = max(1, self.max_chunk_words - self.chunk_overlap_words)
            chunk_idx = 1
            for i in range(0, len(words), step):
                chunk_words = words[i : i + self.max_chunk_words]
                chunk_str = " ".join(chunk_words).strip()
                if len(chunk_words) >= self.min_chunk_words:
                    token_est = int(len(chunk_words) * 1.35)
                    chunk_id = f"{doc_id}_part_{chunk_idx}"
                    chunks.append({
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "chunk_text": chunk_str,
                        "law_title": title,
                        "article_number": "N/A",
                        "source": source,
                        "category": category,
                        "word_count": len(chunk_words),
                        "token_count_est": token_est,
                        "is_article": False,
                        "metadata": parent_meta,
                    })
                    chunk_idx += 1

        return chunks
