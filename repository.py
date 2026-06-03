import asyncio
import logging
from typing import List
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import Base, EventRecord
from app.schemas.event import StoreEvent

logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

class EventRepository:
    """
    Handles efficient bulk insertion of events to support 100,000+ events 
    without blocking the event loop or CV pipelines.
    """
    def __init__(self, batch_size: int = 500, flush_interval: float = 2.0):
        self._buffer: List[StoreEvent] = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._lock = asyncio.Lock()
        self._flush_task = asyncio.create_task(self._auto_flush())

    async def add(self, event: StoreEvent):
        """Add event to memory buffer"""
        async with self._lock:
            self._buffer.append(event)
            
        if len(self._buffer) >= self.batch_size:
            await self.flush()

    async def _auto_flush(self):
        """Background task that flushes events periodically even if batch_size is not reached"""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()

    async def flush(self):
        """Perform bulk insert to database using a separate thread (to avoid blocking async loop)"""
        async with self._lock:
            if not self._buffer:
                return
            
            # Extract to local variable and clear buffer
            events_to_insert = self._buffer[:]
            self._buffer.clear()
            
        # Perform DB insert in an executor to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._sync_bulk_insert, events_to_insert)

    def _sync_bulk_insert(self, events: List[StoreEvent]):
        """Synchronous SQLAlchemy bulk insert"""
        db: Session = SessionLocal()
        try:
            records = [
                EventRecord(
                    event_id=str(e.event_id),
                    visitor_id=e.visitor_id,
                    event_type=e.event_type.value,
                    timestamp=e.timestamp,
                    camera_id=e.camera_id,
                    camera_type=e.camera_type.value,
                    confidence=e.confidence,
                    metadata_blob=e.metadata
                ) for e in events
            ]
            db.bulk_save_objects(records)
            db.commit()
            logger.info(f"Bulk inserted {len(records)} events into database.")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to bulk insert events: {e}")
        finally:
            db.close()

# Global repository instance
event_repository = EventRepository()
