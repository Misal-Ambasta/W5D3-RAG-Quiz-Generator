from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class QuizGenerationRequest(BaseModel):
    """Request model for generating a quiz"""
    topic: str
    question_count: int = 5
    difficulty: str = "medium"
    document_id: Optional[int] = None
    session_id: Optional[str] = None


class QuizResponse(BaseModel):
    """Response model for a generated quiz"""
    quiz_data: Dict[str, Any]
    cached: bool
    session_id: str


class AnswerSubmission(BaseModel):
    """Model for submitting an answer to a quiz question"""
    session_id: str
    question_id: int
    user_answer: str
    response_time_seconds: Optional[int] = None


class AnswerResponse(BaseModel):
    """Response model for an answer submission"""
    question_id: int
    is_correct: bool
    correct_answer: str
    explanation: Optional[str] = None
    feedback: Optional[str] = None


class QuizResultsRequest(BaseModel):
    """Request model for getting quiz results"""
    session_id: str


class QuizResultsResponse(BaseModel):
    """Response model for quiz results"""
    session_id: str
    quiz_title: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    completion_time: Optional[int] = None
    questions: List[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime] = None