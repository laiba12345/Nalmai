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
