from pathlib import Path


def test_every_public_page_displays_only_the_nalmai_brand():
    root = Path(__file__).parents[1] / "public"
    pages = [root / "index.html", root / "call.html"]

    for page in pages:
        content = page.read_text(encoding="utf-8")
        assert '<span class="brand-mark">N</span><span>Nalmai</span>' in content
        assert "Aha" not in content
        assert "ClassPulse" not in content
        assert "ClassroomOS" not in content
        assert "SCHOOL PULSE" not in content

    dashboard = pages[0].read_text(encoding="utf-8")
    assert "NALMAI SESSIONS" in dashboard
    assert "individual language evidence" in dashboard
    assert "CCS soft evidence" not in dashboard


def test_live_call_has_identity_media_and_saved_performance_controls():
    root = Path(__file__).parents[1]
    html = (root / "public/call.html").read_text(encoding="utf-8")
    call_js = (root / "public/call.js").read_text(encoding="utf-8")
    meeting_js = (root / "public/meeting.js").read_text(encoding="utf-8")
    identity_css = (root / "public/identity.css").read_text(encoding="utf-8")
    for control in ("participantName", "participantId", "toggleMic", "toggleCamera", "performanceCard"):
        assert f'id="{control}"' in html
    assert "track.enabled=!track.enabled" in call_js
    assert "participant_profile" in call_js
    assert "known_role=${role}" in meeting_js
    assert "known_speaker_id=${speaker}" in meeting_js
    assert "state.analysisTracks.map(captureTrackWindow)" in meeting_js
    assert "TRANSCRIPTION_WINDOW_SECONDS=10" in meeting_js
    assert "TRANSCRIPTION_WINDOW_SECONDS*1000" in meeting_js
    assert "/api/performance/teacher/" in meeting_js
    assert ".meeting-page{overflow-y:auto" in identity_css
    assert ".meeting-shell{height:auto" in identity_css


def test_dashboard_transcript_and_live_call_controls_have_stable_layout():
    root = Path(__file__).parents[1]
    css = (root / "public/live.css").read_text(encoding="utf-8")
    html = (root / "public/index.html").read_text(encoding="utf-8")
    assert ".live-grid { align-items:start; }" in css
    assert ".transcript-panel { align-self:start" in css
    assert ".call-link { display:inline-flex" in css
    assert "min-width:86px" in css
    assert 'class="call-link"' in html

def test_dashboard_has_all_live_product_surfaces():
    root = Path(__file__).parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    js = (root / "public/app.js").read_text(encoding="utf-8")
    for required in ("transcriptFeed", "ccsGauge", "nudgePanel", "masteryTable", "realDataPanel", "liveInputToggle", "liveStudentId", "liveText", "activeSessions"):
        assert f'id="{required}"' in html
    assert "EventSource" in js
    assert "RECORDED CLASSBANK" in js
    assert "/api/stream/" in js
    assert "/api/evidence/real-data" in js
    assert "session_delta" in js
    assert "/api/live-input/" in js
    assert "/api/sessions" in js
    assert "/stream/" in js
