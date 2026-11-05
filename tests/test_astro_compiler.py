"""
Pruebas Unitarias y de Integración para el Compilador Editorial Astro.
Valida la conversión de Markdown a la plantilla de 3 columnas de 'Formato Blog -Astro.md',
etiquetas HTML balanceadas, dropcaps, pull quotes, FAQ grid y frontmatter de 12 campos.
"""

import importlib.util
from pathlib import Path
import re
import pytest

from backend.exporters.astro_compiler import (
    AstroEditorialCompiler,
    clean_mojibake,
    slugify,
)

# Cargar dinámicamente audit_astro_article desde .agents/
_audit_script_path = (
    Path(__file__).parent.parent
    / ".agents"
    / "skills"
    / "blog-quality-audit"
    / "scripts"
    / "audit_astro_article.py"
)
_spec = importlib.util.spec_from_file_location("audit_astro_article", _audit_script_path)
_audit_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_audit_module)
audit_astro_content = _audit_module.audit_astro_content


class TestAstroCompilerBasics:
    def test_slugify(self):
        assert slugify("Cadena de Custodia Digital en Venezuela") == "cadena-de-custodia-digital-en-venezuela"
        assert slugify("") == "articulo-blog"
        assert slugify("ISO/IEC 27037: ¿Cómo Aplica?") == "iso-iec-27037-como-aplica"

    def test_clean_mojibake(self):
        text = "peritaje de vanguardia con cafǸ y protecciǻn"
        cleaned = clean_mojibake(text)
        assert "café" in cleaned
        assert "protección" in cleaned


class TestAstroCompilerExtraction:
    @pytest.fixture
    def sample_markdown(self):
        return """# Ciberseguridad Forense en Venezuela: Análisis Pericial

> **Meta descripción:** Descubre cómo opera la informática forense y la preservación probatoria bajo norma ISO 27037 en Venezuela.

> «El atacante moderno rara vez derriba la puerta con fuerza bruta; convence a alguien desde adentro.»

En resumen, la **ciberseguridad forense** garantiza la integridad de la evidencia digital para su admisión procesal en tribunales.

## ¿Qué es la Cadena de Custodia Digital? {#cadena-custodia}

La recolección de evidencia requiere un procedimiento estandarizado que impida la contaminación del indicio material.

> **📌 Lección pericial crítica:**
> Un clic imprudente puede anular la validez de la prueba si no se calcula el hash SHA-256 de forma inmediata.

## Protocolo de Respuesta ante Incidentes {#protocolo}

En caso de detectar una anomalía crítica en los servidores:

* **Paso 1:** Desconectar los cables de red física inmediatamente.
* **Paso 2:** No apagar ni reiniciar las máquinas afectadas.
* **Paso 3:** Solicitar inspección pericial forense certificada.

## ❓ Preguntas Frecuentes (FAQ)

### ¿Qué valor probatorio tiene el hash SHA-256?
El hash criptográfico actúa como una huella digital matemática inmutable que certifica que el archivo no fue manipulado.

### ¿Por qué no se deben apagar los equipos?
La memoria volátil RAM contiene procesos activos y conexiones que desaparecen irremediablemente al cortar la energía.

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle"
}
```
"""

    def test_extract_frontmatter_all_12_fields(self, sample_markdown):
        compiler = AstroEditorialCompiler({
            "theme": "cybersecurity",
            "author": "Dr. Perito Forense",
        })
        fm = compiler.extract_frontmatter_metadata("Ciberseguridad Forense en Venezuela", sample_markdown)

        assert fm["title"] == "Ciberseguridad Forense en Venezuela"
        assert fm["author"] == "Dr. Perito Forense"
        assert "ciberseguridad" in fm["tags"]
        assert fm["category"] == "Opinión Pericial"
        assert fm["readingTime"] >= 1
        assert fm["featured"] is True
        assert fm["draft"] is False
        assert len(fm["description"]) <= 165
        assert "pubDate" in fm
        assert "updatedDate" in fm
        assert "heroImage" in fm
        assert "seoKeyword" in fm

    def test_parse_body_elements(self, sample_markdown):
        compiler = AstroEditorialCompiler()
        parsed = compiler.parse_body_elements(sample_markdown)

        # Lead
        assert "ciberseguridad forense" in parsed["lead"]
        # Quote
        assert "«" in parsed["quote"] and "»" in parsed["quote"]
        # Secciones
        assert len(parsed["sections"]) >= 2
        # FAQ items
        assert len(parsed["faq_items"]) >= 2
        assert "hash SHA-256" in parsed["faq_items"][0][0]
        # Schema blocks extraídos
        assert len(parsed["schema_blocks"]) >= 1

    def test_compile_passes_audit_100_percent(self, sample_markdown):
        compiler = AstroEditorialCompiler({
            "theme": "cybersecurity",
            "author": "Equipo Pericial sha256.us",
        })
        compiled = compiler.compile("Ciberseguridad Forense en Venezuela", sample_markdown)

        # Auditar con el auditor canónico
        audit = audit_astro_content(compiled)
        assert audit["score"] == 100
        assert audit["passed_all"] is True

        # Validar componentes específicos
        assert '<div class="editorial-container">' in compiled
        assert '<div class="editorial-lead">' in compiled
        assert '<div class="editorial-quote">' in compiled
        assert '<span class="editorial-dropcap">' in compiled
        assert '<div class="editorial-three-columns">' in compiled
        assert '<div class="editorial-col">' in compiled
        assert '<div class="editorial-box">' in compiled
        assert '<div class="grid-row grid-gap-2">' in compiled
        assert '<div class="editorial-author-box">' in compiled
        assert not re.search(r"^#\s+", compiled.split("---")[2], re.MULTILINE)

    def test_compiler_with_minimal_content(self):
        compiler = AstroEditorialCompiler()
        compiled = compiler.compile("Artículo Breve", "Este es un artículo breve sobre evidencia digital forense.")

        assert compiled.startswith("---")
        assert "editorial-container" in compiled
        assert "editorial-dropcap" in compiled
        assert "editorial-author-box" in compiled
