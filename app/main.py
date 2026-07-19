from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.llm import build_provider
from app.runtime import ClassRuntime
from app.stream import ScriptedClass
from app.real_data import TalkMovesCorpus
from app.memory import build_memory
from app.sessions import SessionRegistry
from pydantic import BaseModel, Field

ROOT = Path(__file__).parents[1]
PUBLIC = ROOT / "public"
app = FastAPI(title="ClassPulse", version="1.0.0")
app.mount("/static", StaticFiles(directory=PUBLIC), name="static")
session_registry = SessionRegistry(build_provider, build_memory)
legacy_sessions: dict[str, str] = {}


class LiveStudentInput(BaseModel):
    student_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=1000)
    timestamp: str


class SessionCreate(BaseModel):
    fixture_id: str


def _runtime_for_lesson(lesson_id: str, *, for_stream: bool = False) -> ClassRuntime:
    key = lesson_id.replace("_", "-")
    record = None
    if key in legacy_sessions:
        try:
            record = session_registry.get(legacy_sessions[key])
        except KeyError:
            record = None
    if record is None or record.runtime.completed or (for_stream and record.runtime.started):
        try:
            record = session_registry.create(key)
        except FileNotFoundError as error:
            raise HTTPException(404, str(error)) from error
        legacy_sessions[key] = record.session_id
    return record.runtime


@app.get("/api/health")
def health():
    provider = build_provider()
    return {"status": "ok", "service": "ClassPulse", "llm_mode": provider.mode, "model": "gpt-5.6" if provider.mode == "gpt-5.6" else None}


@app.get("/api/classes")
def classes():
    return ScriptedClass.catalog()


@app.get("/api/evidence/real-data")
def real_data_evidence():
    return TalkMovesCorpus.load().report()


@app.post("/api/sessions", status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate):
    try:
        return session_registry.create(payload.fixture_id).summary()
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error


@app.get("/api/sessions")
def list_sessions():
    return session_registry.list_sessions()


def _session_record(session_id: str):
    try:
        return session_registry.get(session_id)
    except KeyError as error:
        raise HTTPException(404, f"Unknown session: {session_id}") from error


@app.get("/stream/{session_id}")
async def session_stream(session_id: str, speed: float = Query(3.0, gt=0, le=10_000)):
    record = _session_record(session_id)
    if record.runtime.started:
        raise HTTPException(409, "Session stream has already been consumed")

    async def events():
        async for message in record.runtime.run(speed):
            yield f"event: {message['kind']}\ndata: {json.dumps(message['data'])}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/sessions/{session_id}/live-input", status_code=status.HTTP_202_ACCEPTED)
def session_live_input(session_id: str, payload: LiveStudentInput):
    record = _session_record(session_id)
    if record.runtime.completed:
        raise HTTPException(409, "Session is complete")
    return {"accepted": True, "event": record.runtime.submit_live_event(payload.student_id, payload.text, payload.timestamp)}


@app.get("/api/stream/{lesson_id}")
async def stream(lesson_id: str, speed: float = Query(3.0, gt=0, le=10_000)):
    runtime = _runtime_for_lesson(lesson_id, for_stream=True)

    async def events():
        async for message in runtime.run(speed):
            yield f"event: {message['kind']}\ndata: {json.dumps(message['data'])}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/live-input/{lesson_id}", status_code=status.HTTP_202_ACCEPTED)
def live_input(lesson_id: str, payload: LiveStudentInput):
    runtime = _runtime_for_lesson(lesson_id)
    try:
        event = runtime.submit_live_event(payload.student_id, payload.text, payload.timestamp)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"accepted": True, "event": event}


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(PUBLIC / "index.html")
