"""Export a privacy-safe, randomized, provider-blinded nudge rating packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

RUBRIC = {
    "scale": "1 (poor/unsafe) to 5 (excellent/safe)",
    "dimensions": ["usefulness", "specificity", "factual_correctness", "classroom_feasibility", "labeling_safety"],
    "decision": ["use", "reject"],
}
ALLOWED_PROVENANCE = {"authored", "synthetic_test", "authorized_deidentified"}
PRIVATE_FIELDS = {"student_name", "student_id", "speaker_id", "email", "provider"}


def export_packet(items: list[dict], seed: int) -> dict:
    rng = random.Random(seed)
    exported = []
    for item in items:
        if item.get("provenance") not in ALLOWED_PROVENANCE:
            raise ValueError("items must be authored, synthetic_test, or authorized_deidentified")
        forbidden = PRIVATE_FIELDS.intersection(item) - {"provider"}
        if forbidden:
            raise ValueError(f"private fields are not exportable: {sorted(forbidden)}")
        required = {"item_id", "concept", "transcript_window", "evidence", "nudge", "provenance"}
        if missing := required - item.keys():
            raise ValueError(f"missing item fields: {sorted(missing)}")
        blind_id = hashlib.sha256(f"{seed}:{item['item_id']}".encode()).hexdigest()[:12]
        exported.append({key: item[key] for key in ("concept", "transcript_window", "evidence", "nudge", "provenance")} | {"blind_id": blind_id})
    rng.shuffle(exported)
    return {"schema_version": 1, "study_status": "synthetic_smoke_test" if any(item["provenance"] == "synthetic_test" for item in exported) else "awaiting_authentic_educator_ratings", "rubric": RUBRIC, "items": exported}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seed", type=int, default=20260719)
    args = parser.parse_args()
    packet = export_packet(json.loads(args.input.read_text(encoding="utf-8")), args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print(f"Exported {len(packet['items'])} blinded items to {args.output}")
    print("Open validation/educator_rating_form.html locally and load this packet.")


if __name__ == "__main__":
    main()
