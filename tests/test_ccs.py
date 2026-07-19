from app.ccs import CCSEngine, SignalWindow

def test_confused_window_scores_above_threshold():
    window = SignalWindow(sentiments=[("confused", .9)] * 3, keyword_flags=3, response_latencies=[28, 31, 35], poll_correct=[False, False, True, False])
    result = CCSEngine().score(window)
    assert result.score > .6
    assert result.poll_miss_rate == .75
    assert result.evidence["confused_lines"] == 3

def test_calm_window_scores_low():
    window = SignalWindow(sentiments=[("positive", .9), ("neutral", .8)], keyword_flags=0, response_latencies=[6, 9], poll_correct=[True, True, True])
    assert CCSEngine().score(window).score < .3

def test_ccs_is_always_bounded():
    engine = CCSEngine()
    extreme = SignalWindow(sentiments=[("confused", 1)] * 100, keyword_flags=100, response_latencies=[999] * 100, poll_correct=[False] * 100)
    assert 0 <= engine.score(extreme).score <= 1

def test_early_warning_can_fire_before_confirmed_confusion():
    window = SignalWindow(
        sentiments=[("confused", .9)], keyword_flags=1, response_latencies=[18],
        poll_correct=[], student_ids=["s1"], active_students=4,
    )
    result = CCSEngine().score(window)
    assert result.early_score >= result.warning_threshold
    assert result.score < result.confirmed_threshold
    assert result.state == "warning"

def test_student_breadth_strengthens_early_warning():
    narrow = SignalWindow(sentiments=[("confused", .9)] * 2, keyword_flags=2, student_ids=["s1", "s1"], active_students=4)
    broad = SignalWindow(sentiments=[("confused", .9)] * 2, keyword_flags=2, student_ids=["s1", "s2"], active_students=4)
    assert CCSEngine().score(broad).early_score > CCSEngine().score(narrow).early_score

def test_timed_evidence_decays_after_recovery():
    engine = CCSEngine(half_life_seconds=10)
    recent = SignalWindow(sentiment_events=[("confused", .9, 0, "s1")], keyword_events=[(1, 0)], current_at=0, active_students=4)
    stale = SignalWindow(sentiment_events=[("confused", .9, 0, "s1")], keyword_events=[(1, 0)], current_at=40, active_students=4)
    assert engine.score(stale).early_score < engine.score(recent).early_score
