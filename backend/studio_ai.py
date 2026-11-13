"""AI endpoints used by the Astro editorial studio."""

import os
import re
from datetime import datetime, timezone
from typing import Any, Literal

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.providers import (
    ProviderConfigurationError,
    ProviderError,
    get_provider,
    validate_local_endpoint,
)
from backend.scraper import extract_article_from_url

router = APIRouter()
CHAT_SYSTEM_INSTRUCTION = """Eres el Agente Copiloto Editorial & Pericial de JullEditor para el laboratorio sha256.us.
Tu misión es asistir interactivamente al autor en la redacción, revisión, pulido, ampliación y aseguramiento técnico de artículos de ciberseguridad forense, peritaje digital y doctrina jurídica según el derecho positivo de la República Bolivariana de Venezuela 🇻🇪.

PRINCIPIOS FUNDAMENTALES:
1. Especialidad Dogmática y Técnica: Dominas la Constitución (Arts. 28, 60, 110), Ley Especial contra los Delitos Informáticos (G.O. 37.313), Ley de Mensajes de Datos y Firmas Electrónicas (G.O. 37.148), Ley de Infogobierno (G.O. 40.274), Manual de Cadena de Custodia MP/CICPC 2017, directrices ISO/IEC 27037 y preservación RFC 3227.
2. Formato Blog -Astro.md (sha256.us): Conoces a fondo la estructura de 3 columnas:
   - Frontmatter YAML completo.
   - <div class="editorial-container">
   - <div class="editorial-lead">
   - <div class="editorial-quote">
   - <div class="editorial-three-columns"> con EXACTAMENTE 6 bloques <div class="editorial-col">.
   - Preguntas Frecuentes (FAQ).
   - <div class="editorial-author-box"> para Equipo Pericial sha256.us.

3. REGLA DE VOLUMEN PARA RELLENO DE 3 COLUMNAS (CERO ESPACIOS EN BLANCO):
   - Para que las 3 columnas queden 100% llenas de texto sin dejar fondos vacíos ni espacios en blanco al pie, cada bloque <div class="editorial-col"> debe poseer entre 1.350 y 1.600 caracteres (~200 a 240 palabras), sumando entre 8.000 y 9.200 caracteres dentro de las 3 columnas (~10.500 caracteres totales en el artículo).
   - Si el artículo está corto o desbalanceado, amplía los párrafos con doctrina jurídica o metodología forense para igualar el nivel vertical de las 3 columnas.

4. COLOCACIÓN DE NEGRITAS EN PALABRAS CLAVE:
   - En CADA párrafo del artículo deben colocarse negritas (**término** o <strong>término</strong>) en 2 o 3 conceptos rectores (normas legales, estándares ISO/RFC, términos periciales como cadena de custodia, hash SHA-256, memoria RAM).

INSTRUCCIONES DE RESPUESTA EN CHAT:
- Sé conciso, profesional, analítico y directo.
- Si el usuario te pide modificar, agregar contenido, pulir o corregir el artículo actual, explícale brevemente la mejora y proporciónele el bloque Markdown o la versión actualizada completa delimitada en un bloque de código:
```markdown
---
...
```
- Si el usuario hace una consulta teórica o legal, responde con rigor pericial sin rodeos."""

ACTION_SYSTEM_INSTRUCTION = """Eres JullEditor AI: la inteligencia editorial de redacción científica, doctrina jurídica y ciberseguridad forense para el laboratorio sha256.us y el estándar normativo de la República Bolivariana de Venezuela 🇻🇪.

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

</div>"""


class StudioChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class StudioChatRequest(BaseModel):
    messages: list[StudioChatMessage] = Field(default_factory=list)
    instruction: str | None = None
    current_article: str | None = None
    provider: str = "google"


class StudioActionRequest(BaseModel):
    action: str = "generate"
    provider: str = "google"
    source_url: str | None = None
    source_text: str | None = None
    title: str | None = None
    theme: str = "Opinión Pericial"
    tone: str = "Revista Científica Arbitrada"
    target_words: int = 1500
    custom_instructions: str = ""


async def _check_local_phi_status(endpoint: str) -> dict[str, Any]:
    try:
        clean_endpoint = validate_local_endpoint(endpoint)
        is_v1 = clean_endpoint.endswith("/v1")
        status_url = f"{clean_endpoint}/models" if is_v1 else f"{clean_endpoint}/api/tags"
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(status_url, headers={"Accept": "application/json"})

        if not response.is_success:
            return {
                "connected": False,
                "models": [],
                "message": f"Servidor local respondió con código HTTP {response.status_code}.",
            }

        data = response.json()
        model_names: list[str] = []
        if isinstance(data.get("models"), list):
            model_names = [
                model.get("name") or model.get("model")
                for model in data["models"]
                if isinstance(model, dict) and (model.get("name") or model.get("model"))
            ]
        elif isinstance(data.get("data"), list):
            model_names = [
                model.get("id")
                for model in data["data"]
                if isinstance(model, dict) and model.get("id")
            ]
        return {
            "connected": True,
            "models": model_names,
            "message": (
                f"Conectado al servidor local ({len(model_names)} modelos detectados)"
                if model_names
                else "Conectado a servidor local (no se encontraron modelos descargados aún)"
            ),
        }
    except Exception:
        return {
            "connected": False,
            "models": [],
            "message": "No se pudo conectar al servidor local. Verifica OLLAMA_BASE_URL y que Ollama esté activo.",
        }


async def _generate_with_provider(
    prompt: str,
    system_instruction: str,
    provider: str,
    temperature: float,
    max_tokens: int,
) -> dict[str, str]:
    adapter = get_provider(provider)
    result = await adapter.complete(
        [{"role": "user", "content": prompt}],
        system_instruction,
        temperature,
        max_tokens,
    )
    return {
        "text": result.text,
        "providerUsed": result.provider,
        "modelName": result.model,
    }


async def _chat_with_model(
    messages: list[dict[str, str]],
    system_instruction: str,
    provider: str,
) -> dict[str, str]:
    adapter = get_provider(provider)
    result = await adapter.complete(messages, system_instruction, 0.35, 4000)
    return {
        "reply": result.text,
        "providerUsed": result.provider,
        "modelName": result.model,
    }


def _provider_error_response(error: ProviderError) -> JSONResponse:
    status_code = 503 if isinstance(error, ProviderConfigurationError) else 502
    return JSONResponse({"error": str(error)}, status_code=status_code)


@router.get("/api/ai-status")
async def ai_status():
    endpoint = os.getenv("OLLAMA_BASE_URL", "").strip() or "http://localhost:11434"
    return await _check_local_phi_status(endpoint)


@router.post("/api/ai-chat")
async def ai_chat(req: StudioChatRequest):
    history = [message.model_dump() for message in req.messages]
    if req.instruction and isinstance(req.instruction, str):
        history.append({"role": "user", "content": req.instruction})
    if not history:
        return JSONResponse(
            {"error": "No se enviaron mensajes para la conversación."},
            status_code=400,
        )

    system_instruction = CHAT_SYSTEM_INSTRUCTION
    current_article = (req.current_article or "").strip()
    if current_article:
        system_instruction += (
            "\n\nARTÍCULO ACTUAL EN EL EDITOR DEL USUARIO:\n"
            f'"""\n{current_article[:8000]}\n"""\n'
            "Usa este contenido como referencia cuando el usuario solicite ajustes o adiciones."
        )
    try:
        result = await _chat_with_model(
            history,
            system_instruction,
            req.provider,
        )
        reply = result["reply"]
        updated_article = None
        match = re.search(r"```(?:markdown|md)?\s*\n([\s\S]*?)\n```", reply, re.IGNORECASE)
        if match and ("editorial-container" in match.group(1) or match.group(1).startswith("---")):
            updated_article = match.group(1).strip()
        return {
            "success": True,
            "reply": reply,
            "updatedArticle": updated_article,
            "providerUsed": result["providerUsed"],
            "modelName": result["modelName"],
        }
    except ProviderError as exc:
        return _provider_error_response(exc)
    except Exception:
        return JSONResponse(
            {"error": "Error interno al comunicarse con el proveedor de IA."},
            status_code=500,
        )


def _build_action_prompt(
    action: str,
    source_text: str,
    base_title: str,
    theme: str,
    tone: str,
    target_words: int,
    custom_instructions: str,
    extraction_notes: str,
    today: str,
) -> str:
    if action == "reversion":
        return f"""TAREA ESPECÍFICA: REVERSIONAR ARTÍCULO EXTERNO Y GENERAR DOCUMENTO COMPLETO EN FORMATO BLOG ASTRO.
{extraction_notes}

TEXTO EXTRAÍDO DEL ARTÍCULO ORIGINAL:
\"\"\"
{source_text}
\"\"\"

DIRECTRICES DE REVERSIÓN:
1. Reversiona por completo el contenido: crea un título inédito de 50 a 60 caracteres enfocado en ciberseguridad, informática forense o derecho digital.
2. Adapta la problemática a los estándares técnicos (ISO/IEC 27037, hash SHA-256) y normativos de Venezuela (CRBV, G.O. 37.313 de Delitos Informáticos, G.O. 37.148 de Mensajes de Datos).
3. Estructura el artículo OBLIGATORIAMENTE siguiendo el formato de "Formato Blog -Astro.md":
   - Frontmatter YAML completo con fecha {today}, autor "Equipo Pericial sha256.us", categoría "{theme}", seoKeyword relevante.
   - Envoltorio <div class="editorial-container">.
   - <div class="editorial-lead"> de 90 a 120 palabras con palabras clave en negrita.
   - <div class="editorial-quote"> con cita destacada de 20 a 30 palabras.
   - <div class="editorial-three-columns"> con EXACTAMENTE 6 bloques <div class="editorial-col"> extensos y balanceados (~1.350 a 1.600 caracteres cada uno, total 8.000 a 9.200 caracteres dentro de las columnas) para llenar las 3 columnas completamente sin dejar espacios en blanco ni huecos al pie.
   - CADA PÁRRAFO debe tener 2 a 3 palabras clave en negrita (**norma**, **estándar**, **concepto forense**).
   - Bloque de Preguntas Frecuentes (FAQ) con 2 preguntas de 50 a 70 palabras y términos en negrita.
   - <div class="editorial-author-box"> para el Equipo Pericial sha256.us.
4. Extensión total: ~{target_words} palabras (~10.500 caracteres). Tono: {tone}.
{f"Instrucciones del usuario: {custom_instructions}" if custom_instructions else ""}

IMPORTANTE: Devuelve ÚNICAMENTE el código Markdown resultante, comenzando directamente con "---" del Frontmatter."""
    if action == "summarize":
        return f"""TAREA ESPECÍFICA: RESUMEN EJECUTIVO Y ABSTRACT EDITORIAL PERICIAL.
Título de referencia: "{base_title}"

TEXTO FUENTE:
\"\"\"
{source_text}
\"\"\"

DIRECTRICES:
1. Genera un artículo de síntesis ejecutiva estructurado estrictamente según "Formato Blog -Astro.md":
   - Frontmatter YAML completo con fecha {today}.
   - Lead directo y cita destacada con negritas clave.
   - Cuerpo en 3 columnas (<div class="editorial-three-columns">) con 6 bloques <div class="editorial-col"> densos (~8.000 caracteres en columnas) para llenar las 3 columnas sin espacios en blanco.
   - Negritas en palabras clave a lo largo de cada párrafo.
   - Caja con lección pericial crítica y protocolo.
   - Preguntas frecuentes y caja de autor.
Devuelve ÚNICAMENTE el Markdown comenzando con "---"."""
    if action == "transform":
        return f"""TAREA ESPECÍFICA: TRANSFORMAR BORRADOR AL FORMATO EDITORIAL SHA256.US.
Título propuesto: "{base_title}"
Tono: {tone}

BORRADOR ORIGINAL:
\"\"\"
{source_text}
\"\"\"

DIRECTRICES:
1. Transforma y eleva el borrador al formato de "Formato Blog -Astro.md" de sha256.us.
2. Integra el marco legal venezolano (CRBV Arts. 28/60/110, G.O. 37.313, G.O. 37.148) y las directrices ISO/IEC 27037.
3. Asegura el relleno completo de las 3 columnas (8.000 a 9.200 caracteres en las 3 columnas repartidos en los 6 bloques editorial-col) para eliminar espacios vacíos.
4. Aplica negritas a las palabras clave a lo largo de cada párrafo.
Devuelve ÚNICAMENTE el Markdown comenzando con "---"."""
    return f"""TAREA ESPECÍFICA: REDACTAR ARTÍCULO COMPLETO EN FORMATO BLOG ASTRO (SHA256.US).
Tema: {theme}
Título de trabajo: "{base_title or 'Nuevo Análisis Pericial'}"
Tono: {tone}
Extensión: ~{target_words} palabras (~10.500 caracteres totales).

NOTAS O APUNTES DEL USUARIO:
\"\"\"
{source_text}
\"\"\"
{f"Instrucciones adicionales: {custom_instructions}" if custom_instructions else ""}

DIRECTRICES DE REDACCIÓN Y VOLUMEN DE RELLENO:
1. Aplica con absoluta fidelidad la plantilla "Formato Blog -Astro.md":
   - Frontmatter YAML con título persuasivo (50-60 caracteres), meta description (145-160 caracteres), pubDate: {today}, updatedDate: {today}, author: "Equipo Pericial sha256.us", tags (3-5 en kebab-case), category: "{theme}", readingTime: 6, featured: true, draft: false.
   - <div class="editorial-container">
   - <div class="editorial-lead"> (90 a 120 palabras con negritas en términos de apertura).
   - <div class="editorial-quote"> (20 a 30 palabras).
   - <div class="editorial-three-columns">: OBLIGATORIO generar 6 bloques <div class="editorial-col"> extensos y equilibrados (~1.350 a 1.600 caracteres cada bloque, sumando entre 8.000 y 9.200 caracteres dentro de las columnas). Esto es INDISPENSABLE para que las 3 columnas queden 100% llenas de arriba a abajo en escritorio sin dejar ningún espacio en blanco ni desniveles.
   - NEGRITAS OBLIGATORIAS: En CADA párrafo del artículo, resalta en negrita (**palabra clave** o <strong>palabra clave</strong>) entre 2 y 3 conceptos técnicos o legales esenciales (**cadena de custodia**, **hash criptográfico SHA-256**, **memoria volátil RAM**, **ISO/IEC 27037:2012**, **Ley Especial contra los Delitos Informáticos G.O. 37.313**, **Ley sobre Mensajes de Datos G.O. 37.148**, **principio de mismidad**).
   - Bloque de Preguntas Frecuentes (FAQ con 2 preguntas y respuestas completas de 50-70 palabras con términos en negrita).
   - <div class="editorial-author-box"> institucional.
Devuelve ÚNICAMENTE el Markdown comenzando con "---"."""


@router.post("/api/ai-action")
async def ai_action(req: StudioActionRequest):
    action = req.action or "generate"
    source_url = (req.source_url or "").strip()
    source_text = (req.source_text or "").strip()
    base_title = (req.title or "").strip()
    theme = req.theme or "Opinión Pericial"
    tone = req.tone or "Revista Científica Arbitrada"
    custom_instructions = req.custom_instructions or ""
    url_extraction_notes = ""

    if action == "reversion" or source_url:
        if not source_url and not source_text:
            return JSONResponse(
                {"error": "Debes proporcionar la URL de un artículo o un texto base para reversionar."},
                status_code=400,
            )
        if source_url:
            try:
                extracted = await extract_article_from_url(source_url)
                source_text = extracted["text"]
                if not base_title:
                    base_title = extracted["title"]
                url_extraction_notes = (
                    f'Fuente Externa de Origen: {source_url} (Título original: "{extracted["title"]}").'
                )
            except Exception as exc:
                return JSONResponse(
                    {"error": f"No se pudo extraer el artículo desde la URL: {exc}"},
                    status_code=422,
                )
    if not source_text and not base_title:
        return JSONResponse(
            {"error": "Proporciona un título, tema o texto base para procesar."},
            status_code=400,
        )

    today = datetime.now(timezone.utc).date().isoformat()
    prompt = _build_action_prompt(
        action,
        source_text,
        base_title,
        theme,
        tone,
        req.target_words or 1500,
        custom_instructions,
        url_extraction_notes,
        today,
    )
    try:
        result = await _generate_with_provider(
            prompt,
            ACTION_SYSTEM_INSTRUCTION,
            req.provider,
            0.25,
            6500,
        )
        response_text = re.sub(r"^```(?:markdown|md)?\s*\n", "", result["text"].strip(), count=1, flags=re.IGNORECASE)
        response_text = re.sub(r"\n```\s*$", "", response_text).strip()
        title_match = re.search(r"title:\s*[\"']([^\"']+)[\"']", response_text, re.IGNORECASE)
        desc_match = re.search(r"description:\s*[\"']([^\"']+)[\"']", response_text, re.IGNORECASE)
        slug_match = re.search(r"slug:\s*[\"']([^\"']+)[\"']", response_text, re.IGNORECASE)
        keyword_match = re.search(r"seoKeyword:\s*[\"']([^\"']+)[\"']", response_text, re.IGNORECASE)
        category_match = re.search(r"category:\s*[\"']([^\"']+)[\"']", response_text, re.IGNORECASE)
        generated_title = title_match.group(1) if title_match else (base_title or "Nuevo Artículo Pericial")
        generated_slug = (
            slug_match.group(1)
            if slug_match
            else re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", generated_title.lower()))
        )
        words = len(response_text.split())
        return {
            "success": True,
            "action": action,
            "provider": result["providerUsed"],
            "model": result["modelName"],
            "title": generated_title,
            "description": desc_match.group(1) if desc_match else "Análisis pericial forense y ciberseguridad bajo norma ISO 27037.",
            "slug": generated_slug,
            "seoKeyword": keyword_match.group(1) if keyword_match else "",
            "category": category_match.group(1) if category_match else theme,
            "content": response_text,
            "words": words,
            "readingTime": max(1, int(words / 200 + 0.5)),
            **({"sourceUrl": source_url} if source_url else {}),
        }
    except ProviderError as exc:
        return _provider_error_response(exc)
    except Exception:
        return JSONResponse(
            {"error": "Error interno al procesar la solicitud con IA."},
            status_code=500,
        )
