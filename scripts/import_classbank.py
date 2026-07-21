"""Import registered ClassBank CHAT downloads into the Nalmai catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.classbank import import_chat_lesson, parse_chat
from app.stream import CLASSBANK_DATA_DIR

MEDIA_EXTENSIONS = (".mp4", ".mov", ".m4v", ".wav", ".mp3", ".webm")


def find_media(chat_path: Path, media_dir: Path | None) -> Path | None:
    lesson = parse_chat(chat_path)
    if not media_dir or not lesson.media_name:
        return None
    for extension in MEDIA_EXTENSIONS:
        candidate = media_dir / f"{lesson.media_name}{extension}"
        if candidate.exists():
            return candidate
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Import time-aligned ClassBank CHAT lessons into Nalmai.")
    parser.add_argument("inputs", nargs="+", type=Path, help="CHAT .cha files or directories containing them")
    parser.add_argument("--concept", required=True, help="Concept label used by CCS/BKT, e.g. fractions")
    parser.add_argument("--media-dir", type=Path, help="Directory containing matching ClassBank media files")
    parser.add_argument("--output-dir", type=Path, default=CLASSBANK_DATA_DIR)
    args = parser.parse_args()
    chat_files = []
    for item in args.inputs:
        chat_files.extend(sorted(item.rglob("*.cha")) if item.is_dir() else [item])
    if not chat_files:
        parser.error("No .cha files found")
    print("ClassBank data remains subject to TalkBank Ground Rules and corpus citation requirements.")
    for chat_path in chat_files:
        media = find_media(chat_path, args.media_dir)
        output = import_chat_lesson(chat_path, args.output_dir, concept=args.concept, media_path=media)
        media_status = str(media) if media else "not linked (transcript replay still available)"
        print(f"Imported {chat_path.name} -> {output.name}; media: {media_status}")
    print(f"Imported {len(chat_files)} lesson(s). Restart Nalmai to see them in the lesson selector.")


if __name__ == "__main__":
    main()
