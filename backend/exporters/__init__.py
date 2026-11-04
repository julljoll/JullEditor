"""
Módulo de exportadores para JullEditor.
Soporta exportación a Astro Framework Markdown, WordPress y DOCX.
"""

from backend.exporters.astro_compiler import AstroEditorialCompiler
from backend.exporters.astro_exporter import (
    clean_body_for_astro,
    export_as_astro_md,
    extract_description_from_body,
    extract_tags,
    slugify_astro,
)

__all__ = [
    "AstroEditorialCompiler",
    "clean_body_for_astro",
    "export_as_astro_md",
    "extract_description_from_body",
    "extract_tags",
    "slugify_astro",
]

