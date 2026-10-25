"""
Módulo Gestor de Persistencia y Artículos para IBM Granite.
Gestiona el almacenamiento de fuentes de entrada (.md y .json de Docling) en 'Articulos Generados/inputs/'
y el auto-guardado de todos los artículos finalizados en 'Articulos Generados/' en formatos .md y .html
titulados directamente con el nombre del artículo.
Carga corpus legal desde backend/data/legal_corpus_ve.json e indexa con caché Informacion_docling_rag/.
"""

import glob
import html
import json
import os
import re
import unicodedata
from datetime import datetime
from typing import Any

from backend.logger_config import get_logger

logger = get_logger("rag_manager")

# Rutas base de persistencia dentro del workspace
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_GENERATED_DIR = os.path.join(WORKSPACE_ROOT, "Articulos Generados")
RAG_BASE_DIR = ARTICLES_GENERATED_DIR  # Alias de compatibilidad
RAG_INPUTS_DIR = os.path.join(ARTICLES_GENERATED_DIR, "inputs")
RAG_ARTICLES_DIR = ARTICLES_GENERATED_DIR  # Guardado directo en "Articulos Generados"
LEGACY_ARTICLES_DIR = os.path.join(ARTICLES_GENERATED_DIR, "articulos")
DOCLING_RAG_DIR = os.path.join(WORKSPACE_ROOT, "Informacion_docling_rag")
LEGAL_CORPUS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "legal_corpus_ve.json")

# Caché en memoria
_CACHED_LEGAL_CORPUS: list[dict[str, Any]] | None = None
_CACHED_DOCLING_FILES: list[dict[str, Any]] | None = None

def ensure_rag_directories():
    """Garantiza la existencia de la carpeta 'Articulos Generados' y sus subcarpetas."""
    os.makedirs(ARTICLES_GENERATED_DIR, exist_ok=True)
    os.makedirs(RAG_INPUTS_DIR, exist_ok=True)
    os.makedirs(LEGACY_ARTICLES_DIR, exist_ok=True)

def sanitize_title_to_filename(title: str, max_length: int = 140) -> str:
    """
    Convierte el título del artículo en un nombre de archivo limpio y legible.
    Preserva acentos y espacios, pero reemplaza caracteres no permitidos en Windows
    (/, \\, :, *, ?, \", <, >, |) y caracteres de control.
    Ejemplo: 'Sentencia TSJ: Principio de Intervención Mínima' -> 'Sentencia TSJ - Principio de Intervención Mínima'
    """
    if not title or not title.strip():
        return "Articulo_Sin_Titulo"
    
    clean = title.strip()
    clean = re.sub(r'^#+\s*', '', clean)
    clean = clean.replace(":", " -")
    clean = re.sub(r'[\\/*?"<>|#]', "", clean)
    clean = re.sub(r'[\r\n\t]+', " ", clean)
    clean = re.sub(r'\s+', " ", clean).strip(". ")
    
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip(". ")
        
    return clean if clean else "Articulo_Sin_Titulo"

def sanitize_filename(text: str, max_length: int = 80) -> str:
    """
    Convierte una cadena en un nombre de archivo seguro y limpio en minúsculas (slug).
    Ejemplo: 'Regulación de IA en Venezuela' -> 'regulacion_de_ia_en_venezuela'
    """
    if not text:
        return "documento_sin_titulo"
    
    nfkd_form = unicodedata.normalize('NFKD', text)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', only_ascii).strip('_').lower()
    return clean[:max_length] if clean else "documento"

def markdown_to_standalone_html(title: str, markdown_content: str, metadata: dict[str, Any] | None = None) -> str:
    """
    Convierte un artículo en Markdown en un documento HTML5 autónomo, responsivo y completamente
    estilizado con tipografía Cyber-Legal, tablas, callouts, Schema.org JSON-LD scripts y reglas de impresión.
    """
    text = markdown_content.strip()
    
    # Extraer frontmatter si existe
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2].strip()
            
    # Proteger bloques de código y extraer Schema.org JSON-LD
    schema_scripts = []
    
    def repl_code(match):
        code = match.group(2)
        clean_code = html.escape(code)
        
        # Si es JSON-LD Schema.org, crear script nativo
        if "schema.org" in code:
            schema_scripts.append(f'<script type="application/ld+json">\n{code.strip()}\n</script>')
            return f'\n<div class="code-block schema-block"><div class="code-header">⚡ DATOS ESTRUCTURADOS SCHEMA.ORG (JSON-LD)</div><pre><code>{clean_code}</code></pre></div>\n'
            
        return f'\n<div class="code-block"><pre><code>{clean_code}</code></pre></div>\n'
        
    text = re.sub(r'```([a-zA-Z0-9_\-]+)?\s*\n([\s\S]*?)```', repl_code, text)
    
    # Inline code
    text = re.sub(r'`([^`\n]+)`', lambda m: f'<code>{html.escape(m.group(1))}</code>', text)
    
    # Callouts especiales de formato SEO Blog / TSJ
    text = re.sub(
        r'(?:^|\n)>\s*\*\*📌 Resumen Pr[aá]ctico de la Fuente Original:\*\*\s*([\s\S]*?)(?=\n\n|\n>|\n##|$)',
        lambda m: f'\n<div class="callout callout-summary"><strong>📌 Resumen Práctico de la Fuente Original:</strong><p>{m.group(1).replace(">", "").strip()}</p></div>\n',
        text,
        flags=re.IGNORECASE
    )
    
    text = re.sub(
        r'(?:^|\n)>\s*\*\*⚡ Resumen Ejecutivo en 30 Segundos:\*\*\s*([\s\S]*?)(?=\n\n|\n>|\n##|$)',
        lambda m: f'\n<div class="callout callout-exec"><strong>⚡ Resumen Ejecutivo en 30 Segundos:</strong><p>{m.group(1).replace(">", "").strip()}</p></div>\n',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'(?:^|\n)>\s*\*\*Meta descripci[oó]n:\*\*\s*(.+?)(?=\n\n|$)',
        lambda m: f'\n<div class="callout callout-meta"><strong>🔍 Meta Descripción (SEO CTR):</strong> {m.group(1).strip()}</div>\n',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'(?:^|\n)>\s*\*\*📋\s*RESUMEN ESTRUCTURADO \(ABSTRACT\):\*\*\s*([\s\S]*?)(?=\n\n|\n>|\n##|$)',
        lambda m: f'\n<div class="callout callout-abstract"><strong>📋 Resumen Estructurado (Abstract):</strong><p>{m.group(1).replace(">", "").strip()}</p></div>\n',
        text,
        flags=re.IGNORECASE
    )

    # Conclusiones / Ideas clave
    text = re.sub(
        r'(?:^|\n)\*\*Conclusi[oó]n del p[aá]rrafo:\*\*\s*(.+?)(?=\n|$)',
        lambda m: f'\n<div class="takeaway"><strong>⚡ Conclusión del párrafo:</strong> {m.group(1).strip()}</div>\n',
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r'(?:^|\n)\*\*Idea clave:\*\*\s*(.+?)(?=\n|$)',
        lambda m: f'\n<div class="takeaway"><strong>💡 Idea clave:</strong> {m.group(1).strip()}</div>\n',
        text,
        flags=re.IGNORECASE
    )
    
    # Headings
    text = re.sub(r'^####\s+(.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^###\s+(.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)

    # Negrita e itálica
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^\*\n]+)\*', r'<em>\1</em>', text)
    
    # Enlaces
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)

    # Tablas Markdown
    def convert_table(match):
        lines = [ln.strip() for ln in match.group(0).strip().splitlines() if ln.strip()]
        if len(lines) < 2:
            return match.group(0)
        
        header_cols = [c.strip() for c in lines[0].strip('|').split('|')]
        body_rows = lines[2:] if len(lines) > 2 and re.match(r'^[\|\s\-:]+$', lines[1]) else lines[1:]
        
        th_html = "".join(f"<th>{c}</th>" for c in header_cols)
        tr_html = []
        for r in body_rows:
            cols = [c.strip() for c in r.strip('|').split('|')]
            td_html = "".join(f"<td>{c}</td>" for c in cols)
            tr_html.append(f"<tr>{td_html}</tr>")
            
        return f'<div class="table-container"><table><thead><tr>{th_html}</tr></thead><tbody>{"".join(tr_html)}</tbody></table></div>'

    text = re.sub(r'(?:^\|.+?\|\s*$\n?){2,}', convert_table, text, flags=re.MULTILINE)

    # Listas no ordenadas
    text = re.sub(r'(?:^[-*]\s+.+$\n?)+', lambda m: '<ul>' + ''.join(f'<li>{line[2:].strip()}</li>' for line in m.group(0).strip().splitlines() if line.strip()) + '</ul>\n', text, flags=re.MULTILINE)

    # Párrafos para texto plano
    blocks = text.split("\n\n")
    html_blocks = []
    for b in blocks:
        b_clean = b.strip()
        if not b_clean:
            continue
        if b_clean.startswith(("<h1", "<h2", "<h3", "<h4", "<div", "<ul", "<ol", "<table", "<blockquote", "<pre")):
            html_blocks.append(b_clean)
        else:
            html_blocks.append(f"<p>{b_clean.replace(chr(10), '<br>')}</p>")
            
    body_content = "\n\n".join(html_blocks)
    schema_injections = "\n".join(schema_scripts)
    
    css = """
    :root {
      --bg: #0b0f19;
      --card-bg: #111827;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --border: #1e293b;
      --gold: #d4af37;
      --cyan: #38bdf8;
      --accent-green: #34d399;
      --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font);
      line-height: 1.75;
      margin: 0;
      padding: 40px 20px;
    }
    .article-container {
      max-width: 860px;
      margin: 0 auto;
      background: var(--card-bg);
      padding: 48px;
      border-radius: 12px;
      border: 1px solid var(--border);
      box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    }
    h1 { font-size: 2.1rem; color: #fff; margin-top: 0; border-bottom: 2px solid var(--gold); padding-bottom: 14px; line-height: 1.3; }
    h2 { font-size: 1.5rem; color: var(--gold); margin-top: 38px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    h3 { font-size: 1.25rem; color: var(--cyan); margin-top: 26px; }
    p { margin: 16px 0; font-size: 1.05rem; }
    strong { color: #fff; }
    a { color: var(--cyan); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .callout { background: #1a2234; border-left: 4px solid var(--gold); padding: 16px 20px; margin: 24px 0; border-radius: 0 8px 8px 0; }
    .callout-exec { border-left-color: var(--cyan); background: #132238; }
    .callout-meta { border-left-color: var(--accent-green); background: #0f291e; font-size: 0.95rem; }
    .callout-abstract { border-left-color: #a855f7; background: #231533; }
    .takeaway { background: #162032; border: 1px solid #223554; padding: 12px 18px; margin: 18px 0; border-radius: 6px; font-size: 0.98rem; }
    .table-container { overflow-x: auto; margin: 24px 0; }
    table { width: 100%; border-collapse: collapse; border: 1px solid var(--border); }
    th { background: #1e293b; color: var(--gold); padding: 12px; text-align: left; border: 1px solid var(--border); font-size: 0.95rem; }
    td { padding: 10px 12px; border: 1px solid var(--border); font-size: 0.95rem; }
    tr:nth-child(even) { background: #131c2e; }
    tr:nth-child(odd) { background: #0e1524; }
    pre { background: #070a10; padding: 16px; border-radius: 8px; overflow-x: auto; border: 1px solid var(--border); }
    code { font-family: Consolas, "Courier New", monospace; font-size: 0.9rem; color: #fb923c; }
    .code-header { font-size: 0.8rem; font-weight: 700; color: var(--gold); margin-bottom: 6px; }
    ul, ol { padding-left: 28px; }
    li { margin: 8px 0; }
    .footer-credits { margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border); font-size: 0.85rem; color: var(--text-muted); text-align: center; }
    @media print {
      body { background: #fff; color: #000; }
      .article-container { border: none; box-shadow: none; padding: 0; }
      h1, h2, h3 { color: #000; }
      .callout { background: #f8fafc; color: #000; border-left-color: #333; }
    }
    """
    
    html_out = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <meta name="generator" content="JullEditor — IBM Granite 3.3 Cyber-Legal">
  <style>
{css}
  </style>
  {schema_injections}
</head>
<body>
  <main class="article-container">
    {body_content}
    <div class="footer-credits">
      ⚖️ Generado y Archivado por JullEditor v3.1.0 · IBM Granite 3.3 Local · Rigor Factual 0.0
    </div>
  </main>
</body>
</html>"""
    return html_out

def save_rag_source(filename: str, content: str) -> dict[str, Any]:
    """
    Guarda un archivo .md o .json subido por el usuario en 'Articulos Generados/inputs/'.
    Retorna metadatos de la operación y la ruta local persistida.
    """
    ensure_rag_directories()
    
    if not content or not content.strip():
        logger.warning("Intento de guardar fuente RAG vacía.")
        return {"status": "error", "message": "El contenido está vacío."}
    
    name_root, ext = os.path.splitext(filename or "fuente_docling.md")
    if not ext:
        ext = ".md"
    
    clean_base = sanitize_title_to_filename(name_root)
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
        logger.error(f"Error guardando fuente en Articulos Generados/inputs: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error guardando en Articulos Generados/inputs: {e!s}"
        }

def save_final_article(title: str, markdown_content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Guarda automáticamente el artículo generado en 'Articulos Generados/' en formato .md y .html
    titulados directamente con el nombre del artículo.
    Aplica el scrubber anti-alucinaciones legales y añade Frontmatter YAML para auditoría y publicación.
    """
    ensure_rag_directories()
    
    if not markdown_content or not markdown_content.strip():
        logger.warning("Intento de guardar artículo final vacío.")
        return {"status": "error", "message": "El artículo generado está vacío."}
    
    cleaned_content = clean_legal_hallucinations(markdown_content)
    meta = metadata or {}
    now = datetime.now()
    
    article_title = title.strip() if title else ""
    if not article_title:
        h1_match = re.search(r"^#\s+(.+)$", cleaned_content, re.MULTILINE)
        if h1_match:
            article_title = h1_match.group(1).replace("*", "").strip()
        else:
            article_title = "Articulo Blog Granite"
            
    # Guardar cada artículo con el nombre del título
    clean_title = sanitize_title_to_filename(article_title)
    target_filename_md = f"{clean_title}.md"
    target_filename_html = f"{clean_title}.html"
    
    target_path_md = os.path.join(RAG_ARTICLES_DIR, target_filename_md)
    target_path_html = os.path.join(RAG_ARTICLES_DIR, target_filename_html)
    
    words = cleaned_content.split()
    word_count = len(words)
    reading_time = max(1, round(word_count / 200))

    article_type = meta.get("article_type") or (
        "sentencia_tsj" if meta.get("tone") == "analista_tsj_revista" or meta.get("theme") == "sentencia_tsj" else "blog_post"
    )
    
    yaml_frontmatter = ""
    if not cleaned_content.startswith("---"):
        q = chr(34)  # comilla doble (compatible con Python 3.10 en f-strings)
        bs = chr(92)  # barra invertida
        safe_title = article_title.replace(q, bs + q)
        yaml_frontmatter = (
            f"---{bs}n"
            f"title: {q}{safe_title}{q}{bs}n"
            f"date: {q}{now.strftime('%Y-%m-%d %H:%M:%S')}{q}{bs}n"
            f"slug: {q}{clean_title}{q}{bs}n"
            f"article_type: {q}{article_type}{q}{bs}n"
            f"theme: {q}{meta.get('theme', 'cybersecurity')}{q}{bs}n"
            f"model: {q}{meta.get('model', 'granite3.3:8b')}{q}{bs}n"
            f"tone: {q}{meta.get('tone', 'conversational')}{q}{bs}n"
            f"editorial_mode: {q}{meta.get('editorial_mode', 'magazine')}{q}{bs}n"
            f"word_count: {word_count}{bs}n"
            f"reading_time_min: {reading_time}{bs}n"
            f"source_url: {q}{meta.get('source_url', '')}{q}{bs}n"
            f"html_file: {q}{target_filename_html}{q}{bs}n"
            f"generator: {q}Granite Blog Writer & LegalTech System{q}{bs}n"
            f"---{bs}n{bs}n"
        )
        full_content = yaml_frontmatter + cleaned_content
    else:
        full_content = cleaned_content

    try:
        # 1. Guardar archivo Markdown (.md)
        with open(target_path_md, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        # 2. Guardar archivo HTML (.html)
        html_content = markdown_to_standalone_html(article_title, cleaned_content, meta)
        with open(target_path_html, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        relative_path_md = os.path.relpath(target_path_md, WORKSPACE_ROOT)
        relative_path_html = os.path.relpath(target_path_html, WORKSPACE_ROOT)
        logger.info(f"Artículo final guardado en Articulos Generados: {relative_path_md} y {relative_path_html}")
        return {
            "status": "success",
            "filename": target_filename_md,
            "html_filename": target_filename_html,
            "path": relative_path_md.replace("\\", "/"),
            "html_path": relative_path_html.replace("\\", "/"),
            "absolute_path": target_path_md,
            "absolute_html_path": target_path_html,
            "title": article_title,
            "word_count": word_count,
            "saved_at": now.isoformat()
        }
    except Exception as e:
        logger.error(f"Error guardando artículo en Articulos Generados: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error guardando artículo final en Articulos Generados: {e!s}"
        }

def list_articles_history(limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    """
    Lista los artículos archivados en 'Articulos Generados/' ordenados por fecha descendente.
    Parsea el frontmatter YAML de cada archivo para proveer metadatos a la UI.
    """
    ensure_rag_directories()
    root_md = glob.glob(os.path.join(RAG_ARTICLES_DIR, "*.md"))
    legacy_md = glob.glob(os.path.join(LEGACY_ARTICLES_DIR, "*.md"))
    seen_paths = set()
    all_files = []
    for p in root_md + legacy_md:
        norm = os.path.normpath(p)
        if norm not in seen_paths:
            seen_paths.add(norm)
            all_files.append(p)
            
    all_files.sort(key=os.path.getmtime, reverse=True)
    paginated_files = all_files[offset:offset + limit]
    articles = []
    
    for filepath in paginated_files:
        filename = os.path.basename(filepath)
        stem = os.path.splitext(filename)[0]
        html_sibling = os.path.join(os.path.dirname(filepath), f"{stem}.html")
        has_html = os.path.exists(html_sibling)
        
        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read(2048)
                
            title = stem
            theme = "cybersecurity"
            article_type = "blog_post"
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
                            elif k == "article_type": article_type = v
                            elif k == "date": date = v
                            elif k == "word_count": word_count = int(v) if v.isdigit() else 0
                            elif k == "model": model = v
                            
            rel_path = os.path.relpath(filepath, WORKSPACE_ROOT).replace("\\", "/")
            articles.append({
                "filename": filename,
                "title": title,
                "theme": theme,
                "article_type": article_type,
                "date": date,
                "word_count": word_count,
                "model": model,
                "path": rel_path,
                "has_html": has_html,
                "html_path": rel_path.replace(".md", ".html") if has_html else None
            })
        except Exception as e:
            logger.warning(f"Error leyendo metadatos de {filename}: {e}")
            rel_path = os.path.relpath(filepath, WORKSPACE_ROOT).replace("\\", "/")
            articles.append({
                "filename": filename,
                "title": filename,
                "theme": "general",
                "date": "N/A",
                "word_count": 0,
                "model": "granite",
                "path": rel_path,
                "has_html": False,
                "html_path": None
            })
            
    return articles

def get_article_content(filename: str) -> str | None:
    """Obtiene el contenido Markdown completo de un artículo archivado."""
    safe_name = os.path.basename(filename)
    candidates = [
        os.path.join(RAG_ARTICLES_DIR, safe_name),
        os.path.join(LEGACY_ARTICLES_DIR, safe_name),
        os.path.join(WORKSPACE_ROOT, "RAG", "articulos", safe_name),
    ]
    for filepath in candidates:
        if os.path.exists(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error leyendo contenido de artículo {safe_name}: {e}")
    return None

# ==============================================================================
# MOTOR DE RECUPERACIÓN RAG DESDE JSON Y Informacion_docling_rag/
# ==============================================================================

def load_legal_corpus() -> list[dict[str, Any]]:
    """Carga el corpus legal venezolano desde JSON con caché en memoria."""
    global _CACHED_LEGAL_CORPUS
    if _CACHED_LEGAL_CORPUS is not None:
        return _CACHED_LEGAL_CORPUS
        
    if os.path.exists(LEGAL_CORPUS_JSON):
        try:
            with open(LEGAL_CORPUS_JSON, encoding="utf-8") as f:
                _CACHED_LEGAL_CORPUS = json.load(f)
                logger.info(f"Corpus legal cargado desde JSON: {len(_CACHED_LEGAL_CORPUS)} bloques normativos.")
                return _CACHED_LEGAL_CORPUS
        except Exception as e:
            logger.error(f"Error cargando legal_corpus_ve.json: {e}", exc_info=True)
            
    _CACHED_LEGAL_CORPUS = []
    return _CACHED_LEGAL_CORPUS

def _get_docling_files_cache() -> list[dict[str, Any]]:
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
                        with open(filepath, encoding='utf-8', errors='ignore') as f:
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

def search_docling_rag_files(query_text: str, top_k: int = 2) -> list[dict[str, str]]:
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

    is_jurisprudential = any(term in query_text.lower() for term in ["jurisprudencia", "sentencia", "tsj", "tribunal supremo", "casaci", "ponente", "fallo"])

    for item in docs:
        text_lower = item["text_lower"]
        rel_lower = item["rel_path"].lower()
        first_pos = -1
        matches = 0
        for tok in query_tokens:
            pos = text_lower.find(tok)
            if pos != -1:
                matches += 1
                if first_pos == -1 or pos < first_pos:
                    first_pos = pos

        if is_jurisprudential and "jurisprudencia" in rel_lower:
            matches += 8
        if is_jurisprudential and "tribunal-supremo" in rel_lower:
            matches += 6

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
        if theme in ("forensic_law", "legal_tech") and ("Cadena" in block.get("norma", "") or "Forense" in block.get("norma", "")): score += 6
        if theme in ("forensic_law", "legal_tech") and "Mensajes de Datos" in block.get("norma", ""): score += 5
        if theme in ("forensic_law", "cybersecurity") and "Delitos" in block.get("norma", ""): score += 5
        if theme == "cybersecurity" and "Cadena" in block.get("norma", ""): score += 3
        if theme == "ai_data" and "Constitucional" in block.get("area", ""): score += 4
        if theme == "ai_data" and "Infogobierno" in block.get("area", ""): score += 3
        if theme == "legal_tech" and "Constitucional" in block.get("area", ""): score += 3
        if theme == "science_tech" and "Telecomunicaciones" in block.get("area", ""): score += 4
        
        if any(w in query_lower for w in ["dato", "privacidad", "personal", "seguridad", "ciber", "regula", "cadena", "custodia", "evidencia", "forense", "hash", "tsj", "contrato"]):
            if "Constitucional" in block.get("area", "") or "Delitos" in block.get("norma", "") or "Cadena" in block.get("norma", "") or "Mensajes" in block.get("norma", ""):
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
