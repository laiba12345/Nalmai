import pytest

from scripts.heldout_confusion import configuration_hash, evaluate_annotations, export_annotation_packet, validate_annotation


WINDOWS = [{"window_id": "h1", "source_path": "data/heldout/lesson-1.json", "provenance": "authorized_deidentified", "transcript": ["Student: I am not sure."], "predicted_state": "confirmed", "pre_poll_predicted_state": "warning", "contains_future_poll": False}]


def test_annotation_export_freezes_configuration_and_separates_heldout():
    packet = export_annotation_packet(WINDOWS)
    assert packet["held_out"] is True
    assert packet["configuration_hash"] == configuration_hash()
    assert packet["items"][0]["transcript"]


@pytest.mark.parametrize("change", [
    {"source_path": "data/classes/fractions_live.json"},
    {"source_path": "data/validation_classes/test.json"},
    {"contains_future_poll": True},
    {"provenance": "talkmoves_proxy"},
])
def test_export_refuses_calibration_poll_leakage_and_proxy_labels(change):
    with pytest.raises(ValueError):
        export_annotation_packet([{**WINDOWS[0], **change}])


def test_annotation_schema_and_hash_mismatch_are_rejected():
    valid = {"window_id": "h1", "rater_id": "r1", "label": "confirmed_confusion", "evidence_source": "student_language", "concept_note": ""}
    assert validate_annotation(valid)["label"] == "confirmed_confusion"
    with pytest.raises(ValueError):
        validate_annotation({**valid, "label": "confused"})
    packet = export_annotation_packet(WINDOWS)
    with pytest.raises(ValueError):
        evaluate_annotations(packet, [valid], expected_configuration_hash="wrong")


def test_evaluation_reports_metrics_exclusions_false_alerts_and_agreement():
    packet = export_annotation_packet(WINDOWS)
    ratings = [
        {"window_id": "h1", "rater_id": "r1", "label": "confirmed_confusion", "evidence_source": "student_language", "concept_note": ""},
        {"window_id": "h1", "rater_id": "r2", "label": "insufficient_context", "evidence_source": "insufficient", "concept_note": ""},
    ]
    report = evaluate_annotations(packet, ratings, packet["configuration_hash"])
    assert report["confusion_matrix"]["tp"] == 1
    assert report["insufficient_context"] == 1
    assert report["rater_count"] == 2
    assert report["overlapping_windows"] == 1
    assert report["disagreements"]
    assert "pre_poll" in report
