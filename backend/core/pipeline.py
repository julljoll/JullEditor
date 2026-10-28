"""
Orquestador del Pipeline Agéntico de 4 Etapas para JullEditor v4.0.
Coordina Analista -> Investigador RAG -> Redactor Granite -> Crítico Adversarial.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Callable
from typing import Any

from backend.core.agent_analyst import AnalystAgent
from backend.core.agent_critic import CriticAgent
from backend.core.agent_researcher import ResearcherAgent
from backend.core.agent_writer import WriterAgent


class EditorialPipeline:
    """Pipeline canónico de redacción editorial asistida por agentes autónomos."""

    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "granite3.3:8b",
    ):
        self.analyst = AnalystAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent(ollama_url=ollama_url, model=model)
        self.critic = CriticAgent()

    async def run(
        self,
        source_text: str,
        config: dict[str, Any] | None = None,
        on_token: Callable[[str], None] | None = None,
        on_stage: Callable[[str, Any], None] | None = None,
    ) -> dict[str, Any]:
        """Ejecuta secuencialmente las 4 etapas del pipeline."""
        cfg = config or {}

        # Etapa 1: Análisis
        if on_stage:
            on_stage("stage_start", {"stage": 1, "name": "Analista Documental"})
        analysis = await self.analyst.analyze(source_text, cfg)
        if on_stage:
            on_stage("stage_done", {"stage": 1, "data": analysis})

        # Etapa 2: Investigación RAG
        if on_stage:
            on_stage("stage_start", {"stage": 2, "name": "Investigador RAG Normativo"})
        dossier = await self.researcher.research(analysis, cfg)
        if on_stage:
            on_stage("stage_done", {"stage": 2, "data": dossier})

        # Etapa 3: Redacción (con streaming token a token)
        if on_stage:
            on_stage("stage_start", {"stage": 3, "name": "Redactor IBM Granite"})
        draft = await self.writer.write(source_text, analysis, dossier, cfg, on_token=on_token)
        if on_stage:
            on_stage("stage_done", {"stage": 3, "length": len(draft)})

        # Etapa 4: Crítica y Revisión Adversarial
        if on_stage:
            on_stage("stage_start", {"stage": 4, "name": "Auditor Legal y Crítico"})
        review = await self.critic.review(draft, dossier, cfg)
        if on_stage:
            on_stage("stage_done", {"stage": 4, "data": review})

        return {
            "status": "success",
            "article": review["final_article"],
            "score": review["score"],
            "passed": review["passed"],
            "patch_notes": review["patch_notes"],
            "analysis": analysis,
            "dossier": dossier,
            "review": review,
        }

    async def run_streaming(
        self,
        source_text: str,
        config: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generador asíncrono para streaming SSE con actualizaciones de etapa y tokens."""
        queue: asyncio.Queue = asyncio.Queue()

        def _on_token(token: str):
            queue.put_nowait({"type": "token", "token": token})

        def _on_stage(event_name: str, payload: Any):
            queue.put_nowait({"type": event_name, "payload": payload})

        async def _worker():
            try:
                res = await self.run(source_text, config, on_token=_on_token, on_stage=_on_stage)
                queue.put_nowait({"type": "completed", "result": res})
            except Exception as e:
                queue.put_nowait({"type": "error", "error": str(e)})
            finally:
                queue.put_nowait(None)

        task = asyncio.create_task(_worker())

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

        await task
