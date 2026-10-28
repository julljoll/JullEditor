"""
Chunker Jurídico Inteligente para JullEditor v4.0.
Segmenta el corpus de Informacion_docling_rag/ por artículo normativo y metadatos periciales.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extrae metadatos de frontmatter YAML si están presentes."""
    meta: dict[str, Any] = {}
    content = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            content = parts[2]
            for line in raw_yaml.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    meta[k] = v
    return meta, content.strip()


class LegalChunker:
    """Chunker semántico especializado en leyes y normas procesadas por Docling."""

    # Detecta encabezados tipo: "###### Articulo 49", "## Artículo 28.", "**Artículo 6.**", etc. con o sin indentación
    ARTICLE_PATTERN = re.compile(
        r"(?:^|\n)\s*(?:#{1,6}\s*|\*{1,2})?Art[ií]culo\s+(\d+[A-Za-z0-9\-º°]*)[\.\:\s\n°]*",
        re.IGNORECASE,
    )

    def __init__(self, fallback_chunk_size: int = 600, overlap: int = 80):
        self.fallback_chunk_size = fallback_chunk_size
        self.overlap = overlap

    def chunk_file(self, file_path: Path | str, category: str = "General") -> list[dict[str, Any]]:
        path = Path(file_path)
        if not path.exists():
            return []

        try:
            raw_text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        frontmatter, clean_body = parse_frontmatter(raw_text)
        law_name = frontmatter.get("nombre_oficial") or path.stem.replace("-", " ").title()

        return self.chunk_text(clean_body, source=path.name, category=category, law_name=law_name)

    def chunk_text(
        self,
        text: str,
        source: str = "unknown.md",
        category: str = "General",
        law_name: str = "",
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []

        matches = list(self.ARTICLE_PATTERN.finditer(text))
        if len(matches) >= 2:
            # Segmentación por artículo
            for i, match in enumerate(matches):
                art_num = match.group(1).replace("°", "").replace("º", "").strip()
                start_idx = match.start()
                end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(text)

                art_text = text[start_idx:end_idx].strip()
                # Limpiar caracteres aislados de docling como ° o saltos redundantes
                art_text = re.sub(r"\n\s*°\s*\n", "\n", art_text)

                if len(art_text) >= 20:
                    chunks.append({
                        "text": art_text,
                        "metadata": {
                            "source": source,
                            "category": category,
                            "article_number": art_num,
                            "law_name": law_name or source,
                        },
                    })
        else:
            # Fallback para textos sin división clara por artículos (preámbulos, doctrina)
            words = text.split()
            step = self.fallback_chunk_size - self.overlap
            for i in range(0, len(words), max(1, step)):
                chunk_words = words[i:i + self.fallback_chunk_size]
                chunk_str = " ".join(chunk_words).strip()
                if len(chunk_str) >= 40:
                    chunks.append({
                        "text": chunk_str,
                        "metadata": {
                            "source": source,
                            "category": category,
                            "article_number": "N/A",
                            "law_name": law_name or source,
                        },
                    })

        return chunks
