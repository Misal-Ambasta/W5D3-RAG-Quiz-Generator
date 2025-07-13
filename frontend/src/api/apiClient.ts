/**
 * API Client for Quiz Generator
 * Centralized API client using Axios
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorMessage = error.response?.data?.detail || `API error: ${error.response?.status || 'unknown'}`;
    return Promise.reject(new Error(errorMessage));
  }
);

// API client with methods for all endpoints
const apiClient = {
  // Document upload
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post('/langchain/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Session management
  createSession: async (documentId: number, topic: string, metadata: Record<string, any> = {}) => {
    return api.post('/sessions', {
      document_id: documentId,
      topic,
      metadata,
    });
  },
  
  getSession: async (sessionId: string) => {
    return api.get(`/sessions/${sessionId}`);
  },
  
  // Quiz generation and submission
  generateQuiz: async (topic: string, questionCount: number = 5, difficulty: string = 'medium') => {
    return api.post('/langchain/generate-quiz', {
      topic,
      question_count: questionCount,
      difficulty,
    });
  },
  
  submitAnswer: async (sessionId: string, questionId: number, userAnswer: string) => {
    return api.post(`/sessions/${sessionId}/answers`, {
      question_id: questionId,
      user_answer: userAnswer,
    });
  },
  
  getQuizResults: async (sessionId: string) => {
    return api.get(`/sessions/${sessionId}/results`);
  },
  
  // Feedback
  submitQuizFeedback: async (sessionId: string, rating: number, feedback: string) => {
    return api.post('/feedback/quiz', {
      session_id: sessionId,
      rating,
      feedback,
    });
  },
  
  submitQuestionFeedback: async (questionId: number, rating: number, feedback: string) => {
    return api.post('/feedback/question', {
      question_id: questionId,
      rating,
      feedback,
    });
  },
};

export default apiClient