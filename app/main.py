from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.llm import build_provider
from app.runtime import ClassRuntime
from app.stream import ScriptedClass

ROOT = Path(__file__).parents[1]
PUBLIC = ROOT / "public"
app = FastAPI(title="ClassPulse", version="1.0.0")
app.mount("/static", StaticFiles(directory=PUBLIC), name="static")


@app.get("/api/health")
def health():
    provider = build_provider()
    return {"status": "ok", "service": "ClassPulse", "llm_mode": provider.mode, "model": "gpt-5.6" if provider.mode == "gpt-5.6" else None}


@app.get("/api/classes")
def classes():
    return ScriptedClass.catalog()


@app.get("/api/stream/{lesson_id}")
async def stream(lesson_id: str, speed: float = Query(3.0, gt=0, le=10_000)):
    try:
        lesson = ScriptedClass.load(lesson_id.replace("-", "_"))
    except FileNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    runtime = ClassRuntime(lesson, build_provider())

    async def events():
        async for message in runtime.run(speed):
            yield f"event: {message['kind']}\ndata: {json.dumps(message['data'])}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(PUBLIC / "index.html")
