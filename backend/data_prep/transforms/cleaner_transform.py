"""
Transformador de Limpieza y Depuración (Header Cleanser / Noise Filter) para IBM Data Prep Kit.
Elimina artefactos de OCR, avisos de cookies/privacidad, saltos de página y mojibake de Windows.
"""

from __future__ import annotations

import re
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform

MOJIBAKE_MAP = {
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã±": "ñ",
    "Ã\x81": "Á",
    "Ã‰": "É",
    "Ã\x8d": "Í",
    "Ã“": "Ó",
    "Ãš": "Ú",
    "Ã‘": "Ñ",
    "Ǹ": "é",
    "ǭ": "á",
    "ǧ": "ú",
    "Ǭ": "É",
    "ǻ": "ó",
    "Ǫ": "Ó",
    "ǖ": "ü",
    "ǫ": "ó",
    "ǵ": "í",
    "ǔ": "ú",
    "ǩ": "k",
    "â€œ": '"',
    "â€\x9d": '"',
    "â€™": "'",
    "â€”": "—",
    "â€“": "–",
}

BOILERPLATE_PATTERNS = [
    r"(?i)accept all cookies.*?(?=\n|\Z)",
    r"(?i)subscribe to our newsletter.*?(?=\n|\Z)",
    r"(?i)todos los derechos reservados.*?(?=\n|\Z)",
    r"(?i)política de privacidad.*?(?=\n|\Z)",
    r"(?i)share on (facebook|twitter|linkedin|whatsapp|telegram).*?(?=\n|\Z)",
    r"(?i)advertisement.*?(?=\n|\Z)",
    r"(?i)read also:.*?(?=\n|\Z)",
    r"(?i)lea también:.*?(?=\n|\Z)",
    r"(?i)\b(página|page)\s+\d+(\s+de\s+\d+)?\b",
    r"<!--\s*image\s*-->",
    r"<!--\s*page\s*-->",
]


class HeaderCleanerTransform(BaseDPKTableTransform):
    """
    Limpia texto de artefactos de escaneo Docling, cabeceras repetitivas y ruido de scraping.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.min_line_chars = self.config.get("min_line_chars", 5)

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        cleaned_records: list[dict[str, Any]] = []

        total_original_chars = 0
        total_cleaned_chars = 0
        removed_boilerplate_hits = 0

        for rec in records:
            text = rec.get("text", "")
            orig_len = len(text)
            total_original_chars += orig_len

            # 1. Corrección de Mojibake / Windows-1252
            for bad, good in MOJIBAKE_MAP.items():
                text = text.replace(bad, good)

            # 2. Eliminación de HTML residual
            text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)

            # 3. Limpieza de boilerplate y cookies
            for pat in BOILERPLATE_PATTERNS:
                matches = len(re.findall(pat, text))
                removed_boilerplate_hits += matches
                text = re.sub(pat, " ", text)

            # 4. Normalización de líneas y párrafos
            lines = [line.strip() for line in text.splitlines()]
            filtered_lines = [ln for ln in lines if len(ln) >= self.min_line_chars or ln.startswith(("#", "-", "*", ">"))]
            text = "\n".join(filtered_lines)
            text = re.sub(r"\n{3,}", "\n\n", text).strip()

            clean_len = len(text)
            total_cleaned_chars += clean_len

            rec["text"] = text
            rec["char_count"] = clean_len
            rec["cleaned"] = True
            cleaned_records.append(rec)

        out_table = self.records_to_table(cleaned_records)
        stats = {
            "processed_docs": len(records),
            "original_chars": total_original_chars,
            "cleaned_chars": total_cleaned_chars,
            "noise_reduction_ratio": round(1.0 - (total_cleaned_chars / max(1, total_original_chars)), 3),
            "boilerplate_hits_removed": removed_boilerplate_hits,
        }
        return [out_table], stats
