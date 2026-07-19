from __future__ import annotations

import math
from dataclasses import dataclass, field

CONFUSION_TERMS = ("confused", "not sure", "don't understand", "doesn't make sense", "lost", "right?", "maybe")


@dataclass
class SignalWindow:
    sentiments: list[tuple[str, float]] = field(default_factory=list)
    keyword_flags: int = 0
    response_latencies: list[float] = field(default_factory=list)
    poll_correct: list[bool] = field(default_factory=list)
    student_quotes: list[str] = field(default_factory=list)
    student_ids: list[str] = field(default_factory=list)
    active_students: int = 0
    current_at: float = 0
    sentiment_events: list[tuple[str, float, float, str]] = field(default_factory=list)
    keyword_events: list[tuple[int, float]] = field(default_factory=list)
    latency_events: list[tuple[float, float]] = field(default_factory=list)
    poll_events: list[tuple[bool, float]] = field(default_factory=list)


@dataclass(frozen=True)
class CCSResult:
    score: float
    early_score: float
    state: str
    warning_threshold: float
    confirmed_threshold: float
    sentiment_signal: float
    keyword_signal: float
    latency_signal: float
    poll_miss_rate: float
    evidence: dict
    confidence: float
    limitations: str

    def as_dict(self) -> dict:
        return self.__dict__


class CCSEngine:
    """Deterministic weighted-sigmoid fusion of four confusion signals."""

    def __init__(self, *, bias=-2.2, weights=(1.6, .8, .8, 1.8), early_bias=-1.8,
                 breadth_weight=.7, warning_threshold=.4, confirmed_threshold=.6,
                 half_life_seconds=20):
        self.bias = bias
        self.weights = weights
        self.early_bias = early_bias
        self.breadth_weight = breadth_weight
        self.warning_threshold = warning_threshold
        self.confirmed_threshold = confirmed_threshold
        self.half_life_seconds = half_life_seconds

    @staticmethod
    def keyword_count(text: str) -> int:
        lowered = text.lower()
        return sum(term in lowered for term in CONFUSION_TERMS)

    def score(self, window: SignalWindow) -> CCSResult:
        def decay(at: float) -> float:
            age = max(0.0, window.current_at - at)
            return .5 ** (age / self.half_life_seconds)

        if window.sentiment_events:
            weights = [decay(at) for _, _, at, _ in window.sentiment_events]
            confused = [confidence * weight for (label, confidence, _, _), weight in zip(window.sentiment_events, weights) if label == "confused"]
            sentiment = sum(confused) / max(1, len(weights))
            student_weights = {student: weight for (_, _, _, student), weight in zip(window.sentiment_events, weights) if student}
            student_ids = list(student_weights)
            breadth = min(1.0, sum(student_weights.values()) / max(1, window.active_students))
        else:
            confused = [confidence for label, confidence in window.sentiments if label == "confused"]
            sentiment = sum(confused) / max(1, len(window.sentiments))
            student_ids = window.student_ids
            breadth = min(1.0, len(set(student_ids)) / max(1, window.active_students))
        keyword = min(1.0, sum(count * decay(at) for count, at in window.keyword_events) / 3) if window.keyword_events else min(1.0, window.keyword_flags / 3)
        if window.latency_events:
            latency_weights = [decay(at) for _, at in window.latency_events]
            average_latency = sum(value * weight for (value, _), weight in zip(window.latency_events, latency_weights)) / max(1.0, sum(latency_weights))
            latency = sum(min(1.0, max(0.0, (value - 10) / 30)) * weight for (value, _), weight in zip(window.latency_events, latency_weights)) / max(1, len(window.latency_events))
        else:
            average_latency = sum(window.response_latencies) / max(1, len(window.response_latencies))
            latency = min(1.0, max(0.0, (average_latency - 10) / 30))
        if window.poll_events:
            poll_weights = [decay(at) for _, at in window.poll_events]
            misses = sum((not answer) * weight for (answer, _), weight in zip(window.poll_events, poll_weights))
            poll_miss = misses / max(1, len(window.poll_events))
            miss_count = sum(not answer for answer, _ in window.poll_events)
        else:
            miss_count = sum(not answer for answer in window.poll_correct)
            poll_miss = miss_count / max(1, len(window.poll_correct)) if window.poll_correct else 0.0
        raw = self.bias + sum(weight * signal for weight, signal in zip(self.weights, (sentiment, keyword, latency, poll_miss))) + .4 * breadth
        early_raw = self.early_bias + sum(weight * signal for weight, signal in zip(self.weights[:3], (sentiment, keyword, latency))) + self.breadth_weight * breadth
        value = 1 / (1 + math.exp(-raw))
        early_value = 1 / (1 + math.exp(-early_raw))
        state = "confirmed" if value >= self.confirmed_threshold else "warning" if early_value >= self.warning_threshold else "calm"
        evidence = {
            "confused_lines": len(confused), "keyword_flags": window.keyword_flags,
            "average_latency_seconds": round(average_latency, 1), "poll_misses": miss_count,
            "poll_responses": len(window.poll_events) or len(window.poll_correct), "student_quotes": window.student_quotes[-3:],
            "unique_students_signaling": len(set(student_ids)), "active_students": window.active_students,
        }
        evidence_points = len(window.sentiments) + len(window.poll_correct) + len(window.response_latencies)
        return CCSResult(
            round(value, 3), round(early_value, 3), state, self.warning_threshold, self.confirmed_threshold,
            round(sentiment, 3), round(keyword, 3), round(latency, 3), round(poll_miss, 3),
            evidence, round(min(.96, .5 + evidence_points * .05), 2),
            "CCS estimates confusion from observed language, latency, and polls; silence and non-verbal cues are not captured.",
        )
