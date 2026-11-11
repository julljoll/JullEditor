from fastapi.testclient import TestClient

from backend import studio_ai
from backend.app import app

client = TestClient(app)


def test_ai_status_endpoint_forwards_endpoint(monkeypatch):
    async def fake_status(endpoint):
        return {"connected": True, "models": ["phi3"], "message": endpoint}

    monkeypatch.setattr(studio_ai, "_check_local_phi_status", fake_status)

    response = client.get("/api/ai-status", params={"endpoint": "http://ollama.local:11434"})

    assert response.status_code == 200
    assert response.json() == {
        "connected": True,
        "models": ["phi3"],
        "message": "http://ollama.local:11434",
    }


def test_ai_chat_requires_messages_or_instruction():
    response = client.post("/api/ai-chat", json={})

    assert response.status_code == 400
    assert response.json()["error"] == "No se enviaron mensajes para la conversación."


def test_ai_chat_preserves_response_contract(monkeypatch):
    async def fake_chat(messages, system_instruction, provider, api_key, local_endpoint, phi_model):
        assert messages[-1] == {"role": "user", "content": "Corrige el texto"}
        assert "ARTÍCULO ACTUAL EN EL EDITOR DEL USUARIO" in system_instruction
        assert provider == "phi"
        return {
            "reply": "```markdown\n---\ntitle: Prueba\n---\n<div class=\"editorial-container\">Texto</div>\n```",
            "providerUsed": "phi",
            "modelName": "phi3",
        }

    monkeypatch.setattr(studio_ai, "_chat_with_model", fake_chat)
    response = client.post(
        "/api/ai-chat",
        json={
            "messages": [{"role": "user", "content": "Corrige el texto"}],
            "current_article": "Borrador",
            "provider": "phi",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["providerUsed"] == "phi"
    assert data["modelName"] == "phi3"
    assert data["updatedArticle"] == "---\ntitle: Prueba\n---\n<div class=\"editorial-container\">Texto</div>"


def test_ai_action_preserves_generated_article_metadata(monkeypatch):
    async def fake_generate(prompt, system_instruction, api_key, temperature, max_tokens):
        assert "Tema: LegalTech" in prompt
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
            "providerUsed": "gemini",
            "modelName": "gemini-3.5-flash-lite",
        }

    monkeypatch.setattr(studio_ai, "_generate_with_gemini", fake_generate)
    response = client.post(
        "/api/ai-action",
        json={"source_text": "Notas de prueba", "theme": "LegalTech", "provider": "gemini"},
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
