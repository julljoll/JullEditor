"""
Módulo de Extracción y Limpieza de Artículos desde URLs.
Utiliza HTTPX y BeautifulSoup con heurísticas avanzadas de legibilidad,
con fallback opcional para Playwright.
"""

import ipaddress
import re
import socket
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from backend.logger_config import get_logger

logger = get_logger("scraper")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def is_safe_url(url: str) -> bool:
    """
    Valida que una URL use http/https y no apunte a localhost, loopback,
    rangos privados o link-local (SSRF protection).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        hostname_clean = hostname.strip().lower()
        if hostname_clean in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
            return False
            
        addr_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)
            if (
                ip_obj.is_loopback
                or ip_obj.is_private
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            ):
                return False
        return True
    except Exception as e:
        logger.warning(f"Validación SSRF falló para '{url}': {e}")
        return False

async def extract_article_from_url(url: str) -> dict[str, Any]:
    """
    Descarga una página web y extrae el texto central, título y metadatos relevantes.
    Incorpora soporte multi-etapa (HTTPX -> urllib -> Playwright).
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    if not is_safe_url(url):
        logger.warning(f"URL rechazada por seguridad SSRF: {url}")
        raise ValueError("La URL proporcionada no es segura o apunta a una dirección interna o no permitida.")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate",
        "Cache-Control": "max-age=0",
        "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    
    html_content = ""
    timeout = httpx.Timeout(connect=8.0, read=18.0, write=5.0, pool=10.0)
    
    # 1. Intento primario con HTTPX
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers)
            if response.status_code in (200, 201, 202, 203):
                html_content = response.text
                logger.info(f"HTML descargado con éxito vía HTTPX para: {url} ({len(html_content)} bytes)")
            elif response.text and len(response.text) > 1000:
                html_content = response.text
                logger.info(f"HTML obtenido con status {response.status_code} pero con contenido usable: {url} ({len(html_content)} bytes)")
            else:
                logger.warning(f"HTTPX retornó status {response.status_code} para: {url}")
    except Exception as e:
        logger.warning(f"HTTPX falló para {url}: {e}")
        
    # 2. Fallback secundario con urllib.request (evita bloqueos de fingerprints HTTPX)
    if not html_content or len(html_content) < 500:
        try:
            logger.info(f"Iniciando fallback con urllib para: {url}")
            import gzip
            import ssl
            import urllib.request
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                raw_bytes = resp.read()
                try:
                    html_content = gzip.decompress(raw_bytes).decode('utf-8', errors='ignore')
                except Exception:
                    html_content = raw_bytes.decode('utf-8', errors='ignore')
                logger.info(f"urllib extrajo {len(html_content)} bytes para: {url}")
        except Exception as ue:
            logger.info(f"Nota urllib fallback: {ue}")

    # 3. Fallback terciario con Playwright si está disponible
    if not html_content or len(html_content) < 500:
        try:
            logger.info(f"Iniciando fallback con Playwright para: {url}")
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(user_agent=USER_AGENT)
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                html_content = await page.content()
                await browser.close()
                logger.info(f"Playwright extrajo {len(html_content)} bytes para: {url}")
        except Exception as pe:
            logger.info(f"Nota Playwright fallback: {pe}")

    if not html_content:
        logger.error(f"No fue posible acceder al contenido de la URL: {url}")
        raise ValueError(f"No fue posible acceder al contenido de la URL: {url}. Verifica que el sitio permita acceso público o copia y pega el texto directamente en 'Pegar Texto'.")

    return parse_html_to_clean_article(html_content, url)

def parse_html_to_clean_article(html: str, url: str) -> dict[str, Any]:
    """
    Limpia y estructura el contenido HTML eliminando ruido (nav, footers, scripts, ads),
    y localiza la imagen de cabecera original (og:image, twitter:image, thumbnail, hero).
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Extraer Título
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.find("h1"):
        title = soup.find("h1").get_text().strip()
    elif soup.title:
        title = soup.title.get_text().strip()
        
    # 2. Extraer Meta Description original
    meta_desc = ""
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if og_desc and og_desc.get("content"):
        meta_desc = og_desc["content"].strip()

    # 2b. Extraer Idioma Original
    source_lang = ""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        source_lang = html_tag["lang"].strip()
    if not source_lang:
        og_locale = soup.find("meta", property="og:locale")
        if og_locale and og_locale.get("content"):
            source_lang = og_locale["content"].strip()

    # 2c. Extraer Autor Original
    source_author = ""
    author_meta = (
        soup.find("meta", attrs={"name": "author"}) or
        soup.find("meta", property="article:author") or
        soup.find("meta", property="og:article:author")
    )
    if author_meta and author_meta.get("content"):
        source_author = author_meta["content"].strip()
    if not source_author:
        author_el = soup.find(attrs={"itemprop": "author"})
        if author_el:
            source_author = author_el.get_text().strip()
    if not source_author:
        for script_tag in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                ld_data = json.loads(script_tag.string or "{}")
                if isinstance(ld_data, dict) and ld_data.get("author"):
                    author_obj = ld_data["author"]
                    if isinstance(author_obj, dict):
                        source_author = author_obj.get("name", "")
                    elif isinstance(author_obj, str):
                        source_author = author_obj
                    if source_author:
                        break
            except Exception:
                pass

    # 2d. Extraer Fecha de Publicación Original
    source_date = ""
    date_meta = (
        soup.find("meta", property="article:published_time") or
        soup.find("meta", property="og:article:published_time") or
        soup.find("meta", attrs={"name": "date"}) or
        soup.find("meta", attrs={"name": "pubdate"}) or
        soup.find("time", attrs={"datetime": True})
    )
    if date_meta:
        source_date = (date_meta.get("content") or date_meta.get("datetime", "")).strip()

    # 2e. Extraer Sección/Categoría
    source_section = ""
    section_meta = (
        soup.find("meta", property="article:section") or
        soup.find("meta", property="og:article:section")
    )
    if section_meta and section_meta.get("content"):
        source_section = section_meta["content"].strip()

    # 3. Localizar Imagen de Cabecera Original
    image_url = ""
    og_img = (
        soup.find("meta", property="og:image") or
        soup.find("meta", property="og:image:secure_url") or
        soup.find("meta", attrs={"name": "twitter:image"}) or
        soup.find("meta", attrs={"name": "twitter:image:src"}) or
        soup.find("link", rel="image_src") or
        soup.find("meta", itemprop="image")
    )
    if og_img:
        img_src = og_img.get("content") or og_img.get("href")
        if img_src and not img_src.startswith("data:"):
            image_url = urljoin(url, img_src.strip())

    if not image_url:
        img_candidates = soup.find_all("img")
        for img in img_candidates:
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or img.get("srcset")
            if src:
                if " " in src and "," in src:
                    src = src.split(",")[0].strip().split(" ")[0]
                elif " " in src:
                    src = src.split(" ")[0]
                    
                src_lower = src.lower()
                if not any(noise in src_lower for noise in ["logo", "avatar", "icon", "pixel", "1x1", "spacer", "badge", "ad-"]):
                    image_url = urljoin(url, src.strip())
                    break

    # 4. Eliminar elementos de ruido estructural sin eliminar contenedores principales
    tags_to_remove = [
        "script", "style", "nav", "footer", "header", "aside", "form",
        "noscript", "iframe", "svg", "button", "input", "select", "dialog"
    ]
    for tag in tags_to_remove:
        for match in soup.find_all(tag):
            match.decompose()

    # 5. Localizar candidato a contenedor principal ANTES de borrar elementos por clase
    candidates = []
    for art in soup.find_all("article"):
        candidates.append(art)
        
    main_elem = soup.find("main") or soup.find(attrs={"role": "main"})
    if main_elem:
        candidates.append(main_elem)
        
    for elem in soup.find_all(attrs={"class": re.compile(r"post-content|article-body|entry-content|story-body|content-body|c-article-body|blog-post|single-post|rich-text|article__content", re.IGNORECASE)}):
        candidates.append(elem)

    for elem in soup.find_all(attrs={"id": re.compile(r"article|content|main-content|story|post", re.IGNORECASE)}):
        candidates.append(elem)
        
    if soup.body:
        candidates.append(soup.body)

    def score_container(container) -> int:
        if not container:
            return 0
        p_elems = container.find_all("p")
        return sum(len(p.get_text().strip()) for p in p_elems if len(p.get_text().strip()) > 15)

    content_container = max(candidates, key=score_container) if candidates else (soup.body or soup)

    # 6. Eliminar elementos publicitarios puntuales sin destruir contenedores padre con layout classes
    noise_patterns = re.compile(r"\b(ad-box|advertisement|ad-container|social-share|share-buttons|cookie-notice|cookie-banner|newsletter-signup|comments-area)\b", re.IGNORECASE)
    for element in list(content_container.find_all(attrs={"class": noise_patterns})):
        if len(element.get_text().strip()) < 300 and not element.find(["h1", "h2", "article"]):
            element.decompose()

    # 7. Extraer párrafos y encabezados con texto significativo
    extracted_paragraphs = []
    if content_container:
        for elem in content_container.find_all(["p", "h2", "h3", "h4", "li", "blockquote"]):
            text = elem.get_text().strip()
            if len(text) > 15 and not any(noise in text.lower() for noise in [
                "suscríbete", "cookies", "todos los derechos reservados", 
                "política de privacidad", "aviso legal", "configuración de cookies"
            ]):
                extracted_paragraphs.append(text)
    
    clean_text = "\n\n".join(extracted_paragraphs)
    
    if not clean_text or len(clean_text) < 100:
        lines = [line.strip() for line in (content_container or soup).get_text().splitlines() if len(line.strip()) > 25]
        clean_text = "\n\n".join(lines[:60])

    word_count = len(clean_text.split())
    logger.info(f"Extracción completada: '{title}' ({word_count} palabras, imagen: {'Sí' if image_url else 'No'})")

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "image_url": image_url,
        "source_lang": source_lang,
        "source_author": source_author,
        "source_date": source_date,
        "source_section": source_section,
        "text": clean_text,
        "word_count": word_count,
        "status": "success"
    }
