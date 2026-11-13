"""
Exportador de Artículos para Astro Framework Markdown.
Genera archivos .md listos para producción y compatibles al 100% con
las colecciones de contenido de Astro (Content Collections).
Preserva y potencia el SEO profesional de primer nivel, metadata enriquecida
y formato limpio sin artefactos.
"""

import re
import unicodedata
from datetime import datetime
from typing import Any

import yaml


def slugify_astro(text: str) -> str:
    """
    Convierte cualquier título o texto en un slug URL-friendly canónico para Astro:
    - Normaliza Unicode (NFD) para separar acentos y diacríticos
    - Filtra los caracteres de marca diacrítica
    - Convierte a minúsculas
    - Sustituye cualquier caracter no alfanumérico por guiones
    - Elimina guiones repetidos y extremos
    - Limita la longitud a 80 caracteres
    Ejemplo: 'Principio de Intervención Mínima' -> 'principio-de-intervencion-minima'
    """
    if not text:
        return "articulo-blog"
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    slug = text[:80].rstrip("-")
    return slug or "articulo-blog"


def extract_description_from_body(markdown: str) -> tuple[str, str]:
    """
    Extrae la meta descripción del contenido Markdown y la remueve del cuerpo si procede.
    Estrategias en orden de prioridad:
    1. Directiva explícita 'META_DESC: ...'
    2. Sección '## Meta Descripción' con blockquote (> ...)
    3. Primer blockquote con verbo editorial (Explora, Descubre, Analizamos, etc.)
    4. Primer párrafo de texto ordinario
    Retorna una tupla (descripcion_160_chars, cuerpo_limpio).
    """
    if not markdown:
        return "", ""

    # Estrategia 1: Prefijo explícito META_DESC:
    meta_desc_match = re.search(r"^META_DESC:\s*(.+)$", markdown, re.MULTILINE | re.IGNORECASE)
    if meta_desc_match:
        desc = meta_desc_match.group(1).strip()
        cleaned = markdown[: meta_desc_match.start()] + markdown[meta_desc_match.end() :]
        return _format_description(desc), cleaned.strip()

    # Estrategia 1b: Blockquote '> **Meta descripción:** ...'
    quote_meta_match = re.search(
        r"^>\s*\*\*Meta\s+descripci[oó]n:\*\*\s*(.+)$",
        markdown,
        re.MULTILINE | re.IGNORECASE,
    )
    if quote_meta_match:
        desc = quote_meta_match.group(1).strip()
        cleaned = markdown[: quote_meta_match.start()] + markdown[quote_meta_match.end() :]
        return _format_description(desc), cleaned.strip()

    # Estrategia 2: Sección '## Meta Descripción'
    section_match = re.search(
        r"^##\s+Meta\s+Descripci[oó]n\s*\n+((?:>\s*.+\n?)+)",
        markdown,
        re.MULTILINE | re.IGNORECASE,
    )
    if section_match:
        raw_lines = section_match.group(1).splitlines()
        desc_lines = [re.sub(r"^>\s*", "", ln).strip() for ln in raw_lines]
        desc = " ".join(l for l in desc_lines if l)
        cleaned = markdown[: section_match.start()] + markdown[section_match.end() :]
        return _format_description(desc), cleaned.strip()

    # Estrategia 3: Blockquote con verbos típicos de resumen/intro
    pattern_quote = re.compile(
        r"^>\s*(?:Explora|Descubre|Analizamos|En este|Este art[íi]culo|Aprende|Conoce)(.+)$",
        re.MULTILINE | re.IGNORECASE,
    )
    quote_match = pattern_quote.search(markdown)
    if quote_match:
        desc = quote_match.group(0).lstrip("> ").strip()
        cleaned = markdown[: quote_match.start()] + markdown[quote_match.end() :]
        return _format_description(desc), cleaned.strip()

    # Estrategia 4: Primer párrafo ordinario que no sea título ni bloque
    for para in markdown.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if p.startswith(("#", ">", "```", "---", "|", "*", "-")):
            continue
        return _format_description(p), markdown

    return "", markdown


def _format_description(text: str) -> str:
    """Limpia y ajusta la descripción entre 50 y 160 caracteres óptimos de SEO."""
    # Eliminar Markdown inline (negritas, cursivas, links)
    clean = re.sub(r"[*_~`]", "", text)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    clean = " ".join(clean.split())
    if len(clean) > 160:
        cut = clean[:157]
        last_space = cut.rfind(" ")
        clean = (cut[:last_space] if last_space > 100 else cut) + "..."
    return clean


def extract_tags(content: str, theme: str, metadata: dict[str, Any] | None = None) -> list[str]:
    """
    Genera lista canónica de tags compatibles con Astro a partir de:
    - Tema principal
    - Keywords en metadata
    - Keywords en negrita frecuentes en el contenido
    """
    meta = metadata or {}
    tag_map: dict[str, list[str]] = {
        "cybersecurity": ["ciberseguridad", "seguridad-digital", "venezuela", "hacking-etico"],
        "legal_tech": ["legal-tech", "derecho-digital", "venezuela", "inteligencia-artificial"],
        "forensic_law": ["derecho-penal", "forense-digital", "tsj", "venezuela", "evidencia-digital"],
        "ai_data": ["inteligencia-artificial", "datos", "tecnologia", "machine-learning"],
        "sentencia_tsj": ["tsj", "jurisprudencia", "venezuela", "derecho", "casacion-penal"],
        "science_tech": ["ciencia", "tecnologia", "innovacion", "venezuela"],
    }
    tags = list(tag_map.get(theme, ["venezuela", "tecnologia"]))

    # Extra tags de metadata
    extra = meta.get("keywords") or meta.get("tags") or []
    if isinstance(extra, str):
        extra = [k.strip() for k in extra.split(",") if k.strip()]
    for t in extra:
        slug_t = slugify_astro(str(t))
        if slug_t and slug_t not in tags:
            tags.append(slug_t)

    # Identificar términos destacados en negrita relevantes si faltan tags
    if len(tags) < 4 and content:
        bold_matches = re.findall(r"\*\*([a-zA-ZáéíóúÁÉÍÓÚñÑ0-9\s]{3,25})\*\*", content)
        for bm in bold_matches:
            slug_b = slugify_astro(bm)
            if slug_b and len(slug_b) >= 3 and slug_b not in tags:
                tags.append(slug_b)
                if len(tags) >= 6:
                    break

    return tags[:6]


def clean_body_for_astro(markdown: str) -> str:
    """
    Limpia y optimiza el cuerpo Markdown para renderizado perfecto en Astro MD / MDX:
    1. Elimina encabezados redundantemente repetidos como '## Meta Descripción'
    2. Elimina bloques JSON-LD del cuerpo; el layout Astro gestiona los datos estructurados
    3. Normaliza encoding dañado típico de terminales Windows-1252 / mojibake
    4. Corrige espacios y saltos de línea excesivos
    """
    if not markdown:
        return ""

    # 1. Eliminar sección Meta Descripción si quedó en el texto
    markdown = re.sub(
        r"^##\s+Meta\s+Descripci[oó]n\s*\n+(?:>\s*.+\n?)+",
        "",
        markdown,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # 2. Eliminar bloques JSON-LD; no forman parte del cuerpo Markdown.
    markdown = re.sub(
        r"```(?:json)?\s*\{[\s\S]*?\"@context\"[\s\S]*?\}\s*```",
        "",
        markdown,
        flags=re.IGNORECASE,
    )
    markdown = re.sub(
        r"<!--\s*SCHEMA_JSONLD[\s\S]*?-->",
        "",
        markdown,
        flags=re.IGNORECASE,
    )

    # 3. Reparar mojibake / caracteres corruptos comunes de Windows
    mojibake_map = {
        "Ǹ": "é",
        "ǭ": "á",
        "ǧ": "ú",
        "Ǭ": "É",
        "ǻ": "ó",
        "Ǫ": "Ó",
        "ǖ": "ü",
        "ǫ": "ó",
        "ǵ": "í",
        "ǔ": "ú",
        "ǩ": "k",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€™": "'",
        "â€”": "—",
        "â€“": "–",
    }
    for bad, good in mojibake_map.items():
        markdown = markdown.replace(bad, good)

    # 4. Remover artefactos de metadata previa si existen en el cuerpo
    markdown = re.sub(r"^html_file:\s*.*$", "", markdown, flags=re.MULTILINE)
    markdown = re.sub(r"^generator:\s*.*$", "", markdown, flags=re.MULTILINE)

    # 5. Normalizar saltos de línea (máximo 2 consecutivos)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    return markdown.strip()


def export_as_astro_md(
    title: str,
    markdown_content: str,
    metadata: dict[str, Any] | None = None,
    author: str = "Jull Editor",
    editorial_layout: bool = False,
) -> str:
    """
    Genera un archivo Markdown puro para la colección Astro.
    `editorial_layout` se conserva por compatibilidad con clientes existentes,
    pero no altera el formato de salida.
    """
    meta = dict(metadata or {})
    if author and not meta.get("author"):
        meta["author"] = author

    # Si el contenido ya incluye frontmatter interno previo, separarlo
    content_to_process = markdown_content
    if content_to_process.startswith("---"):
        parts = content_to_process.split("---", 2)
        if len(parts) >= 3:
            content_to_process = parts[2].strip()

    # Extraer meta descripción
    extracted_desc, body = extract_description_from_body(content_to_process)
    description = meta.get("description") or extracted_desc
    if not description:
        description = f"Artículo técnico sobre {title} analizado con rigor jurídico y tecnológico."
    description = _format_description(description)

    # Limpiar cuerpo y evitar un segundo H1: el layout Astro usa `title`.
    body = clean_body_for_astro(body)
    body = re.sub(r"^#\s+.+(?:\r?\n|$)\s*", "", body, count=1)
    if re.search(r"</?[A-Za-z][\w-]*(?:\s+[^>]*)?\s*/?>", body):
        raise ValueError("El cuerpo debe ser Markdown estándar, no HTML.")

    # Normalizar título limpio
    clean_title = title.strip()
    if not clean_title:
        raise ValueError("El título es obligatorio para generar el archivo Astro.")
    if len(clean_title) > 200:
        raise ValueError("El título excede el máximo de 200 caracteres del esquema Astro.")

    # Fechas
    now = datetime.now()
    pub_date_str = meta.get("pub_date") or meta.get("date") or now.strftime("%Y-%m-%d")
    if " " in str(pub_date_str):
        pub_date_str = str(pub_date_str).split(" ")[0]

    # Slug y tags
    slug = meta.get("slug") or slugify_astro(title)
    theme = meta.get("theme", "science_tech")
    tags = extract_tags(body, theme, meta)[:6]

    # Estadísticas de lectura
    word_count = len(body.split())
    reading_time = max(1, round(word_count / 200))

    # Autor
    author_name = meta.get("author") or author

    frontmatter_data: dict[str, Any] = {
        "title": clean_title,
        "description": description,
        "pubDate": str(pub_date_str),
        "author": author_name,
        "slug": slug,
        "tags": tags,
        "category": meta.get("category") or theme,
        "readingTime": reading_time,
        "featured": bool(meta.get("featured", False)),
        "draft": bool(meta.get("draft", False)),
    }
    updated_date = meta.get("updated_date") or meta.get("updatedDate")
    if updated_date:
        frontmatter_data["updatedDate"] = str(updated_date)
    hero_image = meta.get("hero_image") or meta.get("heroImage")
    if hero_image:
        frontmatter_data["heroImage"] = str(hero_image)
    seo_keyword = meta.get("seo_keyword") or meta.get("seoKeyword") or meta.get("keyword")
    if seo_keyword:
        frontmatter_data["seoKeyword"] = str(seo_keyword)

    frontmatter = yaml.safe_dump(frontmatter_data, allow_unicode=True, sort_keys=False).strip()
    result = f"---\n{frontmatter}\n---\n\n{body.strip()}\n"
    from backend.astro_publisher import parse_frontmatter, validate_frontmatter

    errors = validate_frontmatter(parse_frontmatter(result) or {})
    if errors:
        raise ValueError("Frontmatter incompatible con Astro: " + "; ".join(errors))
    return result
