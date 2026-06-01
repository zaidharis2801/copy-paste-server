import asyncio
import json
from typing import List


class EventBroadcaster:
    def __init__(self) -> None:
        self._queues: List[asyncio.Queue] = []

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        try:
            self._queues.remove(q)
        except ValueError:
            pass

    async def broadcast(self, event_type: str, data: dict) -> None:
        msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        stale: List[asyncio.Queue] = []
        for q in self._queues:
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                stale.append(q)
        for q in stale:
            self.unsubscribe(q)


broadcaster = EventBroadcaster()
