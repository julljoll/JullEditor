"""
Paquete modular de Prompts Especializados para JullEditor v4.0.
Re-exporta la interfaz canónica para garantizar 100% de retrocompatibilidad.
"""

from __future__ import annotations

from backend.prompts.base import (
    MAGAZINE_INTERPRETATIVE_BLOCK,
    SYSTEM_BASE_PROMPT,
    THEMATIC_PROMPTS,
    THEMATIC_PROMPTS_NEUTRAL,
)
from backend.prompts.blog_writer import build_generation_prompt
from backend.prompts.critic import CRITIC_SYSTEM_PROMPT, build_critic_prompt
from backend.prompts.researcher import RESEARCHER_SYSTEM_PROMPT, build_researcher_prompt
from backend.prompts.sentencia_tsj import (
    SENTENCIA_TSJ_OUTPUT_TEMPLATE,
    SENTENCIA_TSJ_SYSTEM_PROMPT,
    build_sentencia_tsj_prompt,
)

__all__ = [
    "SYSTEM_BASE_PROMPT",
    "THEMATIC_PROMPTS",
    "THEMATIC_PROMPTS_NEUTRAL",
    "MAGAZINE_INTERPRETATIVE_BLOCK",
    "SENTENCIA_TSJ_SYSTEM_PROMPT",
    "SENTENCIA_TSJ_OUTPUT_TEMPLATE",
    "CRITIC_SYSTEM_PROMPT",
    "RESEARCHER_SYSTEM_PROMPT",
    "build_generation_prompt",
    "build_sentencia_tsj_prompt",
    "build_critic_prompt",
    "build_researcher_prompt",
]
