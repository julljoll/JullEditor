"""
Generador de Prompts para Artículos de Blog Técnicos, Legales y Cyber-Legal.
Formato canónico SEO Blog PDF + estándares Top Blogs 2026.
"""

from __future__ import annotations

from backend.legal_profiles import (
    JURISDICTION_LABELS,
    PERSONAS,
    build_persona_block,
    is_legal_persona,
    resolve_jurisdiction,
)
from backend.prompts.base import (
    MAGAZINE_INTERPRETATIVE_BLOCK,
    SYSTEM_BASE_PROMPT,
    THEMATIC_PROMPTS,
    THEMATIC_PROMPTS_NEUTRAL,
)


def build_generation_prompt(
    article_source_text: str,
    source_title: str = "",
    source_url: str = "",
    source_lang: str = "",
    source_author: str = "",
    source_date: str = "",
    source_section: str = "",
    theme: str = "cybersecurity",
    tone: str = "conversational",
    target_words: int = 1000,
    custom_instructions: str = "",
    legal_rag_context: str = "",
    jurisdiction: str = "auto",
    editorial_mode: str = "magazine",
) -> str:
    """Construye el prompt completo en español para alimentar al modelo IBM Granite,

    siguiendo estrictamente el FORMATO SEO BLOG PDF con control de palabras,
    corpus legal RAG local (si aplica según jurisdicción),
    traducción y resumen práctico del enlace original, y derechos de autor al final.
    Incluye metadatos enriquecidos del scraper para Schema.org y E-E-A-T.
    """
    query_str = f"{source_title} {article_source_text} {custom_instructions}".lower()
    jcode = resolve_jurisdiction(
        jurisdiction=jurisdiction,
        text=query_str,
        theme=theme,
        persona=tone,
        has_ve_rag=bool(legal_rag_context),
    )
    wants_ve = jcode == "ve"
    wants_co = jcode == "co"

    if wants_ve:
        theme_instruction = THEMATIC_PROMPTS.get(theme, THEMATIC_PROMPTS["cybersecurity"])
    else:
        theme_instruction = THEMATIC_PROMPTS_NEUTRAL.get(theme, THEMATIC_PROMPTS_NEUTRAL["cybersecurity"])

    jurisdiction_label = JURISDICTION_LABELS[jcode]

    if wants_ve:
        jurisdiction_directive = """- Jurisdicción Primaria: República Bolivariana de Venezuela (Corpus Informacion_docling_rag).
- Sección Legal Obligatoria: ## ⚖️ Marco Legal e Institucional Aplicable en Venezuela {#marco-legal} (citando únicamente leyes reales del corpus autorizado).
- Sección Prospectiva Obligatoria: ## 🔬 Análisis de Compatibilidad y Prospectiva Tecnológica en Venezuela {#compatibilidad}."""
    elif wants_co:
        jurisdiction_directive = """- Jurisdicción Primaria: República de Colombia (idioma es-CO).
- Sección Legal Obligatoria: ## ⚖️ Marco Legal e Institucional Aplicable en Colombia {#marco-legal} (citando únicamente las normas autorizadas del perfil; si necesitas un artículo o una sentencia que no conste, no inventes número).
- Sección Prospectiva Obligatoria: ## 🔬 Análisis de Impacto y Prospectiva en Colombia {#impacto-colombia}.
- REGLA: Las sentencias se citan con tipo, número, año y órgano (p. ej. Corte Constitucional, Sentencia T-xxx de aaaa) SOLO si constan en el contexto."""
    else:
        jurisdiction_directive = """- Jurisdicción Primaria: Internacional y Estándares Globales (ISO/IEC, NIST, Regulaciones UE/Globales según la fuente original).
- Sección Regulatoria Obligatoria: ## 🌐 Marco Regulatorio y Estándares Internacionales Aplicables (ISO / NIST / UE) {#marco-regulatorio}.
- Sección Prospectiva Obligatoria: ## 🔬 Análisis de Adopción e Impacto Tecnológico Global {#impacto-tecnologico}.
- REGLA: No forzar menciones a leyes locales de un país específico a menos que la fuente original las mencione explícitamente."""

    tone_descriptions = {
        "jull": "Tono Jull (Español Venezolano Técnico-Científico Simple): Redacción en un tono simple en español venezolano, diáfano, directo, pedagógico y cercano, pero con máxima rigurosidad profesional, pericial, técnica y científica. Emplea giros idiomáticos naturales del español venezolano culto aplicados a la informática forense, ciberseguridad, IA y derecho digital, explicando conceptos complejos con total simplicidad y claridad meridiana sin perder rigor científico.",
        "jull_explicativo": "Tono Jull (Español Venezolano Explicativo y Claro): Redacción en un tono diáfano, pedagógico, cercano y transparente en español venezolano culto. Se enfoca en explicar con total nitidez y simplicidad la idea general y el fondo práctico de la fuente original, desglosando conceptos complejos en un lenguaje accesible y fácil de asimilar para directores, profesionales y público general, sin perder el rigor técnico, normativo ni la fidelidad a los hechos.",
        "conversational": "Conversacional, amigable, directo, profesional pero cálido (como hablar con un colega especialista que explica con total claridad).",
        "analytical": "Analítico pericial, metódico, apoyado en evidencia técnica, doctrina jurídica y razonamiento lógico.",
        "didactic": "Didáctico y pedagógico, con analogías cotidianas, ideal para rápida comprensión por cualquier usuario.",
        "executive": "Ejecutivo y directivo, orientado a la toma de decisiones, gestión de riesgos legales y gobernanza tecnológica.",
        "revista_cientifica_law_tech": "Revista Científica Arbitrada (Derecho & Computación Forense — Nivel Universidad / Postgrado). Máximo rigor dogmático, pericial y metodológico con abstract estructurado bilingüe, referencias APA 7ª y Schema.org ScholarlyArticle.",
    }
    selected_tone = tone_descriptions.get(tone, tone_descriptions["conversational"])

    persona_block = ""
    if is_legal_persona(tone):
        persona_def = PERSONAS[tone]
        selected_tone = f"{persona_def['label']}: {persona_def['register']}"
        persona_block = build_persona_block(tone, jcode, query_str[:3000])

    academic_specific_structure = ""
    if tone == "revista_cientifica_law_tech":
        academic_specific_structure = """
DIRECTRICES ESPECÍFICAS DE REVISTA CIENTÍFICA ARBITRADA (LAW & TECH REVIEW):
- **Estructura Académica Formal de Universidad/Postgrado:**
  • **Título Académico Bilingüe:** 
    `# [TÍTULO CIENTÍFICO EN ESPAÑOL DE 8-12 PALABRAS CON LA PALABRA CLAVE PRIMARIA]`
    `### *[Scientific Title in English: Formal Academic Translation for International Indexing]*`
  • **Meta Descripción CTR:** 145 a 160 caracteres contigua bajo el título.
  • **Cinta de Indexación:** Palabra Clave Primaria | Keywords LSI | Descriptores UNESCO / Tesauro Jurídico | Jurisdicción: Venezuela 🇻🇪 | Cita Sugerida: Revista Arbitrada de Derecho & Ciberseguridad.
  • **Resumen Estructurado (Abstract Bilingüe Obligatorio):**
    `> **📋 RESUMEN ESTRUCTURADO (ABSTRACT):**`
    `> - **Objetivo / Problema Jurídico:** [Planteamiento del conflicto técnico-legal analizado].`
    `> - **Metodología / Marco Doctrinal:** [Cruce de normativas venezolanas, normas ISO/NIST y cadena de custodia].`
    `> - **Resultados / Hallazgos Periciales:** [Comprobación de autenticidad, riesgos procesales o validez de cláusulas].`
    `> - **Conclusiones Doctrinales:** [Dictamen pericial aplicable al ejercicio pericial y litigio].`
    `> `
    `> **Palabras Clave:** [5 descriptores formales en español]`
    `> **Keywords (EN):** [5 keywords correspondientes en inglés]`
  • **Párrafo GEO 2026 de Respuesta Directa (Answer-First):** Párrafo autocontenido de 40 a 60 palabras exactas inmediatamente bajo el abstract, respondiendo directamente a la cuestión central antes de la Tabla de Contenidos.
  • **Cajas de Entrada Rápida:** `> **⚡ RESUMEN EJECUTIVO EN 30 SEGUNDOS (PARA ABOGADOS Y PERITOS):**` y `> **📌 SÍNTESIS FIDEDIGNA DE LA FUENTE ORIGINAL:**`.
  • **Cuerpo Canónico con Secciones Numeradas con anclas {#slug}:**
    1. `## 1. Introducción y Estado del Arte (State of the Art) {#introduccion}`
    2. `## 2. Marco Normativo y Doctrinal Venezolano Aplicable {#marco-normativo}` (CRBV Arts. 28, 49, 60, 110; Ley Especial contra los Delitos Informáticos G.O. 37.313; Ley sobre Mensajes de Datos y Firmas Electrónicas G.O. 37.148; Ley de Infogobierno).
    3. `## 3. Discusión Técnico-Forense y Protocolos de Ciberseguridad {#discusion-forense}` (Metodología RFC 3227, ISO/IEC 27037, cálculo y verificación de hash SHA-256 e imagen bit a bit, fases del Manual Único de Cadena de Custodia MP/CICPC 2017).
    4. `## 4. Análisis Jurisprudencial del TSJ y Contratación Electrónica {#analisis-jurisprudencial}` (Criterios vinculantes de salas del TSJ sobre prueba electrónica, y cláusulas de confidencialidad y validez contractual electrónica).
    5. `## 5. Compatibilidad y Viabilidad Tecnológica en Venezuela {#compatibilidad-venezuela}` (Infraestructura, conectividad, acreditación pericial SUSCERTE y gobernanza CNTI).
    6. `## 6. Conclusiones y Recomendaciones Deontológicas {#conclusiones}` (Dictamen pericial y deberes éticos del abogado).
    7. `## 7. Preguntas Frecuentes Jurídico-Técnicas (FAQ) {#faq}` (3 preguntas P/R).
    8. `## 8. Referencias Bibliográficas y Normativas (Normas APA 7ª Edición / ISO 690) {#referencias}` (Citas formales de Gacetas Oficiales, leyes, sentencias del TSJ y estándares ISO/NIST).
  • **Doble Bloque Schema.org JSON-LD:** Primer bloque con `@type: "ScholarlyArticle"` (con `about`, `audience: Abogados y Peritos`, `educationalLevel: Postgrado`) y segundo bloque `@type: "FAQPage"`.
"""

    jull_specific_structure = ""
    if tone in ("jull", "jull_explicativo"):
        if tone == "jull":
            voice_style = """- **Voz y Estilo Editorial (Técnico-Científico):**
  • Emplea un español venezolano culto, diáfano, pedagógico y directo. Transmite conceptos científicos, forenses y jurídicos con palabras precisas y directas ("en nuestra práctica pericial", "en el contexto tecnológico", "de forma diáfana"). Cero vulgarismos; máxima elegancia técnica, pericial y científica."""
        else:
            voice_style = """- **Voz y Estilo Editorial (Explicativo y Claro):**
  • Emplea un español venezolano culto, sumamente claro, cercano, ilustrativo y pedagógico. Su objetivo primordial es **explicar la idea general y el valor práctico del artículo de forma cristalina**, desmenuzando tecnicismos complejos en explicaciones directas, fluidas y comprensibles para cualquier lector ("vamos a explicar esto con total claridad", "en términos sencillos", "la idea fundamental detrás de esto").
  • Refuerza las analogías prácticas, la relación causa-efecto y la síntesis conceptual en cada sección, manteniendo intacta la fidelidad a los datos de la fuente."""

        legal_close = "Marco Legal Venezolano" if wants_ve else ("Marco Legal Colombiano" if wants_co else "Marco Regulatorio y Estándares Globales")
        jull_specific_structure = f"""
DIRECTRICES ESPECÍFICAS DE ESTRUCTURA Y TONO JULL (WIREFRAME EDITORIAL EXACTO):
{voice_style}
- **Distribución Exacta de Párrafos y Palabras por Sección (Esquema del Documento):**
  • **Título H1:** Impactante, en mayúsculas o estilo titular, de 8 a 12 palabras (50-65 caracteres) incorporando la palabra clave primaria repetida.
  • **Meta Descripción:** 145 a 160 caracteres contigua bajo el H1 con intención de búsqueda y llamada a la acción.
  • **Respuesta Directa GEO 2026 (Answer-First):** Párrafo autocontenido de 40 a 60 palabras exactas inmediatamente bajo la cinta de metadatos, respondiendo a la pregunta central antes de la Tabla de Contenidos.
  • **Subtítulos H2 como preguntas:** Al menos el 50% de los encabezados H2 formulados como preguntas ("¿Qué es...?", "¿Cómo aplica...?").
  • **Sección 1 (Primer H2 de 5 a 9 palabras):** Desarrolla exactamente 5 párrafos controlados de 3 a 4 oraciones cada uno (45 a 65 palabras por párrafo). Resalta palabras clave esenciales en **negrita** en cada párrafo, incluye un enlace autoritativo e inserta en el 4to/5to párrafo la `**Conclusión del párrafo:** [síntesis directa]`.
  • **Sección 2 (Segundo H2 de 5 a 9 palabras):** Desarrolla exactamente 3 párrafos controlados de 3 a 4 oraciones cada uno (45 a 65 palabras por párrafo), con términos en **negrita**, enlaces y `**Conclusión del párrafo:**`.
  • **Sección 3 (Tercer H2 de 5 a 9 palabras):** Desarrolla exactamente 3 párrafos controlados de 3 a 4 oraciones cada uno (45 a 65 palabras por párrafo), con términos en **negrita**, enlaces y `**Conclusión del párrafo:**`.
  • **Sección 4 (Cuarto H2 de 5 a 9 palabras):** Desarrolla exactamente 4 párrafos controlados de 3 a 4 oraciones cada uno (45 a 65 palabras por párrafo), con términos en **negrita**, enlaces y `**Conclusión del párrafo:**`.
  • **Cajas y Bloques Didácticos:** Incluye `> **📌 Resumen Práctico de la Fuente Original:**`, `> **⚡ Resumen Ejecutivo en 30 Segundos:**` y `> ### 💡 En Palabras Simples`.
  • **Cierre LegalTech & Microdatos:** {legal_close}, FAQ (3 preguntas), Derechos de Autor, Sobre el Autor (E-E-A-T), Conclusión y Debate con CTA, Descargo ético obligatorio («Este contenido es exclusivamente informativo y no constituye asesoría legal...») y doble bloque Schema.org JSON-LD (TechArticle con 15 campos + FAQPage).
"""

    source_url_display = source_url if source_url else "Texto o notas suministradas directamente"
    source_title_display = source_title if source_title else "N/A"

    source_metadata_block = ""
    if source_lang or source_author or source_date or source_section:
        source_metadata_block = "\nMETADATOS EXTRAÍDOS DE LA FUENTE ORIGINAL (para enriquecer Schema.org y atribución E-E-A-T):"
        if source_lang:
            source_metadata_block += f"\n- Idioma de la Fuente: {source_lang}"
        if source_author:
            source_metadata_block += f"\n- Autor de la Fuente Original: {source_author}"
        if source_date:
            source_metadata_block += f"\n- Fecha de Publicación Original: {source_date}"
        if source_section:
            source_metadata_block += f"\n- Sección/Categoría Original: {source_section}"
        source_metadata_block += "\n- Usa estos datos para completar los campos del Schema.org JSON-LD (author, datePublished, articleSection). En la sección de Derechos de Autor, cita al autor original por nombre si está disponible.\n"

    legal_rag_section = ""
    if (wants_ve or wants_co) and legal_rag_context:
        legal_rag_section = f"\n{legal_rag_context}\n"

    magazine_block = MAGAZINE_INTERPRETATIVE_BLOCK if editorial_mode == "magazine" else ""
    magazine_closing_directive = (
        "\n7b. (MODO REVISTA OBLIGATORIO) Inmediatamente tras el resumen ejecutivo, inserta la sección interpretativa: `## 🔎 Nuestra Lectura del Artículo {#nuestra-lectura}` con 2 párrafos explicativos analizando el alcance y la trascendencia práctica de la fuente original."
        if editorial_mode == "magazine" else ""
    )

    prompt = f"""
{SYSTEM_BASE_PROMPT}

{theme_instruction}

{magazine_block}

{jull_specific_structure}

{academic_specific_structure}

{persona_block}

{legal_rag_section}


CONFIGURACIÓN DE LA PUBLICACIÓN:
- Idioma de Redacción: ESPAÑOL ESTRICTO (100% traducido y analizado conceptualmente).
- Tono Requerido: {selected_tone}
- Longitud Objetivo Global: Aproximadamente {target_words} palabras (distribuidas equilibradamente entre todas las secciones).
- Control de Tamaño Específico:
  • Título H1: 8 a 12 palabras (50-65 caracteres) con la palabra clave primaria.
  • Subtítulos H2/H3: 5 a 9 palabras con keywords secundarias.
  • Meta Descripción: 145 a 160 caracteres (22-28 palabras).
  • Párrafos de Desarrollo: 3 a 4 oraciones (45 a 65 palabras por párrafo).
- Jurisdicción Seleccionada: {jurisdiction_label}
{jurisdiction_directive}
- Estructura y Estilo Visual: FORMATO SEO BLOG PDF + ESTÁNDARES TOP BLOGS 2026 (H1 con Keyword + Meta Descripción + Tabla de Contenidos + Answer-First + Resumen Práctico + FAQ Schema + E-E-A-T Author + CTA + Schema.org completo con 15+ campos + FAQPage Schema).
- URL Original de Referencia (Source Link): {source_url_display}
- Título/Tema de Referencia: {source_title_display}
{source_metadata_block}

{f"INSTRUCCIONES PERSONALIZADAS DEL USUARIO: {custom_instructions}" if custom_instructions else ""}

TEXTO FUENTE A ANALIZAR, TRADUCIR Y TRANSFORMAR EDITORIALMENTE:
\"\"\"
{article_source_text}
\"\"\"

INSTRUCCIÓN FINAL (REINTERPRETACIÓN INTEGRAL, MÁXIMA FIDELIDAD, CERO ALUCINACIÓN + FORMATO MARKDOWN ESTRICTO PARA WORDPRESS):
Genera el artículo completo en ESPAÑOL respetando estrictamente el formato MARKDOWN (GitHub Flavored Markdown) para garantizar compatibilidad total y preservación de estilos al copiar a WordPress (Gutenberg):
- **FORMATO MARKDOWN ESTRICTO:** Redacta exclusivamente en Markdown estándar (# para H1, ## para H2, > para callouts, **negrita**, [enlace](url), etc.). Esto permite que al transferir a WordPress se mantenga el 100% de la jerarquía, cajas de resumen, enlaces y diseño visual.
- **REINTERPRETACIÓN PROFUNDA:** Reinterpreta todo el contenido del texto fuente utilizando tus propias palabras y vocabulario técnico en español para evitar duplicados o traducciones literales.
- **FIDELIDAD SEMÁNTICA TOTAL (SIN INVENTAR NADA):** Mantén con absoluta exactitud el sentido original, los hechos, los datos y las conclusiones de la fuente. Está prohibido inventar cifras o afirmaciones que la fuente no contenga.
- **CERO ALUCINACIONES LEGALES:** Cita únicamente normas reales del corpus o de la lista autorizada de la jurisdicción seleccionada. Prohibido inventar leyes, artículos o sentencias.
1. Inicia inmediatamente con el Título H1 (#) de 8-12 palabras con la palabra clave primaria (NUNCA escribas "### Título H1:" ni uses etiquetas; escribe directamente `# [Tu Título Real]`).
2. Coloca inmediatamente debajo del H1 el bloque de Meta Descripción como blockquote: `> **Meta descripción:** [Texto...]` de 145-160 caracteres (NUNCA crees un encabezado `## Meta Descripción`).
3. Inserta la cinta horizontal de metadatos SEO.
4. Redacta inmediatamente el párrafo introductorio GEO ANSWER-FIRST (OBLIGATORIO): redacta exactamente 40 a 60 palabras respondiendo DIRECTAMENTE a la consulta central. Comienza con "En resumen," seguido de la respuesta directa con la keyword en negrita.
5. Inserta la sección `## 📑 Tabla de Contenidos` con enlaces ancla a cada sección H2 del artículo (al menos 50% de los H2 redactados como preguntas directas).
6. Añade la caja `> **📌 Resumen Práctico de la Fuente Original:**` resumiendo con tus propias palabras en español la esencia y tesis del artículo de origen, sin desviar su sentido.
7. Inserta el resumen ejecutivo en 30 segundos (`> **⚡ Resumen Ejecutivo en 30 Segundos:**`).{magazine_closing_directive}
8. Desarrolla cada sección con subtítulos H2 (`## ` de 5-9 palabras; NUNCA uses `###` para las secciones principales; mínimo 50% de los H2 redactados como preguntas directas que un usuario busca en Google: ¿Qué es...?, ¿Cómo funciona...?, etc.) y párrafos breves de 3-4 oraciones (45-65 palabras), manteniendo la cadencia rítmica del PDF. Incluye anclas {{#seccion-slug}} en cada H2.
9. Repite y resalta en **negrita** la palabra clave primaria y secundarias a lo largo de cada sección (`**palabra clave**`).
10. Incluye la `**Conclusión del párrafo:**` al cierre de las secciones clave e inserta al menos 2 enlaces autoritativos oficiales en formato Markdown.
11. Inserta la sección `## ❓ Preguntas Frecuentes (FAQ)` con EXACTAMENTE 3 preguntas y respuestas relevantes al tema (formato P:/R:).
12. Inserta las Referencias y la sección `## ⚖️ Derechos de Autor y Fuente de Origen` reconociendo la fuente original y enlazando `{source_url_display}`.
13. Incluye la sección `## ✍️ Sobre el Autor` con credenciales profesionales y entidad editora (E-E-A-T).
14. Finaliza con `## Conclusión y Debate` invitando a la participación con llamada a la acción (CTA).
15. Inserta OBLIGATORIAMENTE el descargo ético y deontológico (YMYL 2026):
    `> *Descargo ético: Este contenido es exclusivamente informativo y no constituye asesoría legal ni crea una relación abogado-cliente. Cada caso requiere análisis particular por un profesional del derecho.*`
16. Genera obligatoriamente el primer bloque de microdatos Schema.org JSON-LD en un bloque de código ````json ... ```` ({'ScholarlyArticle' if tone == 'revista_cientifica_law_tech' else 'TechArticle'} completo con al menos 15 campos requeridos).
17. Genera obligatoriamente el segundo bloque de microdatos Schema.org JSON-LD en un bloque separado ````json ... ```` con `@type: "FAQPage"` mapeando las 3 preguntas del FAQ.
"""
    return prompt.strip()
