from sqlalchemy import Column, String, Float, DateTime, JSON
from app.db.database import Base
from datetime import datetime
import uuid

class EventRecord(Base):
    """
    SQLAlchemy Model for storing StoreEvents efficiently.
    Indexed properly to support querying large datasets (100k+ rows).
    """
    __tablename__ = "store_events"

    # Store UUIDs as strings for cross-DB compatibility (SQLite doesn't have native UUID)
    event_id = Column(String(36), primary_key=True, index=True)
    visitor_id = Column(String(36), index=True, nullable=False)
    event_type = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    camera_id = Column(String(50), index=True, nullable=False)
    camera_type = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Store dynamic metadata as JSON (SQLite, PG natively support this)
    metadata_blob = Column(JSON, nullable=True)
