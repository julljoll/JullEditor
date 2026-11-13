# Plan de Reorientación — JullEditor → Estación de Redacción para Blog Astro Estático

> **Estado:** COMPLETADO AL 100% · EN PRODUCCIÓN (v4.0.0)  
> **Lanzador Local Canónico:** `ejecutar_local.bat`  
> **Objetivo cumplido:** La aplicación opera con una interfaz **Astro unificada** (`frontend/`) para el Blog y el Studio, alimentada por un backend **Python (FastAPI)** y **Ollama local (IBM Granite 3.3)**, con persistencia directa en colecciones de contenido de Astro y `Articulos Generados/`.

---

## 1. Situación Actual (Análisis del Repo)

| Componente | Estado actual | Destino en el nuevo plan |
|---|---|---|
| `backend/app.py` (FastAPI, SSE, Ollama) | ✅ Completo: generación streaming, scraper, RAG, SEO, exportadores Astro | ✅ **Se conserva** como núcleo de redacción |
| `backend/exporters/astro_exporter.py` + `astro_compiler.py` | ✅ Genera `.md` con frontmatter compatible con Content Collections | ✅ **Se conserva y potencia** (canal principal de salida) |
| `backend/rag_manager.py` (`ASTRO_READY_DIR`) | ✅ Guarda artículos en `data/articles_generated/astro_ready/` | ✅ **Se conserva**: será el puente de entrega al blog |
| Exportadores WordPress/Elementor/Sitejet | ✅ Existen (`legal_profiles`, `sitejet-lab.html`) | ❌ **Se retiran** (fuera de alcance) |
| TUI (`textual`), CLI, desktop (Tauri) | ✅ Existen | ⚠️ **Opcionales/legacy**: no se desarrollan más |
| `frontend/` (HTML+CSS+JS vanilla servido por FastAPI) | ✅ SPA artesanal | ❌ **Se reemplaza por un estudio Astro** |
| Ramas Git | ✅ Solo `main` | ✔️ Se mantiene flujo monorama |

**Flujo que se quiere lograr:**

```
[Estudio Astro (redacción)] --HTTP/SSE--> [FastAPI Python + Ollama]
        .md + imágenes --> data/.../astro_ready/ --copia--> [blog/ (Astro estático)] --astro build--> dist/ (HTML puro)
```

Dos roles claros de Astro:
- **`studio/`**: interfaz de autoría (puede correr en dev-mode contra la API Python).
- **`blog/`**: sitio **100% estático** (`output: 'static'`), consume solo los `.md` de las colecciones de contenido. No necesita Python en producción.

---

## 2. Fase 0 — Decisiones y Preparación (0.5 día)

1. Definir estructura de monorepo final:
   ```
   /workspace
   ├── backend/            # Python/FastAPI (intocable como motor de redacción)
   ├── studio/             # Frontend Astro: estación de redacción (reemplaza frontend/)
   ├── blog/               # Sitio Astro estático (producto final publicable)
   ├── docs/               # Documentación (este plan, design tokens)
   └── scripts/            # sync/publish helpers
   ```
2. Decidir integración Studio→Blog: **opción recomendada = filesystem** (`astro_ready/` → `blog/src/content/blog/`). Sin base de datos: los `.md` son la única fuente de verdad.
3. Fijar versión: Astro ≥ 5.x, `@astrojs/rss`, `@astrojs/sitemap`, TypeScript estricto.

### Criterios de salida (DoD Fase 0)
- [ ] Estructura de carpetas acordada y rama única `main` confirmada.

---

## 3. Fase 1 — Backend Python: Contraer a "Solo Redacción + Export Astro" (2–3 días)

### 3.1 Quitar funcionalidad fuera de alcance
- Eliminar endpoints y módulos de WordPress/Elementor/Sitejet (`sitejet-lab.html`, perfiles CMS legacy en `seo_validator/legal_profiles` que emitan HTML inline para esos builders).
- Servir el frontend vanilla desde FastAPI → **desactivar** `StaticFiles`/`FileResponse` de `frontend/` (el Studio Astro corre en su propio dev server, puerto 4321).
- Mantener CORS para `http://localhost:4321`.

### 3.2 Endpoints objetivo (API canónica)
| Método | Ruta | Función |
|---|---|---|
| POST | `/api/generate-stream` | Redacción con IA vía SSE (se conserva) |
| POST | `/api/stop-generation` | Cancelar generación |
| POST | `/api/save-generated-article` | Guarda `.md` + versión astro_ready con frontmatter |
| GET | `/api/articles-history` | Lista de borradores/publicados |
| GET | `/api/articles-history/{filename}` | Contenido de un artículo |
| POST | `/api/seo-audit` | Auditoría SEO previa a publicar |
| POST | `/api/scrape` / `/api/parse-docling-md` / `/api/extract-sentencia` | Ingesta de fuentes para redactar |
| POST | `/api/generate-header-image` | Imagen 16:9 del artículo |
| **NUEVO** | POST `/api/export/publish` | Copia el `.md` de `astro_ready/` a `blog/src/content/blog/` (+ sus imágenes a `blog/src/assets/images/`) |
| **NUEVO** | GET `/api/export/drafts` | Estado de publicación (borrador / publicado / desincronizado) |

### 3.3 Contrato de frontmatter (garantizar compatibilidad Content Collections)
```yaml
---
title: "…"
title_en: "…"          # bilingüe (ya lo genera el exporter)
description: "≤160 chars"
pubDate: 2026-11-05
author: "…"
tags: [ciberseguridad, cadena-de-custodia]
categories: ["Forense Digital"]
heroImage: "/images/articles/<slug>.webp"
draft: false
readingTime: 8
lang: es
---
```
- Validar en `astro_exporter.py` que **nunca** se emitan campos no declarados en el esquema Zod del blog (y viceversa: el esquema debe cubrir todo lo generado).

### Criterios de salida
- [ ] `pytest -q` verde tras eliminar rutas legacy.
- [ ] Un artículo generado por `/api/generate-stream` queda en `astro_ready/` con frontmatter válido según el esquema del blog.

---

## 4. Fase 2 — `blog/`: Sitio Astro Estático (2–3 días)

1. `npm create astro@latest blog` → plantilla **Blog** o minimal, JavaScript/TS, **sin integraciones de servidor** (`output: 'static'`).
2. **Content Collection** `src/content/blog/` con esquema:
   ```ts
   // src/content.config.ts
   import { defineCollection, z } from 'astro:content';
   const blog = defineCollection({
     type: 'content',
     schema: z.object({
       title: z.string(), title_en: z.string().optional(),
       description: z.string().max(170), pubDate: z.coerce.date(),
      author: z.string(), tags: z.array(z.string()).default([]),
       categories: z.array(z.string()).default([]),
       heroImage: z.string().optional(), draft: z.boolean().default(false),
       lang: z.enum(['es','en']).default('es'), readingTime: z.number().optional(),
     }),
   });
   export const collections = { blog };
   ```
3. Páginas: `/` (listado paginado), `/blog/[slug]/` (layouts con `prose` + tokens de diseño de `docs/design_tokens.md`), `/tags/[tag]/`, `/about`, RSS (`@astrojs/rss`), sitemap (`@astrojs/sitemap`), JSON-LD `Article` (aprovecha el SEO que ya inyecta el backend).
4. Configurar `image service` local + `webp/avif` automático para `heroImage`; servir imágenes desde `src/assets` o `public/images/articles`.
5. **Preview sin backend:** script `npm run sync:articles` que copia `../backend/data/articles_generated/astro_ready/*.md` → `src/content/blog/` (idempotente, ignora `draft: true` en build de producción).
6. Publicación: `astro check && astro build` → subir `dist/` a Netlify/Cloudflare Pages/GitHub Pages (CI opcional con GitHub Action).

### Criterios de salida
- [ ] `astro build` produce `dist/` 100% estático (sin `_server-islands`, sin functions).
- [ ] Lighthouse ≥ 95 (Performance/SEO/Best Practices/Accessibility).
- [ ] Los `.md` generados por el backend se renderizan sin errores de esquema.

---

## 5. Fase 3 — `studio/`: Frontend Astro de Redacción (3–4 días)

El Studio **no es el blog**: es la herramienta de autoría. Como Astro es estático por naturaleza, la interactividad se resuelve así:

1. Arquitectura: página Astro con **islas de componentes** (elegir UNA opción y justificarla en PR):
   - **Recomendada: Preact islands** (`@astrojs/preact`) — mejor ergonomía para el editor reactivo (estado de streaming SSE, previsualización, historial). Alternativa ligera: `<script>` + web components vanilla si se quiere cero framework.
2. Vistas del Studio:
   - **Redacción:** formulario (tema, perfil jurídico, modelo Granite 2B/8B, temperatura) → consola SSE con texto en vivo (mismo contrato de `/api/generate-stream`).
   - **Editor/Revisión:** textarea con Markdown, panel de auditoría SEO (`/api/seo-audit`), vista previa renderizada con el *mismo* pipeline de remark que usará el blog (importar el layout del blog o duplicar estilos `prose`).
   - **Historial:** lista desde `/api/articles-history`, filtros por estado (borrador / astro_ready / publicado).
   - **Publicación:** botón "Publicar en blog" → `/api/export/publish`; muestra diff de qué archivos se copiarán.
3. Dev: `astro dev` en `:4321` con proxy a FastAPI `:8000` (`vite.server.proxy['/api']`) → sin problemas de CORS.
4. Migrar los tokens de diseño (`docs/design_tokens.md`) a variables CSS compartidas entre Studio y Blog (paquete interno o symlink a `styles/tokens.css`).

### Criterios de salida
- [ ] Redactar → auditar → guardar → publicar completado íntegramente desde el navegador.
- [ ] El `frontend/` vanilla queda obsoleto y se archiva/elimina.

---

## 6. Fase 4 — Integración, Pruebas y Limpieza (2 días)

1. **Tests:**
   - Backend: pytest para `/api/export/publish` (copiado correcto, rechazo de slug duplicado, manejo de imágenes huérfanas). Test de contrato frontmatter↔esquema Zod (fixture `.md` → parsea con el schema).
   - Blog: `astro check` en CI + snapshot de build.
2. **Scripts de un comando** (Makefile o `justfile`):
   ```
   make dev      # ollama check + uvicorn :8000 + astro dev studio :4321
   make publish  # save article -> copy to blog -> astro build
   make site     # astro build blog -> dist/
   ```
3. **Limpieza del repo:**
   - Borrar `frontend/`, `desktop/` (si no se usa), `sitejet-lab.html`, laboratorios Sitejet del README.
   - Actualizar `README.md`: nuevo diagrama de arquitectura, quitar badges/secciones de multi-CMS.
   - Añadir `.gitignore` para `blog/dist/`, `blog/.astro/`, `studio/dist/`, `node_modules/`.
   - Decidir si `blog/src/content/blog/` se versiona (recomendado: **sí**, el blog es el archivo público; `astro_ready/` sigue ignorado).
4. **Seguridad/higiene:** mantener SSRF guard del scraper, límites de tamaño de payload, y validar rutas de destino en `/api/export/publish` (path traversal).

### Criterios de salida
- [ ] Flujo end-to-end demostrado: tema → artículo IA → edición → publicar → `astro build` → HTML estático servible.
- [ ] Suite de tests verde, README actualizado, repo sin código muerto.

---

## 7. Hoja de Ruta Resumida

| Semana | Entregable |
|---|---|
| S1 | Fase 0 + Fase 1 (backend contraído, API canónica, publish endpoint) |
| S2 | Fase 2 (blog estático funcionando con artículos reales de `astro_ready/`) |
| S3 | Fase 3 (Studio Astro: redacción SSE + publicación) |
| S4 | Fase 4 (tests, scripts, limpieza, despliegue del blog) |

## 8. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Frontmatter generado diverge del esquema Zod del blog | Test de contrato automatizado (Fase 4.1); un único lugar donde se construye el YAML (`astro_exporter.py`) |
| Streaming SSE difícil de integrar en Astro (estático) | Islas cliente (`client:load`) — el resto de la página sí es estática |
| Imágenes huérfanas o duplicadas al publicar | `/api/export/publish` idempotente por slug + reporte de huérfanas |
| Pérdida de funciones legacy (WordPress/Tauri) al borrarlas | Retiro en commits separados y etiquetados; el historial Git conserva todo |
| Ollama ausente/模型 caído | `/api/health` ya reporta; Studio muestra banner de estado y modo "solo edición manual" |
