/**
 * Módulo para alternar el diseño Revista Digital (3 Columnas) vs Estándar (1 Columna),
 * Modo Lectura a pantalla completa y calibración visual del modo editorial.
 */

import { renderArticle } from "./markdown-renderer.js";

export function initLayoutToggle(state) {
  const btnToggleColumns = document.getElementById("btnToggleColumns");
  const btnToggleColumnsText = document.getElementById("btnToggleColumnsText");
  const btnReadingMode = document.getElementById("btnReadingMode");
  const btnReadingModeText = document.getElementById("btnReadingModeText");
  const articleContainer = document.getElementById("articleContainer");
  const appContainer = document.querySelector(".app-container");
  const editorialModeSelect = document.getElementById("editorialMode");
  const tempSlider = document.getElementById("tempSlider");
  const tempValueLabel = document.getElementById("tempValueLabel");

  // 1. Restaurar preferencias de diseño desde localStorage
  const savedLayout = localStorage.getItem("granite.layout") || "magazine";
  // El modo lectura NUNCA debe persistir al iniciar para asegurar que el panel de creación principal siempre sea visible
  localStorage.removeItem("granite.reading");
  const savedReading = false;

  function applyLayout(layout) {
    if (!articleContainer) return;
    if (layout === "single") {
      articleContainer.dataset.layout = "single";
      if (btnToggleColumnsText) btnToggleColumnsText.innerText = "1 Columna";
      if (btnToggleColumns) {
        btnToggleColumns.title = "Cambiar a Revista 3 Columnas";
        btnToggleColumns.classList.remove("active");
      }
    } else {
      articleContainer.dataset.layout = "magazine";
      if (btnToggleColumnsText) btnToggleColumnsText.innerText = "Revista 3 Col";
      if (btnToggleColumns) {
        btnToggleColumns.title = "Cambiar a 1 Columna Estándar";
        btnToggleColumns.classList.add("active");
      }
    }
    localStorage.setItem("granite.layout", layout);
    if (state && state.currentRawMarkdown) {
      renderArticle(state.currentRawMarkdown, false);
    }
  }

  function applyReadingMode(active) {
    if (!appContainer) return;
    if (active) {
      appContainer.classList.add("reading-mode");
      if (btnReadingModeText) btnReadingModeText.innerText = "Vista 3 Paneles";
      if (btnReadingMode) {
        btnReadingMode.classList.add("active");
        btnReadingMode.title = "Restaurar paneles laterales de configuración y SEO";
      }
    } else {
      appContainer.classList.remove("reading-mode");
      if (btnReadingModeText) btnReadingModeText.innerText = "Modo Lectura";
      if (btnReadingMode) {
        btnReadingMode.classList.remove("active");
        btnReadingMode.title = "Ocultar paneles laterales para lectura completa en 3 columnas";
      }
    }
    localStorage.setItem("granite.reading", active ? "true" : "false");
  }

  applyLayout(savedLayout);
  applyReadingMode(savedReading);

  if (btnToggleColumns) {
    btnToggleColumns.addEventListener("click", () => {
      const current = articleContainer ? articleContainer.dataset.layout : "magazine";
      const next = current === "single" ? "magazine" : "single";
      applyLayout(next);
    });
  }

  if (btnReadingMode) {
    btnReadingMode.addEventListener("click", () => {
      const isReading = appContainer && appContainer.classList.contains("reading-mode");
      applyReadingMode(!isReading);
    });
  }

  // 2. Calibración automática de temperatura según el modo editorial seleccionado
  if (editorialModeSelect && tempSlider) {
    editorialModeSelect.addEventListener("change", () => {
      const mode = editorialModeSelect.value;
      if (mode === "magazine") {
        // En modo revista interpretativa se recomienda 0.45 para fluidez analítica
        tempSlider.value = "0.45";
        if (tempValueLabel) {
          tempValueLabel.innerText = "0.45 (Equilibrio Interpretativo)";
          tempValueLabel.style.color = "var(--color-primary)";
        }
      } else {
        // En modo clásico se recomienda 0.2 para rigor factual estricto
        tempSlider.value = "0.2";
        if (tempValueLabel) {
          tempValueLabel.innerText = "0.2 (Rigor Factual)";
          tempValueLabel.style.color = "var(--color-secondary)";
        }
      }
    });
  }

  return {
    setLayout: applyLayout,
    setReadingMode: applyReadingMode
  };
}
