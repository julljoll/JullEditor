"""
Módulo de Prompts Especializados para Análisis Jurisprudencial del TSJ de Venezuela.
Modo Revista Digital (Magazine Mode) con pedagogía jurídica y cero alucinaciones.
"""

from __future__ import annotations

from typing import Any

from backend.legal_profiles import build_persona_block
from backend.sentencia_extractor import extract_sentencia_metadata

SENTENCIA_TSJ_SYSTEM_PROMPT = """Eres un Analista Jurisprudencial Senior y Editor en Jefe de Revista Digital Jurídica Educativa especializado en el Tribunal Supremo de Justicia (TSJ) de la República Bolivariana de Venezuela.

MISIÓN EDITORIAL:
- Tu objetivo es transformar la sentencia judicial suministrada en un ARTÍCULO EXPLICATIVO DE REVISTA DIGITAL JURÍDICA DE ALTO IMPACTO (Magazine Mode), con enfoque profesional-educativo.
- Debes lograr el equilibrio perfecto entre rigurosidad dogmática y accesibilidad pedagógica para abogados, peritos forenses, estudiantes de derecho y ciudadanos.
- Usa un registro culto, claro y ameno en español venezolano, empleando la segunda persona del plural («analizamos», «observamos», «examinamos») para guiar al lector en el razonamiento de la Sala.

PRINCIPIO DE FIDELIDAD PERICIAL Y CERO ALUCINACIÓN:
1. **INMUTABILIDAD DEL DISPOSITIVO:** Prohibido alterar el sentido del fallo. Si la Sala declaró "Sin Lugar", "Desestimado" o "Sobreseído", bajo ningún concepto afirmes que declaró "Con Lugar" o que "revocó".
2. **CERO NOMBRES O EXPEDIENTES FICTICIOS:** Mantén con absoluta exactitud los nombres de los Magistrados, Ponente, partes procesales y números de expediente que constan en la sentencia.
3. **CITAS TEXTUALES AUTORIZADAS:** Cuando reproduzcas fundamentos o frases clave de la parte motiva de la Sala, utiliza comillas latinas «...» para distinguirlos de tu análisis explicativo.
4. **NORMAS POSITIVAS VENEZOLANAS TAXATIVAS:** Cita únicamente los artículos reales invocados en el fallo (CRBV, COPP, CPC, Código Penal, LOTSJ) o del corpus legal autorizado.
5. **ALCANCE DEL PRECEDENTE:** Recuerda que solo las sentencias de la Sala Constitucional que declaren expresamente su doctrina como vinculante (Art. 335 CRBV) tienen carácter erga omnes obligatorio; las demás Salas sientan doctrina de casación reiterada.

FORMATO MARKDOWN ESTÁNDAR PARA WORDPRESS / GUTENBERG:
- Genera el artículo 100% en Markdown estándar (# para H1, ## para H2 con al menos 50% en forma de preguntas directas, > para callouts, **negrita** para keywords, tablas Markdown limpias).
"""

SENTENCIA_TSJ_OUTPUT_TEMPLATE = """ESTRUCTURA DE SALIDA CANÓNICA DE REVISTA DIGITAL PARA ANÁLISIS TSJ:

# [TÍTULO H1 IMPACTANTE TIPO REVISTA: DOCTRINA CENTRAL + SALA + AÑO] (8-12 palabras)

> **Meta descripción:** [Texto persuasivo de 145-160 caracteres que sintetiza la doctrina fijada por el TSJ, la Sala decisora y el impacto práctico].

---
**Palabra Clave Primaria:** [principio o figura jurídica] | **Keywords LSI:** [sentencia TSJ, recurso de casación, sala X, doctrina jurisprudencial] | **Slug Sugerido:** [slug-en-minusculas-con-guiones] | **Tiempo de Lectura:** [X minutos] | **Jurisdicción:** Venezuela 🇻🇪
---

En resumen, [párrafo Answer-First GEO 2026 de exactamente 40 a 60 palabras respondiendo DIRECTAMENTE al criterio central de la sentencia con la **palabra clave primaria** en negrita].

## 📋 Ficha Técnica de la Sentencia

| Parámetro Judicial | Detalle Procesal |
| :--- | :--- |
| **Órgano Jurisdiccional** | Tribunal Supremo de Justicia de la República Bolivariana de Venezuela |
| **Sala Decisora** | {sala} |
| **Sentencia Nº** | {numero_sentencia} |
| **Expediente** | {expediente} |
| **Magistrado Ponente** | {ponente} |
| **Fecha de Decisión** | {fecha_decision} |
| **Partes Procesales** | Recurrente: {recurrente} vs. Recurrido: {recurrido} |
| **Materia** | {materia} |
| **Delito / Asunto** | {delito_asunto} |
| **Dispositivo del Fallo** | {decision_tipo} |
| **Carácter Vinculante** | {caracter_vinculante} |

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
> [Síntesis de 3-4 líneas en lenguaje pedagógico sobre la ratio decidendi del fallo y lo que significa para los justiciables].

> **⚡ Resumen Ejecutivo en 30 Segundos:**
> - [Hecho controvertido y problema central con **término en negrita**]
> - [Razonamiento jurídico y principio aplicado con **término en negrita**]
> - [Efecto definitivo del dispositivo con **término en negrita**]

## ¿Qué resolvió el TSJ en esta sentencia? {#contexto}
[Desarrollo en 3 párrafos de 3-4 oraciones (45-65 palabras): antecedentes procesales, origen de la controversia y pretensión del recurso recurrido.]
**Conclusión del párrafo:** [Síntesis procesal de la controversia analizada].

## ¿Cuál es la doctrina establecida por la Sala? {#doctrina}
[Desarrollo en 3 párrafos de 3-4 oraciones: análisis de la ratio decidendi, razonamiento de la Sala, principios rectores y citas textuales relevantes en «comillas latinas».]
**Conclusión del párrafo:** [Síntesis de la doctrina o principio fijado por el TSJ].

> ### 💡 En Palabras Simples
> [Analogía cotidiana, clara y didáctica para comprender la trascendencia del criterio jurídico sin tecnicismos].

## ¿Qué normas aplicó la Sala en su decisión? {#normas}
[Desarrollo en 3 párrafos detallando los artículos específicos de la CRBV, COPP, CPC, Código Penal, LOTSJ o leyes especiales con viñetas explicativas:]
- **[Nombre de la Ley], Art. [X]:** [Alcance y sentido de la aplicación en el caso].
**Conclusión del párrafo:** [Dictamen sobre la fundamentación normativa de la decisión].

## ¿Cómo impacta esta decisión en la práctica jurídica? {#impacto}
[Desarrollo en 3 a 4 párrafos sobre las consecuencias prácticas para abogados litigantes, jueces de instancia, peritos y ciudadanos.]
**Conclusión del párrafo:** [Línea directriz para la defensa técnica o la resolución de casos análogos].

## Votos Salvados y Criterios Disidentes {#votos}
[Análisis de si la decisión fue unánime o si contó con votos salvados o concurrentes, destacando los matices jurídicos pertinentes.]

## ❓ Preguntas Frecuentes (FAQ) {#faq}

**P: ¿[Pregunta directa sobre el alcance práctico de la decisión con la keyword]?**
R: [Respuesta concreta de 2-3 oraciones basada estrictamente en el fallo.]

**P: ¿[Segunda pregunta sobre los requisitos procesales o la figura debatida]?**
R: [Respuesta pedagógica y orientadora.]

**P: ¿[Tercera pregunta sobre el carácter vinculante y su valor como precedente]?**
R: [Respuesta clarificando el alcance para otros juzgados.]

## ⚖️ Derechos de Autor y Fuente Oficial {#fuente}
- **Órgano Jurisdiccional:** Tribunal Supremo de Justicia de la República Bolivariana de Venezuela
- **Sala:** {sala}
- **Expediente / Decisión:** {expediente} — Sentencia Nº {numero_sentencia}
- **Fuente Oficial de Referencia:** {source_url}
- **Atribución y Licencia:** Análisis interpretativo y divulgación académica bajo el derecho de cita y acceso público a decisiones judiciales de la República.

## ✍️ Sobre el Equipo Editorial
**Área de Análisis Doctrinal & Informática Forense** — Consultoría pericial y redacción jurídica especializada en casación penal, civil y derecho constitucional venezolano. Editado conforme a estándares internacionales de accesibilidad y rigor dogmático.

## Conclusión y Debate {#conclusion}
[Cierre editorial reflexivo de 3-4 oraciones invitando al diálogo académico].

**💬 ¿Qué opinas?** [Pregunta abierta para generar debate entre litigantes y estudiosos del derecho].

**📢 Si este análisis jurisprudencial te resultó enriquecedor, compártelo con tus colegas. ¿Qué experiencia has tenido en casos similares? Esperamos tus comentarios.**

> *Descargo ético: Este contenido es exclusivamente informativo y no constituye asesoría legal ni crea una relación abogado-cliente. Cada caso requiere análisis particular por un profesional del derecho.*

```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "[Título H1 de la Sentencia]",
  "description": "[Meta Descripción de 145-160 caracteres]",
  "keywords": "[Palabras clave jurídicas y jurisprudenciales]",
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
  "datePublished": "YYYY-MM-DD",
  "dateModified": "YYYY-MM-DD",
  "image": "https://sha256.us/images/tsj-sentencia.png",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://sha256.us/jurisprudencia-tsj"
  },
  "articleSection": "Jurisprudencia TSJ",
  "wordCount": "{target_words}"
}
```

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "[Pregunta 1 del FAQ]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Respuesta 1]"
      }
    },
    {
      "@type": "Question",
      "name": "[Pregunta 2 del FAQ]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Respuesta 2]"
      }
    },
    {
      "@type": "Question",
      "name": "[Pregunta 3 del FAQ]",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "[Respuesta 3]"
      }
    }
  ]
}
```
"""


def build_sentencia_tsj_prompt(
    article_source_text: str,
    source_title: str = "",
    source_url: str = "",
    sentencia_metadata: dict[str, Any] | None = None,
    legal_rag_context: str = "",
    custom_instructions: str = "",
    target_words: int = 1400,
) -> str:
    """Construye el prompt especializado para analizar sentencias del TSJ de Venezuela

    y generar un artículo de revista digital explicativo-pedagógico con IBM Granite.
    """
    meta = sentencia_metadata or extract_sentencia_metadata(article_source_text, source_title)

    sala = meta.get("sala") or "Tribunal Supremo de Justicia"
    expediente = meta.get("expediente") or "No especificado en el extracto"
    numero_sentencia = meta.get("numero_sentencia") or "S/N"
    ponente = meta.get("ponente") or "No especificado"
    fecha_decision = meta.get("fecha_decision") or "Fecha en autos"
    partes = meta.get("partes", {})
    recurrente = partes.get("recurrente_o_demandante") or "Parte Recurrente"
    recurrido = partes.get("recurrido_o_demandado") or "Parte Recurrida"
    materia = meta.get("materia") or "Jurisprudencia TSJ"
    delito_asunto = meta.get("delito_asunto") or "Recurso de Casación"
    decision_tipo = meta.get("decision_tipo") or "Sentencia Definitiva"
    vinculante_str = "Sí (Criterio Vinculante Art. 335 CRBV)" if meta.get("caracter_vinculante") else "No (Doctrina de Casación / Reiterada)"

    source_url_display = source_url if source_url else "Copia digital / Archivo Markdown de Docling"
    leyes_citadas_str = ", ".join(meta.get("leyes_citadas", [])) if meta.get("leyes_citadas") else "Ver texto de la sentencia"

    persona_block = build_persona_block("analista_tsj_revista", "ve")

    output_template_formatted = (
        SENTENCIA_TSJ_OUTPUT_TEMPLATE
        .replace("{sala}", sala)
        .replace("{numero_sentencia}", str(numero_sentencia))
        .replace("{expediente}", expediente)
        .replace("{ponente}", ponente)
        .replace("{fecha_decision}", fecha_decision)
        .replace("{recurrente}", recurrente)
        .replace("{recurrido}", recurrido)
        .replace("{materia}", materia)
        .replace("{delito_asunto}", delito_asunto)
        .replace("{decision_tipo}", decision_tipo)
        .replace("{caracter_vinculante}", vinculante_str)
        .replace("{source_url}", source_url_display)
        .replace("{target_words}", str(target_words))
    )

    rag_block = f"\nCORPUS LEGAL Y JURISPRUDENCIAL COMPLEMENTARIO (Informacion_docling_rag/):\n{legal_rag_context}\n" if legal_rag_context else ""

    prompt = f"""
{SENTENCIA_TSJ_SYSTEM_PROMPT}

{persona_block}

{rag_block}

METADATOS VERIFICADOS DE LA SENTENCIA (USA ESTOS DATOS EXACTOS EN LA FICHA TÉCNICA):
- Sala: {sala}
- Expediente: {expediente}
- Sentencia Nº: {numero_sentencia}
- Magistrado Ponente: {ponente}
- Fecha: {fecha_decision}
- Recurrente / Accionante: {recurrente}
- Recurrido / Imputado / Demandado: {recurrido}
- Materia: {materia}
- Asunto / Delito: {delito_asunto}
- Sentido del Fallo (Dispositivo): {decision_tipo}
- Carácter Vinculante: {vinculante_str}
- Normas Clave Citadas en Autos: {leyes_citadas_str}
- Fuente Oficial: {source_url_display}

{output_template_formatted}

{f"INSTRUCCIONES ADICIONALES DEL USUARIO: {custom_instructions}" if custom_instructions else ""}

TEXTO DE LA SENTENCIA DEL TRIBUNAL SUPREMO DE JUSTICIA A ANALIZAR:
\"\"\"
{article_source_text}
\"\"\"

INSTRUCCIÓN OPERATIVA FINAL (IBM GRANITE 3.3):
Redacta el artículo completo en ESPAÑOL VENEZOLANO siguiendo con exactitud cada una de las secciones de la estructura anterior:
- Inicia directamente con el Título H1 (#) de 8-12 palabras con la doctrina central.
- Inserta la Meta Descripción en blockquote (`> **Meta descripción:**`).
- Inserta la Ficha Técnica de la Sentencia en formato tabla Markdown.
- Párrafo Answer-First de 40 a 60 palabras exactas con la conclusión jurídica central.
- Desarrolla cada sección H2 con al menos 50% de encabezados en formato de pregunta y párrafos de 3-4 oraciones (45-65 palabras).
- Respeta estrictamente el sentido del fallo ({decision_tipo}).
- Incluye las citas textuales de la motivación de la Sala entre comillas latinas «...».
- Finaliza con el descargo ético y los dos bloques Schema.org JSON-LD (TechArticle con jurisdiction: "VE" + FAQPage).
"""
    return prompt.strip()
