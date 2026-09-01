/**
 * Módulo de Health Check y Estado del Sistema Ollama / IBM Granite
 */

import { toast } from "./toast-notifications.js";

export function setGraniteVisualStatus(state, message) {
  const graniteActivityBtn = document.getElementById("graniteActivityBtn");
  const graniteActivityIcon = document.getElementById("graniteActivityIcon");
  const graniteActivityText = document.getElementById("graniteActivityText");

  if (!graniteActivityBtn) return;
  graniteActivityBtn.className = `btn-granite-status ${state}`;

  if (state === "working") {
    if (graniteActivityIcon) graniteActivityIcon.innerText = "autorenew";
    if (graniteActivityText) graniteActivityText.innerText = message || "Granite Trabajando...";
  } else if (state === "error") {
    if (graniteActivityIcon) graniteActivityIcon.innerText = "error";
    if (graniteActivityText) graniteActivityText.innerText = message || "Error en Granite";
  } else if (state === "completed") {
    if (graniteActivityIcon) graniteActivityIcon.innerText = "check_circle";
    if (graniteActivityText) graniteActivityText.innerText = message || "Redacción Lista";
  } else {
    if (graniteActivityIcon) graniteActivityIcon.innerText = "psychology";
    if (graniteActivityText) graniteActivityText.innerText = message || "Granite Standby";
  }
}

export async function checkSystemHealth() {
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const terminalStatus = document.getElementById("terminalStatus");
  const modelSelect = document.getElementById("modelSelect");
  const terminalModel = document.getElementById("terminalModel");

  if (statusText) statusText.innerText = "Verificando Ollama...";

  try {
    const res = await fetch("/api/health");
    const data = await res.json();

    if (data.status === "online") {
      if (statusDot) statusDot.className = "status-dot online";
      if (statusText) statusText.innerText = "Ollama Local Activo";
      if (terminalStatus) {
        terminalStatus.innerText = "ONLINE (CPU)";
        terminalStatus.style.color = "var(--color-secondary)";
      }
      setGraniteVisualStatus("standby", "Granite Listo");

      if (data.models && data.models.length > 0 && modelSelect) {
        modelSelect.innerHTML = "";
        data.models.forEach((m) => {
          const opt = document.createElement("option");
          opt.value = m;
          opt.innerText = m;
          if (m.includes("granite")) opt.selected = true;
          modelSelect.appendChild(opt);
        });
        if (terminalModel) terminalModel.innerText = modelSelect.value || "Granite Local";
      }
    } else {
      throw new Error(data.error || "Ollama desconectado");
    }
  } catch (err) {
    if (statusDot) statusDot.className = "status-dot offline";
    if (statusText) statusText.innerText = "Ollama Inactivo";
    if (terminalStatus) {
      terminalStatus.innerText = "OFFLINE";
      terminalStatus.style.color = "var(--color-error)";
    }
    setGraniteVisualStatus("error", "Ollama Inactivo");
    console.warn("Health check error:", err);
  }
}
