from __future__ import annotations

import json
import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.llm import build_provider
from app.runtime import ClassRuntime
from app.stream import ScriptedClass
from app.real_data import TalkMovesCorpus
from app.memory import build_memory
from app.sessions import SessionRegistry
from app.config import load_env_file
from app.transcription import build_transcriber
from app.calls import CallRoomRegistry, RoomFullError

load_env_file()
from pydantic import BaseModel, Field

ROOT = Path(__file__).parents[1]
PUBLIC = ROOT / "public"
app = FastAPI(title="AhaLoop", version="1.0.0")
app.mount("/static", StaticFiles(directory=PUBLIC), name="static")
session_registry = SessionRegistry(build_provider, build_memory)
transcriber = build_transcriber()
TRANSCRIPTION_TIMEOUT = float(os.getenv("CLASSPULSE_TRANSCRIPTION_TIMEOUT", "30"))
legacy_sessions: dict[str, str] = {}
call_rooms = CallRoomRegistry(max_participants=2)


class LiveStudentInput(BaseModel):
    student_id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=1000)
    timestamp: str


class SessionCreate(BaseModel):
    fixture_id: str
    mode: str = "replay"


@app.websocket("/ws/calls/{room_id}/{participant_id}")
async def call_signaling(websocket: WebSocket, room_id: str, participant_id: str):
    if not room_id.replace("-", "").isalnum() or not participant_id.replace("-", "").isalnum():
        await websocket.close(code=1008, reason="room and participant IDs must be alphanumeric")
        return
    await websocket.accept()
    try:
        peers = await call_rooms.join(room_id, participant_id, websocket)
    except (RoomFullError, ValueError) as error:
        await websocket.send_json({"type": "error", "message": str(error)})
        await websocket.close(code=1008, reason=str(error))
        return
    await websocket.send_json({"type": "joined", "room_id": room_id, "participant_id": participant_id, "peers": peers, "capacity": 2})
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") not in {"ready", "offer", "answer", "ice"}:
                await websocket.send_json({"type": "error", "message": "unsupported signaling message"})
                continue
            await call_rooms.relay(room_id, participant_id, payload)
    except WebSocketDisconnect:
        pass
    finally:
        await call_rooms.leave(room_id, participant_id)


class NudgeDecision(BaseModel):
    decision: str


class LivePollInput(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    responses: dict[str, bool]


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
    return {"status": "ok", "service": "AhaLoop", "llm_mode": provider.mode, "model": "gpt-5.6" if provider.mode == "gpt-5.6" else None}


@app.get("/api/classes")
def classes():
    return ScriptedClass.catalog()


@app.get("/api/evidence/real-data")
def real_data_evidence():
    return TalkMovesCorpus.load().report()


@app.post("/api/sessions", status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate):
    try:
        return session_registry.create(payload.fixture_id, mode=payload.mode).summary()
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


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


@app.post("/api/sessions/{session_id}/audio-chunks", status_code=status.HTTP_202_ACCEPTED)
async def session_audio_chunk(
    session_id: str, request: Request, offset_seconds: float = Query(0, ge=0),
    teacher_speaker: str = Query("speaker_0", min_length=1), filename: str = Query("classroom.webm"),
):
    record = _session_record(session_id)
    audio = await request.body()
    if not audio:
        raise HTTPException(400, "Audio chunk is empty")
    if len(audio) > 20 * 1024 * 1024:
        raise HTTPException(413, "Audio chunk exceeds 20 MB")
    if transcriber is None:
        raise HTTPException(503, "OPENAI_API_KEY is required for live transcription")
    try:
        segments = await asyncio.wait_for(run_in_threadpool(transcriber.transcribe, audio, filename), timeout=TRANSCRIPTION_TIMEOUT)
    except asyncio.TimeoutError as error:
        raise HTTPException(504, "Transcription timed out; no transcript was fabricated") from error
    except Exception as error:
        raise HTTPException(502, f"Transcription failed: {error}") from error
    events = [
        record.runtime.submit_transcript_segment(segment, offset_seconds=offset_seconds, teacher_speaker=teacher_speaker)
        for segment in segments
    ]
    return {"accepted": True, "model": transcriber.model, "segments": [segment.as_dict() for segment in segments], "events": events}


@app.post("/api/sessions/{session_id}/nudges/{nudge_id}/decision")
def decide_session_nudge(session_id: str, nudge_id: str, payload: NudgeDecision):
    record = _session_record(session_id)
    try:
        return record.runtime.decide_nudge(nudge_id, payload.decision)
    except KeyError as error:
        raise HTTPException(404, f"Unknown nudge: {nudge_id}") from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@app.get("/api/sessions/{session_id}/outcomes")
def session_outcomes(session_id: str):
    return _session_record(session_id).runtime.outcomes.snapshot()


@app.post("/api/sessions/{session_id}/polls", status_code=status.HTTP_202_ACCEPTED)
def session_live_poll(session_id: str, payload: LivePollInput):
    runtime = _session_record(session_id).runtime
    if runtime.completed:
        raise HTTPException(409, "Session is complete")
    try:
        event = runtime.submit_live_poll(payload.question, payload.responses)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"accepted": True, "event": event}


@app.post("/api/sessions/{session_id}/stop")
def stop_session(session_id: str):
    runtime = _session_record(session_id).runtime
    runtime.stop()
    return {"stopping": True, "session_id": session_id}


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
