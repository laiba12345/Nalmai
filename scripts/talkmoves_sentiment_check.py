"""TalkMoves discourse-label to sentiment proxy agreement check.

This is deliberately not an accuracy test. TalkMoves labels describe discourse
moves, not confusion or affect. The mapping below is a transparent proxy:
asking for information -> confused, making a claim -> neutral, and providing
evidence -> positive. Labels 0 and 1 are excluded because they have no
defensible sentiment direction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import load_env_file
from app.llm import DemoStructuredProvider, OpenAIStructuredProvider, StructuredProvider
from app.real_data import STUDENT_LABELS, TalkMoveSplit, _normalise_label

PROXY_MAPPING = {"2": "confused", "3": "neutral", "4": "positive"}
DEFAULT_REPORT = ROOT / "validation" / "TALKMOVES_SENTIMENT_PROXY.md"


def sample_proxy_rows(per_label: int = 10) -> list[dict]:
    split = TalkMoveSplit.read("student")
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in split.rows:
        label = _normalise_label(row["labels"])
        if label in PROXY_MAPPING and row["text_b"].strip():
            grouped[label].append(row)
    samples = []
    for label in PROXY_MAPPING:
        candidates = grouped[label]
        if len(candidates) < per_label:
            raise ValueError(f"Only {len(candidates)} usable TalkMoves rows for label {label}")
        indexes = [int(index * len(candidates) / per_label) for index in range(per_label)]
        for index in indexes:
            row = candidates[index]
            samples.append({
                "talkmove_label": label, "talkmove_name": STUDENT_LABELS[label],
                "proxy_expected": PROXY_MAPPING[label], "context": row["text_a"],
                "utterance": row["text_b"],
            })
    return samples


def evaluate_provider(provider: StructuredProvider, rows: list[dict]) -> dict:
    comparisons = []
    for row in rows:
        prediction = provider.classify_sentiment(row["utterance"])
        comparisons.append({
            **row, "predicted": prediction.sentiment,
            "confusion_probability": prediction.confusion_probability,
            "agrees": prediction.sentiment == row["proxy_expected"],
        })
    by_label = {}
    for label in PROXY_MAPPING:
        subset = [item for item in comparisons if item["talkmove_label"] == label]
        by_label[label] = {
            "talkmove_name": STUDENT_LABELS[label], "proxy_expected": PROXY_MAPPING[label],
            "samples": len(subset), "agreements": sum(item["agrees"] for item in subset),
            "agreement_rate": round(sum(item["agrees"] for item in subset) / len(subset), 3),
            "predictions": dict(Counter(item["predicted"] for item in subset)),
        }
    agreements = sum(item["agrees"] for item in comparisons)
    return {
        "provider": provider.mode, "samples": len(comparisons), "agreements": agreements,
        "agreement_rate": round(agreements / len(comparisons), 3), "by_label": by_label,
        "comparisons": comparisons,
    }


def write_report(rows: list[dict], results: list[dict], output: Path = DEFAULT_REPORT) -> Path:
    lines = [
        "# TalkMoves sentiment proxy agreement", "",
        "> **Proxy only—not confusion ground truth and not classifier accuracy.** TalkMoves annotates discourse moves, not learning-state sentiment. The mapping is a documented judgment used to check directional consistency.", "",
        "## Proxy mapping", "", "| TalkMoves student label | Expected direction | Rationale |", "|---|---|---|",
        "| Asking for more information (2) | confused | A clarification request can weakly proxy uncertainty. |",
        "| Making a claim (3) | neutral | A claim alone does not establish understanding or confusion. |",
        "| Providing evidence (4) | positive | An explanation can weakly proxy confident understanding. |", "",
        "Labels 0 (no talk move) and 1 (relating to another student) are excluded because neither has a defensible sentiment direction.", "",
        "## Results", "", "| Provider | Samples | Agreements | Agreement rate |", "|---|---:|---:|---:|",
    ]
    for result in results:
        lines.append(f"| {result['provider']} | {result['samples']} | {result['agreements']} | {result['agreement_rate']:.3f} |")
    for result in results:
        lines += ["", f"### {result['provider']}", "", "| TalkMoves label | Proxy | Agreement | Predictions |", "|---|---|---:|---|"]
        for detail in result["by_label"].values():
            lines.append(f"| {detail['talkmove_name']} | {detail['proxy_expected']} | {detail['agreement_rate']:.3f} | `{json.dumps(detail['predictions'], sort_keys=True)}` |")
    lines += [
        "", "## Interpretation limits", "",
        "Agreement means the classifier output matched this proxy mapping. It does not mean the student was truly confused, neutral, or understanding; it does not measure classroom efficacy, calibration, subgroup fairness, or causal validity.", "",
        "## Machine-readable detail", "", "```json", json.dumps(results, indent=2), "```", "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def providers_for(mode: str) -> list[StructuredProvider]:
    load_env_file()
    providers: list[StructuredProvider] = [DemoStructuredProvider()]
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    if mode == "openai":
        return [OpenAIStructuredProvider()]
    if mode == "all" or (mode == "auto" and has_key):
        providers.append(OpenAIStructuredProvider())
    return providers


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure TalkMoves proxy sentiment agreement (not accuracy).")
    parser.add_argument("--sample-per-label", type=int, default=10)
    parser.add_argument("--provider", choices=("auto", "demo", "openai", "all"), default="auto")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    rows = sample_proxy_rows(args.sample_per_label)
    results = [evaluate_provider(provider, rows) for provider in providers_for(args.provider)]
    path = write_report(rows, results, args.output)
    print("PROXY AGREEMENT ONLY — not confusion accuracy or ground truth")
    print("Mapping: 2->confused, 3->neutral, 4->positive; labels 0/1 excluded")
    for result in results:
        print(f"{result['provider']}: {result['agreements']}/{result['samples']} agreement ({result['agreement_rate']:.3f})")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
