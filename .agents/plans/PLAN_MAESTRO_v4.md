# 📋 PLAN MAESTRO DE OPTIMIZACIÓN PROFESIONAL — JullEditor v4.0

## Documento Canónico de Ejecución Paso a Paso para Agentes IA

> **Propósito:** Este documento es la fuente única de verdad para llevar JullEditor
> desde su estado actual (v3.4.0) hasta un nivel profesional de producción (v4.0.0).
> Está diseñado para que **cualquier agente IA** pueda ejecutarlo paso a paso sin
> ambigüedad ni errores. Cada fase tiene prerequisitos, acciones exactas, archivos
> a modificar/crear, comandos a ejecutar, y criterios de salida verificables.

**Fecha de creación:** 2026-10-27
**Versión actual del proyecto:** v3.4.0
**Versión objetivo:** v4.0.0
**Repositorio:** `gh repo clone julljoll/JullEditor` (https://github.com/julljoll/JullEditor.git)
**Rama de trabajo:** `main`
**Sistema operativo objetivo:** Windows 10/11 (64-bit)
**Lenguaje exclusivo:** Python ≥ 3.10 (toda lógica propia)
**Modelo IA local:** IBM Granite 3.3 vía Ollama

---

## 🔍 DIAGNÓSTICO COMPLETO DEL ESTADO ACTUAL (v3.4.0)

### Arquitectura actual

```
JullEditor/
├── backend/                  # FastAPI + módulos Python (17 archivos .py)
│   ├── app.py               # Servidor FastAPI (817 líneas, 36KB)
│   ├── bootstrap.py          # Auto-instalación Python/Ollama/Granite (375 líneas)
│   ├── cli_generator.py      # CLI interactivo terminal (37KB)
│   ├── editorial_catalog.py  # Catálogo editorial unificado
│   ├── prompts.py            # Mega-prompts (~59KB, el más grande)
│   ├── rag_manager.py        # RAG léxico local (35KB)
│   ├── legal_profiles.py     # Perfiles jurisdiccionales (32KB)
│   ├── tui_app.py            # TUI Textual (17KB)
│   ├── scraper.py            # Web scraper anti-SSRF (14KB)
│   ├── sentencia_extractor.py # Extractor metadatos TSJ
│   ├── seo_validator.py      # Auditoría SEO
│   ├── legal_validator.py    # Validación jurídica
│   ├── image_generator.py    # Generador SVG de cabeceras
│   ├── docling_parser.py     # Parser Docling MD/JSON
│   ├── system_profiler.py    # Detección hardware
│   ├── logger_config.py      # Configuración logging
│   └── version.py            # Versionado SemVer
├── frontend/                 # HTML/CSS/JS estático (42KB index.html, 12KB app.js)
│   ├── index.html
│   ├── js/app.js + modules/
│   └── css/, images/, fonts/
├── desktop/                  # Shell Electron (package.json + main.js)
├── Informacion_docling_rag/  # Corpus jurídico VE (12 subdirs, ~96 fuentes)
├── Articulos Generados/      # Salida de artículos (.md + .html)
├── tests/                    # 10 archivos de test (79/79 verdes)
├── run.py                    # Orquestador principal (307 líneas)
├── crear_articulo.bat        # Launcher Windows con auto-install Python
├── start.bat                 # Launcher simplificado
├── pyproject.toml            # Config proyecto + ruff + mypy
├── requirements.txt          # 11 dependencias
└── .env.example              # Variables de entorno
```

### Inventario de fortalezas

| Componente | Estado | Detalle |
|---|---|---|
| Bootstrap 100% Python | ✅ Excelente | Auto-instala Python, Ollama, Granite acorde a hardware |
| FastAPI + SSE streaming | ✅ Sólido | Concurrencia controlada, validación Pydantic |
| Catálogo editorial unificado | ✅ Bien | 5 temas, 12 tonos, 3 jurisdicciones en un solo .py |
| Tests | ✅ 79/79 verdes | Cobertura funcional decente |
| Offline-first | ✅ Core | Todo funciona sin internet |
| Anti-alucinación | ✅ Parcial | Temperatura 0.15-0.3 por tema |
| .bat con auto-install | ✅ Funcional | Instala Python + deps + Ollama + modelo |

### Inventario de deudas técnicas y brechas

| Problema | Severidad | Impacto |
|---|---|---|
| RAG léxico simple (sin embeddings) | 🔴 Alta | Recuperación imprecisa de normas jurídicas |
| Generación single-shot (1 pasada LLM) | 🔴 Alta | Sin ciclo borrador→revisión→refinamiento |
| `prompts.py` monolítico (59KB) | 🟡 Media | Difícil de mantener y testear |
| JS contiene algo de lógica de negocio | 🟡 Media | Duplicación Python/JS |
| Sin validación literal de citas | 🔴 Alta | Puede citar artículos inexistentes |
| `.gitignore` débil | 🟡 Media | No excluye `Articulos Generados/`, `.venv`, etc. |
| Sin `setup.py`/`pyproject.toml` entry_points | 🟡 Media | No instalable como paquete pip |
| desktop/ depende de Node/Electron | 🟡 Media | Contradicción con "100% Python" |
| Sin pre-commit hooks | 🟢 Baja | QA no automatizada en commits |
| Sin typing completo | 🟢 Baja | mypy configurado pero sin cobertura total |

---

## 🏗️ ARQUITECTURA OBJETIVO v4.0

```
JullEditor v4.0/
├── backend/
│   ├── core/                     # NUEVO: Pipeline agéntico
│   │   ├── __init__.py
│   │   ├── pipeline.py           # Orquestador 4 agentes
│   │   ├── agent_analyst.py      # Agente 1: Análisis de fuente
│   │   ├── agent_researcher.py   # Agente 2: Consulta RAG
│   │   ├── agent_writer.py       # Agente 3: Redacción por bloques
│   │   └── agent_critic.py       # Agente 4: Revisión adversarial
│   ├── rag/                      # NUEVO: RAG vectorial
│   │   ├── __init__.py
│   │   ├── vector_store.py       # ChromaDB + embeddings
│   │   ├── chunker.py            # Chunking por artículo normativo
│   │   └── reranker.py           # Reranking híbrido BM25+denso
│   ├── validators/               # NUEVO: Validadores reforzados
│   │   ├── __init__.py
│   │   ├── legal_v2.py           # Validación literal contra índice
│   │   ├── seo_geo.py            # SEO + GEO élite
│   │   └── citation_checker.py   # Verificador de citas
│   ├── exporters/                # NUEVO: Exportadores
│   │   ├── __init__.py
│   │   ├── wordpress.py
│   │   ├── markdown_export.py
│   │   └── docx_export.py        # python-docx
│   ├── prompts/                  # REFACTORIZADO: prompts por agente
│   │   ├── __init__.py
│   │   ├── analyst.py
│   │   ├── researcher.py
│   │   ├── writer.py
│   │   ├── critic.py
│   │   └── templates/            # Plantillas Jinja2
│   ├── app.py                    # OPTIMIZADO
│   ├── bootstrap.py              # EXISTENTE (mejorado)
│   ├── editorial_catalog.py      # EXISTENTE
│   ├── rag_manager.py            # EXISTENTE (delegará a rag/)
│   └── ...otros existentes
├── frontend/                     # EXISTENTE (presentación estática)
├── installer/                    # NUEVO: Instalador Windows nativo Python
│   ├── build_installer.py        # Script de construcción
│   ├── julleditor_installer.py   # Instalador GUI (tkinter)
│   └── README_INSTALLER.md
├── Informacion_docling_rag/      # EXISTENTE
├── tests/                        # AMPLIADO
├── run.py                        # EXISTENTE (entry point)
├── crear_articulo.bat            # EXISTENTE (puente)
├── pyproject.toml                # MEJORADO (entry_points, deps)
└── requirements.txt              # ACTUALIZADO
```

---

## 📦 FASES DE EJECUCIÓN (7 Fases)

---

### FASE 0 — Cimientos: Higiene, Instalación Windows y Estructura
**Versión objetivo:** v3.4.1 (PATCH)
**Duración estimada:** 1-2 días
**Prerequisitos:** Repositorio clonado, Python >=3.10 instalado

#### PASO 0.1 — Fortalecer `.gitignore`
**Archivo:** `.gitignore`
**Acción:** Reescribir completamente con exclusiones profesionales.
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
*.egg
.venv/
venv/
env/

# Entorno
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs y caché
logs/
*.log
.coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/

# Node (desktop shell legacy)
node_modules/
desktop/dist/
desktop/python/

# Datos generados
Articulos Generados/
Jurisprudencias/

# RAG vectorial (índice local, regenerable)
.julleditor_db/

# OS
Thumbs.db
.DS_Store
```

#### PASO 0.2 — Crear virtualenv estándar y `requirements.txt` limpio
**Comandos a ejecutar (en PowerShell, desde la raíz del proyecto):**
```powershell
# Crear entorno virtual
python -m venv .venv

# Activar
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
pip install -e ".[dev]"
```

**Archivo:** `requirements.txt` — Actualizar con versiones pinneadas:
```
fastapi>=0.115.0,<1.0.0
uvicorn[standard]>=0.30.6,<1.0.0
httpx>=0.27.2,<1.0.0
beautifulsoup4>=4.12.3
playwright>=1.47.0
python-dotenv>=1.0.1
pydantic>=2.9.2,<3.0.0
aiofiles>=24.1.0
textual>=0.80,<9.0.0
# QA (dev)
pytest>=8.3.3
pytest-asyncio>=0.24.0
pytest-cov>=5.0.0
ruff>=0.7.0
```

#### PASO 0.3 — Mejorar `pyproject.toml` con entry_points
**Archivo:** `pyproject.toml`
**Agregar bloques:**
```toml
[project.scripts]
julleditor = "run:main"

[project.optional-dependencies]
dev = [
    "pytest>=8.3.3",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.7.0",
]
rag = [
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",
    "rank-bm25>=0.2.2",
]
export = [
    "python-docx>=1.1.0",
    "Jinja2>=3.1.0",
]
```

#### PASO 0.4 — Actualizar `bootstrap.py` para virtualenv awareness
**Archivo:** `backend/bootstrap.py`
**Acción:** Agregar detección de virtualenv para optimizar el bootstrap:
```python
def _in_virtualenv() -> bool:
    """Detecta si estamos corriendo dentro de un virtualenv."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
```

#### PASO 0.5 — Crear instalador Windows nativo (100% Python, sin Electron)
**Directorio:** `installer/`
**Archivo:** `installer/julleditor_installer.py`
**Propósito:** Reemplazar Electron con un instalador/launcher GUI nativo en
Python usando `tkinter` (incluido en Python estándar).

Funcionalidades del instalador:
1. Ventana splash con logo y barra de progreso
2. Detecta si Python está instalado; si no, descarga e instala silenciosamente
3. Crea `.venv`, instala `requirements.txt`
4. Verifica/instala Ollama
5. Descarga modelo Granite acorde a hardware
6. Crea acceso directo en Escritorio
7. Lanza `run.py` al finalizar

Se puede compilar a `.exe` con PyInstaller:
```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --icon=frontend/favicon.svg --name "JullEditor Setup" installer/julleditor_installer.py
```

#### PASO 0.6 — Ejecutar tests y verificar verde
**Comando:**
```powershell
python run.py --test
```
**Criterio de salida:** 79/79 tests verdes. Si alguno falla, corregir ANTES de
continuar a Fase 1.

#### Criterios de salida Fase 0:
- [ ] `.gitignore` profesional escrito
- [ ] `.venv` creado y funcional
- [ ] `pyproject.toml` tiene `[project.scripts]` y dependencias opcionales
- [ ] `bootstrap.py` detecta virtualenvs
- [ ] `installer/julleditor_installer.py` creado y funcional
- [ ] Todos los tests pasan
- [ ] Commit: `chore(v3.4.1): higiene, .gitignore, venv, instalador Python nativo`

---

### FASE 1 — Refactorización de Prompts y Estructura Modular
**Versión objetivo:** v3.5.0 (MINOR)
**Duración estimada:** 3-5 días
**Prerequisitos:** Fase 0 completada

#### PASO 1.1 — Descomponer `prompts.py` (59KB) en módulos
**Problema:** `prompts.py` es un archivo monolítico de 59KB con todos los
prompts hardcodeados. Es imposible de mantener y testear.

**Acción:** Crear directorio `backend/prompts/` con módulos por función:
```
backend/prompts/
├── __init__.py          # Re-exporta build_generation_prompt, build_sentencia_tsj_prompt
├── base.py              # Constantes y bloques compartidos
├── blog_writer.py       # Prompt de generación de artículos blog
├── sentencia_tsj.py     # Prompt para análisis de sentencias TSJ
├── critic.py            # NUEVO: Prompt del agente crítico (Fase 3)
├── researcher.py        # NUEVO: Prompt del agente investigador (Fase 3)
└── templates/           # Plantillas Jinja2 para secciones del artículo
    ├── article_header.j2
    ├── article_body.j2
    ├── faq_section.j2
    └── schema_jsonld.j2
```

**Regla crítica:** El `__init__.py` DEBE re-exportar las mismas funciones
públicas (`build_generation_prompt`, `build_sentencia_tsj_prompt`) para no
romper imports existentes en `app.py` y `cli_generator.py`:
```python
# backend/prompts/__init__.py
from backend.prompts.blog_writer import build_generation_prompt
from backend.prompts.sentencia_tsj import build_sentencia_tsj_prompt
```

#### PASO 1.2 — Migrar lógica JS residual a Python
**Archivos JS a auditar:** `frontend/js/modules/`
**Acción:** Identificar toda función JS que contenga reglas de negocio
(conteo SEO, validación, formateo) y moverla a endpoints Python.

**Principio:** JavaScript solo hace:
- Fetch a endpoints Python
- Renderizado DOM
- Eventos UI

**Python contiene toda la lógica:**
- Conteo de palabras/caracteres
- Cálculo de densidad de keywords
- Validación de estructura
- Formateo de exportación

#### PASO 1.3 — Tests para los prompts refactorizados
**Archivo:** `tests/test_prompts.py` (ampliar)
**Acción:** Cada módulo de prompts debe tener al menos 3 tests:
1. Que retorne un string no vacío
2. Que contenga las keywords obligatorias del formato
3. Que respete el límite de tokens estimado

#### Criterios de salida Fase 1:
- [ ] `backend/prompts/` es un paquete con >=4 módulos
- [ ] `prompts.py` original eliminado o convertido en redirect
- [ ] `from backend.prompts import build_generation_prompt` funciona
- [ ] Toda lógica de negocio removida de JS
- [ ] Tests de prompts >= 10 casos
- [ ] Todos los tests pasan (>=85 tests verdes)
- [ ] Commit: `refactor(v3.5.0): modularizar prompts, migrar lógica JS a Python`

---

### FASE 2 — RAG Vectorial Jurídico Venezolano
**Versión objetivo:** v3.6.0 (MINOR)
**Duración estimada:** 5-7 días
**Prerequisitos:** Fase 1 completada

#### PASO 2.1 — Instalar dependencias de RAG vectorial
**Comando:**
```powershell
pip install chromadb sentence-transformers rank-bm25
```
**Agregar a `requirements.txt`:**
```
chromadb>=0.5.0
sentence-transformers>=3.0.0
rank-bm25>=0.2.2
```

#### PASO 2.2 — Crear chunker jurídico inteligente
**Archivo:** `backend/rag/chunker.py`
**Propósito:** Dividir el corpus de `Informacion_docling_rag/` en chunks
semánticos por **artículo normativo** (no por tokens fijos).

**Lógica del chunker:**
1. Leer cada archivo .md del corpus
2. Detectar encabezados de artículos (`## Artículo X`, `**Artículo X.**`)
3. Cada artículo = 1 chunk con metadatos:
   ```python
   {
       "text": "Artículo 25. Toda persona tiene derecho...",
       "metadata": {
           "source": "constitucion-republica-bolivariana.md",
           "category": "Constitucion",
           "article_number": "25",
           "law_name": "Constitución de la República Bolivariana de Venezuela",
       }
   }
   ```
4. Chunks de leyes sin artículos claros: ventana de 512 tokens con overlap de 64

#### PASO 2.3 — Crear vector store con ChromaDB
**Archivo:** `backend/rag/vector_store.py`
**Modelo de embeddings:** `paraphrase-multilingual-MiniLM-L12-v2`
(optimizado CPU, soporta español, ~120MB)

```python
# Pseudocódigo de la interfaz pública
class LegalVectorStore:
    def __init__(self, persist_dir: str = ".julleditor_db"):
        """Inicializa ChromaDB con persistencia local."""
    
    def index_corpus(self, corpus_dir: str) -> int:
        """Indexa todo Informacion_docling_rag/. Retorna # de chunks."""
    
    def search(self, query: str, top_k: int = 5,
               category: str | None = None) -> list[dict]:
        """Búsqueda híbrida BM25 + coseno con reranking."""
    
    def is_indexed(self) -> bool:
        """Retorna True si el índice ya existe y tiene datos."""
```

#### PASO 2.4 — Crear reranker híbrido
**Archivo:** `backend/rag/reranker.py`
**Estrategia:** Score final = 0.4 * BM25_score + 0.6 * cosine_score

#### PASO 2.5 — Agregar comando `--index` a `run.py`
**Archivo:** `run.py`
**Acción:** Agregar al parser de argumentos:
```python
parser.add_argument("--index", action="store_true",
                    help="(Re)construir el índice vectorial del corpus jurídico")
```
**Comportamiento:**
```
python run.py --index
>>> [INFO] Indexando corpus en Informacion_docling_rag/...
>>> [INFO] 12 directorios, 96 archivos procesados
>>> [INFO] 4,231 chunks indexados en .julleditor_db/
>>> [OK] Índice vectorial listo
```

#### PASO 2.6 — Integrar con `rag_manager.py` existente
**Archivo:** `backend/rag_manager.py`
**Acción:** La función `retrieve_legal_context()` debe intentar primero
el vector store; si no está disponible, fallback al RAG léxico actual.

```python
def retrieve_legal_context(query_text, theme, top_k=3, jurisdiction="ve"):
    try:
        from backend.rag.vector_store import LegalVectorStore
        vs = LegalVectorStore()
        if vs.is_indexed():
            results = vs.search(query_text, top_k=top_k)
            return _format_rag_results(results)
    except ImportError:
        pass  # ChromaDB no instalado: fallback léxico
    # ... código léxico existente (sin cambiar)
```

#### PASO 2.7 — Tests de RAG vectorial
**Archivo:** `tests/test_vector_store.py`
**Casos mínimos:**
1. Indexar un subdirectorio pequeño (ej: `Constitucion/`) y verificar chunks > 0
2. Buscar "derecho a la defensa" y verificar que retorna CRBV Art. 49
3. Buscar "cadena de custodia" y verificar que retorna ley de delitos informáticos
4. Verificar fallback léxico cuando ChromaDB no está instalado

#### Criterios de salida Fase 2:
- [ ] `python run.py --index` indexa el corpus completo sin errores
- [ ] `.julleditor_db/` creado con datos persistidos
- [ ] `retrieve_legal_context()` usa vector store cuando disponible
- [ ] Recall@5 >= 0.85 en set de 30 consultas jurídicas estándar
- [ ] Tests de RAG >= 8 casos verdes
- [ ] Fallback léxico funciona sin ChromaDB
- [ ] Commit: `feat(v3.6.0): RAG vectorial jurídico VE (ChromaDB + embeddings)`

---

### FASE 3 — Pipeline Agéntico de 4 Etapas
**Versión objetivo:** v3.7.0 (MINOR)
**Duración estimada:** 7-10 días
**Prerequisitos:** Fase 2 completada

#### PASO 3.1 — Crear directorio core y pipeline base
**Directorio:** `backend/core/`

**Archivo:** `backend/core/pipeline.py`
```python
class EditorialPipeline:
    """Orquestador de 4 agentes para generación de artículos."""
    
    async def run(self, source_text: str, config: dict,
                  on_token=None, on_stage=None):
        """Ejecuta las 4 etapas secuencialmente con streaming."""
        # Etapa 1: Análisis
        analysis = await self.analyst.analyze(source_text, config)
        if on_stage: on_stage("analyst_done", analysis)
        
        # Etapa 2: Investigación RAG
        dossier = await self.researcher.research(analysis, config)
        if on_stage: on_stage("researcher_done", dossier)
        
        # Etapa 3: Redacción (con streaming token a token)
        draft = await self.writer.write(analysis, dossier, config, on_token)
        if on_stage: on_stage("writer_done", draft)
        
        # Etapa 4: Crítica y revisión (máx 2 ciclos)
        final = await self.critic.review(draft, dossier, config)
        if on_stage: on_stage("critic_done", final)
        
        return final
```

#### PASO 3.2 — Agente Analista
**Archivo:** `backend/core/agent_analyst.py`
**Función:** Extrae del texto fuente:
- Problema jurídico / tema central
- Normas mencionadas o aplicables
- Si es sentencia: ratio decidendi, obiter dicta, votos salvados
- Palabras clave candidatas para SEO
- Idioma detectado y tono sugerido

#### PASO 3.3 — Agente Investigador
**Archivo:** `backend/core/agent_researcher.py`
**Función:** Consulta el RAG vectorial y arma un "dossier" con:
- Artículos normativos relevantes (texto exacto del corpus)
- Jurisprudencia relacionada (expediente, ponente, fecha)
- Estándares ISO/NIST aplicables
- **Regla anti-alucinación:** Solo incluye material que EXISTE en el corpus

#### PASO 3.4 — Agente Redactor
**Archivo:** `backend/core/agent_writer.py`
**Función:** Escribe el artículo por secciones, inyectando SOLO el dossier:
- Sigue el formato SEO Blog PDF del `AGENTS.md`
- Streaming token a token vía callback
- **Contexto cerrado:** No puede inventar más allá del dossier

#### PASO 3.5 — Agente Crítico
**Archivo:** `backend/core/agent_critic.py`
**Función:** Revisión adversarial con rúbrica de 10 puntos:
1. Exactitud de citas normativas (verificación contra dossier)
2. Coherencia argumentativa (IRAC/FILAC)
3. Densidad informativa (info por párrafo)
4. Ausencia de muletillas IA ("es importante señalar", "cabe destacar")
5. Conectores académicos variados
6. Estructura SEO correcta (H1/H2/H3/FAQ)
7. Extensión dentro del target (+/-10%)
8. Schema.org JSON-LD completo
9. Originalidad estilística
10. Cumplimiento jurisdiccional

**Ciclo:** Si score < 75/100, reescribe las secciones débiles (máx 2 ciclos).

#### PASO 3.6 — Integrar pipeline en app.py
**Archivo:** `backend/app.py`
**Acción:** El endpoint `/api/generate-stream` debe usar el pipeline:
```python
@app.post("/api/generate-stream")
async def generate_article_stream(req: GenerateRequest, request: Request):
    pipeline = EditorialPipeline(ollama_url=OLLAMA_BASE_URL, model=selected_model)
    
    async def event_generator():
        async for event in pipeline.run_streaming(req, config):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Retrocompatibilidad:** Agregar flag `pipeline_mode` (default: True). Si
`pipeline_mode=False`, usar el flujo single-shot actual.

#### Criterios de salida Fase 3:
- [ ] `backend/core/` con 5 archivos funcionales
- [ ] Pipeline ejecuta las 4 etapas secuencialmente
- [ ] Streaming SSE muestra indicador de etapa en el frontend
- [ ] Agente Crítico genera score y patch-notes
- [ ] Retrocompatibilidad con modo single-shot
- [ ] Tests del pipeline >= 12 casos
- [ ] Commit: `feat(v3.7.0): pipeline agéntico 4 etapas`

---

### FASE 4 — Validación Jurídica Literal
**Versión objetivo:** v3.8.0 (MINOR)
**Duración estimada:** 4-5 días
**Prerequisitos:** Fase 3 completada

#### PASO 4.1 — Validador literal de citas
**Archivo:** `backend/validators/legal_v2.py`
**Función:** Para cada cita normativa en el artículo generado:
1. Extraer: nombre de ley + número de artículo
2. Buscar en el índice vectorial si existe literalmente
3. Semáforo: verificada / imprecisa / inexistente

#### PASO 4.2 — Verificador de jurisprudencia
**Archivo:** `backend/validators/citation_checker.py`
**Función:** Para cada referencia a sentencia TSJ:
1. Extraer: Sala + Expediente + Ponente + Fecha
2. Verificar contra `Informacion_docling_rag/Jurisprudencias/`
3. Semáforo

#### PASO 4.3 — Informe de auditoría por artículo
**Salida:** `Articulos Generados/auditoria_{slug}.json`
```json
{
  "article_title": "...",
  "total_citations": 12,
  "verified": 10,
  "imprecise": 1,
  "not_found": 1,
  "details": [
    {"citation": "Art. 49 CRBV", "status": "verified", "source": "constitucion.md"},
    {"citation": "Art. 999 CC", "status": "not_found", "suggestion": null}
  ],
  "overall_status": "warning"
}
```

#### Criterios de salida Fase 4:
- [ ] Validador literal funciona con semáforo 3 colores
- [ ] Verificador de jurisprudencia funciona
- [ ] Informe JSON generado automáticamente al guardar artículo
- [ ] Cero artículos publicables con semáforo rojo
- [ ] Commit: `feat(v3.8.0): validación jurídica literal con semáforo`

---

### FASE 5 — SEO + GEO de Élite
**Versión objetivo:** v3.9.0 (MINOR)
**Duración estimada:** 3-4 días
**Prerequisitos:** Fase 4 completada

#### PASO 5.1 — GEO real (Answer Engine Optimization)
**Archivo:** `backend/validators/seo_geo.py`
**Funciones:**
- Generación automática de FAQ (schema.org/FAQPage) con <=48 palabras por respuesta
- Definiciones destacables (featured-snippet ready)
- JSON-LD `Article` + `LegalService` + breadcrumbs

#### PASO 5.2 — Análisis de legibilidad jurídica español-VE
- Índice de Flesch adaptado a sílabas del español
- Índice de nominalización
- Longitud media de período jurídico: 25-35 palabras

#### PASO 5.3 — Cluster semántico entre artículos
**Archivo:** `backend/validators/related_articles.py`
**Función:** Sugiere enlaces internos entre artículos generados basándose
en similitud de embeddings.

#### Criterios de salida Fase 5:
- [ ] Score SEO/GEO >= 90 para 100% de artículos exportados
- [ ] JSON-LD completo emitido en exportación
- [ ] FAQ generado automáticamente
- [ ] Commit: `feat(v3.9.0): SEO/GEO élite con FAQ, JSON-LD, legibilidad VE`

---

### FASE 6 — Exportación Profesional y Modelos Híbridos
**Versión objetivo:** v4.0.0 (MAJOR)
**Duración estimada:** 5-7 días
**Prerequisitos:** Fases 0-5 completadas

#### PASO 6.1 — Exportación `.docx` con plantilla de revista jurídica
**Archivo:** `backend/exporters/docx_export.py`
**Dependencia:** `python-docx>=1.1.0`
**Funciones:**
- Portada con título bilingüe, autor, fecha
- Sumario automático
- Notas al pie reales
- Bibliografía APA 7ma edición

#### PASO 6.2 — Modo híbrido de modelos
**Acción:** Agregar soporte para API OpenAI-compatible opcional:
```env
# .env
API_MODE=local  # local | api
API_BASE_URL=
API_KEY=
API_MODEL=
```
**Comportamiento:** Si `API_MODE=api` y falla, degradar automáticamente a local.

#### PASO 6.3 — Documentación final
- README v4.0 actualizado
- Guía del redactor (cómo usar el pipeline)
- CHANGELOG consolidado
- Release notes GitHub v4.0.0

#### PASO 6.4 — Compilar instalador final
```powershell
cd installer
pip install pyinstaller
pyinstaller --onefile --windowed --name "JullEditor Setup v4" julleditor_installer.py
```

#### Criterios de salida Fase 6:
- [ ] Exportación `.docx` funcional con portada y bibliografía
- [ ] Modo híbrido local/API funcional con degradación
- [ ] README v4.0 completo y actualizado
- [ ] Instalador `.exe` compilado y funcional
- [ ] Tag `v4.0.0` creado en GitHub
- [ ] Commit: `release(v4.0.0): JullEditor profesional`

---

### FASE 7 — Eliminación de Dependencia Electron (Python Puro)
**Versión objetivo:** v4.0.0 (incluida en la misma major)
**Duración estimada:** 2-3 días (puede ejecutarse en paralelo con Fase 6)

#### PASO 7.1 — Crear launcher de escritorio con pywebview
**Archivo:** `installer/desktop_launcher.py`
**Propósito:** Reemplazar `desktop/` (Electron + Node.js):
```python
import webview
import subprocess, threading, sys

def start_backend():
    subprocess.run([sys.executable, "run.py", "--no-browser", "--no-bootstrap"])

threading.Thread(target=start_backend, daemon=True).start()
webview.create_window("JullEditor", "http://127.0.0.1:8000", width=1400, height=900)
webview.start()
```

#### PASO 7.2 — Deprecar directorio `desktop/`
- Mover `desktop/` a `desktop_legacy/`
- Agregar nota en README

#### Criterios de salida Fase 7:
- [ ] `installer/desktop_launcher.py` funcional
- [ ] `desktop/` movido a `desktop_legacy/`
- [ ] Sin dependencias de Node.js/npm en el flujo principal

---

## GUÍA DE INSTALACIÓN EN WINDOWS (para usuario final)

### Método 1: Doble clic (el más simple)
```
1. Descargar el proyecto desde GitHub (ZIP o git clone)
2. Abrir la carpeta del proyecto
3. Hacer doble clic en crear_articulo.bat
4. El .bat automáticamente:
   a. Instala Python 3.12 si no existe (winget o python.org)
   b. Instala dependencias pip
   c. Instala Ollama si falta
   d. Descarga el modelo Granite acorde a tu RAM
   e. Abre JullEditor en el navegador
```

### Método 2: Instalador GUI (v4.0)
```
1. Descargar JullEditor Setup v4.exe
2. Ejecutar el instalador
3. El instalador configura todo automáticamente
4. Acceso directo en el Escritorio
```

### Método 3: Manual (desarrolladores)
```powershell
git clone https://github.com/julljoll/Creador-de-Articulos-Blog-con-Granite.git
cd Creador-de-Articulos-Blog-con-Granite

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e ".[dev]"

# Indexar corpus jurídico (opcional, mejora calidad RAG)
python run.py --index

# Lanzar servidor web
python run.py

# O usar interfaz TUI en terminal
python run.py --tui

# O ejecutar tests
python run.py --test
```

---

## MÉTRICAS DE CALIDAD EDITORIAL

| Métrica | v3.4.0 (actual) | v4.0.0 (meta) | Cómo se mide |
|---|---|---|---|
| Exactitud citas normativas | ~70% | **100%** | Validador literal contra índice |
| Alucinaciones jurisprudenciales | Ocasionales | **0** | Expediente+ponente verificados |
| Estructura científica | Variable | **IMRD/doctrinal completa** | Checklist Agente Crítico |
| Originalidad estilística | Media | Alta | Detector muletillas LLM |
| Tiempo artículo 1500 palabras | ~4 min | <=6 min (con 2 ciclos crítica) | Log del pipeline |
| Score SEO/GEO | ~75 | **>=90** | `seo_geo.py` v2 |
| Tests verdes | 79/79 | **>=120/120** | `python run.py --test` |
| Cobertura de código | ~45% | **>=70%** | `pytest --cov` |

---

## RESTRICCIONES NO NEGOCIABLES

1. **Solo Python** para toda lógica propia (>=3.10). `.bat` = puente de 2 líneas.
2. **Offline-first:** Nada requiere internet salvo modo API explícito.
3. **CPU-only como piso:** Todo funciona en el perfil más bajo (granite 2b).
4. **Venezuela exclusiva en UX;** motor multi-jurisdicción latente.
5. **SemVer estricto:** Cada fase libera versión con tag y CHANGELOG.
6. **Anti-alucinación por diseño:** El redactor solo cita lo del dossier.
7. **Cero lógica de negocio en JavaScript.**
8. **Cero dependencia de Node.js/npm en el flujo principal.**

---

## ARCHIVOS DE REFERENCIA OBLIGATORIOS

Antes de ejecutar cualquier fase, el agente DEBE leer:
1. `.agents/AGENTS.md` — Reglas editoriales y de formato
2. `.agents/skills/blog-seo-writer/SKILL.md` — Formato SEO Blog PDF
3. `.agents/skills/blog-legal-enrichment/SKILL.md` — Corpus jurídico VE
4. `.agents/skills/sentencia-tsj-analyzer/SKILL.md` — Análisis de sentencias
5. `backend/editorial_catalog.py` — Catálogo editorial unificado (fuente de verdad)
6. `backend/version.py` — Versión actual (actualizar en cada fase)
7. `pyproject.toml` — Configuración del proyecto

---

*Documento creado el 2026-10-27. Fuente de verdad para la optimización de JullEditor.*
*Toda modificación a este plan debe mantener los criterios de salida verificables.*
