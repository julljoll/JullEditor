/**
 * Módulo de Scraping de URLs Externas e Imagen de Cabecera Original
 */

import { toast } from "./toast-notifications.js";

export function initScraperHandler(state) {
  const urlInput = document.getElementById("urlInput");
  const btnScrape = document.getElementById("btnScrape");
  const sourceTitle = document.getElementById("sourceTitle");
  const sourceText = document.getElementById("sourceText");
  const headerBannerWrapper = document.getElementById("headerBannerWrapper");
  const headerBannerImg = document.getElementById("headerBannerImg");
  const headerBannerBadgeText = document.getElementById("headerBannerBadgeText");
  const btnDownloadSelectedImage = document.getElementById("btnDownloadSelectedImage");
  const terminalStatus = document.getElementById("terminalStatus");

  if (!btnScrape) return;

  btnScrape.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      toast.warning("Por favor ingresa una URL válida.");
      return;
    }

    btnScrape.disabled = true;
    btnScrape.innerHTML = '<span class="material-symbols-outlined">hourglass_top</span> Extrayendo...';
    if (terminalStatus) terminalStatus.innerText = "SCRAPING & ANALYZING...";

    try {
      const res = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Error extrayendo artículo");
      }

      const data = await res.json();
      if (sourceTitle) {
        sourceTitle.value = data.title || "";
        sourceTitle.dispatchEvent(new Event("input"));
      }
      if (sourceText) {
        sourceText.value = data.text || "";
        sourceText.dispatchEvent(new Event("input"));
      }

      // Guardar metadatos en el objeto state compartido
      state.scraperMetadata.source_lang = data.source_lang || "";
      state.scraperMetadata.source_author = data.source_author || "";
      state.scraperMetadata.source_date = data.source_date || "";
      state.scraperMetadata.source_section = data.source_section || "";

      if (terminalStatus) {
        terminalStatus.innerText = `ANALIZADO (${data.word_count} palabras)`;
        terminalStatus.style.color = "var(--color-secondary)";
      }

      if (data.image_url) {
        state.currentBannerUrl = data.image_url;
        if (headerBannerImg) headerBannerImg.src = data.image_url;
        if (headerBannerBadgeText) headerBannerBadgeText.innerText = "IMAGEN DE LA FUENTE ORIGINAL";
        if (headerBannerWrapper) headerBannerWrapper.style.display = "block";
        if (btnDownloadSelectedImage) btnDownloadSelectedImage.style.display = "inline-flex";
      } else {
        state.currentBannerUrl = "";
        if (headerBannerWrapper) headerBannerWrapper.style.display = "none";
        if (btnDownloadSelectedImage) btnDownloadSelectedImage.style.display = "none";
      }

      toast.success(`Artículo extraído con éxito (${data.word_count} palabras).`);

      btnScrape.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Extraído';
      setTimeout(() => {
        btnScrape.disabled = false;
        btnScrape.innerHTML = '<span class="material-symbols-outlined">download</span> Extraer';
      }, 2000);

    } catch (err) {
      toast.error(`No se pudo extraer el artículo: ${err.message}`);
      btnScrape.disabled = false;
      btnScrape.innerHTML = '<span class="material-symbols-outlined">download</span> Extraer';
      if (terminalStatus) {
        terminalStatus.innerText = "ERROR EN SCRAPING";
        terminalStatus.style.color = "var(--color-error)";
      }
    }
  });
}
