"""Answer Validation Service for Quiz Generator

Implements Phase 14 - Answer Validation & Feedback
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from difflib import SequenceMatcher

class AnswerValidationService:
    """Service for validating quiz answers and providing feedback"""
    
    def __init__(self):
        """Initialize the answer validation service"""
        pass
    
    def validate_answer(self, question: Dict[str, Any], user_answer: str) -> Tuple[bool, str]:
        """Validate a user's answer against the correct answer
        
        Args:
            question: The question dictionary with type, correct_answer, etc.
            user_answer: The user's submitted answer
            
        Returns:
            Tuple of (is_correct, feedback)
        """
        question_type = question.get('type', '').lower()
        correct_answer = question.get('correct_answer', '')
        
        # Handle different question types
        if question_type == 'multiple_choice':
            return self._validate_mcq(user_answer, correct_answer)
        elif question_type == 'true_false':
            return self._validate_true_false(user_answer, correct_answer)
        elif question_type == 'fill_in_the_blank':
            return self._validate_fill_in_blank(user_answer, correct_answer)
        elif question_type == 'short_answer':
            return self._validate_short_answer(user_answer, correct_answer)
        else:
            # Default to exact match
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            feedback = "Correct!" if is_correct else f"The correct answer is: {correct_answer}"
            return is_correct, feedback
    
    def _validate_mcq(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """Validate a multiple choice question answer"""
        # Normalize answers (remove spaces, convert to uppercase)
        user_ans = user_answer.strip().upper()
        correct_ans = correct_answer.strip().upper()
        
        is_correct = user_ans == correct_ans
        
        if is_correct:
            feedback = "Correct!"
        else:
            feedback = f"Incorrect. The correct answer is {correct_answer}."
        
        return is_correct, feedback
    
    def _validate_true_false(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """Validate a true/false question answer"""
        # Normalize answers
        user_ans = user_answer.strip().lower()
        correct_ans = correct_answer.strip().lower()
        
        # Handle variations of true/false
        user_is_true = user_ans in ['true', 't', 'yes', 'y', '1']
        user_is_false = user_ans in ['false', 'f', 'no', 'n', '0']
        
        correct_is_true = correct_ans in ['true', 't', 'yes', 'y', '1']
        
        # Determine if answer is correct
        if (user_is_true and correct_is_true) or (user_is_false and not correct_is_true):
            return True, "Correct!"
        else:
            return False, f"Incorrect. The correct answer is {correct_answer}."
    
    def _validate_fill_in_blank(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """Validate a fill-in-the-blank question answer"""
        # Normalize answers
        user_ans = user_answer.strip().lower()
        correct_ans = correct_answer.strip().lower()
        
        # Check for exact match first
        if user_ans == correct_ans:
            return True, "Correct!"
        
        # Check for close match (accounting for minor typos)
        similarity = SequenceMatcher(None, user_ans, correct_ans).ratio()
        if similarity >= 0.85:  # 85% similarity threshold
            return True, "Correct! (Note: Your answer had minor differences from the expected answer)"
        
        return False, f"Incorrect. The correct answer is '{correct_answer}'."
    
    def _validate_short_answer(self, user_answer: str, correct_answer: str) -> Tuple[bool, str]:
        """Validate a short answer question"""
        # Normalize answers
        user_ans = user_answer.strip().lower()
        correct_ans = correct_answer.strip().lower()
        
        # For short answers, check if key terms are present
        key_terms = [term.strip() for term in correct_ans.split(',')]
        
        # Count how many key terms are in the user's answer
        matched_terms = [term for term in key_terms if term in user_ans]
        match_ratio = len(matched_terms) / len(key_terms) if key_terms else 0
        
        # If 70% or more key terms are present, consider it correct
        if match_ratio >= 0.7:
            return True, "Correct!"
        elif match_ratio >= 0.5:
            return True, "Partially correct. The full answer is: " + correct_answer
        else:
            return False, f"Incorrect. The correct answer is: {correct_answer}"
    
    def generate_feedback(self, question: Dict[str, Any], is_correct: bool, user_answer: str) -> str:
        """Generate detailed feedback for a question"""
        if is_correct:
            base_feedback = "Correct! "
        else:
            base_feedback = "Incorrect. "
        
        # Add explanation if available
        explanation = question.get('explanation', '')
        if explanation:
            base_feedback += explanation
        else:
            # If no explanation, provide the correct answer
            correct_answer = question.get('correct_answer', '')
            if not is_correct and correct_answer:
                base_feedback += f"The correct answer is: {correct_answer}"
        
        return base_feedback