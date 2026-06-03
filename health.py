from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import EventRecord
from app.schemas.analytics import HealthResponse
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    warnings = []
    
    # Check last event timestamp
    last_event = db.query(EventRecord).order_by(EventRecord.timestamp.desc()).first()
    
    if last_event:
        time_diff = datetime.utcnow() - last_event.timestamp
        if time_diff > timedelta(minutes=5):
            warnings.append(f"Stale feed warning: No events received for {time_diff.total_seconds() / 60:.1f} minutes.")
            
    return HealthResponse(
        status="OK",
        last_event_timestamp=last_event.timestamp if last_event else None,
        stale_feed_warnings=warnings
    )
