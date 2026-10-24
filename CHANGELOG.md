# 📜 Registro de Cambios (Changelog)

Todas las modificaciones notables a **JullEditor** están documentadas en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

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
