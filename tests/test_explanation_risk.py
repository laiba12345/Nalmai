import asyncio
import json

from app.llm import DemoStructuredProvider, EXPLANATION_RISK_SCHEMA, OpenAIStructuredProvider
from app.runtime import ClassRuntime
from app.stream import ScriptedClass


def test_teacher_explanation_risk_uses_strict_structured_output():
    class Responses:
        def __init__(self): self.kwargs = None
        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("R", (), {"output_text": json.dumps({
                "concept": "fractions", "factual_risk": .1, "clarity_risk": .8,
                "possible_issue": "Rule lacks conceptual explanation", "evidence": "Only a rule was stated",
                "suggested_check": "Ask why equal wholes matter"
            })})()
    responses = Responses(); provider = OpenAIStructuredProvider(type("C", (), {"responses": responses})())
    result = provider.analyze_explanation("fractions", "Always choose the smaller denominator")
    assert result.clarity_risk == .8
    assert responses.kwargs["text"]["format"]["schema"] == EXPLANATION_RISK_SCHEMA
    assert responses.kwargs["text"]["format"]["strict"] is True


def test_runtime_emits_explanation_risk_for_teacher_turns():
    runtime = ClassRuntime(ScriptedClass.load("fractions_live"), DemoStructuredProvider())
    messages = asyncio.run(_first_teacher(runtime))
    risk = next(message for message in messages if message["kind"] == "explanation_risk")
    assert risk["data"]["concept"] == "fractions"
    assert 0 <= risk["data"]["factual_risk"] <= 1
    assert "session_id" in risk["data"]


def test_elevated_teacher_explanation_risk_emits_teaching_suggestion():
    runtime = ClassRuntime(ScriptedClass.load("fractions_live"), DemoStructuredProvider(), live_mode=True)
    event = {
        "id": "risky-teacher-1", "at": 1, "type": "teacher", "speaker": "Teacher",
        "text": "Always use this rule. Just remember it without asking why.",
    }
    messages = asyncio.run(_process(runtime, event))
    nudge = next(message for message in messages if message["kind"] == "nudge")
    assert nudge["data"]["trigger_source"] == "explanation_risk"
    assert nudge["data"]["evidence"]["clarity_risk"] >= .55


def test_repeated_elevated_teacher_risk_is_deduplicated_until_risk_resets():
    runtime = ClassRuntime(ScriptedClass.load("fractions_live"), DemoStructuredProvider(), live_mode=True)
    risky = {"at": 1, "type": "teacher", "speaker": "Teacher", "text": "Always just remember this rule."}
    first = asyncio.run(_process(runtime, {**risky, "id": "risk-1"}))
    second = asyncio.run(_process(runtime, {**risky, "id": "risk-2", "at": 2}))
    assert any(message["kind"] == "nudge" for message in first)
    assert not any(message["kind"] == "nudge" for message in second)


async def _first_teacher(runtime):
    event = runtime.lesson.events[0].copy()
    return [message async for message in runtime.process_event(event)]


async def _process(runtime, event):
    return [message async for message in runtime.process_event(event)]
