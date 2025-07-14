import { useState, useEffect } from 'react';
import './App.css';
import DocumentUpload from './components/DocumentUpload';
import QuizInterface from './components/QuizInterface';
import QuizResults from './components/QuizResults';
import { useSessionStore, type Session } from './store/sessionStore';
import apiClient from './api/apiClient';

interface QuizResult {
  question_id: number;
  is_correct: boolean;
  user_answer: string;
  correct_answer: string;
  explanation: string;
  response_time_ms: number;
}

function App() {
  // Application state
  const [currentView, setCurrentView] = useState<'upload' | 'quiz' | 'results'>('upload');
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [topic, setTopic] = useState<string>('');
  const [difficulty, setDifficulty] = useState<string>('easy');
  const [questionCount, setQuestionCount] = useState<number>(5);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  // Session store
  const sessionStore = useSessionStore();
  
  // Check for existing session on mount
  useEffect(() => {
    if (sessionStore.session) {
      // If we have quiz questions, go to quiz view
      if (sessionStore.quizQuestions.length > 0) {
        setCurrentView(sessionStore.isQuizCompleted ? 'results' : 'quiz');
      }
    }
  }, []);
  
  // Handle document upload success
  const handleUploadSuccess = (docId: number, _filename: string) => {
    setDocumentId(docId);
    setError(null);
    
    // Show topic input
    setCurrentView('upload');
  };
  
  // Handle document upload error
  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };
  
  // Handle topic submission and quiz generation
  const handleGenerateQuiz = async () => {
    if (!documentId) {
      setError('Please upload a document first');
      return;
    }
    
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Create a session using apiClient
      const sessionData = await apiClient.createSession(documentId, topic, {});
      sessionStore.setSessionData(sessionData as unknown as Session);
      
      // Generate quiz using apiClient with selected difficulty and question count
      const quizData = await apiClient.generateQuiz(topic, questionCount, difficulty);
      
      // Set quiz data in store
      const questions = (quizData as any).quiz_data.questions.map((q: any) => ({
        ...q,
        // Ensure question_type is set for backward compatibility
        question_type: q.question_type || q.type
      }));
      sessionStore.setQuizData(questions);
      
      // Navigate to quiz view
      setCurrentView('quiz');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle answer submission
  const handleAnswerSubmit = (questionId: number, answer: string) => {
    // Save answer locally only
    sessionStore.saveAnswer(questionId, answer);
  };
  
  // Handle quiz completion
  const handleQuizComplete = async () => {
    setIsLoading(true);
    try {
      // Generate results locally by comparing user answers with correct answers
      const results: QuizResult[] = [];
      const userAnswers = sessionStore.userAnswers;
      const quizQuestions = sessionStore.quizQuestions;
      
      quizQuestions.forEach(question => {
        const userAnswer = userAnswers[question.id];
        const isCorrect = userAnswer === question.correct_answer;
        
        results.push({
          question_id: question.id,
          is_correct: isCorrect,
          user_answer: userAnswer || '',
          correct_answer: question.correct_answer,
          explanation: question.explanation || '',
          response_time_ms: 0 // We don't have response time data when generating locally
        });
      });
      
      // Set results in session store
      sessionStore.setResults(results);
      sessionStore.setIsQuizCompleted(true);
      
      // Navigate to results view
      setCurrentView('results');
    } catch (error) {
      console.error('Error completing quiz:', error);
      setError('Failed to complete quiz. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle retake quiz
  const handleRetakeQuiz = () => {
    sessionStore.setIsQuizCompleted(false);
    setCurrentView('quiz');
  };
  
  // Handle new quiz
  const handleNewQuiz = () => {
    sessionStore.clearSession();
    setDocumentId(null);
    setTopic('');
    setCurrentView('upload');
  };
  
  // Render upload view
  const renderUploadView = () => (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-center mb-6">Automated Quiz Generator</h1>
      
      <DocumentUpload 
        onUploadSuccess={handleUploadSuccess} 
        onUploadError={handleUploadError} 
      />
      
      {documentId && (
        <div className="mt-6 p-6 bg-white rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Generate Quiz</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter Topic or Learning Objective
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Photosynthesis, World War II, Quadratic Equations"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficulty
              </label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of Questions
              </label>
              <select
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[5, 10, 15, 20, 25].map(count => (
                  <option key={count} value={count}>{count}</option>
                ))}
              </select>
            </div>
          </div>
          
          <button
            onClick={handleGenerateQuiz}
            disabled={isLoading}
            className="w-full px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Generating Quiz...' : 'Generate Quiz'}
          </button>
        </div>
      )}
      
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
  
  // Render quiz view
  const renderQuizView = () => (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-center mb-6">Quiz</h1>
      
      <QuizInterface
        questions={sessionStore.quizQuestions}
        currentQuestionIndex={sessionStore.currentQuestionIndex}
        userAnswers={sessionStore.userAnswers}
        onAnswerSubmit={handleAnswerSubmit}
        onNextQuestion={sessionStore.nextQuestion}
        onPreviousQuestion={sessionStore.previousQuestion}
        onComplete={handleQuizComplete}
        isCompleted={sessionStore.isQuizCompleted}
      />
      
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
  
  // Render results view
  const renderResultsView = () => (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-center mb-6">Quiz Results</h1>
      
      <QuizResults
        questions={sessionStore.quizQuestions}
        results={sessionStore.quizResults}
        userAnswers={sessionStore.userAnswers}
        onRetakeQuiz={handleRetakeQuiz}
        onNewQuiz={handleNewQuiz}
      />
    </div>
  );
  
  // Render current view
  const renderCurrentView = () => {
    switch (currentView) {
      case 'upload':
        return renderUploadView();
      case 'quiz':
        return renderQuizView();
      case 'results':
        return renderResultsView();
      default:
        return renderUploadView();
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      {renderCurrentView()}
    </div>
  );
}

export default App;
