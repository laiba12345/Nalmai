import asyncio
from app.llm import DemoStructuredProvider
from app.runtime import ClassRuntime
from app.stream import ScriptedClass

def test_end_to_end_runtime_emits_ccs_nudge_and_mastery_updates():
    runtime = ClassRuntime(ScriptedClass.load("fractions_live"), DemoStructuredProvider())
    messages = asyncio.run(_run(runtime))
    assert any(m["kind"] == "event" for m in messages)
    assert any(m["kind"] == "ccs" and m["data"]["score"] > .6 for m in messages)
    assert sum(m["kind"] == "nudge" for m in messages) == 1
    assert any(m["kind"] == "mastery" for m in messages)

async def _run(runtime):
    return [message async for message in runtime.run(speed=10_000)]
