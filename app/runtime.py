from __future__ import annotations

from collections import deque
import asyncio
import logging
from typing import AsyncIterator

from app.bkt import BKTTracker
from app.ccs import CCSEngine, SignalWindow
from app.llm import StructuredProvider
from app.nudges import NudgeEngine
from app.outcomes import OutcomeTracker
from app.transcription import DiarizedSegment
from app.stream import ScriptedClass, replay_events

logger = logging.getLogger("classpulse.runtime")


class ClassRuntime:
    def __init__(self, lesson: ScriptedClass, provider: StructuredProvider, memory=None, session_id: str | None = None, live_mode: bool = False):
        self.lesson, self.provider = lesson, provider
        self.ccs, self.bkt, self.nudges = CCSEngine(), BKTTracker(memory=memory), NudgeEngine(provider)
        self.sentiments = deque(maxlen=5); self.latencies = deque(maxlen=5); self.quotes = deque(maxlen=5)
        self.sentiment_events = deque(maxlen=20); self.keyword_events = deque(maxlen=20)
        self.latency_events = deque(maxlen=20); self.poll_events = deque(maxlen=40)
        self.student_ids = deque(maxlen=20)
        self.keyword_flags = 0; self.poll_correct = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processed_sources: list[str] = []
        self.current_at = 0
        self.started = False
        self.completed = False
        self.session_id = session_id or lesson.id
        self.current_ccs = 0.0
        self.outcomes = OutcomeTracker()
        self.last_poll_correctness: float | None = None
        self.status = "created"
        self.live_mode = live_mode

    def _window(self) -> SignalWindow:
        return SignalWindow(
            sentiments=list(self.sentiments), keyword_flags=self.keyword_flags,
            response_latencies=list(self.latencies), poll_correct=self.poll_correct[-8:],
            student_quotes=list(self.quotes), student_ids=list(self.student_ids),
            active_students=len(self.lesson.students), current_at=self.current_at,
            sentiment_events=list(self.sentiment_events), keyword_events=list(self.keyword_events),
            latency_events=list(self.latency_events), poll_events=list(self.poll_events),
        )

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

    def submit_transcript_segment(self, segment: DiarizedSegment, *, offset_seconds: float, teacher_speaker: str) -> dict:
        is_teacher = segment.speaker == teacher_speaker
        event = {
            "id": f"audio-{len(self.processed_sources) + self.event_queue.qsize() + 1}",
            "at": round(offset_seconds + segment.start, 3), "end_at": round(offset_seconds + segment.end, 3),
            "type": "teacher" if is_teacher else "chat", "speaker": "Teacher" if is_teacher else segment.speaker,
            "text": segment.text, "latency_seconds": 0, "source": "live_audio", "live": True,
            "session_id": self.session_id, "lesson_id": self.lesson.id, "concept": self.lesson.concept,
        }
        if not is_teacher and segment.speaker not in self.lesson.students:
            self.lesson.students.append(segment.speaker)
        self.event_queue.put_nowait(event)
        return event

    def decide_nudge(self, nudge_id: str, decision: str) -> dict:
        return self.outcomes.decide(nudge_id, decision, self.current_at).as_dict()

    def stop(self) -> None:
        if not self.completed:
            self.event_queue.put_nowait(None)

    async def process_event(self, event: dict) -> AsyncIterator[dict]:
        event.setdefault("source", "scripted"); event.setdefault("live", False); event["session_id"] = self.session_id
        self.processed_sources.append(event["source"]); self.current_at = event.get("at", self.current_at)
        yield {"kind": "event", "data": event}
        if event["type"] in ("teacher", "chat"):
            sentiment = self.provider.classify_sentiment(event["text"])
            event["learning_state"] = sentiment.model_dump()
        if event["type"] == "teacher":
            risk = self.provider.analyze_explanation(self.lesson.concept, event["text"])
            yield {"kind": "explanation_risk", "data": {**risk.model_dump(), "session_id": self.session_id, "at": self.current_at}}
        if event["type"] == "chat":
            effective_label = "confused" if sentiment.confusion_probability >= .5 else sentiment.sentiment
            self.sentiments.append((effective_label, sentiment.confusion_probability))
            self.sentiment_events.append((effective_label, sentiment.confusion_probability, self.current_at, event.get("speaker", "")))
            latency = float(event.get("latency_seconds", 0)); self.latencies.append(latency)
            self.latency_events.append((latency, self.current_at))
            keyword_count = self.ccs.keyword_count(event["text"]); self.keyword_flags += keyword_count
            self.keyword_events.append((keyword_count, self.current_at))
            self.student_ids.append(event.get("speaker", ""))
            self.quotes.append(event["text"])
        elif event["type"] == "poll":
            answers = list(event["responses"].values()); self.poll_correct.extend(answers)
            self.last_poll_correctness = sum(answers) / len(answers)
            self.outcomes.observe_poll(self.lesson.concept, self.current_at, self.last_poll_correctness)
            self.poll_events.extend((answer, self.current_at) for answer in answers)
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
            outcome = self.outcomes.register(self.lesson.concept, self.current_at, self.last_poll_correctness)
            yield {"kind": "nudge", "data": {**nudge.model_dump(), "nudge_id": outcome.nudge_id, "confidence": result.confidence, "evidence": result.evidence, "limitations": result.limitations, "llm_mode": self.provider.mode, "session_id": self.session_id}}

    async def _produce_replay(self, speed: float) -> None:
        if self.live_mode:
            return
        async for event in replay_events(self.lesson, speed):
            event["source"] = self.lesson.source; event["live"] = False
            await self.event_queue.put(event)
        await self.event_queue.put(None)

    async def run(self, speed=1.0) -> AsyncIterator[dict]:
        self.started = True
        self.status = "running"
        yield {"kind": "session", "data": {"lesson": self.lesson.title, "concept": self.lesson.concept, "students": self.lesson.students, "llm_mode": self.provider.mode, "session_id": self.session_id, "nudge_applied": self.lesson.nudge_applied, "source": self.lesson.source, "source_metadata": self.lesson.source_metadata}}
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
