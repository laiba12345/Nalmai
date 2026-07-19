from __future__ import annotations

from collections import deque
import asyncio
import logging
from typing import AsyncIterator

from app.bkt import BKTTracker
from app.ccs import CCSEngine, SignalWindow
from app.llm import StructuredProvider
from app.nudges import NudgeEngine
from app.stream import ScriptedClass, replay_events

logger = logging.getLogger("classpulse.runtime")


class ClassRuntime:
    def __init__(self, lesson: ScriptedClass, provider: StructuredProvider, memory=None, session_id: str | None = None):
        self.lesson, self.provider = lesson, provider
        self.ccs, self.bkt, self.nudges = CCSEngine(), BKTTracker(memory=memory), NudgeEngine(provider)
        self.sentiments = deque(maxlen=5); self.latencies = deque(maxlen=5); self.quotes = deque(maxlen=5)
        self.keyword_flags = 0; self.poll_correct = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processed_sources: list[str] = []
        self.current_at = 0
        self.started = False
        self.completed = False
        self.session_id = session_id or lesson.id
        self.current_ccs = 0.0
        self.status = "created"

    def _window(self) -> SignalWindow:
        return SignalWindow(list(self.sentiments), self.keyword_flags, list(self.latencies), self.poll_correct[-8:], list(self.quotes))

    def submit_live_event(self, student_id: str, text: str, timestamp: str) -> dict:
        student_id, text = student_id.strip(), text.strip()
        if not student_id or not text:
            raise ValueError("student_id and text are required")
        if student_id not in self.lesson.students:
            self.lesson.students.append(student_id)
        event = {
            "id": f"live-{len(self.processed_sources) + self.event_queue.qsize() + 1}", "at": self.current_at,
            "type": "chat", "speaker": student_id, "text": text, "timestamp": timestamp,
            "latency_seconds": 0, "lesson_id": self.lesson.id, "concept": self.lesson.concept,
            "source": "live", "live": True,
            "session_id": self.session_id,
        }
        self.event_queue.put_nowait(event)
        return event

    async def process_event(self, event: dict) -> AsyncIterator[dict]:
        event.setdefault("source", "scripted"); event.setdefault("live", False); event["session_id"] = self.session_id
        self.processed_sources.append(event["source"]); self.current_at = event.get("at", self.current_at)
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
        self.current_ccs = result.score
        logger.info("CCS concept=%s score=%.3f evidence=%s", self.lesson.concept, result.score, result.evidence)
        yield {"kind": "ccs", "data": {**result.as_dict(), "session_id": self.session_id}}
        if event["type"] in ("chat", "poll"):
            for student in self.lesson.students:
                self.bkt.update_mastery(student, self.lesson.concept, correct=None, ccs=result.score)
            yield {"kind": "mastery", "data": {"students": self.bkt.snapshot(self.lesson.concept, self.lesson.students), "session_id": self.session_id}}
        nudge = self.nudges.consider(self.lesson.concept, result.score, result.evidence)
        if nudge:
            yield {"kind": "nudge", "data": {**nudge.model_dump(), "confidence": result.confidence, "evidence": result.evidence, "limitations": result.limitations, "llm_mode": self.provider.mode, "session_id": self.session_id}}

    async def _produce_replay(self, speed: float) -> None:
        async for event in replay_events(self.lesson, speed):
            event["source"] = "scripted"; event["live"] = False
            await self.event_queue.put(event)
        await self.event_queue.put(None)

    async def run(self, speed=1.0) -> AsyncIterator[dict]:
        self.started = True
        self.status = "running"
        yield {"kind": "session", "data": {"lesson": self.lesson.title, "concept": self.lesson.concept, "students": self.lesson.students, "llm_mode": self.provider.mode, "session_id": self.session_id}}
        yield {"kind": "mastery", "data": {"students": self.bkt.snapshot(self.lesson.concept, self.lesson.students), "initial": True, "session_id": self.session_id}}
        producer = asyncio.create_task(self._produce_replay(speed))
        while True:
            event = await self.event_queue.get()
            if event is None:
                while not self.event_queue.empty():
                    queued = self.event_queue.get_nowait()
                    if queued is not None:
                        async for message in self.process_event(queued):
                            yield message
                break
            async for message in self.process_event(event):
                yield message
        await producer
        self.completed = True
        self.status = "complete"
        yield {"kind": "complete", "data": {"lesson": self.lesson.id, "session_id": self.session_id}}
