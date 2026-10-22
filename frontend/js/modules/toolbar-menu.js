/**
 * Módulo de Menú Accesible para la Toolbar (Botón Split Copiar ▾)
 * Proporciona apertura/cierre, navegación con teclado (flechas, Esc), clic fuera y retorno de foco.
 */

export function initToolbarMenu() {
  const trigger = document.getElementById("btnCopySplitChevron");
  const menu = document.getElementById("dropdownMenuCopy");

  if (!trigger || !menu) return;

  function openMenu() {
    menu.classList.add("open");
    trigger.setAttribute("aria-expanded", "true");
    const firstItem = menu.querySelector('[role="menuitem"]:not([disabled])');
    if (firstItem) firstItem.focus();
  }

  function closeMenu(restoreFocus = true) {
    if (!menu.classList.contains("open")) return;
    menu.classList.remove("open");
    trigger.setAttribute("aria-expanded", "false");
    if (restoreFocus) trigger.focus();
  }

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    const isOpen = menu.classList.contains("open");
    if (isOpen) {
      closeMenu(true);
    } else {
      openMenu();
    }
  });

  // Cerrar al hacer clic fuera
  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target) && !trigger.contains(e.target)) {
      closeMenu(false);
    }
  });

  // Cerrar al pulsar un elemento del menú
  menu.addEventListener("click", (e) => {
    const item = e.target.closest('[role="menuitem"]');
    if (item) {
      closeMenu(true);
    }
  });

  // Navegación por teclado dentro del menú
  menu.addEventListener("keydown", (e) => {
    const items = Array.from(menu.querySelectorAll('[role="menuitem"]:not([disabled])'));
    const currentIndex = items.indexOf(document.activeElement);

    if (e.key === "Escape") {
      e.preventDefault();
      closeMenu(true);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % items.length;
      items[nextIndex]?.focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + items.length) % items.length;
      items[prevIndex]?.focus();
    } else if (e.key === "Tab") {
      closeMenu(false);
    }
  });

  trigger.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openMenu();
    }
  });
}
