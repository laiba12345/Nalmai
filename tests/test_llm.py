import json
from app.llm import DemoStructuredProvider, OpenAIStructuredProvider, SENTIMENT_SCHEMA, NUDGE_SCHEMA, IMPLEMENTATION_SCHEMA, FOLLOWUP_POLL_SCHEMA

def test_demo_provider_obeys_sentiment_contract():
    result = DemoStructuredProvider().classify_sentiment("I am confused and not sure")
    assert result.sentiment == "confused"
    assert 0 <= result.confidence <= 1
    assert result.confusion_probability >= .8
    assert result.question_type in {"none", "clarification", "verification", "misconception"}

def test_openai_provider_uses_gpt_56_and_strict_json_schema():
    class FakeResponses:
        def __init__(self): self.kwargs = None
        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("R", (), {"output_text": json.dumps({"sentiment":"neutral","confidence":.8,"confusion_probability":.1,"misconception":"","question_type":"none","evidence_strength":.7})})()
    responses = FakeResponses(); client = type("C", (), {"responses": responses})()
    provider = OpenAIStructuredProvider(client=client)
    provider.classify_sentiment("hello")
    assert responses.kwargs["model"] == "gpt-5.6"
    assert responses.kwargs["text"]["format"]["strict"] is True
    assert responses.kwargs["text"]["format"]["schema"] == SENTIMENT_SCHEMA
    assert "confusion_probability" in SENTIMENT_SCHEMA["required"]
    assert NUDGE_SCHEMA["additionalProperties"] is False

def test_nudge_call_also_uses_strict_structured_outputs():
    class FakeResponses:
        def __init__(self): self.kwargs = None
        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("R", (), {"output_text": json.dumps({"concept":"fractions","trigger_reason":"3 confused lines","suggested_reframing":"Draw fraction bars.","strategy":"visual_model","selection_mode":"exploration","strategy_selection_reason":"Neutral exploration."})})()
    responses = FakeResponses(); client = type("C", (), {"responses": responses})()
    result = OpenAIStructuredProvider(client=client).generate_nudge("fractions", {"confused_lines":3})
    assert result.concept == "fractions"
    assert responses.kwargs["text"]["format"]["strict"] is True
    assert responses.kwargs["text"]["format"]["schema"] == NUDGE_SCHEMA
    assert result.strategy == "visual_model"

def test_nudge_implementation_verification_uses_strict_schema():
    class FakeResponses:
        def __init__(self): self.kwargs = None
        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("R", (), {"output_text": json.dumps({
                "status":"implemented", "confidence":.91,
                "evidence_quote":"Compare these equal-sized fraction bars.",
                "rationale":"The teacher used the recommended visual comparison."
            })})()
    responses = FakeResponses(); client = type("C", (), {"responses": responses})()
    result = OpenAIStructuredProvider(client=client).verify_nudge_implementation(
        "fractions", "Draw equal-sized fraction bars.", "visual_model",
        "Compare these equal-sized fraction bars."
    )
    assert result.status == "implemented"
    assert responses.kwargs["text"]["format"]["strict"] is True
    assert responses.kwargs["text"]["format"]["schema"] == IMPLEMENTATION_SCHEMA

def test_demo_verifier_requires_strategy_evidence_in_teacher_speech():
    provider = DemoStructuredProvider()
    implemented = provider.verify_nudge_implementation(
        "fractions", "Draw equal-sized fraction bars.", "visual_model",
        "Let us draw two equal-sized fraction bars and compare the pieces."
    )
    unrelated = provider.verify_nudge_implementation(
        "fractions", "Draw equal-sized fraction bars.", "visual_model",
        "Please copy the next question."
    )
    assert implemented.status == "implemented"
    assert unrelated.status == "not_implemented"


def test_followup_poll_generation_uses_gpt_56_strict_schema():
    class FakeResponses:
        def __init__(self): self.kwargs = None
        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("R", (), {"output_text": json.dumps({
                "concept":"fractions", "question":"Which is greater?",
                "options":["1/4", "1/8", "They are equal"], "correct_index":0,
                "explanation":"Fourth-sized pieces are larger.",
                "checks":"Whether denominator size is inversely related to unit-fraction size."
            })})()
    responses=FakeResponses();client=type("C",(),{"responses":responses})()
    result=OpenAIStructuredProvider(client=client).generate_followup_poll("fractions","Use fraction bars.","The teacher drew equal fraction bars.")
    assert result.correct_index == 0
    assert len(result.options) == 3
    assert responses.kwargs["text"]["format"]["strict"] is True
    assert responses.kwargs["text"]["format"]["schema"] == FOLLOWUP_POLL_SCHEMA


def test_demo_followup_poll_has_one_valid_correct_option():
    result=DemoStructuredProvider().generate_followup_poll("fractions","Use fraction bars.","We drew equal bars.")
    assert len(result.options) == 3
    assert 0 <= result.correct_index < len(result.options)
