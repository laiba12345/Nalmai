from pathlib import Path

def test_dashboard_has_all_live_product_surfaces():
    root = Path(__file__).parents[1]
    html = (root / "public/index.html").read_text(encoding="utf-8")
    js = (root / "public/app.js").read_text(encoding="utf-8")
    for required in ("transcriptFeed", "ccsGauge", "nudgePanel", "masteryTable"):
        assert f'id="{required}"' in html
    assert "EventSource" in js
    assert "/api/stream/" in js
