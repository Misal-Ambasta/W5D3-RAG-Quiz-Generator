"""
Database Core Module
Wraps the existing DatabaseManager for use in the FastAPI app
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

# Add the backend directory to the path so we can import the services
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.init_db import DatabaseManager as BaseDBManager

class DatabaseManager(BaseDBManager):
    """Extended DatabaseManager with additional app-specific methods"""
    
    def __init__(self, db_path: str = "quiz_generator.db"):
        super().__init__(db_path)
        print(f"📊 Database initialized: {db_path}")
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception:
            return False
    
    # Phase 13 - Session Management Methods
    def create_session(self, document_id: Optional[int] = None, topic: Optional[str] = None, 
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new quiz session"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=24)  # Sessions expire after 24 hours
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Convert metadata to JSON string if provided
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Insert session record
        cursor.execute("""
            INSERT INTO quiz_sessions 
            (session_id, expires_at, status, session_data)
            VALUES (?, ?, ?, ?)
        """, (
            session_id,
            expires_at.isoformat(),
            'active',
            metadata_json
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'status': 'active',
            'document_id': document_id,
            'topic': topic,
            'metadata': metadata
        }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information by session ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, created_at, expires_at, status, session_data, last_activity
            FROM quiz_sessions
            WHERE session_id = ?
        """, (session_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        # Parse session data JSON
        session_data = json.loads(result[4]) if result[4] else {}
        
        return {
            'session_id': result[0],
            'created_at': result[1],
            'expires_at': result[2],
            'status': result[3],
            'metadata': session_data,
            'last_activity': result[5]
        }
    
    def update_session(self, session_id: str, status: Optional[str] = None, 
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update session information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get current session data
        cursor.execute("""
            SELECT session_data FROM quiz_sessions WHERE session_id = ?
        """, (session_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False
        
        # Update session data
        current_data = json.loads(result[0]) if result[0] else {}
        if metadata:
            current_data.update(metadata)
        
        # Build update query
        update_parts = []
        params = []
        
        if status:
            update_parts.append("status = ?")
            params.append(status)
        
        update_parts.append("session_data = ?")
        params.append(json.dumps(current_data))
        
        # Always update last_activity
        update_parts.append("last_activity = ?")
        params.append(datetime.now().isoformat())
        
        # Add session_id to params
        params.append(session_id)
        
        # Execute update
        cursor.execute(f"""
            UPDATE quiz_sessions
            SET {', '.join(update_parts)}
            WHERE session_id = ?
        """, params)
        
        conn.commit()
        conn.close()
        
        return cursor.rowcount > 0
    
    def cleanup_expired_sessions(self) -> int:
        """Delete sessions older than 24 hours"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            DELETE FROM quiz_sessions
            WHERE expires_at < ?
        """, (now,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    # Phase 14 - Answer Validation & Feedback Methods
    def store_user_response(self, session_id: str, question_id: int, 
                           user_answer: str, is_correct: bool,
                           response_time_seconds: Optional[int] = None) -> int:
        """Store user's response to a quiz question"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_responses
            (session_id, question_id, user_answer, is_correct, response_time_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            question_id,
            user_answer,
            is_correct,
            response_time_seconds
        ))
        
        response_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return response_id
    
    def get_quiz_question(self, question_id: int) -> Optional[Dict[str, Any]]:
        """Get quiz question details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, quiz_id, question_order, question_type, question_text, 
                   options, correct_answer, explanation, difficulty_level
            FROM quiz_questions
            WHERE id = ?
        """, (question_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        # Parse options JSON
        options = json.loads(result[5]) if result[5] else None
        
        return {
            'id': result[0],
            'quiz_id': result[1],
            'question_order': result[2],
            'type': result[3],
            'question': result[4],
            'options': options,
            'correct_answer': result[6],
            'explanation': result[7],
            'difficulty': result[8]
        }
    
    def get_quiz_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get quiz results for a session"""
        conn = self.get_connection()
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
        
        # Get user responses
        cursor.execute("""
            SELECT question_id, user_answer, is_correct, response_time_seconds, answered_at
            FROM user_responses
            WHERE session_id = ?
        """, (session_id,))
        
        responses = {}
        total_time = 0
        correct_count = 0
        
        for row in cursor.fetchall():
            question_id = row[0]
            is_correct = bool(row[2])
            response_time = row[3] or 0
            
            if is_correct:
                correct_count += 1
            
            total_time += response_time
            
            responses[question_id] = {
                'user_answer': row[1],
                'is_correct': is_correct,
                'response_time_seconds': response_time,
                'answered_at': row[4]
            }
        
        # Add response data to questions
        for question in questions:
            question_id = question['id']
            if question_id in responses:
                question['user_response'] = responses[question_id]
        
        # Calculate score
        score_percentage = (correct_count / len(questions)) * 100 if questions else 0
        
        conn.close()
        
        return {
            'session_id': session_id,
            'quiz_id': quiz_id,
            'quiz_title': quiz_result[1],
            'difficulty_level': quiz_result[2],
            'total_questions': quiz_result[3],
            'correct_answers': correct_count,
            'score_percentage': round(score_percentage, 2),
            'completion_time': total_time,
            'questions': questions,
            'created_at': quiz_result[4],
            'completed_at': datetime.now().isoformat() if len(responses) == len(questions) else None
        }
