"""In-memory signaling rooms for a two-person WebRTC demonstration call."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Protocol


class SignalSocket(Protocol):
    async def send_json(self, payload: dict) -> None: ...


class RoomFullError(RuntimeError):
    pass


class CallRoomRegistry:
    def __init__(self, max_participants: int = 2):
        self.max_participants = max_participants
        self.rooms: dict[str, dict[str, SignalSocket]] = defaultdict(dict)
        self._lock = asyncio.Lock()

    async def join(self, room_id: str, participant_id: str, socket: SignalSocket) -> list[str]:
        async with self._lock:
            room = self.rooms[room_id]
            if participant_id in room:
                raise ValueError("participant ID is already in this room")
            if len(room) >= self.max_participants:
                if not room:
                    self.rooms.pop(room_id, None)
                raise RoomFullError("this demo call already has two participants")
            peers = list(room)
            room[participant_id] = socket
            return peers

    async def relay(self, room_id: str, sender_id: str, payload: dict) -> None:
        message = {**payload, "from": sender_id}
        peers = [socket for participant, socket in self.rooms.get(room_id, {}).items() if participant != sender_id]
        for socket in peers:
            await socket.send_json(message)

    async def leave(self, room_id: str, participant_id: str) -> None:
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return
            room.pop(participant_id, None)
            peers = list(room.values())
            if not room:
                self.rooms.pop(room_id, None)
        for socket in peers:
            await socket.send_json({"type": "peer_left", "participant_id": participant_id})
