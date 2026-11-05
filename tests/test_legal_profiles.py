"""
Pruebas unitarias para los perfiles jurídicos (Venezuela y Colombia),
glosarios, resolución de jurisdicción y validador legal / GEO 2026.
"""

from fastapi.testclient import TestClient

from backend.app import app
from backend.legal_profiles import (
    DISCLAIMER_TEXT,
    GLOSSARY,
    PERSONAS,
    build_persona_block,
    resolve_jurisdiction,
    select_glossary_terms,
)
from backend.legal_validator import audit_legal_quality
from backend.prompts import build_generation_prompt

client = TestClient(app)

def test_resolve_jurisdiction_explicit():
    assert resolve_jurisdiction("venezuela") == "ve"
    assert resolve_jurisdiction("ve") == "ve"
    assert resolve_jurisdiction("colombia") == "co"
    assert resolve_jurisdiction("co") == "co"
    assert resolve_jurisdiction("international") == "intl"
    assert resolve_jurisdiction("intl") == "intl"

def test_resolve_jurisdiction_by_persona():
    assert resolve_jurisdiction("auto", persona="abogado_co_litigante") == "co"
    assert resolve_jurisdiction("auto", persona="abogado_ve_doctrinal") == "ve"

def test_resolve_jurisdiction_by_text_hints():
    co_text = "Se radicó una acción de tutela ante el juzgado de Bogotá por vulneración de habeas data."
    assert resolve_jurisdiction("auto", text=co_text) == "co"

    ve_text = "Publicado en Gaceta Oficial conforme a la jurisprudencia de la Sala Constitucional del TSJ."
    assert resolve_jurisdiction("auto", text=ve_text) == "ve"

def test_personas_structure():
    expected_keys = {"jurisdiction", "label", "register", "formulas", "structure"}
    assert "abogado_ve_doctrinal" in PERSONAS
    assert "abogado_co_litigante" in PERSONAS
    assert "consultor_corporativo" in PERSONAS

    for pid, pdata in PERSONAS.items():
        assert expected_keys.issubset(pdata.keys()), f"Faltan claves en {pid}"
        assert len(pdata["formulas"]) > 0

def test_glossaries_populated():
    assert "ve" in GLOSSARY
    assert "co" in GLOSSARY
    assert len(GLOSSARY["ve"]) >= 15
    assert len(GLOSSARY["co"]) >= 15

    # Términos clave colombianos
    co_terms = [t["term"] for t in GLOSSARY["co"]]
    assert any("tutela" in t.lower() for t in co_terms)
    assert any("habeas data" in t.lower() for t in co_terms)
    assert any("sic" in t.lower() or "industria y comercio" in t.lower() for t in co_terms)

    # Términos clave venezolanos
    ve_terms = [t["term"] for t in GLOSSARY["ve"]]
    assert any("amparo" in t.lower() for t in ve_terms)
    assert any("tsj" in t.lower() or "sala constitucional" in t.lower() for t in ve_terms)
    assert any("gaceta oficial" in t.lower() for t in ve_terms)

def test_select_glossary_terms():
    picked = select_glossary_terms("delito informático y ciberseguridad forense", "co", k=5)
    assert len(picked) == 5
    assert any("informático" in p["term"].lower() or "custodia" in p["term"].lower() for p in picked)

def test_build_persona_block():
    block = build_persona_block("abogado_co_litigante", "co", "tutela y habeas data")
    assert "Abogado Colombiano" in block
    assert "Registro:" in block
    assert "LÉXICO JURÍDICO" in block
    assert "ÉTICA PUBLICITARIA" in block
    assert DISCLAIMER_TEXT in block

def test_prompt_generation_with_colombia():
    prompt = build_generation_prompt(
        article_source_text="Análisis de seguridad digital y protección de datos.",
        source_title="Seguridad en la nube",
        theme="cybersecurity",
        tone="abogado_co_litigante",
        jurisdiction="colombia"
    )
    assert "República de Colombia" in prompt
    assert "Ley 1273 de 2009" in prompt or "Ley 1581 de 2012" in prompt
    assert "abogado_co_litigante" not in prompt  # El id técnico se transforma a etiqueta legible
    assert "Abogado Colombiano — Litigante" in prompt

def test_legal_validator_audit_clean():
    markdown = """# GUÍA COMPLETA DE CIBERSEGURIDAD Y DELITOS INFORMÁTICOS EN COLOMBIA
> **Meta descripción:** Descubre las acciones legales y sanciones frente a delitos informáticos en Colombia bajo la Ley 1273 y el régimen de protección de datos personales.

En resumen, la normativa penal colombiana protege la confidencialidad, integridad y disponibilidad de los datos informáticos, sancionando conductas como el acceso abusivo a sistemas y la interceptación de datos con penas privativas de la libertad y multas significativas impuestas por las autoridades judiciales competentes en el territorio nacional.

## 📑 Tabla de Contenidos
1. [¿Qué conductas sanciona la Ley 1273?](#conductas)

## ¿Qué conductas sanciona la Ley 1273? {#conductas}
La **acción de tutela** y el **derecho de petición** son mecanismos procesales para exigir la protección de datos y el **habeas data** ante el **responsable y encargado del tratamiento**.
La **Superintendencia de Industria y Comercio (SIC)** vigila el cumplimiento. En caso de delito, la **Fiscalía General de la Nación** asume el **radicado** del proceso penal. La **cadena de custodia** garantiza la validez probatoria del **mensaje de datos** con base en el **Código General del Proceso (CGP)**.

## ❓ Preguntas Frecuentes
P: ¿Cómo denunciar?
R: Ante la Fiscalía.

## ✍️ Sobre el Autor
Abogado litigante inscrito ante el Consejo Superior de la Judicatura (Tarjeta Profesional).

[Enlace Oficial SIC](https://www.sic.gov.co)
[Enlace Senado](http://www.secretariasenado.gov.co)

""" + DISCLAIMER_TEXT + "\n"
    result = audit_legal_quality(markdown, jurisdiction="co")
    assert result["score"] >= 80
    assert result["jurisdiction"] == "co"
    assert result["term_hits"] >= 5

def test_legal_validator_catches_promises_and_missing_disclaimer():
    bad_markdown = """# Artículo de Prueba
Le garantizamos 100% efectivo que gane su caso sin riesgo alguno.
"""
    result = audit_legal_quality(bad_markdown, jurisdiction="ve")
    rules_hit = [i["rule"] for i in result["issues"]]
    assert "etica" in rules_hit
    assert "descargo" in rules_hit
    assert result["passed"] is False

def test_seo_audit_api_endpoint_with_legal_scores():
    md = """# DERECHO DIGITAL Y FORENSE INFORMÁTICO
> **Meta descripción:** Análisis pericial y normativo de la evidencia digital y el valor probatorio de los mensajes de datos en procesos judiciales contemporáneos.

En resumen, la evidencia digital requiere estricta observancia de los protocolos periciales y de cadena de custodia para conservar plena eficacia probatoria en sede jurisdiccional, garantizando el derecho a la defensa y el debido proceso de las partes intervinientes en el litigio.

## 📑 Tabla de Contenidos
1. [Cadena de custodia](#custodia)

## ¿Cómo asegurar la cadena de custodia? {#custodia}
La **experticia informática** sobre el **mensaje de datos** debe preservar la integridad.
La **Sala Constitucional del Tribunal Supremo de Justicia** ha fijado criterio vinculante.
El **amparo constitucional** procede ante violaciones flagrantes del **debido proceso**.
Asimismo, la **caducidad** y la **prescripción** son figuras procesales distintas.
La **prueba electrónica** se promueve conforme al procedimiento civil.

## ❓ Preguntas Frecuentes
P: ¿Qué es la prueba electrónica?
R: Todo mensaje de datos con valor probatorio.

## ✍️ Sobre el Autor
Abogado especialista (INPREABOGADO).

## Conclusión y Debate
Comparte tus opiniones y comentarios.

[TSJ Enlace Oficial](http://www.tsj.gob.ve)
[Gaceta Oficial](http://www.tsj.gob.ve/gaceta)

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Derecho Digital y Forense"
}
```

""" + DISCLAIMER_TEXT + "\n"
    response = client.post("/api/seo-audit", json={"markdown": md, "jurisdiction": "venezuela"})
    assert response.status_code == 200
    data = response.json()
    assert "report" in data
    assert "legal_report" in data
    assert "combined_score" in data
    assert data["jurisdiction"] == "ve"
    assert data["combined_score"] > 60


def test_academic_persona_structure_and_terms():
    """Verifica que el perfil de Revista Científica Arbitrada esté configurado con rigor académico y forense."""
    assert "revista_cientifica_law_tech" in PERSONAS
    pdata = PERSONAS["revista_cientifica_law_tech"]
    assert pdata["jurisdiction"] == "ve"
    assert "doctoral" in pdata["register"].lower()
    assert pdata["structure"] == "academic_law_tech_review"
    assert any("27037" in f for f in pdata["formulas"])
    assert any("cadena de custodia" in f.lower() for f in pdata["formulas"])

    ve_terms = [t["term"] for t in GLOSSARY["ve"]]
    assert any("mismidad" in t.lower() for t in ve_terms)
    assert any("hash criptográfico" in t.lower() or "sha-256" in t.lower() for t in ve_terms)
    assert any("manual único de cadena de custodia" in t.lower() for t in ve_terms)
    assert any("cenif" in t.lower() for t in ve_terms)


def test_prompt_generation_with_academic_persona():
    """Verifica que el prompt de generación para revista científica inyecte la estructura canónica doctoral."""
    prompt = build_generation_prompt(
        article_source_text="Estudio sobre la evidencia digital y adquisición en memoria volátil conforme a RFC 3227.",
        source_title="Preservación de Evidencia Informática y Cadena de Custodia",
        theme="forensic_law",
        tone="revista_cientifica_law_tech",
        jurisdiction="venezuela"
    )
    assert "ScholarlyArticle" in prompt
    assert "RESUMEN ESTRUCTURADO (ABSTRACT)" in prompt
    assert "ISO/IEC 27037" in prompt
    assert "Manual Único de Cadena de Custodia" in prompt
    assert "Tribunal Supremo de Justicia" in prompt
    assert "APA 7" in prompt or "APA" in prompt


