"""Speaker-aware transcription for repeated live classroom audio chunks."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DiarizedSegment:
    speaker: str
    text: str
    start: float
    end: float

    def as_dict(self) -> dict:
        return self.__dict__


class OpenAIDiarizedTranscriber:
    model = "gpt-4o-transcribe-diarize"

    def __init__(self, client=None):
        if client is None:
            from openai import OpenAI
            client = OpenAI()
        self.client = client

    def transcribe(self, audio: bytes, filename: str = "classroom.webm") -> list[DiarizedSegment]:
        file = io.BytesIO(audio)
        file.name = filename
        response = self.client.audio.transcriptions.create(
            model=self.model, file=file, response_format="diarized_json", chunking_strategy="auto",
        )
        return [
            DiarizedSegment(str(segment.speaker), segment.text.strip(), float(segment.start), float(segment.end))
            for segment in response.segments if segment.text.strip()
        ]


def build_transcriber() -> OpenAIDiarizedTranscriber | None:
    return OpenAIDiarizedTranscriber() if os.getenv("OPENAI_API_KEY") else None
