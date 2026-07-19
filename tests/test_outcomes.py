from app.outcomes import OutcomeTracker


def test_applied_nudge_links_baseline_and_next_poll_outcome():
    tracker = OutcomeTracker()
    record = tracker.register("fractions", trigger_at=10, baseline_correctness=.25)
    tracker.decide(record.nudge_id, "applied", decided_at=12)
    tracker.observe_poll("fractions", at=20, correctness=.75)
    result = tracker.get(record.nudge_id)
    assert result.decision == "applied"
    assert result.next_poll_correctness == .75
    assert result.correctness_delta == .5


def test_dismissed_nudge_is_recorded_but_not_attributed_as_applied():
    tracker = OutcomeTracker()
    record = tracker.register("forces", trigger_at=5, baseline_correctness=.5)
    tracker.decide(record.nudge_id, "dismissed", decided_at=6)
    tracker.observe_poll("forces", at=12, correctness=.75)
    result = tracker.get(record.nudge_id)
    assert result.decision == "dismissed"
    assert result.next_poll_correctness == .75
    assert result.applied is False
