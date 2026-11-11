---
name: blog-source-analyzer
description: >-
  Preprocesa, limpia y analiza textos o notas suministradas para redactar artículos de blog optimizados con IBM Granite e IBM Data Prep Kit (DPK). Permite decidir de forma eficiente el método de ingesta (texto pegado directo vs URL), anonimiza PII sensible venezolana, audita calidad editorial con PyArrow, cuenta palabras y prepara el payload listo para inferencia local offline.
---

# Blog Source Analyzer (Analizador Inteligente de Fuentes con IBM Data Prep Kit)

Este skill define el procedimiento profesional para la ingesta y preparación de información antes de alimentar al modelo local IBM Granite, incorporando la arquitectura enterprise de **IBM Data Prep Kit (DPK)** y **Apache Arrow**.

## 1. Decisión de Ingesta: ¿Archivo Docling .MD, Texto Pegado o URL?

Aplica la siguiente matriz de decisión técnica:

| Escenario | Método Recomendado | Razón Técnica |
| :--- | :--- | :--- |
| **Archivos procesados por Docling (PDFs, docs)** | **Subir Archivo .MD (Docling)** | Extrae el H1, estructura secciones, detecta la temática y opera con **0ms de latencia offline**. |
| **Sin conexión a Internet (Offline)** | **Docling .MD / Texto Pegado** | El modelo LLM y Ollama son locales; no requieren web. La URL fallará si no hay red. |
| **Notas rápidas, borradores o transcripciones** | **Texto Pegado Directo** | Evita latencias innecesarias de scraping y permite filtrar ruido previo. |
| **Artículos con datos personales o sensibles** | **Texto Pegado + DPK PII Redactor** | IBM DPK enmascara automáticamente Cédulas (V/E), RIF, teléfonos, correos y cuentas bancarias. |
| **Artículos detrás de paywalls o JS pesados** | **Texto Pegado / Archivo .MD** | Los scrapers automáticos suelen ser bloqueados por Cloudflare/Paywalls. |
| **Artículo público online con internet activo** | **URL + Extracción Scraper** | Extrae automáticamente metadatos OpenGraph, autor y fecha original. |

> [!TIP]
> Si procesaste documentos con **Docling** (`Informacion_docling_rag/` o PDFs externos), simplemente **arrastra el archivo `.md` a la zona de carga**. El sistema extraerá automáticamente el título, limpiará artefactos de paginación y seleccionará la temática adecuada.

---

## 2. Pipeline IBM Data Prep Kit (DPK) para Fuentes

El preprocesamiento se ejecuta mediante un pipeline componible de transformaciones Apache Arrow:

1. **`DoclingIngestTransform`**: Mapea Markdown/JSON a tablas estructuradas Apache Arrow (`pyarrow.Table`).
2. **`HeaderCleanerTransform`**: Elimina avisos de cookies, suscripciones, pie de páginas, marcas de paginación OCR y mojibake Windows-1252.
3. **`PIIRedactorTransform`**: Detecta y anonimiza información personal identificable conforme al marco legal venezolano:
   - Cédulas de Identidad (`[CÉDULA_PROTEGIDA]`)
   - RIF (`[RIF_PROTEGIDO]`)
   - Números telefónicos nacionales (`[TELÉFONO_PROTEGIDO]`)
   - Correos electrónicos (`[EMAIL_PROTEGIDO]`)
   - Cuentas bancarias de 20 dígitos (`[CUENTA_BANCARIA_PROTEGIDA]`)
4. **`ExactDedupTransform`**: Detección de duplicados mediante hashing criptográfico SHA-256.
5. **`DocQualityTransform`**: Evalúa la densidad lexical, ratio de símbolos, legibilidad y calcula el `quality_score` y la bandera `is_ready_for_granite`.

---

## 3. Ejecución del Preprocesador

Ejecuta el script local [preprocess_source.py](./scripts/preprocess_source.py):

```bash
# Procesar archivo o texto con IBM Data Prep Kit (por defecto con PII redaction y calidad)
python .agents/skills/blog-source-analyzer/scripts/preprocess_source.py --input "ruta_al_archivo_o_texto"

# Ejecutar test sintético con verificación de PII
python .agents/skills/blog-source-analyzer/scripts/preprocess_source.py --test

# Opcional: Desactivar PII o usar motor regex clásico
python .agents/skills/blog-source-analyzer/scripts/preprocess_source.py --input "nota.txt" --no-pii
```

---

## 4. Endpoints API Disponibles en FastAPI

El backend expone directamente el motor IBM Data Prep Kit:

- `POST /api/data-prep/preprocess`: Pipeline completo de preparación de fuente con DPK.
- `POST /api/data-prep/redact-pii`: Anonimización atómica de datos personales sensibles.
- `GET /api/data-prep/corpus-stats`: Métricas y metadatos del corpus legal persistido en Apache Parquet.
- `POST /api/data-prep/index-corpus`: Indexación RAG completa con segmentación semántica y exportación Parquet.
