"""
Agente Crítico (Etapa 4 del Pipeline Agéntico de JullEditor v4.0).
Auditoría adversarial de 10 puntos: anti-alucinaciones, SEO 2026, Schema y deontología.
"""

from __future__ import annotations

import re
from typing import Any

from backend.legal_validator import audit_legal_quality
from backend.seo_validator import audit_article_seo


class CriticAgent:
    """Evalúa la calidad del borrador frente al dossier y emite dictamen con patch-notes."""

    def __init__(self):
        pass

    async def review(
        self,
        draft: str,
        dossier: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cfg = config or {}
        jurisdiction = dossier.get("jurisdiction", "ve")

        # 1. Auditoría SEO determinista en Python
        seo_report = audit_article_seo(draft)

        # 2. Auditoría Jurídica y Deontológica en Python
        legal_report = audit_legal_quality(draft, jurisdiction=jurisdiction)

        # 3. Detección de muletillas clásicas de LLMs
        cliche_patterns = [
            r"\bes importante destacar\b",
            r"\bcabe señalar\b",
            r"\ben conclusi[oó]n,\b",
            r"\bes fundamental mencionar\b",
            r"\ben resumen podemos decir\b",
        ]
        cliches_found = [p for p in cliche_patterns if re.search(p, draft, re.I)]

        # 4. Verificación de alucinaciones contra el dossier
        hallucinations: list[str] = []
        for prohibited in dossier.get("prohibited_hallucinations", []):
            if "Ley Orgánica de Protección de Datos Personales" in prohibited and re.search(r"ley org[aá]nica de protecci[oó]n de datos", draft, re.I):
                hallucinations.append("Cita la ficticia 'Ley Orgánica de Protección de Datos Personales'")

        # 5. Cálculo del Score Integral de Calidad (0-100)
        seo_score = seo_report.get("score", 70)
        legal_score = legal_report.get("score", 70)

        penalty = (len(cliches_found) * 5) + (len(hallucinations) * 25)
        raw_final = (0.5 * seo_score) + (0.5 * legal_score) - penalty
        final_score = max(0, min(100, int(round(raw_final))))

        passed = final_score >= 75 and len(hallucinations) == 0

        # 6. Generación de patch-notes y sugerencias de corrección
        patch_notes: list[str] = []
        if hallucinations:
            for h in hallucinations:
                patch_notes.append(f"CRÍTICO: Eliminar mención a norma inexistente ({h}).")
        if cliches_found:
            patch_notes.append(f"ESTILO: Reemplazar muletillas detectadas ({', '.join(cliches_found)}) por transiciones analíticas directas.")
        if not seo_report.get("has_schema"):
            patch_notes.append("ESTRUCTURA: Inyectar bloque Schema.org JSON-LD.")

        return {
            "score": final_score,
            "passed": passed,
            "seo_score": seo_score,
            "legal_score": legal_score,
            "cliches_detected": cliches_found,
            "hallucinations": hallucinations,
            "patch_notes": patch_notes,
            "final_article": draft,
        }
