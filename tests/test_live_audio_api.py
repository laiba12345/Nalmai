from fastapi.testclient import TestClient

import app.main as main_module
from app.transcription import DiarizedSegment

client = TestClient(main_module.app)


class FakeTranscriber:
    model = "fake-diarized"
    def transcribe(self, audio, filename):
        assert audio == b"audio-bytes"
        return [
            DiarizedSegment("speaker_0", "Let us compare fractions", 0, 1.5),
            DiarizedSegment("speaker_1", "I do not understand", 1.6, 2.8),
        ]


def test_audio_chunk_transcribes_diarizes_and_queues_events(monkeypatch):
    monkeypatch.setattr(main_module, "transcriber", FakeTranscriber())
    session = client.post("/api/sessions", json={"fixture_id": "fractions-live"}).json()
    response = client.post(
        f"/api/sessions/{session['session_id']}/audio-chunks?offset_seconds=30&teacher_speaker=speaker_0&filename=part.webm",
        content=b"audio-bytes", headers={"content-type": "audio/webm"},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["model"] == "fake-diarized"
    assert [event["type"] for event in body["events"]] == ["teacher", "chat"]
    assert body["events"][1]["source"] == "live_audio"
    assert body["events"][1]["at"] == 31.6


def test_nudge_decision_and_outcome_api():
    session = client.post("/api/sessions", json={"fixture_id": "forces-live"}).json()
    runtime = main_module.session_registry.get(session["session_id"]).runtime
    nudge = runtime.outcomes.register("forces", 5, .25)
    response = client.post(f"/api/sessions/{session['session_id']}/nudges/{nudge.nudge_id}/decision", json={"decision": "applied"})
    assert response.status_code == 200
    runtime.outcomes.observe_poll("forces", 10, .75)
    outcomes = client.get(f"/api/sessions/{session['session_id']}/outcomes").json()
    assert outcomes[0]["correctness_delta"] == .5


def test_live_session_mode_stays_open_until_stopped():
    session = client.post("/api/sessions", json={"fixture_id": "forces-live", "mode": "live"}).json()
    assert session["mode"] == "live"
    runtime = main_module.session_registry.get(session["session_id"]).runtime
    assert runtime.live_mode is True
    response = client.post(f"/api/sessions/{session['session_id']}/stop")
    assert response.status_code == 200
