import asyncio
import json
from collections import defaultdict
from datetime import datetime

from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._state: dict[str, str] = {}

    async def publish(self, channel: str, data: dict) -> None:
        payload = json.dumps(data)
        for queue in self._subscribers.get(channel, []):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, channel: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers[channel].append(queue)
        return queue

    def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        if channel in self._subscribers and queue in self._subscribers[channel]:
            self._subscribers[channel].remove(queue)

    async def publish_telemetry(self, chat_id: int, user_id: int, lat: float, lon: float) -> None:
        await self.publish("race_tracking", {
            "chat_id": chat_id,
            "user_id": user_id,
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def publish_event(self, event_type: str, data: dict) -> None:
        await self.publish("race_events", {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        })

    def set_race_state(self, key: str, value: str) -> None:
        self._state[f"race:{key}"] = value

    def get_race_state(self, key: str) -> str | None:
        return self._state.get(f"race:{key}")


bus = EventBus()
