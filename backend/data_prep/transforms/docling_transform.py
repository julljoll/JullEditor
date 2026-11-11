"""
Transformador de Ingesta Docling (docling2parquet pattern) para IBM Data Prep Kit.
Normaliza documentos Markdown, JSON o textos de Docling a un esquema estructurado Apache Arrow.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any

import pyarrow as pa
from backend.data_prep.base import BaseDPKTableTransform


class DoclingIngestTransform(BaseDPKTableTransform):
    """
    Transforma texto crudo o estructuras de Docling en una tabla PyArrow con esquema:
    (doc_id, title, text, raw_markdown, source, category, metadata, created_at).
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self.default_category = self.config.get("default_category", "General")

    def transform(
        self, table: pa.Table, file_name: str | None = None
    ) -> tuple[list[pa.Table], dict[str, Any]]:
        records = self.table_to_records(table)
        output_records: list[dict[str, Any]] = []

        total_words = 0
        total_docs = len(records)

        for rec in records:
            # Obtener contenido crudo (puede venir como 'content', 'text', 'markdown', 'raw')
            raw_text = rec.get("text") or rec.get("content") or rec.get("markdown") or rec.get("raw") or ""
            filename = rec.get("filename") or file_name or rec.get("source") or "documento_docling.md"
            category = rec.get("category") or self.default_category

            parsed = self._extract_docling_structure(raw_text, filename)
            doc_id = rec.get("doc_id") or hashlib.sha256((filename + parsed["title"]).encode("utf-8")).hexdigest()[:16]

            words_in_doc = len(parsed["text"].split())
            total_words += words_in_doc

            output_records.append({
                "doc_id": doc_id,
                "title": parsed["title"],
                "text": parsed["text"],
                "raw_markdown": raw_text,
                "source": filename,
                "category": category,
                "word_count": words_in_doc,
                "metadata": parsed["metadata"],
                "created_at": datetime.now().isoformat(),
            })

        out_table = self.records_to_table(output_records)
        stats = {
            "ingested_docs": total_docs,
            "total_words": total_words,
            "avg_words_per_doc": round(total_words / max(1, total_docs), 1),
        }
        return [out_table], stats

    def _extract_docling_structure(self, raw_text: Any, filename: str) -> dict[str, Any]:
        """Extrae metadatos, título y cuerpo limpio de un documento Docling."""
        if isinstance(raw_text, dict):
            extracted_title = raw_text.get("title") or raw_text.get("name") or raw_text.get("document_title") or ""
            metadata = raw_text.get("metadata", {})
            text = raw_text.get("markdown") or raw_text.get("text") or ""
            return {"title": extracted_title, "metadata": metadata, "text": text}

        text = str(raw_text or "").strip()
        metadata: dict[str, Any] = {}
        extracted_title = ""

        # Si el contenido es JSON de Docling
        if filename.lower().endswith(".json") or (text.startswith("{") and text.endswith("}")):
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    extracted_title = data.get("title") or data.get("name") or data.get("document_title") or ""
                    metadata = data.get("metadata", {})
                    if "markdown" in data and isinstance(data["markdown"], str):
                        text = data["markdown"]
                    elif "text" in data and isinstance(data["text"], str):
                        text = data["text"]
                    elif "nodes" in data and isinstance(data["nodes"], list):
                        node_texts = [n.get("text", "") for n in data["nodes"] if isinstance(n, dict) and "text" in n]
                        text = "\n\n".join(node_texts)
            except Exception:
                pass

        # Frontmatter YAML si existe
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                text = parts[2].strip()
                for line in fm_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip().lower()] = v.strip().strip('"').strip("'")

        # Título principal
        if not extracted_title:
            extracted_title = metadata.get("title", "")
        if not extracted_title:
            h1 = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if h1:
                extracted_title = h1.group(1).strip()
            else:
                h2 = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
                if h2:
                    extracted_title = h2.group(1).strip()
                else:
                    clean_fn = re.sub(r"\.(md|markdown|txt|json)$", "", filename, flags=re.IGNORECASE)
                    extracted_title = clean_fn.replace("_", " ").replace("-", " ").title()

        extracted_title = re.sub(r"[\*\_\[\]\#]", "", extracted_title).strip()

        return {
            "title": extracted_title,
            "text": text,
            "metadata": metadata,
        }
