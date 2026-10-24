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
import { updateSeoAudit, runBackendSeoAudit } from "./modules/seo-audit.js";
import { initWordPressExporter } from "./modules/wordpress-exporter.js";
import { initSitejetExporter } from "./modules/sitejet-exporter.js";
import { initArticleHistory } from "./modules/article-history.js";
import { initKeyboardShortcuts } from "./modules/keyboard-shortcuts.js";
import { initArticleGenerator } from "./modules/article-generator.js";
import { initLayoutToggle } from "./modules/layout-toggle.js";
import { initCreationFlow } from "./modules/creation-flow.js";
import { initToolbarMenu } from "./modules/toolbar-menu.js";
import { initLivePreview } from "./modules/live-preview.js";

document.addEventListener("DOMContentLoaded", () => {
  // Asegurar que la página siempre inicie arriba en el panel principal de creación
  window.scrollTo(0, 0);

  // Estado global compartido
  const state = {
    selectedTheme: "legal_tech",
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
  const urlInput = document.getElementById("urlInput");
  const sourceText = document.getElementById("sourceText");

  function setIngestMode(mode) {
    ingestTabs.forEach((tab) => {
      const isActive = tab.dataset.mode === mode;
      tab.classList.toggle("active", isActive);
      tab.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    if (mode === "docling") {
      if (doclingUploadSection) doclingUploadSection.style.display = "block";
      if (urlSection) urlSection.style.display = "none";
    } else if (mode === "text") {
      if (doclingUploadSection) doclingUploadSection.style.display = "none";
      if (urlSection) urlSection.style.display = "none";
      if (sourceText) sourceText.focus();
    } else if (mode === "url") {
      if (doclingUploadSection) doclingUploadSection.style.display = "none";
      if (urlSection) {
        urlSection.style.display = "block";
        if (urlInput) urlInput.focus();
      }
    }
  }

  // Delegación de eventos y listeners directos para máxima confiabilidad
  const ingestTabsContainer = document.querySelector(".ingest-tabs");
  if (ingestTabsContainer) {
    ingestTabsContainer.addEventListener("click", (e) => {
      const tab = e.target.closest(".ingest-tab");
      if (tab && tab.dataset.mode) {
        setIngestMode(tab.dataset.mode);
      }
    });
  }

  // Exponer a window para integración y testing
  window.setIngestMode = setIngestMode;

  // 3. Manejo de Temas (Pills)
  const themePills = document.querySelectorAll(".theme-pill");
  const tempSlider = document.getElementById("tempSlider");
  const tempValueLabel = document.getElementById("tempValueLabel");

  const THEME_DEFAULTS = {
    legal_tech: 0.2,
    forensic_law: 0.2,
    cybersecurity: 0.25,
    ai_data: 0.3,
    science_tech: 0.3
  };

  function formatTempLabel(val) {
    if (val <= 0.3) return `${val} (Rigor Factual)`;
    if (val <= 0.5) return `${val} (Moderado)`;
    return `${val} (Creativo / Riesgo)`;
  }

  function formatTempColor(val) {
    if (val <= 0.3) return "var(--color-secondary)";
    if (val <= 0.5) return "var(--color-gold)";
    return "var(--color-error)";
  }

  function selectTheme(themeKey) {
    themePills.forEach((p) => {
      if (p.dataset.theme === themeKey) {
        p.classList.add("active");
      } else {
        p.classList.remove("active");
      }
    });
    state.selectedTheme = themeKey;

    if (tempSlider && THEME_DEFAULTS[themeKey] !== undefined) {
      const val = THEME_DEFAULTS[themeKey];
      tempSlider.value = val;
      if (tempValueLabel) {
        tempValueLabel.innerText = formatTempLabel(val);
        tempValueLabel.style.color = formatTempColor(val);
      }
    }
  }

  themePills.forEach((pill) => {
    pill.addEventListener("click", () => {
      selectTheme(pill.dataset.theme);
    });
  });

  // Inicializar tema y temperatura por defecto (LegalTech 0.2 Rigor Factual para máxima puntuación SEO & Deontología)
  selectTheme("legal_tech");

  const toneSelect = document.getElementById("toneSelect");
  const wordCountTarget = document.getElementById("wordCountTarget");

  if (toneSelect) {
    toneSelect.addEventListener("change", () => {
      if (toneSelect.value === "revista_cientifica_law_tech") {
        if (wordCountTarget) wordCountTarget.value = "1500";
        if (tempSlider) {
          tempSlider.value = 0.2;
          if (tempValueLabel) {
            tempValueLabel.innerText = "0.2 (Rigor Científico & Doctrinal)";
            tempValueLabel.style.color = "var(--color-secondary)";
          }
        }
        selectTheme("forensic_law");
        toast.info("Modo Revista Científica Arbitrada activado: Rigor 0.20 · Extensión ~1.500 pal.");
      }
    });
  }

  if (tempSlider && tempValueLabel) {
    tempSlider.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      tempValueLabel.innerText = formatTempLabel(val);
      tempValueLabel.style.color = formatTempColor(val);
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

  // 6.1 Inicializar Exportador Especializado para Sitejet Builder (Namecheap)
  initSitejetExporter(state);

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

  // 9.1 Inicializar Alternador de Revista 3 Columnas y Modo Lectura
  initLayoutToggle(state);

  // 9.2 Inicializar Flujo Guiado de Creación (Stepper, validación fuente, segmentos)
  initCreationFlow(state);

  // 9.3 Inicializar Menú Accesible de Toolbar (Copiar ▾)
  initToolbarMenu();

  // 9.4 Inicializar Vista Previa en Vivo (Esqueleto vivo, estructura 12 bloques, tabs, streaming)
  initLivePreview(state);

  // 10. Auditoría Profunda 2026 y Sincronización Jurisdiccional
  const btnDeepAudit = document.getElementById("btnDeepAudit");
  const jurisdictionSelect = document.getElementById("jurisdictionSelect");
  const terminalJurisdiction = document.getElementById("terminalJurisdiction");

  if (jurisdictionSelect && terminalJurisdiction) {
    jurisdictionSelect.addEventListener("change", () => {
      const jur = jurisdictionSelect.value;
      if (jur === "ve" || jur === "venezuela") terminalJurisdiction.innerText = "VENEZUELA 🇻🇪";
      else terminalJurisdiction.innerText = "AUTO (VE) ⚖️";
    });
  }

  if (btnDeepAudit) {
    btnDeepAudit.addEventListener("click", () => {
      const jur = (jurisdictionSelect && jurisdictionSelect.value) || "auto";
      runBackendSeoAudit(state.currentRawMarkdown, jur);
    });
  }

  // 11. Botón de Limpieza
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
      if (sourceText) {
        sourceText.value = "";
        sourceText.dispatchEvent(new Event("input"));
      }
      if (sourceTitle) {
        sourceTitle.value = "";
        sourceTitle.dispatchEvent(new Event("input"));
      }
      if (urlInput) urlInput.value = "";
      if (terminalTokens) terminalTokens.innerText = "0";
      if (terminalTime) terminalTime.innerText = "0s";
      toast.info("Editor limpiado.");
    });
  }

  // 12. Carga automática de archivo precargado desde el lanzador CLI / .bat
  fetch("/api/preloaded-file")
    .then((res) => res.json())
    .then((payload) => {
      if (payload && payload.has_file && payload.data) {
        const d = payload.data;
        const sourceTitleEl = document.getElementById("sourceTitle");
        const sourceTextEl = document.getElementById("sourceText");
        const tempSliderEl = document.getElementById("tempSlider");
        const tempValueLabelEl = document.getElementById("tempValueLabel");

        if (sourceTitleEl && d.title) {
          sourceTitleEl.value = d.title;
          sourceTitleEl.dispatchEvent(new Event("input"));
        }
        if (sourceTextEl && d.content) {
          sourceTextEl.value = d.content;
          sourceTextEl.dispatchEvent(new Event("input"));
        }
        if (tempSliderEl && d.temperature !== undefined) {
          tempSliderEl.value = d.temperature;
          if (tempValueLabelEl) tempValueLabelEl.textContent = `${d.temperature} (Rigor Factual TSJ)`;
        }
        if (d.theme) {
          const pill = document.querySelector(`.theme-pill[data-theme="${d.theme}"]`);
          if (pill) pill.click();
        }
        if (d.tone) {
          const toneSel = document.getElementById("toneSelect");
          if (toneSel) toneSel.value = d.tone;
        }
        if (d.jurisdiction) {
          const jurSel = document.getElementById("jurisdictionSelect");
          if (jurSel) jurSel.value = d.jurisdiction;
        }
        if (d.target_words) {
          const wordSel = document.getElementById("wordCountTarget");
          if (wordSel) wordSel.value = String(d.target_words);
        }
        if (d.model) {
          const modelSel = document.getElementById("modelSelect");
          if (modelSel) modelSel.value = d.model;
        }
        if (d.editorial_mode) {
          const modeSel = document.getElementById("editorialMode");
          if (modeSel) {
            modeSel.value = d.editorial_mode;
            const magBtn = document.getElementById("segmentModeMagazine");
            const clsBtn = document.getElementById("segmentModeClassic");
            if (magBtn && clsBtn) {
              const isMag = d.editorial_mode === "magazine";
              magBtn.classList.toggle("active", isMag);
              clsBtn.classList.toggle("active", !isMag);
              magBtn.setAttribute("aria-checked", String(isMag));
              clsBtn.setAttribute("aria-checked", String(!isMag));
            }
          }
        }
        if (d.custom_instructions) {
          const customEl = document.getElementById("customInstructions");
          if (customEl) customEl.value = d.custom_instructions;
        }
        toast.success(`Documento TSJ precargado: ${d.filename}`);
      }
    })
    .catch(() => {});
});

