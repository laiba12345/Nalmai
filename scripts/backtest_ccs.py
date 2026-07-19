from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm import DemoStructuredProvider
from app.runtime import ClassRuntime
from app.stream import DATA_DIR, ScriptedClass

DEFAULT_REPORT = ROOT / "validation" / "CCS_BACKTEST.md"


async def _collect(name: str) -> dict:
    raw = json.loads((DATA_DIR / f"{name}.json").read_text(encoding="utf-8"))
    window = raw["ground_truth"]["confusion_window"]
    runtime = ClassRuntime(ScriptedClass.load(name), DemoStructuredProvider())
    timeline: list[dict] = []
    polls: list[dict] = []
    current_event: dict | None = None
    async for message in runtime.run(speed=100_000):
        if message["kind"] == "event":
            current_event = message["data"]
            if current_event["type"] == "poll":
                answers = list(current_event["responses"].values())
                polls.append({
                    "at": current_event["at"], "pre_poll_ccs": timeline[-1]["score"] if timeline else 0,
                    "predicted_miss": bool(timeline and timeline[-1]["score"] >= .6),
                    "pre_poll_early_score": timeline[-1]["early_score"] if timeline else 0,
                    "predicted_miss_early": bool(timeline and timeline[-1]["early_score"] >= .4),
                    "poll_miss_rate": round(sum(not answer for answer in answers) / len(answers), 3),
                    "actual_majority_miss": sum(not answer for answer in answers) / len(answers) > .5,
                    "score_source": "previous_event",
                })
        elif message["kind"] == "ccs" and current_event:
            at = current_event["at"]
            timeline.append({"at": at, "event_type": current_event["type"], "score": message["data"]["score"], "early_score": message["data"]["early_score"], "state": message["data"]["state"], "ground_truth_confused": window["start"] <= at <= window["end"]})
    return {"raw": raw, "timeline": timeline, "polls": polls}


def backtest_fixture(name: str) -> dict:
    collected = asyncio.run(_collect(name)); timeline = collected["timeline"]
    tp = sum(point["score"] >= .6 and point["ground_truth_confused"] for point in timeline)
    fp = sum(point["score"] >= .6 and not point["ground_truth_confused"] for point in timeline)
    fn = sum(point["score"] < .6 and point["ground_truth_confused"] for point in timeline)
    tn = sum(point["score"] < .6 and not point["ground_truth_confused"] for point in timeline)
    early_tp = sum(point["early_score"] >= .4 and point["ground_truth_confused"] for point in timeline)
    early_fp = sum(point["early_score"] >= .4 and not point["ground_truth_confused"] for point in timeline)
    early_fn = sum(point["early_score"] < .4 and point["ground_truth_confused"] for point in timeline)
    early_tn = sum(point["early_score"] < .4 and not point["ground_truth_confused"] for point in timeline)
    polls = collected["polls"]
    correct_predictions = sum(poll["predicted_miss"] == poll["actual_majority_miss"] for poll in polls)
    return {
        "fixture": collected["raw"]["id"], "title": collected["raw"]["title"],
        "confusion_window": collected["raw"]["ground_truth"]["confusion_window"],
        "window_precision": round(tp / (tp + fp), 3) if tp + fp else 0,
        "window_recall": round(tp / (tp + fn), 3) if tp + fn else 0,
        "early_warning_precision": round(early_tp / (early_tp + early_fp), 3) if early_tp + early_fp else 0,
        "early_warning_recall": round(early_tp / (early_tp + early_fn), 3) if early_tp + early_fn else 0,
        "confusion_points": tp + fn, "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "early_warning_matrix": {"tp": early_tp, "fp": early_fp, "tn": early_tn, "fn": early_fn},
        "polls": len(polls), "poll_prediction_accuracy": round(correct_predictions / len(polls), 3) if polls else 0,
        "poll_predictions": polls, "timeline": timeline,
    }


def backtest_all() -> list[dict]:
    return [backtest_fixture(path.stem) for path in sorted(DATA_DIR.glob("*.json"))]


def write_report(results: list[dict], output: Path = DEFAULT_REPORT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    total = {key: sum(item["confusion_matrix"][key] for item in results) for key in ("tp", "fp", "tn", "fn")}
    early_total = {key: sum(item["early_warning_matrix"][key] for item in results) for key in ("tp", "fp", "tn", "fn")}
    precision = total["tp"] / (total["tp"] + total["fp"]) if total["tp"] + total["fp"] else 0
    recall = total["tp"] / (total["tp"] + total["fn"]) if total["tp"] + total["fn"] else 0
    poll_total = sum(item["polls"] for item in results)
    poll_correct = sum(round(item["poll_prediction_accuracy"] * item["polls"]) for item in results)
    early_poll_correct = sum(sum(p["predicted_miss_early"] == p["actual_majority_miss"] for p in item["poll_predictions"]) for item in results)
    early_precision = early_total["tp"] / (early_total["tp"] + early_total["fp"]) if early_total["tp"] + early_total["fp"] else 0
    early_recall = early_total["tp"] / (early_total["tp"] + early_total["fn"]) if early_total["tp"] + early_total["fn"] else 0
    lines = [
        "# CCS Backtest", "", "Generated from the three authored ClassPulse fixtures using the production CCS path and deterministic demo sentiment provider.", "",
        "| Fixture | Confirmed Precision | Confirmed Recall | Early Precision | Early Recall |", "|---|---:|---:|---:|---:|",
    ]
    for item in results:
        lines.append(f"| {item['title']} | {item['window_precision']:.3f} | {item['window_recall']:.3f} | {item['early_warning_precision']:.3f} | {item['early_warning_recall']:.3f} |")
    lines += [
        "", "## Aggregate", "", f"- Confirmed-confusion precision: **{precision:.3f}**", f"- Confirmed-confusion recall: **{recall:.3f}**",
        f"- Early-warning precision: **{early_precision:.3f}**", f"- Early-warning recall: **{early_recall:.3f}**",
        f"- Confirmed pre-poll majority-miss prediction: **{poll_correct}/{poll_total}**", f"- Early-warning pre-poll prediction: **{early_poll_correct}/{poll_total}**",
        f"- Confirmed confusion matrix: `{total}`", f"- Early-warning confusion matrix: `{early_total}`", "",
        "## Interpretation", "", "This is fixture backtesting, not real-world confusion accuracy. Authored windows test whether the current threshold behaves as intended in known demo moments. Poll prediction uses only the CCS from the previous event, preventing poll-result leakage. The sample is three deliberately constructed lessons and is too small for calibration, fairness, or deployment claims.", "",
        "## Machine-readable detail", "", "```json", json.dumps(results, indent=2), "```", "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Backtest CCS against authored fixture windows")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(); results = backtest_all(); path = write_report(results, args.output)
    print(f"Wrote {path}")
    for result in results:
        print(f"{result['fixture']}: precision={result['window_precision']:.3f} recall={result['window_recall']:.3f} poll={result['poll_prediction_accuracy']:.3f}")


if __name__ == "__main__":
    main()
