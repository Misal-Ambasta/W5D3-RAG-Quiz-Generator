"""Session Management API Routes

Implements Phase 13 - Session Management and Phase 14 - Answer Validation & Feedback
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, status

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.dependencies import get_database_manager, get_settings
from app.core.database import DatabaseManager
from app.core.config import Settings
from app.models.session import SessionCreate, SessionResponse, SessionUpdate, QuizSessionResponse
from app.models.quiz import AnswerSubmission, AnswerResponse, QuizResultsRequest, QuizResultsResponse
from services.session_service import SessionService
from services.answer_validation_service import AnswerValidationService

router = APIRouter(prefix="/sessions", tags=["quiz-sessions"])

# Global service instances
_session_service: Optional[SessionService] = None
_answer_validation_service: Optional[AnswerValidationService] = None

def get_session_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> SessionService:
    """Dependency to get session service instance"""
    global _session_service
    
    if _session_service is None:
        _session_service = SessionService(db_manager=db_manager)
    
    return _session_service

def get_answer_validation_service() -> AnswerValidationService:
    """Dependency to get answer validation service instance"""
    global _answer_validation_service
    
    if _answer_validation_service is None:
        _answer_validation_service = AnswerValidationService()
    
    return _answer_validation_service

# Session Management Endpoints
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    session_service: SessionService = Depends(get_session_service)
):
    """Create a new quiz session"""
    try:
        result = session_service.create_session(
            document_id=session_data.document_id,
            topic=session_data.topic,
            metadata=session_data.metadata
        )
        
        return SessionResponse(
            session_id=result['session_id'],
            created_at=result['created_at'],
            expires_at=result['expires_at'],
            status=result['status'],
            document_id=result['document_id'],
            topic=result['topic'],
            metadata=result['metadata']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get session information by session ID"""
    try:
        result = session_service.get_session(session_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return SessionResponse(
            session_id=result['session_id'],
            created_at=result['created_at'],
            expires_at=result['expires_at'],
            status=result['status'],
            metadata=result['metadata']
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_data: SessionUpdate,
    session_service: SessionService = Depends(get_session_service)
):
    """Update session information"""
    try:
        # Check if session exists
        existing_session = session_service.get_session(session_id)
        if not existing_session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Update session
        success = session_service.update_session(
            session_id=session_id,
            status=session_data.status,
            metadata=session_data.metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to update session {session_id}")
        
        # Get updated session
        updated_session = session_service.get_session(session_id)
        
        return SessionResponse(
            session_id=updated_session['session_id'],
            created_at=updated_session['created_at'],
            expires_at=updated_session['expires_at'],
            status=updated_session['status'],
            metadata=updated_session['metadata']
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@router.get("/{session_id}/quiz", response_model=QuizSessionResponse)
async def get_session_quiz(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get quiz information for a session"""
    try:
        # Check if session is valid
        if not session_service.is_session_valid(session_id):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or expired")
        
        # Get quiz data
        quiz_data = session_service.get_session_quiz(session_id)
        
        if not quiz_data:
            raise HTTPException(status_code=404, detail=f"No quiz found for session {session_id}")
        
        return QuizSessionResponse(
            session_id=quiz_data['session_id'],
            quiz_id=quiz_data['quiz_id'],
            quiz_title=quiz_data['quiz_title'],
            difficulty_level=quiz_data['difficulty_level'],
            total_questions=quiz_data['total_questions'],
            created_at=quiz_data['created_at'],
            status=quiz_data['status'],
            questions=quiz_data['questions']
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz: {str(e)}")

# Answer Validation Endpoints
@router.post("/{session_id}/answers", response_model=AnswerResponse)
async def submit_answer(
    session_id: str,
    answer_submission: AnswerSubmission,
    db_manager: DatabaseManager = Depends(get_database_manager),
    session_service: SessionService = Depends(get_session_service),
    answer_validation_service: AnswerValidationService = Depends(get_answer_validation_service)
):
    """Submit an answer to a quiz question"""
    try:
        # Check if session is valid
        if not session_service.is_session_valid(session_id):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or expired")
        
        # Check if session ID matches
        if answer_submission.session_id != session_id:
            raise HTTPException(status_code=400, detail="Session ID mismatch")
        
        # Get question details
        question = db_manager.get_quiz_question(answer_submission.question_id)
        if not question:
            raise HTTPException(status_code=404, detail=f"Question {answer_submission.question_id} not found")
        
        # Validate answer
        is_correct, feedback = answer_validation_service.validate_answer(
            question=question,
            user_answer=answer_submission.user_answer
        )
        
        # Generate detailed feedback
        explanation = answer_validation_service.generate_feedback(
            question=question,
            is_correct=is_correct,
            user_answer=answer_submission.user_answer
        )
        
        # Store user response
        db_manager.store_user_response(
            session_id=session_id,
            question_id=answer_submission.question_id,
            user_answer=answer_submission.user_answer,
            is_correct=is_correct,
            response_time_seconds=answer_submission.response_time_seconds
        )
        
        return AnswerResponse(
            question_id=answer_submission.question_id,
            is_correct=is_correct,
            correct_answer=question['correct_answer'],
            explanation=question.get('explanation'),
            feedback=feedback
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")

@router.get("/{session_id}/results", response_model=QuizResultsResponse)
async def get_quiz_results(
    session_id: str,
    db_manager: DatabaseManager = Depends(get_database_manager),
    session_service: SessionService = Depends(get_session_service)
):
    """Get quiz results for a session"""
    try:
        # Check if session exists
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        # Get quiz results
        results = db_manager.get_quiz_results(session_id)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No quiz results found for session {session_id}")
        
        return QuizResultsResponse(
            session_id=results['session_id'],
            quiz_title=results['quiz_title'],
            total_questions=results['total_questions'],
            correct_answers=results['correct_answers'],
            score_percentage=results['score_percentage'],
            completion_time=results['completion_time'],
            questions=results['questions'],
            created_at=results['created_at'],
            completed_at=results['completed_at']
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz results: {str(e)}")