"""Smoke-test the deployed two-person signaling endpoint against real Uvicorn."""

from __future__ import annotations

import argparse
import asyncio
import json

from websockets.asyncio.client import connect


async def smoke(base_url: str) -> dict:
    room = "smoke-room"
    async with connect(f"{base_url}/{room}/teacher-smoke") as teacher:
        teacher_joined = json.loads(await teacher.recv())
        async with connect(f"{base_url}/{room}/student-smoke") as student:
            student_joined = json.loads(await student.recv())
            await student.send(json.dumps({"type": "ready"}))
            relayed = json.loads(await teacher.recv())
            await student.send(json.dumps({"type": "app_event", "payload": {"kind": "poll_response", "selected_index": 1}}))
            app_relay = json.loads(await teacher.recv())
            async with connect(f"{base_url}/{room}/third-smoke") as third:
                rejected = json.loads(await third.recv())
            assert teacher_joined["capacity"] == 2
            assert student_joined["peers"] == ["teacher-smoke"]
            assert relayed == {"type": "ready", "from": "student-smoke"}
            assert app_relay == {"type": "app_event", "payload": {"kind": "poll_response", "selected_index": 1}, "from": "student-smoke"}
            assert rejected["type"] == "error" and "two participants" in rejected["message"]
            return {"teacher": "joined", "student": "joined", "signaling_relay": "passed", "poll_response_relay": "passed", "third_participant": "rejected"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="ws://127.0.0.1:8000/ws/calls")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(smoke(args.url)), indent=2))


if __name__ == "__main__":
    main()
