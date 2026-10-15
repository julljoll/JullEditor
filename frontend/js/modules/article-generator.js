/**
 * Módulo Generador de Artículos con Streaming SSE, Buffer Robusto, Throttling UI,
 * Medidor de Velocidad y Parámetros Jurisdiccionales.
 */

import { toast } from "./toast-notifications.js";
import { setGraniteVisualStatus } from "./health-check.js";
import { renderArticle } from "./markdown-renderer.js";
import { updateSeoAudit } from "./seo-audit.js";

export function initArticleGenerator(state, callbacks) {
  const btnGenerate = document.getElementById("btnGenerate");
  const btnStop = document.getElementById("btnStop");
  const sourceText = document.getElementById("sourceText");
  const sourceTitle = document.getElementById("sourceTitle");
  const urlInput = document.getElementById("urlInput");
  const toneSelect = document.getElementById("toneSelect");
  const wordCountTarget = document.getElementById("wordCountTarget");
  const modelSelect = document.getElementById("modelSelect");
  const customInstructions = document.getElementById("customInstructions");
  const jurisdictionSelect = document.getElementById("jurisdictionSelect");
  const articleView = document.getElementById("articleView");
  const tempSlider = document.getElementById("tempSlider");

  const terminalTokens = document.getElementById("terminalTokens");
  const terminalTime = document.getElementById("terminalTime");
  const terminalStatus = document.getElementById("terminalStatus");

  let abortController = null;
  let generationStartTime = 0;
  let timerInterval = null;

  async function generateArticle() {
    const rawText = sourceText.value.trim();
    if (!rawText) {
      toast.warning("Por favor ingresa o extrae un texto para redactar el artículo.");
      return;
    }

    state.currentRawMarkdown = "";
    if (articleView) articleView.innerHTML = '<span class="streaming-cursor"></span>';
    if (btnGenerate) btnGenerate.disabled = true;
    if (btnStop) btnStop.disabled = false;
    if (terminalTokens) terminalTokens.innerText = "0";
    if (terminalTime) terminalTime.innerText = "0s";
    generationStartTime = Date.now();

    setGraniteVisualStatus("working", "Granite Analizando...");

    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - generationStartTime) / 1000);
      if (terminalTime) terminalTime.innerText = `${elapsed}s`;
    }, 1000);

    if (terminalStatus) {
      terminalStatus.innerText = "GENERATING (CPU)...";
      terminalStatus.style.color = "var(--color-primary)";
    }

    const payload = {
      source_text: rawText,
      source_title: (sourceTitle && sourceTitle.value.trim()) || "",
      source_url: (urlInput && urlInput.value.trim()) || "",
      source_lang: state.scraperMetadata.source_lang,
      source_author: state.scraperMetadata.source_author,
      source_date: state.scraperMetadata.source_date,
      source_section: state.scraperMetadata.source_section,
      theme: state.selectedTheme,
      tone: (toneSelect && toneSelect.value) || "conversational",
      target_words: parseInt(wordCountTarget ? wordCountTarget.value : "1000") || 1000,
      custom_instructions: (customInstructions && customInstructions.value.trim()) || "",
      model: (modelSelect && modelSelect.value) || "granite3.3:8b",
      temperature: tempSlider ? parseFloat(tempSlider.value) : undefined,
      jurisdiction: (jurisdictionSelect && jurisdictionSelect.value) || "auto"
    };

    abortController = new AbortController();

    try {
      const response = await fetch("/api/generate-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });

      if (!response.ok) {
        let errDetail = response.statusText;
        try {
          const errData = await response.json();
          if (errData.detail) errDetail = errData.detail;
        } catch (_) {}
        throw new Error(`Error ${response.status}: ${errDetail}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let tokenCounter = 0;
      let sseBuffer = "";
      let renderPending = false;
      let lastSeoAuditTime = 0;

      function scheduleRender(isStreaming = true) {
        if (!renderPending) {
          renderPending = true;
          requestAnimationFrame(() => {
            renderArticle(state.currentRawMarkdown, isStreaming);
            renderPending = false;
          });
        }
      }

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        sseBuffer += decoder.decode(value, { stream: true });
        const events = sseBuffer.split("\n\n");
        // Preservar fragmento incompleto al final del buffer
        sseBuffer = events.pop() || "";

        for (const event of events) {
          if (!event.trim()) continue;

          const lines = event.split("\n");
          for (const rawLine of lines) {
            const line = rawLine.trim();
            if (line.startsWith("data: ")) {
              const dataStr = line.slice(6).trim();
              if (!dataStr) continue;

              try {
                const dataObj = JSON.parse(dataStr);
                if (dataObj.error) {
                  throw new Error(dataObj.error);
                }

                if (dataObj.token) {
                  state.currentRawMarkdown += dataObj.token;
                  tokenCounter++;
                  if (terminalTokens) terminalTokens.innerText = tokenCounter.toString();
                  
                  const elapsedSec = Math.max(1, (Date.now() - generationStartTime) / 1000);
                  const speed = (tokenCounter / elapsedSec).toFixed(1);
                  setGraniteVisualStatus("working", `Granite (${tokenCounter} tok · ${speed} t/s)`);

                  scheduleRender(true);

                  // Throttling de auditoría SEO: máximo 1 vez por segundo durante streaming
                  const now = Date.now();
                  if (now - lastSeoAuditTime > 1000) {
                    lastSeoAuditTime = now;
                    updateSeoAudit(state.currentRawMarkdown);
                  }
                }

                if (dataObj.done) {
                  break;
                }
              } catch (e) {
                if (e.message && e.message.includes("Ollama error")) {
                  throw e;
                }
                console.warn("Parse SSE chunk note:", e);
              }
            }
          }
        }
      }

      // Renderizado final y auditoría definitiva completa
      renderArticle(state.currentRawMarkdown, false);
      updateSeoAudit(state.currentRawMarkdown);

      // Si no hay imagen de cabecera (ingesta Docling o texto pegado), generar banner 16:9 procedural
      if (!state.currentBannerUrl) {
        try {
          const previewTitle = document.getElementById("previewTitle");
          const genTitle = (sourceTitle && sourceTitle.value) || (previewTitle && previewTitle.innerText) || "Artículo de Blog Optimizado";
          const bannerRes = await fetch("/api/generate-header-image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: genTitle,
              theme: state.selectedTheme || "cybersecurity"
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
      }

      // Auto-guardado RAG
      let ragSavedArticleMsg = "";
      try {
        const previewTitle = document.getElementById("previewTitle");
        const saveRes = await fetch("/api/save-generated-article", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: (sourceTitle && sourceTitle.value) || (previewTitle && previewTitle.innerText) || "Articulo Blog Granite",
            markdown_content: state.currentRawMarkdown,
            theme: state.selectedTheme,
            model: (modelSelect && modelSelect.value) || "granite3.3:8b",
            tone: (toneSelect && toneSelect.value) || "conversational",
            source_url: (urlInput && urlInput.value) || "",
            jurisdiction: (jurisdictionSelect && jurisdictionSelect.value) || "auto"
          })
        });
        if (saveRes.ok) {
          const saveData = await saveRes.json();
          ragSavedArticleMsg = ` · ARCHIVADO EN ${saveData.path}`;
          if (callbacks && callbacks.onArticleSaved) {
            callbacks.onArticleSaved();
          }
        }
      } catch (saveErr) {
        console.warn("Auto-save generated article note:", saveErr);
      }

      if (terminalStatus) {
        terminalStatus.innerText = `COMPLETED${ragSavedArticleMsg}`;
        terminalStatus.style.color = "var(--color-secondary)";
      }

      setGraniteVisualStatus("completed", "Artículo Completado");
      toast.success("¡Artículo generado y archivado con éxito en RAG/articulos/!");

    } catch (err) {
      if (err.name === "AbortError") {
        if (terminalStatus) {
          terminalStatus.innerText = "DETENIDO POR USUARIO";
          terminalStatus.style.color = "var(--color-warning)";
        }
        setGraniteVisualStatus("standby", "Generación Detenida");
        toast.info("Generación detenida.");
      } else {
        toast.error(`Error durante la generación: ${err.message}`);
        if (terminalStatus) {
          terminalStatus.innerText = "ERROR INFERENCIA";
          terminalStatus.style.color = "var(--color-error)";
        }
        setGraniteVisualStatus("error", "Error en Granite / Ollama");
        
        if (!state.currentRawMarkdown && articleView) {
          const isConnectionErr = err.message.includes("Ollama") || err.message.includes("connection") || err.message.includes("failed");
          articleView.innerHTML = `
            <div style="background: #fff5f5; border: 1px solid #fed7d7; border-left: 5px solid var(--color-error); padding: 22px; border-radius: 8px; margin: 20px 0; font-family: Arial, sans-serif;">
              <div style="display: flex; align-items: center; gap: 8px; color: var(--color-error); font-weight: 700; font-size: 1.1rem; margin-bottom: 10px;">
                <span class="material-symbols-outlined">cloud_off</span>
                <span>${isConnectionErr ? "Motor Local IBM Granite (Ollama) no disponible" : "Error en Inferencia"}</span>
              </div>
              <p style="color: #2d3748; font-size: 0.95rem; line-height: 1.6; margin-bottom: 12px;">
                ${isConnectionErr 
                  ? "La aplicación no pudo comunicarse con el servicio local de Ollama en <code>http://localhost:11434</code>. Por esta razón, el artículo no se generó ni se visualizó en la pantalla."
                  : `Detalle del fallo: <code>${err.message}</code>`}
              </p>
              <div style="background: #111111; color: #00FF41; padding: 12px 16px; border-radius: 6px; font-family: monospace; font-size: 0.85rem; margin-bottom: 12px; line-height: 1.5;">
                <span style="color: #888;"># Paso 1: Inicia el servicio de Ollama en tu terminal o PowerShell:</span><br>
                <strong>ollama serve</strong><br><br>
                <span style="color: #888;"># Paso 2: Asegúrate de tener descargado el modelo:</span><br>
                <strong>ollama pull granite3.3:8b</strong>
              </div>
              <p style="color: #718096; font-size: 0.85rem; margin: 0;">
                💡 Una vez iniciado Ollama, la píldora superior indicará <strong>'Ollama Local Activo'</strong> y podrás generar y copiar el artículo sin interrupciones.
              </p>
            </div>
          `;
          return;
        }
      }
      renderArticle(state.currentRawMarkdown, false);
    } finally {
      clearInterval(timerInterval);
      if (btnGenerate) btnGenerate.disabled = false;
      if (btnStop) btnStop.disabled = true;
    }
  }

  function stopGeneration() {
    if (abortController) {
      abortController.abort();
      setGraniteVisualStatus("standby", "Granite Standby");
    }
  }

  // Sincronización inteligente entre Perfil Jurídico y Jurisdicción
  if (toneSelect && jurisdictionSelect) {
    toneSelect.addEventListener("change", () => {
      const val = toneSelect.value;
      if (val.startsWith("abogado_ve") || val.startsWith("jull")) {
        if (jurisdictionSelect.value === "colombia") {
          jurisdictionSelect.value = "venezuela";
        }
      } else if (val.startsWith("abogado_co")) {
        if (jurisdictionSelect.value === "venezuela" || jurisdictionSelect.value === "auto") {
          jurisdictionSelect.value = "colombia";
        }
      }
    });

    jurisdictionSelect.addEventListener("change", () => {
      const jur = jurisdictionSelect.value;
      const currentTone = toneSelect.value;
      if (jur === "colombia" && (currentTone.startsWith("abogado_ve") || currentTone.startsWith("jull"))) {
        toneSelect.value = "abogado_co_litigante";
      } else if (jur === "venezuela" && currentTone.startsWith("abogado_co")) {
        toneSelect.value = "abogado_ve_litigante";
      }
    });
  }

  if (btnGenerate) btnGenerate.addEventListener("click", generateArticle);
  if (btnStop) btnStop.addEventListener("click", stopGeneration);

  return {
    generate: generateArticle,
    stop: stopGeneration
  };
}
