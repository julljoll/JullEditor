"""
Paquete RAG Vectorial & Híbrido Jurídico de JullEditor v4.0.
"""

from backend.rag.chunker import LegalChunker
from backend.rag.reranker import HybridReranker
from backend.rag.vector_store import LegalVectorStore

__all__ = [
    "LegalChunker",
    "HybridReranker",
    "LegalVectorStore",
]
