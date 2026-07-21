from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_lesson_catalog():
    health = client.get("/api/health").json()
    assert health["status"] == "ok"
    assert health["service"] == "AhaLoop"
    lessons = client.get("/api/classes").json()
    assert len(lessons) >= 3
    assert {"forces-live", "fractions-live", "photosynthesis-live", "ahaloop-extended"}.issubset({lesson["id"] for lesson in lessons})

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
    assert "AhaLoop" in response.text
    assert "ClassPulse" not in response.text
    assert 'id="presentDemo"' in response.text
    assert 'id="demoGuide"' in response.text
    assert "GPT-5.6 analyzes language" in response.text
    assert 'id="createCall"' in response.text
    assert 'id="joinCall"' in response.text
    assert 'id="remoteVideo"' in response.text

def test_real_dataset_evidence_endpoint():
    response = client.get("/api/evidence/real-data")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset"] == "TalkMoves"
    assert payload["total_rows"] > 2000

def test_live_input_enters_same_sse_stream_with_visible_tag():
    submitted = client.post("/api/live-input/forces-live", json={"student_id": "Live Guest", "text": "I am confused about the force", "timestamp": "2026-07-19T10:00:00Z"})
    assert submitted.status_code == 202
    with client.stream("GET", "/api/stream/forces-live?speed=10000") as response:
        text = "".join(response.iter_text())
    assert '"live": true' in text
    assert "Live Guest" in text

def test_create_list_and_stream_two_isolated_sessions():
    first = client.post("/api/sessions", json={"fixture_id": "fractions-live"}).json()
    second = client.post("/api/sessions", json={"fixture_id": "forces-live"}).json()
    assert first["session_id"] != second["session_id"]
    sessions = client.get("/api/sessions").json()
    assert {first["session_id"], second["session_id"]}.issubset({row["session_id"] for row in sessions})
    with client.stream("GET", f"/stream/{first['session_id']}?speed=10000") as response:
        first_stream = "".join(response.iter_text())
    with client.stream("GET", f"/stream/{second['session_id']}?speed=10000") as response:
        second_stream = "".join(response.iter_text())
    assert '"concept": "fractions"' in first_stream
    assert '"concept": "forces"' in second_stream
    assert second["session_id"] not in first_stream


def test_session_scoped_live_input():
    created = client.post("/api/sessions", json={"fixture_id": "photosynthesis-live"}).json()
    response = client.post(f"/api/sessions/{created['session_id']}/live-input", json={"student_id": "Live Bio", "text": "I do not understand", "timestamp": "2026-07-19T11:00:00Z"})
    assert response.status_code == 202
    with client.stream("GET", f"/stream/{created['session_id']}?speed=10000") as stream:
        assert "Live Bio" in "".join(stream.iter_text())
