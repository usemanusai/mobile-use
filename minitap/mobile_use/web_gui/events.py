import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any


class EventBroadcaster:
    def __init__(self):
        self._subscribers: set[asyncio.Queue[str]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: dict[str, Any]) -> None:
        data = f"data: {json.dumps(event)}\n\n"
        async with self._lock:
            dead: list[asyncio.Queue[str]] = []
            for q in list(self._subscribers):
                try:
                    q.put_nowait(data)
                except asyncio.QueueFull:
                    dead.append(q)
            for q in dead:
                self._subscribers.discard(q)

    async def subscribe(self) -> AsyncGenerator[bytes, None]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._subscribers.add(q)
        try:
            # Send a hello event
            await q.put('data: {"type": "hello"}\n\n')
            while True:
                data = await q.get()
                yield data.encode("utf-8")
        finally:
            async with self._lock:
                self._subscribers.discard(q)


broadcaster = EventBroadcaster()
