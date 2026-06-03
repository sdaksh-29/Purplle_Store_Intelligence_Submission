from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import List
from app.schemas.event import StoreEvent
from app.schemas.analytics import IngestResponse
from app.core.bus import event_bus
from app.services.event_validator import validator

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(events: List[StoreEvent], background_tasks: BackgroundTasks):
    """
    Batch Ingestion Endpoint for Store Events.
    - Max 500 events per request.
    - Idempotent: Deduplicates events based on signature and time window.
    - Partial Success: Valid events are accepted, invalid/duplicates are rejected.
    """
    if len(events) > 500:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Batch size exceeds maximum of 500 events."
        )

    accepted = 0
    rejected = 0
    errors = []

    for event in events:
        # Pydantic has already validated the schema.
        # Now we validate business logic / idempotency using the validator.
        if validator.process(event):
            # Publish to the Event Bus asynchronously (fire-and-forget approach for max throughput)
            background_tasks.add_task(event_bus.publish, "store_events", event)
            accepted += 1
        else:
            rejected += 1
            errors.append(f"Event {event.event_id} rejected: Duplicate or invalid within window.")

    return IngestResponse(
        accepted=accepted,
        rejected=rejected,
        errors=errors
    )
