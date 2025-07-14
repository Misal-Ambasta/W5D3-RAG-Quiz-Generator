/**
 * Quiz Results Component
 * Displays quiz results with correct/incorrect answers and explanations
 */

import type { QuizQuestion, QuizResult } from '../store/sessionStore';

interface QuizResultsProps {
  questions: QuizQuestion[];
  results: QuizResult[];
  userAnswers: Record<number, string>;
  onRetakeQuiz: () => void;
  onNewQuiz: () => void;
}

const QuizResults = ({
  questions,
  results,
  userAnswers,
  onRetakeQuiz,
  onNewQuiz,
}: QuizResultsProps) => {
  // Calculate overall score
  const correctAnswers = results.filter(result => result.is_correct).length;
  const totalQuestions = questions.length;
  const scorePercentage = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;
  
  // Get question by ID
  const getQuestionById = (questionId: number) => {
    return questions.find(question => question.id === questionId);
  };
  
  // Format response time
  const formatResponseTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };
  
  // Format question type
  const formatQuestionType = (type: string | undefined) => {
    if (!type) return '';
    return type.replace('_', ' ');
  };
  
  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-2">Quiz Results</h2>
      
      {/* Overall score */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex justify-between items-center mb-2">
          <span className="text-lg font-medium">Your Score</span>
          <span className="text-lg font-bold">
            {correctAnswers} / {totalQuestions} ({scorePercentage.toFixed(0)}%)
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${scorePercentage >= 70 ? 'bg-green-600' : scorePercentage >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${scorePercentage}%` }}
          ></div>
        </div>
      </div>
      
      {/* Question results */}
      <div className="space-y-6">
        {questions.map((question) => {
          const result = results.find(r => r.question_id === question.id);
          const userAnswer = userAnswers[question.id] || 'No answer provided';
          const isCorrect = result?.is_correct || false;
          const questionType = question.question_type || question.type;
          
          return (
            <div 
              key={question.id}
              className={`p-4 rounded-lg border ${isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-md font-medium">{question.question}</h3>
                  <span className="text-xs text-gray-500">{formatQuestionType(questionType)}</span>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${isCorrect ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {isCorrect ? 'Correct' : 'Incorrect'}
                </span>
              </div>
              
              <div className="mt-3 text-sm">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="font-medium text-gray-700">Your Answer:</p>
                    <p className={`mt-1 ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
                      {userAnswer}
                    </p>
                  </div>
                  
                  <div>
                    <p className="font-medium text-gray-700">Correct Answer:</p>
                    <p className="mt-1 text-green-700">{question.correct_answer}</p>
                  </div>
                </div>
                
                {question.explanation && (
                  <div className="mt-3">
                    <p className="font-medium text-gray-700">Explanation:</p>
                    <p className="mt-1 text-gray-600">{question.explanation}</p>
                  </div>
                )}
                
                {result && (
                  <div className="mt-3 text-xs text-gray-500">
                    Response time: {formatResponseTime(result.response_time_ms)}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Actions */}
      <div className="mt-8 flex space-x-4">
        <button
          onClick={onRetakeQuiz}
          className="flex-1 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-100 rounded-md hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Retake Quiz
        </button>
        
        <button
          onClick={onNewQuiz}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          New Quiz
        </button>
      </div>
    </div>
  );
};

export default QuizResults;