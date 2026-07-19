from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_lesson_catalog():
    assert client.get("/api/health").json()["status"] == "ok"
    lessons = client.get("/api/classes").json()
    assert len(lessons) == 3

def test_sse_stream_has_ordered_live_messages():
    with client.stream("GET", "/api/stream/fractions-live?speed=10000") as response:
        text = "".join(response.iter_text())
    assert response.status_code == 200
    assert "event: event" in text
    assert "event: ccs" in text
    assert "event: nudge" in text

def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "ClassPulse" in response.text
