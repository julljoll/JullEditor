/**
 * Módulo de Historial de Artículos Generados y Archivados en RAG/articulos/
 */

import { toast } from "./toast-notifications.js";
import { renderArticle } from "./markdown-renderer.js";
import { updateSeoAudit } from "./seo-audit.js";

export function initArticleHistory(state) {
  const historyContainer = document.getElementById("articlesHistoryList");
  const btnRefreshHistory = document.getElementById("btnRefreshHistory");
  const sourceTitle = document.getElementById("sourceTitle");
  const sourceText = document.getElementById("sourceText");

  async function loadHistory() {
    if (!historyContainer) return;
    historyContainer.innerHTML = '<div class="text-center p-3 text-muted" style="font-size:0.8rem;"><span class="spinner-border spinner-border-sm me-1"></span> Cargando historial...</div>';

    try {
      const res = await fetch("/api/articles-history?limit=15");
      if (!res.ok) throw new Error("Error consultando historial");
      const data = await res.json();

      if (!data.articles || data.articles.length === 0) {
        historyContainer.innerHTML = '<div class="p-3 text-muted" style="font-size:0.8rem; text-align:center; font-style:italic;">No hay artículos guardados aún en Articulos Generados/.</div>';
        return;
      }

      historyContainer.innerHTML = "";
      data.articles.forEach(art => {
        const item = document.createElement("div");
        item.className = "history-item";
        item.innerHTML = `
          <div class="history-item-title" title="${art.title}">${art.title}</div>
          <div class="history-item-meta">
            <span>📅 ${art.date}</span>
            <span>📝 ${art.word_count} pal.</span>
            <span class="badge bg-secondary" style="font-size:0.65rem;">${art.theme}</span>
          </div>
        `;

        item.addEventListener("click", async () => {
          try {
            const articleRes = await fetch(`/api/articles-history/${encodeURIComponent(art.filename)}`);
            if (!articleRes.ok) throw new Error("No se pudo cargar el artículo");
            const articleData = await articleRes.json();

            state.currentRawMarkdown = articleData.content;
            renderArticle(state.currentRawMarkdown, false);
            updateSeoAudit(state.currentRawMarkdown);

            if (sourceTitle) sourceTitle.value = art.title;

            // Generar o asignar banner procedural para el artículo cargado del historial
            try {
              const bannerRes = await fetch("/api/generate-header-image", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  title: art.title,
                  theme: art.theme || state.selectedTheme || "cybersecurity"
                })
              });
              if (bannerRes.ok) {
                const bannerData = await bannerRes.json();
                state.currentBannerUrl = bannerData.url;
                const headerBannerImg = document.getElementById("headerBannerImg");
                const headerBannerWrapper = document.getElementById("headerBannerWrapper");
                const headerBannerBadgeText = document.getElementById("headerBannerBadgeText");
                const btnDownloadSelectedImage = document.getElementById("btnDownloadSelectedImage");
                if (headerBannerImg) headerBannerImg.src = bannerData.url;
                if (headerBannerBadgeText) headerBannerBadgeText.innerText = "CABECERA PROCEDURAL 16:9";
                if (headerBannerWrapper) headerBannerWrapper.style.display = "block";
                if (btnDownloadSelectedImage) btnDownloadSelectedImage.style.display = "inline-flex";
              }
            } catch (_) {}

            toast.info(`Artículo "${art.title}" cargado en el visor.`);
          } catch (e) {
            toast.error(`Error cargando artículo: ${e.message}`);
          }
        });

        historyContainer.appendChild(item);
      });

    } catch (err) {
      if (historyContainer) {
        historyContainer.innerHTML = `<div class="p-2 text-danger" style="font-size:0.8rem;">Error: ${err.message}</div>`;
      }
    }
  }

  if (btnRefreshHistory) {
    btnRefreshHistory.addEventListener("click", () => {
      loadHistory();
      toast.info("Historial actualizado.");
    });
  }

  // Carga inicial
  loadHistory();

  return { refresh: loadHistory };
}
