"""Validate educator ratings and generate an honest aggregate report."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DIMENSIONS = ("usefulness", "specificity", "factual_correctness", "classroom_feasibility", "labeling_safety")


def validate_rating(value: dict) -> dict:
    required = {"blind_id", "rater_id", *DIMENSIONS, "decision", "comment"}
    if missing := required - value.keys():
        raise ValueError(f"missing rating fields: {sorted(missing)}")
    for dimension in DIMENSIONS:
        if type(value[dimension]) is not int or not 1 <= value[dimension] <= 5:
            raise ValueError(f"{dimension} must be an integer from 1 to 5")
    if value["decision"] not in {"use", "reject"}:
        raise ValueError("decision must be use or reject")
    if not str(value["rater_id"]).strip() or not str(value["blind_id"]).strip():
        raise ValueError("blind_id and rater_id are required")
    return value


def summarize_ratings(values: list[dict]) -> dict:
    ratings = [validate_rating(dict(value)) for value in values]
    by_item = defaultdict(list)
    for rating in ratings:
        by_item[rating["blind_id"]].append(rating)
    overlaps = [group for group in by_item.values() if len({item["rater_id"] for item in group}) >= 2]
    pair_agreements = []
    for group in overlaps:
        decisions = [item["decision"] for item in group]
        pairs = [(decisions[i], decisions[j]) for i in range(len(decisions)) for j in range(i + 1, len(decisions))]
        pair_agreements.extend(a == b for a, b in pairs)
    return {
        "result_status": "authentic_results" if ratings else "not_yet_collected",
        "sample_size": len(ratings), "rated_items": len(by_item),
        "raters": len({item["rater_id"] for item in ratings}),
        "dimension_distributions": {dimension: dict(sorted(Counter(item[dimension] for item in ratings).items())) for dimension in DIMENSIONS},
        "use_rate": round(sum(item["decision"] == "use" for item in ratings) / len(ratings), 3) if ratings else None,
        "overlapping_items": len(overlaps),
        "decision_agreement": round(sum(pair_agreements) / len(pair_agreements), 3) if pair_agreements else None,
        "agreement_note": "Raw pairwise decision agreement; interpret cautiously with small samples." if pair_agreements else "Requires at least two educators rating an overlapping item.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ratings", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = summarize_ratings(json.loads(args.ratings.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
