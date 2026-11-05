---
name: blog-source-analyzer
description: >-
  Preprocesa, limpia y analiza textos o notas suministradas para redactar artículos de blog optimizados con IBM Granite. Permite decidir de forma eficiente el método de ingesta (texto pegado directo vs URL), extrae metadatos clave, cuenta palabras y prepara el payload listo para inferencia local offline.
---

# Blog Source Analyzer (Analizador Inteligente de Fuentes)

Este skill define el procedimiento profesional para la ingesta y preparación de información antes de alimentar al modelo local IBM Granite.

## 1. Decisión de Ingesta: ¿Archivo Docling .MD, Texto Pegado o URL?

Aplica la siguiente matriz de decisión técnica:

| Escenario | Método Recomendado | Razón Técnica |
| :--- | :--- | :--- |
| **Archivos procesados por Docling (PDFs, docs)** | **Subir Archivo .MD (Docling)** | Extrae el H1, estructura secciones, detecta la temática y opera con **0ms de latencia offline**. |
| **Sin conexión a Internet (Offline)** | **Docling .MD / Texto Pegado** | El modelo LLM y Ollama son locales; no requieren web. La URL fallará si no hay red. |
| **Notas rápidas, borradores o transcripciones** | **Texto Pegado Directo** | Evita latencias innecesarias de scraping y permite filtrar ruido previo. |
| **Artículos detrás de paywalls o JS pesados** | **Texto Pegado / Archivo .MD** | Los scrapers automáticos suelen ser bloqueados por Cloudflare/Paywalls. |
| **Artículo público online con internet activo** | **URL + Extracción Scraper** | Extrae automáticamente metadatos OpenGraph, autor y fecha original. |

> [!TIP]
> Si procesaste documentos con **Docling** (`Informacion_docling_rag/` o PDFs externos), simplemente **arrastra el archivo `.md` a la zona de carga**. El sistema extraerá automáticamente el título, limpiará artefactos de paginación y seleccionará la temática adecuada.

---

## 2. Flujo de Preprocesamiento de la Fuente

Cuando se suministre un texto base, sigue estos pasos:

1. **Ejecutar Limpieza y Extracción**:
   Utiliza el script de ayuda local [preprocess_source.py](./scripts/preprocess_source.py):
   ```bash
   python .agents/skills/blog-source-analyzer/scripts/preprocess_source.py --input "ruta_al_archivo_o_texto"
   ```
2. **Filtrar Ruido**:
   - Eliminar avisos de cookies, botones sociales, suscripciones de newsletter y anuncios.
   - Preservar la tesis central, datos estadísticos, nombres propios y citas textuales relevantes.
3. **Determinar la Keyword Primaria**:
   - Identificar el tema medular en 2 a 4 palabras (ej: *Inteligencia Artificial en Delitos Informáticos*, *Cadena de Custodia Digital*).
4. **Detectar Idioma de Origen**:
   - Si el texto original está en inglés u otro idioma, marcarlo para traducción conceptual completa al español durante la redacción.
5. **Estructurar el Payload**:
   Asegurar que el texto resultante tenga suficiente contexto (mínimo 150-300 palabras) para que Granite desarrolle un artículo con profundidad técnica.
