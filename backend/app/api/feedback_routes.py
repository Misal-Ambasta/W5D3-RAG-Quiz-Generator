"""Feedback API Routes

Implements Phase 16 - Feedback Collection
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.dependencies import get_database_manager
from app.core.database import DatabaseManager
from services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])

# Global service instance
_feedback_service: Optional[FeedbackService] = None

def get_feedback_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> FeedbackService:
    """Dependency to get feedback service instance"""
    global _feedback_service
    
    if _feedback_service is None:
        _feedback_service = FeedbackService(db_manager=db_manager)
    
    return _feedback_service

# Pydantic models for request validation
class QuizFeedbackRequest(BaseModel):
    """Quiz feedback request model"""
    session_id: str
    quiz_id: int
    rating: int = Field(..., ge=1, le=5, description="Overall rating (1-5)")
    comments: Optional[str] = None
    improvement_suggestions: Optional[str] = None
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5, description="Difficulty rating (1-5)")
    relevance_rating: Optional[int] = Field(None, ge=1, le=5, description="Relevance rating (1-5)")
    ui_rating: Optional[int] = Field(None, ge=1, le=5, description="UI/UX rating (1-5)")
    tags: Optional[List[str]] = None

class QuestionFeedbackRequest(BaseModel):
    """Question feedback request model"""
    session_id: str
    question_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    comments: Optional[str] = None
    is_confusing: Optional[bool] = None
    is_irrelevant: Optional[bool] = None
    has_errors: Optional[bool] = None

# Feedback endpoints
@router.post("/quiz")
async def submit_quiz_feedback(
    feedback: QuizFeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Submit feedback for a quiz"""
    try:
        result = feedback_service.submit_quiz_feedback(
            session_id=feedback.session_id,
            quiz_id=feedback.quiz_id,
            rating=feedback.rating,
            comments=feedback.comments,
            improvement_suggestions=feedback.improvement_suggestions,
            difficulty_rating=feedback.difficulty_rating,
            relevance_rating=feedback.relevance_rating,
            ui_rating=feedback.ui_rating,
            tags=feedback.tags
        )
        
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to submit feedback'))
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz feedback: {str(e)}")

@router.post("/question")
async def submit_question_feedback(
    feedback: QuestionFeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Submit feedback for a specific question"""
    try:
        result = feedback_service.submit_question_feedback(
            session_id=feedback.session_id,
            question_id=feedback.question_id,
            rating=feedback.rating,
            comments=feedback.comments,
            is_confusing=feedback.is_confusing,
            is_irrelevant=feedback.is_irrelevant,
            has_errors=feedback.has_errors
        )
        
        if not result.get('success', False):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to submit feedback'))
        
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit question feedback: {str(e)}")

@router.get("/quiz/{quiz_id}")
async def get_quiz_feedback(
    quiz_id: int,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get all feedback for a specific quiz"""
    try:
        feedback = feedback_service.get_quiz_feedback(quiz_id)
        return {"quiz_id": quiz_id, "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz feedback: {str(e)}")

@router.get("/question/{question_id}")
async def get_question_feedback(
    question_id: int,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get all feedback for a specific question"""
    try:
        feedback = feedback_service.get_question_feedback(question_id)
        return {"question_id": question_id, "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get question feedback: {str(e)}")

@router.get("/summary")
async def get_feedback_summary(
    quiz_id: Optional[int] = None,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get a summary of feedback"""
    try:
        summary = feedback_service.get_feedback_summary(quiz_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get feedback summary: {str(e)}")