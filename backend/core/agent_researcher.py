"""
Agente Investigador (Etapa 2 del Pipeline Agéntico de JullEditor v4.0).
Consulta el RAG Vectorial e Híbrido local para armar un Dossier Fáctico sin alucinaciones.
"""

from __future__ import annotations

from typing import Any

from backend.rag.vector_store import LegalVectorStore
from backend.rag_manager import retrieve_legal_context


class ResearcherAgent:
    """Investiga y consolida el cuerpo normativo y fáctico necesario para la redacción."""

    def __init__(self, vector_store: LegalVectorStore | None = None):
        self.vector_store = vector_store or LegalVectorStore()

    async def research(
        self,
        analysis: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cfg = config or {}
        theme = analysis.get("theme", "cybersecurity")
        primary_kw = analysis.get("primary_keyword", "")
        lead_summary = analysis.get("lead_summary", "")
        jurisdiction = analysis.get("jurisdiction", "ve")

        search_query = f"{primary_kw} {lead_summary} {theme}".strip()

        # 1. Recuperar contexto legal estructurado (con fallback léxico garantizado)
        legal_rag_context = retrieve_legal_context(
            query_text=search_query,
            theme=theme,
            top_k=3,
            jurisdiction=jurisdiction,
        )

        # 2. Fragmentos vectoriales específicos
        vector_chunks: list[dict[str, Any]] = []
        if self.vector_store.is_indexed() and jurisdiction == "ve":
            vector_chunks = self.vector_store.search(search_query, top_k=3)

        dossier = {
            "query": search_query,
            "theme": theme,
            "jurisdiction": jurisdiction,
            "legal_rag_context": legal_rag_context,
            "verified_vector_chunks": vector_chunks,
            "prohibited_hallucinations": [
                "Ley Orgánica de Protección de Datos Personales (NO EXISTE EN VENEZUELA)",
                "Artículos inventados fuera del texto legal suministrado",
                "Sentencias ficticias sin número o Sala real",
            ],
            "dossier_ready": True,
        }

        return dossier
