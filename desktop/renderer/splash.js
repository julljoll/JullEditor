/**
 * Splash renderer — refleja el progreso del sidecar Python recibido por IPC.
 * Los estados provienen de run.py --json-status (STATUS_JSON:{...} en stdout).
 */
(function () {
  const api = window.jullDesktop;
  if (!api) return;

  const stepsEl = Array.from(document.querySelectorAll('#steps li'));
  const logEl = document.getElementById('log');
  const statusText = document.getElementById('status-text');

  // Orden canónico de pasos y textos del pie de página
  const STATE_ORDER = ['launched', 'hardware', 'installing_deps', 'installing_ollama', 'pulling_model', 'ready'];
  const FOOTER_TEXT = {
    launched: 'Iniciando motor Python…',
    bootstrapping: 'Preparando entorno…',
    hardware: 'Analizando tu computadora…',
    installing_deps: 'Instalando dependencias Python (pip)…',
    installing_ollama: 'Instalando Ollama…',
    pulling_model: 'Descargando modelo Granite (puede tardar según tu conexión)…',
    bootstrap_done: 'Arrancando servidor web…',
    starting_server: 'Arrancando servidor FastAPI…',
    ready: '¡Listo! Abriendo JullEditor…',
  };

  let lastIdx = -1;

  function stepIndexFor(state) {
    // Mapea estados crudos al índice del <li> correspondiente
    switch (state) {
      case 'launched': return 0;
      case 'bootstrapping':
      case 'hardware': return 1;
      case 'installing_deps': return 2;
      case 'installing_ollama': return 3;
      case 'pulling_model': return 4;
      case 'bootstrap_done':
      case 'starting_server':
      case 'ready': return 5;
      default: return -1;
    }
  }

  function markProgress(state) {
    const idx = stepIndexFor(state);
    if (idx < 0) return;
    if (idx > lastIdx) lastIdx = idx;
    stepsEl.forEach((li, i) => {
      li.classList.toggle('done', i < lastIdx);
      li.classList.toggle('active', i === lastIdx && state !== 'ready');
      if (state === 'ready') li.classList.add('done');
    });
    statusText.textContent = FOOTER_TEXT[state] || 'Iniciando…';
  }

  function appendLog(line) {
    // Limitar tamaño del buffer visible
    const MAX_LINES = 400;
    logEl.textContent += line + '\n';
    const lines = logEl.textContent.split('\n');
    if (lines.length > MAX_LINES) logEl.textContent = lines.slice(-MAX_LINES).join('\n');
    logEl.scrollTop = logEl.scrollHeight;
  }

  api.onStatus((status) => {
    if (status && status.state) {
      markProgress(status.state);
      if (status.model) appendLog(`[modelo sugerido] ${status.model} (RAM ${status.ram_gb} GB)`);
    }
  });

  api.onLog((line) => appendLog(line));
})();
