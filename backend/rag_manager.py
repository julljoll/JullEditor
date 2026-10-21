"""
Módulo Gestor de RAG Local y Persistencia de Archivos para IBM Granite.
Gestiona el almacenamiento de fuentes de entrada (.md y .json de Docling) en RAG/inputs/
y el auto-guardado de artículos finalizados en RAG/articulos/.
Carga corpus legal desde backend/data/legal_corpus_ve.json e indexa con caché Informacion_docling_rag/.
"""

import os
import re
import json
import glob
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.logger_config import get_logger

logger = get_logger("rag_manager")

# Rutas base del RAG dentro del workspace
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG_BASE_DIR = os.path.join(WORKSPACE_ROOT, "RAG")
RAG_INPUTS_DIR = os.path.join(RAG_BASE_DIR, "inputs")
RAG_ARTICLES_DIR = os.path.join(RAG_BASE_DIR, "articulos")
DOCLING_RAG_DIR = os.path.join(WORKSPACE_ROOT, "Informacion_docling_rag")
LEGAL_CORPUS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "legal_corpus_ve.json")

# Caché en memoria
_CACHED_LEGAL_CORPUS: Optional[List[Dict[str, Any]]] = None
_CACHED_DOCLING_FILES: Optional[List[Dict[str, Any]]] = None

def ensure_rag_directories():
    """Garantiza la existencia de las carpetas RAG/inputs y RAG/articulos."""
    os.makedirs(RAG_INPUTS_DIR, exist_ok=True)
    os.makedirs(RAG_ARTICLES_DIR, exist_ok=True)

def sanitize_filename(text: str, max_length: int = 80) -> str:
    """
    Convierte una cadena en un nombre de archivo seguro y limpio en minúsculas.
    Ejemplo: 'Regulación de IA en Venezuela' -> 'regulacion_de_ia_en_venezuela'
    """
    if not text:
        return "documento_sin_titulo"
    
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', only_ascii).strip('_').lower()
    return clean[:max_length] if clean else "documento"

def save_rag_source(filename: str, content: str) -> Dict[str, Any]:
    """
    Guarda un archivo .md o .json subido por el usuario en RAG/inputs/.
    Retorna metadatos de la operación y la ruta local persistida.
    """
    ensure_rag_directories()
    
    if not content or not content.strip():
        logger.warning("Intento de guardar fuente RAG vacía.")
        return {"status": "error", "message": "El contenido está vacío."}
    
    name_root, ext = os.path.splitext(filename or "fuente_docling.md")
    if not ext:
        ext = ".md"
    
    clean_base = sanitize_filename(name_root)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_filename = f"{clean_base}_{timestamp}{ext}"
    target_path = os.path.join(RAG_INPUTS_DIR, target_filename)
    
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        relative_path = os.path.relpath(target_path, WORKSPACE_ROOT)
        logger.info(f"Fuente RAG persistida exitosamente: {relative_path}")
        return {
            "status": "success",
            "filename": target_filename,
            "path": relative_path.replace("\\", "/"),
            "absolute_path": target_path,
            "bytes": len(content.encode("utf-8")),
            "saved_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error guardando fuente en RAG/inputs: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error guardando en RAG/inputs: {str(e)}"
        }

def save_final_article(title: str, markdown_content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Guarda automáticamente el artículo generado en RAG/articulos/ en formato .md
    con Frontmatter YAML de metadatos para auditoría y publicación en CMS/WordPress.
    Aplica el scrubber anti-alucinaciones legales.
    """
    ensure_rag_directories()
    
    if not markdown_content or not markdown_content.strip():
        logger.warning("Intento de guardar artículo final vacío.")
        return {"status": "error", "message": "El artículo generado está vacío."}
    
    cleaned_content = clean_legal_hallucinations(markdown_content)
    meta = metadata or {}
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    article_title = title.strip() if title else ""
    if not article_title:
        h1_match = re.search(r"^#\s+(.+)$", cleaned_content, re.MULTILINE)
        if h1_match:
            article_title = h1_match.group(1).replace("*", "").strip()
        else:
            article_title = "Articulo Blog Granite"
            
    slug = sanitize_filename(article_title, max_length=60)
    target_filename = f"{date_str}_{slug}.md"
    target_path = os.path.join(RAG_ARTICLES_DIR, target_filename)
    
    words = cleaned_content.split()
    word_count = len(words)
    reading_time = max(1, round(word_count / 200))
    
    yaml_frontmatter = ""
    if not cleaned_content.startswith("---"):
        yaml_frontmatter = (
            f"---\n"
            f"title: \"{article_title.replace('\"', '\\\"')}\"\n"
            f"date: \"{now.strftime('%Y-%m-%d %H:%M:%S')}\"\n"
            f"slug: \"{slug}\"\n"
            f"theme: \"{meta.get('theme', 'cybersecurity')}\"\n"
            f"model: \"{meta.get('model', 'granite3.3:8b')}\"\n"
            f"tone: \"{meta.get('tone', 'conversational')}\"\n"
            f"editorial_mode: \"{meta.get('editorial_mode', 'magazine')}\"\n"
            f"word_count: {word_count}\n"
            f"reading_time_min: {reading_time}\n"
            f"source_url: \"{meta.get('source_url', '')}\"\n"
            f"generator: \"Granite Blog Writer & LegalTech RAG System\"\n"
            f"---\n\n"
        )
        full_content = yaml_frontmatter + cleaned_content
    else:
        full_content = cleaned_content

    try:
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        relative_path = os.path.relpath(target_path, WORKSPACE_ROOT)
        logger.info(f"Artículo final guardado en RAG/articulos: {relative_path}")
        return {
            "status": "success",
            "filename": target_filename,
            "path": relative_path.replace("\\", "/"),
            "absolute_path": target_path,
            "title": article_title,
            "word_count": word_count,
            "saved_at": now.isoformat()
        }
    except Exception as e:
        logger.error(f"Error guardando artículo en RAG/articulos: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error guardando artículo final en RAG/articulos: {str(e)}"
        }

def list_articles_history(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Lista los artículos archivados en RAG/articulos/ ordenados por fecha descendente.
    Parsea el frontmatter YAML de cada archivo para proveer metadatos a la UI.
    """
    ensure_rag_directories()
    md_files = glob.glob(os.path.join(RAG_ARTICLES_DIR, "*.md"))
    md_files.sort(key=os.path.getmtime, reverse=True)
    
    paginated_files = md_files[offset:offset + limit]
    articles = []
    
    for filepath in paginated_files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read(2048)
                
            title = filename
            theme = "cybersecurity"
            date = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M")
            word_count = 0
            model = "granite3.3:8b"
            
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm = parts[1]
                    for line in fm.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k = k.strip().lower()
                            v = v.strip().strip('"').strip("'")
                            if k == "title": title = v
                            elif k == "theme": theme = v
                            elif k == "date": date = v
                            elif k == "word_count": word_count = int(v) if v.isdigit() else 0
                            elif k == "model": model = v
                            
            articles.append({
                "filename": filename,
                "title": title,
                "theme": theme,
                "date": date,
                "word_count": word_count,
                "model": model,
                "path": f"RAG/articulos/{filename}"
            })
        except Exception as e:
            logger.warning(f"Error leyendo metadatos de {filename}: {e}")
            articles.append({
                "filename": filename,
                "title": filename,
                "theme": "general",
                "date": "N/A",
                "word_count": 0,
                "model": "granite",
                "path": f"RAG/articulos/{filename}"
            })
            
    return articles

def get_article_content(filename: str) -> Optional[str]:
    """Obtiene el contenido Markdown completo de un artículo archivado."""
    safe_name = os.path.basename(filename)
    filepath = os.path.join(RAG_ARTICLES_DIR, safe_name)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error leyendo contenido de artículo {safe_name}: {e}")
    return None

# ==============================================================================
# MOTOR DE RECUPERACIÓN RAG DESDE JSON Y Informacion_docling_rag/
# ==============================================================================

def load_legal_corpus() -> List[Dict[str, Any]]:
    """Carga el corpus legal venezolano desde JSON con caché en memoria."""
    global _CACHED_LEGAL_CORPUS
    if _CACHED_LEGAL_CORPUS is not None:
        return _CACHED_LEGAL_CORPUS
        
    if os.path.exists(LEGAL_CORPUS_JSON):
        try:
            with open(LEGAL_CORPUS_JSON, "r", encoding="utf-8") as f:
                _CACHED_LEGAL_CORPUS = json.load(f)
                logger.info(f"Corpus legal cargado desde JSON: {len(_CACHED_LEGAL_CORPUS)} bloques normativos.")
                return _CACHED_LEGAL_CORPUS
        except Exception as e:
            logger.error(f"Error cargando legal_corpus_ve.json: {e}", exc_info=True)
            
    _CACHED_LEGAL_CORPUS = []
    return _CACHED_LEGAL_CORPUS

def _get_docling_files_cache() -> List[Dict[str, Any]]:
    """Carga e indexa en memoria una sola vez los archivos de Informacion_docling_rag/."""
    global _CACHED_DOCLING_FILES
    if _CACHED_DOCLING_FILES is not None:
        return _CACHED_DOCLING_FILES

    if not os.path.exists(DOCLING_RAG_DIR):
        _CACHED_DOCLING_FILES = []
        return _CACHED_DOCLING_FILES

    cached = []
    try:
        for root, _, files in os.walk(DOCLING_RAG_DIR):
            for file in files:
                if file.endswith(('.md', '.txt')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT).replace('\\', '/')
                        cached.append({
                            "file": file,
                            "rel_path": rel_path,
                            "text": text,
                            "text_lower": text.lower()
                        })
                    except Exception as e:
                        logger.debug(f"Error indexando {file}: {e}")
        logger.info(f"Índice RAG Docling precargado: {len(cached)} documentos en memoria.")
    except Exception as e:
        logger.error(f"Error escaneando {DOCLING_RAG_DIR}: {e}")

    _CACHED_DOCLING_FILES = cached
    return _CACHED_DOCLING_FILES

def search_docling_rag_files(query_text: str, top_k: int = 2) -> List[Dict[str, str]]:
    """
    Busca fragmentos relevantes en los archivos Markdown reales dentro de Informacion_docling_rag/
    usando el índice en caché y extrayendo un fragmento contextualizado alrededor de la coincidencia.
    """
    if not query_text:
        return []
        
    query_tokens = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', query_text.lower()))
    if not query_tokens:
        return []

    docs = _get_docling_files_cache()
    results = []

    for item in docs:
        text_lower = item["text_lower"]
        first_pos = -1
        matches = 0
        for tok in query_tokens:
            pos = text_lower.find(tok)
            if pos != -1:
                matches += 1
                if first_pos == -1 or pos < first_pos:
                    first_pos = pos

        if matches > 0:
            raw_text = item["text"]
            if first_pos != -1:
                start = max(0, first_pos - 120)
                end = min(len(raw_text), first_pos + 380)
                extract = raw_text[start:end].replace('\n', ' ').strip()
                if start > 0:
                    extract = "..." + extract
                if end < len(raw_text):
                    extract = extract + "..."
            else:
                extract = raw_text[:400].replace('\n', ' ').strip()

            results.append({
                "source": f"{item['file']} ({item['rel_path']})",
                "score": matches,
                "extract": extract
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def clean_legal_hallucinations(markdown: str) -> str:
    """
    Scrubber determinista que previene la mención errónea de leyes inexistentes
    en Venezuela, sustituyéndolas por el marco constitucional y legal verificado.
    """
    if not markdown:
        return ""
    
    pattern = re.compile(
        r'(?:la\s+)?Ley\s+Org[aá]nica\s+de\s+Protecci[oó]n\s+de\s+Datos\s+Personales(?:\s+de\s+Venezuela)?',
        re.IGNORECASE
    )
    replacement = "la tutela de datos personales en Venezuela (fundamentada en los Arts. 28 y 60 de la CRBV y la Ley Especial contra los Delitos Informáticos)"
    return pattern.sub(replacement, markdown)

def retrieve_legal_context(query_text: str, theme: str = "cybersecurity", top_k: int = 3, jurisdiction: str = "ve") -> str:
    """
    Motor RAG Local que recupera los artículos y normativas exactas desde
    la base de conocimiento JSON e Informacion_docling_rag/ según temática, palabras clave y jurisdicción (ve | co).
    Garantiza CERO ALUCINACIÓN de leyes inexistentes.
    """
    if not query_text:
        query_text = ""
        
    query_lower = query_text.lower()

    # Si la jurisdicción es Colombia, recuperar desde Informacion_docling_rag/Colombia
    if jurisdiction == "co":
        rag_output = []
        rag_output.append("================================================================================")
        rag_output.append("📚 CORPUS JURÍDICO COLOMBIANO AUTORIZADO (RAG OFFLINE DESDE Informacion_docling_rag/Colombia/)")
        rag_output.append("================================================================================")
        rag_output.append("IMPORTANTE: Para fundamentar jurídicamente el artículo en Colombia, DEBES utilizar")
        rag_output.append("EXCLUSIVAMENTE las siguientes normas reales de Colombia recuperadas de la base local:\n")

        docling_matches = search_docling_rag_files(f"colombia {query_text}", top_k=top_k + 2)
        co_matches = [d for d in docling_matches if "colombia" in d["source"].lower()] or docling_matches
        for i, doc in enumerate(co_matches[:top_k], 1):
            rag_output.append(f"### Fuente Legal Colombiana #{i}: {doc['source']}")
            rag_output.append(f"  • {doc['extract']}")
            rag_output.append("")

        rag_output.append("--------------------------------------------------------------------------------")
        rag_output.append("🛡️ REGLAS ESTRICTAS DE CERO ALUCINACIÓN (COLOMBIA):")
        rag_output.append("1. Las normas primarias autorizadas son la Ley 1273 de 2009 (delitos informáticos),")
        rag_output.append("   Ley 1581 de 2012 (datos personales), Ley 527 de 1999 (mensajes de datos) y C.P. de 1991 (Arts 15 y 86).")
        rag_output.append("2. Cita sentencias de la Corte Constitucional (C-, T-, SU-) ÚNICAMENTE si constan en la fuente o contexto.")
        rag_output.append("   No inventes números de radicado ni fechas ficticias.")
        rag_output.append("================================================================================\n")
        return "\n".join(rag_output)

    corpus = load_legal_corpus()
    scored_blocks = []
    for block in corpus:
        score = 0
        for kw in block.get("keywords", []):
            if kw in query_lower:
                score += 3
        if theme == "cybersecurity" and "Delitos" in block.get("norma", ""): score += 4
        if theme == "cybersecurity" and "Cadena" in block.get("norma", ""): score += 3
        if theme == "ai_data" and "Constitucional" in block.get("area", ""): score += 4
        if theme == "ai_data" and "Infogobierno" in block.get("area", ""): score += 3
        if theme == "legal_tech" and "Mensajes de Datos" in block.get("norma", ""): score += 4
        if theme == "legal_tech" and "Constitucional" in block.get("area", ""): score += 3
        if theme == "science_tech" and "Telecomunicaciones" in block.get("area", ""): score += 4
        
        if any(w in query_lower for w in ["dato", "privacidad", "personal", "seguridad", "ciber", "regula"]):
            if "Constitucional" in block.get("area", "") or "Delitos" in block.get("norma", ""):
                score += 5
                
        scored_blocks.append((score, block))
        
    scored_blocks.sort(key=lambda x: x[0], reverse=True)
    selected_blocks = [b[1] for b in scored_blocks[:top_k]]
    
    rag_output = []
    rag_output.append("================================================================================")
    rag_output.append("📚 CORPUS JURÍDICO VENEZOLANO AUTORIZADO (RAG OFFLINE DESDE Informacion_docling_rag/)")
    rag_output.append("================================================================================")
    rag_output.append("IMPORTANTE: Para fundamentar jurídicamente el artículo, DEBES utilizar EXCLUSIVAMENTE")
    rag_output.append("los siguientes artículos y leyes reales de Venezuela recuperados de la base de datos local:\n")
    
    for i, block in enumerate(selected_blocks, 1):
        rag_output.append(f"### Fuente Legal #{i}: {block['norma']} ({block['area']})")
        for art in block["articulos"]:
            rag_output.append(f"  • {art}")
        rag_output.append("")
        
    # Fragmentos adicionales desde Informacion_docling_rag/
    docling_matches = search_docling_rag_files(query_text, top_k=2)
    if docling_matches:
        rag_output.append("### Documentos Adicionales de Referencia Local:")
        for doc in docling_matches:
            rag_output.append(f"  • [{doc['source']}]: \"{doc['extract'][:200]}...\"")
        rag_output.append("")
        
    rag_output.append("--------------------------------------------------------------------------------")
    rag_output.append("🛡️ ADVERTENCIA ESTRICTA CONTRA ALUCINACIÓN DE LEYES (REGLA INQUEBRANTABLE):")
    rag_output.append("1. EN VENEZUELA NO EXISTE una 'Ley Orgánica de Protección de Datos Personales'.")
    rag_output.append("   La tutela de la privacidad y los datos en Venezuela se fundamenta EXCLUSIVAMENTE en:")
    rag_output.append("   - Artículos 28 (Habeas Data) y 60 (Privacidad) de la Constitución (CRBV).")
    rag_output.append("   - Artículos 20, 21 y 22 de la Ley Especial contra los Delitos Informáticos (G.O. Nº 37.313).")
    rag_output.append("   - Ley de Infogobierno (G.O. Nº 40.274, Art. 34).")
    rag_output.append("   - Ley sobre Mensajes de Datos y Firmas Electrónicas (G.O. Nº 37.148).")
    rag_output.append("2. QUEDA TERMINANTEMENTE PROHIBIDO inventar o citar una 'Ley Orgánica de Protección de Datos Personales'.")
    rag_output.append("3. Si comparas con regulaciones internacionales (como GDPR europeo o NIST), aclara expresamente")
    rag_output.append("   que son normas foráneas de referencia comparada y cita las normas venezolanas aplicables.")
    rag_output.append("================================================================================\n")
    
    return "\n".join(rag_output)
