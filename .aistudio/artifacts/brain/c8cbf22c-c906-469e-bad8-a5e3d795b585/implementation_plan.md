# JullEditor: Estudio Pericial LegalTech, Suite de QA Testing & Publicación Astro

Plan integral para dotar a JullEditor de una suite exhaustiva de pruebas de calidad (QA Testing) para el frontend Astro y colecciones de contenido, integrar un estudio interactivo de redacción pericial y auditoría SEO en tiempo real, y aplicar una experiencia visual **Cyber-Legal Dark OLED** de alto rigor editorial.

---

## Decisiones Críticas y Preferencias del Usuario

> [!IMPORTANT]
> A continuación se detallan las elecciones confirmadas en la fase de clarificación interactiva:
> - **Alcance de QA Testing:** Pruebas integrales de frontend Astro, validación estricta de colecciones de contenido Zod, esquemas Schema.org y contratos editoriales.
> - **Evolución del Concepto Principal:** Integrar directamente en la aplicación web un **Estudio Interactivo de Redacción Pericial** con simulación de inferencia/plantillas dogmáticas y panel de **Auditoría SEO & Jurídica en tiempo real**.
> - **Dirección Estética:** Estilo **Cyber-Legal Dark OLED** con fondos negro puro y pizarra oscura (`#0B0F19`, `#111827`), tipografía serifa editorial de alto contraste para lectura académica y lectura pericial, fuente mono tabular para hashes criptográficos SHA-256 y cero pills decorativas para metadatos.

---

## 1. Visión General y Concepto Principal

### ¿Qué es JullEditor?
**JullEditor** es una estación de trabajo pericial y editorial diseñada para transformar apuntes técnicos, dictámenes periciales y sentencias del Tribunal Supremo de Justicia (TSJ) de Venezuela en **artículos científicos y publicaciones de blog de nivel universitario** optimizadas para buscadores y motores de respuesta IA (Google AI Overviews, Perplexity).

### Problema que Resuelve
1. **Falta de rigor metodológico y alucinaciones:** La redacción pericial y jurídica requiere estricto apego al marco positivo (CRBV, Delitos Informáticos G.O. 37.313, Mensajes de Datos G.O. 37.148, Manual Único de Cadena de Custodia CICPC/MP 2017 e ISO/IEC 27037).
2. **Desconexión entre el generador y el blog:** Los usuarios necesitan no solo leer artículos publicados, sino contar en la misma interfaz con un **laboratorio de autoría**, previsualización en tres formatos (Revista Digital, Markdown Crudo, WordPress/CMS) y un scorecard determinista que audite SEO y calidad jurídica antes de publicar.
3. **Calidad y Robustez de Código:** Garantizar mediante pruebas automatizadas de QA que cada artículo cumpla con el esquema Zod, que los metadatos y enlaces canónicos estén sincronizados y que no existan errores de compilación ni enlaces rotos.

---

## 2. Experiencia de Usuario y Diseño Visual (Cyber-Legal Dark OLED)

### Dirección Estética & Paleta
- **Canvas Principal (60%):** Fondo Dark OLED profundo (`#080C14` y `#0D131F`) con superficie de lectura en pizarra suave (`#111827` y `#1E293B`).
- **Superficies Estructurales (30%):** Bordes milimétricos hairline de 1px (`rgba(255, 255, 255, 0.08)`), divisores sutiles y tarjetas con tipografía nítida sin sombras artificiales.
- **Acentos Periciales (10%):** Acento primario en Azul Cobalto Criptográfico (`#38BDF8`), Verde Hash Verificado (`#10B981`) para evidencias validadas y Ambar Forense (`#F59E0B`) para advertencias o cadenas de custodia.
- **Tipografía**:
  - *Titulares y Portada:* Tipografía serifa de alto contraste (Georgia / Playfair Display) con tracking óptico compensado para dark mode.
  - *Cuerpo de Lectura:* Lectura serifa académica con ancho de lectura restringido a 68ch y altura de línea 1.75 para máxima legibilidad.
  - *Datos Periciales & Hashes:* Tipografía mono tabular (`JetBrains Mono` / `ui-monospace`) con `font-variant-numeric: tabular-nums`.
- **Disciplina Anti-Slop & Zero-Pill:**
  - Cero etiquetas en cápsula (pill badges) en metadatos estáticos. Las etiquetas, fechas, autores y tiempos de lectura se presentan como texto limpio con separadores tipográficos (`·`, `/`).
  - Cero indicadores de pulso decorativos o botones con jerga temática ficticia.

### Contrato de Barra Superior (Top Bar)
Una sola fila limpia de 3 zonas:
```
[ JullEditor · Cyber-Legal ] ── [ Artículos · Estudio Redactor · Auditoría SEO · Taxonomía · RSS ] ── [ [ Nuevo Artículo ] ]
```

### Recorrido de Usuario (User Flows)
1. **Página Principal (Catálogo Editorial `/`):**
   - Marquee pericial con estadísticas reales del corpus de artículos.
   - Buscador reactivo y selector de categorías (Forense & TSJ, Derecho Digital, Ciberseguridad, IA & Datos, Ciencia).
   - Tarjetas de artículos con salience jerárquico, abstract visible y metadatos limpios.
2. **Visor de Artículo Científico (`/[slug]`):**
   - Tarjeta de Abstract bilingüe estructurado (Objetivo, Metodología, Resultados, Conclusiones).
   - Bloque de Evidencia Digital con verificación de hash SHA-256 de muestra y preservación de mismidad.
   - Marco normativo venezolano citado textualmente con llamada procesal.
   - Citas destacadas (Pull Quotes) y referencias bibliográficas en formato APA 7ma edición.
   - Descargo ético profesional obligatorio y metadatos Schema.org `TechArticle` / `ScholarlyArticle`.
3. **Estudio Interactivo de Redacción & Auditoría (`/studio`):**
   - **Paso 1: Ingesta de Fuente:** Pegar notas, cargar plantilla pericial preconfigurada (Forense TSJ, Delitos Informáticos, Cadena de Custodia).
   - **Paso 2: Parámetros Editoriales:** Selección de tema, tono de voz (Doctrinal, Litigante, Revista Arbitrada), extensión objetivo y temperatura de rigor fáctico.
   - **Paso 3: Editor / Visor Multimodo:** Conmutación fluida entre:
     - *Revista Digital:* Renderizado tipográfico idéntico a la publicación final.
     - *Markdown Fuente:* Código con frontmatter YAML editable y botón de copia con 1 clic.
     - *Vista Previa CMS:* Simulación en iframe con estilos universales para WordPress o Sitejet.
   - **Paso 4: Doble Scorecard de Auditoría en Tiempo Real:**
     - *Score SEO Estructural (0-100%):* Longitud de H1, presencia de meta descripción (145-160 caracteres), ritmo de encabezados H2/H3, FAQ estructurada y Schema.org.
     - *Score Calidad Jurídica & GEO 2026 (0-100%):* Respuesta Answer-First, descargo ético profesional, mención a normativas clave (CRBV, G.O. 37.313) y ausencia de promesas engañosas.
4. **Consola de QA Testing & Validación (`/qa`):**
   - Suite de pruebas de validación automatizada en el cliente que ejecuta:
     - Test de Contrato de Frontmatter Zod (todos los artículos en `src/content/blog/`).
     - Test de Microdatos Schema.org (validación de JSON-LD).
     - Test de Integridad de Slugs y Rutas.
     - Test de Rendimiento de Renderizado y Tiempos de Carga.
     - Informe de resultados descargable en JSON / Markdown.

---

## 3. Decisiones Técnicas y Arquitectura

```
┌────────────────────────────────────────────────────────────────────────┐
│                        JULL EDITOR WORKSPACE                           │
├──────────────────────────────────────┬─────────────────────────────────┤
│          ASTRO STATIC BLOG           │       STUDIO & QA ENGINE        │
│    (src/pages/, src/content/blog/)   │    (src/pages/studio.astro)     │
│                                      │    (src/pages/qa.astro)         │
├──────────────────────────────────────┼─────────────────────────────────┤
│ • Colecciones de Contenido (Zod)     │ • Motor de Redacción Reactivo   │
│ • Rutas Dinámicas [slug].astro       │ • Parser Markdown con Callouts  │
│ • Taxonomía /tags, /tags/[tag]       │ • Doble Auditoría SEO/GEO 2026  │
│ • Feed RSS (/rss.xml) & Sitemap      │ • Suite de QA Testing en Cliente│
│ • Layouts Base Cyber-Legal OLED      │ • Exportador Astro/MD/WP/JSON   │
└──────────────────────────────────────┴─────────────────────────────────┘
```

### Decisiones de Arquitectura
1. **Unificación en la Aplicación Astro:** En lugar de mantener una interfaz vanilla desactualizada y un blog separado, Astro aloja tanto el blog de publicación estática como el estudio interactivo de redacción (`/studio`) y la suite de pruebas (`/qa`), logrando un ecosistema 100% coherente que corre en Node.js 22 en el puerto 3000.
2. **Client-Side Islands para el Estudio y QA:** Las herramientas interactivas (el editor, el analizador SEO y la suite de QA) se implementan como componentes modulares TypeScript ejecutados en el cliente sin requerir backend adicional para la auditoría, con almacenamiento reactivo en `localStorage`.
3. **Compatibilidad Estricta con Content Collections:** Todo contenido creado o exportado en el estudio cumple al 100% con el esquema Zod de `src/content.config.ts`, permitiendo copiar o guardar directamente nuevos artículos para compilación estática.
4. **Automatización de QA:** Se implementan pruebas tanto a nivel de build (`tsc --noEmit`, `astro build`) como en tiempo de ejecución en la página `/qa` para verificar la salud de los datos.

---

## 4. Plan de Ejecución Paso a Paso

### Fase 1: QA Testing & Corrección de Colecciones y Esquemas
- Auditar y validar todos los artículos `.md` existentes en `src/content/blog/`.
- Verificar que los campos obligatorios del esquema Zod (`title`, `description`, `pubDate`, `author`, `slug`, `tags`, `category`, `readingTime`) estén correctamente estructurados sin advertencias.
- Crear script y página interactiva `/qa` con tests deterministas para:
  - Validador de frontmatter Zod de cada artículo.
  - Validador de unicidad de slugs y correspondencia de rutas.
  - Validador de etiquetas Schema.org en el layout.
  - Validador de enlaces canónicos y meta descriptions.

### Fase 2: Rediseño Visual Cyber-Legal Dark OLED
- Actualizar `blog/public/styles/global.css` con la paleta Dark OLED, tipografía de revista académica, variables CSS semánticas y diseño responsive fluido.
- Eliminar pills decorativas y reemplazar metadatos con tipografía limpia y separadores sutiles.
- Refactorizar `Base.astro` con la barra de navegación de 3 zonas (`Top Bar Contract`), enlaces de navegación accesibles y pie de página institucional.
- Enriquecer la maquetación de artículos (`[slug].astro`) con tarjetas de abstract, callouts doctrinales, tablas estilizadas y bloques de código para evidencias digitales.

### Fase 3: Estudio Interactivo de Redacción y Auditoría SEO (`/studio.astro`)
- Crear la página del Estudio Editorial con:
  - Selector de plantilla pericial (Ciberseguridad & Delitos Informáticos, Cadena de Custodia ISO 27037, Análisis de Sentencia TSJ, Doctrina LegalTech).
  - Editor de texto con sincronización reactiva y estimador de tiempo de lectura.
  - Visor de previsualización en tres pestañas (Revista, Markdown, Código HTML CMS).
  - Scorecard de Doble Auditoría en tiempo real:
    - *Auditoría SEO:* Verificación de H1, meta descripción (longitud óptima 145-160 caracteres), jerarquía H2-H3, conteo de palabras y densidad de palabras clave.
    - *Auditoría Jurídica & GEO 2026:* Presencia de Answer-First, descargo de responsabilidad profesional, marco jurídico venezolano y glosario pericial.
  - Botones de exportación: Copiar Markdown con frontmatter Astro, copiar HTML con inline styles y descargar archivo `.md`.

### Fase 4: Pruebas de Verificación y Compilación
- Ejecutar `tsc --noEmit` y `astro build` para verificar que todas las 13+ páginas compilen sin errores ni advertencias.
- Comprobar que el servidor en el puerto 3000 responda con código HTTP 200 en `/`, `/[slug]`, `/studio`, `/qa`, `/tags` y `/rss.xml`.
- Verificar contraste WCAG AA en todo el esquema Cyber-Legal Dark OLED.
