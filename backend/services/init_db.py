"""
SQLite Database Schema for Automated Quiz Generator MVP
"""

import sqlite3
from datetime import datetime
from typing import Optional
import uuid

class DatabaseManager:
    """Manages SQLite database operations for the Quiz Generator."""
    
    def __init__(self, db_path: str = "quiz_generator.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with foreign key support."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
        
    # Feedback methods
    def store_quiz_feedback(self, session_id, quiz_id, rating, comments=None, improvement_suggestions=None, metadata=None):
        """Store feedback for a quiz
        
        Args:
            session_id: ID of the session
            quiz_id: ID of the quiz
            rating: Overall rating (1-5)
            comments: Optional comments
            improvement_suggestions: Optional improvement suggestions
            metadata: Optional metadata as JSON string
            
        Returns:
            ID of the created feedback entry
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO quiz_feedback (
                session_id, quiz_id, rating, comments, improvement_suggestions, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, quiz_id, rating, comments, improvement_suggestions, metadata, datetime.now()))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def store_question_feedback(self, session_id, question_id, rating, comments=None, metadata=None):
        """Store feedback for a question
        
        Args:
            session_id: ID of the session
            question_id: ID of the question
            rating: Rating (1-5)
            comments: Optional comments
            metadata: Optional metadata as JSON string
            
        Returns:
            ID of the created feedback entry
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get quiz_id from question
        cursor.execute("SELECT quiz_id FROM quiz_questions WHERE id = ?", (question_id,))
        result = cursor.fetchone()
        quiz_id = result['quiz_id'] if result else None
        
        cursor.execute("""
            INSERT INTO question_feedback (
                session_id, question_id, quiz_id, rating, comments, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (session_id, question_id, quiz_id, rating, comments, metadata, datetime.now()))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_quiz_feedback(self, quiz_id):
        """Get all feedback for a specific quiz
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            List of feedback entries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM quiz_feedback WHERE quiz_id = ? ORDER BY created_at DESC
        """, (quiz_id,))
        
        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return feedback
    
    def get_question_feedback(self, question_id):
        """Get all feedback for a specific question
        
        Args:
            question_id: ID of the question
            
        Returns:
            List of feedback entries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM question_feedback WHERE question_id = ? ORDER BY created_at DESC
        """, (question_id,))
        
        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return feedback
    
    def get_question_feedback_by_quiz(self, quiz_id):
        """Get all question feedback for a specific quiz
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            List of feedback entries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM question_feedback WHERE quiz_id = ? ORDER BY created_at DESC
        """, (quiz_id,))
        
        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return feedback
    
    def get_all_quiz_feedback(self):
        """Get all quiz feedback
        
        Returns:
            List of feedback entries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM quiz_feedback ORDER BY created_at DESC")
        
        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return feedback
    
    def get_all_question_feedback(self):
        """Get all question feedback
        
        Returns:
            List of feedback entries
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM question_feedback ORDER BY created_at DESC")
        
        feedback = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return feedback
        
    # Analytics methods
    def get_quiz_by_id(self, quiz_id):
        """Get quiz by ID
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            Quiz data or None if not found
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM generated_quizzes WHERE id = ?
        """, (quiz_id,))
        
        quiz = cursor.fetchone()
        conn.close()
        
        return dict(quiz) if quiz else None
    
    def get_sessions_by_quiz_id(self, quiz_id):
        """Get all sessions for a specific quiz
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            List of session data
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT qs.* FROM quiz_sessions qs
            JOIN generated_quizzes gq ON qs.id = gq.session_id
            WHERE gq.id = ?
        """, (quiz_id,))
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sessions
    
    def get_sessions_by_date_range(self, start_date=None, end_date=None):
        """Get all sessions within a date range
        
        Args:
            start_date: Optional start date (datetime)
            end_date: Optional end date (datetime)
            
        Returns:
            List of session data
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM quiz_sessions"
        params = []
        
        if start_date or end_date:
            query += " WHERE "
            
            if start_date:
                query += "created_at >= ?"
                params.append(start_date)
                
                if end_date:
                    query += " AND "
            
            if end_date:
                query += "created_at <= ?"
                params.append(end_date)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sessions
        
    def get_quiz_results(self, session_id=None, question_id=None):
        """Get quiz results for a session or question
        
        Args:
            session_id: Optional session ID to filter by
            question_id: Optional question ID to filter by
            
        Returns:
            List of quiz result data
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM quiz_results"
        params = []
        
        if session_id or question_id:
            query += " WHERE "
            
            if session_id:
                query += "session_id = ?"
                params.append(session_id)
                
                if question_id:
                    query += " AND "
            
            if question_id:
                query += "question_id = ?"
                params.append(question_id)
        
        query += " ORDER BY created_at ASC"
        
        cursor.execute(query, params)
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
        
    def get_session(self, session_id):
        """Get session by ID
        
        Args:
            session_id: ID of the session
            
        Returns:
            Session data or None if not found
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM quiz_sessions WHERE id = ?
        """, (session_id,))
        
        session = cursor.fetchone()
        conn.close()
        
        return dict(session) if session else None
        
    def get_quiz_questions(self, quiz_id):
        """Get all questions for a specific quiz
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            List of question data
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY id
        """, (quiz_id,))
        
        questions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return questions
        
    def store_quiz_result(self, session_id, question_id, user_answer, is_correct, response_time_ms=None):
        """Store a quiz result
        
        Args:
            session_id: ID of the session
            question_id: ID of the question
            user_answer: User's answer
            is_correct: Whether the answer is correct
            response_time_ms: Optional response time in milliseconds
            
        Returns:
            ID of the created result entry
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        result_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO quiz_results (
                id, session_id, question_id, user_answer, is_correct, response_time_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (result_id, session_id, question_id, user_answer, is_correct, response_time_ms, datetime.now()))
        
        conn.commit()
        conn.close()
        
        return result_id
    
    def init_database(self):
        """Initialize database with all required tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create all tables
        self._create_documents_table(cursor)
        self._create_document_chunks_table(cursor)
        self._create_learning_objectives_table(cursor)
        self._create_quiz_sessions_table(cursor)
        self._create_generated_quizzes_table(cursor)
        self._create_quiz_questions_table(cursor)
        self._create_question_answers_table(cursor)
        self._create_user_responses_table(cursor)
        self._create_quiz_feedback_table(cursor)
        self._create_question_feedback_table(cursor)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    
    def _create_documents_table(self, cursor):
        """Store uploaded documents metadata."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                content_hash TEXT UNIQUE,
                raw_content TEXT,
                metadata TEXT,  -- JSON string for additional metadata
                processing_status TEXT DEFAULT 'pending',  -- pending, processed, failed
                error_message TEXT
            )
        """)
    
    def _create_document_chunks_table(self, cursor):
        """Store processed document chunks for RAG."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_size INTEGER NOT NULL,
                start_position INTEGER,
                end_position INTEGER,
                embedding_vector TEXT,  -- JSON string of embedding vector
                chunk_metadata TEXT,  -- JSON string for chunk-specific metadata
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE(document_id, chunk_index)
            )
        """)
    
    def _create_learning_objectives_table(self, cursor):
        """Store extracted learning objectives."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                objective_text TEXT NOT NULL,
                extraction_method TEXT NOT NULL,  -- llm, heading, manual
                confidence_score REAL,
                related_chunks TEXT,  -- JSON array of chunk IDs
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
    
    def _create_quiz_sessions_table(self, cursor):
        """Store anonymous quiz sessions."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                status TEXT DEFAULT 'active',  -- active, completed, expired
                session_data TEXT,  -- JSON string for session metadata
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def _create_generated_quizzes_table(self, cursor):
        """Store generated quiz metadata."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                document_id INTEGER NOT NULL,
                quiz_title TEXT,
                difficulty_level TEXT,
                total_questions INTEGER DEFAULT 0,
                generation_parameters TEXT,  -- JSON string of generation params
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)
    
    def _create_quiz_questions_table(self, cursor):
        """Store individual quiz questions."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_order INTEGER NOT NULL,
                question_type TEXT NOT NULL,  -- mcq, fill_blank, true_false, short_answer
                question_text TEXT NOT NULL,
                options TEXT,  -- JSON array for MCQ options
                correct_answer TEXT NOT NULL,
                explanation TEXT,
                difficulty_level TEXT,
                source_chunks TEXT,  -- JSON array of chunk IDs used
                learning_objective_id INTEGER,
                validation_score REAL,  -- Quality validation score
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES generated_quizzes(id) ON DELETE CASCADE,
                FOREIGN KEY (learning_objective_id) REFERENCES learning_objectives(id),
                UNIQUE(quiz_id, question_order)
            )
        """)
    
    def _create_question_answers_table(self, cursor):
        """Store correct answers for different question types."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                answer_explanation TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
            )
        """)
    
    def _create_user_responses_table(self, cursor):
        """Store user responses to quiz questions."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                user_answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                response_time_seconds INTEGER,
                answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
                UNIQUE(session_id, question_id)
            )
        """)
    
    def create_indexes(self):
        """Create indexes for better query performance."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Indexes for common queries
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_upload_timestamp ON documents(upload_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_documents_processing_status ON documents(processing_status)",
            "CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_learning_objectives_document_id ON learning_objectives(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_session_id ON quiz_sessions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_sessions_expires_at ON quiz_sessions(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_generated_quizzes_session_id ON generated_quizzes(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz_id ON quiz_questions(quiz_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_responses_session_id ON user_responses(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_responses_question_id ON user_responses(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_feedback_session_id ON quiz_feedback(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_feedback_quiz_id ON quiz_feedback(quiz_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_feedback_created_at ON quiz_feedback(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_question_feedback_session_id ON question_feedback(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_question_feedback_question_id ON question_feedback(question_id)",
            "CREATE INDEX IF NOT EXISTS idx_question_feedback_quiz_id ON question_feedback(quiz_id)",
            "CREATE INDEX IF NOT EXISTS idx_question_feedback_created_at ON question_feedback(created_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        print("Database indexes created successfully!")
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions and related data."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete expired sessions (cascading will handle related data)
        cursor.execute("""
            DELETE FROM quiz_sessions 
            WHERE expires_at < CURRENT_TIMESTAMP
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_database_stats(self):
        """Get database statistics for monitoring."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count records in each table
        tables = [
            'documents', 'document_chunks', 'learning_objectives',
            'quiz_sessions', 'generated_quizzes', 'quiz_questions',
            'question_answers', 'user_responses'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]
        
        # Get database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        stats['database_size_bytes'] = cursor.fetchone()[0]
        
        conn.close()
        return stats


# Create feedback tables
    def _create_quiz_feedback_table(self, cursor):
        """Store feedback for quizzes."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                quiz_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comments TEXT,
                improvement_suggestions TEXT,
                metadata TEXT,  -- JSON string for additional metadata
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES generated_quizzes(id) ON DELETE CASCADE
            )
        """)
    
    def _create_question_feedback_table(self, cursor):
        """Store feedback for individual questions."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question_id INTEGER NOT NULL,
                quiz_id INTEGER,
                rating INTEGER NOT NULL,
                comments TEXT,
                metadata TEXT,  -- JSON string for additional metadata
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES quiz_sessions(session_id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE,
                FOREIGN KEY (quiz_id) REFERENCES generated_quizzes(id) ON DELETE CASCADE
            )
        """)

# Utility functions for common operations
def create_session_id() -> str:
    """Generate a unique session ID."""
    return str(uuid.uuid4())

def create_quiz_session(db_manager: DatabaseManager, expires_in_hours: int = 24) -> str:
    """Create a new quiz session."""
    session_id = create_session_id()
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO quiz_sessions (session_id, expires_at)
        VALUES (?, datetime('now', '+{} hours'))
    """.format(expires_in_hours), (session_id,))
    
    conn.commit()
    conn.close()
    
    return session_id

def get_document_id_by_hash(db_manager: DatabaseManager, content_hash: str) -> Optional[int]:
    """Fetch the document id for a given content_hash."""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM documents WHERE content_hash = ?", (content_hash,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def store_document(db_manager: DatabaseManager, filename: str, original_filename: str, 
                  file_type: str, file_size: int, content_hash: str, 
                  raw_content: str, metadata: str = None) -> Optional[int]:
    """Store a document in the database. If content_hash already exists, return its id."""
    # First check if document already exists
    existing_id = get_document_id_by_hash(db_manager, content_hash)
    if existing_id:
        print(f"Document with content_hash '{content_hash}' already exists with id: {existing_id}")
        return existing_id
    
    # Insert new document
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO documents (filename, original_filename, file_type, file_size, 
                                 content_hash, raw_content, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (filename, original_filename, file_type, file_size, content_hash, raw_content, metadata))
        
        document_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return document_id
    except sqlite3.IntegrityError as e:
        conn.close()
        print(f"Error inserting document: {e}")
        # Try to get existing document id as fallback
        return get_document_id_by_hash(db_manager, content_hash)


def store_document_chunk(db_manager: DatabaseManager, document_id: int, chunk_index: int,
                        chunk_text: str, chunk_size: int, start_pos: int = None,
                        end_pos: int = None, embedding_vector: str = None,
                        chunk_metadata: str = None) -> Optional[int]:
    """Store a document chunk in the database with duplicate protection."""
    if document_id is None:
        print("Error: document_id is None, cannot store chunk")
        return None
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Check if chunk already exists
    cursor.execute("""
        SELECT id FROM document_chunks 
        WHERE document_id = ? AND chunk_index = ?
    """, (document_id, chunk_index))
    
    existing_chunk = cursor.fetchone()
    if existing_chunk:
        print(f"Chunk with document_id={document_id}, chunk_index={chunk_index} already exists with id: {existing_chunk[0]}")
        conn.close()
        return existing_chunk[0]
    
    try:
        cursor.execute("""
            INSERT INTO document_chunks (document_id, chunk_index, chunk_text, chunk_size,
                                       start_position, end_position, embedding_vector, chunk_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (document_id, chunk_index, chunk_text, chunk_size, start_pos, end_pos, 
              embedding_vector, chunk_metadata))
        
        chunk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return chunk_id
    except sqlite3.IntegrityError as e:
        conn.close()
        print(f"Error inserting chunk: {e}")
        return None


# Feedback and Analytics Methods

def store_quiz_feedback(db_manager, session_id, quiz_id, rating, comments=None, improvement_suggestions=None, metadata=None):
    """Store feedback for a quiz
    
    Args:
        db_manager: Database manager instance
        session_id: ID of the session
        quiz_id: ID of the quiz
        rating: Overall rating (1-5)
        comments: Optional comments
        improvement_suggestions: Optional improvement suggestions
        metadata: Optional metadata as JSON string
        
    Returns:
        ID of the created feedback entry
    """
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO quiz_feedback (
            session_id, quiz_id, rating, comments, improvement_suggestions, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, quiz_id, rating, comments, improvement_suggestions, metadata, datetime.now()))
    
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return feedback_id

def store_question_feedback(db_manager, session_id, question_id, rating, comments=None, metadata=None):
    """Store feedback for a question
    
    Args:
        db_manager: Database manager instance
        session_id: ID of the session
        question_id: ID of the question
        rating: Rating (1-5)
        comments: Optional comments
        metadata: Optional metadata as JSON string
        
    Returns:
        ID of the created feedback entry
    """
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Get quiz_id from question
    cursor.execute("SELECT quiz_id FROM quiz_questions WHERE id = ?", (question_id,))
    result = cursor.fetchone()
    quiz_id = result['quiz_id'] if result else None
    
    cursor.execute("""
        INSERT INTO question_feedback (
            session_id, question_id, quiz_id, rating, comments, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, question_id, quiz_id, rating, comments, metadata, datetime.now()))
    
    feedback_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return feedback_id

def get_quiz_feedback(db_manager, quiz_id):
    """Get all feedback for a specific quiz
    
    Args:
        db_manager: Database manager instance
        quiz_id: ID of the quiz
        
    Returns:
        List of feedback entries
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM quiz_feedback WHERE quiz_id = ? ORDER BY created_at DESC
    """, (quiz_id,))
    
    feedback = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return feedback

def get_question_feedback(db_manager, question_id):
    """Get all feedback for a specific question
    
    Args:
        db_manager: Database manager instance
        question_id: ID of the question
        
    Returns:
        List of feedback entries
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM question_feedback WHERE question_id = ? ORDER BY created_at DESC
    """, (question_id,))
    
    feedback = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return feedback

def get_question_feedback_by_quiz(db_manager, quiz_id):
    """Get all question feedback for a specific quiz
    
    Args:
        db_manager: Database manager instance
        quiz_id: ID of the quiz
        
    Returns:
        List of feedback entries
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM question_feedback WHERE quiz_id = ? ORDER BY created_at DESC
    """, (quiz_id,))
    
    feedback = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return feedback

def get_all_quiz_feedback(db_manager):
    """Get all quiz feedback
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        List of feedback entries
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM quiz_feedback ORDER BY created_at DESC")
    
    feedback = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return feedback

def get_all_question_feedback(db_manager):
    """Get all question feedback
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        List of feedback entries
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM question_feedback ORDER BY created_at DESC")
    
    feedback = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return feedback

def get_quiz_by_id(db_manager, quiz_id):
    """Get quiz by ID
    
    Args:
        db_manager: Database manager instance
        quiz_id: ID of the quiz
        
    Returns:
        Quiz data or None if not found
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM generated_quizzes WHERE id = ?
    """, (quiz_id,))
    
    quiz = cursor.fetchone()
    conn.close()
    
    return dict(quiz) if quiz else None

def get_sessions_by_quiz_id(db_manager, quiz_id):
    """Get all sessions for a specific quiz
    
    Args:
        db_manager: Database manager instance
        quiz_id: ID of the quiz
        
    Returns:
        List of session data
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT qs.* FROM quiz_sessions qs
        JOIN generated_quizzes gq ON qs.session_id = gq.session_id
        WHERE gq.id = ?
    """, (quiz_id,))
    
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return sessions

def get_sessions_by_date_range(db_manager, start_date=None, end_date=None):
    """Get all sessions within a date range
    
    Args:
        db_manager: Database manager instance
        start_date: Optional start date (datetime)
        end_date: Optional end date (datetime)
        
    Returns:
        List of session data
    """
    conn = db_manager.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM quiz_sessions"
    params = []
    
    if start_date or end_date:
        query += " WHERE "
        
        if start_date:
            query += "created_at >= ?"
            params.append(start_date)
            
            if end_date:
                query += " AND "
        
        if end_date:
            query += "created_at <= ?"
            params.append(end_date)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return sessions

# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Clean up any existing test database
    test_db_path = "quiz_generator.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("Removed existing test database")
    
    # Initialize database
    db_manager = DatabaseManager(test_db_path)
    
    # Create indexes
    db_manager.create_indexes()
    
    # Test with sample data
    session_id = create_quiz_session(db_manager)
    print(f"Created session: {session_id}")
    
    # Store a sample document
    doc_id = store_document(
        db_manager,
        filename="sample.pdf",
        original_filename="Chapter_1_Biology.pdf",
        file_type="pdf",
        file_size=1024000,
        content_hash="abc123",
        raw_content="Sample biology content about photosynthesis...",
        metadata='{"subject": "biology", "chapter": 1}'
    )
    print(f"Document ID: {doc_id}")
    
    if doc_id is not None and doc_id > 0:
        # Store a sample chunk only if document exists
        chunk_id = store_document_chunk(
            db_manager,
            document_id=doc_id,
            chunk_index=0,
            chunk_text="Photosynthesis is the process by which plants convert light energy into chemical energy.",
            chunk_size=88,
            start_pos=0,
            end_pos=88,
            embedding_vector='[0.1, 0.2, 0.3, 0.4, 0.5]',
            chunk_metadata='{"section": "introduction", "page": 1}'
        )
        print(f"Chunk ID: {chunk_id}")
        
        # Test storing a second chunk
        chunk_id2 = store_document_chunk(
            db_manager,
            document_id=doc_id,
            chunk_index=1,
            chunk_text="Plants use chlorophyll to capture light energy during photosynthesis.",
            chunk_size=68,
            start_pos=88,
            end_pos=156,
            embedding_vector='[0.2, 0.3, 0.4, 0.5, 0.6]',
            chunk_metadata='{"section": "details", "page": 1}'
        )
        print(f"Second chunk ID: {chunk_id2}")
    else:
        print("Failed to create or find document for chunk insertion.")
    
    # Test duplicate document insertion
    print("\n--- Testing duplicate document insertion ---")
    doc_id2 = store_document(
        db_manager,
        filename="sample2.pdf",  # Different filename
        original_filename="Chapter_1_Biology_Copy.pdf",
        file_type="pdf",
        file_size=1024000,
        content_hash="abc123",  # Same content hash
        raw_content="Sample biology content about photosynthesis...",
        metadata='{"subject": "biology", "chapter": 1}'
    )
    print(f"Duplicate document ID: {doc_id2}")
    
    # Test duplicate chunk insertion
    print("\n--- Testing duplicate chunk insertion ---")
    if doc_id is not None and doc_id > 0:
        chunk_id3 = store_document_chunk(
            db_manager,
            document_id=doc_id,
            chunk_index=0,  # Same index as first chunk
            chunk_text="Different text but same index",
            chunk_size=32,
            start_pos=0,
            end_pos=32,
            embedding_vector='[0.7, 0.8, 0.9, 1.0, 1.1]',
            chunk_metadata='{"section": "duplicate_test", "page": 1}'
        )
        print(f"Duplicate chunk ID: {chunk_id3}")
    
    # Get database stats
    stats = db_manager.get_database_stats()
    print(f"\nDatabase stats: {stats}")
    
    print("\nDatabase schema created and tested successfully!")