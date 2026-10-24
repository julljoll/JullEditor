# Reglas Globales de Redacción Editorial y LegalTech (Modo Offline-First)

Este espacio de trabajo está diseñado para operar como una estación pericial de redacción de artículos de blog técnicos, jurídicos y de ciberseguridad, optimizado para funcionar **100% de manera local y offline** utilizando el modelo local **IBM Granite 3.3** a través de **Ollama**.

## 1. Principio Fundamental de Entrada (Archivos Docling .MD / Texto Pegado > URLs)

1. **Prioridad Absoluta a Docling .MD y Texto Pegado**:
   - En entornos locales o sin conexión a internet, la entrada principal para crear un artículo debe ser **cargar directamente el archivo `.md` estructurado desde Docling** o **pegar el texto/notas** en el campo fuente.
   - La ingesta de archivos Markdown de Docling permite extraer títulos limpios, estructurar secciones y clasificar temáticas sin fricción y con **0ms de latencia de red**.
   - **No depender del scraper web** cuando se trabaje offline o cuando el usuario ya disponga del material base.
   - Si se incluye una URL, se debe tratar principalmente como un **metadato de atribución y derechos de autor (`source_url`)**, no como una dependencia operativa obligatoria.

2. **Cero Alucinación e Invención de Datos**:
   - Reinterpretar el texto con vocabulario editorial propio en español técnico pero **preservando invariablemente la veracidad, cifras, citas y conclusiones del artículo original**.
   - No inventar estadísticas ni nombres no presentes en la fuente.

## 2. Parámetros de Inferencia y Rendimiento Local (CPU/GPU)

1. **Modelo Predeterminado**: `granite3.3:8b` (o `granite3.3:2b` para equipos con recursos ajustados).
2. **Context Window & Tokens**: Mantener `num_predict` entre 3000 y 4096 tokens para asegurar respuestas completas sin saturar la memoria RAM.
3. **Temperatura**: Usar `0.7` para redacción equilibrada o `0.3-0.5` para síntesis legal y técnica estricta.

## 3. Estándar de Salida Editorial (Formato SEO Blog PDF)

Todo artículo generado debe cumplir con la estructura canónica del proyecto:
- **Título H1**: 8 a 12 palabras (50-65 caracteres) con la palabra clave primaria.
- **Meta Descripción**: 145 a 160 caracteres contigua bajo el H1.
- **Tabla de Contenidos**: Con anclas `#slug-de-seccion`.
- **Párrafo Answer-First**: Primeras 100 palabras responden directamente con la keyword en **negrita**.
- **Caja de Resumen Práctico**: `> **📌 Resumen Práctico de la Fuente Original:**`.
- **Caja 30 Segundos**: `> **⚡ Resumen Ejecutivo en 30 Segundos:**`.
- **Párrafos Controlados**: 3 a 4 oraciones (45 a 65 palabras) por párrafo.
- **Keywords en Negrita**: Resaltado constante de términos clave a lo largo del texto.
- **Conclusión de Párrafo**: `**Conclusión del párrafo:**` al cierre de puntos clave.
- **Marco Legal Exclusivo**: Citar solo el corpus legal venezolano autorizado (`Informacion_docling_rag`) y estándares ISO/NIST.
- **Sección de Compatibilidad en Venezuela**: Análisis de infraestructura, gobernanza CNTI/Infogobierno y adopción real.
- **FAQ con 3 Preguntas**: Formato P: / R: claro y directo.
- **Derechos de Autor y Atribución**: Cita de la fuente original al pie.
- **Doble Bloque Schema.org JSON-LD**: `TechArticle` (con 15 campos) y `FAQPage`.

## 4. Arquitectura de Persistencia de Artículos (`Articulos Generados/`)

1. **Almacenamiento de Fuentes en `Articulos Generados/inputs/`**:
   - Todo archivo `.md` o `.json` cargado desde la interfaz se persiste automáticamente en `Articulos Generados/inputs/` con timestamp para alimentar la memoria viva local de IBM Granite.
2. **Auto-Guardado Dual de Artículos Terminados en `Articulos Generados/`**:
   - Al finalizar la generación, el backend genera y guarda automáticamente cada artículo en dos formatos simultáneos dentro de `Articulos Generados/`, nombrado directamente con el título del artículo:
     - Formato `.md`: `{Titulo_del_Articulo}.md` con Frontmatter YAML estructurado (título, slug, fecha, tema, palabras, modelo, archivo HTML).
     - Formato `.html`: `{Titulo_del_Articulo}.html` como documento HTML5 autónomo, responsivo y completamente estilizado con diseño Cyber-Legal, Schema.org JSON-LD scripts y reglas de impresión, listo para navegador o publicación.
