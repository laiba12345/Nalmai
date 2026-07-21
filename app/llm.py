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
    "properties": {"concept": {"type": "string"}, "trigger_reason": {"type": "string"}, "suggested_reframing": {"type": "string"}, "strategy": {"type": "string", "enum": ["visual_model", "worked_example", "contrast_case", "analogy", "student_explanation"]}, "selection_mode": {"type": "string", "enum": ["exploration", "evidence_informed"]}, "strategy_selection_reason": {"type": "string"}},
    "required": ["concept", "trigger_reason", "suggested_reframing", "strategy", "selection_mode", "strategy_selection_reason"],
}
EXPLANATION_RISK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "concept": {"type": "string"},
        "factual_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "clarity_risk": {"type": "number", "minimum": 0, "maximum": 1},
        "possible_issue": {"type": "string"}, "evidence": {"type": "string"},
        "suggested_check": {"type": "string"},
    },
    "required": ["concept", "factual_risk", "clarity_risk", "possible_issue", "evidence", "suggested_check"],
}
IMPLEMENTATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "status": {"type": "string", "enum": ["implemented", "partially_implemented", "not_implemented", "uncertain"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_quote": {"type": "string"},
        "rationale": {"type": "string"},
    },
    "required": ["status", "confidence", "evidence_quote", "rationale"],
}
FOLLOWUP_POLL_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "concept": {"type": "string"}, "question": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 3},
        "correct_index": {"type": "integer", "minimum": 0, "maximum": 2},
        "explanation": {"type": "string"}, "checks": {"type": "string"},
    },
    "required": ["concept", "question", "options", "correct_index", "explanation", "checks"],
}
MEMORY_INSIGHT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"}, "recurring_need": {"type": "string"},
        "recommended_strategy": {"type": "string", "enum": ["visual_model", "worked_example", "contrast_case", "analogy", "student_explanation"]},
        "rationale": {"type": "string"}, "limitations": {"type": "string"},
    },
    "required": ["summary", "recurring_need", "recommended_strategy", "rationale", "limitations"],
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
    strategy: Literal["visual_model", "worked_example", "contrast_case", "analogy", "student_explanation"]
    selection_mode: Literal["exploration", "evidence_informed"]
    strategy_selection_reason: str


class ExplanationRiskResult(BaseModel):
    concept: str
    factual_risk: float = Field(ge=0, le=1)
    clarity_risk: float = Field(ge=0, le=1)
    possible_issue: str
    evidence: str
    suggested_check: str


class ImplementationVerificationResult(BaseModel):
    status: Literal["implemented", "partially_implemented", "not_implemented", "uncertain"]
    confidence: float = Field(ge=0, le=1)
    evidence_quote: str
    rationale: str


class FollowupPollResult(BaseModel):
    concept: str
    question: str
    options: list[str] = Field(min_length=3, max_length=3)
    correct_index: int = Field(ge=0, le=2)
    explanation: str
    checks: str


class MemoryInsightResult(BaseModel):
    summary: str
    recurring_need: str
    recommended_strategy: Literal["visual_model", "worked_example", "contrast_case", "analogy", "student_explanation"]
    rationale: str
    limitations: str


class StructuredProvider(ABC):
    mode: str
    @abstractmethod
    def classify_sentiment(self, text: str) -> SentimentResult: ...
    @abstractmethod
    def generate_nudge(self, concept: str, evidence: dict, strategy: str = "visual_model", selection_mode: str = "exploration", strategy_selection_reason: str = "Neutral exploration.") -> NudgeResult: ...
    @abstractmethod
    def analyze_explanation(self, concept: str, text: str) -> ExplanationRiskResult: ...
    @abstractmethod
    def verify_nudge_implementation(self, concept: str, suggestion: str, strategy: str, teacher_text: str) -> ImplementationVerificationResult: ...
    @abstractmethod
    def generate_followup_poll(self, concept: str, suggestion: str, teacher_text: str, stage: str = "followup") -> FollowupPollResult: ...
    @abstractmethod
    def synthesize_memory(self, concept: str, context: dict) -> MemoryInsightResult: ...


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

    def generate_nudge(self, concept: str, evidence: dict, strategy: str = "visual_model", selection_mode: str = "exploration", strategy_selection_reason: str = "Neutral exploration.") -> NudgeResult:
        prompt = f"Concept: {concept}\nRequired intervention strategy: {strategy}\nSelection mode: {selection_mode}\nSelection reason: {strategy_selection_reason}\nObserved signals: {json.dumps(evidence)}\nDraft one short, concrete strategy-specific re-explanation. Preserve the supplied strategy metadata exactly. Cite signal counts; do not diagnose students."
        payload = self._request("You are a real-time teacher copilot. Return only the strict schema.", prompt, "teacher_nudge", NUDGE_SCHEMA)
        return NudgeResult.model_validate(payload)

    def analyze_explanation(self, concept: str, text: str) -> ExplanationRiskResult:
        prompt = f"Concept: {concept}\nTeacher utterance: {text}\nIdentify only plausible factual or clarity risks. Do not declare the teacher wrong when context is insufficient."
        payload = self._request("You are a cautious instructional-quality reviewer. Return the strict schema.", prompt, "teacher_explanation_risk", EXPLANATION_RISK_SCHEMA)
        return ExplanationRiskResult.model_validate(payload)

    def verify_nudge_implementation(self, concept: str, suggestion: str, strategy: str, teacher_text: str) -> ImplementationVerificationResult:
        prompt = f"Concept: {concept}\nRecommended strategy: {strategy}\nSuggested teaching move: {suggestion}\nSubsequent teacher speech: {teacher_text}"
        instructions = "Determine whether the subsequent teacher speech demonstrates the suggested teaching move. Require observable strategy evidence; wording need not match. Do not infer implementation from intent or topic overlap. Quote only supplied teacher speech. Return the strict schema."
        payload = self._request(instructions, prompt, "nudge_implementation_verification", IMPLEMENTATION_SCHEMA)
        return ImplementationVerificationResult.model_validate(payload)

    def generate_followup_poll(self, concept: str, suggestion: str, teacher_text: str, stage: str = "followup") -> FollowupPollResult:
        purpose = "baseline misconception check before the re-teach" if stage == "baseline" else "transfer check after the implemented re-teach"
        prompt = f"Concept: {concept}\nTeaching move: {suggestion}\nAvailable classroom language: {teacher_text}\nCreate one short three-option {purpose}. It must have exactly one correct answer and avoid trick questions."
        payload = self._request("You create fair, age-appropriate formative assessment checks. Return the strict schema.", prompt, "followup_learning_check", FOLLOWUP_POLL_SCHEMA)
        return FollowupPollResult.model_validate(payload)

    def synthesize_memory(self, concept: str, context: dict) -> MemoryInsightResult:
        prompt = f"Concept: {concept}\nPseudonymous prior-session evidence: {json.dumps(context)}"
        payload = self._request("Summarize only supplied longitudinal evidence for a teacher copilot. Prefer strategies with observed implementation and improvement, but never claim causality. Return the strict schema.", prompt, "teacher_memory_insight", MEMORY_INSIGHT_SCHEMA)
        return MemoryInsightResult.model_validate(payload)


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

    def generate_nudge(self, concept: str, evidence: dict, strategy: str = "visual_model", selection_mode: str = "exploration", strategy_selection_reason: str = "Neutral exploration.") -> NudgeResult:
        frames = {
            "fractions": "Draw equal-sized fraction bars for 1/4 and 1/8, then ask students what happens to piece size as the denominator grows.",
            "photosynthesis": "Trace a carbon atom from CO₂ into glucose with an input-output diagram; distinguish soil minerals from plant-made food.",
            "forces": "Use a low-friction puck and force arrows to separate constant velocity from acceleration.",
        }
        if evidence.get("trigger_source") == "explanation_risk":
            reason = f"Teacher explanation risk was elevated: {evidence.get('possible_issue', 'the explanation may need clarification')}"
        else:
            reason = f"{evidence.get('confused_lines', 0)} confused-language lines, {evidence.get('poll_misses', 0)} poll misses, and {evidence.get('average_latency_seconds', 0)}s average latency."
        return NudgeResult(concept=concept, trigger_reason=reason, suggested_reframing=frames.get(concept, f"Ask students to represent {concept} in a different way and explain what changed."), strategy=strategy, selection_mode=selection_mode, strategy_selection_reason=strategy_selection_reason)

    def analyze_explanation(self, concept: str, text: str) -> ExplanationRiskResult:
        lowered = text.lower()
        rule_only = any(term in lowered for term in ("always", "just remember", "rule"))
        return ExplanationRiskResult(
            concept=concept, factual_risk=.12, clarity_risk=.68 if rule_only else .22,
            possible_issue="A rule may be stated without enough conceptual support." if rule_only else "No specific issue detected from this isolated utterance.",
            evidence=text[:240], suggested_check="Ask a student to explain why the representation supports the rule." if rule_only else "Check understanding with a short student explanation.",
        )

    def verify_nudge_implementation(self, concept: str, suggestion: str, strategy: str, teacher_text: str) -> ImplementationVerificationResult:
        lowered = teacher_text.lower()
        strategy_terms = {
            "visual_model": ("draw", "diagram", "bar", "model", "number line", "arrow"),
            "worked_example": ("step", "example", "first", "then"),
            "contrast_case": ("compare", "contrast", "instead", "difference"),
            "analogy": ("like", "imagine", "similar"),
            "student_explanation": ("explain", "tell me why", "your reasoning", "in your own words"),
        }
        matches = [term for term in strategy_terms.get(strategy, ()) if term in lowered]
        implemented = bool(matches)
        return ImplementationVerificationResult(
            status="implemented" if implemented else "not_implemented",
            confidence=.9 if implemented else .76,
            evidence_quote=teacher_text[:240] if implemented else "",
            rationale=f"Observed strategy evidence: {', '.join(matches)}." if implemented else "No observable evidence of the recommended strategy appears in this teacher segment.",
        )

    def generate_followup_poll(self, concept: str, suggestion: str, teacher_text: str, stage: str = "followup") -> FollowupPollResult:
        baseline_checks = {
            "fractions": ("Which is greater?", ["1/4", "1/8", "They are equal"], 0, "One fourth is larger than one eighth."),
            "forces": ("A puck moves at constant speed in a straight line. Is it accelerating?", ["Yes", "No", "Only if it is fast"], 1, "Constant velocity means no acceleration."),
            "photosynthesis": ("What material supplies carbon for plant sugar?", ["Soil", "Carbon dioxide", "Sunlight"], 1, "Carbon dioxide supplies the carbon."),
        }
        followup_checks = {
            "fractions": ("Which unit fraction has the largest piece?", ["1/3", "1/6", "1/9"], 0, "With the same whole, fewer equal pieces means each piece is larger."),
            "forces": ("Which situation shows acceleration?", ["A puck moving steadily", "A cart changing direction", "A book resting"], 1, "Changing direction changes velocity, so the cart accelerates."),
            "photosynthesis": ("Where does the carbon in plant sugar come from?", ["Soil minerals", "Carbon dioxide", "Sunlight"], 1, "Plants incorporate carbon from carbon dioxide into sugar."),
        }
        checks = baseline_checks if stage == "baseline" else followup_checks
        question, options, correct, explanation = checks.get(concept, (f"Which statement best applies the new explanation of {concept}?", ["The first statement", "The second statement", "The third statement"], 0, "The first statement applies the explanation."))
        return FollowupPollResult(concept=concept, question=question, options=options, correct_index=correct, explanation=explanation, checks=f"{stage.title()} conceptual check about {concept}.")

    def synthesize_memory(self, concept: str, context: dict) -> MemoryInsightResult:
        strategies = context.get("teacher", {}).get("strategies", {})
        ranked = sorted(strategies, key=lambda name: (strategies[name].get("mean_observed_delta") or -1), reverse=True)
        strategy = ranked[0] if ranked else "visual_model"
        return MemoryInsightResult(summary=f"Prior evidence for {concept} was retrieved." if context.get("available") else "No prior evidence is available yet.", recurring_need="Review the current concept evidence alongside prior mastery.", recommended_strategy=strategy, rationale="Uses stored mastery and observed strategy outcomes without treating them as causal.", limitations="Sparse, pseudonymous records may not generalize to the next lesson.")


def build_provider() -> StructuredProvider:
    requested = os.getenv("NALMAI_LLM_MODE", "auto").lower()
    if requested == "openai" or (requested == "auto" and os.getenv("OPENAI_API_KEY")):
        return OpenAIStructuredProvider()
    return DemoStructuredProvider()
