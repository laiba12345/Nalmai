"""Import time-aligned TalkBank CHAT classroom transcripts into Nalmai."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

TIME_MARK = re.compile(r"\x15(\d+)_(\d+)\x15")
ANNOTATION = re.compile(r"\s*\[(?:=!|=|\?|/|//|\*)[^\]]*\]")


@dataclass(frozen=True)
class ChatTurn:
    speaker: str
    text: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True)
class ChatLesson:
    participants: dict[str, dict[str, str]]
    turns: tuple[ChatTurn, ...]
    media_name: str | None
    media_type: str | None


def _clean_text(value: str) -> str:
    value = TIME_MARK.sub("", value)
    value = ANNOTATION.sub("", value)
    value = value.replace("\t", " ").replace("  ", " ")
    return value.strip()


def parse_chat(path: Path) -> ChatLesson:
    text = path.read_text(encoding="utf-8-sig")
    participants: dict[str, dict[str, str]] = {}
    media_name = media_type = None
    logical_lines: list[str] = []
    for raw in text.splitlines():
        if raw.startswith(("\t", " ")) and logical_lines and logical_lines[-1].startswith("*"):
            logical_lines[-1] += " " + raw.strip()
        else:
            logical_lines.append(raw)
    turns: list[ChatTurn] = []
    for line in logical_lines:
        if line.startswith("@Participants:"):
            for entry in line.split(":", 1)[1].strip().split(","):
                pieces = entry.strip().split()
                if len(pieces) >= 3:
                    participants[pieces[0]] = {"name": " ".join(pieces[1:-1]), "role": pieces[-1]}
        elif line.startswith("@Media:"):
            media = [part.strip() for part in line.split(":", 1)[1].split(",")]
            media_name = media[0] if media else None
            media_type = media[1] if len(media) > 1 else None
        elif line.startswith("*") and ":" in line:
            speaker, utterance = line[1:].split(":", 1)
            timing = TIME_MARK.search(utterance)
            if timing:
                turns.append(ChatTurn(speaker.strip(), _clean_text(utterance), int(timing.group(1)), int(timing.group(2))))
    if not turns:
        raise ValueError(f"No time-aligned utterances found in {path}")
    return ChatLesson(participants, tuple(turns), media_name, media_type)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def import_chat_lesson(chat_path: Path, output_dir: Path, *, concept: str, media_path: Path | None = None) -> Path:
    lesson = parse_chat(chat_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    student_codes = [code for code, details in lesson.participants.items() if details["role"].lower() != "teacher"]
    student_names = [lesson.participants[code]["name"] for code in student_codes]
    display_names = {
        code: (code if name.lower() in {"student", "pupil", "child"} or student_names.count(name) > 1 else name)
        for code, name in zip(student_codes, student_names)
    }
    students = [display_names[code] for code in student_codes]
    events = []
    for turn in lesson.turns:
        participant = lesson.participants.get(turn.speaker, {"name": turn.speaker, "role": "Student"})
        is_teacher = participant["role"].lower() == "teacher"
        speaker_name = participant["name"] if is_teacher else display_names.get(turn.speaker, participant["name"])
        event = {
            "at": round(turn.start_ms / 1000, 3), "end_at": round(turn.end_ms / 1000, 3),
            "type": "teacher" if is_teacher else "chat", "speaker": speaker_name,
            "text": turn.text, "recorded_timing": True,
        }
        if not is_teacher:
            event["latency_seconds"] = 0
        events.append(event)
    lesson_id = f"classbank-{_slug(chat_path.stem)}"
    payload = {
        "id": lesson_id, "title": f"ClassBank: {chat_path.stem}", "concept": concept,
        "students": students, "events": events, "source_type": "classbank",
        "source": {
            "dataset": "ClassBank", "corpus": "TIMSS-Math", "chat_file": chat_path.name,
            "media_name": lesson.media_name, "media_type": lesson.media_type,
            "media_path": str(media_path.resolve()) if media_path else None,
            "citation": "Stigler, Gallimore, and Hiebert (2000)",
            "access": "https://talkbank.org/class/access/TIMSS-Math/TIMSS-Math.html",
            "notice": "Use is subject to TalkBank Ground Rules and corpus citation requirements.",
        },
    }
    output = output_dir / f"{lesson_id.replace('-', '_')}.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output
