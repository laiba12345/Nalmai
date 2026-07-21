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

logger = logging.getLogger("nalmai.runtime")


class ClassRuntime:
    def __init__(self, lesson: ScriptedClass, provider: StructuredProvider, memory=None, session_id: str | None = None, live_mode: bool = False, model_timeout: float = 8.0):
        self.lesson, self.provider = lesson, provider
        self.outcomes = OutcomeTracker()
        self.ccs, self.bkt, self.nudges = CCSEngine(), BKTTracker(memory=memory), NudgeEngine(provider, outcomes=self.outcomes)
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
        self.last_poll_correctness: float | None = None
        self.status = "created"
        self.live_mode = live_mode
        self.model_timeout = model_timeout
        self.processed_event_ids: set[str] = set()

    async def _model_call(self, operation: str, function, *args):
        try:
            return await asyncio.wait_for(asyncio.to_thread(function, *args), timeout=self.model_timeout), None
        except asyncio.TimeoutError:
            return None, {"operation": operation, "error": "timeout", "message": f"{operation} model call timed out", "provider": self.provider.mode, "session_id": self.session_id}
        except Exception as error:
            logger.warning("model call failed operation=%s provider=%s error=%s", operation, self.provider.mode, error)
            return None, {"operation": operation, "error": "provider_error", "message": str(error), "provider": self.provider.mode, "session_id": self.session_id}

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

    def submit_transcript_segment(self, segment: DiarizedSegment, *, offset_seconds: float, teacher_speaker: str,
                                  student_id: str | None = None, known_role: str | None = None,
                                  known_speaker_id: str | None = None) -> dict:
        is_teacher = known_role == "teacher" if known_role else segment.speaker == teacher_speaker
        speaker = known_speaker_id if known_role and known_speaker_id else ("Teacher" if is_teacher else (student_id or segment.speaker))
        event = {
            "id": f"audio-{len(self.processed_sources) + self.event_queue.qsize() + 1}",
            "at": round(offset_seconds + segment.start, 3), "end_at": round(offset_seconds + segment.end, 3),
            "type": "teacher" if is_teacher else "chat", "speaker": speaker,
            "text": segment.text, "latency_seconds": 0, "source": "live_audio", "live": True,
            "session_id": self.session_id, "lesson_id": self.lesson.id, "concept": self.lesson.concept,
        }
        if not is_teacher and segment.speaker not in self.lesson.students:
            self.lesson.students.append(segment.speaker)
        self.event_queue.put_nowait(event)
        return event

    def submit_live_poll(self, question: str, responses: dict[str, bool]) -> dict:
        if not question.strip() or not responses:
            raise ValueError("question and responses are required")
        event = {
            "id": f"poll-{len(self.processed_sources) + self.event_queue.qsize() + 1}",
            "at": self.current_at + .001, "type": "poll", "question": question.strip(),
            "responses": responses, "source": "live_poll", "live": True,
            "session_id": self.session_id, "lesson_id": self.lesson.id, "concept": self.lesson.concept,
        }
        for student in responses:
            if student not in self.lesson.students:
                self.lesson.students.append(student)
        self.event_queue.put_nowait(event)
        return event

    def decide_nudge(self, nudge_id: str, decision: str) -> dict:
        return self.outcomes.decide(nudge_id, decision, self.current_at).as_dict()

    def stop(self) -> None:
        if not self.completed:
            self.event_queue.put_nowait(None)

    async def process_event(self, event: dict) -> AsyncIterator[dict]:
        event_id = event.get("id")
        if event_id and event_id in self.processed_event_ids:
            yield {"kind": "duplicate_ignored", "data": {"event_id": event_id, "session_id": self.session_id}}
            return
        if event_id:
            self.processed_event_ids.add(event_id)
        event.setdefault("source", "scripted"); event.setdefault("live", False); event["session_id"] = self.session_id
        self.processed_sources.append(event["source"]); self.current_at = event.get("at", self.current_at)
        yield {"kind": "event", "data": event}
        sentiment = None
        if event["type"] == "chat":
            sentiment, error = await self._model_call("sentiment", self.provider.classify_sentiment, event["text"])
            if error:
                yield {"kind": "model_error", "data": error}
            else:
                event["learning_state"] = sentiment.model_dump()
        if event["type"] == "teacher":
            risk, error = await self._model_call("explanation_risk", self.provider.analyze_explanation, self.lesson.concept, event["text"])
            if error:
                yield {"kind": "model_error", "data": error}
            else:
                yield {"kind": "explanation_risk", "data": {**risk.model_dump(), "session_id": self.session_id, "at": self.current_at}}
            pending = self.outcomes.pending_verification(self.lesson.concept, self.current_at)
            if pending:
                verification, error = await self._model_call("implementation_verification", self.provider.verify_nudge_implementation, self.lesson.concept, pending.suggestion, pending.strategy, event["text"])
                if error:
                    yield {"kind": "model_error", "data": error}
                else:
                    record = self.outcomes.record_implementation(pending.nudge_id, verification.status, verification.confidence, verification.evidence_quote, verification.rationale, self.current_at)
                    yield {"kind": "implementation_verification", "data": {**record.as_dict(), "session_id": self.session_id}}
                    if verification.status == "implemented":
                        poll, poll_error = await self._model_call("followup_poll", self.provider.generate_followup_poll, self.lesson.concept, pending.suggestion, event["text"], "followup")
                        if poll_error:
                            yield {"kind": "model_error", "data": poll_error}
                        else:
                            yield {"kind": "generated_poll", "data": {**poll.model_dump(), "poll_id": f"{pending.nudge_id}-followup", "stage": "followup", "nudge_id": pending.nudge_id, "session_id": self.session_id, "llm_mode": self.provider.mode}}
            if risk is not None and self.live_mode:
                risk_score = max(risk.factual_risk, risk.clarity_risk)
                selection = self.nudges.prepare_risk(self.lesson.concept, risk_score)
                if selection:
                    strategy, mode, reason = selection
                    evidence = {
                        "trigger_source": "explanation_risk", "factual_risk": risk.factual_risk,
                        "clarity_risk": risk.clarity_risk, "possible_issue": risk.possible_issue,
                        "teacher_evidence": risk.evidence, "suggested_check": risk.suggested_check,
                    }
                    nudge, nudge_error = await self._model_call(
                        "nudge", self.provider.generate_nudge, self.lesson.concept,
                        evidence, strategy, mode, reason,
                    )
                    if nudge_error:
                        yield {"kind": "model_error", "data": nudge_error}
                    else:
                        outcome = self.outcomes.register(
                            self.lesson.concept, self.current_at, self.last_poll_correctness,
                            strategy=nudge.strategy, suggestion=nudge.suggested_reframing,
                        )
                        yield {"kind": "nudge", "data": {
                            **nudge.model_dump(), "nudge_id": outcome.nudge_id,
                            "trigger_source": "explanation_risk", "evidence_quality": risk_score,
                            "evidence": evidence,
                            "limitations": "Explanation risk is based on one transcript window and should be treated as coaching evidence, not a definitive judgment.",
                            "llm_mode": self.provider.mode, "session_id": self.session_id,
                        }}
                        baseline_poll, poll_error = await self._model_call(
                            "baseline_poll", self.provider.generate_followup_poll,
                            self.lesson.concept, nudge.suggested_reframing,
                            "Observed teacher explanation risk before re-teaching.", "baseline",
                        )
                        if poll_error:
                            yield {"kind": "model_error", "data": poll_error}
                        else:
                            yield {"kind": "generated_poll", "data": {
                                **baseline_poll.model_dump(), "poll_id": f"{outcome.nudge_id}-baseline",
                                "stage": "baseline", "nudge_id": outcome.nudge_id,
                                "session_id": self.session_id, "llm_mode": self.provider.mode,
                            }}
        if event["type"] == "chat":
            if sentiment is not None:
                effective_label = "confused" if sentiment.confusion_probability >= .5 else sentiment.sentiment
                self.sentiments.append((effective_label, sentiment.confusion_probability))
                self.sentiment_events.append((effective_label, sentiment.confusion_probability, self.current_at, event.get("speaker", "")))
            latency = float(event.get("latency_seconds", 0)); self.latencies.append(latency)
            self.latency_events.append((latency, self.current_at))
            keyword_count = self.ccs.keyword_count(event["text"]); self.keyword_flags += keyword_count
            self.keyword_events.append((keyword_count, self.current_at))
            self.student_ids.append(event.get("speaker", ""))
            self.quotes.append(event["text"])
            if sentiment is not None and sentiment.sentiment == "confused" and sentiment.confusion_probability >= .5:
                self.bkt.update_mastery(event.get("speaker", "Unknown"), self.lesson.concept, correct=None, language_confusion=sentiment.confusion_probability)
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
            yield {"kind": "mastery", "data": {"students": self.bkt.snapshot(self.lesson.concept, self.lesson.students), "session_id": self.session_id}}
        selection = self.nudges.prepare(self.lesson.concept, result.score)
        if selection:
            strategy, mode, reason = selection
            nudge, error = await self._model_call("nudge", self.provider.generate_nudge, self.lesson.concept, result.evidence, strategy, mode, reason)
            if error:
                yield {"kind": "model_error", "data": error}
                return
            outcome = self.outcomes.register(self.lesson.concept, self.current_at, self.last_poll_correctness, strategy=nudge.strategy, suggestion=nudge.suggested_reframing)
            yield {"kind": "nudge", "data": {**nudge.model_dump(), "nudge_id": outcome.nudge_id, "evidence_quality": result.evidence_quality, "evidence": result.evidence, "limitations": result.limitations, "llm_mode": self.provider.mode, "session_id": self.session_id}}
            baseline_poll, poll_error = await self._model_call("baseline_poll", self.provider.generate_followup_poll, self.lesson.concept, nudge.suggested_reframing, "Observed confusion evidence before re-teaching.", "baseline")
            if poll_error:
                yield {"kind": "model_error", "data": poll_error}
            else:
                yield {"kind": "generated_poll", "data": {**baseline_poll.model_dump(), "poll_id": f"{outcome.nudge_id}-baseline", "stage": "baseline", "nudge_id": outcome.nudge_id, "session_id": self.session_id, "llm_mode": self.provider.mode}}

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
