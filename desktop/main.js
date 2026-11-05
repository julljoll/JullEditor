/**
 * JullEditor Desktop — Proceso principal de Electron.
 *
 * Arquitectura: Electron actúa como shell que lanza el backend FastAPI
 * (run.py) como proceso "sidecar" de Python, muestra un splash con el
 * progreso real del bootstrap (pip / Ollama / modelo Granite) y luego
 * carga http://127.0.0.1:<puerto> en la ventana principal.
 *
 * (c) JullEditor v3.4.0 — ver PLAN_ELECTRON_WINDOWS.md
 */

const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn, execFile } = require('child_process');
const net = require('net');
const path = require('path');
const fs = require('fs');
const os = require('os');
const http = require('http');
const log = require('electron-log');

log.transports.file.level = 'info';
log.info('JullEditor Desktop iniciando, versión', app.getVersion());

const IS_DEV = process.argv.includes('--dev');
// En desarrollo: el sidecor corre desde la raíz del repo; empaquetado: desde
// resources/app (copiado vía extraResources por electron-builder).
const APP_ROOT = IS_DEV ? path.resolve(__dirname, '..') : path.join(process.resourcesPath, 'app');
const EMBEDDED_PYTHON = path.join(process.resourcesPath, 'python', process.platform === 'win32' ? 'python.exe' : 'bin/python3');

const PORT_RANGE_START = 8100;
const PORT_RANGE_END = 8999;
const READY_TIMEOUT_MS = 10 * 60 * 1000; // 10 min: primer arranque instala pip + Ollama + modelo

let mainWindow = null;
let splashWindow = null;
let pythonProcess = null;
let currentPort = null;
let quitting = false;

// ---------------------------------------------------------------------------
// Single instance lock: evita dos backends peleando por puerto/Ollama
// ---------------------------------------------------------------------------
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });
}

// ---------------------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------------------
function findFreePort(start, end) {
  return new Promise((resolve, reject) => {
    const tryPort = (p) => {
      if (p > end) return reject(new Error('No hay puertos libres en el rango'));
      const srv = net.createServer();
      srv.once('error', () => tryPort(p + 1));
      srv.once('listening', () => srv.close(() => resolve(p)));
      srv.listen(p, '127.0.0.1');
    };
    tryPort(start);
  });
}

function resolvePythonCommand() {
  // 1) Runtime embebido del instalador (producción)
  if (!IS_DEV && fs.existsSync(EMBEDDED_PYTHON)) {
    return { cmd: EMBEDDED_PYTHON, argsPrefix: [] };
  }
  // 2) Intérprete actual de Python (desarrollo / fallback sistema)
  const sysPy = process.env.JULL_PYTHON ||
    (process.platform === 'win32' ? 'python' : 'python3');
  return { cmd: sysPy, argsPrefix: [] };
}

function httpGetJson(url, timeoutMs = 3000) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout: timeoutMs }, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => {
        try { resolve(JSON.parse(body)); } catch { resolve(null); }
      });
    });
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
  });
}

function sendToSplash(channel, payload) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send(channel, payload);
  }
}

// ---------------------------------------------------------------------------
// Splash window
// ---------------------------------------------------------------------------
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 640,
    height: 460,
    frame: false,
    resizable: false,
    alwaysOnTop: true,
    show: true,
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  splashWindow.loadFile(path.join(__dirname, 'renderer', 'splash.html'));
}

// ---------------------------------------------------------------------------
// Ciclo de vida del sidecar Python
// ---------------------------------------------------------------------------
async function startBackend() {
  const port = await findFreePort(PORT_RANGE_START, PORT_RANGE_END);
  currentPort = port;

  const outputDir = path.join(os.homedir(), 'Documents', 'JullEditor');
  fs.mkdirSync(outputDir, { recursive: true });

  const { cmd } = resolvePythonCommand();
  const args = [
    path.join(APP_ROOT, 'run.py'),
    '--port', String(port),
    '--no-browser',
    '--json-status',
  ];
  // Con el runtime embebido las dependencias pip ya vienen preinstaladas
  // (Fase 3 del plan) → se omite la parte de pip del bootstrap; Ollama y el
  // modelo Granite sí se verifican/descargan en el equipo del usuario.
  const useEmbedded = !IS_DEV && fs.existsSync(EMBEDDED_PYTHON);
  if (useEmbedded) args.push('--skip-deps');

  log.info(`Lanzando sidecar: ${cmd} ${args.join(' ')} (cwd=${APP_ROOT})`);

  pythonProcess = spawn(cmd, args, {
    cwd: APP_ROOT,
    env: {
      ...process.env,
      JULL_OUTPUT_DIR: outputDir,
      PYTHONUNBUFFERED: '1',
      PYTHONIOENCODING: 'utf-8',
    },
    windowsHide: true,
  });

  pythonProcess.stdout.setEncoding('utf-8');
  pythonProcess.stderr.setEncoding('utf-8');

  let stdoutBuf = '';
  pythonProcess.stdout.on('data', (chunk) => {
    stdoutBuf += chunk;
    let idx;
    while ((idx = stdoutBuf.indexOf('\n')) >= 0) {
      const line = stdoutBuf.slice(0, idx);
      stdoutBuf = stdoutBuf.slice(idx + 1);
      if (line.startsWith('STATUS_JSON:')) {
        try {
          const status = JSON.parse(line.slice('STATUS_JSON:'.length));
          log.info('Estado backend:', status);
          sendToSplash('bootstrap-status', status);
        } catch (e) {
          log.warn('STATUS_JSON malformado:', line);
        }
      } else if (line.trim()) {
        sendToSplash('bootstrap-log', line.trim());
      }
    }
  });

  pythonProcess.stderr.on('data', (chunk) => {
    const text = String(chunk).trim();
    if (text) {
      log.warn('stderr backend:', text);
      sendToSplash('bootstrap-log', text);
    }
  });

  pythonProcess.on('exit', (code, signal) => {
    log.info(`Backend Python terminó (code=${code}, signal=${signal})`);
    pythonProcess = null;
    if (!quitting) {
      showFailure(`El motor de JullEditor se cerró inesperadamente (código ${code}).`, code);
    }
  });

  pythonProcess.on('error', (err) => {
    log.error('No se pudo lanzar Python:', err);
    showFailure(
      'No se pudo iniciar Python. Verifica que el runtime embebido esté presente o instala Python 3.11+.\n' + err.message,
      -1
    );
  });

  // Polling de salud hasta que FastAPI responda
  const deadline = Date.now() + READY_TIMEOUT_MS;
  while (Date.now() < deadline) {
    if (!pythonProcess) throw new Error('backend-exited');
    const health = await httpGetJson(`http://127.0.0.1:${port}/api/health`);
    if (health && typeof health.status === 'string') {
      sendToSplash('bootstrap-status', { state: 'ready', port });
      return port;
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error('timeout');
}

function killBackendTree() {
  if (!pythonProcess) return;
  const pid = pythonProcess.pid;
  try {
    if (process.platform === 'win32') {
      // Matar todo el árbol (uvicorn --reload crea hijos)
      execFile('taskkill', ['/T', '/F', '/PID', String(pid)], () => {});
    } else {
      pythonProcess.kill('SIGTERM');
    }
  } catch (e) {
    log.warn('Error matiendo backend:', e);
  }
  pythonProcess = null;
}

// ---------------------------------------------------------------------------
// Ventana principal
// ---------------------------------------------------------------------------
function showMain(port) {
  if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
  splashWindow = null;

  mainWindow = new BrowserWindow({
    width: 1360,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'JullEditor',
    backgroundColor: '#0f172a',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadURL(`http://127.0.0.1:${port}`);
  mainWindow.on('closed', () => {
    mainWindow = null;
    app.quit();
  });
}

function showFailure(message, code) {
  if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
  splashWindow = null;
  const choice = dialog.showMessageBoxSync({
    type: 'error',
    title: 'JullEditor no pudo iniciar',
    message,
    buttons: ['Reintentar', 'Cerrar'],
    defaultId: 0,
  });
  if (choice === 0) {
    createSplash();
    boot();
  } else {
    app.quit();
  }
}

async function boot() {
  try {
    const port = await startBackend();
    showMain(port);
  } catch (err) {
    log.error('Fallo de arranque:', err);
    const msg =
      err.message === 'timeout'
        ? 'El motor tardó demasiado en estar listo (>10 min). Revisa tu conexión a internet: el primer arranque descarga Ollama y el modelo IA.'
        : err.message;
    showFailure(msg, -1);
  }
}

// ---------------------------------------------------------------------------
// IPC expuesto al splash (mínimo, sin nodeIntegration)
// ---------------------------------------------------------------------------
ipcMain.handle('get-bootstrap-info', () => ({ port: currentPort, dev: IS_DEV }));
ipcMain.on('retry-boot', () => {
  killBackendTree();
  boot();
});

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------
app.whenReady().then(() => {
  createSplash();
  boot();
});

app.on('before-quit', () => {
  quitting = true;
  killBackendTree();
});

app.on('window-all-closed', () => {
  quitting = true;
  killBackendTree();
  app.quit();
});

process.on('exit', killBackendTree);
