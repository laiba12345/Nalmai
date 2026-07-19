"""Export and evaluate educator annotations for held-out confusion windows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from app.ccs import CCSEngine

LABELS = {"calm", "possible_confusion", "confirmed_confusion", "insufficient_context"}
POSITIVE_LABELS = {"possible_confusion", "confirmed_confusion"}
POSITIVE_PREDICTIONS = {"warning", "confirmed"}
ALLOWED_PROVENANCE = {"authorized_deidentified", "authored_heldout"}


def configuration_hash() -> str:
    engine = CCSEngine()
    frozen = {"bias": engine.bias, "weights": engine.weights, "early_bias": engine.early_bias, "breadth_weight": engine.breadth_weight, "warning_threshold": engine.warning_threshold, "confirmed_threshold": engine.confirmed_threshold, "half_life_seconds": engine.half_life_seconds}
    return hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()[:16]


def export_annotation_packet(windows: list[dict]) -> dict:
    required = {"window_id", "source_path", "provenance", "transcript", "predicted_state", "pre_poll_predicted_state", "contains_future_poll"}
    cleaned = []
    for window in windows:
        if missing := required - window.keys():
            raise ValueError(f"missing window fields: {sorted(missing)}")
        normalized = str(window["source_path"]).replace("\\", "/").lower()
        if "/classes/" in normalized or "/validation_classes/" in normalized:
            raise ValueError("calibration/demo fixtures cannot enter held-out evaluation")
        if window["contains_future_poll"]:
            raise ValueError("transcript window leaks a future poll outcome")
        if window["provenance"] not in ALLOWED_PROVENANCE:
            raise ValueError("held-out labels require authorized/de-identified or authored-heldout provenance; TalkMoves is not confusion ground truth")
        if window["predicted_state"] not in {"calm", "warning", "confirmed"} or window["pre_poll_predicted_state"] not in {"calm", "warning", "confirmed"}:
            raise ValueError("invalid production prediction state")
        cleaned.append(dict(window))
    return {"schema_version": 1, "held_out": True, "configuration_hash": configuration_hash(), "thresholds_frozen_before_annotation": True, "items": cleaned}


def validate_annotation(value: dict) -> dict:
    required = {"window_id", "rater_id", "label", "evidence_source", "concept_note"}
    if missing := required - value.keys():
        raise ValueError(f"missing annotation fields: {sorted(missing)}")
    if value["label"] not in LABELS:
        raise ValueError(f"label must be one of {sorted(LABELS)}")
    if not str(value["window_id"]).strip() or not str(value["rater_id"]).strip() or not str(value["evidence_source"]).strip():
        raise ValueError("window_id, rater_id, and evidence_source are required")
    return value


def _metrics(pairs: list[tuple[str, str]]) -> dict:
    matrix = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    false_alerts = []
    for window_id, predicted, actual in pairs:
        positive_prediction, positive_actual = predicted in POSITIVE_PREDICTIONS, actual in POSITIVE_LABELS
        cell = "tp" if positive_prediction and positive_actual else "fp" if positive_prediction else "fn" if positive_actual else "tn"
        matrix[cell] += 1
        if cell == "fp": false_alerts.append(window_id)
    precision = matrix["tp"] / (matrix["tp"] + matrix["fp"]) if matrix["tp"] + matrix["fp"] else 0
    recall = matrix["tp"] / (matrix["tp"] + matrix["fn"]) if matrix["tp"] + matrix["fn"] else 0
    return {"confusion_matrix": matrix, "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(2 * precision * recall / (precision + recall), 3) if precision + recall else 0, "false_alert_windows": false_alerts}


def evaluate_annotations(packet: dict, annotations: list[dict], expected_configuration_hash: str) -> dict:
    if not packet.get("held_out") or packet.get("configuration_hash") != expected_configuration_hash or expected_configuration_hash != configuration_hash():
        raise ValueError("held-out status or frozen configuration hash mismatch")
    items = {item["window_id"]: item for item in packet["items"]}
    ratings = [validate_annotation(dict(value)) for value in annotations]
    if any(value["window_id"] not in items for value in ratings):
        raise ValueError("annotation references an unknown held-out window")
    included = [value for value in ratings if value["label"] != "insufficient_context"]
    pairs = [(value["window_id"], items[value["window_id"]]["predicted_state"], value["label"]) for value in included]
    pre_poll_pairs = [(value["window_id"], items[value["window_id"]]["pre_poll_predicted_state"], value["label"]) for value in included]
    by_window = defaultdict(list)
    for value in ratings: by_window[value["window_id"]].append(value["label"])
    overlaps = {key: labels for key, labels in by_window.items() if len(labels) > 1}
    disagreements = [{"window_id": key, "labels": labels} for key, labels in overlaps.items() if len(set(labels)) > 1]
    result = _metrics(pairs)
    return {"dataset_provenance": sorted({item["provenance"] for item in items.values()}), "held_out": True, "configuration_hash": packet["configuration_hash"], "result_status": "authentic_educator_annotations" if any(item["provenance"] == "authorized_deidentified" for item in items.values()) else "authored_workflow_smoke_test", "rater_count": len({value["rater_id"] for value in ratings}), "annotations": len(ratings), "insufficient_context": len(ratings) - len(included), **result, "pre_poll": _metrics(pre_poll_pairs), "overlapping_windows": len(overlaps), "exact_label_agreement": round(sum(len(set(labels)) == 1 for labels in overlaps.values()) / len(overlaps), 3) if overlaps else None, "disagreements": disagreements, "limitations": "Window-level educator labels assess detection, not student learning or intervention efficacy."}


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export"); export.add_argument("windows", type=Path); export.add_argument("packet", type=Path)
    evaluate = sub.add_parser("evaluate"); evaluate.add_argument("packet", type=Path); evaluate.add_argument("annotations", type=Path); evaluate.add_argument("report", type=Path)
    args = parser.parse_args()
    if args.command == "export":
        result, output = export_annotation_packet(json.loads(args.windows.read_text(encoding="utf-8"))), args.packet
    else:
        packet = json.loads(args.packet.read_text(encoding="utf-8")); result = evaluate_annotations(packet, json.loads(args.annotations.read_text(encoding="utf-8")), packet["configuration_hash"]); output = args.report
    output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(result, indent=2), encoding="utf-8"); print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
