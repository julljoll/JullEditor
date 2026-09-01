/**
 * Módulo Generador de Artículos con Streaming SSE, Medidor de Velocidad y ETA
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
      temperature: tempSlider ? parseFloat(tempSlider.value) : undefined
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
        throw new Error(`Error en servidor: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let tokenCounter = 0;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkText = decoder.decode(value, { stream: true });
        const lines = chunkText.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.replace("data: ", "").trim();
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

                renderArticle(state.currentRawMarkdown, true);
                updateSeoAudit(state.currentRawMarkdown);
              }

              if (dataObj.done) {
                break;
              }
            } catch (e) {
              console.warn("Parse SSE chunk note:", e);
            }
          }
        }
      }

      renderArticle(state.currentRawMarkdown, false);
      updateSeoAudit(state.currentRawMarkdown);

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
            source_url: (urlInput && urlInput.value) || ""
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

  if (btnGenerate) btnGenerate.addEventListener("click", generateArticle);
  if (btnStop) btnStop.addEventListener("click", stopGeneration);

  return {
    generate: generateArticle,
    stop: stopGeneration
  };
}
