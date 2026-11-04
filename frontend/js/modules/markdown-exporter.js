/**
 * Módulo de Exportación SOLO Markdown (.MD)
 * - Copiar Markdown puro al portapapeles
 * - Copiar/Descargar Markdown editorial para Astro Framework (.md)
 * - Descargar Markdown puro (.md)
 * (WordPress Gutenberg, HTML y Sitejet fueron eliminados del editor)
 */

import { toast } from "./toast-notifications.js";

function getArticleTitle() {
  const previewTitle = document.getElementById("previewTitle");
  const sourceTitle = document.getElementById("sourceTitle");
  return (sourceTitle && sourceTitle.value) || (previewTitle && previewTitle.innerText) || "articulo-blog";
}

function slugify(title) {
  return String(title)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "articulo-blog";
}

export function initMarkdownExporter(state) {
  const btnCopyMarkdown = document.getElementById("btnCopyMarkdown");
  const btnDownloadSelectedImage = document.getElementById("btnDownloadSelectedImage");
  const btnCopy = document.getElementById("btnCopy");
  const btnDownloadMarkdown = document.getElementById("btnDownloadMarkdown");
  const btnPrint = document.getElementById("btnPrint");

  // Copiar Markdown puro al portapapeles (botón principal split "Copiar .MD")
  if (btnCopyMarkdown) {
    btnCopyMarkdown.addEventListener("click", async () => {
      if (!state.currentRawMarkdown) {
        toast.warning("No hay contenido Markdown para copiar.");
        return;
      }
      try {
        await navigator.clipboard.writeText(state.currentRawMarkdown);
        const orig = btnCopyMarkdown.innerHTML;
        btnCopyMarkdown.innerHTML = '<span class="material-symbols-outlined">done_all</span> ¡Copiado!';
        btnCopyMarkdown.classList.add("btn-secondary");
        btnCopyMarkdown.classList.remove("btn-primary");
        toast.success("Markdown copiado al portapapeles.");
        setTimeout(() => {
          btnCopyMarkdown.innerHTML = orig;
          btnCopyMarkdown.classList.add("btn-primary");
          btnCopyMarkdown.classList.remove("btn-secondary");
        }, 2500);
      } catch (e) {
        toast.error("Error al copiar Markdown.");
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

  const btnCopyAstro = document.getElementById("btnCopyAstro");
  const btnDownloadAstro = document.getElementById("btnDownloadAstro");

  if (btnCopyAstro) {
    btnCopyAstro.addEventListener("click", async () => {
      if (!state.currentRawMarkdown) {
        toast.warning("No hay contenido para exportar a Astro.");
        return;
      }
      try {
        const title = getArticleTitle();
        const resp = await fetch(`/api/export/astro/${encodeURIComponent(title)}`);
        let textToCopy = "";
        if (resp.ok) {
          const data = await resp.json();
          textToCopy = data.content;
        } else {
          // Conversión dinámica bajo demanda si aún no está en disco
          const convResp = await fetch("/api/export/astro/convert", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: title,
              markdown_content: state.currentRawMarkdown,
              editorial_layout: true
            })
          });
          if (convResp.ok) {
            const convData = await convResp.json();
            textToCopy = convData.content;
          } else {
            textToCopy = state.currentRawMarkdown;
          }
        }
        await navigator.clipboard.writeText(textToCopy);
        toast.success("🚀 ¡Artículo copiado con formato editorial de 3 columnas para Astro!");
      } catch (err) {
        await navigator.clipboard.writeText(state.currentRawMarkdown);
        toast.info("Markdown copiado al portapapeles.");
      }
    });
  }

  if (btnDownloadAstro) {
    btnDownloadAstro.addEventListener("click", () => {
      if (!state.currentRawMarkdown) {
        toast.warning("No hay contenido para descargar.");
        return;
      }
      const title = getArticleTitle();
      const a = document.createElement("a");
      a.href = `/api/export/astro/${encodeURIComponent(title)}?download=true`;
      a.download = "articulo-astro.md";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      toast.success("Descargando Markdown para Astro...");
    });
  }

  // Descargar Markdown puro (.md) desde el contenido actual del editor
  if (btnDownloadMarkdown) {
    btnDownloadMarkdown.addEventListener("click", () => {
      if (!state.currentRawMarkdown) {
        toast.warning("No hay contenido Markdown para descargar.");
        return;
      }
      const blob = new Blob([state.currentRawMarkdown], { type: "text/markdown;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${slugify(getArticleTitle())}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Archivo Markdown (.MD) descargado.");
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

  if (btnPrint) {
    btnPrint.addEventListener("click", () => {
      window.print();
    });
  }
}
