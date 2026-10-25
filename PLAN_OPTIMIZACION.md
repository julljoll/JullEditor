# 📋 PLAN DE OPTIMIZACIÓN — JullEditor v4.0
## Redactor Jurídico-Científico de Primer Nivel · 100% Python

**Proyecto:** JullEditor (estación editorial LegalTech offline-first)
**Versión actual:** v3.2.1 → **Objetivo:** v4.0.0 (MAJOR: nueva arquitectura + rupturas de API planificadas, según [SemVer](https://semver.org/))
**Horizonte estimado:** 6 sprints (~12 semanas), priorizado por impacto editorial
**Jurisdicción operativa:** Venezuela 🇻🇪 (exclusiva en la interfaz; motor multi-jurisdicción latente)

---

## 🎯 VISIÓN DEL PRODUCTO v4.0

Convertir JullEditor de un *generador de borradores* en un **redactor jurídico-científico de primer nivel**, capaz de producir artículos que cumplan simultáneamente:

1. **Rigor científico-académico**: estructura IMRD/doctrinal, citación normativa venezolana exacta (CRBV, códigos, gacetas), referencias a jurisprudencia TSJ con expediente y ponente verificables.
2. **Calidad editorial profesional**: prosa sin alucinaciones, coherencia argumentativa, estilo humano indetectable ante patrones genéricos de IA.
3. **Publicabilidad inmediata**: exportación limpia a WordPress/Sitejet con SEO + GEO (Answer Engine Optimization para buscadores conversacionales) ya resueltos.

**Principio rector:** todo el sistema de generación, validación y orquestación se ejecuta en **Python puro**; ningún script auxiliar en Batch/PowerShell/Bash contendrá lógica.

---

## 🔍 DIAGNÓSTICO ACTUAL (línea base v3.2.1)

| Componente | Estado | Brecha frente a "primer nivel" |
|---|---|---|
| `backend/prompts.py` | ✅ Funcional | Prompts de una sola pasada; sin cadena de razonamiento jurídico estructurado (IRAC/FILAC), sin auto-crítica |
| `backend/rag_manager.py` | ⚠️ Básico | Búsqueda léxica/simple sobre corpus; sin embeddings vectoriales ni reranking → recuperación imprecisa de normas |
| Generación | ⚠️ Single-shot | Un solo paso LLM; sin ciclo borrador→revisión→refinamiento (pipeline agéntico) |
| Validación legal | ⚠️ Superficial | Verifica presencia de citas, no su exactitud (número de artículo, gaceta, expediente) |
| Validación SEO/GEO | ✅ Aceptable | Cobertura de palabras clave OK; falta structured data (JSON-LD Article/FAQPage) real |
| GUI web (`frontend/js`) | ⚠️ Fuera de pila Python | Requiere navegador + JS; duplica lógica de prompts/validación en dos lenguajes |
| `crear_articulo.bat` / `start.bat` | ⚠️ Puentes vacíos | Correcto hoy, pero la experiencia terminal puede ser superior con TUI Python |
| Tests | ⚠️ Parciales | Suite existe pero marca defectuosa en `test_cli_generator`; cobertura de RAG/prompts baja |
| Modelos | granite3.3:8b/2b CPU | Suficiente en CPU; margen grande si se añade modo híbrido con API opcional |

---

## 🏗️ ARQUITECTURA OBJETIVO v4.0 (todo Python)

```
Usuario ──► TUI Python (Textual)  ◄── espejo 1:1 del flujo .bat actual
              │
              ▼
        core/pipeline.py          ← orquestador agéntico (LangGraph-free, Python puro)
              │
   ┌──────────┼───────────┬──────────────┐
   ▼          ▼           ▼              ▼
analista   investigador  redactor      crítico        ← 4 agentes internos (prompts especializados)
(sentencia) (RAG vectorial)(borrador)  (auto-revisión IRAC + anti-alucinación)
   │          │           │              │
   └────► backend/rag/vector_store.py (ChromaDB + embeddings sentence-transformers)
              │
              ▼
        validadores (legal_ve.py, seo_geo.py) ──► exportadores (wordpress, markdown, docx-vía-Python)
              │
              ▼
        Articulos Generados/ + auditoría JSON por artículo
```

**Regla de lenguaje:** Python ≥3.11 en el 100% del código propio. Los `.bat` restantes son únicamente dos líneas de puente (`python run.py`). La HTML/CSS de la web queda como capa de presentación estática opcional; **toda la lógica migra a Python** (API FastAPI sirve también una GUI renderizada desde Python con Jinja2 + htmx mínimo o, preferentemente, la TUI Textual como interfaz principal).

---

## 📦 FASES Y TAREAS

### FASE 1 — Núcleo 100% Python y limpieza total (Sprint 1) · `v3.3.0`
- [ ] **TUI principal con Textual**: pantalla de 3 pasos espejo de index.html (especialidad → tono VE/jurisdicción → ajustes avanzados) + streaming del token en vivo. Reemplaza funcionalmente a la GUI JS como interfaz canónica.
- [ ] Migrar `frontend/js/app.js` (lógica de prompts, conteo SEO, exportación Sitejet) a módulos Python: `backend/frontend_logic.py` consumido por FastAPI/Jinja2. El navegador deja de contener lógica de negocio.
- [ ] `crear_articulo.bat` y `start.bat`: reducir a puente mínimo sin lógica (ya casi cumple; auditar bucles residuales).
- [ ] Corregir suite de tests (`test_cli_generator`, fixtures/marks) y elevar cobertura mínima a 70 % con `pytest --cov`.
- [ ] Añadir `ruff` + `mypy` al pre-commit y a `run.py --test`.
- **Criterio de salida:** `grep -r "function\|=>" backend/*.py frontend/js/*.js` → cero archivos JS con lógica de negocio; toda prueba verde.

### FASE 2 — RAG vectorial jurídico venezolano (Sprint 2) · `v3.4.0`
- [ ] Embeddings locales: `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`, optimizado CPU) sobre corpus `Informacion_docling_rag/Venezuela` (~96 fuentes: CRBV, CC, CPC, COIP, Leyes especiales, Gacetas, sentencias TSJ/SCP).
- [ ] `vector_store.py` con ChromaDB (persistido en `.julleditor_db/`): chunking inteligente por **artículo normativo / ratio decidendi** (no por tokens fijos).
- [ ] Híbrido BM25 (`rank_bm25`) + denso, con **reranker** ligero; metadatos obligatorios: norma, artículo, gaceta, fecha, tribunal, expediente, ponente.
- [ ] Comando `python run.py --index` para (re)construir el índice desde el corpus.
- **Criterio de salida:** recall@5 ≥ 0.85 en set de 30 consultas jurídicas estándar (p. ej., "caducidad acción reivindicatoria", "recurso de interpretación constitucional").

### FASE 3 — Pipeline agéntico de 4 etapas (Sprint 3-4) · `v3.5.0`
- [ ] **Agente Analista**: extrae de la sentencia/hechos: problema jurídico, normas aplicables, ratio, obiter dicta, votos salvados.
- [ ] **Agente Investigador**: consulta el RAG y arma el *dossier* normativo-jurisprudencial con citas verificadas.
- [ ] **Agente Redactor**: escribe por secciones (IMRD o doctrinal según especialidad) inyectando solo el dossier (anti-alucinación por contexto cerrado).
- [ ] **Agente Crítico**: revisión adversarial con rúbrica de 10 puntos (exactitud de citas, coherencia IRAC, conectores académicos, ausencia de muletillas IA, densidad informativa); genera patch-notes y dispara reescritura (máx. 2 ciclos, configurable).
- [ ] Streaming SSE/TUI del pipeline completo con indicador de etapa.
- **Criterio de salida:** en benchmark interno de 10 sentencias SCP reales, el 100 % de las citas normativas del borrador final deben existir literalmente en el corpus (hoy ~70 %).

### FASE 4 — Validación jurídica de primer nivel (Sprint 4-5) · `v3.6.0`
- [ ] `legal_validator_v2.py`: verificación **literal** de cada cita contra el índice (número de artículo, texto parcial, vigencia) y de sentencias (expediente + ponente + Sala + fecha) contra `Jurisprudencias/`.
- [ ] Detección de normas derogadas/inconstitucionales (lista negra mantenida: p. ej. reformas y leyes sustituidas) con sugerencia automática de la norma vigente.
- [ ] Formato de citación normalizado: estilo revista jurídica venezolana (Revista de Derecho Público / Facultad de Ciencias Jurídicas UCV) parametrizable.
- [ ] Informe de auditoría por artículo (`auditoria_<slug>.json`) con semáforo: 🔴 cita inexistente · 🟡 cita imprecisa · 🟢 verificada.
- **Criterio de salida:** cero artículos publicables exportados con semáforo rojo.

### FASE 5 — SEO + GEO de élite (Sprint 5) · `v3.7.0`
- [ ] GEO real: generación automática de bloque FAQ (schema.org/FAQPage), respuestas de ≤48 palabras a preguntas conversacionales ("¿cuánto prescribe la acción…?"), definiciones destacables (featured-snippet ready).
- [ ] JSON-LD `Article` + `LegalService` + breadcrumbs emitidos en la exportación WordPress.
- [ ] Análisis de legibilidad jurídica específica español-VE (flesch-silabas adaptado, índice de nominalización, longitud media de período jurídico objetivo: 25-35 palabras).
- [ ] Sugeridor de cluster semántico desde el corpus (enlaces internos entre artículos generados: `related_articles.py`).
- **Criterio de salida:** score SEO/GEO ≥ 90 en el validador interno para el 100 % de artículos exportados.

### FASE 6 — Salida profesional y modelos (Sprint 6) · `v4.0.0`
- [ ] Exportación `.docx` con plantilla de revista jurídica vía `python-docx` (portada, sumario, notas al pie reales, bibliografía APA-legal).
- [ ] Plantilla LaTeX (`pylatex`) opcional para revistas indexadas.
- [ ] Modo híbrido de modelo: `granite3.3:8b` (por defecto, offline) + proveedor opcional OpenAI-compatible (`--api-base/--api-key`) con degradación automática a local si falla.
- [ ] Perfilado de hardware extendido: selección dinámica granularidad MoE/quantización según RAM/AVX detectados.
- [ ] Documentación final: README v4, guía del redactor (cómo usar el pipeline), CHANGELOG consolidado, release notes GitHub `v4.0.0`.

---

## 🧪 MÉTRICAS DE CALIDAD EDITORIAL (definición de "primer nivel")

| Métrica | Hoy (est.) | Meta v4.0 | Cómo se mide |
|---|---|---|---|
| Exactitud de citas normativas | ~70 % | **100 %** | Validador literal contra índice |
| Alucinaciones jurísprudenciales | Ocasionales | **0** | Expediente+ponente verificados |
| Estructura científica | Variable | **IMRD/doctrinal completa** | Checklist del Agente Crítico |
| Originalidad estilística | Media | Alta | Detector de muletillas LLM + variación de períodos |
| Tiempo artículo 1500 palabras | ~4 min | ≤6 min (incluye 2 ciclos de crítica) | Log del pipeline |
| Score SEO/GEO | ~75 | **≥90** | `seo_geo.py` v2 |

---

## 🔒 RESTRICCIONES Y PRINCIPIOS NO NEGOCIABLES

1. **Solo Python** para toda lógica propia (≥3.11). Batch = puente de 2 líneas; JS = solo presentación estática opcional sin reglas de negocio.
2. **Offline-first**: nada puede requerir internet salvo el modo API explícitamente activado.
3. **CPU-only como piso**: todo debe funcionar en el perfil más bajo detectado (granite 2b fallback).
4. **Venezuela exclusiva en UX**; el motor conserva jurisdicciones latentes sin exponerlas.
5. **SemVer estricto**: cada fase libera una versión con tag anotada y CHANGELOG; Fase 6 justifica el salto MAJOR por cambios de API internos.
6. **Anti-alucinación por diseño**: el redactor solo puede citar lo que el investigador le entregó con anclaje documental.

---

## 🗓️ RESUMEN DE HOJA DE RUTA

| Versión | Sprint | Entrega clave |
|---|---|---|
| 3.3.0 | 1 | TUI Textual + lógica JS migrada a Python + tests verdes |
| 3.4.0 | 2 | RAG vectorial VE (ChromaDB + embeddings + reranking) |
| 3.5.0 | 3-4 | Pipeline agéntico Analista→Investigador→Redactor→Crítico |
| 3.6.0 | 4-5 | Validación jurídica literal + auditoría con semáforo |
| 3.7.0 | 5 | SEO/GEO de élite (FAQ schema, JSON-LD, clusters) |
| **4.0.0** | 6 | DOCX/LaTeX editorial, modo híbrido de modelos, docs finales |

---

*Documento vivo: actualizar tras cerrar cada fase. Creado el 2026-10-25 sobre la base v3.2.1.*
