import asyncio
import time
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


def test_chat_soft_evidence_only_updates_the_student_who_spoke():
    lesson = ScriptedClass("individual", "Individual evidence", "fractions", ["A", "B"], [])
    runtime = ClassRuntime(lesson, DemoStructuredProvider())
    before_a = runtime.bkt.get("A", "fractions")
    before_b = runtime.bkt.get("B", "fractions")
    event = {"at": 1, "type": "chat", "speaker": "A", "text": "I am confused and do not understand", "latency_seconds": 2}
    asyncio.run(_process(runtime, event))
    assert runtime.bkt.get("A", "fractions") < before_a
    assert runtime.bkt.get("B", "fractions") == before_b


def test_poll_correctness_is_not_followed_by_class_wide_ccs_penalty():
    lesson = ScriptedClass("poll", "Poll evidence", "fractions", ["A", "B"], [])
    runtime = ClassRuntime(lesson, DemoStructuredProvider())
    expected = runtime.bkt.update_mastery("Expected", "fractions", correct=True, ccs=None)
    event = {"at": 2, "type": "poll", "question": "Which is larger?", "responses": {"A": True, "B": False}}
    asyncio.run(_process(runtime, event))
    assert runtime.bkt.get("A", "fractions") == expected
    assert runtime.bkt.states[("A", "fractions")].soft_updates == 0
    assert runtime.bkt.states[("B", "fractions")].soft_updates == 0


async def _process(runtime, event):
    return [message async for message in runtime.process_event(event)]


def test_neutral_and_positive_language_do_not_lower_mastery():
    lesson = ScriptedClass("language", "Language boundary", "fractions", ["A", "B"], [])
    runtime = ClassRuntime(lesson, DemoStructuredProvider())
    before = runtime.bkt.get("A", "fractions")
    asyncio.run(_process(runtime, {"id": "neutral", "at": 1, "type": "chat", "speaker": "A", "text": "I see the example.", "latency_seconds": 1}))
    asyncio.run(_process(runtime, {"id": "positive", "at": 2, "type": "chat", "speaker": "A", "text": "I understand because the pieces are equal.", "latency_seconds": 1}))
    assert runtime.bkt.get("A", "fractions") == before
    assert runtime.bkt.states[("A", "fractions")].soft_updates == 0


def test_same_student_utterance_is_soft_applied_exactly_once():
    lesson = ScriptedClass("once", "Once only", "fractions", ["A"], [])
    runtime = ClassRuntime(lesson, DemoStructuredProvider())
    event = {"id": "message-1", "at": 1, "type": "chat", "speaker": "A", "text": "I am confused", "latency_seconds": 1}
    asyncio.run(_process(runtime, event))
    after_first = runtime.bkt.get("A", "fractions")
    messages = asyncio.run(_process(runtime, event))
    assert runtime.bkt.get("A", "fractions") == after_first
    assert runtime.bkt.states[("A", "fractions")].soft_updates == 1
    assert messages[0]["kind"] == "duplicate_ignored"


class SlowProvider(DemoStructuredProvider):
    def classify_sentiment(self, text):
        time.sleep(.15)
        return super().classify_sentiment(text)


class BrokenProvider(DemoStructuredProvider):
    mode = "broken-test-provider"
    def classify_sentiment(self, text):
        raise RuntimeError("provider unavailable")


def test_slow_provider_does_not_freeze_unrelated_session():
    lesson = ScriptedClass("concurrent", "Concurrent", "fractions", ["A"], [])
    slow = ClassRuntime(lesson, SlowProvider(), model_timeout=.5)
    fast = ClassRuntime(lesson, DemoStructuredProvider(), model_timeout=.5)
    event = lambda event_id: {"id": event_id, "at": 1, "type": "chat", "speaker": "A", "text": "I am confused", "latency_seconds": 1}

    async def exercise():
        slow_task = asyncio.create_task(_process(slow, event("slow")))
        await asyncio.sleep(.01)
        started = time.perf_counter()
        await _process(fast, event("fast"))
        fast_elapsed = time.perf_counter() - started
        await slow_task
        return fast_elapsed

    assert asyncio.run(exercise()) < .1


def test_provider_error_is_visible_and_does_not_fabricate_analysis():
    lesson = ScriptedClass("error", "Error", "fractions", ["A"], [])
    runtime = ClassRuntime(lesson, BrokenProvider(), model_timeout=.05)
    messages = asyncio.run(_process(runtime, {"id": "error-1", "at": 1, "type": "chat", "speaker": "A", "text": "I am confused", "latency_seconds": 1}))
    errors = [message for message in messages if message["kind"] == "model_error"]
    assert errors and errors[0]["data"]["operation"] == "sentiment"
    state = runtime.bkt.states[("A", "fractions")]
    assert state.mastery == runtime.bkt.initial_mastery
    assert state.soft_updates == 0


def test_provider_timeout_is_visible_and_no_sentiment_is_fabricated():
    lesson = ScriptedClass("timeout", "Timeout", "fractions", ["A"], [])
    runtime = ClassRuntime(lesson, SlowProvider(), model_timeout=.01)
    messages = asyncio.run(_process(runtime, {"id": "timeout-1", "at": 1, "type": "chat", "speaker": "A", "text": "I am confused", "latency_seconds": 1}))
    error = next(message for message in messages if message["kind"] == "model_error")
    assert error["data"]["error"] == "timeout"
    assert not any(message["kind"] == "nudge" for message in messages)


class BrokenOptionalProvider(DemoStructuredProvider):
    mode = "broken-optional-provider"
    def analyze_explanation(self, concept, text):
        raise RuntimeError("risk unavailable")
    def generate_nudge(self, *args):
        raise RuntimeError("nudge unavailable")


def test_explanation_and_nudge_failures_emit_degraded_events():
    from app.ccs import CCSEngine
    lesson = ScriptedClass("optional", "Optional", "fractions", ["A"], [])
    runtime = ClassRuntime(lesson, BrokenOptionalProvider(), model_timeout=.05)
    teacher = asyncio.run(_process(runtime, {"id": "teacher-1", "at": 1, "type": "teacher", "speaker": "Teacher", "text": "Always use this rule."}))
    assert any(message["kind"] == "model_error" and message["data"]["operation"] == "explanation_risk" for message in teacher)
    runtime.ccs = CCSEngine(bias=5)
    poll = asyncio.run(_process(runtime, {"id": "poll-1", "at": 2, "type": "poll", "question": "Check", "responses": {"A": False}}))
    assert any(message["kind"] == "model_error" and message["data"]["operation"] == "nudge" for message in poll)
    assert not any(message["kind"] == "nudge" for message in poll)


def test_teacher_followup_emits_nudge_implementation_verification():
    from app.ccs import CCSEngine
    lesson = ScriptedClass("verify", "Verify", "fractions", ["A"], [])
    runtime = ClassRuntime(lesson, DemoStructuredProvider())
    runtime.ccs = CCSEngine(bias=5)
    poll = asyncio.run(_process(runtime, {"id":"poll-trigger", "at":2, "type":"poll", "question":"Check", "responses":{"A":False}}))
    nudge = next(message for message in poll if message["kind"] == "nudge")
    teacher = asyncio.run(_process(runtime, {"id":"teacher-followup", "at":4, "type":"teacher", "speaker":"Teacher", "text":"Let us draw equal-sized fraction bars and compare the pieces."}))
    verification = next(message for message in teacher if message["kind"] == "implementation_verification")
    assert verification["data"]["nudge_id"] == nudge["data"]["nudge_id"]
    assert verification["data"]["implementation_status"] == "implemented"
    assert runtime.outcomes.get(nudge["data"]["nudge_id"]).applied is True


def test_extended_demo_emits_verified_implementation_and_followup_outcome():
    runtime = ClassRuntime(ScriptedClass.load("ahaloop_extended"), DemoStructuredProvider())
    messages = asyncio.run(_run(runtime))
    verification = next(message for message in messages if message["kind"] == "implementation_verification")
    assert verification["data"]["implementation_status"] == "implemented"
    generated = next(message for message in messages if message["kind"] == "generated_poll")
    assert generated["data"]["question"]
    assert len(generated["data"]["options"]) == 3
    outcome = runtime.outcomes.snapshot()[0]
    assert outcome["baseline_correctness"] == .25
    assert outcome["next_poll_correctness"] == 1.0
    assert outcome["correctness_delta"] == .75


class BrokenVerificationProvider(DemoStructuredProvider):
    def verify_nudge_implementation(self, concept, suggestion, strategy, teacher_text):
        raise RuntimeError("verification unavailable")


def test_verification_failure_is_visible_and_does_not_fabricate_implementation():
    from app.ccs import CCSEngine
    lesson = ScriptedClass("verify-error", "Verify error", "fractions", ["A"], [])
    runtime = ClassRuntime(lesson, BrokenVerificationProvider())
    runtime.ccs = CCSEngine(bias=5)
    poll = asyncio.run(_process(runtime, {"id":"verify-poll", "at":2, "type":"poll", "question":"Check", "responses":{"A":False}}))
    nudge = next(message for message in poll if message["kind"] == "nudge")
    teacher = asyncio.run(_process(runtime, {"id":"verify-teacher", "at":4, "type":"teacher", "speaker":"Teacher", "text":"Draw equal-sized fraction bars."}))
    assert any(message["kind"] == "model_error" and message["data"]["operation"] == "implementation_verification" for message in teacher)
    assert runtime.outcomes.get(nudge["data"]["nudge_id"]).implementation_status == "not_checked"
