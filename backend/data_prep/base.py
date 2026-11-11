"""
Clases Base para Transformaciones de IBM Data Prep Kit (DPK) en JullEditor.
Implementa el contrato canónico AbstractTableTransform de data_processing.transform
operando sobre tablas PyArrow (Apache Arrow).
"""

from __future__ import annotations

import json
from abc import abstractmethod
from typing import Any

import pyarrow as pa
from data_processing.transform import AbstractTableTransform, TransformConfiguration


class BaseDPKTableTransform(AbstractTableTransform):
    """
    Transformador de tabla compatible al 100% con la arquitectura de IBM Data Prep Kit.
    Procesa lotes de datos estructurados representados como pyarrow.Table,
    calcula estadísticas de transformación y preserva linaje de datos.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config or {})
        self.config = config or {}
        self.stats: dict[str, Any] = {}

    @abstractmethod
    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        """
        Contrato canónico DPK:
        Entrada: pyarrow.Table y nombre de archivo opcional.
        Salida: tupla (lista de tablas transformadas, diccionario de estadísticas).
        """
        pass

    def flush(self) -> tuple[list[pa.Table], dict[str, Any]]:
        """Limpia búferes internos al final del lote si aplica."""
        return [], {}

    # -------------------------------------------------------------------------
    # Utilidades auxiliares para conversión transparente Dict/List <-> PyArrow
    # -------------------------------------------------------------------------

    @staticmethod
    def records_to_table(records: list[dict[str, Any]]) -> pa.Table:
        """Convierte una lista de diccionarios en una tabla PyArrow con tipos seguros."""
        if not records:
            return pa.Table.from_batches([], schema=pa.schema([pa.field("empty", pa.string())]))

        # Normalizar diccionarios anidados a JSON strings para compatibilidad Arrow plana
        normalized_records: list[dict[str, Any]] = []
        for r in records:
            norm = {}
            for k, v in r.items():
                if isinstance(v, (dict, list)):
                    norm[k] = json.dumps(v, ensure_ascii=False)
                elif v is None:
                    norm[k] = ""
                else:
                    norm[k] = v
            normalized_records.append(norm)

        return pa.Table.from_pylist(normalized_records)

    @staticmethod
    def table_to_records(table: pa.Table) -> list[dict[str, Any]]:
        """Convierte una tabla PyArrow en una lista de diccionarios con deserialización JSON."""
        records = table.to_pylist()
        json_fields = {
            "metadata", "pii_audit", "quality_metrics", "stats",
            "params", "step_statistics", "hits_by_entity"
        }
        for r in records:
            for k, v in r.items():
                if k in json_fields and isinstance(v, str) and (
                    (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]"))
                ):
                    try:
                        r[k] = json.loads(v)
                    except Exception:
                        pass
        return records


class GenericTransformConfiguration(TransformConfiguration):
    """Configuración estándar de transformador DPK para instanciación por fábrica."""

    def __init__(self, name: str, transform_class: type[BaseDPKTableTransform], options: dict[str, Any] | None = None):
        super().__init__(name=name, transform_class=transform_class)
        self.options = options or {}
