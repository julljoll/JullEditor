/**
 * Módulo de Vista Previa en Tiempo Real (Live Preview)
 * - Esqueleto dinámico inteligente (shimmer) basado en la configuración actual
 * - Checklist de Estructura Viva (12 bloques canónicos de AGENTS.md)
 * - Barra de progreso de generación en vivo (sección actual, palabras, tokens/s)
 * - Simulador de dispositivos responsive (Escritorio, Tablet, Móvil)
 * - Pestañas de previsualización (Revista, Markdown puro, WordPress HTML iframe)
 * - Control inteligente de auto-scroll con botón flotante "Seguir generación ↓"
 */

import { generateWordPressHtml } from "./wordpress-exporter.js";

export function initLivePreview(state) {
  const articleContainer = document.getElementById("articleContainer");
  const articleView = document.getElementById("articleView");
  const livePreviewMarkdown = document.getElementById("livePreviewMarkdown");
  const livePreviewWp = document.getElementById("livePreviewWp");
  const btnFollowStream = document.getElementById("btnFollowStream");
  const liveStructureList = document.getElementById("liveStructureList");
  const liveProgressSection = document.getElementById("liveProgressSection");
  const liveProgressBar = document.getElementById("liveProgressBar");
  const liveProgressBarWrap = document.getElementById("liveProgressBarWrap");
  const liveProgressWords = document.getElementById("liveProgressWords");

  const sourceTitle = document.getElementById("sourceTitle");
  const toneSelect = document.getElementById("toneSelect");
  const editorialMode = document.getElementById("editorialMode");
  const jurisdictionSelect = document.getElementById("jurisdictionSelect");
  const wordCountTarget = document.getElementById("wordCountTarget");

  let activeTab = localStorage.getItem("granite.previewTab") || "magazine";
  let activeDevice = localStorage.getItem("granite.device") || "desktop";

  // 1. Esqueleto vivo antes de generar
  // 1. Maqueta viva de vista previa en blanco (Lienzo en Espera)
  function renderSkeleton() {
    if (state.currentRawMarkdown && state.currentRawMarkdown.trim().length > 0) return;
    if (!articleView) return;

    const userTitle = (sourceTitle && sourceTitle.value.trim()) || "";
    const toneText = (toneSelect && toneSelect.options[toneSelect.selectedIndex]?.text) || "Rigor Jurídico Doctrinal (Forense / TSJ)";
    const mode = (editorialMode && editorialMode.value) || "magazine";
    const jur = (jurisdictionSelect && jurisdictionSelect.value) || "Venezuela (CRBV / Delitos Inf.)";
    const targetWords = parseInt((wordCountTarget && wordCountTarget.value) || "1000", 10);
    const readTime = Math.ceil(targetWords / 200);

    let skeletonHtml = `
      <div class="canvas-waiting-state" style="padding: 24px 20px; max-width: 900px; margin: 0 auto; text-align: left;">
        
        <!-- Tarjeta Hero de Estado Inicial -->
        <div style="background: var(--bg-elevated); border: 1px solid var(--border-gold); border-radius: var(--radius-card); padding: 24px; margin-bottom: 24px; box-shadow: var(--co-shadow-2);">
          <div style="display: flex; align-items: flex-start; gap: 16px;">
            <div style="width: 48px; height: 48px; border-radius: 10px; background: var(--color-primary-soft); border: var(--border-gold); display: flex; align-items: center; justify-content: center; color: var(--color-primary); flex-shrink: 0;">
              <span class="material-symbols-outlined" style="font-size: 1.75rem;">history_edu</span>
            </div>
            <div style="flex: 1;">
              <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--color-primary); margin: 0;">
                  Lienzo de Redacción Listo (Esperando Ingesta)
                </h2>
                <span class="badge" style="background: var(--color-secondary-soft); color: var(--color-secondary); border: var(--border-green); font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">
                  100% OFFLINE · STANDBY
                </span>
              </div>
              <p style="color: var(--text-secondary); font-size: 0.92rem; margin: 0 0 14px 0; line-height: 1.55;">
                Aún no has generado ningún artículo en esta sesión. Ingresa tu texto o carga tus archivos en el <strong style="color: var(--text-primary);">Paso ① (Fuente de Origen)</strong> del panel izquierdo y presiona <strong style="color: var(--color-primary);">"Redactar Artículo"</strong> (<kbd>Ctrl+Enter</kbd>) para ver el contenido transmitirse en tiempo real.
              </p>
              
              <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="skel-chip"><span class="material-symbols-outlined" style="font-size:0.8rem;">auto_stories</span> FORMATO: ${mode === "magazine" ? "REVISTA 3 COL." : "RESUMEN CLÁSICO"}</span>
                <span class="skel-chip"><span class="material-symbols-outlined" style="font-size:0.8rem;">gavel</span> JURISDICCIÓN: ${jur}</span>
                <span class="skel-chip"><span class="material-symbols-outlined" style="font-size:0.8rem;">psychology</span> TONO: ${toneText}</span>
                <span class="skel-chip"><span class="material-symbols-outlined" style="font-size:0.8rem;">schedule</span> META: ~${targetWords} PALABRAS</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Blueprint de Estructura Canónica (Plano Guía de los 12 Bloques) -->
        <div style="margin-bottom: 20px;">
          <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
            <span class="material-symbols-outlined" style="font-size: 1rem; color: var(--color-primary);">schema</span>
            Estructura Canónica que IBM Granite construirá automáticamente:
          </div>

          <div style="display: grid; gap: 12px;">
            <!-- Bloque 1: Título y Meta -->
            <div style="border: 1px dashed rgba(242, 194, 48, 0.35); background: rgba(242, 194, 48, 0.03); border-radius: 8px; padding: 14px 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; color: var(--color-secondary); font-size: 0.95rem;">
                  ${userTitle ? escapeHtml(userTitle) : "① Título H1 Primario (8-12 palabras con Keyword Clave)"}
                </span>
                <span style="font-size: 0.70rem; color: var(--text-muted); font-family: var(--font-mono);">BLOQUE 1 & 2</span>
              </div>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0; font-style: italic;">
                ↳ Meta descripción adyacente de 145 a 160 caracteres optimizada para CTR y fragmento destacado en buscadores.
              </p>
            </div>

            <!-- Bloque 2: Answer First y Cajas Ejecutivas -->
            <div style="border: 1px dashed rgba(61, 214, 140, 0.35); background: rgba(61, 214, 140, 0.03); border-radius: 8px; padding: 14px 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; color: var(--color-secondary); font-size: 0.95rem;">
                  ② Respuesta Directa (Answer-First) & Síntesis Pericial
                </span>
                <span style="font-size: 0.70rem; color: var(--text-muted); font-family: var(--font-mono);">BLOQUES 4, 5 & 6</span>
              </div>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0;">
                ↳ Resumen ejecutivo en 30 segundos, caja de síntesis de la fuente original y tesis legal/técnica en las primeras 50 palabras.
              </p>
            </div>

            <!-- Bloque 3: Cuerpo Estilo Revista Digital -->
            <div style="border: 1px dashed rgba(255, 255, 255, 0.15); background: rgba(255, 255, 255, 0.02); border-radius: 8px; padding: 14px 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; color: var(--text-primary); font-size: 0.95rem;">
                  ③ Cuerpo Canónico en 3 Columnas Fluidas (Modo Revista)
                </span>
                <span style="font-size: 0.70rem; color: var(--text-muted); font-family: var(--font-mono);">BLOQUES 7, 8 & 9</span>
              </div>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0; line-height: 1.5;">
                ↳ Desarrollo técnico con letra capitular · Marco jurídico exclusivo (CRBV, Delitos Informáticos, Infogobierno) · Viabilidad y compatibilidad de infraestructura en Venezuela (CNTI).
              </p>
            </div>

            <!-- Bloque 4: FAQ y Microdatos Schema -->
            <div style="border: 1px dashed rgba(242, 194, 48, 0.25); background: rgba(242, 194, 48, 0.02); border-radius: 8px; padding: 14px 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 700; color: var(--color-primary); font-size: 0.95rem;">
                  ④ FAQ de 3 Preguntas Frecuentes & Doble Schema JSON-LD
                </span>
                <span style="font-size: 0.70rem; color: var(--text-muted); font-family: var(--font-mono);">BLOQUES 10, 11 & 12</span>
              </div>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin: 0;">
                ↳ Citas deontológicas, atribución a derechos de autor y microdatos estructurados <code>TechArticle</code> y <code>FAQPage</code> listos para WordPress y Sitejet.
              </p>
            </div>
          </div>
        </div>

        <div style="text-align: center; padding: 12px; color: var(--text-muted); font-size: 0.82rem;">
          <span class="material-symbols-outlined" style="vertical-align: middle; font-size: 1rem; margin-right: 4px; color: var(--color-primary);">keyboard</span>
          Presiona <kbd style="padding: 2px 6px; border: 1px solid var(--border-subtle); border-radius: 3px; font-size: 0.75rem;">Ctrl + Enter</kbd> cuando tu fuente esté lista para iniciar.
        </div>

      </div>
    `;

    articleView.innerHTML = skeletonHtml;
  }


  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Escuchar cambios de configuración para actualizar el esqueleto
  const configInputs = [sourceTitle, toneSelect, editorialMode, jurisdictionSelect, wordCountTarget];
  configInputs.forEach((input) => {
    if (input) {
      input.addEventListener("input", debounce(renderSkeleton, 150));
      input.addEventListener("change", renderSkeleton);
    }
  });

  document.querySelectorAll(".theme-pill").forEach((pill) => {
    pill.addEventListener("click", () => setTimeout(renderSkeleton, 50));
  });

  const btnToggleColumns = document.getElementById("btnToggleColumns");
  if (btnToggleColumns) {
    btnToggleColumns.addEventListener("click", () => setTimeout(renderSkeleton, 50));
  }

  // 2. Estructura viva (12 Bloques canónicos)
  const STRUCTURE_RULES = [
    { id: "struct-h1", label: "Título H1 Optimizado", regex: /^#\s+\S/m, selector: "h1" },
    { id: "struct-meta", label: "Meta Descripción (145-160 car.)", regex: /\*\*Meta descripci[oó]n:\*\*/i, selector: ".meta-description-callout" },
    { id: "struct-seo-ribbon", label: "Cinta de Badges SEO", regex: /Palabra Clave Primaria:/i, selector: ".seo-badge-container, .seo-badge" },
    { id: "struct-answer-first", label: "Párrafo Answer-First", regex: /^En resumen,/mi, selector: "p" },
    { id: "struct-toc", label: "Tabla de Contenidos", regex: /Tabla de Contenidos/i, selector: ".toc-card" },
    { id: "struct-summary", label: "📌 Resumen Práctico Fuente", regex: /📌 Resumen Pr[aá]ctico/i, selector: ".source-summary-callout" },
    { id: "struct-30s", label: "⚡ Resumen Ejecutivo 30s", regex: /⚡ Resumen Ejecutivo/i, selector: ".source-summary-callout--exec" },
    { id: "struct-our-take", label: "🔎 Nuestra Lectura Editorial", regex: /Nuestra Lectura del Art[ií]culo/i, selector: ".source-summary-callout--simple", modeCheck: "magazine" },
    { id: "struct-legal", label: "Marco Legal y Normativo", regex: /^##\s.*(Marco\s+(Legal|Regulatorio|Normativo))/mi, selector: "h2" },
    { id: "struct-faq", label: "FAQ ×3 con Preguntas/Respuestas", regex: /\*\*P:\s*/g, count: 3, selector: ".faq-section-card" },
    { id: "struct-copyright", label: "Derechos de Autor y Atribución", regex: /Derechos de Autor/i, selector: ".copyright-card" },
    { id: "struct-schema", label: "Schema JSON-LD (Scholarly/Tech + FAQ)", regex: /"@type":\s*"(TechArticle|ScholarlyArticle|FAQPage)"/g, count: 2, selector: "pre code" },
  ];

  function updateLiveStructure(markdown) {
    if (!liveStructureList) return;
    const currentMode = (editorialMode && editorialMode.value) || "magazine";

    STRUCTURE_RULES.forEach((rule) => {
      let itemEl = document.getElementById(rule.id);
      if (!itemEl) return;

      if (rule.modeCheck && rule.modeCheck !== currentMode) {
        itemEl.style.display = "none";
        return;
      }
      itemEl.style.display = "flex";

      let isDone = false;
      if (markdown) {
        if (rule.count) {
          const matches = markdown.match(rule.regex);
          isDone = matches && matches.length >= rule.count;
        } else {
          isDone = rule.regex.test(markdown);
        }
      }

      const prevDone = itemEl.getAttribute("data-state") === "done";
      itemEl.setAttribute("data-state", isDone ? "done" : "pending");

      const icon = itemEl.querySelector(".struct-icon");
      if (icon) {
        icon.textContent = isDone ? "check_circle" : "radio_button_unchecked";
      }

      if (isDone && !prevDone) {
        itemEl.classList.add("just-completed");
        setTimeout(() => itemEl.classList.remove("just-completed"), 500);
      }
    });
  }

  // Click en ítem de estructura viva → scroll a la sección en artículo
  if (liveStructureList) {
    liveStructureList.addEventListener("click", (e) => {
      const li = e.target.closest("li[data-state='done']");
      if (!li) return;
      const rule = STRUCTURE_RULES.find((r) => r.id === li.id);
      if (rule && rule.selector && articleView) {
        const target = articleView.querySelector(rule.selector);
        if (target) {
          target.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    });
  }

  // 3. Barra de progreso en vivo
  function updateLiveProgress(markdown, isStreaming) {
    if (!liveProgressBarWrap) return;

    if (!isStreaming) {
      liveProgressBarWrap.classList.remove("streaming");
      return;
    }

    liveProgressBarWrap.classList.add("streaming");

    // Extraer última sección H2 detectada
    if (markdown && liveProgressSection) {
      const h2Matches = Array.from(markdown.matchAll(/^##\s+([^\n]+)/gm));
      if (h2Matches.length > 0) {
        const lastH2 = h2Matches[h2Matches.length - 1][1].replace(/[\*\_\[\]\#]/g, "").trim();
        liveProgressSection.textContent = `Generando: ${lastH2}`;
      } else {
        liveProgressSection.textContent = "Generando estructura editorial...";
      }
    }

    // Progreso de palabras
    const words = markdown ? markdown.split(/\s+/).filter(Boolean).length : 0;
    const target = parseInt((wordCountTarget && wordCountTarget.value) || "1000", 10);
    const pct = Math.min(100, Math.round((words / target) * 100));

    if (liveProgressBar) {
      liveProgressBar.style.width = `${pct}%`;
    }
    if (liveProgressWords) {
      liveProgressWords.textContent = `${words.toLocaleString()} / ${target} pal. (${pct}%)`;
    }
  }

  // 4. Simulador de dispositivos responsive
  function applyDevice(device) {
    activeDevice = device;
    localStorage.setItem("granite.device", device);
    if (articleContainer) {
      articleContainer.dataset.device = device;
    }
    document.querySelectorAll(".btn-device").forEach((btn) => {
      const isActive = btn.dataset.device === device;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-checked", isActive ? "true" : "false");
    });
  }

  document.querySelectorAll(".btn-device").forEach((btn) => {
    btn.addEventListener("click", () => {
      applyDevice(btn.dataset.device || "desktop");
    });
  });

  // 5. Pestañas de Vista Previa (Revista, Markdown, WordPress)
  let lastWpUpdate = 0;
  let lastMdUpdate = 0;

  function switchTab(tab) {
    activeTab = tab;
    localStorage.setItem("granite.previewTab", tab);

    document.querySelectorAll(".preview-tab").forEach((btn) => {
      const isActive = btn.dataset.tab === tab;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive ? "true" : "false");
    });

    if (articleView) articleView.style.display = tab === "magazine" ? "block" : "none";
    if (livePreviewMarkdown) livePreviewMarkdown.style.display = tab === "markdown" ? "block" : "none";
    if (livePreviewWp) livePreviewWp.style.display = tab === "wordpress" ? "block" : "none";

    // Actualizar vista inmediatamente al cambiar de pestaña
    if (tab === "markdown" && livePreviewMarkdown) {
      livePreviewMarkdown.textContent = state.currentRawMarkdown || "Sin contenido Markdown redactado.";
    } else if (tab === "wordpress" && livePreviewWp) {
      updateWordPressPreview();
    }
  }

  function updateWordPressPreview() {
    if (!livePreviewWp || activeTab !== "wordpress") return;
    if (!state.currentRawMarkdown) {
      livePreviewWp.srcdoc = `
        <!DOCTYPE html>
        <html lang="es">
        <head>
          <meta charset="utf-8">
          <style>body { font-family: Arial, sans-serif; background: #ffffff; color: #666; padding: 24px; font-style: italic; }</style>
        </head>
        <body>
          <p>El código HTML estructurado para WordPress Gutenberg aparecerá aquí tras iniciar la redacción con IBM Granite.</p>
        </body>
        </html>
      `;
      return;
    }
    const wpContent = generateWordPressHtml(state);
    const docHtml = `
      <!DOCTYPE html>
      <html lang="es">
      <head>
        <meta charset="utf-8">
        <style>
          body { font-family: Arial, sans-serif; background: #ffffff; color: #1a1a1a; padding: 24px; margin: 0; line-height: 1.6; }
          img { max-width: 100%; height: auto; }
        </style>
      </head>
      <body>
        ${wpContent || "<p style='color:#666; font-style:italic;'>El contenido en formato WordPress Gutenberg aparecerá aquí...</p>"}
      </body>
      </html>
    `;
    livePreviewWp.srcdoc = docHtml;
  }

  document.querySelectorAll(".preview-tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      switchTab(btn.dataset.tab || "magazine");
    });
  });

  // 6. Seguimiento inteligente del stream de generación (Auto-scroll & Botón Flotante)
  if (articleContainer) {
    articleContainer.addEventListener("scroll", () => {
      if (liveProgressBarWrap && liveProgressBarWrap.classList.contains("streaming")) {
        const distanceFromBottom = articleContainer.scrollHeight - articleContainer.scrollTop - articleContainer.clientHeight;
        if (distanceFromBottom > 120) {
          articleContainer.dataset.follow = "false";
          if (btnFollowStream) btnFollowStream.classList.add("visible");
        } else {
          articleContainer.dataset.follow = "true";
          if (btnFollowStream) btnFollowStream.classList.remove("visible");
        }
      }
    });
  }

  if (btnFollowStream) {
    btnFollowStream.addEventListener("click", () => {
      if (articleContainer) {
        articleContainer.dataset.follow = "true";
        articleContainer.scrollTo({ top: articleContainer.scrollHeight, behavior: "smooth" });
      }
      btnFollowStream.classList.remove("visible");
    });
  }

  // 7. Escucha del evento global unificado "article:rendered"
  document.addEventListener("article:rendered", (e) => {
    const { markdown, isStreaming } = e.detail || {};

    if (!markdown || !markdown.trim()) {
      renderSkeleton();
      updateLiveStructure("");
      updateLiveProgress("", false);
      return;
    }

    updateLiveStructure(markdown);
    updateLiveProgress(markdown, isStreaming);

    const now = Date.now();

    // Actualización de pestaña Markdown
    if (activeTab === "markdown" && livePreviewMarkdown && now - lastMdUpdate > 250) {
      livePreviewMarkdown.textContent = markdown;
      lastMdUpdate = now;
    }

    // Actualización de pestaña WordPress (con throttle de 1s para no ralentizar el render)
    if (activeTab === "wordpress" && now - lastWpUpdate > 1000) {
      updateWordPressPreview();
      lastWpUpdate = now;
    }
  });

  // Atajos de teclado en live preview (Ctrl+1/2/3 para tabs, Ctrl+Shift+F para follow)
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && !e.shiftKey && !e.altKey) {
      if (e.key === "1") { e.preventDefault(); switchTab("magazine"); }
      if (e.key === "2") { e.preventDefault(); switchTab("markdown"); }
      if (e.key === "3") { e.preventDefault(); switchTab("wordpress"); }
    }
    if (e.ctrlKey && e.shiftKey && (e.key === "F" || e.key === "f")) {
      e.preventDefault();
      if (btnFollowStream && btnFollowStream.classList.contains("visible")) {
        btnFollowStream.click();
      }
    }
  });

  // Inicialización
  applyDevice(activeDevice);
  switchTab(activeTab);
  renderSkeleton();
}

function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
