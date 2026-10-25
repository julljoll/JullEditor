/**
 * Módulo de Renderizado Markdown de Alta Calidad para el 'Formato SEO Blog PDF'
 * Transforma Markdown estructurado en HTML con jerarquía visual, callouts y bloques especiales.
 */

export function renderArticle(markdown, isStreaming = false) {
  const articleView = document.getElementById("articleView");
  if (!articleView) return;

  if (!markdown) {
    articleView.innerHTML = "";
    document.dispatchEvent(new CustomEvent("article:rendered", {
      detail: { markdown: "", isStreaming: false }
    }));
    return;
  }

  // 1. Proteger bloques de código ``` ... ```
  const codeBlocks = [];
  let text = markdown.replace(/```(json|markdown|html|xml|css|js|py|python)?\s*([\s\S]*?)```/gim, (match, lang, code) => {
    const idx = codeBlocks.length;
    const cleanCode = code.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const isJson = lang && lang.toLowerCase() === "json";
    const blockHtml = isJson
      ? `<div style="margin: 16px 0;"><div style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--color-secondary); margin-bottom: 4px; font-weight: 700;">⚡ DATOS ESTRUCTURADOS SCHEMA.ORG (JSON-LD)</div><pre><code>${cleanCode}</code></pre></div>`
      : `<pre><code>${cleanCode}</code></pre>`;
    codeBlocks.push(blockHtml);
    return `\n\n%%CODE_BLOCK_${idx}%%\n\n`;
  });

  // 2. Proteger código en línea `code`
  const inlineCodes = [];
  text = text.replace(/`([^`\n]+)`/g, (match, code) => {
    const idx = inlineCodes.length;
    const clean = code.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    inlineCodes.push(`<code>${clean}</code>`);
    return `%%INLINE_CODE_${idx}%%`;
  });

  // 3. Escapar < y > fuera de código
  text = text.replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // 4. Bloques Especiales Callouts
  text = text.replace(/(?:^|\n)(?:&gt;|>)?\s*\*\*Meta descripci[oó]n:\*\*\s*(.+?)(?=\n\n|$)/gim, (match, p1) => {
    return `\n\n<div class="meta-description-callout"><div class="meta-description-label"><span class="material-symbols-outlined" style="font-size:1rem;">search_check</span> Meta Descripción (CTR Snippet)</div><div class="meta-description-text">${p1.trim()}</div></div>\n\n`;
  });

  text = text.replace(/(?:^|\n)(?:&gt;|>)?\s*\*\*📌 Resumen Pr[aá]ctico de la Fuente Original:\*\*\s*([\s\S]*?)(?=\n\n|\n(?:&gt;|>)\s*\*\*|##|$)/gim, (match, p1) => {
    const clean = p1.replace(/^(?:&gt;|>)\s*/gm, '').trim();
    return `\n\n<div class="source-summary-callout"><div class="source-summary-label"><span class="material-symbols-outlined" style="font-size:1rem;">auto_stories</span> Resumen Práctico de la Fuente Original (Traducción & Análisis)</div><div class="source-summary-text">${clean}</div></div>\n\n`;
  });

  text = text.replace(/(?:^|\n)(?:&gt;|>)?\s*\*\*📋\s*RESUMEN ESTRUCTURADO \(ABSTRACT\):\*\*\s*([\s\S]*?)(?=\n\n|\n(?:&gt;|>)\s*\*\*|##|$)/gim, (match, p1) => {
    const clean = p1.replace(/^(?:&gt;|>)\s*/gm, '').trim();
    return `\n\n<div class="academic-abstract-card"><div class="academic-abstract-label"><span class="material-symbols-outlined" style="font-size:1.1rem;">school</span> Resumen Estructurado / Abstract (Normas de Publicación Científica)</div><div class="academic-abstract-text">${clean}</div></div>\n\n`;
  });

  text = text.replace(/(?:^|\n)(?:&gt;|>)?\s*\*\*⚡ Resumen Ejecutivo en 30 Segundos:\*\*\s*([\s\S]*?)(?=\n\n|\n(?:&gt;|>)\s*\*\*|##|$)/gim, (match, p1) => {
    const clean = p1.replace(/^(?:&gt;|>)\s*/gm, '').trim();
    return `\n\n<div class="source-summary-callout source-summary-callout--exec"><div class="source-summary-label"><span class="material-symbols-outlined" style="font-size:1rem;">bolt</span> Resumen Ejecutivo en 30 Segundos</div><div class="source-summary-text">${clean}</div></div>\n\n`;
  });

  text = text.replace(/(?:^|\n)(?:&gt;|>)?\s*(?:###\s*)?(?:💡\s*)?En Palabras Simples\s*([\s\S]*?)(?=\n\n|##|$)/gim, (match, p1) => {
    const clean = p1.replace(/^(?:&gt;|>)\s*/gm, '').trim();
    return `\n\n<div class="source-summary-callout source-summary-callout--simple"><div class="source-summary-label"><span class="material-symbols-outlined" style="font-size:1rem;">lightbulb</span> En Palabras Simples</div><div class="source-summary-text">${clean}</div></div>\n\n`;
  });


  text = text.replace(/(?:^|\n)\*\*Conclusi[oó]n del p[aá]rrafo:\*\*\s*(.+?)(?=\n|$)/gim, (match, p1) => {
    return `\n\n<div class="paragraph-takeaway"><strong>⚡ Conclusión del párrafo:</strong> ${p1.trim()}</div>\n\n`;
  });
  text = text.replace(/(?:^|\n)\*\*Idea clave:\*\*\s*(.+?)(?=\n|$)/gim, (match, p1) => {
    return `\n\n<div class="paragraph-takeaway"><strong>💡 Idea clave:</strong> ${p1.trim()}</div>\n\n`;
  });

  // 5. Cintas de Metadatos SEO
  text = text.replace(/\*\*Palabra Clave Primaria:\*\*(.*?)(?=\s*\||\n|$)/gi, '<div class="seo-badge"><strong>Keyword Primaria:</strong>$1</div>');
  text = text.replace(/\*\*Keywords LSI:\*\*(.*?)(?=\s*\||\n|$)/gi, '<div class="seo-badge"><strong>Keywords LSI:</strong>$1</div>');
  text = text.replace(/\*\*Palabras Clave Secundarias:\*\*(.*?)(?=\s*\||\n|$)/gi, '<div class="seo-badge"><strong>Keywords LSI:</strong>$1</div>');
  text = text.replace(/\*\*Slug Sugerido:\*\*(.*?)(?=\s*\||\n|$)/gi, '<div class="seo-badge"><strong>Slug:</strong>$1</div>');
  text = text.replace(/\*\*Tiempo de Lectura(?: Estimado)?:\*\*(.*?)(?=\s*\||\n|$)/gi, '<div class="seo-badge"><strong>⏱ Lectura:</strong>$1</div>');
  text = text.replace(/\*\*Jurisdicci[oó]n(?: Aplicable)?:\*\*(.*?)(?=\s*\||\n|$)/gi, '<div class="seo-badge seo-badge--jurisdiction"><strong>⚖️ Jurisdicción:</strong>$1</div>');

  text = text.replace(/(<div class="seo-badge"[\s\S]*?<\/div>)+/gim, (match) => {
    return `\n\n<div class="seo-badge-container">${match}</div>\n\n`;
  });

  // 6. Secciones Especiales
  text = text.replace(/^##\s*❓\s*Preguntas Frecuentes\s*\(FAQ\)([\s\S]*?)(?=\n##\s|%%CODE_BLOCK_|$)/gim, (match, p1) => {
    let faqContent = p1;
    faqContent = faqContent.replace(/\*\*P:\s*(.*?)\*\*/gim, '<div class="faq-question"><strong>❓ $1</strong></div>');
    faqContent = faqContent.replace(/^R:\s*(.*$)/gim, '<div class="faq-answer">$1</div>');
    return `\n\n<div class="faq-section-card"><div class="faq-section-title"><span class="material-symbols-outlined" style="font-size:1.1rem;">quiz</span> Preguntas Frecuentes (FAQ Schema)</div>${faqContent}</div>\n\n`;
  });

  text = text.replace(/^##\s*⚖️\s*Derechos de Autor y Fuente de Origen([\s\S]*?)(?=\n##\s|%%CODE_BLOCK_|$)/gim, (match, p1) => {
    return `\n\n<div class="copyright-card"><div class="copyright-card-title"><span class="material-symbols-outlined" style="font-size:1.1rem;">copyright</span> Derechos de Autor y Fuente de Origen</div>${p1}</div>\n\n`;
  });

  text = text.replace(/^##\s*✍️\s*Sobre el Autor([\s\S]*?)(?=\n##\s|%%CODE_BLOCK_|$)/gim, (match, p1) => {
    return `\n\n<div class="author-bio-card"><div class="author-bio-title"><span class="material-symbols-outlined" style="font-size:1.1rem;">person</span> Sobre el Autor (E-E-A-T)</div>${p1}</div>\n\n`;
  });

  text = text.replace(/^##\s*📑\s*Tabla de Contenidos([\s\S]*?)(?=\n##\s|\[PÁRRAFO|^En resumen|\n\n[A-Z]|$)/gim, (match, p1) => {
    return `\n\n<nav class="toc-card"><div class="toc-title"><span class="material-symbols-outlined" style="font-size:1.1rem;">toc</span> Tabla de Contenidos</div>${p1}</nav>\n\n`;
  });

  // 7. Tablas Markdown
  text = text.replace(/(?:^|\n)((?:\|[^\n]+\|\r?\n)+)/g, (match, tableText) => {
    const rows = tableText.trim().split('\n').map(r => r.trim()).filter(Boolean);
    if (rows.length < 2) return match;
    
    let tableHtml = '<table>';
    let inThead = true;

    rows.forEach((row, rIdx) => {
      if (row.match(/^\|(?:\s*:?-+:?\s*\|)+$/)) {
        inThead = false;
        return;
      }

      const cells = row.split('|').slice(1, -1).map(c => c.trim());
      if (rIdx === 0 && inThead) {
        tableHtml += '<thead><tr>';
        cells.forEach(c => { tableHtml += `<th>${c}</th>`; });
        tableHtml += '</tr></thead><tbody>';
      } else {
        tableHtml += '<tr>';
        cells.forEach(c => { tableHtml += `<td>${c}</td>`; });
        tableHtml += '</tr>';
      }
    });

    if (!inThead) tableHtml += '</tbody>';
    tableHtml += '</table>';
    return `\n\n${tableHtml}\n\n`;
  });

  // 8. Encabezados Semánticos
  text = text.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');
  text = text.replace(/^##\s+(.+?)(?:\s*\{#([\w-]+)\})?\s*$/gm, (match, hText, anchor) => {
    const slug = anchor || hText.replace(/[^a-záéíóúñü0-9\s]/gi, '').trim().toLowerCase().replace(/\s+/g, '-').substring(0, 50);
    return `<h2 id="${slug}">${hText}</h2>`;
  });
  text = text.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
  text = text.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');

  // 9. Blockquotes genéricos
  text = text.replace(/(?:^|\n)((?:(?:&gt;|>)[^\n]+\r?\n?)+)/g, (match, bqText) => {
    const cleanBq = bqText.replace(/^(?:&gt;|>)\s*/gm, '').trim();
    return `\n\n<blockquote>${cleanBq}</blockquote>\n\n`;
  });

  // 10. Negritas, Cursivas y Enlaces
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
  text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a>');

  // 11. Listas
  text = text.replace(/(?:^|\n)((?:^[\-\*]\s+[^\n]+\r?\n?)+)/gm, (match, listContent) => {
    const items = listContent.trim().split('\n').map(l => l.replace(/^[\-\*]\s+/, '').trim()).filter(Boolean);
    return `\n\n<ul>${items.map(i => `<li>${i}</li>`).join('')}</ul>\n\n`;
  });

  text = text.replace(/(?:^|\n)((?:^\d+\.\s+[^\n]+\r?\n?)+)/gm, (match, listContent) => {
    const items = listContent.trim().split('\n').map(l => l.replace(/^\d+\.\s+/, '').trim()).filter(Boolean);
    return `\n\n<ol>${items.map(i => `<li>${i}</li>`).join('')}</ol>\n\n`;
  });

  // 12. Párrafos
  const rawBlocks = text.split(/\n{2,}/);
  const parsedBlocks = rawBlocks.map(block => {
    const trimmed = block.trim();
    if (!trimmed) return '';
    if (trimmed.startsWith('<h1') || trimmed.startsWith('<h2') || trimmed.startsWith('<h3') || trimmed.startsWith('<h4') ||
        trimmed.startsWith('<ul') || trimmed.startsWith('<ol') || trimmed.startsWith('<blockquote') ||
        trimmed.startsWith('<div') || trimmed.startsWith('<nav') || trimmed.startsWith('<table') ||
        trimmed.startsWith('<pre') || trimmed.startsWith('%%CODE_BLOCK_')) {
      return trimmed;
    }
    const paragraphText = trimmed.replace(/\n+/g, ' ');
    return `<p>${paragraphText}</p>`;
  }).filter(Boolean);

  let finalHtml = parsedBlocks.join('\n');

  // 13. Restaurar códigos
  inlineCodes.forEach((codeHtml, idx) => {
    finalHtml = finalHtml.replace(`%%INLINE_CODE_${idx}%%`, codeHtml);
  });
  codeBlocks.forEach((blockHtml, idx) => {
    finalHtml = finalHtml.replace(`%%CODE_BLOCK_${idx}%%`, blockHtml);
  });

  // 14. Envolver en estructura de Revista Digital si no está en modo 'single'
  const articleContainer = document.getElementById("articleContainer");
  const isSingle = articleContainer && articleContainer.dataset.layout === "single";
  if (!isSingle) {
    finalHtml = wrapMagazine(finalHtml);
  }

  if (isStreaming) {
    if (finalHtml.includes('</footer>')) {
      finalHtml = finalHtml.replace('</footer>', '<span class="streaming-cursor"></span></footer>');
    } else if (finalHtml.includes('</div>')) {
      finalHtml = finalHtml.replace(/<\/div>$/, '<span class="streaming-cursor"></span></div>');
    } else {
      finalHtml += '<span class="streaming-cursor"></span>';
    }
  }

  articleView.innerHTML = finalHtml;

  if (articleContainer && isStreaming && articleContainer.dataset.follow !== "false") {
    articleContainer.scrollTop = articleContainer.scrollHeight;
  }

  document.dispatchEvent(new CustomEvent("article:rendered", {
    detail: { markdown, isStreaming }
  }));
}

/**
 * Envuelve el HTML plano en 3 zonas semánticas de Revista Digital:
 * - mag-head: Título, meta descripción, badges SEO y párrafo Answer-First
 * - mag-body: Secciones de contenido estructurado en 3 columnas
 * - mag-foot: FAQ, Derechos de Autor, Sobre el Autor y Schema.org JSON-LD
 */
export function wrapMagazine(html) {
  const firstH2 = html.search(/<h2[\s>]/);
  if (firstH2 === -1) return html; // Durante el streaming inicial sin H2 se mantiene plano

  const faqIdx = html.indexOf('<div class="faq-section-card"');
  const footStart = faqIdx !== -1 && faqIdx > firstH2 ? faqIdx : html.length;

  const head = html.slice(0, firstH2);
  const body = html.slice(firstH2, footStart);
  const foot = html.slice(footStart);

  return `<header class="mag-head">${head}</header>` +
         `<div class="mag-body">${body}</div>` +
         (foot ? `<footer class="mag-foot">${foot}</footer>` : '');
}

/**
 * Deshace el envoltorio de revista en un elemento DOM (útil para exportadores a CMS)
 */
export function unwrapMagazine(containerOrEl) {
  if (!containerOrEl) return;
  const wrappers = containerOrEl.querySelectorAll(".mag-head, .mag-body, .mag-foot");
  wrappers.forEach(wrapper => {
    while (wrapper.firstChild) {
      wrapper.parentNode.insertBefore(wrapper.firstChild, wrapper);
    }
    wrapper.remove();
  });
}

