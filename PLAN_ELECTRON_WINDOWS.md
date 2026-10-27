# 🪟 Plan: Empaquetar JullEditor como Aplicación de Escritorio para Windows con Electron

**Objetivo:** Distribuir JullEditor v3.4.0 como una aplicación instalable (`.exe` / NSIS) en Windows, donde **Electron actúa como contenedor nativo** que carga la interfaz web existente (`frontend/`) servida por el backend FastAPI, y gestiona el ciclo de vida del proceso Python (bootstrap + Ollama + modelo Granite).

**Arquitectura elegida:** *Electron shell + Backend Python sidecar* (patrón "embedded server"). No se reescribe el frontend ni se empaqueta Python en un `.exe` monolítico con PyInstaller; se reutiliza `run.py` / `backend/bootstrap.py` tal como están.

```
┌─────────────────────────────────────────────┐
│  JullEditor.exe (Electron)                  │
│  ├─ Main process: spawn python run.py       │
│  ├─ BrowserWindow → http://127.0.0.1:PORT   │
│  └─ Splash/estado: bootstrap, Ollama, puerto│
├─────────────────────────────────────────────┤
│  Python sidecar (FastAPI + uvicorn)         │
│  ├─ backend/bootstrap.py (pip, Ollama, GGUF)│
│  └─ Sirve frontend/ estático + API SSE      │
├─────────────────────────────────────────────┤
│  Ollama (servicio local) + IBM Granite      │
└─────────────────────────────────────────────┘
```

---

## Fase 0 — Preparación (0,5 día)

- [ ] Crear rama `feature/electron-desktop`.
- [ ] Verificar que `python run.py --port <P>` arranca sin abrir navegador automáticamente (agregar flag `--no-browser` si no existe; Electron abre su propia ventana).
- [ ] Confirmar que FastAPI sirve el SPA completo en `http://127.0.0.1:P` (ya monta `/static`, `/css`, `/js`, `/fonts` y `index.html` — líneas 757-814 de `backend/app.py`). ✅ verificado
- [ ] Definir puerto dinámico: Electron elige un puerto libre (ej. 8000-8999) y lo pasa a `run.py --port`.

## Fase 1 — Esqueleto Electron (1-2 días)

Estructura nueva en `desktop/`:

```
desktop/
├── package.json          # electron, electron-builder, electron-log
├── main.js               # proceso principal
├── preload.js            # puente IPC seguro (contextIsolation: true)
├── renderer/
│   ├── splash.html       # pantalla de arranque con progreso del bootstrap
│   └── splash.js
├── python/               # runtime Python portable (embeddable) — generado en Fase 3
└── build/                # iconos .ico, recursos del instalador
```

- [ ] `npm init` + instalar dependencias: `electron`, `electron-builder`, `electron-log`.
- [ ] **main.js**:
  - [ ] Al arrancar: buscar puerto libre → hacer `spawn` de `python/python.exe run.py --port P --no-browser` con `cwd = resources/app` (la raíz del repo empaquetada).
  - [ ] Hacer *polling* de `GET http://127.0.0.1:P/health` (o raíz) cada 1 s hasta que el backend responda (timeout razonable ~10 min para el primer arranque, que incluye `pip install` + `ollama pull`).
  - [ ] Mientras tanto, mostrar `splash.html` transmitiendo stdout/stderr del proceso Python vía IPC (`webContents.send('bootstrap-log', chunk)`).
  - [ ] Al estar listo: `loadURL('http://127.0.0.1:P')` en la ventana principal (frameless o con menú propio, ancho 1280+).
  - [ ] En `window-all-closed` / `before-quit`: matar el proceso Python **y solo ese PID** (árbol con `taskkill /T /PID` en Windows) para no dejar uvicorn huérfano.
  - [ ] Manejo de errores: si Python muere, mostrar diálogo con log de `electron-log` y botón "Reintentar".
- [ ] **preload.js**: exponer solo `getBootstrapStatus()`, `onLog(cb)`, `retry()` — nada de `nodeIntegration`.
- [ ] Single-instance lock (`app.requestSingleInstanceLock()`) para evitar dos backends peleando por el puerto/Ollama.

## Fase 2 — Ajustes mínimos en el repo existente (0,5-1 día)

- [ ] `run.py`: agregar `--no-browser` (suprimir `webbrowser.open`) y `--json-status` opcional que imprima `{"state":"installing_deps|pulling_model|ready","port":P}` línea a línea en stdout, para que Electron muestre progreso granular en el splash.
- [ ] `backend/bootstrap.py`: asegurar comportamiento no interactivo cuando corra bajo Electron (sin `input()`/`pause`); las descargas grandes (OllamaSetup.exe, modelos) deben reportar progreso por stdout.
- [ ] Verificar CORS/CSP: al cargar desde `http://127.0.0.1` todo es same-origin; revisar que `index.html` no tenga URLs absolutas rotas.
- [ ] Agregar script npm en `desktop/package.json`: `npm run dev` (Electron apuntando al repo local, sin empaquetar) para iterar rápido.

## Fase 3 — Runtime Python embebido (1-2 días)

Opción recomendada: **Python Embeddable** oficial de Microsoft, preparada en la máquina de build (Windows):

- [ ] Script `desktop/scripts/prepare-python.ps1`:
  1. Descargar `python-3.11.x-embed-amd64.zip` → descomprimir en `desktop/python/`.
  2. Habilitar `import site` en `python311._pth` e instalar `pip` (get-pip.py).
  3. `python -m pip install -r requirements.txt --target desktop/python/Lib/site-packages` (o crear un venv dentro de `desktop/python-env/`).
  4. Sanity check: `python -c "import fastapi, uvicorn"`.
- [ ] El instalador **NO** debe incluir los modelos GGUF (5-8 GB): `backend/bootstrap.py` ya los descarga en el equipo del usuario vía Ollama. Esto mantiene el `.exe` ligero (~200-300 MB).
- [ ] Alternativa evaluada y descartada: PyInstaller del backend (complica SSE/docling y aumenta tiempos de build; el sidecar con Python embeddable es más mantenible).

## Fase 4 — Configuración de electron-builder (1 día)

En `desktop/package.json` → bloque `"build"`:

- [ ] `appId: com.julleditor.desktop`, `productName: JullEditor`.
- [ ] `files`: `main.js`, `preload.js`, `renderer/**`.
- [ ] `extraResources`: copiar al instalador → `backend/`, `frontend/`, `run.py`, `requirements.txt`, `pyproject.toml`, `.env.example`, `desktop/python/` (runtime embebido). Excluir: `Informacion_docling_rag/`, `notebooks/`, `tests/`, `docker/`, `.git`, `Articulos Generados/` (esta carpeta de salida debe redirigirse a `%USERPROFILE%\Documents\JullEditor\` vía variable de entorno que fija Electron).
- [ ] `win`: target `nsis` (+ opcional `portable`), `icon: build/icon.ico`, `signAndEditExecutable` (firma de código opcional; sin certificado, advertir SmartScreen y documentar).
- [ ] `nsis`: `oneClick: false`, `perMachine: false` (instalación por usuario, sin necesidad de admin), `allowToChangeInstallationDirectory: true`, `createDesktopShortcut: true`, `deleteAppDataOnUninstall: false`.
- [ ] `npm run dist` → artefacto en `desktop/dist/JullEditor Setup 3.4.0.exe`.

## Fase 5 — Pruebas en Windows (1-2 días)

- [ ] **Escenario PC limpia** (VM Windows 11 sin Python ni Ollama): instalar → primer arranque → verificar flujo completo del splash: detección de hardware → pip → instalación de Ollama (winget/fallback) → `ollama pull granite3.3:2b|8b` según RAM → apertura de la app.
- [ ] **Segundo arranque** (todo cacheado): tiempo hasta ventana principal < 10 s.
- [ ] Probar generación de artículo end-to-end (SSE streaming dentro de Electron funciona igual que en navegador).
- [ ] Cerrar la app y verificar que no quedan procesos `python.exe`/puertos abiertos (`netstat`).
- [ ] Probar actualización: reinstalar versión nueva sin perder artículos ni modelos.
- [ ] Casos borde: sin internet (debe funcionar si todo ya está instalado), Ollama ya instalada por el usuario, disco lleno, puerto ocupado.

## Fase 6 — Distribución y mantenimiento (0,5-1 día)

- [ ] Publicar el instalador en GitHub Releases (workflow CI: job Windows con `npm ci && npm run dist` como artefacto).
- [ ] Documentar en README sección "Instalación como aplicación de escritorio (Windows)".
- [ ] Opcional fase 7: `electron-updater` para auto-update del shell (el backend Python se actualiza junto al reinstalar).

---

## Resumen de esfuerzo y riesgos

| Ítem | Estimación |
|---|---|
| Duración total | **5-8 días** de trabajo efectivo |
| Tamaño del instalador | ~250-350 MB (Electron + Python embeddido; modelos se descargan aparte) |
| Riesgo principal | Primer arranque largo (descarga de Ollama + modelo) → mitigado con splash con progreso real |
| Riesgo secundario | SmartScreen sin firma de código → mitigado comprando certificado EV/OV o indicando "Más información → Ejecutar de todas formas" |
| Ventaja clave | Cero cambios en frontend/backend existentes; `bootstrap.py` sigue siendo la fuente única de arranque |

### Orden de ejecución sugerido
`Fase 0 → 1 → 2 → 4 (con Python del sistema en modo dev) → 3 → 5 → 6`
(Se puede validar toda la integración Electron↔FastAPI antes de construir el runtime embebido.)
