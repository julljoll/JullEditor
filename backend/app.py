"""
Servidor Backend FastAPI para el Creador de Artículos de Blog con IBM Granite.
Integra Ollama local optimizado para CPU, Scraper de URLs con protección SSRF,
Generador de Imágenes de Cabecera 16:9, Gestor RAG Local con caché,
Validador SEO Backend, Concurrencia controlada y Streaming SSE.
"""

import asyncio
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.docling_parser import parse_docling_markdown
from backend.image_generator import generate_header_image
from backend.legal_profiles import resolve_jurisdiction
from backend.legal_validator import audit_legal_quality
from backend.logger_config import get_logger
from backend.prompts import build_generation_prompt, build_sentencia_tsj_prompt
from backend.rag_manager import (
    get_article_content,
    list_articles_history,
    retrieve_legal_context,
    save_final_article,
    save_rag_source,
)
from backend.scraper import extract_article_from_url, is_safe_url
from backend.sentencia_extractor import extract_sentencia_metadata, is_sentencia_text
from backend.seo_validator import audit_article_seo
from backend.system_profiler import detect_system_resources
from backend.version import __version__

logger = get_logger("app")

# Cargar variables de entorno
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_GRANITE_MODEL = os.getenv("GRANITE_MODEL", "granite3.3:8b")
FAST_MODEL = os.getenv("FAST_MODEL", "granite3.3:2b")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))
KEEP_ALIVE = os.getenv("KEEP_ALIVE", "30m")
NUM_THREAD = int(os.getenv("NUM_THREAD", "4"))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
DEFAULT_JURISDICTION = os.getenv("DEFAULT_JURISDICTION", "auto")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")

# Código de estado 422 agnóstico a versiones de Starlette (evita StarletteDeprecationWarning)
HTTP_422_UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

# Semáforo de concurrencia: 1 inferencia activa a la vez para no saturar CPU
generation_semaphore = asyncio.Semaphore(1)
active_client: httpx.AsyncClient | None = None

# Temperaturas predeterminadas por especialidad temática (Anti-alucinación y rigor fáctico 0.2 - 0.3)
THEME_TEMPERATURES = {
    "sentencia_tsj": 0.15,
    "legal_tech": 0.2,
    "forensic_law": 0.2,
    "cybersecurity": 0.25,
    "ai_data": 0.3,
    "science_tech": 0.3
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida del servidor: diagnóstico y warmup inicial, cleanup ordenado al apagar."""
    logger.info("=" * 60)
    logger.info("JullEditor v3.1.0 — Motor Activo (CPU/GPU)")
    logger.info(f"Ollama URL: {OLLAMA_BASE_URL} | Modelo Predeterminado: {DEFAULT_GRANITE_MODEL}")
    logger.info(f"Ventana Contexto: {NUM_CTX} | Hilos CPU: {NUM_THREAD}")
    logger.info("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                tags_data = resp.json()
                models = [m.get("name") for m in tags_data.get("models", [])]
                granite_found = [m for m in models if "granite" in m.lower()]
                if granite_found:
                    logger.info(f"✅ Conexión con Ollama establecida. Modelos Granite listos: {granite_found}")
                else:
                    logger.warning(f"⚠️ Ollama activo pero no tiene modelos Granite instalados: {models}")
    except Exception as e:
        logger.warning(f"⚠️ Aviso: Ollama no respondió en {OLLAMA_BASE_URL} durante arranque: {e}")
    yield
    global active_client
    if active_client and not active_client.is_closed:
        try:
            await active_client.aclose()
        except Exception:
            pass
    logger.info("JullEditor v3.1.0 finalizado correctamente.")

app = FastAPI(
    title="JullEditor API",
    description="JullEditor: Motor local de redacción de artículos con IBM Granite y diseño Cyber-Legal optimizado para CPU, SEO estricto y RAG verificado",
    version=__version__,
    lifespan=lifespan
)

# Configurar CORS restrictivo y seguro
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ==============================================================================
# MANEJADORES GLOBALES DE EXCEPCIONES
# ==============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Error de validación en {request.url.path}: {exc.errors()}")
    formatted_errors = [
        {
            "field": ".".join(str(x) for x in err.get("loc", [])),
            "message": err.get("msg", ""),
            "type": err.get("type", "")
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "message": "Los datos enviados no cumplen con los requisitos de validación.",
            "details": formatted_errors
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado en {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": exc.__class__.__name__,
            "message": "Ocurrió un error interno en el servidor.",
            "details": str(exc)
        }
    )

# ==============================================================================
# ESQUEMAS PYDANTIC CON VALIDACIÓN REFORZADA
# ==============================================================================

class ScrapeRequest(BaseModel):
    url: str = Field(..., max_length=2048, description="URL válida del artículo a extraer")

class GenerateRequest(BaseModel):
    source_text: str = Field(..., min_length=10, max_length=120000, description="Texto fuente base")
    source_title: str | None = Field("", max_length=300)
    source_url: str | None = Field("", max_length=2048)
    source_lang: str | None = Field("", max_length=20)
    source_author: str | None = Field("", max_length=200)
    source_date: str | None = Field("", max_length=100)
    source_section: str | None = Field("", max_length=200)
    theme: str = Field("cybersecurity", max_length=50)
    tone: str = Field("conversational", max_length=50)
    target_words: int = Field(1000, ge=200, le=4000)
    custom_instructions: str | None = Field("", max_length=1000)
    model: str | None = Field(None, max_length=100)
    temperature: float | None = Field(None, ge=0.0, le=1.5)
    jurisdiction: str | None = Field("auto", max_length=50, description="auto | venezuela | international")
    editorial_mode: str | None = Field("magazine", pattern="^(magazine|classic)$", description="magazine | classic")
    sentencia_metadata: dict[str, Any] | None = Field(None, description="Metadatos estructurados de sentencia TSJ")

    @field_validator("editorial_mode", mode="before")
    @classmethod
    def validate_editorial_mode(cls, v):
        if v is None or v == "":
            return "magazine"
        if v not in ("magazine", "classic"):
            raise ValueError("editorial_mode debe ser 'magazine' o 'classic'")
        return v

    @field_validator("source_title", "source_url", "source_lang", "source_author", "source_date", "source_section", "custom_instructions", mode="before")
    @classmethod
    def coerce_none_to_empty_str(cls, v):
        return "" if v is None else str(v)

    @field_validator("target_words", mode="before")
    @classmethod
    def clamp_target_words(cls, v):
        try:
            val = int(v)
            return max(300, min(val, 4000))
        except (ValueError, TypeError):
            return 1000

    @field_validator("temperature", mode="before")
    @classmethod
    def clamp_temperature(cls, v):
        if v is None:
            return None
        try:
            val = float(v)
            return max(0.0, min(val, 1.5))
        except (ValueError, TypeError):
            return None

class ExtractSentenciaRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=1000000)
    filename: str | None = Field("", max_length=255)

class DoclingParseRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000000)
    filename: str | None = Field("docling_export.md", max_length=255)

class SaveArticleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    markdown_content: str = Field(..., min_length=10, max_length=1000000)
    theme: str | None = Field("cybersecurity", max_length=50)
    model: str | None = Field("granite3.3:8b", max_length=100)
    tone: str | None = Field("conversational", max_length=50)
    source_url: str | None = Field("", max_length=2048)
    jurisdiction: str | None = Field("auto", max_length=50)
    editorial_mode: str | None = Field("magazine", max_length=50)

class GenerateHeaderImageRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    theme: str | None = Field("cybersecurity", max_length=50)
    custom_prompt: str | None = Field(None, max_length=500)

class SeoAuditRequest(BaseModel):
    markdown: str = Field(..., max_length=2000000, description="Contenido Markdown del artículo")
    jurisdiction: str | None = Field("auto", max_length=50, description="auto | venezuela | international")

# ==============================================================================
# ENDPOINTS API
# ==============================================================================


@app.get("/api/editorial-options")
async def editorial_options():
    """Catálogo editorial unificado (fuente única de verdad en Python).

    La GUI web consume este endpoint para poblar sus selects; así ninguna
    opción de negocio vive en JavaScript (PLAN v4.0 — Fase 1)."""
    from backend import editorial_catalog as cat
    return {
        "themes": [{"code": code, "icon": icon, "label": label} for code, icon, label in cat.THEMES],
        "editorial_modes": [{"code": code, "label": label} for code, label in cat.EDITORIAL_MODES],
        "tones": [{"code": code, "label": label} for code, label in cat.TONES],
        "jurisdictions": [{"code": code, "label": label} for code, label in cat.JURISDICTIONS],
        "models": [{"code": code, "label": label} for code, label in cat.MODELS],
        "word_count_targets": [{"words": words, "label": label} for words, label in cat.WORD_COUNT_TARGETS],
        "defaults": {
            "tone": cat.DEFAULT_TONE,
            "jurisdiction": cat.DEFAULT_JURISDICTION,
            "temperature": cat.DEFAULT_TEMPERATURE,
            "model": cat.DEFAULT_MODEL,
            "target_words": cat.DEFAULT_WORD_COUNT,
        },
    }

@app.get("/api/health")
async def health_check():
    """
    Verifica el estado de conexión con Ollama, latencia, parámetros de CPU y modelos disponibles con auto-reintento.
    """
    queue_busy = generation_semaphore.locked()
    start_time = time.time()
    last_err = None

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=3.5) as client:
                resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if resp.status_code == 200:
                    latency_ms = round((time.time() - start_time) * 1000)
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    granite_available = any("granite" in m.lower() for m in models)
                    return {
                        "status": "online",
                        "ollama_url": OLLAMA_BASE_URL,
                        "models": models,
                        "granite_installed": granite_available,
                        "default_model": DEFAULT_GRANITE_MODEL,
                        "fast_model": FAST_MODEL,
                        "num_ctx": NUM_CTX,
                        "num_thread": NUM_THREAD,
                        "keep_alive": KEEP_ALIVE,
                        "queue_busy": queue_busy,
                        "jurisdiction": DEFAULT_JURISDICTION,
                        "latency_ms": latency_ms,
                        "version": __version__
                    }
        except Exception as e:
            last_err = e
            if attempt == 0:
                await asyncio.sleep(0.3)
                continue

    logger.warning(f"Health check: no se pudo conectar a Ollama tras reintento: {last_err}")
    return {
        "status": "offline",
        "error": f"No se pudo conectar a Ollama en {OLLAMA_BASE_URL}.",
        "details": str(last_err),
        "granite_installed": False,
        "default_model": DEFAULT_GRANITE_MODEL,
        "fast_model": FAST_MODEL,
        "num_ctx": NUM_CTX,
        "num_thread": NUM_THREAD,
        "keep_alive": KEEP_ALIVE,
        "queue_busy": queue_busy,
        "jurisdiction": DEFAULT_JURISDICTION,
        "latency_ms": round((time.time() - start_time) * 1000),
        "version": __version__,
        "models": []
    }

@app.get("/api/system-info")
async def system_info_endpoint():
    """
    Retorna el diagnóstico automático de hardware del sistema (CPU, RAM, OS)
    y la configuración recomendada vs la activa para IBM Granite.
    """
    res = detect_system_resources()
    return {
        "status": "success",
        "system": res,
        "active_config": {
            "model": DEFAULT_GRANITE_MODEL,
            "fast_model": FAST_MODEL,
            "num_ctx": NUM_CTX,
            "num_thread": NUM_THREAD,
            "max_tokens": MAX_TOKENS,
            "temperature": DEFAULT_TEMPERATURE,
            "jurisdiction": DEFAULT_JURISDICTION,
            "keep_alive": KEEP_ALIVE
        }
    }

@app.get("/api/models")
async def list_models():
    """Retorna la lista de modelos instalados en Ollama."""
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                return resp.json()
            raise HTTPException(status_code=resp.status_code, detail="Error en Ollama API")
    except Exception as e:
        logger.error(f"Error consultando modelos en Ollama: {e}")
        raise HTTPException(status_code=503, detail=f"Error consultando Ollama: {e!s}")

@app.post("/api/seo-audit")
async def seo_audit_endpoint(req: SeoAuditRequest):
    """
    Auditoría SEO backend determinista para evaluar estructura, headings,
    palabras clave, metadatos, Schema.org JSON-LD y calidad jurídica / GEO 2026.
    """
    try:
        report = audit_article_seo(req.markdown)
        jcode = resolve_jurisdiction(req.jurisdiction or "auto", text=req.markdown[:4000])
        legal_report = audit_legal_quality(req.markdown, jurisdiction=jcode)
        combined_score = round(report["score"] * 0.6 + legal_report["score"] * 0.4)
        return {
            "status": "success",
            "report": report,
            "legal_report": legal_report,
            "combined_score": combined_score,
            "jurisdiction": jcode
        }
    except Exception as e:
        logger.error(f"Error en auditoría SEO: {e}")
        raise HTTPException(status_code=500, detail=f"Error evaluando SEO: {e!s}")

@app.post("/api/scrape")
async def scrape_url_endpoint(req: ScrapeRequest):
    """Extrae y limpia el contenido textual de una URL externa con validación anti-SSRF."""
    target_url = (req.url or "").strip()
    if not target_url:
        raise HTTPException(status_code=400, detail="Por favor proporciona una URL válida.")
    
    if not target_url.startswith(("http://", "https://")):
        target_url = f"https://{target_url}"
    
    if not is_safe_url(target_url):
        raise HTTPException(status_code=400, detail="URL no permitida por razones de seguridad (protección anti-SSRF).")

    try:
        article_data = await extract_article_from_url(target_url)
        return article_data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error procesando URL {target_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la URL: {e!s}")

@app.post("/api/parse-docling-md")
async def parse_docling_md_endpoint(req: DoclingParseRequest):
    """
    Procesa un archivo Markdown o JSON generado por Docling o texto local,
    lo persiste automáticamente en RAG/inputs/ para la base de conocimiento local,
    extrayendo títulos, limpiando artefactos y detectando la temática.
    """
    try:
        parsed_data = parse_docling_markdown(req.content, req.filename or "")
        rag_save_res = save_rag_source(req.filename or "docling_export.md", req.content)
        parsed_data["rag_input"] = rag_save_res
        return parsed_data
    except Exception as e:
        logger.error(f"Error procesando Docling: {e}")
        raise HTTPException(status_code=500, detail=f"Error procesando archivo Docling: {e!s}")

@app.post("/api/extract-sentencia")
async def extract_sentencia_endpoint(req: ExtractSentenciaRequest):
    """
    Extrae la Ficha Técnica estructurada de una sentencia del TSJ desde su texto Markdown.
    100% offline, determinista y sin dependencias externas.
    """
    try:
        meta = extract_sentencia_metadata(req.content, req.filename or "")
        return {
            "status": "success",
            "metadata": meta
        }
    except Exception as e:
        logger.error(f"Error extrayendo metadatos de sentencia TSJ: {e}")
        raise HTTPException(status_code=500, detail=f"Error analizando sentencia TSJ: {e!s}")

@app.post("/api/save-generated-article")
async def save_generated_article_endpoint(req: SaveArticleRequest):
    """
    Guarda automáticamente una copia en formato Markdown (.md) y HTML (.html) del artículo
    redactado por IBM Granite en el directorio 'Articulos Generados/', titulado con el nombre del artículo.
    """
    try:
        metadata = {
            "theme": req.theme,
            "model": req.model,
            "tone": req.tone,
            "source_url": req.source_url,
            "jurisdiction": req.jurisdiction,
            "editorial_mode": req.editorial_mode or "magazine"
        }
        res = save_final_article(
            title=req.title,
            markdown_content=req.markdown_content,
            metadata=metadata
        )
        if res.get("status") == "error":
            raise HTTPException(status_code=500, detail=res.get("message"))
        return res
    except Exception as e:
        logger.error(f"Error guardando artículo generado: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando artículo en Articulos Generados: {e!s}")

@app.get("/api/articles-history")
async def get_articles_history(limit: int = 20, offset: int = 0):
    """Retorna la lista de artículos previamente generados y archivados en 'Articulos Generados/'."""
    try:
        articles = list_articles_history(limit=limit, offset=offset)
        return {
            "status": "success",
            "articles": articles,
            "count": len(articles)
        }
    except Exception as e:
        logger.error(f"Error obteniendo historial de artículos: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando artículos: {e!s}")

@app.get("/api/articles-history/{filename}")
async def get_single_article(filename: str):
    """Retorna el contenido de un artículo archivado."""
    content = get_article_content(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    return {
        "status": "success",
        "filename": filename,
        "content": content
    }

PRELOADED_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "preloaded.json")

@app.get("/api/preloaded-file")
async def get_preloaded_file():
    """
    Retorna la información de un archivo Markdown precargado por el selector CLI
    (crear_articulo.bat / cli_generator.py) para que la interfaz web lo cargue automáticamente.
    """
    if os.path.exists(PRELOADED_FILE_PATH):
        try:
            with open(PRELOADED_FILE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            try:
                os.remove(PRELOADED_FILE_PATH)
            except Exception:
                pass
            return {"status": "success", "has_file": True, "data": data}
        except Exception as e:
            logger.warning(f"Error leyendo archivo de precarga: {e}")
    return {"status": "success", "has_file": False, "data": None}

@app.post("/api/generate-header-image")
async def generate_header_image_endpoint(req: GenerateHeaderImageRequest):
    """Genera una imagen de cabecera 16:9 SVG Cyber-Legal procedural."""
    try:
        result = await generate_header_image(
            title=req.title,
            theme=req.theme or "cybersecurity",
            custom_prompt=req.custom_prompt
        )
        return result
    except Exception as e:
        logger.error(f"Error generando imagen de cabecera: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando imagen: {e!s}")

@app.get("/api/download-proxy-image")
async def download_proxy_image(image_url: str):
    """
    Descarga una imagen remota y la entrega como archivo descargable para evitar bloqueos CORS
    con verificación anti-SSRF.
    """
    if not image_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagen inválida")

    if not is_safe_url(image_url):
        raise HTTPException(status_code=400, detail="URL de imagen rechazada por razones de seguridad (SSRF).")
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
        }
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(image_url, headers=headers)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                ext = "jpg"
                if "png" in content_type: ext = "png"
                elif "webp" in content_type: ext = "webp"
                elif "svg" in content_type: ext = "svg"
                elif "gif" in content_type: ext = "gif"
                
                filename = f"imagen_cabecera_{int(time.time())}.{ext}"
                return Response(
                    content=resp.content,
                    media_type=content_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                )
            raise HTTPException(status_code=400, detail="No se pudo descargar la imagen remota")
    except Exception as e:
        logger.error(f"Error en proxy de imagen {image_url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error descargando imagen: {e!s}")

@app.post("/api/stop-generation")
async def stop_generation_endpoint():
    """Cancela inmediatamente la inferencia activa en Ollama si existe."""
    global active_client
    if active_client and not active_client.is_closed:
        try:
            await active_client.aclose()
            logger.info("Inferencia en Ollama cancelada exitosamente vía /api/stop-generation.")
        except Exception as e:
            logger.warning(f"Aviso cerrando cliente de generación: {e}")
    return {"status": "stopped"}

@app.post("/api/generate-stream")
async def generate_article_stream(req: GenerateRequest, request: Request):
    """
    Genera el artículo en tiempo real mediante Server-Sent Events (SSE) desde Ollama
    con control de concurrencia en CPU, ventana de contexto extendida (num_ctx),
    parámetros de inferencia de alto rendimiento y adaptación jurisdiccional.
    """
    global active_client
    if generation_semaphore.locked():
        # Si hay una sesión previa huérfana o el cliente inició otra solicitud, intentar liberar
        if active_client and not active_client.is_closed:
            logger.info("Cerrando sesión previa huérfana para atender nueva solicitud de generación.")
            try:
                await active_client.aclose()
            except Exception:
                pass

        # Esperar hasta 3.5 segundos a que el semáforo se libere
        try:
            await asyncio.wait_for(generation_semaphore.acquire(), timeout=3.5)
            generation_semaphore.release()
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="El motor Granite local está procesando otra redacción en CPU. Por favor espera unos momentos a que finalice."
            )

    selected_model = req.model or DEFAULT_GRANITE_MODEL
    selected_temp = req.temperature if req.temperature is not None else THEME_TEMPERATURES.get(req.theme, DEFAULT_TEMPERATURE)
    selected_jurisdiction = req.jurisdiction or DEFAULT_JURISDICTION

    # 1. Determinar jurisdicción efectiva y recuperar RAG offline si aplica
    eff_jurisdiction = resolve_jurisdiction(
        jurisdiction=selected_jurisdiction,
        text=f"{req.source_title} {req.source_text} {req.custom_instructions}",
        theme=req.theme,
        persona=req.tone,
        has_ve_rag=False
    )
    
    rag_legal_context = ""
    if eff_jurisdiction in ("ve", "co"):
        rag_legal_context = retrieve_legal_context(
            query_text=f"{req.source_title} {req.source_text} {req.custom_instructions}",
            theme=req.theme or "cybersecurity",
            top_k=3,
            jurisdiction=eff_jurisdiction
        )

    # 2. Control de truncado seguro según num_ctx disponible
    source_text_processed = req.source_text
    max_safe_source_chars = (NUM_CTX - MAX_TOKENS - 1200) * 3
    if len(source_text_processed) > max_safe_source_chars:
        logger.warning(f"Texto fuente excede presupuesto de contexto ({len(source_text_processed)} chars). Truncando a {max_safe_source_chars} chars.")
        source_text_processed = source_text_processed[:max_safe_source_chars] + "\n\n[...Texto original truncado para respetar la ventana de contexto de inferencia...]"

    is_sentencia = (
        req.tone == "analista_tsj_revista"
        or req.theme == "sentencia_tsj"
        or req.sentencia_metadata is not None
        or is_sentencia_text(source_text_processed)
    )

    if is_sentencia and req.temperature is None:
        selected_temp = 0.15

    # 3. Construir el prompt optimizado
    if is_sentencia:
        logger.info("Detectado modo Análisis de Sentencia TSJ (Revista Digital). Usando build_sentencia_tsj_prompt().")
        full_prompt = build_sentencia_tsj_prompt(
            article_source_text=source_text_processed,
            source_title=req.source_title or "",
            source_url=req.source_url or "",
            sentencia_metadata=req.sentencia_metadata,
            legal_rag_context=rag_legal_context,
            custom_instructions=req.custom_instructions or "",
            target_words=req.target_words or 1400
        )
    else:
        full_prompt = build_generation_prompt(
            article_source_text=source_text_processed,
            source_title=req.source_title or "",
            source_url=req.source_url or "",
            source_lang=req.source_lang or "",
            source_author=req.source_author or "",
            source_date=req.source_date or "",
            source_section=req.source_section or "",
            theme=req.theme,
            tone=req.tone,
            target_words=req.target_words,
            custom_instructions=req.custom_instructions or "",
            legal_rag_context=rag_legal_context,
            jurisdiction=selected_jurisdiction,
            editorial_mode=req.editorial_mode or "magazine"
        )

    ollama_payload = {
        "model": selected_model,
        "prompt": full_prompt,
        "stream": True,
        "keep_alive": KEEP_ALIVE,
        "options": {
            "temperature": selected_temp,
            "num_predict": MAX_TOKENS,
            "num_ctx": NUM_CTX,
            "num_thread": NUM_THREAD,
            "repeat_penalty": 1.1,
            "top_p": 0.9,
        }
    }

    logger.info(
        f"Iniciando generación SSE con modelo {selected_model} "
        f"(ctx={NUM_CTX}, threads={NUM_THREAD}, temp={selected_temp}, tema={req.theme}, jur={selected_jurisdiction})"
    )

    async def event_generator():
        global active_client
        timeout_cfg = httpx.Timeout(timeout=600.0, connect=10.0, read=300.0, write=30.0)
        async with generation_semaphore:
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                active_client = client
                try:
                    async with client.stream(
                        "POST",
                        f"{OLLAMA_BASE_URL}/api/generate",
                        json=ollama_payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status_code != 200:
                            err_msg = f"Ollama error {response.status_code}: {response.reason_phrase}"
                            logger.error(err_msg)
                            yield f"data: {json.dumps({'error': err_msg})}\n\n"
                            return

                        async for chunk in response.aiter_lines():
                            # Verificar si el cliente del navegador se desconectó
                            if await request.is_disconnected():
                                logger.info("Cliente desconectado de SSE (cancelado o recarga). Deteniendo inferencia en Ollama.")
                                break

                            if chunk:
                                try:
                                    parsed = json.loads(chunk)
                                    response_token = parsed.get("response", "")
                                    is_done = parsed.get("done", False)
                                    
                                    payload = {
                                        "token": response_token,
                                        "done": is_done,
                                        "total_duration": parsed.get("total_duration", 0),
                                        "eval_count": parsed.get("eval_count", 0)
                                    }
                                    yield f"data: {json.dumps(payload)}\n\n"
                                    
                                    if is_done:
                                        logger.info(f"Generación SSE finalizada con éxito. Tokens generados: {parsed.get('eval_count', 0)}")
                                        break
                                except json.JSONDecodeError:
                                    continue
                except (httpx.RequestError, asyncio.CancelledError) as exc:
                    logger.info(f"Stream cancelado o interrumpido: {exc}")
                except Exception as e:
                    logger.error(f"Error en streaming SSE: {e}", exc_info=True)
                    err_text = str(e)
                    if "connection" in err_text.lower() or "connect" in err_text.lower():
                        err_text = f"No se pudo conectar a Ollama en {OLLAMA_BASE_URL}. Inicia el servicio ejecutando 'ollama serve' en una terminal."
                    yield f"data: {json.dumps({'error': err_text})}\n\n"
                finally:
                    active_client = None

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ==============================================================================
# SERVIR FRONTEND ESTÁTICO
# ==============================================================================

frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    css_dir = os.path.join(frontend_path, "css")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
        
    js_dir = os.path.join(frontend_path, "js")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
        
    img_dir = os.path.join(frontend_path, "images")
    if os.path.exists(img_dir):
        app.mount("/images", StaticFiles(directory=img_dir), name="images")

    fonts_dir = os.path.join(frontend_path, "fonts")
    if os.path.exists(fonts_dir):
        app.mount("/fonts", StaticFiles(directory=fonts_dir), name="fonts")

    @app.get("/")
    async def serve_index():
        index_file = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_file):
            return FileResponse(
                index_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        return {"message": "Frontend index.html no encontrado"}

    @app.get("/sitejet-lab.html")
    async def serve_sitejet_lab():
        lab_file = os.path.join(frontend_path, "sitejet-lab.html")
        if os.path.exists(lab_file):
            return FileResponse(
                lab_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        return {"message": "Laboratorio sitejet-lab.html no encontrado"}

    @app.get("/favicon.svg")
    async def serve_favicon():
        fav_file = os.path.join(frontend_path, "favicon.svg")
        if os.path.exists(fav_file):
            return FileResponse(fav_file)
        return {"message": "favicon not found"}

    @app.get("/manifest.json")
    async def serve_manifest():
        m_file = os.path.join(frontend_path, "manifest.json")
        if os.path.exists(m_file):
            return FileResponse(m_file)
        return {"message": "manifest not found"}
