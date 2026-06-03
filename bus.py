import asyncio
import json
import logging
from typing import Callable, Awaitable, List
from app.schemas.event import StoreEvent

logger = logging.getLogger(__name__)

class EventBus:
    """
    Abstract Event Bus for publishing and consuming events.
    In a full production environment, this maps to Kafka or Redis Streams.
    For this implementation, we use an asyncio.Queue to remain lightweight 
    while supporting the exact same pub/sub async patterns.
    """
    def __init__(self):
        # We simulate a topic-based queue system
        self._queues = {}
        self._subscribers = {}

    def _get_queue(self, topic: str) -> asyncio.Queue:
        if topic not in self._queues:
            self._queues[topic] = asyncio.Queue(maxsize=100000) # Support 100k+ events
        return self._queues[topic]

    async def publish(self, topic: str, event: StoreEvent):
        """
        Publish an event to a topic.
        """
        queue = self._get_queue(topic)
        try:
            await queue.put(event)
            logger.debug(f"Published event {event.event_id} to {topic}")
        except asyncio.QueueFull:
            logger.error(f"Event bus queue for {topic} is full!")

    async def subscribe(self, topic: str, callback: Callable[[StoreEvent], Awaitable[None]]):
        """
        Subscribe to a topic and process events via the callback.
        Runs as a background task.
        """
        queue = self._get_queue(topic)
        if topic not in self._subscribers:
            self._subscribers[topic] = []
            
        async def worker():
            while True:
                event = await queue.get()
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error processing event {event.event_id}: {e}")
                finally:
                    queue.task_done()

        task = asyncio.create_task(worker())
        self._subscribers[topic].append(task)
        logger.info(f"Subscribed to topic {topic}")

# Global instance
event_bus = EventBus()
