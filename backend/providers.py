"""Server-side text generation adapters for configured AI providers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from urllib.parse import quote, urlsplit

import httpx

ProviderName = Literal["local", "google", "openai", "anthropic"]
Message = dict[str, str]
ANTHROPIC_API_VERSION = "2026-10-21"


class ProviderError(RuntimeError):
    """Safe provider error suitable for returning to an API client."""


class ProviderConfigurationError(ProviderError):
    """A provider is missing required server-side configuration."""


@dataclass(frozen=True)
class ProviderResult:
    text: str
    provider: ProviderName
    model: str


class TextProvider(Protocol):
    provider: ProviderName
    model: str

    async def complete(
        self,
        messages: list[Message],
        system_instruction: str,
        temperature: float,
        max_tokens: int,
    ) -> ProviderResult: ...


async def _post_json(
    provider_name: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise ProviderError(f"El proveedor {provider_name} excedió el tiempo de respuesta.") from None
    except httpx.HTTPError:
        raise ProviderError(f"No se pudo conectar con el proveedor {provider_name}.") from None

    if not response.is_success:
        raise ProviderError(
            f"El proveedor {provider_name} respondió con HTTP {response.status_code}."
        )
    try:
        data = response.json()
    except (ValueError, TypeError):
        raise ProviderError(
            f"El proveedor {provider_name} devolvió una respuesta inválida."
        ) from None
    if not isinstance(data, dict):
        raise ProviderError(
            f"El proveedor {provider_name} devolvió una respuesta inválida."
        )
    return data


def _text_from_blocks(blocks: Any) -> str:
    if not isinstance(blocks, list):
        return ""
    return "".join(
        block.get("text", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ).strip()


def validate_local_endpoint(endpoint: str) -> str:
    clean_endpoint = endpoint.strip().rstrip("/")
    parsed = urlsplit(clean_endpoint)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ProviderConfigurationError(
            "OLLAMA_BASE_URL debe ser una URL HTTP(S) sin credenciales, query ni fragmento."
        )
    return clean_endpoint


@dataclass(frozen=True)
class GoogleProvider:
    model: str
    api_key: str = field(repr=False)
    provider: Literal["google"] = "google"

    async def complete(
        self,
        messages: list[Message],
        system_instruction: str,
        temperature: float,
        max_tokens: int,
    ) -> ProviderResult:
        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
        ]
        data = await _post_json(
            "Google Gemini",
            f"https://generativelanguage.googleapis.com/v1beta/models/{quote(self.model, safe='')}:generateContent",
            {"x-goog-api-key": self.api_key},
            {
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
        )
        candidates = data.get("candidates")
        parts = (
            candidates[0].get("content", {}).get("parts", [])
            if isinstance(candidates, list) and candidates and isinstance(candidates[0], dict)
            else []
        )
        text = _text_from_blocks(
            [{"type": "text", "text": part.get("text", "")} for part in parts if isinstance(part, dict)]
        )
        if not text:
            raise ProviderError("Google Gemini no devolvió contenido de texto.")
        return ProviderResult(text, self.provider, self.model)


@dataclass(frozen=True)
class OpenAIProvider:
    model: str
    api_key: str = field(repr=False)
    provider: Literal["openai"] = "openai"

    async def complete(
        self,
        messages: list[Message],
        system_instruction: str,
        temperature: float,
        max_tokens: int,
    ) -> ProviderResult:
        data = await _post_json(
            "OpenAI",
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {self.api_key}"},
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    *messages,
                ],
                "max_completion_tokens": max_tokens,
            },
        )
        choices = data.get("choices")
        message = (
            choices[0].get("message", {})
            if isinstance(choices, list) and choices and isinstance(choices[0], dict)
            else {}
        )
        content = message.get("content", "") if isinstance(message, dict) else ""
        text = content.strip() if isinstance(content, str) else _text_from_blocks(content)
        if not text:
            raise ProviderError("OpenAI no devolvió contenido de texto.")
        return ProviderResult(text, self.provider, self.model)


@dataclass(frozen=True)
class AnthropicProvider:
    model: str
    api_key: str = field(repr=False)
    provider: Literal["anthropic"] = "anthropic"

    async def complete(
        self,
        messages: list[Message],
        system_instruction: str,
        temperature: float,
        max_tokens: int,
    ) -> ProviderResult:
        data = await _post_json(
            "Anthropic",
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": self.api_key,
                "anthropic-version": ANTHROPIC_API_VERSION,
            },
            {
                "model": self.model,
                "system": system_instruction,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        text = _text_from_blocks(data.get("content"))
        if not text:
            raise ProviderError("Anthropic no devolvió contenido de texto.")
        return ProviderResult(text, self.provider, self.model)


@dataclass(frozen=True)
class OllamaProvider:
    endpoint: str
    model: str
    provider: Literal["local"] = "local"

    async def complete(
        self,
        messages: list[Message],
        system_instruction: str,
        temperature: float,
        max_tokens: int,
    ) -> ProviderResult:
        messages = [
            {"role": "system", "content": system_instruction},
            *messages,
        ]
        if self.endpoint.endswith("/v1"):
            url = f"{self.endpoint}/chat/completions"
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        else:
            url = f"{self.endpoint}/api/chat"
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
        data = await _post_json("Local", url, {}, payload)
        if self.endpoint.endswith("/v1"):
            choices = data.get("choices")
            message = (
                choices[0].get("message", {})
                if isinstance(choices, list) and choices and isinstance(choices[0], dict)
                else {}
            )
            text = message.get("content", "").strip() if isinstance(message, dict) else ""
        else:
            message = data.get("message", {})
            text = message.get("content", "").strip() if isinstance(message, dict) else ""
        if not text:
            raise ProviderError("Ollama local no devolvió contenido de texto.")
        return ProviderResult(text, self.provider, self.model)


def normalize_provider(provider: str) -> ProviderName:
    aliases = {"phi": "local", "gemini": "google"}
    normalized = aliases.get(provider, provider)
    if normalized == "local":
        return "local"
    if normalized == "google":
        return "google"
    if normalized == "openai":
        return "openai"
    if normalized == "anthropic":
        return "anthropic"
    raise ProviderConfigurationError("Proveedor de IA no soportado.")


def _required_environment(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ProviderConfigurationError(
            f"Configura {name} en el entorno del backend para usar este proveedor."
        )
    return value


def _required_model(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ProviderConfigurationError(
            f"Configura {name} con un identificador de modelo vigente en el backend."
        )
    return value


def get_provider(
    provider: str,
    local_endpoint: str | None = None,
    local_model: str | None = None,
) -> TextProvider:
    provider_name = normalize_provider(provider)
    if provider_name == "google":
        return GoogleProvider(
            model=_required_model("GEMINI_MODEL"),
            api_key=_required_environment("GEMINI_API_KEY"),
        )
    if provider_name == "openai":
        return OpenAIProvider(
            model=_required_model("OPENAI_MODEL"),
            api_key=_required_environment("OPENAI_API_KEY"),
        )
    if provider_name == "anthropic":
        return AnthropicProvider(
            model=_required_model("ANTHROPIC_MODEL"),
            api_key=_required_environment("ANTHROPIC_API_KEY"),
        )

    endpoint = local_endpoint or os.getenv("OLLAMA_BASE_URL", "").strip() or "http://localhost:11434"
    model = (
        (local_model or "").strip()
        or os.getenv("OLLAMA_MODEL", "").strip()
        or os.getenv("GRANITE_MODEL", "").strip()
        or "granite3.3:8b"
    )
    return OllamaProvider(
        endpoint=validate_local_endpoint(endpoint),
        model=model,
    )
