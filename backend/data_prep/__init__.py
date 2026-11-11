"""
Módulo IBM Data Prep Kit (DPK) para JullEditor.
Proporciona pipelines y transformaciones de alto rendimiento para preparación de datos,
limpieza de fuentes Docling, anonimización PII, desduplicación, control de calidad
y segmentación RAG alineada con IBM Granite 3.3.
"""

from __future__ import annotations

from typing import Any

from backend.data_prep.base import BaseDPKTableTransform
from backend.data_prep.parquet_store import ParquetDatasetManager
from backend.data_prep.pipeline import (
    DataPrepPipeline,
    create_rag_indexing_pipeline,
    create_source_prep_pipeline,
)
from backend.data_prep.transforms.chunker_transform import SemanticLegalChunkTransform
from backend.data_prep.transforms.cleaner_transform import HeaderCleanerTransform
from backend.data_prep.transforms.dedup_transform import ExactDedupTransform, FuzzyDedupTransform
from backend.data_prep.transforms.docling_transform import DoclingIngestTransform
from backend.data_prep.transforms.pii_transform import PIIRedactorTransform
from backend.data_prep.transforms.quality_transform import DocQualityTransform


def preprocess_source_dpk(
    text_or_path: str,
    filename: str = "",
    redact_pii: bool = True,
    min_words: int = 30,
) -> dict[str, Any]:
    """
    Función de alto nivel para preprocesar texto fuente con IBM Data Prep Kit.
    Retorna diccionario con texto limpio, estadísticas de calidad, auditoría PII y reporte.
    """
    pipe = create_source_prep_pipeline(min_words=min_words, redact_pii=redact_pii)
    table, stats = pipe.run(text_or_path, file_name=filename or "source.md")

    records = BaseDPKTableTransform.table_to_records(table)
    if not records:
        return {
            "status": "error",
            "message": "El documento no superó los filtros mínimos de calidad de DPK.",
            "cleaned_text": "",
            "stats": stats,
        }

    rec = records[0]
    return {
        "status": "success",
        "doc_id": rec.get("doc_id"),
        "title": rec.get("title"),
        "cleaned_text": rec.get("text"),
        "word_count": rec.get("word_count"),
        "quality_score": rec.get("quality_score"),
        "is_ready_for_granite": rec.get("is_ready_for_granite"),
        "pii_redacted": rec.get("pii_redacted", False),
        "pii_audit": rec.get("pii_audit", []),
        "pipeline_stats": stats,
    }


__all__ = [
    "BaseDPKTableTransform",
    "DataPrepPipeline",
    "DoclingIngestTransform",
    "HeaderCleanerTransform",
    "DocQualityTransform",
    "ExactDedupTransform",
    "FuzzyDedupTransform",
    "PIIRedactorTransform",
    "SemanticLegalChunkTransform",
    "ParquetDatasetManager",
    "create_source_prep_pipeline",
    "create_rag_indexing_pipeline",
    "preprocess_source_dpk",
]

