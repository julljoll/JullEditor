/**
 * Módulo de Ingesta y Procesamiento de Archivos Docling (.md, .json, .txt)
 * Soporta Drag & Drop, múltiples archivos simultáneos y persistencia automática en RAG/inputs/.
 */

import { toast } from "./toast-notifications.js";

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve({ name: file.name, text: e.target.result || "" });
    reader.onerror = (err) => reject(err);
    reader.readAsText(file, "UTF-8");
  });
}

export function initDoclingHandler(callbacks) {
  const fileDoclingInput = document.getElementById("fileDoclingInput");
  const doclingDropzone = document.getElementById("doclingDropzone");
  const doclingProgress = document.getElementById("doclingProgress");
  const doclingProgressBar = document.getElementById("doclingProgressBar");
  const doclingProgressText = document.getElementById("doclingProgressText");
  const doclingProgressPercent = document.getElementById("doclingProgressPercent");
  const doclingFileChip = document.getElementById("doclingFileChip");
  const doclingFileName = document.getElementById("doclingFileName");
  const doclingFileMeta = document.getElementById("doclingFileMeta");
  const btnRemoveDoclingFile = document.getElementById("btnRemoveDoclingFile");
  const sourceTitle = document.getElementById("sourceTitle");
  const sourceText = document.getElementById("sourceText");
  const terminalStatus = document.getElementById("terminalStatus");

  function updateUploadProgress(percent, message) {
    if (doclingProgressBar) doclingProgressBar.style.width = `${percent}%`;
    if (doclingProgressPercent) doclingProgressPercent.innerText = `${percent}%`;
    if (doclingProgressText && message) {
      doclingProgressText.innerHTML = `<span class="spinner-border spinner-border-sm text-success me-2" role="status"></span> ${message}`;
    }
  }

  async function processDoclingFiles(fileList) {
    if (!fileList || fileList.length === 0) return;

    const files = Array.from(fileList);

    doclingDropzone.style.display = "none";
    doclingFileChip.style.display = "none";
    doclingProgress.style.display = "block";
    updateUploadProgress(15, `Leyendo ${files.length} archivo(s)...`);

    if (terminalStatus) {
      terminalStatus.innerText = `PROCESANDO ${files.length} ARCHIVO(S)...`;
      terminalStatus.style.color = "var(--color-primary)";
    }

    try {
      const readResults = await Promise.all(files.map(f => readFileAsText(f)));
      updateUploadProgress(45, "Extrayendo estructura Markdown y metadatos...");

      let primaryTitle = "";
      let primaryText = "";
      let finalTheme = "cybersecurity";
      let combinedWordCount = 0;
      let savedPaths = [];
      let fileNames = [];

      const mdFile = readResults.find(r => /\.(md|markdown|txt)$/i.test(r.name));
      const jsonFile = readResults.find(r => /\.json$/i.test(r.name));
      const otherFiles = readResults.filter(r => r !== mdFile && r !== jsonFile);

      let fileIndex = 0;
      for (const item of readResults) {
        if (!item.text.trim()) continue;
        fileNames.push(item.name);
        fileIndex++;

        updateUploadProgress(50 + Math.round((fileIndex / readResults.length) * 35), `Guardando ${item.name} en RAG/inputs/...`);

        try {
          const res = await fetch("/api/parse-docling-md", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              content: item.text,
              filename: item.name
            })
          });
          if (res.ok) {
            const data = await res.json();
            if (data.title && !primaryTitle) primaryTitle = data.title;
            if (data.detected_theme) finalTheme = data.detected_theme;
            if (data.rag_input && data.rag_input.path) {
              savedPaths.push(data.rag_input.path);
            }
          }
        } catch (apiErr) {
          console.warn(`Error procesando ${item.name}:`, apiErr);
        }
      }

      if (mdFile && mdFile.text.trim()) {
        primaryText = mdFile.text.trim();
        if (!primaryTitle) {
          const h1Match = primaryText.match(/^#\s+(.+)$/m);
          if (h1Match) primaryTitle = h1Match[1].replace(/[\*\_\[\]\#]/g, "").trim();
        }
      }

      if (jsonFile && jsonFile.text.trim()) {
        try {
          const jsonObj = JSON.parse(jsonFile.text);
          const jsonTitle = jsonObj.title || jsonObj.name || jsonObj.document_title || "";
          if (jsonTitle && !primaryTitle) primaryTitle = jsonTitle;
          if (!primaryText) {
            primaryText = jsonObj.markdown || jsonObj.text || jsonObj.content || jsonObj.body || jsonObj.main_text || (jsonObj.nodes ? jsonObj.nodes.map(n => n.text || "").join("\n\n") : JSON.stringify(jsonObj, null, 2));
          }
        } catch (jErr) {
          console.warn("Error parseando JSON local:", jErr);
        }
      }

      if (!primaryText && otherFiles.length > 0) {
        primaryText = otherFiles.map(o => o.text).join("\n\n");
      }

      if (!primaryTitle) {
        primaryTitle = fileNames.length > 0 ? fileNames[0].replace(/\.(md|markdown|txt|json)$/i, "").replace(/[_-]/g, " ") : "Documento Docling";
      }

      combinedWordCount = primaryText.split(/\s+/).filter(Boolean).length;

      if (sourceTitle) sourceTitle.value = primaryTitle;
      if (sourceText) sourceText.value = primaryText;

      if (callbacks && callbacks.onThemeDetected) {
        callbacks.onThemeDetected(finalTheme);
      }

      updateUploadProgress(100, `¡${fileNames.length} archivo(s) importados con éxito!`);

      setTimeout(() => {
        doclingProgress.style.display = "none";
        if (doclingFileName) doclingFileName.innerText = fileNames.join(" + ");
        const ragSummary = savedPaths.length > 0 ? `${savedPaths.length} en RAG/inputs/` : `Guardado en RAG`;
        if (doclingFileMeta) doclingFileMeta.innerText = `${combinedWordCount.toLocaleString()} palabras · ${ragSummary}`;
        doclingFileChip.style.display = "flex";

        if (terminalStatus) {
          terminalStatus.innerText = `DOCLING EN RAG (${fileNames.length} archivos · ${combinedWordCount} pal.)`;
          terminalStatus.style.color = "var(--color-secondary)";
        }
        toast.success(`Se importaron ${fileNames.length} archivo(s) correctamente.`);
      }, 350);

    } catch (err) {
      doclingProgress.style.display = "none";
      doclingDropzone.style.display = "block";
      toast.error(`Error procesando archivos: ${err.message}`);
      if (terminalStatus) {
        terminalStatus.innerText = "ERROR CARGANDO ARCHIVOS";
        terminalStatus.style.color = "var(--color-error)";
      }
    }
  }

  // Event Listeners
  if (fileDoclingInput) {
    fileDoclingInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files.length > 0) {
        processDoclingFiles(e.target.files);
      }
    });
  }

  if (doclingDropzone) {
    doclingDropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        fileDoclingInput.click();
      }
    });

    doclingDropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      doclingDropzone.classList.add("dragover");
    });
    doclingDropzone.addEventListener("dragleave", () => {
      doclingDropzone.classList.remove("dragover");
    });
    doclingDropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      doclingDropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        processDoclingFiles(e.dataTransfer.files);
      }
    });
  }

  if (btnRemoveDoclingFile) {
    btnRemoveDoclingFile.addEventListener("click", () => {
      if (fileDoclingInput) fileDoclingInput.value = "";
      if (doclingProgressBar) doclingProgressBar.style.width = "0%";
      if (doclingProgressPercent) doclingProgressPercent.innerText = "0%";
      doclingProgress.style.display = "none";
      doclingFileChip.style.display = "none";
      doclingDropzone.style.display = "block";
      if (sourceTitle) sourceTitle.value = "";
      if (sourceText) sourceText.value = "";
      if (terminalStatus) {
        terminalStatus.innerText = "STANDBY";
        terminalStatus.style.color = "var(--text-secondary)";
      }
      toast.info("Archivos removidos.");
    });
  }
}
