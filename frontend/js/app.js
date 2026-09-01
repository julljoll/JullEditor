/**
 * Granite Cyber-Legal Blog Generator — Orquestador Principal ES6
 * Integra módulos especializados para Ingesta Docling, Scraping, Streaming SSE,
 * Auditoría SEO Top-Tier 2026, Exportación WordPress, Historial y Atajos.
 */

import { toast } from "./modules/toast-notifications.js";
import { checkSystemHealth, setGraniteVisualStatus } from "./modules/health-check.js";
import { initDoclingHandler } from "./modules/docling-handler.js";
import { initScraperHandler } from "./modules/scraper-handler.js";
import { renderArticle } from "./modules/markdown-renderer.js";
import { updateSeoAudit } from "./modules/seo-audit.js";
import { initWordPressExporter } from "./modules/wordpress-exporter.js";
import { initArticleHistory } from "./modules/article-history.js";
import { initKeyboardShortcuts } from "./modules/keyboard-shortcuts.js";
import { initArticleGenerator } from "./modules/article-generator.js";

document.addEventListener("DOMContentLoaded", () => {
  // Estado global compartido
  const state = {
    selectedTheme: "cybersecurity",
    currentRawMarkdown: "",
    currentBannerUrl: "",
    scraperMetadata: {
      source_lang: "",
      source_author: "",
      source_date: "",
      source_section: ""
    }
  };

  // 1. Health check inicial
  checkSystemHealth();

  // 2. Manejo de Pestañas de Ingesta (Docling / Texto / URL)
  const ingestTabs = document.querySelectorAll(".ingest-tab");
  const doclingUploadSection = document.getElementById("doclingUploadSection");
  const urlSection = document.getElementById("urlSection");

  ingestTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      ingestTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const mode = tab.dataset.mode;
      if (mode === "docling") {
        if (doclingUploadSection) doclingUploadSection.style.display = "block";
        if (urlSection) urlSection.style.display = "none";
      } else if (mode === "text") {
        if (doclingUploadSection) doclingUploadSection.style.display = "none";
        if (urlSection) urlSection.style.display = "none";
      } else if (mode === "url") {
        if (doclingUploadSection) doclingUploadSection.style.display = "none";
        if (urlSection) urlSection.style.display = "block";
      }
    });
  });

  // 3. Manejo de Temas (Pills)
  const themePills = document.querySelectorAll(".theme-pill");
  const tempSlider = document.getElementById("tempSlider");
  const tempValueLabel = document.getElementById("tempValueLabel");

  const THEME_DEFAULTS = {
    cybersecurity: 0.5,
    ai_data: 0.6,
    legal_tech: 0.4,
    science_tech: 0.7
  };

  function selectTheme(themeKey) {
    themePills.forEach((p) => {
      if (p.dataset.theme === themeKey) {
        p.classList.add("active");
      } else {
        p.classList.remove("active");
      }
    });
    state.selectedTheme = themeKey;

    if (tempSlider && THEME_DEFAULTS[themeKey]) {
      tempSlider.value = THEME_DEFAULTS[themeKey];
      if (tempValueLabel) tempValueLabel.innerText = `${THEME_DEFAULTS[themeKey]} (Óptimo)`;
    }
  }

  themePills.forEach((pill) => {
    pill.addEventListener("click", () => {
      selectTheme(pill.dataset.theme);
    });
  });

  if (tempSlider && tempValueLabel) {
    tempSlider.addEventListener("input", (e) => {
      tempValueLabel.innerText = `${e.target.value}`;
    });
  }

  // 4. Inicializar Docling Handler
  initDoclingHandler({
    onThemeDetected: (theme) => selectTheme(theme)
  });

  // 5. Inicializar Scraper Handler
  initScraperHandler(state);

  // 6. Inicializar Exportador de WordPress, Markdown, HTML
  initWordPressExporter(state);

  // 7. Inicializar Historial de Artículos
  const historyModule = initArticleHistory(state);

  // 8. Inicializar Generador de Artículos
  const generatorModule = initArticleGenerator(state, {
    onArticleSaved: () => {
      if (historyModule && historyModule.refresh) {
        historyModule.refresh();
      }
    }
  });

  // 9. Inicializar Atajos de Teclado
  initKeyboardShortcuts({
    onGenerate: () => generatorModule.generate(),
    onStop: () => generatorModule.stop()
  });

  // 10. Botón de Limpieza
  const btnClear = document.getElementById("btnClear");
  if (btnClear) {
    btnClear.addEventListener("click", () => {
      state.currentRawMarkdown = "";
      state.currentBannerUrl = "";
      const headerBannerWrapper = document.getElementById("headerBannerWrapper");
      const btnDownloadSelectedImage = document.getElementById("btnDownloadSelectedImage");
      const sourceText = document.getElementById("sourceText");
      const sourceTitle = document.getElementById("sourceTitle");
      const urlInput = document.getElementById("urlInput");
      const terminalTokens = document.getElementById("terminalTokens");
      const terminalTime = document.getElementById("terminalTime");

      if (headerBannerWrapper) headerBannerWrapper.style.display = "none";
      if (btnDownloadSelectedImage) btnDownloadSelectedImage.style.display = "none";
      renderArticle("");
      updateSeoAudit("");
      if (sourceText) sourceText.value = "";
      if (sourceTitle) sourceTitle.value = "";
      if (urlInput) urlInput.value = "";
      if (terminalTokens) terminalTokens.innerText = "0";
      if (terminalTime) terminalTime.innerText = "0s";
      toast.info("Editor limpiado.");
    });
  }
});
