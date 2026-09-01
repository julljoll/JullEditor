# Sistema de Diseño: Documento de Tokens Oficiales (USWDS Design Tokens)

Este documento define de forma **exclusiva y taxativa los Tokens de Diseño Oficiales (Design Tokens)** del proyecto **Granite Blog Writer & LegalTech CMS**, fundamentados íntegramente en la normativa base:

👉 **[USWDS (U.S. Web Design System)](https://github.com/uswds/uswds.git)** (Estándares WCAG 2.1 AA/AAA, diseño modular centrado en el usuario, escala tipográfica sistemática, retícula USWDS Grid y espaciado de 8pt / unidades del sistema).

> [!NOTE]
> Este proyecto opera en **Modo Claro Profesional (Light Mode / High Contrast)** bajo los principios de accesibilidad de USWDS. Todos los tokens de texto cumplen ratio mínimo de `4.5:1` sobre fondos claros (WCAG 2.1 AA). La única excepción es el formato imprimible pericial `@media print` en tamaño oficio venezolano (216mm × 330mm).

---

## 1. Principios de Diseño USWDS

1. **Accesibilidad Universal (WCAG 2.1 AA/AAA)**:
   - Ratios de contraste de color mínimos de `4.5:1` para texto estándar y `3:1` para elementos gráficos y encabezados de gran escala.
   - Todos los colores de texto (`--color-primary`, `--color-secondary`, `--color-info`) cumplen ratio ≥ 5:1 sobre los fondos claros.
   - Indicadores de foco de alta visibilidad USWDS (`:focus-visible` de 2px con offset de 2px en tokens de oro/verde).
2. **Sistema de Retícula USWDS Grid**:
   - Estructura modular basada en `grid-container`, `grid-row`, `grid-col-*` y `grid-gap-*` con diseño responsive adaptativo.
3. **Escala de Espaciado Modular USWDS (System Units / 8pt Grid)**:
   - Todo padding, margen y separación se construye estrictamente en múltiplos de unidades USWDS (4px / 8px / 12px / 16px / 24px / 32px / 48px).
4. **Paleta Cyber-Legal Tokenizada en USWDS — Light Mode**:
   - Fondo Base: Crema Técnico Neutro (`#F4F3EE`) y Paneles Blancos (`#FFFFFF` / `#EEEEE8`).
   - Prohibición estricta de azules genéricos en interfaces operativas.
   - Acentos Textuales (WCAG AA): Oro Técnico Oscuro (`#8A6800`), Verde Técnico Oscuro (`#1A6B1A`) y Lima Técnico Oscuro (`#4A6A00`).
   - Acentos Decorativos (solo fondos/bordes): Oro Vivo (`#FECF06`), Verde Vivo (`#1A9A2A`), Lima Vivo (`#7AB800`).
5. **Tipografía Dual de Alta Legibilidad**:
   - **`font-sans` (USWDS Body Scale):** `'Arial'`, `'Ubuntu'`, `'Segoe UI'`, sans-serif.
   - **`font-mono` (USWDS Code / Data Scale):** `'Consolas'`, `'Fira Code'`, `'Roboto Mono'`, monospace.
6. **Integración con Bootstrap 5 (Local Offline-First)**:
   - Framework base de componentes y retícula: `frontend/css/bootstrap.min.css`.
   - Mapeo de variables Bootstrap (`--bs-primary`, `--bs-body-bg`, etc.) directamente a los tokens USWDS Light Mode para neutralizar los azules genéricos y preservar la estética pericial.
7. **Material Design Icons**:
   - Iconografía: Google Material Symbols Outlined (`font-size: 1rem` a `2.2rem`).
   - Carga desde CDN de Google Fonts. Compatible con modo offline si se cachea localmente.

---

## 2. Paleta de Tokens de Color USWDS

| Token Semántico USWDS | Variable CSS | Valor Hex / Uso WCAG | Uso Semántico en la Interfaz |
| :--- | :--- | :--- | :--- |
| `color.theme.base-lightest` | `--bg-default` | `#F4F3EE` | Fondo general de la aplicación (Crema Técnico Neutro) |
| `color.theme.surface-light` | `--bg-paper` | `#FFFFFF` | Paneles técnicos, tarjetas primarias y controles |
| `color.theme.surface-subtle` | `--bg-surface-dark` | `#EEEEE8` | Área de lectura y visor pericial de artículos |
| `color.theme.primary` | `--color-primary` | `#8A6800` • ratio 5.1:1 | Botones primarios, encabezados H2-H4, estados activos (WCAG AA) |
| `color.theme.secondary` | `--color-secondary` | `#1A6B1A` • ratio 5.4:1 | Títulos H1, validación pericial, estado ONLINE (WCAG AA) |
| `color.theme.accent-warm` | `--color-info` | `#4A6A00` • ratio 5.0:1 | Hipervínculos Markdown autoritativos (WCAG AA) |
| `color.theme.warning` | `--color-warning` | `#B85A00` • ratio 4.6:1 | Advertencias de compliance, procesos en ejecución |
| `color.theme.error` | `--color-error` | `#C0392B` • ratio 5.1:1 | Alertas críticas, fallos de auditoría o conexión caída |
| `color.theme.ink` | `--text-primary` | `#1A1A1A` • ratio 16:1 | Texto principal de lectura y títulos (WCAG AAA) |
| `color.theme.ink-secondary` | `--text-secondary` | `#505050` • ratio 7:1 | Etiquetas secundarias, subtextos y metadatos (WCAG AAA) |
| `color.theme.ink-muted` | `--text-muted` | `#767676` • ratio 4.5:1 | Textos de ayuda, notas al pie y placeholders (WCAG AA) |
| `border.theme.gold-subtle` | `--border-gold` | `rgba(138, 104, 0, 0.30)` | Bordes periciales y divisores estructurales |
| `border.theme.green-subtle`| `--border-green` | `rgba(26, 107, 26, 0.30)` | Bordes de verificación y éxito probatorio |

> [!TIP]
> Los colores de acento vivos (`--color-primary-vivid: #FECF06`, `--color-secondary-vivid: #1A9A2A`) solo se usan en **elementos decorativos, fondos translúcidos y bordes**. Nunca como color de texto sobre fondo claro.

---

## 3. Escala Tipográfica USWDS (Type Scale Tokens)

```css
/* Escala de Tipografías USWDS */
--usa-font-sans: 'Arial', 'Ubuntu', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--usa-font-mono: 'Consolas', 'Fira Code', 'Roboto Mono', monospace;

/* Jerarquía de Encabezados USWDS — Light Mode */
h1 { font-size: var(--usa-font-size-xl, 1.85rem); font-weight: 700; color: var(--color-secondary); /* #1A6B1A */ line-height: 1.25; }
h2 { font-size: var(--usa-font-size-lg, 1.40rem); font-weight: 600; color: var(--color-primary); /* #8A6800 */ line-height: 1.30; }
h3 { font-size: var(--usa-font-size-md, 1.15rem); font-weight: 600; color: var(--color-primary); /* #8A6800 */ line-height: 1.35; }
h4 { font-size: var(--usa-font-size-sm, 1.00rem); font-weight: 600; color: var(--color-primary); /* #8A6800 */ }
p  { font-size: var(--usa-font-size-base, 1.02rem); font-weight: 400; color: var(--text-primary); /* #1A1A1A */ line-height: 1.60; }
```

---

## 4. Escala de Espaciado Modular USWDS (Spacing Units / 8pt Grid)

| Token USWDS | Multiplicador | Valor en Píxeles | Uso en Componentes |
| :--- | :--- | :--- | :--- |
| `units(0.5)` | `--usa-space-05` | `2px` | Micro-offsets y separadores de tags |
| `units(1)` | `--usa-space-1` | `4px` | Padding de chips, radios internos |
| `units(2)` | `--usa-space-2` | `8px` | Gaps entre controles, padding de botones compactos |
| `units(3)` | `--usa-space-3` | `12px` | Padding interno de inputs, selects y textarea |
| `units(4)` | `--usa-space-4` | `16px` | Padding estándar de tarjetas y paneles laterales |
| `units(5)` | `--usa-space-5` | `24px` | Separación entre módulos y padding de cabeceras |
| `units(6)` | `--usa-space-6` | `32px` | Padding del contenedor de lectura editorial |
| `units(8)` | `--usa-space-8` | `48px` | Separaciones de secciones principales |

---

## 5. Gestión de Imágenes (Modo Manual y Extracción desde URL)

* **Modo URL**: Si se ingresa un enlace externo, el scraper extrae la imagen destacada (`og:image` / `twitter:image`) automáticamente y la muestra en el visor con la etiqueta *"IMAGEN DE LA FUENTE ORIGINAL"*.
* **Modo Docling `.md` / Texto Pegado**: No se genera ningún banner automático. La inserción y maquetación de imágenes se realiza de forma **manual** durante la publicación final en WordPress o el CMS.
* **Formato Recomendado**: Imagen destacada 16:9 (`1200px × 675px`) para WordPress.
* **Descarga Proxy**: El endpoint `/api/download-proxy-image` permite descargar la imagen extraída desde URL sin bloqueos CORS.

---

## 6. Delimitación Estricta de Normativas Citables (`Informacion_docling_rag`)

El motor editorial y el sistema de generación **SOLO tienen permitido citar expresamente las siguientes normativas y cuerpos técnicos oficiales**:

1. **Normativa Base de Diseño:**
   - **USWDS**: [https://github.com/uswds/uswds.git](https://github.com/uswds/uswds.git) (Accesibilidad WCAG 2.1 AA/AAA, Design System Tokens, Spacing Units).
2. **Constitución y Marco Regulatorio Venezolano:**
   - **CRBV** (Arts. 28, 60, 110), Ley de Amparo Constitucional.
   - **Ley Especial contra los Delitos Informáticos** (G.O. Nº 37.313).
   - **Ley de Infogobierno** (G.O. Nº 40.274).
   - **Decreto-Ley sobre Mensajes de Datos y Firmas Electrónicas** (G.O. Nº 37.148).
   - **Ley Orgánica de Telecomunicaciones (LOTEL / Conatel)**.
   - **Ley Orgánica de Ciencia, Tecnología e Innovación (LOCTI)**.
   - **Manual Único de Cadena de Custodia de Evidencias** (MP / CICPC).
   - **CENIF** (G.O. N° 39.847), Providencias SUSCERTE y VenCERT.
   - **COPP**, Código Penal, Código Civil, CPC, Código de Comercio, LOPNNA, LOPCYMAT.
   - **Decisiones y Jurisprudencias de las Salas del TSJ**.
3. **Estándares Internacionales Forenses y de Ciberseguridad:**
   - **ISO/IEC 27001**, **ISO/IEC 27002**, **ISO/IEC 27037**, **ISO/IEC 27042**.
   - **NIST SP 800-86**, **NIST SP 800-101**, **RFC 3227** y **ACPO v5**.

---

## 7. Formato Imprimible de Planillas Oficiales (Hojas Blancas Tamaño Oficio)

* **Formato de Papel:** Hojas Blancas Tamaño **Oficio Venezolano** (`216mm x 330mm`).
* **Márgenes de Papel Sellado:** `Top: 20mm`, `Right: 15mm`, `Bottom: 20mm`, `Left: 38mm` (espacio reglamentario de encuadernación/cosido pericial).
* **Comportamiento en Impresión (`@media print`):**
   - Fondo blanco puro (`#FFFFFF`) y texto negro pericial (`#1D1D1F` / `#000000`).
   - Ocultación total de controles UI (`.no-print`).
   - Renderizado fiel de citas legales, tablas y banners.
