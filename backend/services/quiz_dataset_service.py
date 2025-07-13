import json
import os
import random
from typing import List, Dict, Optional, Any
from pathlib import Path

class QuizDatasetService:
    """Service for loading and querying educational quiz datasets"""
    
    def __init__(self, data_path: str = "backend/data/quiz_questions.json"):
        self.data_path = data_path
        self.quiz_data: Dict[str, Any] = {}
        self.categories: List[str] = []
        self.releases: List[str] = []
        self.load_quiz_data()
    
    def load_quiz_data(self) -> None:
        """Load educational quiz JSONs from the data directory"""
        try:
            # Resolve the path relative to the project root
            if os.path.exists(self.data_path):
                file_path = self.data_path
            else:
                # Try relative to current working directory
                file_path = os.path.join(os.getcwd(), self.data_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                self.quiz_data = json.load(f)
            
            # Extract categories and releases for filtering
            self._extract_metadata()
            print(f"Loaded {len(self.quiz_data)} quiz questions from {file_path}")
            
        except FileNotFoundError:
            print(f"Quiz data file not found at {self.data_path}")
            self.quiz_data = {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            self.quiz_data = {}
    
    def _extract_metadata(self) -> None:
        """Extract unique categories and releases from the dataset"""
        categories = set()
        releases = set()
        
        for question_data in self.quiz_data.values():
            if 'category' in question_data:
                categories.add(question_data['category'])
            
            # Extract 3GPP release from question text
            question_text = question_data.get('question', '')
            if '[3GPP Release ' in question_text:
                try:
                    release = question_text.split('[3GPP Release ')[1].split(']')[0]
                    releases.add(release)
                except IndexError:
                    pass
        
        self.categories = sorted(list(categories))
        self.releases = sorted(list(releases))
    
    def search_by_topic(self, category: str) -> List[Dict[str, Any]]:
        """Search quiz questions by topic/category"""
        results = []
        for question_id, question_data in self.quiz_data.items():
            if question_data.get('category', '').lower() == category.lower():
                result = question_data.copy()
                result['question_id'] = question_id
                results.append(result)
        return results
    
    def search_by_difficulty(self, release: str) -> List[Dict[str, Any]]:
        """Search quiz questions by difficulty (3GPP release number)"""
        results = []
        for question_id, question_data in self.quiz_data.items():
            question_text = question_data.get('question', '')
            if f'[3GPP Release {release}]' in question_text:
                result = question_data.copy()
                result['question_id'] = question_id
                results.append(result)
        return results
    
    def search_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """Search quiz questions by keyword in question text"""
        results = []
        keyword_lower = keyword.lower()
        
        for question_id, question_data in self.quiz_data.items():
            question_text = question_data.get('question', '').lower()
            explanation = question_data.get('explanation', '').lower()
            
            if keyword_lower in question_text or keyword_lower in explanation:
                result = question_data.copy()
                result['question_id'] = question_id
                results.append(result)
        
        return results
    
    def get_random_questions(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get random quiz questions"""
        if not self.quiz_data:
            return []
        
        question_ids = list(self.quiz_data.keys())
        selected_ids = random.sample(question_ids, min(count, len(question_ids)))
        
        results = []
        for question_id in selected_ids:
            result = self.quiz_data[question_id].copy()
            result['question_id'] = question_id
            results.append(result)
        
        return results
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific question by ID"""
        if question_id in self.quiz_data:
            result = self.quiz_data[question_id].copy()
            result['question_id'] = question_id
            return result
        return None
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return self.categories
    
    def get_all_releases(self) -> List[str]:
        """Get all available 3GPP releases"""
        return self.releases
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get statistics about the dataset"""
        total_questions = len(self.quiz_data)
        questions_with_5_options = sum(1 for q in self.quiz_data.values() if 'option_5' in q)
        
        return {
            'total_questions': total_questions,
            'categories': self.categories,
            'releases': self.releases,
            'questions_with_5_options': questions_with_5_options,
            'questions_with_4_options': total_questions - questions_with_5_options
        }
    
    def filter_questions(self, category: Optional[str] = None, 
                        release: Optional[str] = None, 
                        keyword: Optional[str] = None,
                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Filter questions by multiple criteria"""
        results = []
        
        for question_id, question_data in self.quiz_data.items():
            # Category filter
            if category and question_data.get('category', '').lower() != category.lower():
                continue
            
            # Release filter
            if release:
                question_text = question_data.get('question', '')
                if f'[3GPP Release {release}]' not in question_text:
                    continue
            
            # Keyword filter
            if keyword:
                keyword_lower = keyword.lower()
                question_text = question_data.get('question', '').lower()
                explanation = question_data.get('explanation', '').lower()
                if keyword_lower not in question_text and keyword_lower not in explanation:
                    continue
            
            result = question_data.copy()
            result['question_id'] = question_id
            results.append(result)
        
        # Apply limit if specified
        if limit and len(results) > limit:
            results = random.sample(results, limit)
        
        return results

# Global instance
quiz_dataset_service = QuizDatasetService() 