from fastapi.testclient import TestClient
from app.main import app
from app.database import initialize_database


def test_health_and_upload_chat_history(tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.database_path", str(tmp_path / "test.db"))
    initialize_database()
    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
    upload = client.post("/api/documents", files={"file": ("faq.md", "Password resets use a secure email link.", "text/markdown")})
    assert upload.status_code == 201
    answer = client.post("/api/chat", json={"question": "How do I reset my password?"})
    assert answer.status_code == 200
    payload = answer.json()
    assert "faq.md" in payload["answer"]
    assert payload["sources"][0]["filename"] == "faq.md"
    history = client.get(f"/api/conversations/{payload['conversation_id']}")
    assert [m["role"] for m in history.json()["messages"]] == ["user", "assistant"]
