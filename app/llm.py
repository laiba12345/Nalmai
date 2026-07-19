from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

SENTIMENT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "sentiment": {"type": "string", "enum": ["confused", "neutral", "positive"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "confusion_probability": {"type": "number", "minimum": 0, "maximum": 1},
        "misconception": {"type": "string"},
        "question_type": {"type": "string", "enum": ["none", "clarification", "verification", "misconception"]},
        "evidence_strength": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": ["sentiment", "confidence", "confusion_probability", "misconception", "question_type", "evidence_strength"],
}
NUDGE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {"concept": {"type": "string"}, "trigger_reason": {"type": "string"}, "suggested_reframing": {"type": "string"}},
    "required": ["concept", "trigger_reason", "suggested_reframing"],
}


class SentimentResult(BaseModel):
    sentiment: Literal["confused", "neutral", "positive"]
    confidence: float = Field(ge=0, le=1)
    confusion_probability: float = Field(ge=0, le=1)
    misconception: str
    question_type: Literal["none", "clarification", "verification", "misconception"]
    evidence_strength: float = Field(ge=0, le=1)


class NudgeResult(BaseModel):
    concept: str
    trigger_reason: str
    suggested_reframing: str


class StructuredProvider(ABC):
    mode: str
    @abstractmethod
    def classify_sentiment(self, text: str) -> SentimentResult: ...
    @abstractmethod
    def generate_nudge(self, concept: str, evidence: dict) -> NudgeResult: ...


class OpenAIStructuredProvider(StructuredProvider):
    mode = "gpt-5.6"
    def __init__(self, client=None):
        if client is None:
            from openai import OpenAI
            client = OpenAI()
        self.client = client

    def _request(self, instructions: str, prompt: str, name: str, schema: dict) -> dict:
        response = self.client.responses.create(
            model="gpt-5.6", instructions=instructions, input=prompt,
            text={"format": {"type": "json_schema", "name": name, "strict": True, "schema": schema}},
        )
        return json.loads(response.output_text)

    def classify_sentiment(self, text: str) -> SentimentResult:
        payload = self._request("Classify the student's expressed learning state. Identify uncertainty, clarification or verification questions, and explicit misconceptions. Probability must reflect confusion rather than general negative sentiment. Return the strict schema.", text, "classroom_sentiment", SENTIMENT_SCHEMA)
        return SentimentResult.model_validate(payload)

    def generate_nudge(self, concept: str, evidence: dict) -> NudgeResult:
        prompt = f"Concept: {concept}\nObserved signals: {json.dumps(evidence)}\nDraft one short, concrete re-explanation. Cite signal counts; do not diagnose students."
        payload = self._request("You are a real-time teacher copilot. Return only the strict schema.", prompt, "teacher_nudge", NUDGE_SCHEMA)
        return NudgeResult.model_validate(payload)


class DemoStructuredProvider(StructuredProvider):
    """Credential-free, explicitly labeled test/demo stand-in for the typed LLM boundary."""
    mode = "deterministic-demo-fallback"
    def classify_sentiment(self, text: str) -> SentimentResult:
        lowered = text.lower()
        if any(term in lowered for term in ("confused", "not sure", "don't understand", "doesn't make sense", "lost", "right?")):
            return SentimentResult(sentiment="confused", confidence=.9, confusion_probability=.9, misconception="", question_type="clarification", evidence_strength=.9)
        if any(term in lowered for term in ("understand", "makes sense", "got it", "because")):
            return SentimentResult(sentiment="positive", confidence=.78, confusion_probability=.08, misconception="", question_type="none", evidence_strength=.75)
        tentative = any(term in lowered for term in ("maybe", "i think", "is it", "would it", "opposite"))
        return SentimentResult(sentiment="confused" if tentative else "neutral", confidence=.65 if tentative else .72, confusion_probability=.58 if tentative else .15, misconception="", question_type="verification" if tentative else "none", evidence_strength=.6)

    def generate_nudge(self, concept: str, evidence: dict) -> NudgeResult:
        frames = {
            "fractions": "Draw equal-sized fraction bars for 1/4 and 1/8, then ask students what happens to piece size as the denominator grows.",
            "photosynthesis": "Trace a carbon atom from CO₂ into glucose with an input-output diagram; distinguish soil minerals from plant-made food.",
            "forces": "Use a low-friction puck and force arrows to separate constant velocity from acceleration.",
        }
        reason = f"{evidence.get('confused_lines', 0)} confused-language lines, {evidence.get('poll_misses', 0)} poll misses, and {evidence.get('average_latency_seconds', 0)}s average latency."
        return NudgeResult(concept=concept, trigger_reason=reason, suggested_reframing=frames.get(concept, f"Ask students to represent {concept} in a different way and explain what changed."))


def build_provider() -> StructuredProvider:
    requested = os.getenv("CLASSPULSE_LLM_MODE", "auto").lower()
    if requested == "openai" or (requested == "auto" and os.getenv("OPENAI_API_KEY")):
        return OpenAIStructuredProvider()
    return DemoStructuredProvider()
