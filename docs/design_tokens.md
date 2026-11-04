# Sistema de Diseño: Documento de Tokens Oficiales (USWDS Dark-Only Design Tokens)

Este documento define de forma **exclusiva y taxativa los Tokens de Diseño Oficiales (Design Tokens)** del proyecto **Granite Blog Writer & LegalTech CMS**, fundamentados íntegramente en la normativa base:

👉 **[USWDS (U.S. Web Design System)](https://github.com/uswds/uswds.git)** (Estándares WCAG 2.1 AA/AAA, diseño modular centrado en el usuario, escala tipográfica sistemática, retícula USWDS Grid y espaciado de 8pt / unidades del sistema).

> [!NOTE]
> Este proyecto opera en **Modo Oscuro Exclusivo (Dark-Only Mode / High Contrast)** bajo los principios de accesibilidad de USWDS. Todos los tokens de texto cumplen ratio mínimo de `4.5:1` sobre fondos oscuros (WCAG 2.1 AA). La única excepción es el formato imprimible pericial `@media print` en tamaño oficio venezolano (216mm × 330mm) sobre papel blanco.

---

## 1. Principios de Diseño USWDS Dark-Only

1. **Accesibilidad Universal (WCAG 2.1 AA/AAA en Oscuro)**:
   - Contraste medido sobre superficies oscuras `--bg-panel` (#12161C) y `--bg-reading` (#0F1318).
   - `--text-primary` (`#E9ECF1`): ratio ≈ 15:1 (WCAG AAA).
   - `--text-secondary` (`#A9B1BD`): ratio ≈ 8:1 (WCAG AAA).
   - `--text-muted` (`#7F8896`): ratio ≈ 4.7:1 (mínimo WCAG AA).
   - Indicadores de foco de alta visibilidad USWDS (`:focus-visible` de 2px con offset de 2px en tokens de oro técnico `--color-primary`).
2. **Sistema de Retícula y Container Queries**:
   - Estructura modular adaptativa con Container Queries (`container-type: inline-size; container-name: article;`).
   - Modo Revista 3 columnas que conmuta dinámicamente a 2 columnas en ≤900px y a 1 columna en ≤560px dentro del contenedor del artículo.
3. **Escala de Espaciado Modular USWDS (8pt Grid)**:
   - Unidades del sistema: 2px (`--usa-space-05`), 4px (`--usa-space-1`), 8px (`--usa-space-2`), 12px (`--usa-space-3`), 16px (`--usa-space-4`), 24px (`--usa-space-5`), 32px (`--usa-space-6`), 48px (`--usa-space-8`).
4. **Paleta Cyber-Legal Tokenizada — Dark Mode**:
   - Superficies profundas: Fondo App (`#0B0E12`), Paneles (`#12161C`), Tarjetas/Inputs (`#181D25`), Lienzo Lectura (`#0F1318`).
   - Cero azules genéricos en la interfaz operativa.
   - Oro Técnico: `--color-primary` (`#F2C230`) y Oro Intenso `--color-primary-strong` (`#FFD54A`).
   - Verde Pericial: `--color-secondary` (`#3DD68C`) y fondos translúcidos `--color-secondary-soft` (`rgba(61,214,140,0.12)`).
   - Lima Info: `--color-info` (`#A3D94F`).
5. **Tipografía Local Offline-First**:
   - **UI / General:** `'Inter'`, `'Segoe UI'`, system-ui, sans-serif.
   - **Terminal / Código:** `'JetBrains Mono'`, `'Cascadia Code'`, Consolas, monospace.
   - **Lectura Editorial:** `'Source Serif 4'`, Georgia, serif.
6. **Integración con Bootstrap 5 (Dark Mapped)**:
   - Variables de Bootstrap (`--bs-body-bg`, `--bs-body-color`, `--bs-primary`, etc.) mapeadas directamente a los tokens oscuros.
7. **Excepción Obligatoria de Impresión**:
   - `@media print` fuerza fondos blancos, texto `#000000` e imágenes claras para planillas periciales y oficios oficiales.

---

## 2. Paleta de Tokens de Superficie y Marca

| Token Semántico | Variable CSS | Valor Hex / RGBA | Uso Semántico |
| :--- | :--- | :--- | :--- |
| `surface.app` | `--bg-app` | `#0B0E12` | Fondo de la aplicación |
| `surface.panel` | `--bg-panel` | `#12161C` | Paneles laterales (Crear y Calidad) |
| `surface.elevated` | `--bg-elevated` | `#181D25` | Tarjetas, inputs, menús desplegables |
| `surface.hover` | `--bg-hover` | `#1F2530` | Estados interactivos hover |
| `surface.reading` | `--bg-reading` | `#0F1318` | Lienzo pericial del artículo |
| `surface.media` | `--bg-media` | `#000000` | Fondo de previsualización de imágenes/cabecera 16:9 |
| `surface.code` | `--bg-code` | `#0A0D11` | Bloques de código preformateado `<pre>` |
| `surface.kbd` | `--bg-kbd` | `var(--bg-hover)` | Teclas del modal de atajos de teclado |
| `text.primary` | `--text-primary` | `#E9ECF1` | Texto principal de lectura y títulos |
| `text.secondary` | `--text-secondary` | `#A9B1BD` | Etiquetas, subtítulos y metadatos |
| `text.muted` | `--text-muted` | `#7F8896` | Placeholders y notas secundarias |
| `text.inverse` | `--text-inverse` | `#0B0E12` | Texto oscuro sobre botones e insignias doradas/verdes |
| `brand.primary` | `--color-primary` | `#F2C230` | Botones de acción principal, H2, foco |
| `brand.primary.strong` | `--color-primary-strong` | `#FFD54A` | Gradiente activo de botones primarios |
| `brand.primary.hover` | `--color-primary-hover` | `#FFE566` | Hover extra-brillante de acción primaria |
| `brand.secondary` | `--color-secondary` | `#3DD68C` | Títulos H1, validación pericial, online |
| `brand.info` | `--color-info` | `#A3D94F` | Bloques explicativos, enlaces, abstract académico |
| `brand.warning` | `--color-warning` | `#FFB23F` | Advertencias de inferencia |
| `brand.error` | `--color-error` | `#FF6B5E` | Errores de conexión o sintaxis |

---

## 3. Escala de Radios y Sombras

```css
--radius-sm: 6px;
--radius-button: 8px;
--radius-card: 12px;
--radius-panel: 14px;
--radius-pill: 999px;

--co-shadow-1: 0 1px 2px rgba(0, 0, 0, 0.5);
--co-shadow-2: 0 4px 14px rgba(0, 0, 0, 0.45);
--co-shadow-3: 0 12px 32px rgba(0, 0, 0, 0.55);
--co-glow-gold: 0 0 0 3px rgba(242, 194, 48, 0.22);
--co-glow-green: 0 0 0 3px rgba(61, 214, 140, 0.22);
```

---

## 4. Micro-Interacciones y Accesibilidad

* **Movimiento y Reducción de Animación**:
  ```css
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```
* **Navegación por Teclado**: Todo control posee estado `:focus-visible` con anillo oro (`--co-glow-gold`).
* **Atajos de Teclado**:
  - `Ctrl+Enter`: Iniciar generación.
  - `Escape`: Detener inferencia o cerrar modales.
  - `Ctrl+Shift+C`: Copiar para WordPress Gutenberg.
  - `Ctrl+Shift+S`: Copiar para Sitejet Builder.
  - `Ctrl+Shift+K`: Abrir Kit SEO Sitejet.
  - `Ctrl+Shift+M`: Copiar Markdown.
  - `Ctrl+Shift+P`: Imprimir en formato oficio pericial.
  - `Ctrl+1 / 2 / 3`: Alternar pestañas Revista / Markdown / WordPress.
  - `Ctrl+Shift+F`: Seguir generación (auto-scroll suave al final).
