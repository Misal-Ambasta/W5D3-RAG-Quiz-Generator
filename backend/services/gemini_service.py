import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import re

from app.core.config import settings

class GeminiService:
    """Service for integrating with Google Gemini AI for educational content generation"""
    
    def __init__(self):
        self.api_key = settings.google_api_key
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        self.text_model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Generation config
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 2048,
        }
    
    def generate_quiz_questions(self, content: str, num_questions: int = 5, 
                               difficulty: str = 'medium', 
                               question_types: List[str] = None) -> Dict[str, Any]:
        """Generate quiz questions from content using Gemini"""
        if question_types is None:
            question_types = ['multiple_choice', 'true_false', 'short_answer', 'fill_in_the_blank']
        
        prompt = f"""
        Based on the following content, generate {num_questions} educational quiz questions.
        
        Content:
        {content}
        
        Requirements:
        - Difficulty level: {difficulty}
        - Question types: {', '.join(question_types)}
        - Each question should test understanding of key concepts
        - For multiple choice questions, provide 4 options with one correct answer
        - For true/false questions, provide a clear statement
        - For short answer questions, provide a concise expected answer
        - For fill-in-the-blank questions, provide the complete sentence with the blank indicated by '____'
        - Include explanations for all answers
        - Ensure questions are directly related to the content provided
        - Questions must be clear, concise, and grammatically correct
        - Multiple choice questions must have exactly one correct answer
        - All questions must end with a question mark (except fill-in-the-blank)
        
        Return the response in the following JSON format:
        {{
            "questions": [
                {{
                    "id": "q1",
                    "type": "multiple_choice",
                    "question": "Question text here?",
                    "options": {{
                        "A": "Option A",
                        "B": "Option B", 
                        "C": "Option C",
                        "D": "Option D"
                    }},
                    "correct_answer": "A",
                    "explanation": "Explanation of why this is correct",
                    "difficulty": "{difficulty}",
                    "topic": "Main topic covered"
                }}
            ]
        }}
        """
        
        try:
            response = self.text_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            
            # Extract JSON from response
            response_text = response.text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                questions_data = json.loads(json_match.group())
                # Validate the generated questions
                validated_questions = self.validate_questions(questions_data.get('questions', []))
                return {
                    'success': True,
                    'questions': validated_questions,
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'difficulty': difficulty,
                        'num_questions': len(questions_data.get('questions', [])),
                        'question_types': question_types
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to parse JSON response from Gemini',
                    'raw_response': response_text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'difficulty': difficulty,
                    'num_questions': 0
                }
            }
    
    def extract_learning_objectives(self, content: str, 
                                  max_objectives: int = 5) -> Dict[str, Any]:
        """Extract learning objectives from content using Gemini"""
        prompt = f"""
        Analyze the following educational content and extract key learning objectives.
        
        Content:
        {content}
        
        Requirements:
        - Extract up to {max_objectives} clear, specific learning objectives
        - Each objective should describe what a student will be able to do after studying this content
        - Use action verbs like "understand", "explain", "analyze", "apply", "evaluate"
        - Organize objectives by complexity level (basic, intermediate, advanced)
        - Include relevant topics and subtopics
        
        Return the response in the following JSON format:
        {{
            "learning_objectives": [
                {{
                    "id": "obj1",
                    "objective": "Students will be able to...",
                    "level": "basic|intermediate|advanced",
                    "topic": "Main topic area",
                    "subtopics": ["subtopic1", "subtopic2"],
                    "bloom_taxonomy": "remember|understand|apply|analyze|evaluate|create"
                }}
            ],
            "content_summary": "Brief summary of the content",
            "difficulty_assessment": "overall difficulty level"
        }}
        """
        
        try:
            response = self.text_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            
            # Extract JSON from response
            response_text = response.text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                objectives_data = json.loads(json_match.group())
                return {
                    'success': True,
                    'learning_objectives': objectives_data.get('learning_objectives', []),
                    'content_summary': objectives_data.get('content_summary', ''),
                    'difficulty_assessment': objectives_data.get('difficulty_assessment', 'medium'),
                    'metadata': {
                        'extracted_at': datetime.now().isoformat(),
                        'num_objectives': len(objectives_data.get('learning_objectives', []))
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to parse JSON response from Gemini',
                    'raw_response': response_text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'num_objectives': 0
                }
            }
    
    def generate_answer_explanations(self, question: str, correct_answer: str, 
                                   incorrect_answers: List[str] = None,
                                   context: str = None) -> Dict[str, Any]:
        """Generate detailed answer explanations using Gemini"""
        prompt = f"""
        Provide a detailed explanation for the following question and answer.
        
        Question: {question}
        Correct Answer: {correct_answer}
        """
        
        if incorrect_answers:
            prompt += f"\nIncorrect Options: {', '.join(incorrect_answers)}"
        
        if context:
            prompt += f"\nContext: {context}"
        
        prompt += """
        
        Requirements:
        - Explain why the correct answer is right
        - If incorrect options are provided, explain why they are wrong
        - Use clear, educational language
        - Include relevant background information
        - Make the explanation helpful for learning
        
        Return the response in the following JSON format:
        {
            "explanation": {
                "correct_answer_explanation": "Why this answer is correct",
                "incorrect_answers_explanation": {
                    "option": "Why this option is incorrect"
                },
                "key_concepts": ["concept1", "concept2"],
                "additional_context": "Additional helpful information",
                "difficulty_level": "easy|medium|hard"
            }
        }
        """
        
        try:
            response = self.text_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            
            # Extract JSON from response
            response_text = response.text
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                explanation_data = json.loads(json_match.group())
                return {
                    'success': True,
                    'explanation': explanation_data.get('explanation', {}),
                    'metadata': {
                        'generated_at': datetime.now().isoformat(),
                        'question': question,
                        'correct_answer': correct_answer
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to parse JSON response from Gemini',
                    'raw_response': response_text
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'question': question
                }
            }
    
    def generate_structured_quiz(self, content: str, 
                               quiz_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured quiz with specific format requirements"""
        num_questions = quiz_config.get('num_questions', 5)
        difficulty = quiz_config.get('difficulty', 'medium')
        question_format = quiz_config.get('format', 'multiple_choice')
        include_explanations = quiz_config.get('include_explanations', True)
        
        prompt = f"""
        Create a structured educational quiz based on the following content.
        
        Content:
        {content}
        
        Quiz Configuration:
        - Number of questions: {num_questions}
        - Difficulty level: {difficulty}
        - Question format: {question_format}
        - Include explanations: {include_explanations}
        
        Requirements:
        - Follow the exact format specified
        - Ensure questions are educationally valuable
        - Vary question difficulty appropriately
        - Include metadata for each question
        
        Return a structured JSON response with the quiz data.
        """
        
        try:
            response = self.text_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            
            return {
                'success': True,
                'quiz_data': response.text,
                'config': quiz_config,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'content_length': len(content),
                    'model': 'models/gemini-2.0-flash'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'config': quiz_config,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'model': 'models/gemini-2.0-flash'
                }
            }
    
    def validate_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and filter quiz questions for quality"""
        validated_questions = []
        
        for question in questions:
            # Initialize validation score
            validation_score = 1.0
            question_type = question.get('type', '').lower()
            question_text = question.get('question', '')
            
            # Basic validation checks
            if not question_text:
                continue  # Skip questions with no text
            
            # Check if question ends with question mark (except fill-in-the-blank)
            if question_type != 'fill_in_the_blank' and not question_text.strip().endswith('?'):
                validation_score -= 0.2
                question['question'] = question_text.strip() + '?'  # Fix it
            
            # Validate multiple choice questions
            if question_type == 'multiple_choice':
                options = question.get('options', {})
                correct_answer = question.get('correct_answer', '')
                
                # Check if options exist
                if not options or len(options) < 2:
                    validation_score -= 0.5
                    continue  # Skip invalid MCQs
                
                # Check if correct answer is valid
                if not correct_answer or correct_answer not in options:
                    validation_score -= 0.5
                    continue  # Skip invalid MCQs
            
            # Validate true/false questions
            elif question_type == 'true_false':
                correct_answer = question.get('correct_answer', '')
                if correct_answer.lower() not in ['true', 'false']:
                    validation_score -= 0.3
                    # Fix it if possible
                    if 't' in correct_answer.lower():
                        question['correct_answer'] = 'True'
                    elif 'f' in correct_answer.lower():
                        question['correct_answer'] = 'False'
                    else:
                        continue  # Skip invalid T/F
            
            # Validate fill-in-the-blank questions
            elif question_type == 'fill_in_the_blank':
                if '____' not in question_text and '_____' not in question_text and '__' not in question_text:
                    validation_score -= 0.3
                    # Try to fix it
                    correct_answer = question.get('correct_answer', '')
                    if correct_answer and correct_answer in question_text:
                        question['question'] = question_text.replace(correct_answer, '____')
                    else:
                        continue  # Skip invalid fill-in-the-blank
            
            # Check for explanation
            if not question.get('explanation', ''):
                validation_score -= 0.1
            
            # Add validation score to question
            question['validation_score'] = round(max(0.0, validation_score), 2)
            
            # Only include questions with acceptable validation scores
            if question['validation_score'] >= 0.7:
                validated_questions.append(question)
        
        return validated_questions

    def generate_fallback_questions(self, content: str, num_questions: int = 3) -> List[Dict[str, Any]]:
        """Generate template-based fallback questions when quality is poor"""
        # Extract key sentences from content
        sentences = content.split('.')
        sentences = [s.strip() + '.' for s in sentences if len(s.strip()) > 30]
        
        fallback_questions = []
        
        # Generate simple true/false questions
        for i, sentence in enumerate(sentences[:num_questions]):
            if i >= num_questions:
                break
                
            question_id = f"fallback_q{i+1}"
            
            # Create a true/false question
            fallback_questions.append({
                "id": question_id,
                "type": "true_false",
                "question": f"Is the following statement true? {sentence}",
                "correct_answer": "True",  # Since we're using actual sentences
                "explanation": "This statement is directly from the source material.",
                "difficulty": "easy",
                "validation_score": 0.8,
                "is_fallback": True
            })
        
        return fallback_questions

    def function_calling_example(self, user_query: str) -> Dict[str, Any]:
        """Example of function calling with Gemini"""
        # Define available functions
        functions = [
            {
                "name": "generate_quiz",
                "description": "Generate a quiz based on content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content to generate quiz from"
                        },
                        "num_questions": {
                            "type": "integer",
                            "description": "Number of questions to generate"
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": ["easy", "medium", "hard"],
                            "description": "Difficulty level"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "extract_objectives",
                "description": "Extract learning objectives from content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The content to analyze"
                        },
                        "max_objectives": {
                            "type": "integer",
                            "description": "Maximum number of objectives to extract"
                        }
                    },
                    "required": ["content"]
                }
            }
        ]
        
        prompt = f"""
        You are an educational AI assistant. Based on the user query, determine which function to call and with what parameters.
        
        User Query: {user_query}
        
        Available Functions: {json.dumps(functions, indent=2)}
        
        Respond with the function call in JSON format.
        """
        
        try:
            response = self.text_model.generate_content(
                prompt,
                safety_settings=self.safety_settings,
                generation_config=self.generation_config
            )
            
            return {
                'success': True,
                'function_call': response.text,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'user_query': user_query
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'user_query': user_query
                }
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available Gemini models"""
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append({
                        'name': model.name,
                        'display_name': model.display_name,
                        'description': model.description,
                        'input_token_limit': model.input_token_limit,
                        'output_token_limit': model.output_token_limit
                    })
            
            return {
                'success': True,
                'models': models,
                'current_model': 'models/gemini-2.0-flash',
                'metadata': {
                    'retrieved_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'retrieved_at': datetime.now().isoformat()
                }
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Gemini API"""
        try:
            response = self.text_model.generate_content(
                "Hello, this is a test message. Please respond with 'Connection successful.'",
                safety_settings=self.safety_settings,
                generation_config={'max_output_tokens': 50}
            )
            
            return {
                'success': True,
                'response': response.text,
                'metadata': {
                    'tested_at': datetime.now().isoformat(),
                    'model': 'models/gemini-2.0-flash'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'tested_at': datetime.now().isoformat(),
                    'model': 'models/gemini-2.0-flash'
                }
            }

# Global instance
gemini_service = GeminiService()