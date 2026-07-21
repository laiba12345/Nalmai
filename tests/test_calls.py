import asyncio
import pytest

from app.calls import CallRoomRegistry, RoomFullError
from fastapi.testclient import TestClient
from app.main import app


class FakeSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, payload):
        self.messages.append(payload)


def test_room_allows_exactly_two_participants_and_relays_signals():
    async def exercise():
        registry = CallRoomRegistry(max_participants=2)
        teacher, student, third = FakeSocket(), FakeSocket(), FakeSocket()
        await registry.join("demo-123", "teacher", teacher)
        await registry.join("demo-123", "student", student)
        with pytest.raises(RoomFullError):
            await registry.join("demo-123", "observer", third)
        await registry.relay("demo-123", "teacher", {"type": "offer", "sdp": "example"})
        assert student.messages[-1] == {"type": "offer", "sdp": "example", "from": "teacher"}
        assert teacher.messages == []
    asyncio.run(exercise())


def test_disconnect_notifies_peer_and_removes_empty_room():
    async def exercise():
        registry = CallRoomRegistry(max_participants=2)
        teacher, student = FakeSocket(), FakeSocket()
        await registry.join("demo-123", "teacher", teacher)
        await registry.join("demo-123", "student", student)
        await registry.leave("demo-123", "student")
        assert teacher.messages[-1] == {"type": "peer_left", "participant_id": "student"}
        await registry.leave("demo-123", "teacher")
        assert "demo-123" not in registry.rooms
    asyncio.run(exercise())


def test_duplicate_participant_id_is_rejected():
    async def exercise():
        registry = CallRoomRegistry(max_participants=2)
        await registry.join("demo-123", "teacher", FakeSocket())
        with pytest.raises(ValueError):
            await registry.join("demo-123", "teacher", FakeSocket())
    asyncio.run(exercise())


def test_websocket_signaling_relays_between_teacher_and_student():
    client = TestClient(app)
    with client.websocket_connect("/ws/calls/test-room/teacher-one") as teacher:
        assert teacher.receive_json()["capacity"] == 2
        with client.websocket_connect("/ws/calls/test-room/student-one") as student:
            assert student.receive_json()["peers"] == ["teacher-one"]
            student.send_json({"type": "ready"})
            assert teacher.receive_json() == {"type": "ready", "from": "student-one"}
