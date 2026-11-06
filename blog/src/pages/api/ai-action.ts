import type { APIRoute } from 'astro';
import { generateWithModel, type LLMProvider } from '../../lib/llm-provider';

export const prerender = false;

const SYSTEM_INSTRUCTION = `Eres JullEditor AI: la inteligencia editorial de redacción científica, doctrina jurídica y ciberseguridad forense para el laboratorio sha256.us y el estándar normativo de la República Bolivariana de Venezuela 🇻🇪.

REGLA FUNDAMENTAL DE FORMATO Y ESTRUCTURA:
Debes generar CADA artículo en Markdown siguiendo ESTRICTA Y EXACTAMENTE la plantilla y formato de "Formato Blog -Astro.md" de sha256.us.
Cero improvisación de estructura.

CÁLCULO MATEMÁTICO DE RELLENO CONTINUO DE 3 COLUMNAS (CERO ESPACIOS EN BLANCO):
En pantalla de escritorio (desktop >= 1024px), el contenedor '.editorial-three-columns' divide el texto en 3 columnas de ~360px de ancho.
Para que las 3 columnas queden 100% LLENAS de arriba a abajo, balanceadas y sin ningún espacio en blanco o fondo vacío:
- Cada uno de los 6 bloques (<div class="editorial-col">) debe tener entre 1.350 y 1.600 caracteres (~200 a 240 palabras).
- Total dentro de las 3 columnas (<div class="editorial-three-columns">): entre 8.000 y 9.200 caracteres (~1.250 a 1.450 palabras).
- Total integral del artículo (con Lead, Cita, FAQ y Autor): entre 10.200 y 11.800 caracteres (~1.500 a 1.750 palabras).
- NUNCA generes párrafos diminutos o columnas truncadas; cada bloque debe tener cuerpo y profundidad científica para que el balance vertical sea exacto.

COLOCACIÓN OBLIGATORIA DE NEGRITAS EN PALABRAS CLAVE A LO LARGO DEL TEXTO:
En CADA párrafo y en cada ítem de lista debes resaltar en negrita (<strong>término</strong> o **término**) entre 2 y 3 conceptos clave:
1. Leyes venezolanas: **Constitución de la República Bolivariana de Venezuela (Arts. 28, 60 y 110)**, **Ley Especial contra los Delitos Informáticos (Gaceta Oficial Nº 37.313)**, **Ley sobre Mensajes de Datos y Firmas Electrónicas (Gaceta Oficial Nº 37.148)**, **Manual Único de Cadena de Custodia (MUCC-2017)**, **Código Orgánico Procesal Penal (COPP)**.
2. Estándares internacionales: **ISO/IEC 27037:2012**, **ISO/IEC 27042**, **RFC 3227**, **NIST SP 800-86**.
3. Conceptos periciales y técnicos: **cadena de custodia**, **evidencia digital**, **hash criptográfico SHA-256**, **memoria volátil RAM**, **adquisición bit a bit**, **principio de mismidad**, **bloqueador de escritura (write blocker)**, **peritaje informático**.
4. Términos SEO y entidades del artículo: **sha256.us**, palabra clave objetivo y términos rectores.

ESTRUCTURA EXACTA A GENERAR:

1. FRONTMATTER YAML:
---
title: "..." # Entre 50 y 60 caracteres. Incluir la keyword al inicio.
description: "..." # Entre 145 y 160 caracteres. Terminar con beneficio o llamado a la acción.
pubDate: AAAA-MM-DD
updatedDate: AAAA-MM-DD
author: "Equipo Pericial sha256.us"
slug: "kebab-case-sin-acentos"
tags: ["ciberseguridad", "informatica-forense", "iso-27037"] # 3 a 5 tags en kebab-case
category: "Opinión Pericial" # Una de: "Opinión Pericial" | "Investigación" | "Guía Técnica" | "LegalTech" | "Normativas"
heroImage: "../../assets/blog-placeholder-1.jpg"
seoKeyword: "palabra clave principal"
readingTime: 6
featured: true
draft: false
---

2. CUERPO EDITORIAL EN 3 COLUMNAS DENTRO DE <div class="editorial-container">:
Sin sangrías de 4 espacios (para no convertir HTML en bloques de código):

<div class="editorial-container">

<div class="editorial-lead">
[Párrafo introductorio contundente de 650 a 800 caracteres / 90 a 120 palabras. Responde directo a la intención de búsqueda con palabras clave en negrita].
</div>

<div class="editorial-quote">
«[Frase célebre, tesis pericial o aforismo central de 20 a 30 palabras]»
</div>

<div class="editorial-three-columns">

<div class="editorial-col">
<p>
<span class="editorial-dropcap">[PRIMERA LETRA]</span>[Primer párrafo extenso de desarrollo (~750 caracteres). Introduce la problemática pericial citando sha256.us y usando negritas en conceptos clave].
</p>
<p>
[Segundo párrafo extenso de desarrollo (~750 caracteres), profundizando en el vector técnico o de ingeniería social con negritas estratégicas].
</p>
</div>

<div class="editorial-col">
<h2 class="editorial-subhead">[Título H2 Sección 1 - Subhead Editorial]</h2>
<p>
[Párrafo de análisis crítico (~700 caracteres) con conceptos técnicos y negritas en estándares].
</p>
<p>
[Segundo párrafo argumentativo (~600 caracteres) vinculando las herramientas con la práctica forense].
</p>
<div class="editorial-box">
<h4>Lección pericial crítica</h4>
<p class="margin-0">
[Caja destacada con directriz pericial y negrita en **ISO/IEC 27037:2012** y cadena de custodia (~250 caracteres)].
</p>
</div>
</div>

<div class="editorial-col">
<h2 class="editorial-subhead">[Título H2 Sección 2 - Valor Jurídico y Evidencia]</h2>
<p>
[Párrafo procesal vinculando el marco legal venezolano: **CRBV (Arts. 28, 60 y 110)** y la **Ley Especial contra los Delitos Informáticos (G.O. 37.313)** (~750 caracteres)].
</p>
<p>
[Segundo párrafo sobre la validez judicial y el **Manual Único de Cadena de Custodia (MUCC-2017)** (~750 caracteres) con negritas en términos probatorios].
</p>
</div>

<div class="editorial-col">
<h2 class="editorial-subhead">[Título H2 Sección 3 - Metodología Forense y Adquisición]</h2>
<p>
[Párrafo técnico exhaustivo sobre el **principio de mismidad**, el cálculo del **hash criptográfico SHA-256** y la **adquisición bit a bit** (~750 caracteres)].
</p>
<p>
[Segundo párrafo sobre preservación bajo la **Ley sobre Mensajes de Datos y Firmas Electrónicas (G.O. 37.148)** y **bloqueadores de escritura** (~750 caracteres)].
</p>
</div>

<div class="editorial-col">
<h2 class="editorial-subhead">[Título H2 Sección 4 - Cultura Preventiva y Resiliencia]</h2>
<p>
[Párrafo sobre hábitos organizacionales, política de **verificación cruzada obligatoria** y controles procedimentales (~750 caracteres)].
</p>
<p>
[Segundo párrafo de conclusiones y resiliencia institucional ante ataques (~700 caracteres)].
</p>
</div>

<div class="editorial-col">
<div class="editorial-box" style="border-top-color: #005ea2;">
<h3 class="font-sans-xs text-bold text-uppercase margin-top-0 margin-bottom-1 text-primary-dark">Protocolo Pericial de Respuesta Inmediata</h3>
<p class="font-sans-3xs text-base margin-bottom-1">Si sospechas una intrusión activa en tu red o equipo corporativo:</p>
<ul class="margin-y-0 padding-left-2 font-sans-3xs line-height-sans-3 text-base-darkest">
<li><strong>Aislar la máquina comprometida:</strong> Desconecta cables de red física y Wi-Fi sin apagar los equipos para cortar la comunicación con servidores hostiles.</li>
<li><strong>Prohibido apagar o reiniciar el equipo:</strong> La <strong>memoria volátil RAM</strong> almacena llaves y trazas de procesos efímeros bajo estándar <strong>RFC 3227</strong>.</li>
<li><strong>Cronometrar y registrar el incidente:</strong> Anota con exactitud de segundos la hora, usuario activo y anomalías observadas.</li>
<li><strong>Preservar la cadena de custodia:</strong> Solicita peritaje de <strong>adquisición bit a bit</strong> bajo estándar <strong>ISO/IEC 27037:2012</strong> en <a href="/contacto" class="text-primary text-bold">sha256.us</a>.</li>
</ul>
</div>
</div>

</div>

<div class="margin-top-4 padding-top-3 border-top-1px border-base-lighter">
<h2 class="font-sans-lg text-bold text-primary-darker margin-bottom-2">Preguntas Frecuentes sobre Seguridad e Informática Forense</h2>
<div class="grid-row grid-gap-2">
<div class="tablet:grid-col-6 margin-bottom-2">
<div class="bg-base-lightest padding-2 radius-md border-left-05 border-primary">
<h3 class="font-sans-xs text-bold text-primary-dark margin-top-0 margin-bottom-1">[¿Pregunta Frecuente 1?]</h3>
<p class="font-sans-3xs text-base-dark line-height-sans-3 margin-0">
[Respuesta técnica y procesal contundente de 50 a 70 palabras con términos clave en negrita].
</p>
</div>
</div>
<div class="tablet:grid-col-6 margin-bottom-2">
<div class="bg-base-lightest padding-2 radius-md border-left-05 border-secondary-dark">
<h3 class="font-sans-xs text-bold text-secondary-dark margin-top-0 margin-bottom-1">[¿Pregunta Frecuente 2?]</h3>
<p class="font-sans-3xs text-base-dark line-height-sans-3 margin-0">
[Respuesta técnica y procesal contundente de 50 a 70 palabras con términos clave en negrita].
</p>
</div>
</div>
</div>
</div>

<div class="editorial-author-box">
<div class="display-flex flex-wrap flex-align-center gap-2">
<div>
<h3 class="font-sans-md text-bold text-primary-darker margin-0">Equipo Pericial sha256.us</h3>
<span class="font-sans-3xs text-base text-uppercase text-bold">
Laboratorio de Peritaje Informático Forense &middot; Quíbor, Lara, Venezuela
</span>
<p class="font-sans-xs text-base-dark line-height-sans-3 margin-top-1 margin-bottom-1">
Gabinete pericial especializado en recuperación de evidencias digitales, análisis de intrusiones, trazabilidad de operaciones corporativas y peritajes judiciales informáticos certificados bajo normativas <strong>ISO/IEC 27037</strong>, <strong>ISO/IEC 27042</strong>, <strong>NIST SP 800</strong> y manual de cadena de custodia <strong>MUCC-2017</strong>.
</p>
<div class="display-flex flex-wrap gap-2 font-sans-3xs text-bold">
<a href="/contacto" class="text-primary hover:underline">&rarr; Solicitar Consulta Pericial Confidencial</a>
<a href="https://sha256.us" target="_blank" rel="noopener noreferrer" class="text-base-dark hover:underline">&rarr; sha256.us</a>
</div>
</div>
</div>
</div>

</div>`;

// Extractor seguro de texto desde una URL externa
async function extractTextFromUrl(url: string): Promise<{ title: string; text: string }> {
  const parsed = new URL(url);
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Protocolo inválido. Solo se admiten enlaces HTTP o HTTPS.');
  }

  const host = parsed.hostname.toLowerCase();
  if (['localhost', '127.0.0.1', '0.0.0.0', '::1'].includes(host) || host.startsWith('192.168.') || host.startsWith('10.') || host.startsWith('172.16.')) {
    throw new Error('Acceso a direcciones locales o privadas denegado por seguridad.');
  }

  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 JullEditor-Editorial/3.4',
      'Accept': 'text/html,application/xhtml+xml,text/plain;q=0.9',
    },
    signal: AbortSignal.timeout(12000),
  });

  if (!response.ok) {
    throw new Error(`Error al acceder al enlace (${response.status}: ${response.statusText})`);
  }

  const html = await response.text();

  const titleMatch = html.match(/<title[^>]*>(.*?)<\/title>/i);
  let title = titleMatch ? titleMatch[1].replace(/\s+/g, ' ').trim() : 'Artículo de Referencia';
  title = title.replace(/\s*[-|–]\s*.*$/, '').trim();

  let clean = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, ' ')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, ' ')
    .replace(/<nav\b[^<]*(?:(?!<\/nav>)<[^<]*)*<\/nav>/gi, ' ')
    .replace(/<footer\b[^<]*(?:(?!<\/footer>)<[^<]*)*<\/footer>/gi, ' ')
    .replace(/<header\b[^<]*(?:(?!<\/header>)<[^<]*)*<\/header>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();

  if (clean.length > 15000) {
    clean = clean.slice(0, 15000);
  }

  return { title, text: clean };
}

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    const action = body.action || 'generate'; // reversion | generate | summarize | transform
    const provider: LLMProvider = body.provider === 'phi' ? 'phi' : 'gemini';
    const sourceUrl = body.source_url ? body.source_url.trim() : '';
    let sourceText = body.source_text ? body.source_text.trim() : '';
    let baseTitle = body.title ? body.title.trim() : '';
    const theme = body.theme || 'Opinión Pericial';
    const tone = body.tone || 'Revista Científica Arbitrada';
    const targetWords = body.target_words || 1500;
    const customInstructions = body.custom_instructions || '';
    const localEndpoint = body.local_endpoint || 'http://localhost:11434';
    const phiModel = body.phi_model || 'phi3';
    const apiKey = body.api_key;

    let urlExtractionNotes = '';

    // Manejo de reversión por URL
    if (action === 'reversion' || sourceUrl) {
      if (!sourceUrl && !sourceText) {
        return new Response(JSON.stringify({
          error: 'Debes proporcionar la URL de un artículo o un texto base para reversionar.',
        }), { status: 400, headers: { 'Content-Type': 'application/json' } });
      }

      if (sourceUrl) {
        try {
          const extracted = await extractTextFromUrl(sourceUrl);
          sourceText = extracted.text;
          if (!baseTitle) {
            baseTitle = extracted.title;
          }
          urlExtractionNotes = `Fuente Externa de Origen: ${sourceUrl} (Título original: "${extracted.title}").`;
        } catch (fetchErr: any) {
          return new Response(JSON.stringify({
            error: `No se pudo extraer el artículo desde la URL: ${fetchErr.message}`,
          }), { status: 422, headers: { 'Content-Type': 'application/json' } });
        }
      }
    }

    if (!sourceText && !baseTitle) {
      return new Response(JSON.stringify({
        error: 'Proporciona un título, tema o texto base para procesar.',
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    const today = new Date().toISOString().slice(0, 10);
    let prompt = '';

    if (action === 'reversion') {
      prompt = `TAREA ESPECÍFICA: REVERSIONAR ARTÍCULO EXTERNO Y GENERAR DOCUMENTO COMPLETO EN FORMATO BLOG ASTRO.
${urlExtractionNotes}

TEXTO EXTRAÍDO DEL ARTÍCULO ORIGINAL:
"""
${sourceText}
"""

DIRECTRICES DE REVERSIÓN:
1. Reversiona por completo el contenido: crea un título inédito de 50 a 60 caracteres enfocado en ciberseguridad, informática forense o derecho digital.
2. Adapta la problemática a los estándares técnicos (ISO/IEC 27037, hash SHA-256) y normativos de Venezuela (CRBV, G.O. 37.313 de Delitos Informáticos, G.O. 37.148 de Mensajes de Datos).
3. Estructura el artículo OBLIGATORIAMENTE siguiendo el formato de "Formato Blog -Astro.md":
   - Frontmatter YAML completo con fecha ${today}, autor "Equipo Pericial sha256.us", categoría "${theme}", seoKeyword relevante.
   - Envoltorio <div class="editorial-container">.
   - <div class="editorial-lead"> de 90 a 120 palabras con palabras clave en negrita.
   - <div class="editorial-quote"> con cita destacada de 20 a 30 palabras.
   - <div class="editorial-three-columns"> con EXACTAMENTE 6 bloques <div class="editorial-col"> extensos y balanceados (~1.350 a 1.600 caracteres cada uno, total 8.000 a 9.200 caracteres dentro de las 3 columnas) para llenar las 3 columnas completamente sin dejar espacios en blanco ni huecos al pie.
   - CADA PÁRRAFO debe tener 2 a 3 palabras clave en negrita (**norma**, **estándar**, **concepto forense**).
   - Bloque de Preguntas Frecuentes (FAQ) con 2 preguntas de 50 a 70 palabras y términos en negrita.
   - <div class="editorial-author-box"> para el Equipo Pericial sha256.us.
4. Extensión total: ~${targetWords} palabras (~10.500 caracteres). Tono: ${tone}.
${customInstructions ? `Instrucciones del usuario: ${customInstructions}` : ''}

IMPORTANTE: Devuelve ÚNICAMENTE el código Markdown resultante, comenzando directamente con "---" del Frontmatter.`;

    } else if (action === 'summarize') {
      prompt = `TAREA ESPECÍFICA: RESUMEN EJECUTIVO Y ABSTRACT EDITORIAL PERICIAL.
Título de referencia: "${baseTitle}"

TEXTO FUENTE:
"""
${sourceText}
"""

DIRECTRICES:
1. Genera un artículo de síntesis ejecutiva estructurado estrictamente según "Formato Blog -Astro.md":
   - Frontmatter YAML completo con fecha ${today}.
   - Lead directo y cita destacada con negritas clave.
   - Cuerpo en 3 columnas (<div class="editorial-three-columns">) con 6 bloques <div class="editorial-col"> densos (~8.000 caracteres en columnas) para llenar las 3 columnas sin espacios en blanco.
   - Negritas en palabras clave a lo largo de cada párrafo.
   - Caja con lección pericial crítica y protocolo.
   - Preguntas frecuentes y caja de autor.
Devuelve ÚNICAMENTE el Markdown comenzando con "---".`;

    } else if (action === 'transform') {
      prompt = `TAREA ESPECÍFICA: TRANSFORMAR BORRADOR AL FORMATO EDITORIAL SHA256.US.
Título propuesto: "${baseTitle}"
Tono: ${tone}

BORRADOR ORIGINAL:
"""
${sourceText}
"""

DIRECTRICES:
1. Transforma y eleva el borrador al formato de "Formato Blog -Astro.md" de sha256.us.
2. Integra el marco legal venezolano (CRBV Arts. 28/60/110, G.O. 37.313, G.O. 37.148) y las directrices ISO/IEC 27037.
3. Asegura el relleno completo de las 3 columnas (8.000 a 9.200 caracteres en las 3 columnas repartidos en los 6 bloques editorial-col) para eliminar espacios vacíos.
4. Aplica negritas a las palabras clave a lo largo de cada párrafo.
Devuelve ÚNICAMENTE el Markdown comenzando con "---".`;

    } else {
      // 'generate'
      prompt = `TAREA ESPECÍFICA: REDACTAR ARTÍCULO COMPLETO EN FORMATO BLOG ASTRO (SHA256.US).
Tema: ${theme}
Título de trabajo: "${baseTitle || 'Nuevo Análisis Pericial'}"
Tono: ${tone}
Extensión: ~${targetWords} palabras (~10.500 caracteres totales).

NOTAS O APUNTES DEL USUARIO:
"""
${sourceText}
"""
${customInstructions ? `Instrucciones adicionales: ${customInstructions}` : ''}

DIRECTRICES DE REDACCIÓN Y VOLUMEN DE RELLENO:
1. Aplica con absoluta fidelidad la plantilla "Formato Blog -Astro.md":
   - Frontmatter YAML con título persuasivo (50-60 caracteres), meta description (145-160 caracteres), pubDate: ${today}, updatedDate: ${today}, author: "Equipo Pericial sha256.us", tags (3-5 en kebab-case), category: "${theme}", readingTime: 6, featured: true, draft: false.
   - <div class="editorial-container">
   - <div class="editorial-lead"> (90 a 120 palabras con negritas en términos de apertura).
   - <div class="editorial-quote"> (20 a 30 palabras).
   - <div class="editorial-three-columns">: OBLIGATORIO generar 6 bloques <div class="editorial-col"> extensos y equilibrados (~1.350 a 1.600 caracteres cada bloque, sumando entre 8.000 y 9.200 caracteres dentro de las columnas). Esto es INDISPENSABLE para que las 3 columnas queden 100% llenas de arriba a abajo en escritorio sin dejar ningún espacio en blanco ni desniveles.
   - NEGRITAS OBLIGATORIAS: En CADA párrafo del artículo, resalta en negrita (**palabra clave** o <strong>palabra clave</strong>) entre 2 y 3 conceptos técnicos o legales esenciales (**cadena de custodia**, **hash criptográfico SHA-256**, **memoria volátil RAM**, **ISO/IEC 27037:2012**, **Ley Especial contra los Delitos Informáticos G.O. 37.313**, **Ley sobre Mensajes de Datos G.O. 37.148**, **principio de mismidad**).
   - Bloque de Preguntas Frecuentes (FAQ con 2 preguntas y respuestas completas de 50-70 palabras con términos en negrita).
   - <div class="editorial-author-box"> institucional.
Devuelve ÚNICAMENTE el Markdown comenzando con "---".`;
    }

    // Ejecutar llamada a través del proveedor unificado (Gemini o Microsoft Phi)
    const result = await generateWithModel(prompt, SYSTEM_INSTRUCTION, {
      provider,
      apiKey,
      localEndpoint,
      phiModel,
      temperature: 0.25,
      maxTokens: 6500,
    });

    let responseText = result.text.trim();
    responseText = responseText.replace(/^```(?:markdown|md)?\s*\n/i, '').replace(/\n```\s*$/i, '').trim();

    // Extraer metadatos
    const titleMatch = responseText.match(/title:\s*["']([^"']+)["']/i);
    const descMatch = responseText.match(/description:\s*["']([^"']+)["']/i);
    const slugMatch = responseText.match(/slug:\s*["']([^"']+)["']/i);
    const keywordMatch = responseText.match(/seoKeyword:\s*["']([^"']+)["']/i);
    const categoryMatch = responseText.match(/category:\s*["']([^"']+)["']/i);

    const generatedTitle = titleMatch ? titleMatch[1] : (baseTitle || 'Nuevo Artículo Pericial');
    const generatedDesc = descMatch ? descMatch[1] : 'Análisis pericial forense y ciberseguridad bajo norma ISO 27037.';
    const generatedSlug = slugMatch ? slugMatch[1] : generatedTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    const generatedKeyword = keywordMatch ? keywordMatch[1] : '';
    const generatedCategory = categoryMatch ? categoryMatch[1] : theme;

    const words = responseText.trim().split(/\s+/).length;
    const readingTime = Math.max(1, Math.round(words / 200));

    return new Response(JSON.stringify({
      success: true,
      action,
      provider: result.providerUsed,
      model: result.modelName,
      title: generatedTitle,
      description: generatedDesc,
      slug: generatedSlug,
      seoKeyword: generatedKeyword,
      category: generatedCategory,
      content: responseText,
      words,
      readingTime,
      sourceUrl: sourceUrl || undefined,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (err: any) {
    console.error('Error en /api/ai-action:', err);
    return new Response(JSON.stringify({
      error: err.message || 'Error interno al procesar la solicitud con IA.',
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
