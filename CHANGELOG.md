# 📜 Registro de Cambios (Changelog)

Todas las modificaciones notables a **JullEditor** están documentadas en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [3.4.0] - 2026-10-25

### Añadido
- **Auto-arranque inteligente del `.bat`** (`backend/bootstrap.py`, 100% Python): al iniciar `crear_articulo.bat` analiza la computadora (CPU/RAM/SO vía `system_profiler`) y verifica/instala automáticamente todo lo necesario para correr el proyecto:
  - **Python**: si no existe, `crear_articulo.bat` lo instala de una vez (`winget install Python.Python.3.12 --silent` con fallback al instalador oficial python.org silencioso con `PrependPath=1`).
  - **Dependencias**: detecta paquetes faltantes de `requirements.txt` y los instala con `pip install -r`.
  - **Ollama**: si falta, se instala según el SO (Windows: winget → instalador oficial `OllamaSetup.exe /SILENT`; Linux/macOS: script oficial `curl | sh` o Homebrew) y arranca `ollama serve` si el servicio no responde.
  - **Modelo Granite acorde al hardware**: `granite3.3:8b` si RAM ≥ 8 GB, `granite3.3:2b` si < 8 GB; solo ejecuta `ollama pull` si el modelo no está ya descargado.
- Bandera `python run.py --no-bootstrap` para omitir la auto-instalación (entornos controlados/CI).
- Suite de tests ampliada: `tests/test_bootstrap.py` (15 casos: parser de requirements, skip de pull, degradación sin Ollama, etc.) — **79/79 pruebas verdes**.

### Corregido
- Mock obsoleto en `test_windows_fallback_to_official_installer` (secuencia real de llamadas a `is_ollama_installed`).
- `diagnose_hardware()` delega ahora en `system_profiler` (eliminado bloque ctypes duplicado en `run.py`).
- `.gitignore` endurecido: `__pycache__/`, `*.pyc`, cachés de pytest/ruff/mypy; artefactos binarios retirados del índice.

## [3.3.1] - 2026-10-25

Incremento de **PATCH** conforme a [SemVer 2.0.0](https://semver.org/lang/es/): correcciones retrocompatibles de calidad y pruebas (ciclo QA completo) sin cambios funcionales ni de API.

### Añadido
- **Infraestructura QA**: configuración bloqueante de `ruff` (reglas F, E9 + higiene I/UP/B/C4/SIM/RUF) y `mypy` en `pyproject.toml`, con tolerancias documentadas para el pipeline offline-first (degradación elegante si Ollama/fuentes fallan).
- **`.gitignore` endurecido**: excluye artefactos de QA (`/logs/`, `.coverage`, SVGs transitorios de headers, inputs efímeros de `test_endpoint`) que llegaban a versionarse.

### Corregido
- **Compatibilidad Python 3.10+**: anotaciones modernizadas (PEP 585/604), eliminación de imports superfluos (F401), variables muertas e imports fuera de orden; validado con `py_compile` total y 64/64 pruebas verdes.
- **Unificación de ramas**: el trabajo de QA (rama `master` huérfana) se integró en `main` como única rama canónica del proyecto; eliminadas `master` y `qa/testing`.

---

## [3.3.0] - 2026-10-25

Incremento de **MINOR** conforme a [SemVer 2.0.0](https://semver.org/lang/es/): nueva funcionalidad retrocompatible (Fase 1 del `PLAN_OPTIMIZACION.md` — núcleo 100% Python) sin rupturas de API.

### Añadido
- **`backend/editorial_catalog.py`**: fuente única de verdad para todas las opciones editoriales (5 temas/especialidades, 12 tonos VE, 3 jurisdicciones, modelos Granite, estilos y ajustes avanzados). CLI, TUI, GUI web y API consumen ahora el mismo catálogo.
- **`backend/tui_app.py`**: interfaz TUI canónica construida con Textual (`python run.py --tui`), espejo 1:1 del flujo editorial web en terminal 100% Python: selección de especialidad, estilo, voz, jurisdicción, temperatura/modelo/extensión/instrucciones personalizadas, generación streaming y guardado en `Articulos Generados/`.
- **API `GET /api/editorial-options`** (`backend/app.py`): expone el catálogo unificado para que el frontend se alimente dinámicamente desde Python.
- **Lanzador `--tui`** en `run.py` junto a `--cli`, `--file`, `--test` y `--port`.

### Cambiado
- **`backend/cli_generator.py`**: refactorizado para importar tonos, jurisdicciones, temas y modelos desde `editorial_catalog`, garantizando consistencia absoluta entre `.bat`, TUI, web y API (misma lógica, misma lista de opciones).
- **Puentes `.bat`** (`crear_articulo.bat`, `start.bat`): encabezados actualizados a v3.3.0; mantienen su rol de launcher sin lógica propia hacia `python run.py`.
- **Versionado centralizado**: `backend/version.py`, `pyproject.toml`, README (badge y estado de versiones) sincronizados a `3.3.0`.

---

## [3.2.1] - 2026-10-25

### Cambios
- **Unificación del lenguaje a Python**: eliminados los scripts obsoletos `start.ps1`, `run_tests.ps1` y `deploy/oracle/setup.sh`; toda la lógica de arranque, pruebas y despliegue vive ahora en `run.py` (orquestador 100% Python).
- **Puentes `.bat` sin lógica**: `crear_articulo.bat` y `start.bat` se simplificaron a launchers que solo localizan el intérprete Python y delegan en `python run.py [--cli|--test|--file|--port]`, conservando la paridad 1:1 con la GUI web (Venezuela exclusivo).
- **README**: sección de inicio actualizada al flujo Python puro y nota explícita sobre el lenguaje del proyecto; sustituida la referencia al script Bash de Oracle por `python run.py --port`.
## [3.2.0] - 2026-10-25

### Cambiado
- **Foco exclusivo en Venezuela 🇻🇪**: la jurisdicción local soportada por el proyecto pasa a ser únicamente Venezuela (ruptura funcional intencional respecto a la GUI).
- **GUI (`frontend/index.html`)**: eliminadas las 3 voces "Abogado CO" del selector de tono (15 → 12 perfiles) y la opción "🇨🇴 Colombia" del selector de jurisdicción (4 → 3 opciones: Auto / Venezuela / Internacional).
- **CLI `.bat` (`backend/cli_generator.py`)**: menú espejo de la interfaz — tonos [1-12], jurisdicciones [1-3]; la detección "Auto" y el RAG legal se resuelven siempre con corpus venezolano.
- **`frontend/js/app.js`**: terminal de jurisdicción simplificado a "VENEZUELA 🇻🇪 / AUTO (VE)"; etiquetas de estructura y SEO tips actualizadas a "Marco Legal Venezuela".
- **README.md**: badge, subtítulo, diagrama de flujo y marco normativo actualizados al enfoque monojurisdiccional VE.

### Conservado
- Los motores internos (`legal_profiles.py`, `prompts.py`, `rag_manager.py`) mantienen la infraestructura multi-jurisdicción como capacidad técnica latente; solo se retiraron del menú de usuario. La carpeta de corpus `Informacion_docling_rag/Colombia` permanece disponible para futuras reactivaciones.

## [3.1.0] - 2026-10-25

Incremento de **MINOR** conforme a [SemVer 2.0.0](https://semver.org/lang/es/): nueva funcionalidad retrocompatible (paridad CLI/GUI) sin romper la API pública.

### 🟢 Nuevas Funcionalidades (New Features)
- **Paridad 1:1 CLI ↔ GUI**: `crear_articulo.bat` (`backend/cli_generator.py`) ahora replica exactamente los controles de `frontend/index.html`: las 15 voces/jurisdicciones del selector de tono, las 4 jurisdicciones con "Auto" predeterminado, y los ajustes avanzados (temperatura, modelo `granite3.3:8b/2b`, extensión 600–2000 palabras e instrucciones personalizadas).
- **Sincronización `.bat → Web`**: al elegir el modo servidor web desde el asistente CLI, la GUI precarga también modelo, estilo editorial e instrucciones personalizadas (antes solo título, tema, tono, jurisdicción, temperatura y palabras).
- **Fuente única de versión (`backend/version.py`)**: constante `__version__` canónica bajo SemVer, consumida por FastAPI (`/api/health`, OpenAPI), el banner CLI y la marca de agua de artículos; sincronizada con `pyproject.toml`.

### 🔴 Correcciones (Bug Fixes)
- Validación en bucle de las selecciones de tono y jurisdicción en el CLI (entradas inválidas ya no abortan la sesión).
- Detección automática de país en el RAG legal cuando la jurisdicción es "Auto", según el tono elegido (mismo criterio que `app.py`).

---

## [3.0.0] - 2026-10-23

### 🔴 Correcciones Críticas (Bug Fixes)
- **Starlette 422 Deprecation Warning**: Resuelto completamente el warning `StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead` mediante manejo de estado agnóstico `getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)`.
- **Validación Defensiva Pydantic v2**: Incorporados validadores `field_validator` en `GenerateRequest` para saneamiento y coerción automática de parámetros (`editorial_mode`, `target_words`, `temperature`, valores nulos en metadatos).
- **Validación y Desempaquetado Frontend**: Validación previa de longitud mínima (10 caracteres) en `article-generator.js` y formateo amigable de errores de validación con toasts explicativos.

### 🟢 Nuevas Funcionalidades (New Features)
- **Perfilador de Hardware Automático (`system_profiler.py`)**: Detección nativa de CPU, RAM y sistema operativo con recomendación dinámica de modelos (`granite3.3:8b` vs `granite3.3:2b`) y parámetros de contexto.
- **Endpoint de Diagnóstico `/api/system-info`**: Inspección en tiempo real de recursos del host y configuración activa.
- **Soporte Google Colab (`notebooks/granite_blog_colab.ipynb`)**: Notebook interactivo paso a paso para levantar Ollama + Granite con túnel público o ventana integrada sin fricción.
- **Despliegue en la Nube / Oracle Cloud (`deploy/oracle/`)**:
  - `docker/Dockerfile` multi-stage optimizado para Linux x86 y ARM.
  - `docker/docker-compose.yml` orquestando Ollama + Backend + Nginx.
  - `docker/nginx/default.conf` con configuración de Server-Sent Events (SSE) sin buffering y con timeout extendido a 600s.
  - Script de instalación desatendida `setup.sh` y servicio `granite-blog.service` para `systemd`.
- **Health Check con Auto-Reintento y Latencia**: Medición de latencia en milisegundos (`latency_ms`) y reporte de versión `3.0.0`.

### 🟡 Mejoras de UX/UI y Accesibilidad
- **Skeleton Pulse Loader**: Animación de carga fluida en CSS para transiciones de generación.
- **Latencia en Vivo en el Header**: El badge de estado de Ollama ahora indica los milisegundos de respuesta del motor local.
- **Accesibilidad WCAG 2.1 AA**: Respeto al modo oscuro del sistema (`color-scheme: dark`) y soporte para usuarios con sensibilidad al movimiento (`prefers-reduced-motion`).
- **Suite de Pruebas de Integración (`tests/test_integration.py`)**: 57 pruebas unitarias y de integración pasando con 100% de éxito.
