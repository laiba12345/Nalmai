import json

import pytest

from scripts.educator_nudge_evaluation import export_packet
from scripts.report_educator_ratings import summarize_ratings, validate_rating


ITEMS = [
    {"item_id": "a", "concept": "fractions", "transcript_window": ["Teacher: Compare equal-sized bars."], "evidence": {"confused_lines": 2}, "nudge": "Draw fraction bars.", "provider": "gpt-5.6", "provenance": "synthetic_test"},
    {"item_id": "b", "concept": "forces", "transcript_window": ["Teacher: What changes motion?"], "evidence": {"poll_misses": 3}, "nudge": "Use force arrows.", "provider": "baseline", "provenance": "authored"},
]


def test_export_is_reproducible_randomized_and_provider_blind():
    first = export_packet(ITEMS, seed=17)
    second = export_packet(ITEMS, seed=17)
    assert first == second
    assert [item["blind_id"] for item in first["items"]] != ["a", "b"]
    assert "provider" not in json.dumps(first).lower()


def test_export_rejects_private_or_unapproved_material():
    unsafe = [{**ITEMS[0], "student_name": "Real Student"}]
    with pytest.raises(ValueError):
        export_packet(unsafe, seed=1)
    with pytest.raises(ValueError):
        export_packet([{**ITEMS[0], "provenance": "protected_classbank"}], seed=1)


def test_rating_schema_rejects_missing_or_out_of_range_values():
    valid = {"blind_id": "x", "rater_id": "educator-1", "usefulness": 4, "specificity": 5, "factual_correctness": 5, "classroom_feasibility": 4, "labeling_safety": 5, "decision": "use", "comment": ""}
    assert validate_rating(valid)["decision"] == "use"
    with pytest.raises(ValueError):
        validate_rating({**valid, "specificity": 6})
    missing = dict(valid); missing.pop("decision")
    with pytest.raises(ValueError):
        validate_rating(missing)


def test_report_aggregates_dimensions_use_rate_and_overlap_agreement():
    base = {"blind_id": "x", "usefulness": 4, "specificity": 5, "factual_correctness": 5, "classroom_feasibility": 4, "labeling_safety": 5, "decision": "use", "comment": ""}
    report = summarize_ratings([{**base, "rater_id": "r1"}, {**base, "rater_id": "r2"}])
    assert report["sample_size"] == 2
    assert report["raters"] == 2
    assert report["use_rate"] == 1
    assert report["overlapping_items"] == 1
    assert report["decision_agreement"] == 1
