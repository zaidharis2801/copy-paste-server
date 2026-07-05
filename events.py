import asyncio
import json
from typing import Dict, List


class EventBroadcaster:
    """Per-user SSE queues so events only reach the owning account."""

    def __init__(self) -> None:
        self._queues: Dict[int, List[asyncio.Queue]] = {}

    async def subscribe(self, user_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.setdefault(user_id, []).append(q)
        return q

    def unsubscribe(self, user_id: int, q: asyncio.Queue) -> None:
        queues = self._queues.get(user_id, [])
        try:
            queues.remove(q)
        except ValueError:
            pass
        if not queues:
            self._queues.pop(user_id, None)

    async def broadcast(self, user_id: int, event_type: str, data: dict) -> None:
        msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        stale: List[asyncio.Queue] = []
        for q in self._queues.get(user_id, []):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                stale.append(q)
        for q in stale:
            self.unsubscribe(user_id, q)


broadcaster = EventBroadcaster()
