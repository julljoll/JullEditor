/**
 * Módulo de Notificaciones Toast Animadas (Elimina alertas bloqueantes alert())
 * Estilo USWDS / Cyber-Legal con auto-dismiss y animación fluida.
 */

class ToastManager {
  constructor() {
    this.container = null;
    this.initContainer();
  }

  initContainer() {
    if (document.getElementById("toastContainer")) {
      this.container = document.getElementById("toastContainer");
      return;
    }
    const container = document.createElement("div");
    container.id = "toastContainer";
    container.className = "toast-container";
    document.body.appendChild(container);
    this.container = container;
  }

  show(message, type = "info", duration = 4000) {
    if (!this.container) this.initContainer();

    const toast = document.createElement("div");
    toast.className = `toast-item toast-${type}`;

    const iconMap = {
      success: "check_circle",
      error: "error",
      warning: "warning",
      info: "info"
    };

    const iconName = iconMap[type] || "info";

    toast.innerHTML = `
      <span class="material-symbols-outlined toast-icon">${iconName}</span>
      <div class="toast-message">${message}</div>
      <button class="toast-close" title="Cerrar">&times;</button>
    `;

    const closeBtn = toast.querySelector(".toast-close");
    closeBtn.addEventListener("click", () => {
      this.dismiss(toast);
    });

    this.container.appendChild(toast);

    // Animación de entrada
    requestAnimationFrame(() => {
      toast.classList.add("toast-show");
    });

    // Auto-dismiss
    if (duration > 0) {
      setTimeout(() => {
        this.dismiss(toast);
      }, duration);
    }

    return toast;
  }

  dismiss(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.remove("toast-show");
    toast.classList.add("toast-hide");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }

  success(msg, dur) { return this.show(msg, "success", dur); }
  error(msg, dur) { return this.show(msg, "error", dur); }
  warning(msg, dur) { return this.show(msg, "warning", dur); }
  info(msg, dur) { return this.show(msg, "info", dur); }
}

export const toast = new ToastManager();
