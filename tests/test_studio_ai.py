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


def test_ai_chat_requires_messages_or_instruction():
    response = client.post("/api/ai-chat", json={})

    assert response.status_code == 400
    assert response.json()["error"] == "No se enviaron mensajes para la conversación."


def test_ai_chat_preserves_response_contract(monkeypatch):
    async def fake_chat(messages, system_instruction, provider):
        assert messages[-1] == {"role": "user", "content": "Corrige el texto"}
        assert "ARTÍCULO ACTUAL EN EL EDITOR DEL USUARIO" in system_instruction
        assert provider == "local"
        return {
            "reply": "```markdown\n---\ntitle: Prueba\n---\n<div class=\"editorial-container\">Texto</div>\n```",
            "providerUsed": "local",
            "modelName": "phi3",
        }

    monkeypatch.setattr(studio_ai, "_chat_with_model", fake_chat)
    response = client.post(
        "/api/ai-chat",
        json={
            "messages": [{"role": "user", "content": "Corrige el texto"}],
            "current_article": "Borrador",
            "provider": "local",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["providerUsed"] == "local"
    assert data["modelName"] == "phi3"
    assert data["updatedArticle"] == "---\ntitle: Prueba\n---\n<div class=\"editorial-container\">Texto</div>"


def test_ai_action_preserves_generated_article_metadata(monkeypatch):
    async def fake_generate(prompt, system_instruction, provider, temperature, max_tokens):
        assert "Tema: LegalTech" in prompt
        assert provider == "google"
        assert temperature == 0.25
        assert max_tokens == 6500
        return {
            "text": (
                '---\ntitle: "Análisis LegalTech"\n'
                'description: "Descripción generada"\n'
                'slug: "analisis-legaltech"\n'
                'seoKeyword: "legaltech"\n'
                'category: "LegalTech"\n---\n'
                "Contenido del artículo"
            ),
            "providerUsed": "google",
            "modelName": "test-google-model",
        }

    monkeypatch.setattr(studio_ai, "_generate_with_provider", fake_generate)
    response = client.post(
        "/api/ai-action",
        json={"source_text": "Notas de prueba", "theme": "LegalTech", "provider": "google"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["action"] == "generate"
    assert data["title"] == "Análisis LegalTech"
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
            "provider": "openai",
            "api_key": secret,
        },
    )

    assert response.status_code == 503
    assert secret not in response.text
    assert "api_key" not in response.text


def test_ai_action_returns_validation_error_for_unsafe_source_url(monkeypatch):
    async def reject_url(_url):
        raise ValueError("URL rechazada por seguridad")

    monkeypatch.setattr(studio_ai, "extract_article_from_url", reject_url)
    response = client.post(
        "/api/ai-action",
        json={"action": "reversion", "source_url": "http://127.0.0.1/internal"},
    )

    assert response.status_code == 422
    assert "URL rechazada por seguridad" in response.json()["error"]
