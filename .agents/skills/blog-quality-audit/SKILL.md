---
name: blog-quality-audit
description: >-
  Audita y califica la calidad editorial, técnica y SEO de los artículos de blog generados con IBM Granite. Evalúa 25 puntos de control de forma offline, valida la estructura Markdown, microdatos Schema.org, densidad de keywords, cumplimiento del marco legal venezolano y genera un reporte cuantitativo del 0 al 100%.
---

# Blog Quality Audit (Auditoría de Calidad Post-Generación)

Este skill permite verificar de forma rigurosa y matemática si un artículo generado cumple con los estándares requeridos por el proyecto antes de su publicación en WordPress o exportación.

## 1. Procedimiento de Auditoría Offline

Para auditar un artículo generado o un archivo Markdown:

```bash
python .agents/skills/blog-quality-audit/scripts/audit_article.py --input "ruta_al_articulo.md"
```

O para evaluar un texto pasado por argumento:
```bash
python .agents/skills/blog-quality-audit/scripts/audit_article.py --text "contenido_del_articulo"
```

## 2. Los 5 Pilares de Evaluación (Scoring del 0 al 100%)

1. **Estructura SERP y Encabezados (25 pts)**:
   - Presencia de H1 único (8-12 palabras).
   - Meta descripción (145-160 caracteres).
   - Tabla de contenidos y subtítulos H2/H3 con extensión controlada (5-9 palabras).

2. **Formato Editorial y Lectura Rápida (20 pts)**:
   - Párrafo Answer-First en las primeras 100 palabras.
   - Caja `📌 Resumen Práctico` y `⚡ Resumen Ejecutivo en 30 Segundos`.
   - Caja `💡 En Palabras Simples`.
   - Conclusiones de párrafo identificables.

3. **Optimización SEO y Palabras Clave (20 pts)**:
   - Densidad de keyword primaria (1.0% a 3.0%).
   - Repetición y presencia de términos resaltados en `**negrita**`.
   - Slug sugerido y cinta de metadatos.

4. **Jurisdicción y Rigor Doctrinal Venezolano (15 pts)**:
   - Mención explícita de leyes venezolanas del corpus autorizado (CRBV, Delitos Informáticos, Infogobierno, Mensajes de Datos).
   - Presencia de la sección `## 🔬 Análisis de Compatibilidad y Prospectiva Tecnológica en Venezuela`.

5. **Microdatos, FAQ y Cierre E-E-A-T (20 pts)**:
   - Sección FAQ con al menos 3 preguntas.
   - Atribución de Derechos de Autor y Fuente de Origen.
   - Sección Sobre el Autor (E-E-A-T) y llamada a la acción (CTA).
   - Bloques Schema.org JSON-LD válidos (`TechArticle` y `FAQPage`).

## 3. Acciones de Corrección

- **Score >= 85%**: Artículo de nivel editorial profesional listo para publicación directa.
- **Score 70-84%**: Requiere ajustes menores (revisar longitud de meta descripción o densidad de negritas).
- **Score < 70%**: Requiere regeneración o edición manual de bloques faltantes.
