"""
Orquestador de Pipeline para IBM Data Prep Kit (DPK Pipeline) en JullEditor.
Permite encadenar transformaciones de datos (ingesta, depuración, desduplicación,
control de calidad, anonimización PII y segmentación semántica) con trazabilidad total.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform
from backend.data_prep.transforms.cleaner_transform import HeaderCleanerTransform
from backend.data_prep.transforms.docling_transform import DoclingIngestTransform
from backend.data_prep.transforms.quality_transform import DocQualityTransform


class DataPrepPipeline:
    """
    Pipeline composable de Data Prep Kit para preparación de datos textuales y normativos.
    """

    def __init__(self, transforms: list[BaseDPKTableTransform] | None = None):
        self.transforms = transforms or []
        self.execution_history: list[dict[str, Any]] = []

    def add_transform(self, transform: BaseDPKTableTransform) -> DataPrepPipeline:
        """Añade un transformador al final de la cadena de ejecución."""
        self.transforms.append(transform)
        return self

    def run(
        self,
        input_data: pa.Table | list[dict[str, Any]] | dict[str, Any] | str,
        file_name: str | None = None,
    ) -> tuple[pa.Table, dict[str, Any]]:
        """
        Ejecuta secuencialmente todos los transformadores sobre los datos de entrada.
        Retorna la tabla final transformada y el reporte consolidado de estadísticas.
        """
        start_time = time.time()
        self.execution_history.clear()

        # 1. Normalizar entrada a pyarrow.Table
        current_table = self._normalize_input(input_data, file_name)
        pipeline_stats: dict[str, Any] = {
            "initial_rows": current_table.num_rows,
            "step_statistics": {},
            "total_transforms": len(self.transforms),
        }

        # 2. Ejecutar cada transformación
        for idx, transform in enumerate(self.transforms):
            step_name = transform.__class__.__name__
            t_start = time.time()

            # Invocar contrato transform() de DPK
            out_tables, stats = transform.transform(current_table, file_name=file_name)

            # Concatenar tablas resultantes si vienen fragmentadas
            if not out_tables:
                current_table = pa.Table.from_batches([], schema=current_table.schema)
            elif len(out_tables) == 1:
                current_table = out_tables[0]
            else:
                current_table = pa.concat_tables(out_tables)

            t_elapsed = round(time.time() - t_start, 4)
            step_record = {
                "step": idx + 1,
                "transform": step_name,
                "elapsed_seconds": t_elapsed,
                "rows_output": current_table.num_rows,
                "stats": stats,
            }
            self.execution_history.append(step_record)
            pipeline_stats["step_statistics"][f"{idx+1}_{step_name}"] = step_record

        pipeline_stats["final_rows"] = current_table.num_rows
        pipeline_stats["total_duration_seconds"] = round(time.time() - start_time, 4)

        return current_table, pipeline_stats

    def _normalize_input(
        self,
        input_data: pa.Table | list[dict[str, Any]] | dict[str, Any] | str,
        file_name: str | None,
    ) -> pa.Table:
        """Convierte cualquier formato de entrada a pyarrow.Table."""
        if isinstance(input_data, pa.Table):
            return input_data

        if isinstance(input_data, str):
            record = {
                "text": input_data,
                "filename": file_name or "input_text.md",
                "source": file_name or "text_input",
            }
            return BaseDPKTableTransform.records_to_table([record])

        if isinstance(input_data, dict):
            return BaseDPKTableTransform.records_to_table([input_data])

        if isinstance(input_data, list):
            return BaseDPKTableTransform.records_to_table(input_data)

        raise TypeError(f"Tipo de entrada no compatible con DPK Pipeline: {type(input_data)}")


def create_source_prep_pipeline(
    min_words: int = 30,
    redact_pii: bool = True,
    dedup: bool = True,
) -> DataPrepPipeline:
    """
    Fábrica canónica del Pipeline de Preparación de Fuentes para IBM Granite.
    Aplica: Ingesta -> Limpieza de Cabeceras -> PII Redaction -> Desduplicación -> Calidad.
    """
    from backend.data_prep.transforms.dedup_transform import ExactDedupTransform
    from backend.data_prep.transforms.pii_transform import PIIRedactorTransform

    pipe = DataPrepPipeline()
    pipe.add_transform(DoclingIngestTransform())
    pipe.add_transform(HeaderCleanerTransform())
    if redact_pii:
        pipe.add_transform(PIIRedactorTransform())
    if dedup:
        pipe.add_transform(ExactDedupTransform())
    pipe.add_transform(DocQualityTransform({"min_words": min_words}))
    return pipe


def create_rag_indexing_pipeline(
    chunk_words: int = 400,
    overlap_words: int = 50,
    min_chunk_words: int = 8,
) -> DataPrepPipeline:
    """
    Fábrica canónica del Pipeline de Indexación RAG para Informacion_docling_rag/.
    Aplica: Ingesta -> Limpieza -> Calidad -> Desduplicación -> Segmentación Semántica/Normativa.
    """
    from backend.data_prep.transforms.chunker_transform import SemanticLegalChunkTransform
    from backend.data_prep.transforms.dedup_transform import ExactDedupTransform

    pipe = DataPrepPipeline()
    pipe.add_transform(DoclingIngestTransform())
    pipe.add_transform(HeaderCleanerTransform())
    pipe.add_transform(ExactDedupTransform())
    pipe.add_transform(DocQualityTransform({"min_words": 10}))
    pipe.add_transform(SemanticLegalChunkTransform({
        "max_chunk_words": chunk_words,
        "chunk_overlap_words": overlap_words,
        "min_chunk_words": min_chunk_words,
    }))
    return pipe
