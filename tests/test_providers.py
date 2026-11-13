import asyncio

import pytest

from backend import providers


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300

    def json(self):
        return self.data


def mock_provider_response(monkeypatch, data, status_code=200):
    requests = []

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, headers, json):
            requests.append({"url": url, "headers": headers, "json": json})
            return MockResponse(data, status_code)

    monkeypatch.setattr(providers.httpx, "AsyncClient", lambda **_kwargs: MockClient())
    return requests


def test_google_provider_uses_server_key_header_and_official_request_shape(monkeypatch):
    secret = "google-test-secret"
    requests = mock_provider_response(
        monkeypatch,
        {"candidates": [{"content": {"parts": [{"text": "Respuesta"}]}}]},
    )
    adapter = providers.GoogleProvider("gemini-test-model", secret)

    result = asyncio.run(
        adapter.complete([{"role": "user", "content": "Pregunta"}], "Sistema", 0.2, 500)
    )

    request = requests[0]
    assert request["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-test-model:generateContent"
    )
    assert request["headers"] == {"x-goog-api-key": secret}
    assert request["json"] == {
        "systemInstruction": {"parts": [{"text": "Sistema"}]},
        "contents": [{"role": "user", "parts": [{"text": "Pregunta"}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 500},
    }
    assert secret not in repr(adapter)
    assert result.text == "Respuesta"
    assert result.provider == "google"


def test_openai_provider_uses_bearer_header_and_chat_completions(monkeypatch):
    secret = "openai-test-secret"
    requests = mock_provider_response(
        monkeypatch,
        {"choices": [{"message": {"content": "Respuesta"}}]},
    )
    adapter = providers.OpenAIProvider("openai-test-model", secret)

    result = asyncio.run(
        adapter.complete([{"role": "user", "content": "Pregunta"}], "Sistema", 0.3, 600)
    )

    request = requests[0]
    assert request["url"] == "https://api.openai.com/v1/chat/completions"
    assert request["headers"] == {"Authorization": f"Bearer {secret}"}
    assert request["json"] == {
        "model": "openai-test-model",
        "messages": [
            {"role": "system", "content": "Sistema"},
            {"role": "user", "content": "Pregunta"},
        ],
        "max_completion_tokens": 600,
    }
    assert secret not in repr(adapter)
    assert result.text == "Respuesta"
    assert result.provider == "openai"


def test_anthropic_provider_uses_key_and_version_headers(monkeypatch):
    secret = "anthropic-test-secret"
    requests = mock_provider_response(
        monkeypatch,
        {"content": [{"type": "text", "text": "Respuesta"}]},
    )
    adapter = providers.AnthropicProvider("anthropic-test-model", secret)

    result = asyncio.run(
        adapter.complete([{"role": "user", "content": "Pregunta"}], "Sistema", 0.4, 700)
    )

    request = requests[0]
    assert request["url"] == "https://api.anthropic.com/v1/messages"
    assert request["headers"] == {
        "x-api-key": secret,
        "anthropic-version": providers.ANTHROPIC_API_VERSION,
    }
    assert request["json"] == {
        "model": "anthropic-test-model",
        "system": "Sistema",
        "messages": [{"role": "user", "content": "Pregunta"}],
        "temperature": 0.4,
        "max_tokens": 700,
    }
    assert secret not in repr(adapter)
    assert result.text == "Respuesta"
    assert result.provider == "anthropic"


def test_ollama_provider_uses_configured_local_model(monkeypatch):
    requests = mock_provider_response(
        monkeypatch,
        {"message": {"content": "Respuesta local"}},
    )
    adapter = providers.OllamaProvider("http://ollama.local:11434", "granite-test")

    result = asyncio.run(
        adapter.complete([{"role": "user", "content": "Pregunta"}], "Sistema", 0.1, 200)
    )

    request = requests[0]
    assert request["url"] == "http://ollama.local:11434/api/chat"
    assert request["headers"] == {}
    assert request["json"] == {
        "model": "granite-test",
        "messages": [
            {"role": "system", "content": "Sistema"},
            {"role": "user", "content": "Pregunta"},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 200},
    }
    assert result.provider == "local"
    assert result.text == "Respuesta local"


def test_ollama_provider_supports_openai_compatible_local_endpoint(monkeypatch):
    requests = mock_provider_response(
        monkeypatch,
        {"choices": [{"message": {"content": "Respuesta local"}}]},
    )
    adapter = providers.OllamaProvider("http://ollama.local:11434/v1", "granite-test")

    result = asyncio.run(
        adapter.complete([{"role": "user", "content": "Pregunta"}], "Sistema", 0.1, 200)
    )

    request = requests[0]
    assert request["url"] == "http://ollama.local:11434/v1/chat/completions"
    assert request["json"] == {
        "model": "granite-test",
        "messages": [
            {"role": "system", "content": "Sistema"},
            {"role": "user", "content": "Pregunta"},
        ],
        "temperature": 0.1,
        "max_tokens": 200,
    }
    assert result.provider == "local"
    assert result.text == "Respuesta local"


def test_get_provider_requires_server_configuration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "configured-only-server-side")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    with pytest.raises(providers.ProviderConfigurationError) as error:
        providers.get_provider("google")

    assert "GEMINI_MODEL" in str(error.value)
    assert "configured-only-server-side" not in str(error.value)


def test_provider_upstream_error_does_not_reflect_secret_or_response_body(monkeypatch):
    secret = "upstream-error-secret"
    requests = mock_provider_response(
        monkeypatch,
        {"error": {"message": secret}},
        status_code=401,
    )
    adapter = providers.OpenAIProvider("openai-test-model", secret)

    with pytest.raises(providers.ProviderError) as error:
        asyncio.run(
            adapter.complete([{"role": "user", "content": "Pregunta"}], "Sistema", 0.2, 100)
        )

    assert secret not in str(error.value)
    assert secret not in repr(error.value)
    assert requests[0]["json"]["model"] == "openai-test-model"
