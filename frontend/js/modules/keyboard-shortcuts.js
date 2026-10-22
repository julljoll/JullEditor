/**
 * Módulo de Atajos de Teclado para Power Users (Ctrl+Enter, Ctrl+Shift+C, Escape, etc.)
 */

import { toast } from "./toast-notifications.js";

export function initKeyboardShortcuts(callbacks) {
  document.addEventListener("keydown", (e) => {
    // Si está en un textarea o input y no es un atajo con modificador, no intervenir
    const isEditing = ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName);

    // Ctrl+Enter / Cmd+Enter: Generar artículo
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (callbacks && callbacks.onGenerate) {
        callbacks.onGenerate();
      }
      return;
    }

    // Escape: Cerrar modales o detener generación
    if (e.key === "Escape") {
      const sitejetModal = document.getElementById("sitejetSeoKitModal");
      if (sitejetModal && sitejetModal.classList.contains("modal-show")) {
        sitejetModal.classList.remove("modal-show");
        return;
      }
      const shortcutsModal = document.getElementById("shortcutsModal");
      if (shortcutsModal && shortcutsModal.classList.contains("modal-show")) {
        shortcutsModal.classList.remove("modal-show");
        return;
      }
      if (callbacks && callbacks.onStop) {
        callbacks.onStop();
      }
      return;
    }

    // Atajos globales con Ctrl+Shift
    if ((e.ctrlKey || e.metaKey) && e.shiftKey) {
      if (e.key === "S" || e.key === "s") {
        e.preventDefault();
        const btnCopySj = document.getElementById("btnCopySitejet");
        if (btnCopySj) btnCopySj.click();
        return;
      }
      if (e.key === "K" || e.key === "k") {
        e.preventDefault();
        const btnSjKit = document.getElementById("btnSitejetKit");
        if (btnSjKit) btnSjKit.click();
        return;
      }
      if (e.key === "C" || e.key === "c") {
        e.preventDefault();
        const btnCopyWp = document.getElementById("btnCopyWordPress");
        if (btnCopyWp) btnCopyWp.click();
        return;
      }
      if (e.key === "H" || e.key === "h") {
        e.preventDefault();
        const btnCopyHtml = document.getElementById("btnCopyRawHtml");
        if (btnCopyHtml) btnCopyHtml.click();
        return;
      }
      if (e.key === "M" || e.key === "m") {
        e.preventDefault();
        const btnCopy = document.getElementById("btnCopy");
        if (btnCopy) btnCopy.click();
        return;
      }
      if (e.key === "P" || e.key === "p") {
        e.preventDefault();
        window.print();
        return;
      }
    }

    // Tecla '?' cuando no se está escribiendo para mostrar ayuda de atajos
    if (e.key === "?" && !isEditing) {
      e.preventDefault();
      showShortcutsModal();
    }
  });

  function showShortcutsModal() {
    let modal = document.getElementById("shortcutsModal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "shortcutsModal";
      modal.className = "shortcuts-modal-overlay";
      modal.innerHTML = `
        <div class="shortcuts-modal-card">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h3 style="margin:0; font-size:1.1rem; color:var(--color-primary);">⌨️ Atajos de Teclado</h3>
            <button class="btn btn-sm btn-outline" id="btnCloseShortcutsModal">&times;</button>
          </div>
          <table style="width:100%; font-size:0.85rem;">
            <tr><td><kbd>Ctrl</kbd> + <kbd>Enter</kbd></td><td>Redactar Artículo</td></tr>
            <tr><td><kbd>Escape</kbd></td><td>Detener Inferencia</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>C</kbd></td><td>Copiar para WordPress (Estilos Inline)</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>H</kbd></td><td>Copiar Código HTML Puro</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd></td><td>Copiar para Sitejet Builder</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>K</kbd></td><td>Abrir Kit SEO Sitejet</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>M</kbd></td><td>Copiar Markdown (.MD)</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>1</kbd> / <kbd>2</kbd> / <kbd>3</kbd></td><td>Pestaña Revista / Markdown / WordPress</td></tr>
            <tr><td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>F</kbd></td><td>Seguir generación (auto-scroll)</td></tr>
            <tr><td><kbd>?</kbd></td><td>Mostrar esta ayuda</td></tr>
          </table>
        </div>
      `;
      document.body.appendChild(modal);

      modal.querySelector("#btnCloseShortcutsModal").addEventListener("click", () => {
        modal.classList.remove("modal-show");
      });
      modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.remove("modal-show");
      });
    }

    modal.classList.toggle("modal-show");
  }
}
