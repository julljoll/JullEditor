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
  const editorialModeSelect = document.getElementById("editorialMode");
  const articleView = document.getElementById("articleView");
  const tempSlider = document.getElementById("tempSlider");

  const terminalTokens = document.getElementById("terminalTokens");
  const terminalTime = document.getElementById("terminalTime");
  const terminalStatus = document.getElementById("terminalStatus");

  let abortController = null;
  let generationStartTime = 0;
  let timerInterval = null;
  let isGenerating = false;

  async function generateArticle() {
    if (isGenerating) {
      toast.info("Ya hay una redacción en curso con IBM Granite...");
      return;
    }

    let rawText = sourceText ? sourceText.value.trim() : "";
    if (!rawText) {
      const urlVal = urlInput ? urlInput.value.trim() : "";
      if (urlVal) {
        toast.info("Extrayendo contenido de la URL antes de redactar...");
        const btnScrape = document.getElementById("btnScrape");
        if (btnScrape) {
          btnScrape.click();
          // Esperar hasta que sourceText se pueble
          await new Promise((resolve) => {
            const checkInt = setInterval(() => {
              if (sourceText && sourceText.value.trim().length > 20) {
                clearInterval(checkInt);
                resolve(true);
              }
            }, 300);
            setTimeout(() => {
              clearInterval(checkInt);
              resolve(false);
            }, 15000);
          });
          if (sourceText) {
            rawText = sourceText.value.trim();
          }
        }
      }
    }

    if (!rawText || rawText.length < 10) {
      toast.warning("Por favor ingresa o extrae un texto o notas base de al menos 10 caracteres para redactar el artículo.");
      return;
    }

    if (articleContainer) articleContainer.dataset.follow = "true";
    isGenerating = true;
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
      source_lang: (state.scraperMetadata && state.scraperMetadata.source_lang) || "",
      source_author: (state.scraperMetadata && state.scraperMetadata.source_author) || "",
      source_date: (state.scraperMetadata && state.scraperMetadata.source_date) || "",
      source_section: (state.scraperMetadata && state.scraperMetadata.source_section) || "",
      theme: state.selectedTheme || "cybersecurity",
      tone: (toneSelect && toneSelect.value) || "conversational",
      target_words: parseInt(wordCountTarget ? wordCountTarget.value : "1000") || 1000,
      custom_instructions: (customInstructions && customInstructions.value.trim()) || "",
      model: (modelSelect && modelSelect.value) || "granite3.3:8b",
      temperature: tempSlider ? parseFloat(tempSlider.value) : undefined,
      jurisdiction: (jurisdictionSelect && jurisdictionSelect.value) || "auto",
      editorial_mode: (editorialModeSelect && editorialModeSelect.value) || "magazine",
      sentencia_metadata: state.sentenciaMetadata || null
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
          if (errData.details && Array.isArray(errData.details)) {
            errDetail = errData.details.map(d => `${d.field}: ${d.message}`).join(" | ");
          } else if (errData.message) {
            errDetail = errData.message;
          } else if (errData.detail) {
            errDetail = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
          }
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
            jurisdiction: (jurisdictionSelect && jurisdictionSelect.value) || "auto",
            editorial_mode: (editorialModeSelect && editorialModeSelect.value) || "magazine",
            article_type: (toneSelect && toneSelect.value === "analista_tsj_revista") ? "sentencia_tsj" : "blog_post"
          })
        });
        if (saveRes.ok) {
          const saveData = await saveRes.json();
          const htmlMsg = saveData.html_filename ? ` (.md + .html)` : "";
          ragSavedArticleMsg = ` · ARCHIVADO EN ${saveData.path}${htmlMsg}`;
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
            <div class="alert-card alert-card--error">
              <div class="alert-card__title">
                <span class="material-symbols-outlined">cloud_off</span>
                <span>${isConnectionErr ? "Motor Local IBM Granite (Ollama) no disponible" : "Error en Inferencia"}</span>
              </div>
              <p style="color: var(--text-primary); font-size: 0.95rem; line-height: 1.6; margin-bottom: 12px;">
                ${isConnectionErr 
                  ? "La aplicación no pudo comunicarse con el servicio local de Ollama en <code>http://localhost:11434</code>. Por esta razón, el artículo no se generó ni se visualizó en la pantalla."
                  : `Detalle del fallo: <code>${err.message}</code>`}
              </p>
              <div class="alert-card__code">
                <span style="color: var(--text-muted);"># Paso 1: Inicia el servicio de Ollama en tu terminal o PowerShell:</span><br>
                <strong>ollama serve</strong><br><br>
                <span style="color: var(--text-muted);"># Paso 2: Asegúrate de tener descargado el modelo:</span><br>
                <strong>ollama pull granite3.3:8b</strong>
              </div>
              <p class="alert-card__note">
                💡 Una vez iniciado Ollama, la píldora superior indicará <strong>'Ollama Local Activo'</strong> y podrás generar y copiar el artículo sin interrupciones.
              </p>
            </div>
          `;
          return;
        }
      }
      renderArticle(state.currentRawMarkdown, false);
    } finally {
      isGenerating = false;
      clearInterval(timerInterval);
      if (btnGenerate) btnGenerate.disabled = false;
      if (btnStop) btnStop.disabled = true;
    }
  }

  function stopGeneration() {
    if (abortController) {
      abortController.abort();
    }
    fetch("/api/stop-generation", { method: "POST" }).catch(() => {});
    setGraniteVisualStatus("standby", "Granite Standby");
    isGenerating = false;
  }

  window.addEventListener("beforeunload", () => {
    if (isGenerating) {
      navigator.sendBeacon("/api/stop-generation");
    }
  });

  // Panel de Ficha Técnica TSJ
  function populateTsjFichaPanel(metadata) {
    if (!metadata) return;
    state.sentenciaMetadata = metadata;

    const elContainer = document.getElementById("tsjDetectionContainer");
    const elSala = document.getElementById("tsjFichaSala");
    const elExp = document.getElementById("tsjFichaExpediente");
    const elNum = document.getElementById("tsjFichaNumero");
    const elPon = document.getElementById("tsjFichaPonente");
    const elFecha = document.getElementById("tsjFichaFecha");
    const elPartes = document.getElementById("tsjFichaPartes");
    const elMat = document.getElementById("tsjFichaMateria");
    const elDec = document.getElementById("tsjFichaDecision");
    const elNormas = document.getElementById("tsjFichaNormas");

    if (elSala) elSala.innerText = metadata.sala || "Tribunal Supremo de Justicia";
    if (elExp) elExp.innerText = metadata.expediente || "S/E";
    if (elNum) elNum.innerText = metadata.numero_sentencia ? `Nº ${metadata.numero_sentencia}` : "S/N";
    if (elPon) elPon.innerText = metadata.ponente || "No especificado";
    if (elFecha) elFecha.innerText = metadata.fecha_decision || "Fecha en autos";

    const partesStr = [
      metadata.partes?.recurrente_o_demandante ? `Rec: ${metadata.partes.recurrente_o_demandante}` : "",
      metadata.partes?.recurrido_o_demandado ? `Recdo: ${metadata.partes.recurrido_o_demandado}` : ""
    ].filter(Boolean).join(" vs. ") || "Partes en autos";
    if (elPartes) elPartes.innerText = partesStr;

    const matStr = [metadata.materia, metadata.delito_asunto].filter(Boolean).join(" · ") || "Materia Jurisprudencial";
    if (elMat) elMat.innerText = matStr;

    if (elDec) elDec.innerText = metadata.decision_tipo || "Sentencia de Fondo";

    if (elNormas) {
      if (metadata.leyes_citadas && metadata.leyes_citadas.length > 0) {
        elNormas.innerText = metadata.leyes_citadas.join(" | ");
      } else {
        elNormas.innerText = "Normas citadas en el texto judicial";
      }
    }

    if (elContainer) {
      elContainer.style.display = "block";
    }
  }

  let tsjDetectDebounce = null;
  async function detectAndConfigureTsj(text, filename = "", force = false) {
    if (!text || text.length < 40) {
      const elContainer = document.getElementById("tsjDetectionContainer");
      if (elContainer && toneSelect && toneSelect.value !== "analista_tsj_revista") {
        elContainer.style.display = "none";
      }
      return;
    }

    const lower = text.toLowerCase();
    const markers = [
      "tribunal supremo de justicia",
      "sala de casación",
      "sala constitucional",
      "recurso de casación",
      "recurso extraordinario de casación",
      "magistrado ponente",
      "magistrada ponente",
      "código orgánico procesal penal",
      "código de procedimiento civil"
    ];
    const matchCount = markers.filter(m => lower.includes(m)).length;
    const isSentencia = force || matchCount >= 2 || (filename && /scp-|scc-|tsj/i.test(filename));

    if (!isSentencia) {
      const elContainer = document.getElementById("tsjDetectionContainer");
      if (elContainer && toneSelect && toneSelect.value !== "analista_tsj_revista") {
        elContainer.style.display = "none";
      }
      return;
    }

    // 1. Configuración automática de parámetros
    if (toneSelect && toneSelect.value !== "analista_tsj_revista") {
      toneSelect.value = "analista_tsj_revista";
      toneSelect.dispatchEvent(new Event("change"));
    }
    if (jurisdictionSelect && jurisdictionSelect.value !== "venezuela") {
      jurisdictionSelect.value = "venezuela";
      jurisdictionSelect.dispatchEvent(new Event("change"));
    }
    if (tempSlider) {
      tempSlider.value = "0.15";
      const tempValueLabel = document.getElementById("tempValueLabel");
      if (tempValueLabel) {
        tempValueLabel.innerText = "0.15 (Rigor TSJ Sentencias)";
        tempValueLabel.style.color = "var(--color-secondary)";
      }
    }

    // Activar pill forense & TSJ si existe
    const forensicPill = document.querySelector('.theme-pill[data-theme="forensic_law"]');
    if (forensicPill && !forensicPill.classList.contains("active")) {
      forensicPill.click();
    }

    // 2. Extraer metadatos vía API
    try {
      const res = await fetch("/api/extract-sentencia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: text.slice(0, 30000), filename: filename || "" })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success" && data.metadata) {
          populateTsjFichaPanel(data.metadata);
          toast.success("🏛️ Sentencia TSJ detectada: Perfil de análisis y Ficha Técnica activados");
        }
      }
    } catch (e) {
      console.warn("Aviso llamando /api/extract-sentencia:", e);
    }
  }

  // Toggle colapsable de la Ficha Técnica
  const btnToggleTsjFicha = document.getElementById("btnToggleTsjFicha");
  const tsjFichaPanel = document.getElementById("tsjFichaPanel");
  const tsjFichaToggleText = document.getElementById("tsjFichaToggleText");
  const tsjFichaToggleIcon = document.getElementById("tsjFichaToggleIcon");

  if (btnToggleTsjFicha && tsjFichaPanel) {
    btnToggleTsjFicha.addEventListener("click", () => {
      const isVisible = tsjFichaPanel.style.display !== "none";
      tsjFichaPanel.style.display = isVisible ? "none" : "block";
      if (tsjFichaToggleText) tsjFichaToggleText.innerText = isVisible ? "Ver Ficha Técnica" : "Ocultar Ficha";
      if (tsjFichaToggleIcon) tsjFichaToggleIcon.innerText = isVisible ? "expand_more" : "expand_less";
    });
  }

  // Escuchar texto fuente para auto-detección de sentencias TSJ
  if (sourceText) {
    sourceText.addEventListener("input", () => {
      clearTimeout(tsjDetectDebounce);
      tsjDetectDebounce = setTimeout(() => {
        detectAndConfigureTsj(sourceText.value, sourceTitle ? sourceTitle.value : "", false);
      }, 500);
    });
  }

  // Sincronización inteligente entre Perfil Jurídico y Jurisdicción
  if (toneSelect && jurisdictionSelect) {
    toneSelect.addEventListener("change", () => {
      const val = toneSelect.value;
      if (val === "analista_tsj_revista") {
        if (jurisdictionSelect) jurisdictionSelect.value = "venezuela";
        if (tempSlider) {
          tempSlider.value = "0.15";
          const tempValueLabel = document.getElementById("tempValueLabel");
          if (tempValueLabel) {
            tempValueLabel.innerText = "0.15 (Rigor TSJ Sentencias)";
            tempValueLabel.style.color = "var(--color-secondary)";
          }
        }
        if (sourceText && sourceText.value.trim().length > 30) {
          detectAndConfigureTsj(sourceText.value, sourceTitle ? sourceTitle.value : "", true);
        }
      } else if (val.startsWith("abogado_ve") || val.startsWith("jull")) {
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
      if (jur === "colombia" && (currentTone.startsWith("abogado_ve") || currentTone.startsWith("jull") || currentTone === "analista_tsj_revista")) {
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
    stop: stopGeneration,
    detectAndConfigureTsj: detectAndConfigureTsj
  };
}
