"""Session Management Service for Quiz Generator

Implements Phase 13 - Session Management
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from app.core.database import DatabaseManager

class SessionService:
    """Service for managing quiz sessions"""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the session service"""
        self.db_manager = db_manager
    
    def create_session(self, document_id: Optional[int] = None, 
                      topic: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new quiz session"""
        # Use the database manager to create a session
        session_data = self.db_manager.create_session(
            document_id=document_id,
            topic=topic,
            metadata=metadata
        )
        
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information by session ID"""
        return self.db_manager.get_session(session_id)
    
    def update_session(self, session_id: str, status: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update session information"""
        return self.db_manager.update_session(
            session_id=session_id,
            status=status,
            metadata=metadata
        )
    
    def cleanup_expired_sessions(self) -> int:
        """Delete sessions older than 24 hours"""
        return self.db_manager.cleanup_expired_sessions()
    
    def get_session_quiz(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get quiz information for a session"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get quiz information
        cursor.execute("""
            SELECT q.id, q.quiz_title, q.difficulty_level, q.total_questions, q.created_at
            FROM generated_quizzes q
            WHERE q.session_id = ?
        """, (session_id,))
        
        quiz_result = cursor.fetchone()
        if not quiz_result:
            conn.close()
            return None
        
        quiz_id = quiz_result[0]
        
        # Get all questions for this quiz
        cursor.execute("""
            SELECT id, question_order, question_type, question_text, 
                   options, correct_answer, explanation, difficulty_level
            FROM quiz_questions
            WHERE quiz_id = ?
            ORDER BY question_order
        """, (quiz_id,))
        
        questions = []
        for row in cursor.fetchall():
            options = json.loads(row[4]) if row[4] else None
            questions.append({
                'id': row[0],
                'order': row[1],
                'type': row[2],
                'question': row[3],
                'options': options,
                'correct_answer': row[5],
                'explanation': row[6],
                'difficulty': row[7]
            })
        
        conn.close()
        
        return {
            'session_id': session_id,
            'quiz_id': quiz_id,
            'quiz_title': quiz_result[1],
            'difficulty_level': quiz_result[2],
            'total_questions': quiz_result[3],
            'questions': questions,
            'created_at': quiz_result[4],
            'status': 'active'
        }
    
    def is_session_valid(self, session_id: str) -> bool:
        """Check if a session is valid and not expired"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Check if session is active
        if session.get('status') != 'active':
            return False
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session.get('expires_at'))
        if expires_at < datetime.now():
            return False
        
        return True