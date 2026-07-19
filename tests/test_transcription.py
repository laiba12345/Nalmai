import asyncio

from app.llm import DemoStructuredProvider
from app.runtime import ClassRuntime
from app.stream import ScriptedClass
from app.transcription import DiarizedSegment, OpenAIDiarizedTranscriber


def test_openai_diarized_transcriber_uses_supported_model_and_schema():
    class Transcriptions:
        def __init__(self): self.kwargs = None
        def create(self, **kwargs):
            self.kwargs = kwargs
            return type("Transcript", (), {"segments": [type("S", (), {"speaker": "teacher", "text": "Explain equivalent fractions", "start": 0.2, "end": 2.1})()]})()
    transcriptions = Transcriptions()
    client = type("Client", (), {"audio": type("Audio", (), {"transcriptions": transcriptions})()})()
    result = OpenAIDiarizedTranscriber(client).transcribe(b"webm-bytes", "lecture.webm")
    assert transcriptions.kwargs["model"] == "gpt-4o-transcribe-diarize"
    assert transcriptions.kwargs["response_format"] == "diarized_json"
    assert transcriptions.kwargs["chunking_strategy"] == "auto"
    assert result[0].speaker == "teacher"


def test_diarized_segments_enter_the_existing_runtime_queue():
    runtime = ClassRuntime(ScriptedClass.load("fractions_live"), DemoStructuredProvider())
    event = runtime.submit_transcript_segment(
        DiarizedSegment(speaker="speaker_1", text="I do not understand the denominator", start=1.0, end=3.0),
        offset_seconds=20, teacher_speaker="speaker_0",
    )
    messages = asyncio.run(_drain_one(runtime))
    assert event["source"] == "live_audio"
    assert event["type"] == "chat"
    assert event["at"] == 21
    assert any(message["kind"] == "ccs" for message in messages)
    assert runtime.processed_sources == ["live_audio"]


async def _drain_one(runtime):
    event = runtime.event_queue.get_nowait()
    return [message async for message in runtime.process_event(event)]
