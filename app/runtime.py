from __future__ import annotations

from collections import deque
import logging
from typing import AsyncIterator

from app.bkt import BKTTracker
from app.ccs import CCSEngine, SignalWindow
from app.llm import StructuredProvider
from app.nudges import NudgeEngine
from app.stream import ScriptedClass, replay_events

logger = logging.getLogger("classpulse.runtime")


class ClassRuntime:
    def __init__(self, lesson: ScriptedClass, provider: StructuredProvider):
        self.lesson, self.provider = lesson, provider
        self.ccs, self.bkt, self.nudges = CCSEngine(), BKTTracker(), NudgeEngine(provider)
        self.sentiments = deque(maxlen=5); self.latencies = deque(maxlen=5); self.quotes = deque(maxlen=5)
        self.keyword_flags = 0; self.poll_correct = []

    def _window(self) -> SignalWindow:
        return SignalWindow(list(self.sentiments), self.keyword_flags, list(self.latencies), self.poll_correct[-8:], list(self.quotes))

    async def run(self, speed=1.0) -> AsyncIterator[dict]:
        yield {"kind": "session", "data": {"lesson": self.lesson.title, "concept": self.lesson.concept, "students": self.lesson.students, "llm_mode": self.provider.mode}}
        for event in [item async for item in replay_events(self.lesson, speed)]:
            yield {"kind": "event", "data": event}
            if event["type"] in ("teacher", "chat"):
                sentiment = self.provider.classify_sentiment(event["text"])
            if event["type"] == "chat":
                self.sentiments.append((sentiment.sentiment, sentiment.confidence))
                self.latencies.append(float(event.get("latency_seconds", 0)))
                self.keyword_flags += self.ccs.keyword_count(event["text"])
                self.quotes.append(event["text"])
            elif event["type"] == "poll":
                answers = list(event["responses"].values()); self.poll_correct.extend(answers)
                for student, correct in event["responses"].items():
                    self.bkt.update_mastery(student, self.lesson.concept, correct=correct, ccs=None)
            result = self.ccs.score(self._window())
            logger.info("CCS concept=%s score=%.3f evidence=%s", self.lesson.concept, result.score, result.evidence)
            yield {"kind": "ccs", "data": result.as_dict()}
            if event["type"] in ("chat", "poll"):
                for student in self.lesson.students:
                    self.bkt.update_mastery(student, self.lesson.concept, correct=None, ccs=result.score)
                yield {"kind": "mastery", "data": {"students": self.bkt.snapshot(self.lesson.concept, self.lesson.students)}}
            nudge = self.nudges.consider(self.lesson.concept, result.score, result.evidence)
            if nudge:
                yield {"kind": "nudge", "data": {**nudge.model_dump(), "confidence": result.confidence, "evidence": result.evidence, "limitations": result.limitations, "llm_mode": self.provider.mode}}
        yield {"kind": "complete", "data": {"lesson": self.lesson.id}}
