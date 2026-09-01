/**
 * Módulo de Auditoría SEO Top-Tier 2026 y Métricas UX en Vivo
 */

export function updateSeoAudit(markdown) {
  const seoScoreEl = document.getElementById("seoScore");
  const seoProgressFill = document.getElementById("seoProgressFill");
  const seoWordCount = document.getElementById("seoWordCount");
  const seoReadingTime = document.getElementById("seoReadingTime");
  const seoBoldKeywordsCount = document.getElementById("seoBoldKeywordsCount");
  const seoKeywordRepetition = document.getElementById("seoKeywordRepetition");
  const seoKeywordDensity = document.getElementById("seoKeywordDensity");
  const seoLinksCount = document.getElementById("seoLinksCount");
  const seoHeadingCount = document.getElementById("seoHeadingCount");
  const seoH1Count = document.getElementById("seoH1Count");
  const previewSlug = document.getElementById("previewSlug");
  const previewTitle = document.getElementById("previewTitle");
  const previewSnippet = document.getElementById("previewSnippet");

  const faqEl = document.getElementById("seoFaqDetected");
  const tocEl = document.getElementById("seoTocDetected");
  const schemaEl = document.getElementById("seoSchemaComplete");
  const authorEl = document.getElementById("seoAuthorDetected");
  const ctaEl = document.getElementById("seoCtaDetected");
  const titleCharEl = document.getElementById("seoTitleChars");
  const descCharEl = document.getElementById("seoDescChars");

  if (!markdown || markdown.trim() === "") {
    if (seoWordCount) seoWordCount.innerText = "0";
    if (seoReadingTime) seoReadingTime.innerText = "0 min";
    if (seoBoldKeywordsCount) seoBoldKeywordsCount.innerText = "0";
    if (seoKeywordRepetition) seoKeywordRepetition.innerText = "0";
    if (seoKeywordDensity) seoKeywordDensity.innerText = "0.0%";
    if (seoLinksCount) seoLinksCount.innerText = "0";
    if (seoHeadingCount) seoHeadingCount.innerText = "0";
    if (seoH1Count) seoH1Count.innerText = "0";

    if (faqEl) { faqEl.innerText = "❌ No"; faqEl.style.color = "var(--color-error)"; }
    if (tocEl) { tocEl.innerText = "❌ No"; tocEl.style.color = "var(--color-error)"; }
    if (schemaEl) { schemaEl.innerText = "❌ No"; schemaEl.style.color = "var(--color-error)"; }
    if (authorEl) { authorEl.innerText = "❌ No"; authorEl.style.color = "var(--color-error)"; }
    if (ctaEl) { ctaEl.innerText = "❌ No"; ctaEl.style.color = "var(--color-error)"; }
    if (titleCharEl) { titleCharEl.innerText = "0/60"; titleCharEl.style.color = "var(--color-primary)"; }
    if (descCharEl) { descCharEl.innerText = "0/160"; descCharEl.style.color = "var(--color-primary)"; }

    if (previewSlug) previewSlug.innerText = "tu-blog.com/articulos/slug-del-articulo";
    if (previewTitle) previewTitle.innerText = "Título del Artículo de Blog Optimizado";
    if (previewSnippet) previewSnippet.innerText = "La meta description generada para capturar clics y responder a la intención del lector aparecerá aquí...";

    if (seoScoreEl) seoScoreEl.innerText = "0%";
    if (seoProgressFill) {
      seoProgressFill.style.width = "0%";
      seoProgressFill.style.background = "linear-gradient(90deg, var(--color-error), var(--color-warning))";
    }
    return;
  }

  const textOnly = markdown.replace(/[#*`>_\[\]\(\)-]/g, " ").trim();
  const words = textOnly.split(/\s+/).filter((w) => w.length > 0);
  const wordCount = words.length;
  const readingTime = Math.max(1, Math.ceil(wordCount / 200));

  const h1Matches = markdown.match(/^# (.*)/gm) || [];
  const h2Matches = markdown.match(/^## (.*)/gm) || [];
  const h3Matches = markdown.match(/^### (.*)/gm) || [];
  const totalHeadings = h1Matches.length + h2Matches.length + h3Matches.length;

  let isH1WordCountOptimal = false;
  if (h1Matches.length === 1) {
    const h1Text = h1Matches[0].replace(/^#\s*/, "").replace(/[*_]/g, "").trim();
    const h1WordLen = h1Text.split(/\s+/).length;
    isH1WordCountOptimal = h1WordLen >= 6 && h1WordLen <= 14;
  }

  let isH2WordCountOptimal = true;
  if (h2Matches.length > 0) {
    const h2Lengths = h2Matches.map(h => h.replace(/^##\s*/, "").replace(/[*_]/g, "").trim().split(/\s+/).length);
    const avgH2Len = h2Lengths.reduce((a, b) => a + b, 0) / h2Lengths.length;
    isH2WordCountOptimal = avgH2Len >= 4 && avgH2Len <= 12;
  }

  const boldMatches = markdown.match(/\*\*[^*]+\*\*/g) || [];
  const boldKeywordsCount = boldMatches.length;
  const linkMatches = markdown.match(/\[.*?\]\(https?:\/\/.*?\)/g) || [];
  const linksCount = linkMatches.length;

  let primaryKeyword = "";
  const kwMatch = markdown.match(/Palabra Clave Primaria:\s*\*?([^\n|*]+)/i);
  if (kwMatch && kwMatch[1]) {
    primaryKeyword = kwMatch[1].trim();
  } else {
    const h1Match = markdown.match(/^#\s*(.*)/m);
    if (h1Match && h1Match[1]) {
      const cleanH1 = h1Match[1].replace(/[*#]/g, "").trim();
      const h1Words = cleanH1.split(/\s+/).filter(w => w.length > 3);
      if (h1Words.length > 0) primaryKeyword = h1Words.slice(0, 2).join(" ");
    }
  }

  let keywordRepetition = 0;
  let keywordDensity = 0;
  if (primaryKeyword && primaryKeyword.length > 2) {
    try {
      const escapedKw = primaryKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const kwRegex = new RegExp(escapedKw, "gi");
      const kwMatches = markdown.match(kwRegex) || [];
      keywordRepetition = kwMatches.length;
      const kwWordCount = primaryKeyword.split(/\s+/).length;
      if (wordCount > 0) {
        keywordDensity = Math.min(10.0, ((keywordRepetition * kwWordCount) / wordCount) * 100);
      }
    } catch (e) {
      keywordRepetition = 0;
    }
  }

  if (seoWordCount) seoWordCount.innerText = wordCount.toString();
  if (seoReadingTime) seoReadingTime.innerText = `${readingTime} min`;
  if (seoBoldKeywordsCount) seoBoldKeywordsCount.innerText = boldKeywordsCount.toString();
  if (seoKeywordRepetition) seoKeywordRepetition.innerText = keywordRepetition.toString();
  if (seoKeywordDensity) seoKeywordDensity.innerText = `${keywordDensity.toFixed(1)}%`;
  if (seoLinksCount) seoLinksCount.innerText = linksCount.toString();
  if (seoHeadingCount) seoHeadingCount.innerText = totalHeadings.toString();
  if (seoH1Count) seoH1Count.innerText = h1Matches.length.toString();

  const titleMatch = markdown.match(/Meta Title:\s*(.*)/i) || markdown.match(/^# (.*)/m);
  if (titleMatch && titleMatch[1] && previewTitle) {
    const cleanTitle = titleMatch[1].replace(/[*#]/g, "").trim();
    previewTitle.innerText = cleanTitle.substring(0, 65);
  }

  const descMatch = markdown.match(/Meta Descripci[oó]n:\s*(.*)/i) || markdown.match(/^\>\s*\*\*Meta descripci[oó]n:\*\*\s*(.*)/im);
  if (descMatch && descMatch[1] && previewSnippet) {
    const cleanDesc = descMatch[1].replace(/[*#]/g, "").trim();
    previewSnippet.innerText = cleanDesc.substring(0, 160);
  } else {
    const firstP = markdown.split("\n\n").find(p => !p.startsWith("#") && !p.startsWith("---") && !p.startsWith(">") && p.length > 30);
    if (firstP && previewSnippet) {
      previewSnippet.innerText = firstP.replace(/[*#]/g, "").trim().substring(0, 150) + "...";
    }
  }

  const slugMatch = markdown.match(/Slug(?: Sugerido)?:\s*([^\n|]+)/i);
  if (slugMatch && slugMatch[1] && previewSlug) {
    previewSlug.innerText = "tu-blog.com/articulos/" + slugMatch[1].trim().toLowerCase().replace(/[^a-z0-9-]/g, "-");
  }

  const hasVenezuelanLaw = /CRBV|Delitos Informáticos|Infogobierno|Mensajes de Datos|LOCTI|LOPNNA|SUSCERTE|TSJ/i.test(markdown);
  const hasCompatibilitySection = /Análisis de Compatibilidad/i.test(markdown);
  const hasCopyrightSection = /Derechos de Autor|Fuente de Origen|Source Link/i.test(markdown);
  const hasJsonLd = /"@context":\s*"https:\/\/schema\.org"/i.test(markdown);

  const hasFaqSection = /Preguntas Frecuentes|FAQ/i.test(markdown);
  const hasTocSection = /Tabla de Contenidos/i.test(markdown);
  const hasSchemaComplete = hasJsonLd && /\"author\"/.test(markdown) && /\"datePublished\"/.test(markdown) && /\"image\"/.test(markdown);
  const hasFaqSchema = /\"FAQPage\"/i.test(markdown);
  const hasAuthorBio = /Sobre el Autor/i.test(markdown);
  const hasCTA = /comparte|comenta|déjanos|suscríbete|qué opinas/i.test(markdown);

  function setMetricTrafficLight(el, isGood) {
    if (!el) return;
    el.innerText = isGood ? "✅ Sí" : "❌ No";
    el.style.color = isGood ? "var(--color-secondary)" : "var(--color-error)";
  }

  setMetricTrafficLight(faqEl, hasFaqSection);
  setMetricTrafficLight(tocEl, hasTocSection);
  setMetricTrafficLight(schemaEl, hasSchemaComplete);
  setMetricTrafficLight(authorEl, hasAuthorBio);
  setMetricTrafficLight(ctaEl, hasCTA);

  function applyTrafficColor(el, value, goodMin, warnMin) {
    if (!el) return;
    const numVal = parseFloat(value);
    if (numVal >= goodMin) el.style.color = "var(--color-secondary)";
    else if (numVal >= warnMin) el.style.color = "var(--color-warning)";
    else el.style.color = "var(--color-error)";
  }
  applyTrafficColor(seoWordCount, wordCount, 600, 300);
  applyTrafficColor(seoBoldKeywordsCount, boldKeywordsCount, 6, 3);
  applyTrafficColor(seoKeywordRepetition, keywordRepetition, 3, 1);
  applyTrafficColor(seoLinksCount, linksCount, 3, 1);
  applyTrafficColor(seoHeadingCount, totalHeadings, 5, 3);

  if (titleMatch && titleMatch[1] && titleCharEl) {
    const titleLen = titleMatch[1].replace(/[*#]/g, "").trim().length;
    titleCharEl.innerText = `${titleLen}/60`;
    titleCharEl.style.color = (titleLen >= 50 && titleLen <= 65) ? "var(--color-secondary)" : (titleLen >= 30 ? "var(--color-warning)" : "var(--color-error)");
  }
  if (descMatch && descMatch[1] && descCharEl) {
    const descLen = descMatch[1].replace(/[*#]/g, "").trim().length;
    descCharEl.innerText = `${descLen}/160`;
    descCharEl.style.color = (descLen >= 145 && descLen <= 160) ? "var(--color-secondary)" : (descLen >= 100 ? "var(--color-warning)" : "var(--color-error)");
  }

  let score = 5;
  if (h1Matches.length === 1 && isH1WordCountOptimal) score += 12;
  else if (h1Matches.length === 1) score += 8;
  
  if (descMatch && descMatch[1].length >= 100) score += 10;
  if (h2Matches.length >= 3 && isH2WordCountOptimal) score += 8;
  if (boldKeywordsCount >= 6) score += 7;
  if (keywordRepetition >= 3) score += 7;
  if (linksCount >= 2) score += 7;
  if (hasVenezuelanLaw && hasCompatibilitySection) score += 7;
  if (hasCopyrightSection) score += 5;
  if (hasFaqSection) score += 7;
  if (hasTocSection) score += 5;
  if (hasSchemaComplete) score += 8;
  if (hasFaqSchema) score += 4;
  if (hasAuthorBio) score += 5;
  if (hasCTA) score += 3;

  score = Math.min(100, score);
  if (seoScoreEl) seoScoreEl.innerText = `${score}%`;
  if (seoProgressFill) {
    seoProgressFill.style.width = `${score}%`;
    if (score >= 80) seoProgressFill.style.background = "linear-gradient(90deg, var(--color-secondary), #00FF41)";
    else if (score >= 50) seoProgressFill.style.background = "linear-gradient(90deg, var(--color-warning), var(--color-primary))";
    else seoProgressFill.style.background = "linear-gradient(90deg, var(--color-error), var(--color-warning))";
  }
}
