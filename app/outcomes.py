"""Track teacher decisions and the first subsequent poll outcome."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from uuid import uuid4


@dataclass
class NudgeOutcome:
    nudge_id: str
    concept: str
    trigger_at: float
    baseline_correctness: float | None
    decision: str = "pending"
    decided_at: float | None = None
    next_poll_at: float | None = None
    next_poll_correctness: float | None = None

    @property
    def applied(self) -> bool:
        return self.decision == "applied"

    @property
    def correctness_delta(self) -> float | None:
        if self.baseline_correctness is None or self.next_poll_correctness is None:
            return None
        return round(self.next_poll_correctness - self.baseline_correctness, 3)

    def as_dict(self) -> dict:
        return {**asdict(self), "applied": self.applied, "correctness_delta": self.correctness_delta}


class OutcomeTracker:
    def __init__(self):
        self.records: dict[str, NudgeOutcome] = {}

    def register(self, concept: str, trigger_at: float, baseline_correctness: float | None) -> NudgeOutcome:
        record = NudgeOutcome(uuid4().hex[:12], concept, trigger_at, baseline_correctness)
        self.records[record.nudge_id] = record
        return record

    def decide(self, nudge_id: str, decision: str, decided_at: float) -> NudgeOutcome:
        if decision not in {"applied", "dismissed"}:
            raise ValueError("decision must be applied or dismissed")
        record = self.get(nudge_id)
        record.decision, record.decided_at = decision, decided_at
        return record

    def observe_poll(self, concept: str, at: float, correctness: float) -> None:
        for record in self.records.values():
            if record.concept == concept and record.next_poll_at is None and at > record.trigger_at:
                record.next_poll_at, record.next_poll_correctness = at, round(correctness, 3)

    def get(self, nudge_id: str) -> NudgeOutcome:
        if nudge_id not in self.records:
            raise KeyError(nudge_id)
        return self.records[nudge_id]

    def snapshot(self) -> list[dict]:
        return [record.as_dict() for record in self.records.values()]
