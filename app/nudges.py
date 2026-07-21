from __future__ import annotations

from app.llm import NudgeResult, StructuredProvider
from app.outcomes import OutcomeTracker


class NudgeEngine:
    def __init__(self, provider: StructuredProvider, threshold=.6, reset_threshold=.4, outcomes: OutcomeTracker | None = None):
        self.provider, self.threshold, self.reset_threshold = provider, threshold, reset_threshold
        self.outcomes = outcomes or OutcomeTracker()
        self.active_spikes: set[str] = set()

    def consider(self, concept: str, ccs: float, evidence: dict) -> NudgeResult | None:
        selection = self.prepare(concept, ccs)
        if selection is None:
            return None
        strategy, mode, reason = selection
        return self.provider.generate_nudge(concept, evidence, strategy, mode, reason)

    def prepare(self, concept: str, ccs: float) -> tuple[str, str, str] | None:
        return self._prepare_signal(concept, ccs, self.threshold, self.reset_threshold)

    def prepare_risk(self, concept: str, risk: float, threshold=.55, reset_threshold=.35) -> tuple[str, str, str] | None:
        return self._prepare_signal(f"explanation-risk:{concept}", risk, threshold, reset_threshold, concept)

    def _prepare_signal(self, spike_key: str, value: float, threshold: float, reset_threshold: float,
                        strategy_concept: str | None = None) -> tuple[str, str, str] | None:
        if value <= reset_threshold:
            self.active_spikes.discard(spike_key)
            return None
        if value < threshold or spike_key in self.active_spikes:
            return None
        self.active_spikes.add(spike_key)
        return self.outcomes.select_strategy(strategy_concept or spike_key)
