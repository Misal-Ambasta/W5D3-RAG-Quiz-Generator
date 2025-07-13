"""Analytics API Routes

Implements Phase 15 - Quiz Analytics
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.dependencies import get_database_manager
from core.database import DatabaseManager
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Global service instance
_analytics_service: Optional[AnalyticsService] = None

def get_analytics_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> AnalyticsService:
    """Dependency to get analytics service instance"""
    global _analytics_service
    
    if _analytics_service is None:
        _analytics_service = AnalyticsService(db_manager=db_manager)
    
    return _analytics_service

@router.get("/quiz/{quiz_id}")
async def get_quiz_analytics(
    quiz_id: int,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a specific quiz
    
    Args:
        quiz_id: ID of the quiz
    
    Returns:
        Quiz performance metrics
    """
    try:
        metrics = analytics_service.get_quiz_performance_metrics(quiz_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Quiz {quiz_id} not found or has no analytics data")
        
        return metrics
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz analytics: {str(e)}")

@router.get("/session/{session_id}")
async def get_session_analytics(
    session_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a specific user session
    
    Args:
        session_id: ID of the session
    
    Returns:
        Session analytics data
    """
    try:
        metrics = analytics_service.get_user_session_analytics(session_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or has no analytics data")
        
        return metrics
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session analytics: {str(e)}")

@router.get("/aggregate")
async def get_aggregate_analytics(
    time_period: str = Query('week', description="Time period for analytics: 'day', 'week', 'month', or 'all'"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get aggregate analytics across all quizzes
    
    Args:
        time_period: Time period for analytics ('day', 'week', 'month', 'all')
    
    Returns:
        Aggregate analytics data
    """
    try:
        # Validate time period
        valid_periods = ['day', 'week', 'month', 'all']
        if time_period not in valid_periods:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid time period. Must be one of: {', '.join(valid_periods)}"
            )
        
        metrics = analytics_service.get_aggregate_analytics(time_period)
        
        return metrics
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get aggregate analytics: {str(e)}")