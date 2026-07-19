from pathlib import Path

def test_dashboard_has_all_live_product_surfaces():
    root = Path(__file__).parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    js = (root / "public/app.js").read_text(encoding="utf-8")
    for required in ("transcriptFeed", "ccsGauge", "nudgePanel", "masteryTable", "realDataPanel", "liveInputToggle", "liveStudentId", "liveText", "activeSessions"):
        assert f'id="{required}"' in html
    assert "EventSource" in js
    assert "/api/stream/" in js
    assert "/api/evidence/real-data" in js
    assert "session_delta" in js
    assert "/api/live-input/" in js
    assert "/api/sessions" in js
    assert "/stream/" in js
