from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.insights import InsightsResponse, CustomerJourneyResponse, PerformanceRankingResponse
from app.services.ai_insights import AIInsightsEngine

router = APIRouter()

@router.get("/{store_id}/insights/comprehensive", response_model=InsightsResponse)
def get_comprehensive_insights(store_id: str, db: Session = Depends(get_db)):
    """
    Returns a bundled payload of AI Insights, Forecasts, Staff Efficiency, and Health Score.
    """
    engine = AIInsightsEngine(db)
    
    return InsightsResponse(
        health_score=engine.generate_health_score(store_id),
        forecasts=engine.generate_forecasts(store_id),
        staff_efficiency=engine.analyze_staff_efficiency(store_id),
        ai_insights=engine.generate_nlp_insights(store_id)
    )

@router.get("/{store_id}/insights/journey", response_model=CustomerJourneyResponse)
def get_customer_journey(store_id: str, db: Session = Depends(get_db)):
    """
    Returns the most common paths taken by visitors through the store.
    """
    engine = AIInsightsEngine(db)
    paths = engine.analyze_customer_journey(store_id)
    return CustomerJourneyResponse(common_paths=paths)

@router.get("/{store_id}/insights/zones", response_model=PerformanceRankingResponse)
def get_zone_rankings(store_id: str, db: Session = Depends(get_db)):
    """
    Ranks zones based on traffic and dwell time, identifying dead zones and revenue opportunities.
    """
    engine = AIInsightsEngine(db)
    rankings = engine.rank_zone_performance(store_id)
    return PerformanceRankingResponse(zones=rankings)
