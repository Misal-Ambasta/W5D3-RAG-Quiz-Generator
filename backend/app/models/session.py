from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class SessionCreate(BaseModel):
    """Model for creating a new quiz session"""
    document_id: Optional[int] = None
    topic: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Response model for session information"""
    session_id: str
    created_at: datetime
    expires_at: datetime
    status: str
    document_id: Optional[int] = None
    topic: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    """Model for updating session information"""
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class QuizSessionResponse(BaseModel):
    """Response model for a quiz session with quiz data"""
    session_id: str
    quiz_id: int
    quiz_title: str
    difficulty_level: str
    total_questions: int
    created_at: datetime
    status: str
    questions: List[Dict[str, Any]]