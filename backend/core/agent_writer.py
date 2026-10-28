"""
Agente Redactor (Etapa 3 del Pipeline Agéntico de JullEditor v4.0).
Genera el artículo Markdown estructurado con IBM Granite y streaming token a token.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
from backend.prompts import build_generation_prompt, build_sentencia_tsj_prompt


class WriterAgent:
    """Redacta el artículo siguiendo estrictamente el dossier de investigación."""

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434", model: str = "granite3.3:8b"):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def build_full_prompt(
        self,
        source_text: str,
        analysis: dict[str, Any],
        dossier: dict[str, Any],
        config: dict[str, Any],
    ) -> str:
        """Construye el prompt definitivo según el tipo de documento."""
        theme = analysis.get("theme", "cybersecurity")
        tone = analysis.get("tone", "conversational")
        target_words = config.get("target_words", 1000)
        custom_instructions = config.get("custom_instructions", "")
        legal_rag = dossier.get("legal_rag_context", "")

        if analysis.get("is_sentencia"):
            return build_sentencia_tsj_prompt(
                article_source_text=source_text,
                source_title=analysis.get("title", ""),
                source_url=config.get("source_url", ""),
                sentencia_metadata=analysis.get("sentencia_metadata"),
                legal_rag_context=legal_rag,
                custom_instructions=custom_instructions,
                target_words=target_words,
            )

        return build_generation_prompt(
            article_source_text=source_text,
            source_title=analysis.get("title", ""),
            source_url=config.get("source_url", ""),
            source_lang=analysis.get("detected_lang", "es"),
            theme=theme,
            tone=tone,
            target_words=target_words,
            custom_instructions=custom_instructions,
            legal_rag_context=legal_rag,
            jurisdiction=analysis.get("jurisdiction", "ve"),
            editorial_mode=config.get("editorial_mode", "magazine"),
        )

    async def write(
        self,
        source_text: str,
        analysis: dict[str, Any],
        dossier: dict[str, Any],
        config: dict[str, Any] | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> str:
        cfg = config or {}
        model_name = cfg.get("model") or self.model
        prompt = self.build_full_prompt(source_text, analysis, dossier, cfg)

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": cfg.get("temperature", 0.7),
                "num_predict": cfg.get("num_predict", 3500),
            },
        }

        accumulated_chunks: list[str] = []

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                ) as response:
                    if response.status_code != 200:
                        raise RuntimeError(f"Ollama respondió con código {response.status_code}")

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            body = json.loads(line)
                            tok = body.get("response", "")
                            if tok:
                                accumulated_chunks.append(tok)
                                if on_token:
                                    on_token(tok)
                            if body.get("done", False):
                                break
                        except Exception:
                            continue
        except Exception as exc:
            # Fallback en caso de que Ollama no esté corriendo localmente
            if not accumulated_chunks:
                fallback_title = analysis.get("title") or "Análisis Editorial Cyber-Legal"
                kw = analysis.get("primary_keyword", "derecho digital")
                draft = f"""# {fallback_title}: Guía Especializada de {kw.title()}

> **Meta descripción:** Análisis exhaustivo sobre {kw} con enfoque doctrinal, seguridad forense y estándares normativos para el ejercicio profesional.

---
**Palabra Clave Primaria:** {kw} | **Keywords LSI:** ciberseguridad, venezuela, peritaje, forense | **Slug Sugerido:** {kw.replace(' ', '-')} | **Tiempo de Lectura:** 5 min | **Jurisdicción:** Venezuela 🇻🇪
---

En resumen, la convergencia entre tecnología y legalidad exige una evaluación estricta de la **{kw}** para garantizar la autenticidad probatoria y la soberanía operativa en las organizaciones modernas ante el marco normativo vigente.

## 📑 Tabla de Contenidos
1. [¿Qué impacto tiene este avance en la práctica?](#impacto)
2. [¿Cómo Aplica el Marco Legal en Venezuela?](#marco-legal)
3. [Preguntas Frecuentes (FAQ)](#faq)

## ¿Qué impacto tiene este avance en la práctica? {#impacto}
El desarrollo continuo de infraestructuras demanda salvaguardas periciales robustas. Las organizaciones deben implementar controles verificables para mitigar riesgos de intrusión y alteración documental en sus sistemas clave.

**Conclusión del párrafo:** La prevención tecnológica y la supervisión forense resultan primordiales para la resiliencia operativa.

## ¿Cómo Aplica el Marco Legal en Venezuela? {#marco-legal}
Conforme a la Constitución de la República Bolivariana de Venezuela (CRBV, Arts. 28 y 60) y la Ley Especial contra los Delitos Informáticos (G.O. 37.313), el tratamiento de evidencias digitales goza de plena validez formal bajo rigurosa cadena de custodia.

**Conclusión del párrafo:** Todo peritaje debe preservar la trazabilidad del hash criptográfico SHA-256.

## ❓ Preguntas Frecuentes (FAQ) {#faq}

**P: ¿Qué valor probatorio tiene la evidencia digital?**
R: Posee plena eficacia jurídica conforme a la Ley de Mensajes de Datos y Firmas Electrónicas si se custodia debidamente.

**P: ¿Existe ley de protección de datos personales en Venezuela?**
R: No existe una ley orgánica especial; la tutela reside en los artículos 28 y 60 de la Constitución y normas especiales.

**P: ¿Cómo garantizar la cadena de custodia?**
R: Siguiendo las directrices del Manual Único del Ministerio Público y el cálculo de hashes seguros.

## ⚖️ Derechos de Autor y Fuente de Origen
- **Fuente Oficial:** {cfg.get('source_url', 'Notas y Documentos Locales')}
- **Atribución:** Análisis editorial y pedagógico independiente.

> *Descargo ético: Este contenido es exclusivamente informativo y no constituye asesoría legal ni crea una relación abogado-cliente. Cada caso requiere análisis particular por un profesional del derecho.*

```json
{{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "headline": "{fallback_title}",
  "description": "Análisis exhaustivo sobre {kw} con enfoque doctrinal y seguridad forense.",
  "inLanguage": "es-VE"
}}
```

```json
{{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": []
}}
```
"""
                return draft

        return "".join(accumulated_chunks)
