/**
 * Session Store
 * Manages session state for the quiz application
 */

import { useState, useEffect } from 'react';

// Types
export interface Session {
  session_id: string;
  created_at: string;
  expires_at: string;
  status: string;
  document_id?: number;
  topic?: string;
  metadata?: Record<string, any>;
}

export interface QuizQuestion {
  id: number;
  question: string;
  question_type?: string;
  type?: string;
  options?: string[];
  correct_answer: string;
  explanation?: string;
}

export interface QuizResult {
  question_id: number;
  user_answer: string;
  is_correct: boolean;
  response_time_ms: number;
  explanation?: string;
}

// Simple store implementation
export const useSessionStore = () => {
  // Session state
  const [session, setSession] = useState<Session | null>(null);
  const [quizQuestions, setQuizQuestions] = useState<QuizQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [quizResults, setQuizResults] = useState<QuizResult[]>([]);
  const [isQuizCompleted, setIsQuizCompleted] = useState(false);
  
  // Load data from localStorage on mount
  useEffect(() => {
    const savedSession = localStorage.getItem('quiz_session');
    const savedQuestions = localStorage.getItem('quiz_questions');
    const savedAnswers = localStorage.getItem('quiz_answers');
    const savedResults = localStorage.getItem('quiz_results');
    
    if (savedSession) {
      try {
        setSession(JSON.parse(savedSession));
      } catch (error) {
        console.error('Error parsing saved session:', error);
      }
    }
    
    if (savedQuestions) {
      try {
        setQuizQuestions(JSON.parse(savedQuestions));
      } catch (error) {
        console.error('Error parsing saved questions:', error);
      }
    }
    
    if (savedAnswers) {
      try {
        setUserAnswers(JSON.parse(savedAnswers));
      } catch (error) {
        console.error('Error parsing saved answers:', error);
      }
    }
    
    if (savedResults) {
      try {
        setQuizResults(JSON.parse(savedResults));
        setIsQuizCompleted(true);
      } catch (error) {
        console.error('Error parsing saved results:', error);
      }
    }
  }, []);
  
  // Save session to localStorage when it changes
  useEffect(() => {
    if (session) {
      localStorage.setItem('quiz_session', JSON.stringify(session));
    }
  }, [session]);
  
  // Save quiz questions to localStorage when they change
  useEffect(() => {
    if (quizQuestions.length > 0) {
      localStorage.setItem('quiz_questions', JSON.stringify(quizQuestions));
    }
  }, [quizQuestions]);
  
  // Save user answers to localStorage when they change
  useEffect(() => {
    if (Object.keys(userAnswers).length > 0) {
      localStorage.setItem('quiz_answers', JSON.stringify(userAnswers));
    }
  }, [userAnswers]);
  
  // Save quiz results to localStorage when they change
  useEffect(() => {
    if (quizResults.length > 0) {
      localStorage.setItem('quiz_results', JSON.stringify(quizResults));
    }
  }, [quizResults]);
  
  // Actions
  const setSessionData = (newSession: Session) => {
    setSession(newSession);
  };
  
  const clearSession = () => {
    setSession(null);
    setQuizQuestions([]);
    setCurrentQuestionIndex(0);
    setUserAnswers({});
    setQuizResults([]);
    setIsQuizCompleted(false);
    localStorage.removeItem('quiz_session');
    localStorage.removeItem('quiz_questions');
    localStorage.removeItem('quiz_answers');
    localStorage.removeItem('quiz_results');
  };
  
  const setQuizData = (questions: QuizQuestion[]) => {
    setQuizQuestions(questions);
    setCurrentQuestionIndex(0);
    setUserAnswers({});
    setQuizResults([]);
    setIsQuizCompleted(false);
  };
  
  const saveAnswer = (questionId: number, answer: string) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: answer,
    }));
  };
  
  const nextQuestion = () => {
    if (currentQuestionIndex < quizQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    } else {
      setIsQuizCompleted(true);
    }
  };
  
  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };
  
  const setResults = (results: QuizResult[]) => {
    setQuizResults(results);
    setIsQuizCompleted(true);
  };
  
  return {
    // State
    session,
    quizQuestions,
    currentQuestionIndex,
    userAnswers,
    quizResults,
    isQuizCompleted,
    
    // Computed
    currentQuestion: quizQuestions[currentQuestionIndex],
    hasNextQuestion: currentQuestionIndex < quizQuestions.length - 1,
    hasPreviousQuestion: currentQuestionIndex > 0,
    progress: quizQuestions.length ? (currentQuestionIndex + 1) / quizQuestions.length : 0,
    
    // Actions
    setSessionData,
    clearSession,
    setQuizData,
    saveAnswer,
    nextQuestion,
    previousQuestion,
    setResults,
    setIsQuizCompleted,
  };
};