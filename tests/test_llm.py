import json
from app.llm import DemoStructuredProvider, OpenAIStructuredProvider, SENTIMENT_SCHEMA, NUDGE_SCHEMA

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
            return type("R", (), {"output_text": json.dumps({"concept":"fractions","trigger_reason":"3 confused lines","suggested_reframing":"Draw fraction bars."})})()
    responses = FakeResponses(); client = type("C", (), {"responses": responses})()
    result = OpenAIStructuredProvider(client=client).generate_nudge("fractions", {"confused_lines":3})
    assert result.concept == "fractions"
    assert responses.kwargs["text"]["format"]["strict"] is True
    assert responses.kwargs["text"]["format"]["schema"] == NUDGE_SCHEMA
