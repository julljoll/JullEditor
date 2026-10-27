/**
 * Preload de JullEditor Desktop — puente IPC seguro.
 * Expone al splash/renderer solo lo necesario (contextIsolation activo,
 * nodeIntegration desactivado).
 */
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jullDesktop', {
  /** Info del backend en arranque: { port, dev } */
  getBootstrapInfo: () => ipcRenderer.invoke('get-bootstrap-info'),

  /** Suscripción a estados estructurados del bootstrap (JSON emitido por run.py) */
  onStatus: (cb) => {
    const listener = (_e, status) => cb(status);
    ipcRenderer.on('bootstrap-status', listener);
    return () => ipcRenderer.removeListener('bootstrap-status', listener);
  },

  /** Suscripción al log en bruto (stdout/stderr del sidecar Python) */
  onLog: (cb) => {
    const listener = (_e, line) => cb(line);
    ipcRenderer.on('bootstrap-log', listener);
    return () => ipcRenderer.removeListener('bootstrap-log', listener);
  },

  /** Reintentar el arranque del motor tras un fallo */
  retry: () => ipcRenderer.send('retry-boot'),
});
