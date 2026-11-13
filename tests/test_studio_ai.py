from pathlib import Path

from fastapi.testclient import TestClient

from backend import studio_ai
from backend.app import app

client = TestClient(app)


def test_studio_template_does_not_render_or_persist_provider_keys():
    template = Path(__file__).parents[1] / "frontend" / "src" / "pages" / "studio.astro"
    source = template.read_text(encoding="utf-8")

    assert "apiKeyInput" not in source
    assert "name=\"api_key\"" not in source
    assert "api_key:" not in source
    assert "localStorage.setItem('julleditor_gemini_api_key'" not in source
    assert "localStorage.removeItem('julleditor_gemini_api_key')" in source


def test_ai_status_uses_backend_configured_ollama_endpoint(monkeypatch):
    endpoint = "http://ollama.internal:11434"
    monkeypatch.setenv("OLLAMA_BASE_URL", endpoint)

    async def fake_status(endpoint):
        return {"connected": True, "models": ["phi3"], "message": endpoint}

    monkeypatch.setattr(studio_ai, "_check_local_phi_status", fake_status)

    response = client.get("/api/ai-status")

    assert response.status_code == 200
    assert response.json() == {
        "connected": True,
        "models": ["phi3"],
        "message": endpoint,
    }


def test_ai_chat_is_disabled_for_article_only_studio():
    response = client.post("/api/ai-chat", json={})

    assert response.status_code == 410


def test_ai_action_preserves_generated_article_metadata(monkeypatch):
    async def fake_generate(prompt, system_instruction, provider, temperature, max_tokens):
        assert "Categoría: LegalTech" in prompt
        assert "Devuelve exactamente un objeto JSON" in system_instruction
        assert provider == "google"
        assert temperature == 0.25
        assert max_tokens == 8000
        return {
            "text": (
                '{"description":"Descripción generada","tags":["legaltech"],'
                '"body":"## Análisis\\n\\nContenido del artículo"}'
            ),
            "providerUsed": "google",
            "modelName": "test-google-model",
        }

    monkeypatch.setattr(studio_ai, "_generate_with_provider", fake_generate)
    response = client.post(
        "/api/ai-action",
        json={
            "source_text": "Notas de prueba",
            "title": "Análisis LegalTech",
            "author": "Autora de prueba",
            "theme": "LegalTech",
            "provider": "google",
            "seo_keyword": "legaltech",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["action"] == "generate"
    assert data["title"] == "Análisis LegalTech"
    assert data["content"].startswith("---\n")
    assert "<" not in data["content"]
    assert "# Análisis LegalTech" not in data["content"]
    assert data["description"] == "Descripción generada"
    assert data["slug"] == "analisis-legaltech"
    assert data["seoKeyword"] == "legaltech"
    assert data["category"] == "LegalTech"
    assert data["content"].endswith("Contenido del artículo")
    assert data["words"] > 0
    assert data["readingTime"] == 1
    assert data["provider"] == "google"
    assert data["model"] == "test-google-model"


def test_ai_action_does_not_return_client_submitted_provider_key(monkeypatch):
    secret = "client-submitted-test-key"

    async def fail_missing_configuration(*args):
        assert all(secret not in repr(argument) for argument in args)
        raise studio_ai.ProviderConfigurationError("Configura OPENAI_API_KEY en el backend.")

    monkeypatch.setattr(studio_ai, "_generate_with_provider", fail_missing_configuration)
    response = client.post(
        "/api/ai-action",
        json={
            "source_text": "Notas de prueba",
            "title": "Artículo LegalTech de prueba",
            "author": "Autora de prueba",
            "provider": "openai",
            "api_key": secret,
        },
    )

    assert response.status_code == 503
    assert secret not in response.text
    assert "api_key" not in response.text


def test_ai_action_rejects_non_generation_actions():
    response = client.post(
        "/api/ai-action",
        json={
            "action": "summarize",
            "title": "Artículo de prueba",
            "author": "Autora de prueba",
        },
    )

    assert response.status_code == 422
