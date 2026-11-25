from fastapi.testclient import TestClient

from app.main import app
from app.services.ai_engine import get_ai_engine

client = TestClient(app)

PAYLOAD = {
    "requirement": "Validate JWT tokens and reject expired tokens on login",
    "code_diff": "+ def validate_jwt(token):\n+     payload = jwt.decode(token)\n+     if payload['exp'] < now(): raise AuthError('expired')",
    "commit_activity": [{"author": "a", "lines_changed": 10}, {"author": "b", "lines_changed": 3}],
    "activity_timestamps": ["2026-11-20T23:30:00Z", "2026-11-21T10:00:00Z"],
    "bug_frequency": 1,
}


def test_health():
    for path in ("/health", "/api/v1/health"):
        r = client.get(path)
        assert r.status_code == 200
        assert r.json()["status"] == "online"


def test_analyze_returns_full_report():
    r = client.post("/api/v1/analyze", json=PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict) and body


def test_model_is_loaded_once_not_per_request():
    import sentence_transformers

    client.post("/api/v1/analyze", json=PAYLOAD)
    before = sentence_transformers.SentenceTransformer.loads
    for _ in range(3):
        client.post("/api/v1/analyze", json=PAYLOAD)
    assert sentence_transformers.SentenceTransformer.loads == before
    assert get_ai_engine.cache_info().currsize == 1


def test_old_ticket_description_field_still_accepted():
    data = dict(PAYLOAD)
    data["ticket_description"] = data.pop("requirement")
    assert client.post("/api/v1/analyze", json=data).status_code == 200


def test_missing_fields_rejected():
    assert client.post("/api/v1/analyze", json={"requirement": "x"}).status_code == 422
