# Formato editorial de artículos para Astro

Plantilla de redacción para artículos estáticos de investigación jurídica y tecnológica. Completa los campos, elimina las instrucciones entre corchetes y conserva solo las secciones que aporten valor al tema. No inventes fuentes, resultados, credenciales ni conclusiones para llenar el formato.

## Contrato de publicación

El frontmatter debe respetar `frontend/src/content.config.ts` y `backend/astro_publisher.py`:

- `title`: obligatorio, texto de 1 a 200 caracteres.
- `description`: obligatorio, texto de 1 a 170 caracteres. Es un resumen útil para lectores; Google puede mostrar un fragmento distinto y no impone una longitud fija.
- `pubDate`: obligatorio, fecha YAML válida (`AAAA-MM-DD`).
- `updatedDate`: opcional; úsala solo cuando el artículo haya cambiado de forma sustancial.
- `author`: obligatorio, nombre real de la persona autora. El renderer actual lo publica como `Person` en JSON-LD; no uses el nombre de una organización o equipo sin adaptar y probar ese contrato.
- `slug`: opcional; si se declara, usa minúsculas, números y guiones simples (`^[a-z0-9]+(?:-[a-z0-9]+)*$`). Sin `slug`, Astro deriva la ruta del nombre del archivo. Mantén la URL estable y coordina cualquier cambio con una redirección.
- `tags`: obligatorio, entre 1 y 6 textos.
- `category`: texto; puede omitirse y Astro aplica `science_tech`.
- `heroImage`: opcional. Usa una ruta existente y comprueba su tratamiento en el sitio: el frontmatter actual la admite, pero la página de artículo no la muestra ni la incluye en sus datos estructurados.
- `seoKeyword`: opcional, para orientar el tema; no es una instrucción para repetir una frase artificialmente.
- `readingTime`: entero positivo; si se incluye, estima el tiempo de forma razonable.
- `featured` y `draft`: booleanos. Los borradores (`draft: true`) no generan una página de artículo.

No agregues otras claves de frontmatter sin actualizar y probar conjuntamente el esquema Astro y el validador del publicador. El cuerpo puede organizarse libremente; el esquema no exige etiquetas HTML, FAQ ni una longitud determinada.

```yaml
---
title: "Título descriptivo y específico del artículo"
description: "Síntesis fiel de la pregunta, el alcance y el aporte principal del artículo."
pubDate: 2026-11-13
# updatedDate: 2026-11-13
author: "Nombre y apellido de la persona autora"
slug: "titulo-descriptivo-del-articulo"
tags: ["derecho-digital", "investigacion"]
category: "Investigación jurídica"
# heroImage: "/images/articles/imagen-existente.webp"
# seoKeyword: "tema principal, expresado naturalmente"
readingTime: 8
featured: false
draft: true
---
```

## Criterios editoriales, jurídicos y de investigación

1. Define la pregunta que resolverá el texto, para quién es útil y qué aporta más allá de resumir otras publicaciones. Responde la pregunta pronto y distingue hechos, interpretación y opinión.
2. Declara la jurisdicción, materia y fecha de corte. No extrapoles normas de otro país ni presentes derecho comparado como derecho venezolano.
3. Explica brevemente el método y sus límites: corpus consultado, criterios de inclusión, período, herramientas o procedimiento usados y qué no puede concluirse con esos datos. Describe el trabajo que realmente se hizo.
4. Sustenta las afirmaciones relevantes con fuentes identificables. Prioriza textos oficiales vigentes, gacetas, decisiones judiciales y documentos originales; usa doctrina y estudios secundarios con atribución clara. Incluye artículo o página, órgano, número/identificador, fecha y enlace estable cuando estén disponibles.
5. Separa la cita textual de la paráfrasis. Usa comillas para citas literales, identifica autor y localizador y verifica que la cita conserve su contexto. No atribuyas a una sentencia una regla que no contiene.
6. Expón discrepancias, vigencia, reformas, criterios opuestos e incertidumbre cuando sean pertinentes. No describas una regla como universal ni afirmes admisibilidad, nulidad, responsabilidad o resultado judicial sin apoyo suficiente.
7. Solicita revisión especializada cuando el tema o el riesgo lo requiera. Identifica a quien revisó y su alcance solo con su autorización; una nota editorial no sustituye asesoría jurídica para un caso concreto.
8. Protege datos personales y confidenciales. Anonimiza expedientes, evidencia y ejemplos, y confirma que exista autorización para publicar los materiales.

## Criterios SEO para personas y buscadores

- Usa un título único, claro y congruente con el título visible. Incluye el concepto central solo si describe con precisión el contenido; no hay una longitud de título que garantice cómo Google mostrará el resultado.
- Escribe una descripción específica y legible dentro del límite de 170 caracteres del esquema de este proyecto. Google puede generar el fragmento desde el contenido y no garantiza mostrar la descripción.
- Organiza el texto con encabezados descriptivos y jerárquicos. La página ya genera el H1 desde `title`; empieza el cuerpo con H2 y no añadas otro H1.
- Usa el tema principal y sinónimos donde tengan sentido. No persigas densidades, repitas palabras clave ni pongas conceptos en negrita por cuota.
- Enlaza fuentes y trabajos relacionados con texto de enlace informativo. Comprueba que los enlaces funcionen y que los enlaces externos apunten a la fuente citada.
- Conserva el `slug` publicado. El sitio genera canonical y sitemap; configura `PUBLIC_SITE_URL` con el dominio real para evitar canonical con el dominio de ejemplo.
- El sitio genera JSON-LD `BlogPosting` con título, descripción, autor y fechas. No dupliques ni pegues JSON-LD en el cuerpo. Los datos estructurados deben representar contenido visible y verificable; no garantizan resultados enriquecidos ni mejor posicionamiento.

## Plantilla del artículo

La página genera automáticamente el H1 desde `title`, además de la descripción y metadatos comunes. El archivo copiable no debe contener un segundo H1, HTML, JSON-LD, explicaciones al autor ni una envoltura Markdown alrededor de todo el documento. El cuerpo usa Markdown estándar; la plantilla visual actual fluye en tres columnas en pantallas amplias, pero eso no exige etiquetas HTML.

```markdown
---
title: "Título descriptivo y específico del artículo"
description: "Síntesis fiel de la pregunta, el alcance y el aporte principal."
pubDate: 2026-11-13
author: "Nombre y apellido de la persona autora"
slug: "titulo-descriptivo-del-articulo"
tags: ["derecho-digital", "investigacion"]
category: "Investigación jurídica"
seoKeyword: "tema principal, expresado naturalmente"
readingTime: 8
featured: false
draft: false
---

[Lead que presenta la pregunta y responde lo esencial con cautela. Distingue los hechos comprobados del análisis.]

## Pregunta y alcance de la investigación

[Expón el problema, el objetivo, la audiencia, la jurisdicción, la materia y la fecha de corte. Define los términos necesarios.]

## Método y fuentes examinadas

[Describe el método realmente aplicado, el corpus, los criterios de selección y sus límites. Identifica las fuentes primarias y secundarias consultadas.]

## Marco normativo y contexto

[Analiza las disposiciones pertinentes con denominación, número, artículo, gaceta y vigencia comprobados. Cita y enlaza la fuente oficial.]

## Decisiones y evidencia relevante

[Identifica el órgano, número de expediente o decisión, fecha, sala y pasaje pertinente. Resume el criterio sin extenderlo a hechos distintos.]

## Análisis, hallazgos y límites

[Relaciona cada hallazgo con su evidencia y fuente. Expón interpretaciones alternativas e incertidumbres; no concluyas más de lo que permite el método.]

## Conclusiones y aplicación práctica

[Responde la pregunta inicial. Distingue la conclusión jurídica, el resultado técnico y las recomendaciones, e indica sus condiciones y límites.]

## Fuentes y referencias

- [Autor u órgano, título, identificador, fecha y artículo o página](URL oficial)
- [Agrega las fuentes citadas en el cuerpo; elimina las entradas no utilizadas](URL)

## Preguntas frecuentes

### [Pregunta genuina de lectores]

[Respuesta directa, matizada y respaldada por el análisis. Omite la sección si no aporta valor.]

## Autoría y revisión

- **Autor:** [Nombre real y perfil verificable.]
- **Revisión:** [Nombre, especialidad, alcance y fecha; solo si hubo revisión.]
- **Nota:** [Aclaración pertinente sobre alcance informativo y límites, si corresponde.]
```

## Fuentes de referencia

- [Astro: colecciones de contenido](https://docs.astro.build/en/guides/content-collections/) y [rutas estáticas](https://docs.astro.build/en/guides/routing/#static-ssg-mode).
- [Google Search Central: contenido útil y fiable](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [enlaces de título](https://developers.google.com/search/docs/appearance/title-link), [fragmentos y descripciones](https://developers.google.com/search/docs/appearance/snippet), [datos estructurados Article](https://developers.google.com/search/docs/appearance/structured-data/article) y [canonical](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls).
