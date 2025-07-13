"""Feedback Service

Implements Phase 16 - Feedback Collection
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime

class FeedbackService:
    """Service for collecting and managing user feedback"""
    
    def __init__(self, db_manager):
        """Initialize the feedback service
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def submit_quiz_feedback(self, 
                            session_id: str, 
                            quiz_id: int, 
                            rating: int, 
                            comments: Optional[str] = None,
                            improvement_suggestions: Optional[str] = None,
                            difficulty_rating: Optional[int] = None,
                            relevance_rating: Optional[int] = None,
                            ui_rating: Optional[int] = None,
                            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Submit feedback for a quiz
        
        Args:
            session_id: ID of the session
            quiz_id: ID of the quiz
            rating: Overall rating (1-5)
            comments: Optional comments
            improvement_suggestions: Optional improvement suggestions
            difficulty_rating: Optional difficulty rating (1-5)
            relevance_rating: Optional relevance rating (1-5)
            ui_rating: Optional UI/UX rating (1-5)
            tags: Optional list of feedback tags
            
        Returns:
            Dictionary containing feedback submission result
        """
        # Validate session and quiz
        session = self.db_manager.get_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        quiz = self.db_manager.get_quiz_by_id(quiz_id)
        if not quiz:
            return {'success': False, 'error': 'Quiz not found'}
        
        # Validate rating
        if not 1 <= rating <= 5:
            return {'success': False, 'error': 'Rating must be between 1 and 5'}
        
        # Prepare metadata
        metadata = {}
        
        if difficulty_rating is not None:
            if not 1 <= difficulty_rating <= 5:
                return {'success': False, 'error': 'Difficulty rating must be between 1 and 5'}
            metadata['difficulty_rating'] = difficulty_rating
        
        if relevance_rating is not None:
            if not 1 <= relevance_rating <= 5:
                return {'success': False, 'error': 'Relevance rating must be between 1 and 5'}
            metadata['relevance_rating'] = relevance_rating
        
        if ui_rating is not None:
            if not 1 <= ui_rating <= 5:
                return {'success': False, 'error': 'UI rating must be between 1 and 5'}
            metadata['ui_rating'] = ui_rating
        
        if tags:
            metadata['tags'] = tags
        
        # Store feedback
        feedback_id = self.db_manager.store_quiz_feedback(
            session_id=session_id,
            quiz_id=quiz_id,
            rating=rating,
            comments=comments,
            improvement_suggestions=improvement_suggestions,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        if not feedback_id:
            return {'success': False, 'error': 'Failed to store feedback'}
        
        return {
            'success': True,
            'feedback_id': feedback_id,
            'session_id': session_id,
            'quiz_id': quiz_id,
            'submitted_at': datetime.now().isoformat()
        }
    
    def submit_question_feedback(self,
                               session_id: str,
                               question_id: int,
                               rating: int,
                               comments: Optional[str] = None,
                               is_confusing: Optional[bool] = None,
                               is_irrelevant: Optional[bool] = None,
                               has_errors: Optional[bool] = None) -> Dict[str, Any]:
        """Submit feedback for a specific question
        
        Args:
            session_id: ID of the session
            question_id: ID of the question
            rating: Rating (1-5)
            comments: Optional comments
            is_confusing: Whether the question is confusing
            is_irrelevant: Whether the question is irrelevant
            has_errors: Whether the question has errors
            
        Returns:
            Dictionary containing feedback submission result
        """
        # Validate session
        session = self.db_manager.get_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        # Validate question
        question = self.db_manager.get_quiz_question(question_id)
        if not question:
            return {'success': False, 'error': 'Question not found'}
        
        # Validate rating
        if not 1 <= rating <= 5:
            return {'success': False, 'error': 'Rating must be between 1 and 5'}
        
        # Prepare metadata
        metadata = {}
        
        if is_confusing is not None:
            metadata['is_confusing'] = is_confusing
        
        if is_irrelevant is not None:
            metadata['is_irrelevant'] = is_irrelevant
        
        if has_errors is not None:
            metadata['has_errors'] = has_errors
        
        # Store feedback
        feedback_id = self.db_manager.store_question_feedback(
            session_id=session_id,
            question_id=question_id,
            rating=rating,
            comments=comments,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        if not feedback_id:
            return {'success': False, 'error': 'Failed to store feedback'}
        
        return {
            'success': True,
            'feedback_id': feedback_id,
            'session_id': session_id,
            'question_id': question_id,
            'submitted_at': datetime.now().isoformat()
        }
    
    def get_quiz_feedback(self, quiz_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a specific quiz
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            List of feedback entries
        """
        return self.db_manager.get_quiz_feedback(quiz_id)
    
    def get_question_feedback(self, question_id: int) -> List[Dict[str, Any]]:
        """Get all feedback for a specific question
        
        Args:
            question_id: ID of the question
            
        Returns:
            List of feedback entries
        """
        return self.db_manager.get_question_feedback(question_id)
    
    def get_feedback_summary(self, quiz_id: Optional[int] = None) -> Dict[str, Any]:
        """Get a summary of feedback
        
        Args:
            quiz_id: Optional ID of the quiz to filter by
            
        Returns:
            Dictionary containing feedback summary
        """
        # Get all feedback
        if quiz_id:
            quiz_feedback = self.db_manager.get_quiz_feedback(quiz_id)
            question_feedback = self.db_manager.get_question_feedback_by_quiz(quiz_id)
        else:
            quiz_feedback = self.db_manager.get_all_quiz_feedback()
            question_feedback = self.db_manager.get_all_question_feedback()
        
        if not quiz_feedback and not question_feedback:
            return {
                'quiz_id': quiz_id,
                'total_feedback': 0,
                'summary': {}
            }
        
        # Calculate quiz feedback metrics
        quiz_ratings = [f.get('rating', 0) for f in quiz_feedback if f.get('rating')]
        avg_quiz_rating = sum(quiz_ratings) / len(quiz_ratings) if quiz_ratings else 0
        
        # Calculate question feedback metrics
        question_ratings = [f.get('rating', 0) for f in question_feedback if f.get('rating')]
        avg_question_rating = sum(question_ratings) / len(question_ratings) if question_ratings else 0
        
        # Count feedback by rating
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for f in quiz_feedback:
            rating = f.get('rating')
            if rating and 1 <= rating <= 5:
                rating_counts[rating] += 1
        
        # Extract common issues from question feedback
        common_issues = {
            'confusing': 0,
            'irrelevant': 0,
            'has_errors': 0
        }
        
        for f in question_feedback:
            metadata = f.get('metadata', '{}')
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            if metadata.get('is_confusing'):
                common_issues['confusing'] += 1
            
            if metadata.get('is_irrelevant'):
                common_issues['irrelevant'] += 1
            
            if metadata.get('has_errors'):
                common_issues['has_errors'] += 1
        
        # Extract improvement suggestions
        improvement_suggestions = []
        for f in quiz_feedback:
            suggestion = f.get('improvement_suggestions')
            if suggestion and suggestion.strip():
                improvement_suggestions.append(suggestion)
        
        return {
            'quiz_id': quiz_id,
            'total_feedback': len(quiz_feedback) + len(question_feedback),
            'summary': {
                'average_quiz_rating': avg_quiz_rating,
                'average_question_rating': avg_question_rating,
                'rating_distribution': rating_counts,
                'common_issues': common_issues,
                'improvement_suggestions_count': len(improvement_suggestions),
                'recent_improvement_suggestions': improvement_suggestions[:5] if improvement_suggestions else []
            }
        }