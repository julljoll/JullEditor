/**
 * Módulo de Flujo Guiado de Creación (Stepper, validaciones y sincronizaciones)
 * - Control de acordeón de pasos (1 a 4)
 * - Validación en vivo de palabras en fuente (umbral 50 palabras)
 * - Control segmentado de Modo Editorial (Revista vs Clásico) sincronizado con select oculto
 * - Gradiente dinámico en el slider de temperatura (--range-pct)
 */

export function initCreationFlow(state) {
  const sourceText = document.getElementById("sourceText");
  const sourceWordCount = document.getElementById("sourceWordCount");
  const btnGenerate = document.getElementById("btnGenerate");
  const editorialMode = document.getElementById("editorialMode");
  const tempSlider = document.getElementById("tempSlider");
  const tempValueLabel = document.getElementById("tempValueLabel");

  // 1. Acordeón de pasos (step-header buttons)
  const stepHeaders = document.querySelectorAll(".step-header-btn");
  stepHeaders.forEach((btn) => {
    btn.addEventListener("click", () => {
      const step = btn.closest(".step");
      if (!step) return;
      const content = step.querySelector(".step-body");
      if (!content) return;

      const isExpanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", isExpanded ? "false" : "true");
      step.classList.toggle("collapsed", isExpanded);
    });
  });

  // 2. Validación de Fuente y conteo de palabras en vivo
  function updateSourceValidation() {
    const text = sourceText ? sourceText.value.trim() : "";
    const words = text ? text.split(/\s+/).filter(Boolean).length : 0;

    const step1Check = document.getElementById("step1Check");
    if (words >= 1) {
      if (sourceWordCount) {
        sourceWordCount.textContent = words >= 50
          ? `${words.toLocaleString()} palabras · Listo ✓`
          : `${words} palabra${words > 1 ? "s" : ""}`;
        sourceWordCount.classList.toggle("text-success", words >= 50);
        sourceWordCount.classList.toggle("text-muted", words < 50);
      }
      if (btnGenerate) {
        btnGenerate.dataset.blockedBySource = "false";
        btnGenerate.removeAttribute("title");
      }
      if (step1Check) {
        step1Check.textContent = "check_circle";
        step1Check.classList.add("step-done");
      }
    } else {
      if (sourceWordCount) {
        sourceWordCount.textContent = "0 palabras";
        sourceWordCount.classList.remove("text-success");
        sourceWordCount.classList.add("text-muted");
      }
      if (btnGenerate) {
        btnGenerate.dataset.blockedBySource = "false";
        btnGenerate.removeAttribute("title");
      }
      if (step1Check) {
        step1Check.textContent = "circle";
        step1Check.classList.remove("step-done");
      }
    }
  }

  if (sourceText) {
    sourceText.addEventListener("input", updateSourceValidation);
    // Intervalo de seguridad por si se llena programáticamente sin evento
    const checkInterval = setInterval(() => {
      const words = sourceText.value.trim().split(/\s+/).filter(Boolean).length;
      if (words >= 50) {
        updateSourceValidation();
      }
    }, 800);
    // Ejecución inicial
    updateSourceValidation();
  }

  // 3. Control segmentado visual de Modo Editorial (Revista vs Clásico)
  const segmentMagazine = document.getElementById("segmentModeMagazine");
  const segmentClassic = document.getElementById("segmentModeClassic");

  function syncEditorialSegmentUI(currentVal) {
    if (segmentMagazine && segmentClassic) {
      if (currentVal === "magazine") {
        segmentMagazine.classList.add("active");
        segmentMagazine.setAttribute("aria-checked", "true");
        segmentClassic.classList.remove("active");
        segmentClassic.setAttribute("aria-checked", "false");
      } else {
        segmentClassic.classList.add("active");
        segmentClassic.setAttribute("aria-checked", "true");
        segmentMagazine.classList.remove("active");
        segmentMagazine.setAttribute("aria-checked", "false");
      }
    }
  }

  if (segmentMagazine && editorialMode) {
    segmentMagazine.addEventListener("click", () => {
      editorialMode.value = "magazine";
      editorialMode.dispatchEvent(new Event("change"));
      syncEditorialSegmentUI("magazine");
    });
  }

  if (segmentClassic && editorialMode) {
    segmentClassic.addEventListener("click", () => {
      editorialMode.value = "classic";
      editorialMode.dispatchEvent(new Event("change"));
      syncEditorialSegmentUI("classic");
    });
  }

  if (editorialMode) {
    editorialMode.addEventListener("change", () => {
      syncEditorialSegmentUI(editorialMode.value);
    });
    syncEditorialSegmentUI(editorialMode.value || "magazine");
  }

  // 4. Relleno dorado del slider de temperatura
  function updateSliderFill() {
    if (!tempSlider) return;
    const min = parseFloat(tempSlider.min) || 0;
    const max = parseFloat(tempSlider.max) || 1;
    const val = parseFloat(tempSlider.value) || 0.2;
    const pct = ((val - min) / (max - min)) * 100;
    tempSlider.style.setProperty("--range-pct", `${pct}%`);
  }

  if (tempSlider) {
    tempSlider.addEventListener("input", updateSliderFill);
    updateSliderFill();
  }
}
