import { useState, useEffect } from 'react';
import './App.css';
import DocumentUpload from './components/DocumentUpload';
import QuizInterface from './components/QuizInterface';
import QuizResults from './components/QuizResults';
import { useSessionStore, type Session } from './store/sessionStore';
import apiClient from './api/apiClient';

function App() {
  // Application state
  const [currentView, setCurrentView] = useState<'upload' | 'quiz' | 'results'>('upload');
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [topic, setTopic] = useState<string>('');
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
      
      // Generate quiz using apiClient
      const quizData = await apiClient.generateQuiz(topic, 5, 'medium');
      
      // Set quiz data in store
      sessionStore.setQuizData((quizData as any).quiz_data.questions);
      
      // Navigate to quiz view
      setCurrentView('quiz');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle answer submission
  const handleAnswerSubmit = async (questionId: number, answer: string) => {
    if (!sessionStore.session) return;
    
    try {
      // Save answer locally
      sessionStore.saveAnswer(questionId, answer);
      
      // Submit answer to API
      await apiClient.submitAnswer(sessionStore.session.session_id, questionId, answer);
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };
  
  // Handle quiz completion
  const handleQuizComplete = async () => {
    if (!sessionStore.session) return;
    
    setIsLoading(true);
    
    try {
      // Get quiz results
      const resultsData = await apiClient.getQuizResults(sessionStore.session.session_id);
      
      // Set results in store
      sessionStore.setResults((resultsData as any).results);
      
      // Navigate to results view
      setCurrentView('results');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
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
