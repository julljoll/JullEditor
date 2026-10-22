/**
 * Módulo de Exportación a WordPress Gutenberg, Markdown, HTML e Impresión
 */

import { toast } from "./toast-notifications.js";
import { unwrapMagazine } from "./markdown-renderer.js";

export function generateWordPressHtml(state) {
  const articleView = document.getElementById("articleView");
  const previewTitle = document.getElementById("previewTitle");
  if (!articleView || !articleView.innerHTML) return "";

  const titleText = (previewTitle && previewTitle.innerText) || "Artículo de Blog Optimizado";
  const bannerUrlResolved = state.currentBannerUrl 
    ? (state.currentBannerUrl.startsWith("/") ? window.location.origin + state.currentBannerUrl : state.currentBannerUrl)
    : "";

  const bannerTag = bannerUrlResolved 
    ? `<figure style="text-align: center; margin: 0 0 28px 0;"><img src="${bannerUrlResolved}" alt="${titleText}" style="max-width: 100%; height: auto; border-radius: 8px; border: 1px solid #FECF06; box-shadow: 0 4px 14px rgba(0,0,0,0.15);" /><figcaption style="font-size: 13px; color: #666; margin-top: 6px; font-style: italic;">Cabecera del artículo optimizado para SEO</figcaption></figure>\n\n` 
    : "";

  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = articleView.innerHTML;
  unwrapMagazine(tempDiv);

  const isSentencia = state.sentenciaMetadata || 
    (state.currentRawMarkdown && /ficha técnica de la sentencia|tribunal supremo de justicia|analista_tsj_revista|dispositivo del fallo/i.test(state.currentRawMarkdown));

  let tsjBadgeHeader = "";
  if (isSentencia) {
    tsjBadgeHeader = `<div style="display: inline-block; background: #fffbe6; color: #b89000; border: 1px solid #FECF06; border-radius: 4px; padding: 5px 12px; font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 16px; font-family: monospace;">🏛️ ANÁLISIS JURISPRUDENCIAL — TSJ VENEZUELA</div>\n`;
  }

  tempDiv.querySelectorAll(".streaming-cursor").forEach(el => el.remove());

  tempDiv.querySelectorAll("h1").forEach(el => {
    el.setAttribute("style", "color: #008726; font-size: 28px; font-weight: 700; border-bottom: 2px solid #008726; padding-bottom: 8px; text-transform: uppercase; margin-top: 10px; margin-bottom: 16px; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll("h2").forEach(el => {
    el.setAttribute("style", "color: #b89000; font-size: 22px; font-weight: 600; margin-top: 28px; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 4px; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll("h3, h4").forEach(el => {
    el.setAttribute("style", "color: #b89000; font-size: 18px; font-weight: 600; border-left: 3px solid #FECF06; background: #fffbe6; padding: 8px 12px; margin-top: 20px; margin-bottom: 10px; border-radius: 0 4px 4px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll("p").forEach(el => {
    el.setAttribute("style", "font-size: 16px; line-height: 1.65; color: #222222; text-align: justify; margin-bottom: 16px; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll("strong").forEach(el => {
    el.setAttribute("style", "color: #000000; font-weight: 700; background: #fff9db; padding: 1px 4px; border-radius: 2px;");
  });
  tempDiv.querySelectorAll("em").forEach(el => {
    el.setAttribute("style", "color: #444444; font-style: italic;");
  });
  tempDiv.querySelectorAll("a").forEach(el => {
    el.setAttribute("style", "color: #008726; font-weight: bold; text-decoration: underline;");
  });
  tempDiv.querySelectorAll("blockquote").forEach(el => {
    el.setAttribute("style", "background: #f8f9fa; border-left: 4px solid #008726; padding: 12px 18px; margin: 18px 0; color: #333333; font-style: italic; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".meta-description-callout").forEach(el => {
    el.setAttribute("style", "background: #f4f6f8; border: 1px solid #e2e8f0; border-left: 4px solid #FECF06; padding: 14px 18px; margin: 18px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".meta-description-label").forEach(el => {
    el.setAttribute("style", "font-size: 12px; font-weight: 700; color: #b89000; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; font-family: monospace;");
  });
  tempDiv.querySelectorAll(".meta-description-text").forEach(el => {
    el.setAttribute("style", "font-style: italic; color: #333333; font-size: 15px; line-height: 1.45;");
  });
  tempDiv.querySelectorAll(".source-summary-callout").forEach(el => {
    el.setAttribute("style", "background: #eef9e8; border: 1px solid #c6f6d5; border-left: 4px solid #008726; padding: 14px 18px; margin: 18px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".source-summary-label").forEach(el => {
    el.setAttribute("style", "font-size: 12px; font-weight: 700; color: #008726; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; font-family: monospace;");
  });
  tempDiv.querySelectorAll(".source-summary-text").forEach(el => {
    el.setAttribute("style", "color: #222222; font-size: 15px; line-height: 1.5;");
  });

  // Tarjeta de Resumen Estructurado / Abstract Científico Universitario
  tempDiv.querySelectorAll(".academic-abstract-card").forEach(el => {
    el.setAttribute("style", "background: #f0f9ff; border: 1px solid #bae6fd; border-left: 4px solid #0284c7; padding: 16px 20px; margin: 20px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".academic-abstract-label").forEach(el => {
    el.setAttribute("style", "font-size: 12px; font-weight: 700; color: #0284c7; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px; font-family: monospace; border-bottom: 1px dashed #bae6fd; padding-bottom: 4px;");
  });
  tempDiv.querySelectorAll(".academic-abstract-text").forEach(el => {
    el.setAttribute("style", "color: #1e293b; font-size: 15px; line-height: 1.6; text-align: justify;");
  });

  tempDiv.querySelectorAll(".paragraph-takeaway").forEach(el => {
    el.setAttribute("style", "background: #e8f8ed; border-left: 3px solid #008726; padding: 10px 14px; margin: 14px 0; border-radius: 0 6px 6px 0; color: #005a19; font-size: 15px; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".copyright-card").forEach(el => {
    el.setAttribute("style", "background: #fdfdfd; border: 1px solid #e2e8f0; border-left: 4px solid #008726; padding: 16px 20px; margin: 24px 0; border-radius: 0 6px 6px 0; color: #333333; font-size: 14px; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".copyright-card-title").forEach(el => {
    el.setAttribute("style", "font-weight: 700; color: #008726; margin-bottom: 6px; text-transform: uppercase; font-family: monospace; font-size: 13px;");
  });

  tempDiv.querySelectorAll(".faq-section-card").forEach(el => {
    el.setAttribute("style", "background: #fffbe6; border: 1px solid #ffe066; border-left: 4px solid #b89000; padding: 18px 22px; margin: 24px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".faq-section-title").forEach(el => {
    el.setAttribute("style", "font-weight: 700; color: #b89000; margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px dashed #ffe066; text-transform: uppercase; font-family: monospace; font-size: 13px;");
  });
  tempDiv.querySelectorAll(".faq-question").forEach(el => {
    el.setAttribute("style", "background: #fff9db; border-left: 3px solid #b89000; padding: 10px 14px; margin: 8px 0 4px 0; border-radius: 0 4px 4px 0; font-size: 16px; color: #222222;");
  });
  tempDiv.querySelectorAll(".faq-answer").forEach(el => {
    el.setAttribute("style", "padding: 8px 14px 8px 20px; margin: 0 0 8px 0; font-size: 15px; color: #333333; line-height: 1.55;");
  });
  tempDiv.querySelectorAll(".author-bio-card").forEach(el => {
    el.setAttribute("style", "background: #eef9e8; border: 1px solid #c6f6d5; border-left: 4px solid #008726; padding: 16px 20px; margin: 24px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".author-bio-title").forEach(el => {
    el.setAttribute("style", "font-weight: 700; color: #008726; margin-bottom: 8px; text-transform: uppercase; font-family: monospace; font-size: 13px;");
  });
  tempDiv.querySelectorAll(".toc-card, nav.toc-card").forEach(el => {
    el.setAttribute("style", "background: #f8f9fa; border: 1px solid #e2e8f0; border-left: 4px solid #b89000; padding: 16px 20px; margin: 16px 0 22px 0; border-radius: 0 6px 6px 0; font-family: Arial, sans-serif;");
  });
  tempDiv.querySelectorAll(".toc-title").forEach(el => {
    el.setAttribute("style", "font-weight: 700; color: #b89000; margin-bottom: 10px; text-transform: uppercase; font-family: monospace; font-size: 13px;");
  });

  // Tablas (Ficha Técnica TSJ / Tablas comparativas)
  tempDiv.querySelectorAll("table").forEach(el => {
    if (isSentencia) {
      el.setAttribute("style", "width: 100%; border-collapse: collapse; margin: 20px 0 24px 0; font-family: Arial, sans-serif; font-size: 14.5px; border: 1px solid #D4A843; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-radius: 4px; overflow: hidden;");
    } else {
      el.setAttribute("style", "width: 100%; border-collapse: collapse; margin: 20px 0 24px 0; font-family: Arial, sans-serif; font-size: 14.5px;");
    }
  });
  tempDiv.querySelectorAll("th").forEach(el => {
    if (isSentencia) {
      el.setAttribute("style", "background: #1a1a2e; color: #F2C230; padding: 11px 14px; text-align: left; font-weight: 700; border: 1px solid #D4A843; font-family: Arial, sans-serif;");
    } else {
      el.setAttribute("style", "background: #008726; color: #ffffff; padding: 10px 14px; text-align: left; font-weight: 700; border: 1px solid #00681d; font-family: Arial, sans-serif;");
    }
  });
  tempDiv.querySelectorAll("td").forEach(el => {
    if (isSentencia) {
      el.setAttribute("style", "padding: 10px 14px; border: 1px solid #e2e8f0; color: #1a1a2e; font-family: Arial, sans-serif; line-height: 1.5; background: #fafafa;");
    } else {
      el.setAttribute("style", "padding: 10px 14px; border: 1px solid #e2e8f0; color: #222222; font-family: Arial, sans-serif; line-height: 1.5;");
    }
  });

  // Listas y código
  tempDiv.querySelectorAll("ul, ol").forEach(el => {
    el.setAttribute("style", "margin: 14px 0 18px 24px; padding-left: 10px; color: #222222; font-family: Arial, sans-serif; line-height: 1.65;");
  });
  tempDiv.querySelectorAll("li").forEach(el => {
    el.setAttribute("style", "margin-bottom: 8px; font-size: 15.5px; color: #222222;");
  });
  tempDiv.querySelectorAll("code").forEach(el => {
    if (!el.closest("pre")) {
      el.setAttribute("style", "background: #f1f5f9; color: #0f172a; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13.5px; border: 1px solid #e2e8f0;");
    }
  });

  tempDiv.querySelectorAll(".seo-badge-container").forEach(el => {
    el.setAttribute("style", "display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; padding: 12px; background: #f8f9fa; border: 1px solid #e2e8f0; border-radius: 6px;");
  });
  tempDiv.querySelectorAll(".seo-badge").forEach(el => {
    el.setAttribute("style", "font-size: 12px; background: #fffbe6; border: 1px solid #ffe066; padding: 4px 10px; border-radius: 4px; color: #333333; font-family: monospace;");
  });
  tempDiv.querySelectorAll("pre").forEach(el => {
    el.setAttribute("style", "background: #111111; color: #00FF41; padding: 14px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 13px; margin: 16px 0;");
  });

  let schemaEmbedHtml = "";
  if (state.currentRawMarkdown) {
    const schemaMatches = state.currentRawMarkdown.match(/```json\s*(\{[\s\S]*?"@context"\s*:\s*"https:\/\/schema\.org"[\s\S]*?\})\s*```/gim);
    if (schemaMatches) {
      schemaMatches.forEach(block => {
        const jsonStr = block.replace(/```json\s*/i, "").replace(/```\s*$/i, "").trim();
        schemaEmbedHtml += `\n<!-- Schema.org JSON-LD (Gutenberg HTML Personalizado) -->\n<script type="application/ld+json">\n${jsonStr}\n</script>\n`;
      });
    }
  }

  const wrappedHtml = `<div class="granite-article-wrapper" style="max-width: 100%; font-family: Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #222222; line-height: 1.65;">\n${bannerTag}${tsjBadgeHeader}${tempDiv.innerHTML}\n</div>${schemaEmbedHtml}`;
  return wrappedHtml;
}

export function initWordPressExporter(state) {
  const btnCopyWordPress = document.getElementById("btnCopyWordPress");
  const btnCopyRawHtml = document.getElementById("btnCopyRawHtml");
  const btnDownloadSelectedImage = document.getElementById("btnDownloadSelectedImage");
  const btnCopy = document.getElementById("btnCopy");
  const btnDownloadHtml = document.getElementById("btnDownloadHtml");
  const btnPrint = document.getElementById("btnPrint");
  const btnClear = document.getElementById("btnClear");
  const articleView = document.getElementById("articleView");
  const previewTitle = document.getElementById("previewTitle");
  const previewSnippet = document.getElementById("previewSnippet");

  if (btnCopyRawHtml) {
    btnCopyRawHtml.addEventListener("click", async () => {
      if (!articleView || !articleView.innerHTML || !state.currentRawMarkdown) {
        toast.warning("No hay ningún artículo generado para copiar.");
        return;
      }
      const rawHtml = generateWordPressHtml(state);
      try {
        await navigator.clipboard.writeText(rawHtml);
        toast.success("¡Código HTML completo copiado al portapapeles! Listo para pegar en bloques de código o CMS.");
      } catch (e) {
        toast.error("Error al copiar código HTML.");
      }
    });
  }

  if (btnCopyWordPress) {
    btnCopyWordPress.addEventListener("click", async () => {
      if (!articleView || !articleView.innerHTML || !state.currentRawMarkdown) {
        toast.warning("No hay ningún artículo generado para copiar.");
        return;
      }

      const wpFormattedHtml = generateWordPressHtml(state);
      
      try {
        if (navigator.clipboard && window.ClipboardItem) {
          const htmlBlob = new Blob([wpFormattedHtml], { type: "text/html" });
          const textBlob = new Blob([wpFormattedHtml], { type: "text/plain" });
          const item = new ClipboardItem({
            "text/html": htmlBlob,
            "text/plain": textBlob,
          });
          await navigator.clipboard.write([item]);
        } else {
          await navigator.clipboard.writeText(wpFormattedHtml);
        }

        const orig = btnCopyWordPress.innerHTML;
        btnCopyWordPress.innerHTML = '<span class="material-symbols-outlined">done_all</span> ¡Copiado!';
        btnCopyWordPress.classList.add("btn-secondary");
        btnCopyWordPress.classList.remove("btn-primary");
        toast.success("¡Artículo copiado con estilos listos para WordPress Gutenberg!");
        setTimeout(() => {
          btnCopyWordPress.innerHTML = orig;
          btnCopyWordPress.classList.add("btn-primary");
          btnCopyWordPress.classList.remove("btn-secondary");
        }, 2500);

      } catch (err) {
        await navigator.clipboard.writeText(wpFormattedHtml);
        toast.info("HTML copiado al portapapeles.");
      }
    });
  }

  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      if (!state.currentRawMarkdown) {
        toast.warning("No hay contenido Markdown para copiar.");
        return;
      }
      navigator.clipboard.writeText(state.currentRawMarkdown).then(() => {
        toast.success("Markdown copiado al portapapeles.");
      });
    });
  }

  if (btnDownloadSelectedImage) {
    btnDownloadSelectedImage.addEventListener("click", () => {
      if (!state.currentBannerUrl) {
        toast.warning("No hay imagen seleccionada.");
        return;
      }

      if (state.currentBannerUrl.startsWith("/")) {
        const a = document.createElement("a");
        a.href = state.currentBannerUrl;
        a.download = `cabecera-${Date.now()}.svg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        toast.success("Imagen descargada.");
      } else {
        const proxyUrl = `/api/download-proxy-image?image_url=${encodeURIComponent(state.currentBannerUrl)}`;
        const a = document.createElement("a");
        a.href = proxyUrl;
        a.download = `cabecera-fuente-${Date.now()}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        toast.success("Imagen descargada vía proxy.");
      }
    });
  }

  if (btnDownloadHtml) {
    btnDownloadHtml.addEventListener("click", () => {
      if (!articleView || !articleView.innerHTML) {
        toast.warning("No hay artículo para descargar.");
        return;
      }
      const bannerTag = state.currentBannerUrl ? `<div style="text-align:center; margin-bottom:24px;"><img src="${state.currentBannerUrl}" alt="Cabecera" style="max-width:100%; border-radius:8px;" /></div>` : '';
      const cleanHtml = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${(previewTitle && previewTitle.innerText) || "Artículo de Blog Optimizado"}</title>
  <meta name="description" content="${(previewSnippet && previewSnippet.innerText) || ""}">
  <style>
    body { font-family: 'Arial', sans-serif; line-height: 1.6; max-width: 1200px; margin: 40px auto; padding: 0 24px; color: #1A1A1A; background: #FFFFFF; }
    h1 { color: #1A6B1A; font-size: 1.85rem; font-weight: 700; border-bottom: 2px solid #1A6B1A; padding-bottom: 10px; text-transform: uppercase; margin-top: 10px; }
    h2 { color: #8A6800; font-size: 1.35rem; font-weight: 600; margin-top: 24px; border-bottom: 1px solid #EEE; padding-bottom: 6px; }
    h3, h4 { color: #8A6800; font-size: 1.15rem; font-weight: 600; border-left: 3px solid #FECF06; background: #FFFBE6; padding: 8px 14px; border-radius: 0 6px 6px 0; margin-top: 20px; }
    p { color: #222; font-size: 1.02rem; margin-bottom: 14px; text-align: justify; }
    strong { color: #000; font-weight: 700; background: #FFF9DB; padding: 1px 4px; border-radius: 3px; }
    em { color: #444; font-style: italic; }
    a { color: #1A6B1A; font-weight: bold; text-decoration: underline; }
    blockquote { border-left: 4px solid #1A6B1A; margin: 16px 0; padding: 12px 18px; background: #F8F9FA; border-radius: 0 8px 8px 0; }
    
    /* Maquetación Revista Digital (3 Columnas) */
    .mag-head { margin-bottom: 24px; }
    .mag-body { column-count: 3; column-gap: 32px; column-rule: 1px solid #E0E0E0; text-align: justify; }
    .mag-body p { font-family: Georgia, serif; font-size: 0.98rem; line-height: 1.65; break-inside: avoid; }
    .mag-body > p:first-of-type::first-letter { float: left; font-size: 3.2em; line-height: 0.85; padding-right: 8px; color: #8A6800; font-weight: bold; }
    .mag-body h2 { break-after: avoid; font-size: 1.18rem; }
    .mag-body blockquote { column-span: all; font-size: 1.25rem; font-style: italic; text-align: center; border: none; border-top: 2px solid #8A6800; border-bottom: 2px solid #8A6800; background: #FFFDF0; padding: 14px 20px; border-radius: 4px; }
    .mag-foot { margin-top: 30px; padding-top: 20px; border-top: 1px dashed #DDD; }
    @media (max-width: 960px) { .mag-body { column-count: 1; } }
  </style>
</head>
<body>
${bannerTag}
${articleView.innerHTML.replace(/<span class="streaming-cursor"><\/span>/g, "")}
</body>
</html>`;
      const blob = new Blob([cleanHtml], { type: "text/html;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `articulo-seo-blog-${Date.now()}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Archivo HTML descargado.");
    });
  }

  if (btnPrint) {
    btnPrint.addEventListener("click", () => {
      window.print();
    });
  }
}
