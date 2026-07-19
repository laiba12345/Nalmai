from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from app.runtime import ClassRuntime
from app.stream import ScriptedClass


@dataclass
class SessionRecord:
    session_id: str
    fixture_id: str
    runtime: ClassRuntime
    created_at: str
    mode: str = "replay"

    def summary(self) -> dict:
        return {
            "session_id": self.session_id, "fixture_id": self.fixture_id,
            "lesson": self.runtime.lesson.title, "concept": self.runtime.lesson.concept,
            "current_ccs": self.runtime.current_ccs, "status": self.runtime.status,
            "students": len(self.runtime.lesson.students), "created_at": self.created_at,
            "stream_url": f"/stream/{self.session_id}",
            "mode": self.mode,
        }


class SessionRegistry:
    def __init__(self, provider_factory: Callable, memory_factory: Callable):
        self.provider_factory, self.memory_factory = provider_factory, memory_factory
        self.sessions: dict[str, SessionRecord] = {}

    def create(self, fixture_id: str, session_id: str | None = None, mode: str = "replay") -> SessionRecord:
        fixture_id = fixture_id.replace("_", "-")
        lesson = ScriptedClass.load_available(fixture_id.replace("-", "_"))
        session_id = session_id or uuid4().hex[:12]
        if session_id in self.sessions:
            raise ValueError(f"Session already exists: {session_id}")
        if mode not in {"replay", "live"}:
            raise ValueError("mode must be replay or live")
        runtime = ClassRuntime(lesson, self.provider_factory(), memory=self.memory_factory(), session_id=session_id, live_mode=mode == "live")
        record = SessionRecord(session_id, fixture_id, runtime, datetime.now(timezone.utc).isoformat(), mode)
        self.sessions[session_id] = record
        return record

    def get(self, session_id: str) -> SessionRecord:
        if session_id not in self.sessions:
            raise KeyError(session_id)
        return self.sessions[session_id]

    def list_sessions(self) -> list[dict]:
        return [record.summary() for record in reversed(list(self.sessions.values()))]
