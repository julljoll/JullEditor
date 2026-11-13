"""
Publicador de artículos Astro-ready hacia el sitio estático `blog/`.

Puente entre el motor de redacción (backend FastAPI) y el blog Astro estático:
copia los .md generados en 'Articulos Generados/astro_ready/' hacia
'blog/src/content/blog/' junto con sus imágenes, validando el frontmatter
contra el contrato de Content Collections antes de publicar.

Reglas de seguridad:
- Solo se publican archivos .md que existen dentro de ASTRO_READY_DIR
  (prevención de path traversal vía slug).
- Las imágenes solo se copian desde directorios controlados del workspace.
- La operación es idempotente por slug: volver a publicar actualiza en su sitio.
"""

import os
import re
import shutil
from datetime import date, datetime
from typing import Any

import yaml

from backend.logger_config import get_logger
from backend.rag_manager import ASTRO_READY_DIR, WORKSPACE_ROOT

logger = get_logger("astro_publisher")

# Destinos dentro del sitio Astro estático (preferencia frontend/ sobre blog/)
def _resolve_astro_dir() -> str:
    env_dir = os.environ.get("JULL_FRONTEND_DIR") or os.environ.get("JULL_BLOG_DIR")
    if env_dir:
        return env_dir
    frontend_dir = os.path.join(WORKSPACE_ROOT, "frontend")
    if os.path.exists(os.path.join(frontend_dir, "astro.config.mjs")):
        return frontend_dir
    return os.path.join(WORKSPACE_ROOT, "blog")

BLOG_DIR = _resolve_astro_dir()
BLOG_CONTENT_DIR = os.path.join(BLOG_DIR, "src", "content", "blog")
BLOG_IMAGES_DIR = os.path.join(BLOG_DIR, "public", "images", "articles")

# Campos requeridos del contrato de frontmatter (esquema Zod del blog)
REQUIRED_FIELDS = ("title", "description", "pubDate", "author", "tags")
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg"}


def _safe_join(base_dir: str, candidate: str) -> str | None:
    """Resuelve `candidate` dentro de `base_dir`; devuelve None si escapa (traversal)."""
    base_real = os.path.realpath(base_dir)
    resolved = os.path.realpath(os.path.join(base_real, candidate))
    if resolved == base_real or resolved.startswith(base_real + os.sep):
        return resolved
    return None


def parse_frontmatter(markdown_content: str) -> dict[str, Any] | None:
    """Extrae y valida el bloque YAML de frontmatter de un .md estilo Astro."""
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", markdown_content, re.DOTALL)
    if not match:
        return None
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return meta if isinstance(meta, dict) else None


def validate_frontmatter(meta: dict[str, Any]) -> list[str]:
    """
    Verifica el frente matter contra el contrato del blog (Content Collections).
    Retorna lista de errores; vacía si es válido.
    """
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in meta or meta[field] in (None, ""):
            errors.append(f"Campo requerido ausente en frontmatter: '{field}'")

    title = meta.get("title")
    if not isinstance(title, str) or not 1 <= len(title) <= 200:
        errors.append("'title' debe contener entre 1 y 200 caracteres")

    desc = meta.get("description")
    if not isinstance(desc, str) or not 1 <= len(desc) <= 170:
        errors.append("'description' debe contener entre 1 y 170 caracteres")

    author = meta.get("author")
    if not isinstance(author, str) or not author.strip():
        errors.append("'author' debe ser un texto no vacío")

    tags = meta.get("tags")
    if not isinstance(tags, list) or not 1 <= len(tags) <= 6:
        errors.append("'tags' debe contener entre 1 y 6 elementos")
    elif any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        errors.append("Cada elemento de 'tags' debe ser un texto no vacío")

    pub = meta.get("pubDate")
    for field in ("pubDate", "updatedDate"):
        value = meta.get(field)
        if value is None and field == "updatedDate":
            continue
        try:
            if isinstance(value, (date, datetime)):
                date.fromisoformat(value.isoformat()[:10])
            elif isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                date.fromisoformat(value)
            else:
                raise ValueError
        except ValueError:
            errors.append(f"'{field}' debe ser una fecha válida con formato YYYY-MM-DD")

    slug = meta.get("slug")
    if slug is not None and (
        not isinstance(slug, str)
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug)
    ):
        errors.append("'slug' debe usar minúsculas, números y guiones simples")

    for field in ("category", "heroImage", "seoKeyword"):
        value = meta.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"'{field}' debe ser un texto")

    draft = meta.get("draft")
    if draft is not None and not isinstance(draft, bool):
        errors.append("'draft' debe ser booleano")

    featured = meta.get("featured")
    if featured is not None and not isinstance(featured, bool):
        errors.append("'featured' debe ser booleano")

    reading = meta.get("readingTime")
    if reading is not None and (
        isinstance(reading, bool) or not isinstance(reading, int) or reading <= 0
    ):
        errors.append("'readingTime' debe ser un entero positivo")

    return errors


def find_astro_file(slug: str) -> str | None:
    """Localiza el .md astro_ready correspondiente a un slug, sin permitir traversal."""
    clean_slug = re.sub(r"\.md$", "", slug or "").strip()
    target = _safe_join(ASTRO_READY_DIR, f"{clean_slug}.md")
    if not target or not os.path.isfile(target):
        return None
    return target


def _collect_images_for_article(astro_path: str, content: str) -> list[str]:
    """
    Busca imágenes locales asociadas al artículo (por slug o referidas en el cuerpo)
    en los directorios controlados de salida. Devuelve rutas absolutas existentes.
    """
    base = os.path.splitext(os.path.basename(astro_path))[0]
    candidates: list[str] = []

    search_dirs = [
        ASTRO_READY_DIR,
        os.path.dirname(astro_path),
        # subcarpeta astro_ready/images/ (destino de image_generator.py)
        os.path.join(ASTRO_READY_DIR, "images"),
        # compatibilidad con la ubicación antigua heredada
        os.path.join(os.path.dirname(ASTRO_READY_DIR), "images"),
    ]
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in ALLOWED_IMAGE_EXT:
                continue
            stem = os.path.splitext(fname)[0]
            if stem == base or stem in content:
                candidates.append(os.path.join(d, fname))

    # Deduplicar preservando orden
    seen: set[str] = set()
    unique = []
    for c in candidates:
        real = os.path.realpath(c)
        if real not in seen:
            seen.add(real)
            unique.append(c)
    return unique


def publish_article(slug: str, force: bool = False) -> dict[str, Any]:
    """
    Publica un artículo astro_ready en el blog estático.

    - Valida frontmatter contra el contrato del blog.
    - Copia el .md a blog/src/content/blog/<slug>.md
    - Copia las imágenes locales detectadas a blog/public/images/articles/
    - Reescribe heroImage hacia /images/articles/<archivo> si existía localmente.

    Retorna un reporte con status success/error y detalles.
    """
    astro_path = find_astro_file(slug)
    if not astro_path:
        return {
            "status": "error",
            "message": f"No existe artículo astro_ready para el slug '{slug}'. "
                       "Genera y guarda el artículo primero.",
        }

    with open(astro_path, encoding="utf-8") as f:
        content = f.read()

    meta = parse_frontmatter(content)
    if meta is None:
        return {
            "status": "error",
            "message": "El archivo no tiene frontmatter YAML válido compatible con Astro Content Collections.",
        }

    errors = validate_frontmatter(meta)
    if errors:
        return {"status": "error", "message": "Frontmatter inválido para el blog.", "errors": errors}

    clean_slug = os.path.splitext(os.path.basename(astro_path))[0]
    dest_md = _safe_join(BLOG_CONTENT_DIR, f"{clean_slug}.md")
    if not dest_md:
        return {"status": "error", "message": "Slug rechazado por prevención de path traversal."}

    if os.path.exists(dest_md) and not force:
        # Idempotencia: comparar contenido para reportar sincronización
        with open(dest_md, encoding="utf-8") as f:
            same = f.read() == content
        if same:
            return {
                "status": "success",
                "action": "unchanged",
                "slug": clean_slug,
                "published_path": os.path.relpath(dest_md, WORKSPACE_ROOT).replace("\\", "/"),
                "images": [],
                "message": "El artículo ya está publicado y sincronizado.",
            }

    if not os.path.isdir(BLOG_DIR):
        return {
            "status": "error",
            "message": f"El sitio Astro no existe en '{os.path.relpath(BLOG_DIR, WORKSPACE_ROOT)}'. "
                       "Crea el blog con `npm create astro` o usa scripts/init_blog.sh.",
        }

    os.makedirs(BLOG_CONTENT_DIR, exist_ok=True)
    os.makedirs(BLOG_IMAGES_DIR, exist_ok=True)

    copied_images: list[str] = []
    images = _collect_images_for_article(astro_path, content)
    for img_src in images:
        fname = os.path.basename(img_src)
        img_dst = _safe_join(BLOG_IMAGES_DIR, fname)
        if not img_dst:
            continue
        shutil.copy2(img_src, img_dst)
        copied_images.append(fname)
        # Normalizar heroImage/referencias locales hacia la ruta pública del blog
        content = content.replace(
            f'heroImage: "{meta.get("heroImage", "")}"',
            f'heroImage: "/images/articles/{fname}"',
            1,
        ) if meta.get("heroImage") and fname.startswith(clean_slug) else content

    action = "updated" if os.path.exists(dest_md) else "created"
    with open(dest_md, "w", encoding="utf-8") as f:
        f.write(content)

    # Si existe carpeta espejo (p.ej. blog/ o frontend/) sincronizar simultáneamente
    alt_dir = os.path.join(WORKSPACE_ROOT, "blog" if "frontend" in BLOG_DIR else "frontend")
    if os.path.isdir(alt_dir) and os.path.realpath(alt_dir) != os.path.realpath(BLOG_DIR):
        try:
            alt_content_dir = os.path.join(alt_dir, "src", "content", "blog")
            if os.path.isdir(alt_content_dir):
                alt_dest = _safe_join(alt_content_dir, f"{clean_slug}.md")
                if alt_dest:
                    with open(alt_dest, "w", encoding="utf-8") as f_alt:
                        f_alt.write(content)
        except Exception:
            pass

    logger.info(f"Artículo publicado en el blog: {clean_slug} (acción: {action})")
    return {
        "status": "success",
        "action": action,
        "slug": clean_slug,
        "title": meta.get("title"),
        "published_path": os.path.relpath(dest_md, WORKSPACE_ROOT).replace("\\", "/"),
        "images": copied_images,
        "message": f"Artículo '{meta.get('title')}' publicado en el blog Astro.",
    }


def get_publication_status() -> list[dict[str, Any]]:
    """
    Estado de publicación de cada borrador astro_ready:
    published | draft | unsynced | missing.
    """
    statuses: list[dict[str, Any]] = []
    if not os.path.isdir(ASTRO_READY_DIR):
        return statuses
    for fname in sorted(os.listdir(ASTRO_READY_DIR)):
        if not fname.endswith(".md"):
            continue
        slug = fname[:-3]
        src = os.path.join(ASTRO_READY_DIR, fname)
        dst = os.path.join(BLOG_CONTENT_DIR, fname)
        with open(src, encoding="utf-8") as f:
            src_content = f.read()
        meta = parse_frontmatter(src_content) or {}
        if meta.get("draft"):
            state = "draft"
        elif not os.path.exists(dst):
            state = "unpublished"
        else:
            with open(dst, encoding="utf-8") as f:
                state = "synced" if f.read() == src_content else "unsynced"
        statuses.append({
            "slug": slug,
            "filename": fname,
            "title": meta.get("title", slug),
            "state": state,
            "published_path": os.path.relpath(dst, WORKSPACE_ROOT).replace("\\", "/")
                             if state in ("synced", "unsynced") else None,
        })
    return statuses
