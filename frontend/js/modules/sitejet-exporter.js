/**
 * Módulo de Exportación Especializado para Sitejet Builder (Namecheap CMS)
 * 
 * Garantiza:
 * 1. Copia 100% completa del artículo (H1, Banner 16:9, Meta descripción, subtítulos,
 *    párrafos justificados, listas, citas periciales, tablas, FAQ, autor y fuentes).
 * 2. Mecanismo de copiado ultra-robusto (4-stage clipboard fallback) sin fallos ni bloqueos.
 * 3. Supresión de scripts en el Rich Text para evitar que el sanitizador WYSIWYG de Sitejet
 *    trunque o rechace el contenido pegado.
 * 4. Modal Kit SEO & Schema interactivo con copia de 1-clic para Title, Slug, Meta, Alt,
 *    Keywords y Schema.org JSON-LD para la configuración de página o bloque HTML.
 * 5. Descarga de imagen en PNG 16:9 y soporte para CDN de Sitejet Media Manager.
 */

import { toast } from "./toast-notifications.js";
import { unwrapMagazine } from "./markdown-renderer.js";

// Caché en memoria para evitar conversiones redundantes de imagen
const pngDataUriCache = new Map();

/**
 * Función ultra-robusta de copiado al portapapeles con 5 niveles de fallback
 * (ClipboardItem HTML -> synthetic copy event -> contentEditable -> writeText -> textarea)
 * @param {string} htmlContent Contenido HTML enriquecido
 * @param {string} plainTextContent Contenido en texto plano alternativo
 * @returns {Promise<boolean>} true si se copió con éxito
 */
export async function copyToClipboardRobust(htmlContent, plainTextContent = "") {
  if (!htmlContent) return false;
  const plain = plainTextContent || htmlContent.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

  // Nivel 1: API moderna ClipboardItem con formatos text/html y text/plain
  if (navigator.clipboard && window.ClipboardItem) {
    try {
      const htmlBlob = new Blob([htmlContent], { type: "text/html" });
      const textBlob = new Blob([plain], { type: "text/plain" });
      const item = new ClipboardItem({
        "text/html": htmlBlob,
        "text/plain": textBlob
      });
      await navigator.clipboard.write([item]);
      return true;
    } catch (e) {
      console.warn("ClipboardItem write falló, pasando a synthetic copy event:", e);
    }
  }

  // Nivel 2: Evento 'copy' sintético con e.clipboardData (Insuperable en compatibilidad de Rich Text)
  try {
    let copyHandled = false;
    const copyListener = (e) => {
      e.preventDefault();
      if (e.clipboardData) {
        e.clipboardData.setData("text/html", htmlContent);
        e.clipboardData.setData("text/plain", plain);
        copyHandled = true;
      }
    };

    document.addEventListener("copy", copyListener);
    const execOk = document.execCommand("copy");
    document.removeEventListener("copy", copyListener);

    if (execOk || copyHandled) return true;
  } catch (e) {
    console.warn("Evento copy falló:", e);
  }

  // Nivel 3: execCommand con contentEditable enfocado en el DOM
  try {
    const tempDiv = document.createElement("div");
    tempDiv.contentEditable = "true";
    tempDiv.style.cssText = "position: fixed; left: 0; top: 0; opacity: 0.01; z-index: 99999;";
    tempDiv.innerHTML = htmlContent;
    document.body.appendChild(tempDiv);
    tempDiv.focus();

    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(tempDiv);
    selection.removeAllRanges();
    selection.addRange(range);

    const ok = document.execCommand("copy");
    selection.removeAllRanges();
    document.body.removeChild(tempDiv);

    if (ok) return true;
  } catch (e) {
    console.warn("execCommand contentEditable falló:", e);
  }

  // Nivel 4: navigator.clipboard.writeText (texto plano / HTML)
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(htmlContent);
      return true;
    } catch (_) {}
  }

  // Nivel 5: execCommand clásico sobre textarea
  try {
    const ta = document.createElement("textarea");
    ta.value = htmlContent;
    ta.style.cssText = "position: fixed; left: 0; top: 0; opacity: 0.01; z-index: 99999;";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    if (ok) return true;
  } catch (_) {}

  return false;
}

/**
 * Convierte un SVG procedural a PNG Data-URI (1200x675) usando un Canvas del navegador.
 * @param {string} svgUrl URL relativa o absoluta del banner SVG
 * @returns {Promise<string>} PNG Data-URI en base64
 */
export async function convertSvgToPngDataUrl(svgUrl) {
  if (!svgUrl) return "";
  if (pngDataUriCache.has(svgUrl)) {
    return pngDataUriCache.get(svgUrl);
  }

  if (svgUrl.startsWith("data:image/png") || svgUrl.startsWith("data:image/jpeg")) {
    return svgUrl;
  }

  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      resolve(svgUrl);
    }, 1800);

    try {
      let resolvedUrl = svgUrl;
      if (svgUrl.startsWith("/")) {
        resolvedUrl = window.location.origin + svgUrl;
      }

      fetch(resolvedUrl)
        .then(res => res.ok ? res.text() : "")
        .then(svgText => {
          const img = new Image();
          img.onload = () => {
            clearTimeout(timeout);
            try {
              const canvas = document.createElement("canvas");
              canvas.width = 1200;
              canvas.height = 675;
              const ctx = canvas.getContext("2d");
              if (!ctx) {
                resolve(resolvedUrl);
                return;
              }
              ctx.fillStyle = "#111111";
              ctx.fillRect(0, 0, 1200, 675);
              ctx.drawImage(img, 0, 0, 1200, 675);
              const pngDataUrl = canvas.toDataURL("image/png", 0.95);
              pngDataUriCache.set(svgUrl, pngDataUrl);
              resolve(pngDataUrl);
            } catch (_) {
              resolve(resolvedUrl);
            }
          };
          img.onerror = () => {
            clearTimeout(timeout);
            resolve(resolvedUrl);
          };

          if (svgText && svgText.includes("<svg")) {
            const blob = new Blob([svgText], { type: "image/svg+xml;charset=utf-8" });
            img.src = URL.createObjectURL(blob);
          } else {
            img.src = resolvedUrl;
          }
        })
        .catch(() => {
          clearTimeout(timeout);
          resolve(resolvedUrl);
        });
    } catch (_) {
      clearTimeout(timeout);
      resolve(svgUrl);
    }
  });
}

/**
 * Extrae metadatos SEO limpios del markdown y DOM para Sitejet Builder
 * @param {object} state Estado global de la aplicación
 * @returns {object} Metadatos para Sitejet Kit
 */
export function extractSeoKitData(state) {
  const md = (state && state.currentRawMarkdown) || "";
  const articleView = document.getElementById("articleView");
  const previewTitle = document.getElementById("previewTitle");
  const previewSnippet = document.getElementById("previewSnippet");
  const previewSlug = document.getElementById("previewSlug");
  const sourceTitle = document.getElementById("sourceTitle");

  // 1. Título
  let title = (sourceTitle && sourceTitle.value.trim()) || "";
  if (!title) {
    const titleMatch = md.match(/Meta Title:\s*(.*)/i) || md.match(/^# (.*)/m);
    if (titleMatch && titleMatch[1]) {
      title = titleMatch[1].replace(/[*#]/g, "").trim();
    } else if (previewTitle && previewTitle.innerText && !previewTitle.innerText.includes("Optimizado")) {
      title = previewTitle.innerText.trim();
    } else if (articleView) {
      const h1El = articleView.querySelector("h1");
      if (h1El) title = h1El.innerText.trim();
    }
  }

  // 2. Meta Descripción
  let metaDescription = "";
  const descMatch = md.match(/Meta Descripci[oó]n:\s*(.*)/i) || md.match(/^\>\s*\*\*Meta descripci[oó]n:\*\*\s*(.*)/im);
  if (descMatch && descMatch[1]) {
    metaDescription = descMatch[1].replace(/[*#]/g, "").trim();
  } else if (previewSnippet && previewSnippet.innerText && !previewSnippet.innerText.includes("aparecerá aquí")) {
    metaDescription = previewSnippet.innerText.trim();
  } else if (articleView) {
    const calloutEl = articleView.querySelector(".meta-description-callout .meta-description-text");
    if (calloutEl) metaDescription = calloutEl.innerText.trim();
  }

  // 3. Slug sugerido
  let slug = "";
  const slugMatch = md.match(/Slug(?: Sugerido)?:\s*([^\n|]+)/i);
  if (slugMatch && slugMatch[1]) {
    slug = slugMatch[1].trim().toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/--+/g, "-");
  } else if (previewSlug && previewSlug.innerText && !previewSlug.innerText.includes("slug-del-articulo")) {
    slug = previewSlug.innerText.replace(/.*articulos\//, "").trim();
  } else if (title) {
    slug = title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  // 4. Alt Text de la Imagen
  let imageAlt = title ? `Cabecera para artículo: ${title}` : "Cabecera de artículo optimizado para SEO";

  // 5. Keywords
  let keywords = "";
  const kwMatch = md.match(/\*\*Palabra Clave Primaria:\*\*(.*?)(?=\s*\||\n|$)/i);
  const lsiMatch = md.match(/\*\*Keywords LSI:\*\*(.*?)(?=\s*\||\n|$)/i) || md.match(/\*\*Palabras Clave Secundarias:\*\*(.*?)(?=\s*\||\n|$)/i);
  const kwList = [];
  if (kwMatch && kwMatch[1]) kwList.push(kwMatch[1].trim());
  if (lsiMatch && lsiMatch[1]) kwList.push(lsiMatch[1].trim());
  keywords = kwList.join(", ");

  // 6. Schema.org JSON-LD
  let schemaJsonLd = "";
  const schemaMatches = md.match(/```json\s*(\{[\s\S]*?"@context"\s*:\s*"https:\/\/schema\.org"[\s\S]*?\})\s*```/gim);
  if (schemaMatches && schemaMatches.length > 0) {
    const rawJson = schemaMatches[0].replace(/```json\s*/i, "").replace(/```\s*$/i, "").trim();
    try {
      const parsed = JSON.parse(rawJson);
      schemaJsonLd = JSON.stringify(parsed, null, 2);
    } catch (_) {
      schemaJsonLd = rawJson;
    }
  } else if (articleView) {
    const preEl = articleView.querySelector("pre code");
    if (preEl && preEl.innerText.includes('"@context"')) {
      schemaJsonLd = preEl.innerText.trim();
    }
  }

  // Si no hay Schema explícito pero hay título, generar uno de plantilla Article
  if (!schemaJsonLd && title) {
    schemaJsonLd = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      "headline": title,
      "description": metaDescription || title,
      "datePublished": new Date().toISOString().split("T")[0],
      "author": {
        "@type": "Person",
        "name": "Redacción Jurídica Especializada"
      }
    }, null, 2);
  }

  const bannerImgEl = document.getElementById("headerBannerImg");
  const bannerUrl = (state && state.currentBannerUrl) || (bannerImgEl ? bannerImgEl.src : "");

  return {
    title: title || "Artículo de Blog Optimizado",
    metaDescription: metaDescription || "",
    slug: slug || "articulo-blog",
    imageAlt,
    keywords,
    schemaJsonLd,
    bannerUrl
  };
}

/**
 * Genera HTML completo optimizado para el editor Rich Text (WYSIWYG) de Sitejet Builder.
 * Preserva TODO el artículo: Título H1, cabecera 16:9, subtítulos H2/H3, párrafos justificados,
 * listas, tablas, FAQ, autor y callouts formateados.
 * NO incluye etiquetas <script> para evitar que el sanitizador WYSIWYG de Sitejet rechace el pegado.
 * @param {object} state Estado global
 * @param {object} options Opciones { sitejetMediaUrl?: string, pngDataUrl?: string, excludeH1?: boolean }
 * @returns {string} HTML completo listo para pegar en Sitejet Rich Text
 */
export function generateSitejetRichTextHtml(state, options = {}) {
  const articleView = document.getElementById("articleView");
  if (!articleView || !articleView.innerHTML) return "";

  const seoData = extractSeoKitData(state);
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = articleView.innerHTML;
  unwrapMagazine(tempDiv);

  // 1. Eliminar cursores de streaming y elementos auxiliares
  tempDiv.querySelectorAll(".streaming-cursor").forEach(el => el.remove());

  // 2. Título H1 del Artículo
  if (options.excludeH1) {
    const firstH1 = tempDiv.querySelector("h1");
    if (firstH1) firstH1.remove();
  } else {
    if (!tempDiv.querySelector("h1") && seoData.title) {
      const h1El = document.createElement("h1");
      h1El.innerText = seoData.title;
      tempDiv.insertBefore(h1El, tempDiv.firstChild);
    }
    tempDiv.querySelectorAll("h1").forEach(el => {
      el.setAttribute("style", "color: #008726; font-size: 28px; font-weight: 700; border-bottom: 2px solid #008726; padding-bottom: 8px; text-transform: uppercase; margin-top: 10px; margin-bottom: 16px; font-family: Arial, sans-serif;");
    });
  }

  // 3. Estilos Semánticos Inline para Sitejet Rich Text
  tempDiv.querySelectorAll("h2").forEach(el => {
    el.setAttribute("style", "color: #8A6800; font-size: 22px; font-weight: 700; margin-top: 32px; margin-bottom: 14px; border-bottom: 2px solid #FECF06; padding-bottom: 6px; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll("h3, h4").forEach(el => {
    el.setAttribute("style", "color: #1A6B1A; font-size: 18px; font-weight: 600; border-left: 4px solid #1A6B1A; background: #eef9e8; padding: 10px 14px; margin-top: 22px; margin-bottom: 12px; border-radius: 0 4px 4px 0; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll("p").forEach(el => {
    el.setAttribute("style", "font-size: 16px; line-height: 1.7; color: #222222; text-align: justify; margin-bottom: 16px; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll("strong").forEach(el => {
    el.setAttribute("style", "color: #000000; font-weight: 700; background: #FFF9DB; padding: 1px 4px; border-radius: 2px;");
  });

  tempDiv.querySelectorAll("em").forEach(el => {
    el.setAttribute("style", "color: #333333; font-style: italic;");
  });

  tempDiv.querySelectorAll("a").forEach(el => {
    el.setAttribute("style", "color: #1A6B1A; font-weight: 700; text-decoration: underline;");
  });

  tempDiv.querySelectorAll("ul, ol").forEach(el => {
    el.setAttribute("style", "padding-left: 24px; margin-bottom: 18px; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll("li").forEach(el => {
    el.setAttribute("style", "font-size: 15.5px; line-height: 1.65; margin-bottom: 6px; color: #222222;");
  });

  tempDiv.querySelectorAll("table").forEach(el => {
    el.setAttribute("style", "width: 100%; border-collapse: collapse; margin: 20px 0; font-family: Arial, sans-serif; font-size: 14.5px;");
  });

  tempDiv.querySelectorAll("th").forEach(el => {
    el.setAttribute("style", "background: #8A6800; color: #ffffff; padding: 10px 12px; text-align: left; border: 1px solid #d4c58f; font-weight: 700;");
  });

  tempDiv.querySelectorAll("td").forEach(el => {
    el.setAttribute("style", "padding: 9px 12px; border: 1px solid #e2e8f0; vertical-align: top;");
  });

  tempDiv.querySelectorAll("blockquote").forEach(el => {
    if (!el.getAttribute("style")) {
      el.setAttribute("style", "background: #f8f9fa; border-left: 4px solid #008726; padding: 12px 18px; margin: 18px 0; color: #333333; font-style: italic; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
    }
  });

  // 4. Transformar Callouts a blockquotes compatibles con Sitejet
  tempDiv.querySelectorAll(".meta-description-callout").forEach(el => {
    const textEl = el.querySelector(".meta-description-text");
    const text = textEl ? textEl.innerHTML : el.innerHTML;
    const bq = document.createElement("blockquote");
    bq.setAttribute("style", "background: #fffbe6; border: 1px solid #ffe066; border-left: 4px solid #8A6800; padding: 14px 18px; margin: 20px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
    bq.innerHTML = `<p style="font-size: 12px; font-weight: 700; color: #8A6800; text-transform: uppercase; margin: 0 0 6px 0; letter-spacing: 0.5px; font-family: monospace;">🔍 META DESCRIPCIÓN (CTR SNIPPET)</p><p style="font-style: italic; color: #222222; font-size: 15px; line-height: 1.5; margin: 0;">${text}</p>`;
    if (el.parentNode) el.parentNode.replaceChild(bq, el);
  });

  tempDiv.querySelectorAll(".source-summary-callout").forEach(el => {
    const textEl = el.querySelector(".source-summary-text");
    const labelEl = el.querySelector(".source-summary-label");
    const text = textEl ? textEl.innerHTML : el.innerHTML;
    const label = labelEl ? labelEl.innerText.replace(/^[^\w\s]+/g, "").trim() : "RESUMEN PRÁCTICO DE LA FUENTE";
    const bq = document.createElement("blockquote");
    bq.setAttribute("style", "background: #eef9e8; border: 1px solid #c6f6d5; border-left: 4px solid #1A6B1A; padding: 14px 18px; margin: 20px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
    bq.innerHTML = `<p style="font-size: 12px; font-weight: 700; color: #1A6B1A; text-transform: uppercase; margin: 0 0 6px 0; letter-spacing: 0.5px; font-family: monospace;">📖 ${label.toUpperCase()}</p><p style="color: #222222; font-size: 15px; line-height: 1.55; margin: 0;">${text}</p>`;
    if (el.parentNode) el.parentNode.replaceChild(bq, el);
  });

  tempDiv.querySelectorAll(".paragraph-takeaway").forEach(el => {
    el.setAttribute("style", "background: #e8f8ed; border-left: 3px solid #1A6B1A; padding: 10px 14px; margin: 14px 0; border-radius: 0 6px 6px 0; color: #005a19; font-size: 15px; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll(".copyright-card").forEach(el => {
    el.setAttribute("style", "background: #fdfdfd; border: 1px solid #e2e8f0; border-left: 4px solid #1A6B1A; padding: 16px 20px; margin: 24px 0; border-radius: 0 6px 6px 0; color: #333333; font-size: 14px; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll(".faq-section-card").forEach(el => {
    el.setAttribute("style", "background: #fffbe6; border: 1px solid #ffe066; border-left: 4px solid #8A6800; padding: 18px 22px; margin: 24px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll(".faq-question").forEach(el => {
    el.setAttribute("style", "background: #fff9db; border-left: 3px solid #8A6800; padding: 10px 14px; margin: 8px 0 4px 0; border-radius: 0 4px 4px 0; font-size: 16px; color: #222222; font-weight: 600;");
  });

  tempDiv.querySelectorAll(".faq-answer").forEach(el => {
    el.setAttribute("style", "padding: 8px 14px 8px 18px; margin: 0 0 8px 0; font-size: 15px; color: #333333; line-height: 1.55;");
  });

  tempDiv.querySelectorAll(".author-bio-card").forEach(el => {
    el.setAttribute("style", "background: #eef9e8; border: 1px solid #c6f6d5; border-left: 4px solid #1A6B1A; padding: 16px 20px; margin: 24px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll(".toc-card, nav.toc-card").forEach(el => {
    el.setAttribute("style", "background: #f8f9fa; border: 1px solid #e2e8f0; border-left: 4px solid #8A6800; padding: 16px 20px; margin: 18px 0 24px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll(".seo-badge-container").forEach(el => {
    el.setAttribute("style", "display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; padding: 12px; background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 6px; font-family: Arial, sans-serif;");
  });

  tempDiv.querySelectorAll(".seo-badge").forEach(el => {
    el.setAttribute("style", "font-size: 12px; background: #fffbe6; border: 1px solid #ffe066; padding: 4px 10px; border-radius: 4px; color: #333333; font-family: monospace;");
  });

  // Ocultar pre con Schema en el pegado Rich Text (se gestiona vía Kit SEO o Bloque HTML)
  tempDiv.querySelectorAll("pre").forEach(el => {
    if (el.innerText.includes('"@context"')) {
      el.remove();
    } else {
      el.setAttribute("style", "background: #111111; color: #00FF41; padding: 14px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 13.5px; margin: 16px 0; line-height: 1.5;");
    }
  });

  // 5. Inserción de la Imagen Cabecera (16:9)
  let finalImageUrl = "";
  if (options.sitejetMediaUrl && options.sitejetMediaUrl.trim()) {
    finalImageUrl = options.sitejetMediaUrl.trim();
  } else if (options.pngDataUrl) {
    finalImageUrl = options.pngDataUrl;
  } else if (seoData.bannerUrl && pngDataUriCache.has(seoData.bannerUrl)) {
    finalImageUrl = pngDataUriCache.get(seoData.bannerUrl);
  } else if (seoData.bannerUrl) {
    finalImageUrl = seoData.bannerUrl.startsWith("/") 
      ? window.location.origin + seoData.bannerUrl 
      : seoData.bannerUrl;
  }

  let bannerTag = "";
  if (finalImageUrl) {
    bannerTag = `<figure style="text-align: center; margin: 0 0 28px 0;">
  <img src="${finalImageUrl}" alt="${seoData.imageAlt}" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #FECF06; box-shadow: 0 4px 14px rgba(0,0,0,0.12);" />
  <figcaption style="font-size: 13px; color: #666; margin-top: 6px; font-style: italic;">Cabecera optimizada para SEO (16:9)</figcaption>
</figure>\n\n`;
  }

  return bannerTag + tempDiv.innerHTML;
}

/**
 * Genera código HTML autónomo con estilos CSS embebidos para el elemento de Código HTML de Sitejet Builder (<> Code)
 * Incluye el Schema JSON-LD y todos los estilos.
 * @param {object} state Estado global
 * @param {object} options Opciones
 * @returns {string} Código HTML completo para elemento <> de Sitejet
 */
export function generateSitejetHtmlBlock(state, options = {}) {
  const seoData = extractSeoKitData(state);
  const richHtml = generateSitejetRichTextHtml(state, options);
  
  let schemaScript = "";
  if (seoData.schemaJsonLd) {
    schemaScript = `\n<!-- Schema.org JSON-LD para Sitejet Builder -->\n<script type="application/ld+json">\n${seoData.schemaJsonLd}\n</script>\n`;
  }

  return `<!-- SITEJET BUILDER HTML BLOCK — GRANITE CYBER-LEGAL -->
<div class="sitejet-article-wrapper" style="max-width: 900px; margin: 0 auto; color: #222222; font-family: Arial, sans-serif;">
${richHtml}
${schemaScript}
</div>`;
}

/**
 * Muestra el modal interactivo del Kit SEO & Schema para Sitejet Builder
 * @param {object} state Estado global
 */
export async function showSitejetSeoKitModal(state) {
  let modal = document.getElementById("sitejetSeoKitModal");
  if (!modal) {
    modal = createSitejetModalElement();
    document.body.appendChild(modal);
    setupModalEvents(modal, state);
  }

  const seoData = extractSeoKitData(state);

  // Poblar campos del modal
  const inputTitle = modal.querySelector("#sitejetKitTitle");
  const inputSlug = modal.querySelector("#sitejetKitSlug");
  const inputMeta = modal.querySelector("#sitejetKitMeta");
  const inputAlt = modal.querySelector("#sitejetKitAlt");
  const inputKeywords = modal.querySelector("#sitejetKitKeywords");
  const inputSchema = modal.querySelector("#sitejetKitSchema");
  const charTitle = modal.querySelector("#sitejetKitTitleCount");
  const charMeta = modal.querySelector("#sitejetKitMetaCount");
  const previewImg = modal.querySelector("#sitejetKitImgPreview");
  const btnDownloadPng = modal.querySelector("#btnSitejetDownloadPng");

  if (inputTitle) inputTitle.value = seoData.title;
  if (inputSlug) inputSlug.value = seoData.slug;
  if (inputMeta) inputMeta.value = seoData.metaDescription;
  if (inputAlt) inputAlt.value = seoData.imageAlt;
  if (inputKeywords) inputKeywords.value = seoData.keywords;
  if (inputSchema) inputSchema.value = seoData.schemaJsonLd;

  if (charTitle) {
    const len = (seoData.title || "").length;
    charTitle.innerText = `${len}/60 chars`;
    charTitle.style.color = len >= 50 && len <= 65 ? "var(--color-secondary)" : "var(--color-primary)";
  }

  if (charMeta) {
    const len = (seoData.metaDescription || "").length;
    charMeta.innerText = `${len}/160 chars`;
    charMeta.style.color = len >= 140 && len <= 160 ? "var(--color-secondary)" : "var(--color-primary)";
  }

  // Previsualizar la imagen y preparar PNG
  const currentBanner = seoData.bannerUrl;
  if (currentBanner) {
    if (previewImg) {
      previewImg.src = currentBanner;
      previewImg.style.display = "block";
    }
    if (btnDownloadPng) btnDownloadPng.style.display = "inline-flex";
  } else {
    if (previewImg) previewImg.style.display = "none";
    if (btnDownloadPng) btnDownloadPng.style.display = "none";
  }

  modal.classList.add("modal-show");
}

/**
 * Crea el elemento DOM del Modal Kit SEO Sitejet
 */
function createSitejetModalElement() {
  const modal = document.createElement("div");
  modal.id = "sitejetSeoKitModal";
  modal.className = "shortcuts-modal-overlay";
  modal.innerHTML = `
    <div class="shortcuts-modal-card" style="max-width: 680px; width: 94%; max-height: 90vh; overflow-y: auto;">
      <div class="d-flex justify-content-between align-items-center mb-3 pb-2" style="border-bottom: 1px solid var(--divider);">
        <div class="d-flex align-items-center gap-2">
          <span class="material-symbols-outlined" style="color: var(--color-primary); font-size: 1.6rem;">rocket_launch</span>
          <h3 style="margin: 0; font-size: 1.15rem; color: var(--color-primary); font-weight: 700;">Kit SEO & Schema para Sitejet Builder</h3>
        </div>
        <button class="btn btn-sm btn-outline py-0 px-2" id="btnCloseSitejetModal" title="Cerrar modal" style="font-size: 1.3rem; line-height: 1;">&times;</button>
      </div>

      <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 16px;">
        Copia individualmente cada elemento en la <strong>Colección de Blog</strong> de Sitejet (Namecheap) para garantizar 100% de indexación, CTR y datos enriquecidos.
      </p>

      <!-- Campo 1: Título de Colección Sitejet -->
      <div class="form-group mb-3">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <label class="form-label mb-0" for="sitejetKitTitle"><strong>1. Título del Artículo (H1 en Sitejet)</strong></label>
          <span id="sitejetKitTitleCount" class="font-monospace" style="font-size: 0.75rem; font-weight: 700;">0/60</span>
        </div>
        <div class="d-flex gap-2">
          <input type="text" id="sitejetKitTitle" class="input-text" readonly style="background: var(--bg-default);" />
          <button type="button" class="btn btn-secondary btn-sm copy-field-btn" data-target="sitejetKitTitle" title="Copiar Título">
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </div>

      <!-- Campo 2: Slug URL -->
      <div class="form-group mb-3">
        <label class="form-label mb-1" for="sitejetKitSlug"><strong>2. Slug URL (URL Amigable)</strong></label>
        <div class="d-flex gap-2">
          <input type="text" id="sitejetKitSlug" class="input-text font-monospace" readonly style="background: var(--bg-default);" />
          <button type="button" class="btn btn-secondary btn-sm copy-field-btn" data-target="sitejetKitSlug" title="Copiar Slug">
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </div>

      <!-- Campo 3: Meta Descripción -->
      <div class="form-group mb-3">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <label class="form-label mb-0" for="sitejetKitMeta"><strong>3. Meta Descripción (Snippet SERP)</strong></label>
          <span id="sitejetKitMetaCount" class="font-monospace" style="font-size: 0.75rem; font-weight: 700;">0/160</span>
        </div>
        <div class="d-flex gap-2">
          <textarea id="sitejetKitMeta" class="textarea-custom" rows="2" readonly style="background: var(--bg-default); resize: none;"></textarea>
          <button type="button" class="btn btn-secondary btn-sm copy-field-btn" data-target="sitejetKitMeta" title="Copiar Meta Descripción">
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </div>

      <!-- Campo 4: Texto Alt de Imagen -->
      <div class="form-group mb-3">
        <label class="form-label mb-1" for="sitejetKitAlt"><strong>4. Texto Alternativo (Alt Text) de la Imagen</strong></label>
        <div class="d-flex gap-2">
          <input type="text" id="sitejetKitAlt" class="input-text" readonly style="background: var(--bg-default);" />
          <button type="button" class="btn btn-secondary btn-sm copy-field-btn" data-target="sitejetKitAlt" title="Copiar Alt">
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </div>

      <!-- Campo 5: Palabras Clave -->
      <div class="form-group mb-3">
        <label class="form-label mb-1" for="sitejetKitKeywords"><strong>5. Palabras Clave (Keywords LSI)</strong></label>
        <div class="d-flex gap-2">
          <input type="text" id="sitejetKitKeywords" class="input-text" readonly style="background: var(--bg-default);" />
          <button type="button" class="btn btn-secondary btn-sm copy-field-btn" data-target="sitejetKitKeywords" title="Copiar Keywords">
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </div>

      <!-- Sección Imagen Cabecera & Media Manager de Sitejet -->
      <div class="form-group mb-3 p-3" style="background: var(--color-primary-soft); border: 1px solid var(--border-gold); border-radius: 6px;">
        <label class="form-label mb-1" style="color: var(--color-primary); font-weight: 700;">
          🖼️ Cabecera 16:9 y Sitejet Media Manager
        </label>
        <p style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px;">
          Descarga la imagen en PNG (1200x675) para subirla a la biblioteca de Sitejet, o pega su URL pública si ya la subiste.
        </p>
        <div class="d-flex align-items-center gap-3 flex-wrap mb-2">
          <img id="sitejetKitImgPreview" src="" alt="Cabecera" style="max-height: 80px; max-width: 140px; border-radius: 4px; border: 1px solid var(--border-gold); object-fit: cover; display: none;" />
          <button type="button" id="btnSitejetDownloadPng" class="btn btn-primary btn-sm">
            <span class="material-symbols-outlined">download</span> Descargar PNG (1200x675)
          </button>
        </div>
        <div>
          <label class="form-label mb-1" for="sitejetUserCdnUrl" style="font-size: 0.78rem;">
            URL en Media Manager de Sitejet (Opcional - Reemplaza Data-URI al copiar):
          </label>
          <input type="url" id="sitejetUserCdnUrl" class="input-text" placeholder="https://assets.sitejet.io/..." style="font-size: 0.82rem;" />
        </div>
      </div>

      <!-- Campo 6: Schema.org JSON-LD -->
      <div class="form-group mb-3">
        <label class="form-label mb-1" for="sitejetKitSchema">
          <strong>6. Schema.org JSON-LD (Pegar en Configuración de Página o Elemento &lt;&gt; de Sitejet)</strong>
        </label>
        <div class="d-flex gap-2">
          <textarea id="sitejetKitSchema" class="textarea-custom font-monospace" rows="5" readonly style="background: var(--bg-default); font-size: 0.8rem;"></textarea>
          <button type="button" class="btn btn-secondary btn-sm copy-field-btn" data-target="sitejetKitSchema" title="Copiar Schema JSON-LD">
            <span class="material-symbols-outlined">content_copy</span>
          </button>
        </div>
      </div>

      <!-- Acciones Finales -->
      <div class="d-flex justify-content-between align-items-center gap-2 pt-2 mt-2" style="border-top: 1px solid var(--divider);">
        <button type="button" id="btnSitejetCopyHtmlBlock" class="btn btn-outline btn-sm" title="Copiar como bloque de código HTML completo con estilos y Schema">
          <span class="material-symbols-outlined">code</span> Copiar Bloque HTML &lt;/&gt;
        </button>
        <button type="button" id="btnSitejetModalCopyRich" class="btn btn-primary btn-sm">
          <span class="material-symbols-outlined">content_paste_go</span> Copiar p/ Rich Text Sitejet
        </button>
      </div>
    </div>
  `;
  return modal;
}

/**
 * Configura los eventos del modal Kit SEO Sitejet
 */
function setupModalEvents(modal, state) {
  // Botón cerrar
  const btnClose = modal.querySelector("#btnCloseSitejetModal");
  if (btnClose) {
    btnClose.addEventListener("click", () => modal.classList.remove("modal-show"));
  }
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.remove("modal-show");
  });

  // Botones de copia individual por campo usando el portapapeles robusto
  modal.querySelectorAll(".copy-field-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const targetId = btn.dataset.target;
      const targetEl = modal.querySelector(`#${targetId}`);
      if (targetEl && targetEl.value) {
        const ok = await copyToClipboardRobust(targetEl.value, targetEl.value);
        if (ok) {
          toast.success("Copiado al portapapeles.");
          btn.classList.add("btn-outline");
          btn.classList.remove("btn-secondary");
          setTimeout(() => {
            btn.classList.add("btn-secondary");
            btn.classList.remove("btn-outline");
          }, 1200);
        } else {
          toast.error("No se pudo copiar el campo.");
        }
      }
    });
  });

  // Botón Descargar PNG
  const btnDownloadPng = modal.querySelector("#btnSitejetDownloadPng");
  if (btnDownloadPng) {
    btnDownloadPng.addEventListener("click", async () => {
      const seoData = extractSeoKitData(state);
      if (!seoData.bannerUrl) {
        toast.warning("No hay imagen de cabecera disponible.");
        return;
      }
      try {
        toast.info("Generando archivo PNG 16:9...");
        const pngData = await convertSvgToPngDataUrl(seoData.bannerUrl);
        const a = document.createElement("a");
        a.href = pngData;
        a.download = `sitejet-banner-${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        toast.success("¡Imagen PNG (1200x675) descargada con éxito!");
      } catch (err) {
        console.error("Error al descargar PNG:", err);
        toast.error("Error al generar PNG: " + err.message);
      }
    });
  }

  // Copiar Bloque HTML </>
  const btnHtmlBlock = modal.querySelector("#btnSitejetCopyHtmlBlock");
  if (btnHtmlBlock) {
    btnHtmlBlock.addEventListener("click", async () => {
      const sitejetUserCdnUrl = modal.querySelector("#sitejetUserCdnUrl");
      const cdnUrl = sitejetUserCdnUrl ? sitejetUserCdnUrl.value.trim() : "";
      
      const seoData = extractSeoKitData(state);
      let pngData = "";
      if (!cdnUrl && seoData.bannerUrl) {
        pngData = await convertSvgToPngDataUrl(seoData.bannerUrl);
      }

      const htmlBlock = generateSitejetHtmlBlock(state, {
        sitejetMediaUrl: cdnUrl,
        pngDataUrl: pngData
      });

      const ok = await copyToClipboardRobust(htmlBlock);
      if (ok) {
        toast.success("¡Bloque HTML </> copiado! Pégalo en el elemento HTML de Sitejet.");
      } else {
        toast.error("No se pudo copiar el bloque HTML.");
      }
    });
  }

  // Copiar p/ Rich Text desde el modal
  const btnModalCopyRich = modal.querySelector("#btnSitejetModalCopyRich");
  if (btnModalCopyRich) {
    btnModalCopyRich.addEventListener("click", async () => {
      const btnMain = document.getElementById("btnCopySitejet");
      if (btnMain) {
        btnMain.click();
      }
    });
  }
}

/**
 * Inicializa los controladores del exportador Sitejet en la vista principal
 * @param {object} state Estado global
 */
export function initSitejetExporter(state) {
  const btnCopySitejet = document.getElementById("btnCopySitejet");
  const btnSitejetKit = document.getElementById("btnSitejetKit");
  const articleView = document.getElementById("articleView");

  // Botón Principal: Copiar para Sitejet Builder
  if (btnCopySitejet) {
    btnCopySitejet.addEventListener("click", async () => {
      const hasContent = articleView && articleView.innerHTML && articleView.innerText.trim().length > 30 && !articleView.innerText.includes("Carga un archivo Docling");

      if (!hasContent && (!state || !state.currentRawMarkdown)) {
        toast.warning("No hay ningún artículo redactado para copiar. Genera o carga un artículo primero.");
        return;
      }

      const origText = btnCopySitejet.innerHTML;

      try {
        const sitejetUserCdnUrl = document.getElementById("sitejetUserCdnUrl");
        const cdnUrl = sitejetUserCdnUrl ? sitejetUserCdnUrl.value.trim() : "";

        const seoData = extractSeoKitData(state);
        let pngData = "";
        if (!cdnUrl && seoData.bannerUrl && pngDataUriCache.has(seoData.bannerUrl)) {
          pngData = pngDataUriCache.get(seoData.bannerUrl);
        }

        const sitejetHtml = generateSitejetRichTextHtml(state, {
          sitejetMediaUrl: cdnUrl,
          pngDataUrl: pngData
        });

        const ok = await copyToClipboardRobust(sitejetHtml);
        if (ok) {
          btnCopySitejet.innerHTML = '<span class="material-symbols-outlined">done_all</span> ¡Copiado Sitejet!';
          btnCopySitejet.classList.add("btn-secondary");
          btnCopySitejet.classList.remove("btn-primary");
          toast.success("¡Artículo completo copiado para Sitejet Builder! (Listo para pegar en Rich Text)");

          setTimeout(() => {
            btnCopySitejet.innerHTML = origText;
            btnCopySitejet.classList.add("btn-primary");
            btnCopySitejet.classList.remove("btn-secondary");
          }, 2500);
        } else {
          toast.error("No se pudo copiar automáticamente. Por favor intenta de nuevo.");
          btnCopySitejet.innerHTML = origText;
        }

      } catch (err) {
        console.error("Error al copiar para Sitejet:", err);
        try {
          const fallbackHtml = generateSitejetRichTextHtml(state);
          await copyToClipboardRobust(fallbackHtml);
          toast.info("HTML copiado al portapapeles.");
        } catch (fallbackErr) {
          toast.error("Error al copiar al portapapeles: " + err.message);
        }
        btnCopySitejet.innerHTML = origText;
      }
    });
  }

  // Botón Secundario: Abrir Kit SEO Sitejet
  if (btnSitejetKit) {
    btnSitejetKit.addEventListener("click", () => {
      showSitejetSeoKitModal(state);
    });
  }
}
