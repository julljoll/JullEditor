"""
Servidor Backend FastAPI para el Creador de Artículos de Blog con IBM Granite.
Integra Ollama local, Scraper de URLs, Generador de Imágenes de Cabecera 16:9,
Gestor RAG Local, Historial de Artículos y Streaming SSE.
"""

import os
import json
import time
import httpx
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

from backend.logger_config import get_logger
from backend.prompts import build_generation_prompt
from backend.scraper import extract_article_from_url
from backend.docling_parser import parse_docling_markdown
from backend.image_generator import generate_header_image
from backend.rag_manager import (
    save_rag_source,
    save_final_article,
    retrieve_legal_context,
    list_articles_history,
    get_article_content
)

logger = get_logger("app")

# Cargar variables de entorno
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_GRANITE_MODEL = os.getenv("GRANITE_MODEL", "granite3.3:8b")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")

# Temperaturas predeterminadas por especialidad temática
THEME_TEMPERATURES = {
    "legal_tech": 0.4,
    "cybersecurity": 0.5,
    "ai_data": 0.6,
    "science_tech": 0.7
}

app = FastAPI(
    title="Granite Blog Article Generator API",
    description="Motor local de redacción de artículos con IBM Granite y diseño Cyber-Legal con soporte de Legislación Venezolana y Generador de Cabeceras 16:9",
    version="2.1.0"
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
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "message": "Los datos enviados no cumplen con los requisitos de validación.",
            "details": exc.errors()
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
    source_text: str = Field(..., min_length=10, max_length=80000, description="Texto fuente base")
    source_title: Optional[str] = Field("", max_length=300)
    source_url: Optional[str] = Field("", max_length=2048)
    source_lang: Optional[str] = Field("", max_length=20)
    source_author: Optional[str] = Field("", max_length=200)
    source_date: Optional[str] = Field("", max_length=100)
    source_section: Optional[str] = Field("", max_length=200)
    theme: str = Field("cybersecurity", max_length=50)
    tone: str = Field("conversational", max_length=50)
    target_words: int = Field(1000, ge=300, le=4000)
    custom_instructions: Optional[str] = Field("", max_length=1000)
    model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.1, le=1.5)

class DoclingParseRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000000)
    filename: Optional[str] = Field("docling_export.md", max_length=255)

class SaveArticleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    markdown_content: str = Field(..., min_length=10, max_length=1000000)
    theme: Optional[str] = Field("cybersecurity", max_length=50)
    model: Optional[str] = Field("granite3.3:8b", max_length=100)
    tone: Optional[str] = Field("conversational", max_length=50)
    source_url: Optional[str] = Field("", max_length=2048)

class GenerateHeaderImageRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    theme: Optional[str] = Field("cybersecurity", max_length=50)
    custom_prompt: Optional[str] = Field(None, max_length=500)

# ==============================================================================
# ENDPOINTS API
# ==============================================================================

@app.get("/api/health")
async def health_check():
    """
    Verifica el estado de conexión con Ollama y lista los modelos locales disponibles.
    """
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                granite_available = any("granite" in m.lower() for m in models)
                return {
                    "status": "online",
                    "ollama_url": OLLAMA_BASE_URL,
                    "models": models,
                    "granite_installed": granite_available,
                    "default_model": DEFAULT_GRANITE_MODEL,
                    "jurisdiction": "Venezuela (CRBV / Delitos Informáticos / Infogobierno)"
                }
    except Exception as e:
        logger.warning(f"Health check: no se pudo conectar a Ollama: {e}")
        return {
            "status": "offline",
            "error": f"No se pudo conectar a Ollama en {OLLAMA_BASE_URL}.",
            "details": str(e),
            "granite_installed": False,
            "default_model": DEFAULT_GRANITE_MODEL,
            "jurisdiction": "Venezuela (CRBV / Delitos Informáticos / Infogobierno)",
            "models": []
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
        raise HTTPException(status_code=503, detail=f"Error consultando Ollama: {str(e)}")

@app.post("/api/scrape")
async def scrape_url_endpoint(req: ScrapeRequest):
    """Extrae y limpia el contenido textual de una URL externa."""
    if not req.url or not req.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Por favor proporciona una URL válida que empiece con http:// o https://")
    
    try:
        article_data = await extract_article_from_url(req.url)
        return article_data
    except Exception as e:
        logger.error(f"Error procesando URL {req.url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar la URL: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error procesando archivo Docling: {str(e)}")

@app.post("/api/save-generated-article")
async def save_generated_article_endpoint(req: SaveArticleRequest):
    """
    Guarda automáticamente una copia en formato Markdown (.md) del artículo
    redactado por IBM Granite en el directorio RAG/articulos/.
    """
    try:
        metadata = {
            "theme": req.theme,
            "model": req.model,
            "tone": req.tone,
            "source_url": req.source_url
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
        raise HTTPException(status_code=500, detail=f"Error guardando artículo en RAG/articulos: {str(e)}")

@app.get("/api/articles-history")
async def get_articles_history(limit: int = 20, offset: int = 0):
    """Retorna la lista de artículos previamente generados y archivados en RAG/articulos/."""
    try:
        articles = list_articles_history(limit=limit, offset=offset)
        return {
            "status": "success",
            "articles": articles,
            "count": len(articles)
        }
    except Exception as e:
        logger.error(f"Error obteniendo historial de artículos: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando artículos: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Error generando imagen: {str(e)}")

@app.get("/api/download-proxy-image")
async def download_proxy_image(image_url: str):
    """
    Descarga una imagen remota y la entrega como archivo descargable para evitar bloqueos CORS.
    """
    if not image_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagen inválida")
        
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
        raise HTTPException(status_code=500, detail=f"Error descargando imagen: {str(e)}")

@app.post("/api/generate-stream")
async def generate_article_stream(req: GenerateRequest):
    """
    Genera el artículo en tiempo real mediante Server-Sent Events (SSE) desde Ollama
    con adaptación a legislación venezolana, SEO estricto y keywords resaltadas.
    """
    selected_model = req.model or DEFAULT_GRANITE_MODEL
    selected_temp = req.temperature if req.temperature is not None else THEME_TEMPERATURES.get(req.theme, DEFAULT_TEMPERATURE)
    
    # 1. Recuperar contexto jurídico venezolano RAG offline SOLO si aplica
    wants_venezuela = (
        "venezuela" in (req.custom_instructions or "").lower() or
        "venezuela" in (req.source_text or "").lower() or
        "venezuela" in (req.source_title or "").lower() or
        req.theme == "legal_tech"
    )
    
    rag_legal_context = ""
    if wants_venezuela:
        rag_legal_context = retrieve_legal_context(
            query_text=f"{req.source_title} {req.source_text} {req.custom_instructions}",
            theme=req.theme or "cybersecurity",
            top_k=3
        )

    # 2. Construir el prompt optimizado
    full_prompt = build_generation_prompt(
        article_source_text=req.source_text,
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
        legal_rag_context=rag_legal_context
    )

    ollama_payload = {
        "model": selected_model,
        "prompt": full_prompt,
        "stream": True,
        "options": {
            "temperature": selected_temp,
            "num_predict": MAX_TOKENS,
        }
    }

    logger.info(f"Iniciando generación SSE con modelo {selected_model} (temp={selected_temp}, tema={req.theme})")

    async def event_generator():
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
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
                                    logger.info(f"Generación SSE finalizada con éxito. Tokens: {parsed.get('eval_count', 0)}")
                                    break
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"Error en streaming SSE: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

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
