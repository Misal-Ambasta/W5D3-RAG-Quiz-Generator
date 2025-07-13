"""Analytics Service

Implements Phase 15 - Quiz Analytics
"""

from typing import Dict, List, Any, Optional
import json
import statistics
from datetime import datetime, timedelta

class AnalyticsService:
    """Service for generating quiz analytics"""
    
    def __init__(self, db_manager):
        """Initialize the analytics service
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def get_quiz_performance_metrics(self, quiz_id: int) -> Dict[str, Any]:
        """Get performance metrics for a specific quiz
        
        Args:
            quiz_id: ID of the quiz
            
        Returns:
            Dictionary containing quiz performance metrics
        """
        # Get quiz data
        quiz = self.db_manager.get_quiz_by_id(quiz_id)
        if not quiz:
            return {}
        
        # Get all sessions for this quiz
        sessions = self.db_manager.get_sessions_by_quiz_id(quiz_id)
        if not sessions:
            return {
                'quiz_id': quiz_id,
                'quiz_title': quiz.get('title', 'Unknown'),
                'total_sessions': 0,
                'metrics': {}
            }
        
        # Calculate metrics
        total_sessions = len(sessions)
        completion_rates = []
        average_scores = []
        question_performance = {}
        response_times = []
        
        for session in sessions:
            session_id = session['session_id']
            
            # Get results for this session
            results = self.db_manager.get_quiz_results(session_id)
            if not results:
                continue
            
            # Calculate completion rate
            if results['total_questions'] > 0:
                completion_rate = len(results['questions']) / results['total_questions'] * 100
                completion_rates.append(completion_rate)
            
            # Add score
            average_scores.append(results['score_percentage'])
            
            # Add response times
            if results.get('completion_time'):
                response_times.append(results['completion_time'])
            
            # Process question performance
            for question in results['questions']:
                question_id = question['question_id']
                
                if question_id not in question_performance:
                    question_performance[question_id] = {
                        'question_id': question_id,
                        'question_text': question.get('question_text', 'Unknown'),
                        'question_type': question.get('question_type', 'Unknown'),
                        'difficulty': question.get('difficulty', 'medium'),
                        'total_attempts': 0,
                        'correct_attempts': 0,
                        'average_response_time': 0,
                        'response_times': []
                    }
                
                question_performance[question_id]['total_attempts'] += 1
                
                if question.get('is_correct', False):
                    question_performance[question_id]['correct_attempts'] += 1
                
                if question.get('response_time_seconds'):
                    question_performance[question_id]['response_times'].append(
                        question['response_time_seconds']
                    )
        
        # Calculate final metrics
        avg_completion_rate = statistics.mean(completion_rates) if completion_rates else 0
        avg_score = statistics.mean(average_scores) if average_scores else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Calculate per-question metrics
        question_metrics = []
        for q_id, q_data in question_performance.items():
            success_rate = 0
            if q_data['total_attempts'] > 0:
                success_rate = (q_data['correct_attempts'] / q_data['total_attempts']) * 100
            
            avg_q_response_time = 0
            if q_data['response_times']:
                avg_q_response_time = statistics.mean(q_data['response_times'])
            
            question_metrics.append({
                'question_id': q_id,
                'question_text': q_data['question_text'],
                'question_type': q_data['question_type'],
                'difficulty': q_data['difficulty'],
                'success_rate': success_rate,
                'average_response_time': avg_q_response_time,
                'total_attempts': q_data['total_attempts']
            })
        
        # Sort questions by success rate (ascending)
        question_metrics.sort(key=lambda x: x['success_rate'])
        
        return {
            'quiz_id': quiz_id,
            'quiz_title': quiz.get('title', 'Unknown'),
            'total_sessions': total_sessions,
            'metrics': {
                'average_completion_rate': avg_completion_rate,
                'average_score': avg_score,
                'average_response_time': avg_response_time,
                'questions': question_metrics
            }
        }
    
    def get_user_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a specific user session
        
        Args:
            session_id: ID of the session
            
        Returns:
            Dictionary containing session analytics
        """
        # Get session data
        session = self.db_manager.get_session(session_id)
        if not session:
            return {}
        
        # Get quiz results
        results = self.db_manager.get_quiz_results(session_id)
        if not results:
            return {
                'session_id': session_id,
                'quiz_id': None,
                'status': session.get('status', 'unknown'),
                'metrics': {}
            }
        
        # Calculate metrics
        total_questions = results['total_questions']
        answered_questions = len(results['questions'])
        completion_rate = (answered_questions / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate difficulty breakdown
        difficulty_counts = {'easy': 0, 'medium': 0, 'hard': 0}
        difficulty_correct = {'easy': 0, 'medium': 0, 'hard': 0}
        question_types = {}
        response_times_by_difficulty = {'easy': [], 'medium': [], 'hard': []}
        
        for question in results['questions']:
            difficulty = question.get('difficulty', 'medium')
            q_type = question.get('question_type', 'unknown')
            
            # Count by difficulty
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1
            
            # Count correct by difficulty
            if question.get('is_correct', False) and difficulty in difficulty_correct:
                difficulty_correct[difficulty] += 1
            
            # Count by question type
            if q_type not in question_types:
                question_types[q_type] = {'total': 0, 'correct': 0, 'response_times': []}
            
            question_types[q_type]['total'] += 1
            
            if question.get('is_correct', False):
                question_types[q_type]['correct'] += 1
            
            # Add response time
            if question.get('response_time_seconds'):
                response_time = question['response_time_seconds']
                question_types[q_type]['response_times'].append(response_time)
                
                if difficulty in response_times_by_difficulty:
                    response_times_by_difficulty[difficulty].append(response_time)
        
        # Calculate success rates by difficulty
        difficulty_success_rates = {}
        for diff, count in difficulty_counts.items():
            if count > 0:
                difficulty_success_rates[diff] = (difficulty_correct[diff] / count) * 100
            else:
                difficulty_success_rates[diff] = 0
        
        # Calculate average response times by difficulty
        avg_response_times_by_difficulty = {}
        for diff, times in response_times_by_difficulty.items():
            if times:
                avg_response_times_by_difficulty[diff] = statistics.mean(times)
            else:
                avg_response_times_by_difficulty[diff] = 0
        
        # Calculate question type metrics
        question_type_metrics = []
        for q_type, data in question_types.items():
            success_rate = 0
            if data['total'] > 0:
                success_rate = (data['correct'] / data['total']) * 100
            
            avg_response_time = 0
            if data['response_times']:
                avg_response_time = statistics.mean(data['response_times'])
            
            question_type_metrics.append({
                'question_type': q_type,
                'total': data['total'],
                'correct': data['correct'],
                'success_rate': success_rate,
                'average_response_time': avg_response_time
            })
        
        return {
            'session_id': session_id,
            'quiz_id': results.get('quiz_id'),
            'quiz_title': results.get('quiz_title', 'Unknown'),
            'status': session.get('status', 'unknown'),
            'created_at': session.get('created_at'),
            'completed_at': results.get('completed_at'),
            'metrics': {
                'total_questions': total_questions,
                'answered_questions': answered_questions,
                'completion_rate': completion_rate,
                'score_percentage': results.get('score_percentage', 0),
                'completion_time': results.get('completion_time'),
                'difficulty_breakdown': {
                    'counts': difficulty_counts,
                    'success_rates': difficulty_success_rates,
                    'average_response_times': avg_response_times_by_difficulty
                },
                'question_types': question_type_metrics
            }
        }
    
    def get_aggregate_analytics(self, time_period: str = 'week') -> Dict[str, Any]:
        """Get aggregate analytics across all quizzes
        
        Args:
            time_period: Time period for analytics ('day', 'week', 'month', 'all')
            
        Returns:
            Dictionary containing aggregate analytics
        """
        # Determine date range
        end_date = datetime.now()
        start_date = None
        
        if time_period == 'day':
            start_date = end_date - timedelta(days=1)
        elif time_period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif time_period == 'month':
            start_date = end_date - timedelta(days=30)
        # 'all' means no start date filter
        
        # Get all sessions within the time period
        sessions = self.db_manager.get_sessions_by_date_range(start_date, end_date)
        
        if not sessions:
            return {
                'time_period': time_period,
                'total_sessions': 0,
                'metrics': {}
            }
        
        # Calculate metrics
        total_sessions = len(sessions)
        completed_sessions = 0
        total_questions_answered = 0
        total_correct_answers = 0
        completion_times = []
        scores = []
        
        # Metrics by difficulty
        difficulty_metrics = {
            'easy': {'total': 0, 'correct': 0, 'response_times': []},
            'medium': {'total': 0, 'correct': 0, 'response_times': []},
            'hard': {'total': 0, 'correct': 0, 'response_times': []}
        }
        
        # Metrics by question type
        question_type_metrics = {}
        
        # Process each session
        for session in sessions:
            session_id = session['session_id']
            
            # Get results for this session
            results = self.db_manager.get_quiz_results(session_id)
            if not results:
                continue
            
            # Count completed sessions
            if session.get('status') == 'completed':
                completed_sessions += 1
            
            # Add score
            if 'score_percentage' in results:
                scores.append(results['score_percentage'])
            
            # Add completion time
            if 'completion_time' in results:
                completion_times.append(results['completion_time'])
            
            # Process questions
            for question in results.get('questions', []):
                total_questions_answered += 1
                
                if question.get('is_correct', False):
                    total_correct_answers += 1
                
                # Process by difficulty
                difficulty = question.get('difficulty', 'medium')
                if difficulty in difficulty_metrics:
                    difficulty_metrics[difficulty]['total'] += 1
                    
                    if question.get('is_correct', False):
                        difficulty_metrics[difficulty]['correct'] += 1
                    
                    if question.get('response_time_seconds'):
                        difficulty_metrics[difficulty]['response_times'].append(
                            question['response_time_seconds']
                        )
                
                # Process by question type
                q_type = question.get('question_type', 'unknown')
                if q_type not in question_type_metrics:
                    question_type_metrics[q_type] = {
                        'total': 0, 'correct': 0, 'response_times': []
                    }
                
                question_type_metrics[q_type]['total'] += 1
                
                if question.get('is_correct', False):
                    question_type_metrics[q_type]['correct'] += 1
                
                if question.get('response_time_seconds'):
                    question_type_metrics[q_type]['response_times'].append(
                        question['response_time_seconds']
                    )
        
        # Calculate final metrics
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        avg_score = statistics.mean(scores) if scores else 0
        avg_completion_time = statistics.mean(completion_times) if completion_times else 0
        overall_success_rate = (total_correct_answers / total_questions_answered * 100) if total_questions_answered > 0 else 0
        
        # Calculate difficulty metrics
        difficulty_results = {}
        for diff, data in difficulty_metrics.items():
            success_rate = 0
            if data['total'] > 0:
                success_rate = (data['correct'] / data['total']) * 100
            
            avg_response_time = 0
            if data['response_times']:
                avg_response_time = statistics.mean(data['response_times'])
            
            difficulty_results[diff] = {
                'total': data['total'],
                'correct': data['correct'],
                'success_rate': success_rate,
                'average_response_time': avg_response_time
            }
        
        # Calculate question type metrics
        question_type_results = []
        for q_type, data in question_type_metrics.items():
            success_rate = 0
            if data['total'] > 0:
                success_rate = (data['correct'] / data['total']) * 100
            
            avg_response_time = 0
            if data['response_times']:
                avg_response_time = statistics.mean(data['response_times'])
            
            question_type_results.append({
                'question_type': q_type,
                'total': data['total'],
                'correct': data['correct'],
                'success_rate': success_rate,
                'average_response_time': avg_response_time
            })
        
        # Sort question types by success rate (ascending)
        question_type_results.sort(key=lambda x: x['success_rate'])
        
        return {
            'time_period': time_period,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'metrics': {
                'completion_rate': completion_rate,
                'average_score': avg_score,
                'average_completion_time': avg_completion_time,
                'total_questions_answered': total_questions_answered,
                'total_correct_answers': total_correct_answers,
                'overall_success_rate': overall_success_rate,
                'difficulty_metrics': difficulty_results,
                'question_type_metrics': question_type_results
            }
        }