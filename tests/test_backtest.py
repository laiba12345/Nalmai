from pathlib import Path

from scripts.backtest_ccs import backtest_all, backtest_fixture, write_report


def test_each_fixture_reports_authored_window_precision_recall_and_poll_prediction():
    results = backtest_all()
    assert len(results) == 3
    for result in results:
        assert result["fixture"]
        assert 0 <= result["window_precision"] <= 1
        assert 0 <= result["window_recall"] <= 1
        assert 0 <= result["early_warning_precision"] <= 1
        assert 0 <= result["early_warning_recall"] <= 1
        assert result["confusion_points"] > 0
        assert result["polls"] >= 1
        assert isinstance(result["timeline"], list)


def test_backtest_uses_pre_poll_score_without_poll_result_leakage():
    result = backtest_fixture("fractions_live")
    first_poll = result["poll_predictions"][0]
    assert first_poll["score_source"] == "previous_event"
    assert first_poll["poll_miss_rate"] == .75
    assert "pre_poll_early_score" in first_poll
    assert "predicted_miss_early" in first_poll


def test_backtest_writes_markdown_summary():
    output = Path("validation/test-summary.md")
    try:
        write_report(backtest_all(), output)
        text = output.read_text(encoding="utf-8")
        assert "CCS Backtest" in text
        assert "Precision" in text
        assert "Early-warning" in text
        assert "not real-world confusion accuracy" in text
    finally:
        output.unlink(missing_ok=True)
