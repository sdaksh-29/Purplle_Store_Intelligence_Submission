from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.analytics import MetricsResponse, FunnelResponse, HeatmapResponse, AnomaliesResponse
from app.services.analytics import AnalyticsEngine

router = APIRouter()

@router.get("/{store_id}/metrics", response_model=MetricsResponse)
def get_metrics(store_id: str, db: Session = Depends(get_db)):
    engine = AnalyticsEngine(db)
    metrics = engine.get_metrics(store_id)
    return MetricsResponse(**metrics)

@router.get("/{store_id}/funnel", response_model=FunnelResponse)
def get_funnel(store_id: str, db: Session = Depends(get_db)):
    engine = AnalyticsEngine(db)
    steps = engine.get_funnel(store_id)
    return FunnelResponse(steps=steps)

@router.get("/{store_id}/heatmap", response_model=HeatmapResponse)
def get_heatmap(store_id: str, db: Session = Depends(get_db)):
    engine = AnalyticsEngine(db)
    zones = engine.get_heatmap(store_id)
    return HeatmapResponse(zones=zones)

@router.get("/{store_id}/anomalies", response_model=AnomaliesResponse)
def get_anomalies(store_id: str, db: Session = Depends(get_db)):
    engine = AnalyticsEngine(db)
    anomalies = engine.get_anomalies(store_id)
    return AnomaliesResponse(anomalies=anomalies)

@router.get("/{store_id}/traffic_trends")
def get_traffic_trends(store_id: str, db: Session = Depends(get_db)):
    from app.services.ai_insights import AIInsightsEngine
    engine = AIInsightsEngine(db)
    return engine.get_traffic_trends(store_id)
