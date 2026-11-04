"""
Compilador Editorial Determinista para Astro Framework (Astro Content Collections).
Transforma contenido Markdown semántico generado por LLM en el diseño periodístico
de 3 columnas enriquecido con HTML5 / CSS editorial de 'Formato Blog -Astro.md'.
"""

from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime
from typing import Any

CATEGORY_MAP: dict[str, str] = {
    "cybersecurity": "Opinión Pericial",
    "legal_tech": "LegalTech",
    "forensic_law": "Investigación",
    "sentencia_tsj": "Opinión Pericial",
    "ai_data": "Guía Técnica",
    "science_tech": "Investigación",
}

DEFAULT_AUTHOR_BOX_HTML = """<div class="editorial-author-box">
<div class="display-flex flex-wrap flex-align-center gap-2">
<div>
<h3 class="font-sans-md text-bold text-primary-darker margin-0">{author_title}</h3>
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
</div>"""

MOJIBAKE_MAP = {
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


def slugify(text: str) -> str:
    """Convierte texto en un slug URL-friendly canónico para Astro."""
    if not text:
        return "articulo-blog"
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower()
    text = re.sub(r"[/_.:,]+", "-", text)
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    slug = text[:80].rstrip("-")
    return slug or "articulo-blog"


def clean_mojibake(text: str) -> str:
    """Repara caracteres corruptos habituales de codificaciones Windows-1252."""
    for bad, good in MOJIBAKE_MAP.items():
        text = text.replace(bad, good)
    return text


class AstroEditorialCompiler:
    """
    Compilador determinista de Markdown a layout periodístico enriquecido
    para el Framework Astro.
    """

    def __init__(self, metadata: dict[str, Any] | None = None):
        self.meta = metadata or {}

    def extract_frontmatter_metadata(
        self, title: str, body: str
    ) -> dict[str, Any]:
        """Extrae y normaliza los 12 campos canónicos del frontmatter YAML."""
        clean_title = title.replace('"', '\\"').strip()
        if not clean_title:
            h1_m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            clean_title = (
                h1_m.group(1).replace('"', '\\"').strip()
                if h1_m
                else "Artículo de Opinión Pericial"
            )

        slug = self.meta.get("slug") or slugify(clean_title)

        # Meta descripción
        description = self.meta.get("description", "")
        if not description:
            # Buscar blockquote de meta descripción o primer párrafo
            meta_m = re.search(
                r"^>\s*\*\*Meta\s+descripci[oó]n:\*\*\s*(.+)$",
                body,
                re.MULTILINE | re.IGNORECASE,
            )
            if meta_m:
                description = meta_m.group(1).strip()
            else:
                lead_m = re.search(
                    r"^>\s*\*\*📌\s*Resumen\s+Pr[aá]ctico.*:\*\*\s*(.+)$",
                    body,
                    re.MULTILINE | re.IGNORECASE,
                )
                if lead_m:
                    description = lead_m.group(1).strip()

        if not description:
            # Fallback al primer párrafo de texto
            for block in body.split("\n\n"):
                b = block.strip()
                if (
                    b
                    and not b.startswith(("#", ">", "```", "---", "|"))
                    and len(b) > 40
                ):
                    description = b
                    break

        if not description:
            description = f"Artículo de opinión pericial sobre {clean_title} con análisis técnico y forense."

        # Limpiar descripción y limitar a 155 caracteres
        clean_desc = re.sub(r"[*_~`]", "", description)
        clean_desc = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_desc)
        clean_desc = " ".join(clean_desc.split()).replace('"', '\\"')
        if len(clean_desc) > 160:
            cut = clean_desc[:157]
            last_space = cut.rfind(" ")
            clean_desc = (
                cut[:last_space] if last_space > 100 else cut
            ) + "..."

        # Fechas
        now = datetime.now()
        pub_date = (
            self.meta.get("pub_date")
            or self.meta.get("date")
            or now.strftime("%Y-%m-%d")
        )
        if " " in str(pub_date):
            pub_date = str(pub_date).split(" ")[0]
        updated_date = now.strftime("%Y-%m-%d")

        # Autor
        author = self.meta.get("author") or "Equipo Pericial sha256.us"

        # Tags
        raw_theme = self.meta.get("theme", "cybersecurity")
        category = self.meta.get(
            "category"
        ) or CATEGORY_MAP.get(raw_theme, "Opinión Pericial")

        tags: list[str] = []
        extra_tags = self.meta.get("tags") or self.meta.get("keywords") or []
        if isinstance(extra_tags, str):
            extra_tags = [t.strip() for t in extra_tags.split(",") if t.strip()]
        for t in extra_tags:
            s_t = slugify(str(t))
            if s_t and s_t not in tags:
                tags.append(s_t)

        if not tags:
            default_tags = {
                "cybersecurity": [
                    "ciberseguridad",
                    "informatica-forense",
                    "ingenieria-social",
                    "iso-27037",
                ],
                "legal_tech": [
                    "legal-tech",
                    "derecho-digital",
                    "evidencia-digital",
                    "venezuela",
                ],
                "forensic_law": [
                    "cadena-de-custodia",
                    "peritaje-forense",
                    "delitos-informaticos",
                ],
                "sentencia_tsj": [
                    "tsj-venezuela",
                    "jurisprudencia",
                    "prueba-digital",
                ],
                "ai_data": [
                    "inteligencia-artificial",
                    "seguridad-datos",
                    "auditoria",
                ],
            }
            tags = default_tags.get(
                raw_theme, ["ciberseguridad", "informatica-forense", "venezuela"]
            )

        # Keyword primaria
        seo_keyword = (
            self.meta.get("seo_keyword")
            or self.meta.get("keyword")
            or (tags[0] if tags else slug)
        )

        # Reading Time
        word_count = len(body.split())
        reading_time = max(1, round(word_count / 200))

        # Hero Image
        hero_image = (
            self.meta.get("hero_image")
            or self.meta.get("heroImage")
            or "../../assets/blog-placeholder-1.jpg"
        )

        return {
            "title": clean_title,
            "slug": slug,
            "description": clean_desc,
            "pubDate": str(pub_date),
            "updatedDate": str(updated_date),
            "author": author,
            "tags": tags[:6],
            "category": category,
            "heroImage": hero_image,
            "seoKeyword": seo_keyword,
            "readingTime": reading_time,
            "featured": bool(self.meta.get("featured", True)),
            "draft": bool(self.meta.get("draft", False)),
        }

    def render_frontmatter(self, meta: dict[str, Any]) -> str:
        """Genera el bloque YAML de frontmatter para Astro."""
        tags_str = "[" + ", ".join(f'"{t}"' for t in meta["tags"]) + "]"
        featured_str = "true" if meta["featured"] else "false"
        draft_str = "true" if meta["draft"] else "false"

        return f"""---
title: "{meta['title']}"
description: "{meta['description']}"
pubDate: {meta['pubDate']}
updatedDate: {meta['updatedDate']}
author: "{meta['author']}"
slug: "{meta['slug']}"
tags: {tags_str}
category: "{meta['category']}"
heroImage: "{meta['heroImage']}"
seoKeyword: "{meta['seoKeyword']}"
readingTime: {meta['readingTime']}
featured: {featured_str}
draft: {draft_str}
---
"""

    def parse_body_elements(self, raw_markdown: str) -> dict[str, Any]:
        """
        Analiza el markdown de entrada y extrae sus componentes editoriales:
        - Lead paragraph
        - Pull quote
        - Secciones H2 con párrafos y callouts
        - Preguntas frecuentes (FAQ)
        - Schema JSON-LD
        """
        text = clean_mojibake(raw_markdown)

        # Quitar frontmatter previo si existe
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                text = parts[2].strip()

        # Quitar H1 si existe (el layout de Astro ya lo dibuja)
        text = re.sub(r"^#\s+.*$\n*", "", text, flags=re.MULTILINE)

        # Quitar Meta Descripción si existe como sección o directiva
        text = re.sub(
            r"^##\s+Meta\s+Descripci[oó]n\s*\n+(?:>\s*.+\n?)+",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        text = re.sub(
            r"^>\s*\*\*Meta\s+descripci[oó]n:\*\*.*$\n*",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        text = re.sub(r"^META_DESC:.*$\n*", "", text, flags=re.MULTILINE)

        # Quitar Tabla de Contenidos (no aplica en diseño periodístico 3 columnas)
        text = re.sub(
            r"^##\s+.*Tabla\s+de\s+Contenidos.*$(?:\n+[-*0-9].*)+",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )

        # Quitar cinta de metadatos tipo "**Palabra Clave Primaria:** ..."
        text = re.sub(
            r"^\*\*Palabra\s+Clave\s+Primaria:\*\*.*$\n*",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )

        # Extraer bloques JSON-LD
        schema_blocks: list[str] = []

        def _schema_extractor(m: re.Match) -> str:
            schema_blocks.append(m.group(1).strip())
            return ""

        text = re.sub(
            r"```(?:json)?\s*(\{[\s\S]*?\"@context\"[\s\S]*?\})\s*```",
            _schema_extractor,
            text,
        )

        # Extraer FAQ si existe
        faq_items: list[tuple[str, str]] = []
        faq_section_match = re.search(
            r"##\s+.*?(?:Preguntas\s+Frecuentes|FAQ).*?\n([\s\S]*?)(?=(?:\n##\s|\Z))",
            text,
            re.IGNORECASE,
        )
        if faq_section_match:
            faq_raw = faq_section_match.group(1).strip()
            # Remover la sección del texto principal para que no se duplique en columnas
            text = (
                text[: faq_section_match.start()]
                + text[faq_section_match.end() :]
            )

            # Formato 1: ### ¿Pregunta? seguido de respuesta
            h3_blocks = re.findall(
                r"###\s*([^?\n]+?\?)\s*\n+([\s\S]*?)(?=(?:\n###|\Z))",
                faq_raw,
            )
            for q, a in h3_blocks:
                faq_items.append((q.strip(), a.strip()))

            # Formato 2: P: ... / R: ...
            if not faq_items:
                pr_pairs = re.findall(
                    r"(?:P|Pregunta|\d+\.?|\*\*P:?\*\*)\s*[:\.]?\s*[*_]*([^?\n]+?\?)[*_]*\s*\n+(?:R|Respuesta|\*\*R:?\*\*)\s*[:\.]?\s*([\s\S]*?)(?=(?:\n(?:P|Pregunta|\d+\.|\*\*P)|\Z))",
                    faq_raw,
                    re.IGNORECASE,
                )
                for q, a in pr_pairs:
                    faq_items.append((q.strip(), a.strip()))

            # Formato 3: **¿Pregunta?** seguido de párrafo
            if not faq_items:
                bold_pairs = re.findall(
                    r"\*\*([^?\n]+?\?)\*\*\s*\n+([\s\S]*?)(?=(?:\n\*\*|\Z))",
                    faq_raw,
                )
                for q, a in bold_pairs:
                    faq_items.append((q.strip(), a.strip()))

        # Quitar sección Sobre el Autor y Derechos de Autor del cuerpo si ya existen en markdown
        # (se renderizarán a través del bloque canónico de autor)
        text = re.sub(
            r"##\s+.*?(?:Sobre\s+el\s+Autor|Acerca\s+del\s+Autor).*?\n[\s\S]*?(?=(?:\n##\s|\Z))",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(
            r"##\s+.*?(?:Derechos\s+de\s+Autor|Fuente\s+de\s+Origen).*?\n[\s\S]*?(?=(?:\n##\s|\Z))",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Quitar descargos éticos del final
        text = re.sub(
            r">?\s*\*?Descargo\s+[eé]tico:?.*?\*?$\n*",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )

        # Extraer Lead Paragraph
        lead_paragraph = ""
        # Buscar Answer-First o primer párrafo contundente
        lead_match = re.search(
            r"(?:^En\s+resumen,\s*|^>.*Answer-First.*?\n>)(.+?)(?:\n\n|\Z)",
            text,
            re.MULTILINE | re.IGNORECASE | re.DOTALL,
        )
        if lead_match:
            lead_paragraph = lead_match.group(1).strip()
            # Remover si estaba en el texto
            text = text[: lead_match.start()] + text[lead_match.end() :]
        else:
            # Buscar blockquote de resumen práctico
            resumen_m = re.search(
                r"^>\s*\*\*📌\s*Resumen\s+Pr[aá]ctico.*:\*\*\s*(.+?)(?:\n\n|\Z)",
                text,
                re.MULTILINE | re.IGNORECASE | re.DOTALL,
            )
            if resumen_m:
                lead_paragraph = resumen_m.group(1).strip()
                text = text[: resumen_m.start()] + text[resumen_m.end() :]

        # Si aún no hay lead, tomar el primer bloque que no sea H2 ni blockquote
        text_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
        remaining_blocks: list[str] = []
        for blk in text_blocks:
            if not lead_paragraph and not blk.startswith(("#", ">", "```", "---", "|")):
                lead_paragraph = blk
            else:
                remaining_blocks.append(blk)

        if not lead_paragraph:
            lead_paragraph = "En el ámbito de la informática forense y la ciberseguridad, la rigurosidad técnica y la preservación probatoria definen la frontera entre la vulnerabilidad y la resiliencia judicial."

        # Limpiar tags markdown en lead
        lead_paragraph = re.sub(r"^>\s*", "", lead_paragraph).strip()

        # Si todo el contenido se consumió en el lead, asegurar que las columnas tengan contenido
        if not remaining_blocks:
            remaining_blocks.append(lead_paragraph)

        # Extraer Pull Quote
        pull_quote = ""
        # Buscar blockquote entrecomillado o con aforismo
        for idx, blk in enumerate(remaining_blocks):
            if blk.startswith(">") and ("«" in blk or '"' in blk or "30 Segundos" not in blk):
                clean_q = re.sub(r"^>\s*", "", blk).strip()
                clean_q = re.sub(r"^\*\*.*\*\*\s*", "", clean_q).strip()
                if 20 < len(clean_q) < 220:
                    pull_quote = clean_q
                    remaining_blocks.pop(idx)
                    break

        if not pull_quote:
            # Buscar una oración contundente con comillas o palabras clave
            reconstructed_text = "\n\n".join(remaining_blocks)
            quote_candidates = re.findall(r"[«\"]([^«\"\n]{25,180})[»\"]", reconstructed_text)
            if quote_candidates:
                pull_quote = quote_candidates[0].strip()

        if not pull_quote:
            pull_quote = "«El atacante moderno rara vez derriba la puerta de acero con fuerza bruta; simplemente persuade a alguien desde adentro para que le abra con una sonrisa.»"

        # Asegurar comillas latinas en el quote
        pull_quote = pull_quote.strip("«»\"' ")
        pull_quote = f"«{pull_quote}»"

        # Parsear las secciones restantes divididas por H2
        reconstructed = "\n\n".join(remaining_blocks)
        sections = self._split_into_sections(reconstructed)

        return {
            "lead": lead_paragraph,
            "quote": pull_quote,
            "sections": sections,
            "faq_items": faq_items,
            "schema_blocks": schema_blocks,
        }

    def _split_into_sections(self, text: str) -> list[dict[str, Any]]:
        """Divide el cuerpo en secciones delimitadas por encabezados H2."""
        # Encontrar todas las posiciones de H2
        h2_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
        matches = list(h2_pattern.finditer(text))

        sections: list[dict[str, Any]] = []

        if not matches:
            # Si no hay H2, tratar todo como una sola sección general
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            sections.append({
                "heading": "Análisis y Perspectiva Pericial",
                "paragraphs": paragraphs,
                "callout": None,
                "checklist": None,
            })
            return sections

        # Párrafos antes del primer H2 (si los hay)
        if matches[0].start() > 0:
            intro_raw = text[: matches[0].start()].strip()
            intro_paras = [p.strip() for p in intro_raw.split("\n\n") if p.strip()]
            if intro_paras:
                sections.append({
                    "heading": None,  # Sección introductoria previa al primer H2
                    "paragraphs": intro_paras,
                    "callout": None,
                    "checklist": None,
                })

        for i, m in enumerate(matches):
            raw_heading = m.group(1).strip()
            # Limpiar anclas tipo {#slug} o emojis del encabezado
            clean_heading = re.sub(r"\{#[^}]+\}", "", raw_heading).strip()
            clean_heading = re.sub(r"^[\d\.\s\-\:\#\U00010000-\U0010ffff]+", "", clean_heading).strip()
            if not clean_heading:
                clean_heading = raw_heading

            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_content = text[start:end].strip()

            paras: list[str] = []
            callout: dict[str, str] | None = None
            checklist: list[str] | None = None

            raw_blocks = [b.strip() for b in section_content.split("\n\n") if b.strip()]
            for blk in raw_blocks:
                # Detectar callouts / cajas destacadas
                if blk.startswith(">"):
                    lines = [re.sub(r"^>\s*", "", ln).strip() for ln in blk.splitlines()]
                    full_callout = " ".join(lines)
                    title_m = re.match(r"^\*\*([^\*]+)\*\*:?\s*(.*)$", full_callout)
                    if title_m:
                        c_title = title_m.group(1).strip()
                        c_body = title_m.group(2).strip()
                    else:
                        c_title = "Lección pericial crítica"
                        c_body = full_callout

                    callout = {"title": c_title, "body": c_body}

                # Detectar checklists o listas de pasos
                elif blk.startswith(("-", "*", "1.", "2.")):
                    list_items = [
                        re.sub(r"^[-*\d\.]+\s*", "", item_ln).strip()
                        for item_ln in blk.splitlines()
                        if item_ln.strip()
                    ]
                    if len(list_items) >= 2:
                        checklist = list_items
                    else:
                        paras.append(blk)
                else:
                    paras.append(blk)

            sections.append({
                "heading": clean_heading,
                "paragraphs": paras,
                "callout": callout,
                "checklist": checklist,
            })

        return sections

    def build_editorial_columns_html(self, sections: list[dict[str, Any]]) -> str:
        """
        Construye la maquetación en 3 columnas asegurando:
        - Columna 1: Dropcap en la primera letra del primer párrafo.
        - Secciones H2 con clase 'editorial-subhead'.
        - Cajas 'editorial-box' para lecciones y checklists.
        - Envoltorio 'editorial-col' para cada bloque.
        """
        columns_html: list[str] = []
        is_first_column = True

        for sec in sections:
            col_parts: list[str] = []
            heading = sec.get("heading")
            paragraphs = sec.get("paragraphs") or []
            callout = sec.get("callout")
            checklist = sec.get("checklist")

            # Inyectar H2 si existe
            if heading:
                col_parts.append(f'<h2 class="editorial-subhead">{html.escape(heading)}</h2>')

            # Renderizar párrafos
            for idx, p in enumerate(paragraphs):
                # Limpiar Markdown inline excesivo pero preservar enlaces y negritas
                p_clean = self._format_inline_html(p)

                if is_first_column and idx == 0:
                    # Inyectar letra capitular (Dropcap)
                    dropcap_char = p_clean[0].upper() if p_clean else "E"
                    rest_of_p = p_clean[1:] if len(p_clean) > 1 else ""
                    col_parts.append(
                        f'<p>\n<span class="editorial-dropcap">{dropcap_char}</span>{rest_of_p}\n</p>'
                    )
                    is_first_column = False
                else:
                    col_parts.append(f'<p>\n{p_clean}\n</p>')

            # Inyectar Callout Box si existe
            if callout:
                c_title = html.escape(callout.get("title", "Lección pericial crítica"))
                c_body = self._format_inline_html(callout.get("body", ""))
                col_parts.append(
                    f'<div class="editorial-box">\n<h4>{c_title}</h4>\n<p class="margin-0">\n{c_body}\n</p>\n</div>'
                )

            # Inyectar Checklist Box si existe
            if checklist:
                items_html = "\n".join(
                    f"<li>{self._format_inline_html(item)}</li>" for item in checklist
                )
                col_parts.append(
                    f'<div class="editorial-box" style="border-top-color: #005ea2;">\n'
                    f'<h3 class="font-sans-xs text-bold text-uppercase margin-top-0 margin-bottom-1 text-primary-dark">Protocolo de Actuación Pericial</h3>\n'
                    f'<ul class="margin-y-0 padding-left-2 font-sans-3xs line-height-sans-3 text-base-darkest">\n'
                    f'{items_html}\n'
                    f'</ul>\n</div>'
                )

            if col_parts:
                col_content = "\n".join(col_parts)
                columns_html.append(f'<div class="editorial-col">\n{col_content}\n</div>')

        return "\n\n".join(columns_html)

    def build_faq_html(self, faq_items: list[tuple[str, str]], title: str) -> str:
        """Construye el bloque de FAQ responsivo estilo USWDS en 2 columnas."""
        if not faq_items:
            # Fallback inteligente si no hubo FAQ explícito
            faq_items = [
                (
                    "¿Qué valor probatorio tiene un peritaje informático bajo norma ISO 27037?",
                    "Garantiza que la evidencia digital fue adquirida e intervenida sin alteración de sus hashes criptográficos, impidiendo que sea desestimada en sede judicial por ruptura de la cadena de custodia.",
                ),
                (
                    "¿Por qué es crítico no reiniciar los equipos tras un incidente?",
                    "La memoria volátil RAM contiene procesos efímeros, llaves criptográficas y conexiones vivas indispensables que se destruyen permanentemente al cortar el suministro eléctrico.",
                ),
            ]

        cards_html: list[str] = []
        border_classes = ["border-primary", "border-secondary-dark", "border-primary", "border-secondary-dark"]

        for idx, (question, answer) in enumerate(faq_items[:4]):
            border_cls = border_classes[idx % len(border_classes)]
            q_esc = html.escape(question)
            a_clean = self._format_inline_html(answer)

            card = f"""<div class="tablet:grid-col-6 margin-bottom-2">
<div class="bg-base-lightest padding-2 radius-md border-left-05 {border_cls}">
<h3 class="font-sans-xs text-bold text-primary-dark margin-top-0 margin-bottom-1">{q_esc}</h3>
<p class="font-sans-3xs text-base-dark line-height-sans-3 margin-0">
{a_clean}
</p>
</div>
</div>"""
            cards_html.append(card)

        grid_content = "\n".join(cards_html)

        return f"""<div class="margin-top-4 padding-top-3 border-top-1px border-base-lighter">
<h2 class="font-sans-lg text-bold text-primary-darker margin-bottom-2">Preguntas Frecuentes sobre Seguridad e Informática Forense</h2>
<div class="grid-row grid-gap-2">
{grid_content}
</div>
</div>"""

    def _format_inline_html(self, text: str) -> str:
        """Convierte Markdown inline (**bold**, *italic*, [link](url)) a HTML seguro."""
        # Convertir negritas
        text = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", text)
        # Convertir cursivas
        text = re.sub(r"\*([^\*]+)\*", r"<em>\1</em>", text)
        # Convertir enlaces
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r'<a href="\2" class="text-primary-dark text-bold text-no-underline hover:underline">\1</a>',
            text,
        )
        # Convertir `código inline`
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        return text.strip()

    def compile(self, title: str, raw_markdown: str) -> str:
        """
        Orquesta la compilación completa de Markdown a la plantilla de Astro.
        Retorna el documento final listo para copiar y pegar en Astro.
        """
        parsed = self.parse_body_elements(raw_markdown)
        frontmatter_meta = self.extract_frontmatter_metadata(title, raw_markdown)
        yaml_header = self.render_frontmatter(frontmatter_meta)

        lead = parsed["lead"]
        quote = parsed["quote"]
        columns_html = self.build_editorial_columns_html(parsed["sections"])
        faq_html = self.build_faq_html(parsed["faq_items"], frontmatter_meta["title"])

        author_box = DEFAULT_AUTHOR_BOX_HTML.format(
            author_title=html.escape(frontmatter_meta["author"])
        )

        # Ensamble final
        body = f"""<!-- ======================================================================= -->
<!-- COMIENZO DEL CUERPO DEL ARTÍCULO (FORMATO EDITORIAL 3 COLUMNAS)         -->
<!-- ======================================================================= -->

<div class="editorial-container">

<!-- SECCIÓN 1: LEAD / ENTRADILLA DE IMPACTO -->
<div class="editorial-lead">
{lead}
</div>

<!-- SECCIÓN 2: CITA DESTACADA EDITORIAL (PULL QUOTE) -->
<div class="editorial-quote">
{quote}
</div>

<!-- SECCIÓN 3: CUERPO EDITORIAL EN 3 COLUMNAS -->
<div class="editorial-three-columns">
{columns_html}
</div>
<!-- FIN DE LAS 3 COLUMNAS -->

<!-- SECCIÓN 4: PREGUNTAS FRECUENTES (FAQ E-E-A-T PARA GOOGLE PAA) -->
{faq_html}

<!-- SECCIÓN 5: BIO DEL AUTOR Y SEÑALES DE AUTORIDAD E-E-A-T -->
{author_box}

</div>
<!-- FIN DE EDITORIAL CONTAINER -->
"""

        # Si se extrajeron microdatos Schema.org, añadirlos como comentarios HTML al pie
        if parsed["schema_blocks"]:
            schema_comments = "\n\n".join(
                f"<!-- SCHEMA_JSONLD\n{s}\n-->" for s in parsed["schema_blocks"]
            )
            body += f"\n\n{schema_comments}\n"

        return yaml_header + "\n" + body
