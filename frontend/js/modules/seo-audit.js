/**
 * Módulo de Auditoría SEO Top-Tier 2026 y Métricas UX / Deontología Jurídica
 * Evaluaciones en tiempo real durante streaming y auditoría profunda contra el backend FastAPI.
 */

import { toast } from "./toast-notifications.js";

const LEGAL_TERMS_SET = [
  // Venezuela
  "crbv", "asamblea nacional", "gaceta oficial", "tsj", "sala constitucional",
  "delitos informáticos", "infogobierno", "mensajes de datos", "firmas electrónicas",
  "locti", "lopnna", "suscerte", "cnti", "código orgánico procesal penal",
  "amparo constitucional", "debido proceso", "cadena de custodia digital",
  // Colombia
  "constitución política", "corte constitucional", "corte suprema de justicia",
  "consejo de estado", "ley 1273", "ley 1581", "ley 527", "habeas data",
  "superintendencia de industria y comercio", "sic", "acción de tutela",
  "código general del proceso", "mensaje de datos", "firma digital",
  // Universal / Cyber-Legal
  "marco normativo", "jurisprudencia", "validez probatoria", "responsabilidad civil",
  "sujeto pasivo", "tipo penal", "fuentes oficiales", "deontología"
];

const PROMISE_PATTERNS = [
  /garantizamos el [eé]xito/i,
  /100%\s*seguro/i,
  /ganar[aá] el juicio/i,
  /sin riesgo alguno/i,
  /resultado garantizado/i
];

const ANTI_CALCOS = [
  { regex: /a nivel de/i, replace: "en el ámbito de / respecto de" },
  { regex: /en base a/i, replace: "con base en / según" },
  { regex: /a la brevedad posible/i, replace: "a la mayor brevedad" }
];

function extractFirstBlockAfterH1(markdown) {
  const cleanMd = (markdown || "").replace(/^---[\s\S]*?---\s*/, "");
  const lines = cleanMd.split("\n");
  let seenH1 = false;
  for (const line of lines) {
    const s = line.trim();
    if (!seenH1) {
      if (s.startsWith("# ") || /^###?\s*T[ií]tulo(?:\s*H1)?:\s*/i.test(s)) {
        seenH1 = true;
      }
      continue;
    }
    if (!s || s.startsWith("#") || s.startsWith(">") || s.startsWith("|") || s.startsWith("-") || s.startsWith("*") || s.startsWith("`") || s.startsWith("<") || s.startsWith("**Meta") || /Meta Descripci[oó]n/i.test(s)) {
      continue;
    }
    return s.replace(/[*_`\[\]()]/g, "").trim();
  }
  return "";
}

/**
 * Actualiza la auditoría SEO y de Calidad Jurídica client-side en tiempo real.
 */
export function updateSeoAudit(markdown) {
  const seoScoreEl = document.getElementById("seoScore");
  const seoProgressFill = document.getElementById("seoProgressFill");
  const legalQualityScoreEl = document.getElementById("legalQualityScore");
  const legalProgressFill = document.getElementById("legalProgressFill");
  const combinedScoreBadge = document.getElementById("combinedScoreBadge");

  const seoWordCount = document.getElementById("seoWordCount");
  const seoReadingTime = document.getElementById("seoReadingTime");
  const seoBoldKeywordsCount = document.getElementById("seoBoldKeywordsCount");
  const seoKeywordRepetition = document.getElementById("seoKeywordRepetition");
  const seoKeywordDensity = document.getElementById("seoKeywordDensity");
  const seoLinksCount = document.getElementById("seoLinksCount");
  const seoHeadingCount = document.getElementById("seoHeadingCount");
  const seoH1Count = document.getElementById("seoH1Count");

  const answerFirstEl = document.getElementById("seoAnswerFirstDetected");
  const disclaimerEl = document.getElementById("seoDisclaimerDetected");
  const legalTermsEl = document.getElementById("seoLegalTermsDetected");
  const h2QuestionsEl = document.getElementById("seoH2QuestionsDetected");

  const faqEl = document.getElementById("seoFaqDetected");
  const tocEl = document.getElementById("seoTocDetected");
  const schemaEl = document.getElementById("seoSchemaComplete");
  const authorEl = document.getElementById("seoAuthorDetected");
  const ctaEl = document.getElementById("seoCtaDetected");
  const titleCharEl = document.getElementById("seoTitleChars");
  const descCharEl = document.getElementById("seoDescChars");

  const previewSlug = document.getElementById("previewSlug");
  const previewTitle = document.getElementById("previewTitle");
  const previewSnippet = document.getElementById("previewSnippet");
  const issuesContainer = document.getElementById("seoAuditIssuesContainer");

  if (!markdown || markdown.trim() === "") {
    if (seoWordCount) seoWordCount.innerText = "0";
    if (seoReadingTime) seoReadingTime.innerText = "0 min";
    if (seoBoldKeywordsCount) seoBoldKeywordsCount.innerText = "0";
    if (seoKeywordRepetition) seoKeywordRepetition.innerText = "0";
    if (seoKeywordDensity) seoKeywordDensity.innerText = "0.0%";
    if (seoLinksCount) seoLinksCount.innerText = "0";
    if (seoHeadingCount) seoHeadingCount.innerText = "0";
    if (seoH1Count) seoH1Count.innerText = "0";

    if (answerFirstEl) { answerFirstEl.innerText = "❌ No"; answerFirstEl.style.color = "var(--color-error)"; }
    if (disclaimerEl) { disclaimerEl.innerText = "❌ Falta"; disclaimerEl.style.color = "var(--color-error)"; }
    if (legalTermsEl) { legalTermsEl.innerText = "0"; legalTermsEl.style.color = "var(--color-error)"; }
    if (h2QuestionsEl) { h2QuestionsEl.innerText = "❌ 0/0"; h2QuestionsEl.style.color = "var(--color-error)"; }

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
    if (legalQualityScoreEl) legalQualityScoreEl.innerText = "0%";
    if (legalProgressFill) {
      legalProgressFill.style.width = "0%";
    }
    if (combinedScoreBadge) {
      combinedScoreBadge.innerText = "0% · STANDBY";
      combinedScoreBadge.className = "seo-score-badge";
    }
    if (issuesContainer) {
      issuesContainer.style.display = "none";
      issuesContainer.innerHTML = "";
    }
    return;
  }

  const cleanMd = (markdown || "").replace(/^---[\s\S]*?---\s*/, "");
  const textOnly = cleanMd.replace(/[#*`>_\[\]\(\)-]/g, " ").trim();
  const words = textOnly.split(/\s+/).filter((w) => w.length > 0);
  const wordCount = words.length;
  const readingTime = Math.max(1, Math.ceil(wordCount / 200));

  let h1Matches = cleanMd.match(/^# (.*)/gm) || [];
  if (h1Matches.length === 0) {
    const fallbackH1 = cleanMd.match(/^###?\s*T[ií]tulo(?:\s*H1)?:\s*(.+)$/gmi);
    if (fallbackH1) h1Matches = fallbackH1;
  }

  let h2Matches = cleanMd.match(/^## (.*)/gm) || [];
  const h3Matches = cleanMd.match(/^### (.*)/gm) || [];
  if (h2Matches.length < 2 && h3Matches.length >= 3) {
    h2Matches = h3Matches;
  }
  const totalHeadings = h1Matches.length + h2Matches.length + h3Matches.length;

  let isH1WordCountOptimal = false;
  if (h1Matches.length === 1) {
    const h1Text = h1Matches[0].replace(/^(?:#+|###?\s*T[ií]tulo(?:\s*H1)?:\s*)/i, "").replace(/[*_`]/g, "").trim();
    const h1WordLen = h1Text.split(/\s+/).length;
    isH1WordCountOptimal = h1WordLen >= 6 && h1WordLen <= 15;
  }

  let isH2WordCountOptimal = true;
  if (h2Matches.length > 0) {
    const h2Lengths = h2Matches.map(h => h.replace(/^#{2,3}\s*/, "").replace(/[*_`]/g, "").trim().split(/\s+/).length);
    const avgH2Len = h2Lengths.reduce((a, b) => a + b, 0) / h2Lengths.length;
    isH2WordCountOptimal = avgH2Len >= 4 && avgH2Len <= 12;
  }

  const boldMatches = cleanMd.match(/\*\*[^*]+\*\*/g) || [];
  const boldKeywordsCount = boldMatches.length;
  const linkMatches = cleanMd.match(/\[.*?\]\(https?:\/\/.*?\)/g) || [];
  const linksCount = linkMatches.length;

  let primaryKeyword = "";
  const kwMatch = cleanMd.match(/Palabra Clave Primaria:\s*\*?([^\n|*]+)/i);
  if (kwMatch && kwMatch[1]) {
    primaryKeyword = kwMatch[1].trim();
  } else {
    const h1Match = cleanMd.match(/^#\s*(.*)/m) || cleanMd.match(/^###?\s*T[ií]tulo(?:\s*H1)?:\s*(.*)/im);
    if (h1Match && h1Match[1]) {
      const cleanH1 = h1Match[1].replace(/^(?:#+|###?\s*T[ií]tulo(?:\s*H1)?:\s*)/i, "").replace(/[*#`]/g, "").trim();
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
      const kwMatches = cleanMd.match(kwRegex) || [];
      keywordRepetition = kwMatches.length;
      const kwWordCount = primaryKeyword.split(/\s+/).length;
      if (wordCount > 0) {
        keywordDensity = Math.min(10.0, ((keywordRepetition * kwWordCount) / wordCount) * 100);
      }
    } catch (_) {
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

  // SERP Google Preview
  const titleMatch = cleanMd.match(/Meta Title:\s*(.*)/i) || cleanMd.match(/^# (.*)/m) || cleanMd.match(/^###?\s*T[ií]tulo(?:\s*H1)?:\s*(.*)/im);
  if (titleMatch && titleMatch[1] && previewTitle) {
    const cleanTitle = titleMatch[1].replace(/^(?:#+|###?\s*T[ií]tulo(?:\s*H1)?:\s*)/i, "").replace(/[*#`]/g, "").trim();
    previewTitle.innerText = cleanTitle.substring(0, 65);
  }

  let descMatch = cleanMd.match(/^\>\s*\*\*Meta descripci[oó]n:\*\*\s*(.+)/im)
    || cleanMd.match(/\*\*Meta descripci[oó]n:\*\*\s*(.+)/i)
    || cleanMd.match(/^#{2,3}\s*Meta Descripci[oó]n\s*\n+([^\n#]+)/im);
  if (descMatch && descMatch[1] && previewSnippet) {
    const cleanDesc = descMatch[1].replace(/[*#`]/g, "").trim();
    previewSnippet.innerText = cleanDesc.substring(0, 160);
  } else {
    const firstP = cleanMd.split("\n\n").find(p => !p.startsWith("#") && !p.startsWith("---") && !p.startsWith(">") && p.length > 30);
    if (firstP && previewSnippet) {
      previewSnippet.innerText = firstP.replace(/[*#]/g, "").trim().substring(0, 150) + "...";
    }
  }

  const slugMatch = cleanMd.match(/Slug(?: Sugerido)?:\s*([^\n|]+)/i);
  if (slugMatch && slugMatch[1] && previewSlug) {
    previewSlug.innerText = "tu-blog.com/articulos/" + slugMatch[1].trim().toLowerCase().replace(/[^a-z0-9-]/g, "-");
  }

  // Detecciones 2026 E-E-A-T y Schema
  const hasRegulatoryFramework = /CRBV|Delitos Informáticos|Infogobierno|Mensajes de Datos|LOCTI|LOPNNA|SUSCERTE|TSJ|Constitución Política|Ley 1273|Ley 1581|Ley 527|Ley 1266|Corte Constitucional|Superintendencia de Industria|CGP|ISO\/IEC|NIST|Reglamento|Directiva|Estándar/i.test(cleanMd);
  const hasAdoptionSection = /Análisis de Compatibilidad|Adopción e Impacto|Impacto Tecnológico|Prospectiva|Impacto.*Colombia/i.test(cleanMd);
  const hasCopyrightSection = /Derechos de Autor|Fuente de Origen|Source Link/i.test(cleanMd);
  const hasJsonLd = /"@context":\s*"https:\/\/schema\.org"/i.test(cleanMd);

  const hasFaqSection = /#{2,3}\s*❓?\s*(?:Preguntas Frecuentes|FAQ)/i.test(cleanMd) || /\b(?:P:|R:|P\/R\d*:|question\d+)\b/i.test(cleanMd);
  const hasTocSection = /#{2,3}\s*📑?\s*Tabla de Contenidos/i.test(cleanMd) || /\[#seccion|\[#marco|\[#impacto/i.test(cleanMd) || /1\.\s+.*?(?:#seccion|\*\*)/i.test(cleanMd);
  const hasSchemaComplete = hasJsonLd && (/\"author\"/.test(cleanMd) || /\"publisher\"/.test(cleanMd)) && /\"datePublished\"/.test(cleanMd);
  const hasFaqSchema = /\"FAQPage\"/i.test(cleanMd);
  const hasAuthorBio = /Sobre el Autor/i.test(cleanMd);
  const hasCTA = /comparte|comenta|déjanos|suscríbete|qué opinas|contacta/i.test(cleanMd);

  // 1. Respuesta Directa GEO 2026 (40-60 palabras tras H1)
  const firstBlock = extractFirstBlockAfterH1(markdown);
  const firstBlockWords = firstBlock ? firstBlock.split(/\s+/).filter(w => w.length > 0).length : 0;
  const isGeoAnswerOptimal = firstBlockWords >= 38 && firstBlockWords <= 68;

  if (answerFirstEl) {
    if (firstBlockWords === 0) {
      answerFirstEl.innerText = "❌ No";
      answerFirstEl.style.color = "var(--color-error)";
    } else if (isGeoAnswerOptimal) {
      answerFirstEl.innerText = `✅ ${firstBlockWords} pal. (GEO)`;
      answerFirstEl.style.color = "var(--color-secondary)";
    } else {
      answerFirstEl.innerText = `⚠️ ${firstBlockWords} pal.`;
      answerFirstEl.style.color = "var(--color-gold)";
    }
  }

  // 2. Descargo Legal Ético
  const hasDisclaimer = /no constituye (?:asesor[ií]a|consejo) (?:legal|jur[ií]dic)/i.test(markdown);
  if (disclaimerEl) {
    disclaimerEl.innerText = hasDisclaimer ? "✅ Presente" : "❌ Falta";
    disclaimerEl.style.color = hasDisclaimer ? "var(--color-secondary)" : "var(--color-error)";
  }

  // 3. Términos Jurídicos detectados
  const lowerMd = markdown.toLowerCase();
  let legalTermsHits = 0;
  for (const term of LEGAL_TERMS_SET) {
    if (lowerMd.includes(term)) legalTermsHits++;
  }
  if (legalTermsEl) {
    legalTermsEl.innerText = `${legalTermsHits} detectados`;
    if (legalTermsHits >= 8) legalTermsEl.style.color = "var(--color-secondary)";
    else if (legalTermsHits >= 4) legalTermsEl.style.color = "var(--color-gold)";
    else legalTermsEl.style.color = "var(--color-error)";
  }

  // 4. H2 como preguntas (≥50%)
  let h2QuestionsCount = 0;
  if (h2Matches.length > 0) {
    const questionMarkers = /^(qué|que|cómo|como|cuándo|cuando|cuál|cual|por qué|por que|quién|quien|dónde|donde)\b/i;
    for (const h of h2Matches) {
      const hText = h.replace(/^##\s*/, "").trim();
      if (hText.includes("?") || questionMarkers.test(hText)) {
        h2QuestionsCount++;
      }
    }
  }
  const h2QuestionRatio = h2Matches.length > 0 ? (h2QuestionsCount / h2Matches.length) : 0;
  if (h2QuestionsEl) {
    if (h2Matches.length === 0) {
      h2QuestionsEl.innerText = "❌ 0/0";
      h2QuestionsEl.style.color = "var(--color-error)";
    } else {
      const pct = Math.round(h2QuestionRatio * 100);
      h2QuestionsEl.innerText = `${h2QuestionsCount}/${h2Matches.length} (${pct}%)`;
      h2QuestionsEl.style.color = h2QuestionRatio >= 0.5 ? "var(--color-secondary)" : "var(--color-gold)";
    }
  }

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

  // --- Cálculo Score Estructural SEO (0-100) ---
  let seoScore = 5;
  if (h1Matches.length === 1 && isH1WordCountOptimal) seoScore += 12;
  else if (h1Matches.length === 1) seoScore += 8;
  if (descMatch && descMatch[1].length >= 100) seoScore += 10;
  if (h2Matches.length >= 3 && isH2WordCountOptimal) seoScore += 8;
  if (boldKeywordsCount >= 6) seoScore += 7;
  if (keywordRepetition >= 3) seoScore += 7;
  if (linksCount >= 2) seoScore += 7;
  if (hasRegulatoryFramework && hasAdoptionSection) seoScore += 7;
  if (hasCopyrightSection) seoScore += 5;
  if (hasFaqSection) seoScore += 7;
  if (hasTocSection) seoScore += 5;
  if (hasSchemaComplete) seoScore += 8;
  if (hasFaqSchema) seoScore += 4;
  if (hasAuthorBio) seoScore += 5;
  if (hasCTA) seoScore += 3;
  seoScore = Math.min(100, Math.max(0, seoScore));

  if (seoScoreEl) seoScoreEl.innerText = `${seoScore}%`;
  if (seoProgressFill) {
    seoProgressFill.style.width = `${seoScore}%`;
    if (seoScore >= 80) seoProgressFill.style.background = "linear-gradient(90deg, var(--color-secondary), #00FF41)";
    else if (seoScore >= 50) seoProgressFill.style.background = "linear-gradient(90deg, var(--color-warning), var(--color-primary))";
    else seoProgressFill.style.background = "linear-gradient(90deg, var(--color-error), var(--color-warning))";
  }

  // --- Cálculo Score Calidad Jurídica & GEO 2026 (0-100) ---
  let legalPenalty = 0;
  if (!hasDisclaimer) legalPenalty += 15;
  if (!firstBlockWords || !isGeoAnswerOptimal) legalPenalty += 10;
  if (legalTermsHits < 4) legalPenalty += 15;
  else if (legalTermsHits < 8) legalPenalty += 6;
  if (h2Matches.length > 0 && h2QuestionRatio < 0.5) legalPenalty += 8;
  if (!hasAuthorBio) legalPenalty += 10;
  if (linksCount < 2) legalPenalty += 8;

  // Promesas y calcos
  for (const p of PROMISE_PATTERNS) {
    if (p.test(markdown)) legalPenalty += 15;
  }
  for (const c of ANTI_CALCOS) {
    if (c.regex.test(markdown)) legalPenalty += 4;
  }

  let legalScore = Math.max(0, Math.min(100, 100 - legalPenalty));
  if (legalQualityScoreEl) legalQualityScoreEl.innerText = `${legalScore}%`;
  if (legalProgressFill) {
    legalProgressFill.style.width = `${legalScore}%`;
    if (legalScore >= 85) legalProgressFill.style.background = "linear-gradient(90deg, var(--color-gold), var(--color-secondary))";
    else if (legalScore >= 60) legalProgressFill.style.background = "linear-gradient(90deg, var(--color-gold), var(--color-warning))";
    else legalProgressFill.style.background = "linear-gradient(90deg, var(--color-error), var(--color-gold))";
  }

  // --- Índice YMYL Combinado ---
  const combinedScore = Math.round(seoScore * 0.6 + legalScore * 0.4);
  if (combinedScoreBadge) {
    let label = "STANDBY";
    let badgeClass = "seo-score-badge";
    if (combinedScore >= 85 && hasDisclaimer) {
      label = "EXCELENTE (2026)";
      badgeClass = "seo-score-badge badge-passed";
    } else if (combinedScore >= 65) {
      label = "ACEPTABLE";
      badgeClass = "seo-score-badge badge-warn";
    } else {
      label = "REVISIÓN REQUERIDA";
      badgeClass = "seo-score-badge badge-error";
    }
    combinedScoreBadge.innerText = `${combinedScore}% · ${label}`;
    combinedScoreBadge.className = badgeClass;
  }
}

/**
 * Ejecuta la auditoría profunda server-side en el backend (/api/seo-audit)
 * y despliega el diagnóstico detallado con tags e incidencias jurídicas.
 */
export async function runBackendSeoAudit(markdown, jurisdiction = "auto") {
  if (!markdown || markdown.trim() === "") {
    toast.error("No hay contenido en el editor para realizar la auditoría.");
    return;
  }

  const btnDeepAudit = document.getElementById("btnDeepAudit");
  const issuesContainer = document.getElementById("seoAuditIssuesContainer");
  const seoScoreEl = document.getElementById("seoScore");
  const seoProgressFill = document.getElementById("seoProgressFill");
  const legalQualityScoreEl = document.getElementById("legalQualityScore");
  const legalProgressFill = document.getElementById("legalProgressFill");
  const combinedScoreBadge = document.getElementById("combinedScoreBadge");
  const terminalJurisdiction = document.getElementById("terminalJurisdiction");

  const originalBtnHtml = btnDeepAudit ? btnDeepAudit.innerHTML : "";
  if (btnDeepAudit) {
    btnDeepAudit.disabled = true;
    btnDeepAudit.innerHTML = `
      <span class="material-symbols-outlined" style="animation: spin 1s infinite linear; font-size: 1.1rem;">progress_activity</span>
      Auditando Estándares 2026...
    `;
  }

  try {
    const res = await fetch("/api/seo-audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        markdown: markdown,
        jurisdiction: jurisdiction || "auto"
      })
    });

    if (!res.ok) {
      let errDetail = res.statusText;
      try {
        const errJson = await res.json();
        if (errJson.detail) errDetail = errJson.detail;
      } catch (_) {}
      throw new Error(`Error ${res.status}: ${errDetail}`);
    }

    const data = await res.json();
    const report = data.report || {};
    const legalReport = data.legal_report || {};
    const combinedScore = data.combined_score || 0;
    const jur = data.jurisdiction || "ve";

    // 1. Sincronizar footer terminal con jurisdicción resuelta
    if (terminalJurisdiction) {
      if (jur === "co") terminalJurisdiction.innerText = "COLOMBIA 🇨🇴";
      else if (jur === "ve") terminalJurisdiction.innerText = "VENEZUELA 🇻🇪";
      else terminalJurisdiction.innerText = "INTERNACIONAL 🌐";
    }

    // 2. Actualizar marcadores con cifras oficiales backend
    if (seoScoreEl) seoScoreEl.innerText = `${report.score || 0}%`;
    if (seoProgressFill) seoProgressFill.style.width = `${report.score || 0}%`;

    if (legalQualityScoreEl) legalQualityScoreEl.innerText = `${legalReport.score || 0}%`;
    if (legalProgressFill) legalProgressFill.style.width = `${legalReport.score || 0}%`;

    if (combinedScoreBadge) {
      const isPassed = legalReport.passed && (report.score >= 80);
      combinedScoreBadge.innerText = `${combinedScore}% · ${isPassed ? "APROBADO 2026" : "REVISIÓN REQUERIDA"}`;
      combinedScoreBadge.className = `seo-score-badge ${isPassed ? "badge-passed" : (combinedScore >= 60 ? "badge-warn" : "badge-error")}`;
    }

    // 3. Renderizar contenedor de diagnóstico e incidencias
    if (issuesContainer) {
      issuesContainer.style.display = "flex";
      issuesContainer.innerHTML = "";

      const allIssues = [];

      // Incidencias del validador jurídico
      if (legalReport.issues && legalReport.issues.length > 0) {
        legalReport.issues.forEach(i => {
          allIssues.push({
            level: i.level || "warning",
            category: i.rule ? `[${i.rule.toUpperCase()}]` : "[LEGAL]",
            message: i.message
          });
        });
      }

      // Violaciones estructurales SEO
      if (report.violations && report.violations.length > 0) {
        report.violations.forEach(v => {
          allIssues.push({
            level: "warning",
            category: "[SEO ON-PAGE]",
            message: v
          });
        });
      }

      // Si no hay problemas
      if (allIssues.length === 0) {
        const chip = document.createElement("div");
        chip.className = "seo-issue-chip chip-success";
        chip.innerHTML = `
          <span class="material-symbols-outlined" style="font-size: 1rem; color: var(--color-secondary);">verified</span>
          <div><strong>100% Óptimo:</strong> El artículo cumple rigurosamente con los estándares SEO 2026, formato GEO y deontología jurídica (${jur.toUpperCase()}).</div>
        `;
        issuesContainer.appendChild(chip);
      } else {
        // Encabezado resumen
        const header = document.createElement("div");
        header.style.cssText = "font-weight: 700; color: var(--text-primary); margin-bottom: 2px; display: flex; justify-content: space-between;";
        header.innerHTML = `
          <span>Diagnóstico (${jur.toUpperCase()}): ${allIssues.length} puntos de mejora</span>
          <span style="font-size: 0.72rem; color: var(--text-secondary);">GEO & YMYL 2026</span>
        `;
        issuesContainer.appendChild(header);

        allIssues.forEach(item => {
          const chip = document.createElement("div");
          let chipClass = "chip-warning";
          let icon = "warning";
          if (item.level === "error") {
            chipClass = "chip-error";
            icon = "error";
          } else if (item.level === "info") {
            chipClass = "chip-info";
            icon = "info";
          }
          chip.className = `seo-issue-chip ${chipClass}`;
          chip.innerHTML = `
            <span class="material-symbols-outlined" style="font-size: 0.95rem; margin-top: 1px;">${icon}</span>
            <div><strong>${item.category}</strong> ${item.message}</div>
          `;
          issuesContainer.appendChild(chip);
        });
      }
    }

    if (legalReport.passed) {
      toast.success(`Auditoría SEO & Jurídica completada: ¡Artículo aprobado (${combinedScore}%)!`);
    } else {
      toast.info(`Auditoría finalizada: Se detectaron puntos clave a corregir (Índice: ${combinedScore}%).`);
    }

  } catch (err) {
    console.error("Error en runBackendSeoAudit:", err);
    toast.error(`Fallo al consultar auditoría: ${err.message}`);
  } finally {
    if (btnDeepAudit) {
      btnDeepAudit.disabled = false;
      btnDeepAudit.innerHTML = originalBtnHtml;
    }
  }
}
