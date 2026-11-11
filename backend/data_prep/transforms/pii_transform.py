"""
Transformador de Detección y Anonimización de Datos Personales (PII Redactor) para IBM Data Prep Kit.
Especializado en marcos jurídicos periciales y formatos venezolanos e internacionales:
Cédulas de Identidad, RIF, correos electrónicos, números telefónicos, cuentas bancarias y tarjetas.
"""

from __future__ import annotations

import re
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform

# Patrones Regex especializados para PII
PII_PATTERNS = {
    "email": (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
        "[EMAIL_PROTEGIDO]",
    ),
    "cedula_ve": (
        # Formatos: V-12.345.678, E-84.123.456, V-12345678, C.I. 12.345.678, C.I: 12345678
        re.compile(
            r"(?i)\b(?:c\.?i\.?\s*[:\.]?\s*|[VvEeJjGg][\-\.\s]?)\s*\d{1,2}(?:\.\d{3}\.\d{3}|\d{6,8})\b"
        ),
        "[CÉDULA_PROTEGIDA]",
    ),
    "rif_ve": (
        # Formatos: J-12345678-0, V-12345678-9, G-20001234-5
        re.compile(r"(?i)\b[JjVvGgEePp][\-\s]?\d{8,9}[\-\s]?\d\b"),
        "[RIF_PROTEGIDO]",
    ),
    "phone": (
        # Teléfonos internacionales o locales VE: +58 412 1234567, 0414-1234567, 0251-1234567
        re.compile(
            r"(?:\+?58[\s\.-]?)?(?:\(?0?[24]\d{2,3}\)?[\s\.-]?)\d{3}[\s\.-]?\d{4}\b"
        ),
        "[TELÉFONO_PROTEGIDO]",
    ),
    "credit_card": (
        # Tarjetas de crédito/débito de 13 a 19 dígitos
        re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b|\b\d{15,16}\b"),
        "[TARJETA_PROTEGIDA]",
    ),
    "bank_account_ve": (
        # Código de cuenta bancaria nacional de 20 dígitos (0102-..., 0105-..., etc.)
        re.compile(r"\b01\d{2}[\s-]?\d{4}[\s-]?\d{2}[\s-]?\d{10}\b"),
        "[CUENTA_BANCARIA_PROTEGIDA]",
    ),
}


class PIIRedactorTransform(BaseDPKTableTransform):
    """
    Detecta y anonimiza información personal identificable (PII)
    para cumplir con la ética YMYL y la confidencialidad forense.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.enabled_entities = self.config.get(
            "entities", list(PII_PATTERNS.keys())
        )

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        redacted_records: list[dict[str, Any]] = []

        total_pii_hits = 0
        hits_by_entity: dict[str, int] = {k: 0 for k in self.enabled_entities}

        for rec in records:
            text = rec.get("text", "")
            redacted_text = text
            doc_pii_audit: list[dict[str, Any]] = []

            for entity_key in self.enabled_entities:
                if entity_key not in PII_PATTERNS:
                    continue
                pattern, replacement = PII_PATTERNS[entity_key]
                matches = list(pattern.finditer(redacted_text))

                if matches:
                    hits_by_entity[entity_key] += len(matches)
                    total_pii_hits += len(matches)
                    for m in matches:
                        doc_pii_audit.append({
                            "entity": entity_key,
                            "match_masked": m.group(0)[:3] + "***",
                            "start": m.start(),
                            "end": m.end(),
                        })
                    redacted_text = pattern.sub(replacement, redacted_text)

            rec["text"] = redacted_text
            rec["pii_redacted"] = len(doc_pii_audit) > 0
            rec["pii_audit"] = doc_pii_audit
            redacted_records.append(rec)

        out_table = self.records_to_table(redacted_records)
        stats = {
            "processed_docs": len(records),
            "total_pii_entities_redacted": total_pii_hits,
            "hits_by_entity": hits_by_entity,
        }
        return [out_table], stats

