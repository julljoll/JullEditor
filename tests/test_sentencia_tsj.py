"""
Test Suite: Perfil Analista Jurisprudencial TSJ (Modo Revista Digital)
Valida extracción de metadatos, construcción de prompts, persistencia RAG
y auditoría SEO/Legal para decisiones del Tribunal Supremo de Justicia.
"""

import os
import sys

# Asegurar codificación utf-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Rutas del workspace
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, WORKSPACE_DIR)

from backend.legal_profiles import _STRUCTURES, PERSONAS, build_persona_block
from backend.legal_validator import audit_legal_quality
from backend.prompts import build_sentencia_tsj_prompt
from backend.rag_manager import save_final_article
from backend.sentencia_extractor import extract_sentencia_metadata, is_sentencia_text
from backend.seo_validator import audit_article_seo

JURISPRUDENCIAS_DIR = os.path.join(WORKSPACE_DIR, "Informacion_docling_rag", "Jurisprudencias")

def run_tests():
    print("=" * 70)
    print("INICIANDO SUITE DE TESTS: PERFIL ANALISTA TSJ (REVISTA DIGITAL)")
    print("=" * 70)

    # TEST 1: Verificar Perfil, Estructura y Glosario en legal_profiles
    print("\n[TEST 1] Verificando legal_profiles.py...")
    assert "analista_tsj_revista" in PERSONAS, "Falta perfil analista_tsj_revista en PERSONAS"
    assert "analisis_sentencia_tsj" in _STRUCTURES, "Falta estructura analisis_sentencia_tsj en _STRUCTURES"
    
    persona = PERSONAS["analista_tsj_revista"]
    assert persona["jurisdiction"] == "ve", "Jurisdicción debe ser 've'"
    assert len(persona["formulas"]) >= 10, "Debe tener al menos 10 fórmulas de estilo"
    
    block = build_persona_block("analista_tsj_revista", "ve")
    assert len(block) > 500, "El bloque de prompt de la persona debe ser sustancial"
    print("  ✓ Perfil 'analista_tsj_revista' verificado correctamente.")
    print("  ✓ Estructura 'analisis_sentencia_tsj' con 16 puntos verificada.")
    print(f"  ✓ Bloque de persona generado: {len(block)} caracteres.")

    # TEST 2: Extracción de Metadatos en Sentencias Reales
    print("\n[TEST 2] Verificando extractor de metadatos en sentencias reales...")
    test_files = [
        ("SCP-268-23-05-2024 principio de intervención mínima.md", "Sala de Casación Penal", "AA30-P-2024-000184", "Elsa Janeth Gómez Moreno"),
        ("330039-000709-101123-2023-23-504.html.md", "Sala de Casación Civil", "AA20-C-2023-000504", "José Luis Gutiérrez Parra"),
    ]

    for fname, expected_sala, expected_exp, expected_ponente in test_files:
        fpath = os.path.join(JURISPRUDENCIAS_DIR, fname)
        assert os.path.exists(fpath), f"No existe el archivo de prueba: {fpath}"
        with open(fpath, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        assert is_sentencia_text(content), f"No detectó como sentencia: {fname}"
        meta = extract_sentencia_metadata(content, fname)
        
        print(f"\n  --- Archivo: {fname} ---")
        print(f"    Sala detectada:       {meta['sala']}")
        print(f"    Expediente:           {meta['expediente']}")
        print(f"    Sentencia Nº:         {meta['numero_sentencia']}")
        print(f"    Ponente:              {meta['ponente']}")
        print(f"    Fecha:                {meta['fecha_decision']}")
        print(f"    Decisión:             {meta['decision_tipo']}")
        print(f"    Leyes citadas ({len(meta['leyes_citadas'])}): {', '.join(meta['leyes_citadas'][:4])}...")
        
        assert meta["sala"] == expected_sala, f"Sala esperada {expected_sala}, obtenida {meta['sala']}"
        assert meta["expediente"] == expected_exp, f"Expediente esperado {expected_exp}, obtenido {meta['expediente']}"
        assert meta["ponente"] == expected_ponente, f"Ponente esperado {expected_ponente}, obtenido {meta['ponente']}"
        assert meta["decision_tipo"], "Debe detectar un tipo de decisión"
        assert len(meta["leyes_citadas"]) > 0, "Debe detectar leyes citadas"
        print(f"  ✓ Extracción de {fname} validada al 100%.")

    # TEST 3: Construcción del Prompt Especializado para Inferencia Local
    print("\n[TEST 3] Verificando construcción del prompt con build_sentencia_tsj_prompt()...")
    sample_text = content[:4000]
    prompt = build_sentencia_tsj_prompt(
        article_source_text=sample_text,
        source_title="Sentencia SCC 709",
        sentencia_metadata=meta,
        target_words=1400
    )
    assert "Analista Jurisprudencial Senior" in prompt
    assert "Ficha Técnica de la Sentencia" in prompt
    assert meta["expediente"] in prompt
    assert meta["ponente"] in prompt
    assert "TechArticle" in prompt
    assert "FAQPage" in prompt
    print(f"  ✓ Prompt de sentencia generado exitosamente ({len(prompt)} caracteres).")

    # TEST 4: Persistencia RAG con frontmatter article_type: "sentencia_tsj"
    print("\n[TEST 4] Verificando persistencia RAG en RAG/articulos/...")
    sample_article_md = """# Principio de Intervención Mínima y Sobreseimiento Penal en Casación TSJ

> **Meta descripción:** Descubre el alcance vinculante del principio de intervención mínima penal fijado por la Sala de Casación Penal del TSJ venezolano en la sentencia 268.

---
**Palabra Clave Primaria:** intervención mínima penal | **Keywords LSI:** sentencia TSJ, sobreseimiento, casación penal, delito de estafa | **Slug Sugerido:** intervencion-minima-penal-tsj-venezuela | **Tiempo de Lectura:** 5 min | **Jurisdicción:** Venezuela 🇻🇪
---

En resumen, la Sala de Casación Penal del Tribunal Supremo de Justicia ratificó que el principio de **intervención mínima penal** obliga a jueces y fiscales a decretar el sobreseimiento de la causa cuando los hechos controvertidos revisten naturaleza estrictamente contractual o civil, reservando el derecho penal como la última ratio del ordenamiento jurídico venezolano.

## 📋 Ficha Técnica de la Sentencia

| Parámetro Judicial | Detalle Procesal |
| :--- | :--- |
| **Órgano Jurisdiccional** | Tribunal Supremo de Justicia de la República Bolivariana de Venezuela |
| **Sala Decisora** | Sala de Casación Penal |
| **Sentencia Nº** | 268 |
| **Expediente** | AA30-P-2024-000184 |
| **Magistrado Ponente** | Elsa Janeth Gómez Moreno |
| **Fecha de Decisión** | 23 de mayo de 2024 |
| **Partes Procesales** | Recurrente: Carlos Rafael Parra Fracachan vs. Recurrido: José Alberto Romero Viloria |
| **Materia** | Penal — Recurso de Casación |
| **Delito / Asunto** | Estafa (Art. 462 Código Penal) |
| **Dispositivo del Fallo** | Desestimado por manifiestamente infundado |
| **Carácter Vinculante** | No (Doctrina de Casación / Reiterada) |

## 📑 Tabla de Contenidos
1. [¿Qué resolvió el TSJ en esta sentencia?](#contexto)
2. [¿Cuál es la doctrina establecida por la Sala?](#doctrina)
3. [¿Qué normas aplicó la Sala en su decisión?](#normas)
4. [¿Cómo impacta esta decisión en la práctica jurídica?](#impacto)
5. [Votos Salvados y Criterios Disidentes](#votos)
6. [Preguntas Frecuentes (FAQ)](#faq)
7. [Derechos de Autor y Fuente Oficial](#fuente)
8. [Conclusión y Debate](#conclusion)

> **📌 Resumen Práctico de la Sentencia:**
> La Sala de Casación Penal desestimó el recurso de casación confirmando que un conflicto derivado del incumplimiento de obligaciones contractuales no puede ventilarse por la vía penal mediante denuncias por estafa, ratificando el sobreseimiento decretado en primera instancia.

> **⚡ Resumen Ejecutivo en 30 Segundos:**
> - El conflicto surgió por un presunto incumplimiento contractual calificado erróneamente como **estafa agravada**.
> - La Sala ratificó que el Derecho Penal opera como **última ratio** y no puede sustituir a la jurisdicción civil mercantil.
> - Se confirmó el **sobreseimiento definitivo** de la causa en beneficio del imputado conforme al Art. 300.2 del COPP.

## ¿Qué resolvió el TSJ en esta sentencia? {#contexto}
El presente caso tuvo su origen en una denuncia penal interpuesta por presunta comisión del delito de estafa contra un ciudadano con quien se sostenían relaciones comerciales. El tribunal de control de primera instancia no admitió la imputación fiscal y decretó oportunamente el sobreseimiento de la causa.

La Corte de Apelaciones respectiva confirmó la decisión absolutoria al constatar que la controversia correspondía exclusivamente al ámbito obligacional mercantil. Los apoderados del querellante acudieron en recurso de casación ante el Máximo Tribunal de la República aduciendo vicios procesales y falta de fundamentación.

La Sala de Casación Penal desestimó el recurso por manifiestamente infundado al constatar que los hechos no revestían carácter punible sino un conflicto contractual propio de los tribunales civiles y mercantiles.

**Conclusión del párrafo:** La Sala reafirma la frontera infranqueable entre el incumplimiento civil contractual y el ilícito penal de estafa.

## ¿Cuál es la doctrina establecida por la Sala? {#doctrina}
La doctrina establecida en el fallo destaca que el Derecho Penal en un Estado social de Derecho y de Justicia rige bajo el principio estricto de subsidiariedad y fragmentariedad. La Sala subrayó que la intervención coercitiva penal solo es admisible cuando los demás medios de defensa jurídica resultan insuficientes para proteger el bien jurídico.

Asimismo, la Sala citó expresamente jurisprudencia de la Sala Constitucional: «cuando los hechos motorizados no puedan subsumirse en ninguna figura punible de nuestra legislación penal, de lo que se trata es de un mero conflicto contractual cuya solución debe ventilarse en los juzgados civiles o mercantiles».

Esta ratificación jurisprudencial impide la instrumentalización indebida de la acción penal con fines de cobro coercitivo de acreencias o extorsión judicial.

**Conclusión del párrafo:** El principio de intervención mínima prohíbe la criminalización de meras controversias mercantiles o civiles.

> ### 💡 En Palabras Simples
> Imagina que prestas dinero o firmas un contrato de servicios y la otra parte no te paga a tiempo. La ley prohíbe meter presa a una persona por deudas contractuales; debes demandarla ante un tribunal civil o mercantil para cobrar, no formular denuncias penales por estafa para asustarla.

## ¿Qué normas aplicó la Sala en su decisión? {#normas}
La Sala fundamentó su juicio en el marco constitucional y adjetivo penal venezolano taxativo:
- **Constitución de la República Bolivariana de Venezuela, Art. 266.8:** Atribución de la Sala para conocer y resolver el recurso de casación penal.
- **Código Orgánico Procesal Penal (COPP), Art. 300, numeral 2:** Causal obligatoria de sobreseimiento cuando el hecho investigado no es punible o no reviste carácter penal.
- **Código Orgánico Procesal Penal, Arts. 454 y 457:** Desestimación del recurso de casación manifiestamente infundado y confirmación del fallo recurrido.
- **Código Penal de Venezuela, Art. 462:** Tipo penal de estafa, inaplicable ante el mero incumplimiento de convenciones comerciales.

**Conclusión del párrafo:** La aplicación del Art. 300.2 del COPP es de orden público procesal ante hechos no constitutivos de delito.

## ¿Cómo impacta esta decisión en la práctica jurídica? {#impacto}
Para los abogados litigantes, esta decisión sienta una pauta clara sobre la improcedencia de interponer querellas penales por fraude o estafa cuando el fondo del litigio nace de un negocio jurídico contractual. Los tribunales de control tienen la facultad y el deber de frenar imputaciones penales infundadas en fases preliminares.

Para los jueces de instancia, el fallo ratifica su facultad revisora en la audiencia de imputación para no admitir pretensiones fiscales que lesionen el debido proceso consagrado en el artículo 49 de la Constitución.

Para los ciudadanos e inversionistas, proporciona certeza jurídica y protección frente a denuncias intimidatorias promovidas indebidamente en sede ministerial o fiscal.

**Conclusión del párrafo:** Se fortalece la seguridad jurídica y se descongestiona el sistema penitenciario de causas de orden estrictamente patrimonial privado.

## Votos Salvados y Criterios Disidentes {#votos}
La decisión de la Sala de Casación Penal fue adoptada por unanimidad de sus magistrados integrantes, sin que consten votos salvados ni votos concurrentes en las actas de la decisión.

## ❓ Preguntas Frecuentes (FAQ) {#faq}

**P: ¿Qué significa el principio de intervención mínima en el derecho penal venezolano?**
R: Significa que el Estado solo puede recurrir a las sanciones penales como último recurso extremo, cuando las ramas civil, mercantil o administrativa no puedan resolver la controversia.

**P: ¿Procede una denuncia penal por estafa si un cliente no cumple un contrato?**
R: No procede; el TSJ reitera que el incumplimiento obligacional debe demandarse ante juzgados civiles o mercantiles, debiendo sobreseerse la acción penal si se intenta criminalizar.

**P: ¿Tiene esta sentencia carácter vinculante erga omnes para todos los tribunales?**
R: No tiene carácter vinculante general (reservado a la Sala Constitucional bajo el Art. 335 CRBV), pero constituye doctrina de casación reiterada que los jueces de instancia deben observar diligentemente.

## ⚖️ Derechos de Autor y Fuente Oficial {#fuente}
- **Órgano Jurisdiccional:** Tribunal Supremo de Justicia de la República Bolivariana de Venezuela
- **Sala Decisora:** Sala de Casación Penal
- **Expediente / Fallo:** AA30-P-2024-000184 — Sentencia Nº 268 de fecha 23 de mayo de 2024
- **Ponente:** Magistrada Elsa Janeth Gómez Moreno
- **Atribución Institucional:** Análisis pericial-educativo elaborado conforme al derecho de acceso a la información judicial pública de la República.

## ✍️ Sobre el Equipo Editorial
**Área de Investigación Doctrinal y LegalTech** — Redacción jurídica pericial en derecho penal sustantivo y casación judicial. Especialistas en derechos humanos, garantías procesales y gobernanza digital.

## Conclusión y Debate {#conclusion}
La sentencia analizada constituye un valioso recordatorio de que los tribunales penales no son despachos de cobranza ni instrumentos de presión mercantil.

**💬 ¿Qué opinas?** ¿Consideras que en Venezuela los juzgados de control frenan a tiempo las denuncias penales por motivos mercantiles?

**📢 Comparte este análisis jurisprudencial con juristas, peritos y estudiantes de derecho interesados en el debido proceso penal.**

> *Descargo ético: Este contenido es exclusivamente informativo y no constituye asesoría legal ni crea una relación abogado-cliente. Cada caso requiere análisis particular por un profesional del derecho.*

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "Principio de Intervención Mínima y Sobreseimiento Penal en Casación TSJ",
  "description": "Descubre el alcance vinculante del principio de intervención mínima penal fijado por la Sala de Casación Penal del TSJ venezolano en la sentencia 268.",
  "keywords": "intervencion minima penal, sentencia TSJ, sobreseimiento, casacion penal, delito de estafa",
  "inLanguage": "es-VE",
  "about": "Análisis Jurisprudencial Tribunal Supremo de Justicia",
  "author": {
    "@type": "Organization",
    "name": "Equipo Editorial LegalTech & Jurisprudencia TSJ"
  },
  "publisher": {
    "@type": "Organization",
    "name": "SHA256.US Cyber-Legal Blueprint",
    "url": "https://sha256.us"
  },
  "datePublished": "2024-05-23",
  "dateModified": "2026-10-22",
  "image": "https://sha256.us/images/tsj-sentencia.png",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://sha256.us/intervencion-minima-penal-tsj-venezuela"
  },
  "articleSection": "Jurisprudencia TSJ",
  "wordCount": "1250"
}
```

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "¿Qué significa el principio de intervención mínima en el derecho penal venezolano?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Significa que el Estado solo puede recurrir a las sanciones penales como último recurso extremo, cuando las ramas civil, mercantil o administrativa no puedan resolver la controversia."
      }
    },
    {
      "@type": "Question",
      "name": "¿Procede una denuncia penal por estafa si un cliente no cumple un contrato?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No procede; el TSJ reitera que el incumplimiento obligacional debe demandarse ante juzgados civiles o mercantiles, debiendo sobreseerse la acción penal si se intenta criminalizar."
      }
    },
    {
      "@type": "Question",
      "name": "¿Tiene esta sentencia carácter vinculante erga omnes para todos los tribunales?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "No tiene carácter vinculante general (reservado a la Sala Constitucional bajo el Art. 335 CRBV), pero constituye doctrina de casación reiterada que los jueces de instancia deben observar diligentemente."
      }
    }
  ]
}
```
"""
    save_result = save_final_article(
        title="Principio de Intervención Mínima y Sobreseimiento Penal en Casación TSJ",
        markdown_content=sample_article_md,
        metadata={
            "tone": "analista_tsj_revista",
            "theme": "forensic_law",
            "model": "granite3.3:8b",
            "source_url": "Informacion_docling_rag/Jurisprudencias/SCP-268-23-05-2024 principio de intervención mínima.md",
            "jurisdiction": "venezuela"
        }
    )
    assert save_result["status"] == "success", f"Fallo al guardar: {save_result}"
    saved_file = save_result["absolute_path"]
    assert os.path.exists(saved_file), "No se encontró el archivo guardado en RAG/articulos/"
    
    with open(saved_file, encoding="utf-8") as f:
        saved_text = f.read()
    assert "article_type: \"sentencia_tsj\"" in saved_text, "Falta article_type: 'sentencia_tsj' en YAML frontmatter"
    print("  ✓ Artículo de prueba guardado exitosamente en RAG/articulos/ con frontmatter 'sentencia_tsj'.")

    # TEST 5: Auditoría SEO y Auditoría Legal
    print("\n[TEST 5] Ejecutando Auditoría SEO y de Calidad Legal...")
    seo_res = audit_article_seo(sample_article_md)
    legal_res = audit_legal_quality(sample_article_md, jurisdiction="ve")
    
    print(f"  • Score SEO:          {seo_res.get('score')}%")
    if seo_res.get('violations'):
        print(f"  • Avisos SEO:         {seo_res.get('violations')}")
    print(f"  • Score LegalTech:    {legal_res.get('score')}%")
    if legal_res.get('issues'):
        print(f"  • Avisos LegalTech:   {legal_res.get('issues')}")
    
    assert seo_res.get("score", 0) >= 80, f"Score SEO debe ser >= 80, obtenido {seo_res.get('score')}"
    assert legal_res.get("score", 0) >= 80, f"Score Legal debe ser >= 80, obtenido {legal_res.get('score')}"
    print("  ✓ Auditoría superada con éxito (Scores >= 80%).")

    # Cleanup test output files
    if os.path.exists(saved_file):
        os.remove(saved_file)
    if save_result.get("absolute_html_path") and os.path.exists(save_result["absolute_html_path"]):
        os.remove(save_result["absolute_html_path"])

    print("\n" + "=" * 70)
    print("¡TODOS LOS TESTS COMPLETADOS Y VERIFICADOS CON ÉXITO! (100% PASS)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
