/**
 * Quiz Interface Component
 * Displays quiz questions and handles user answers
 */

import { useState, useEffect } from 'react';
import type { QuizQuestion } from '../store/sessionStore';

interface QuizInterfaceProps {
  questions: QuizQuestion[];
  currentQuestionIndex: number;
  userAnswers: Record<number, string>;
  onAnswerSubmit: (questionId: number, answer: string) => void;
  onNextQuestion: () => void;
  onPreviousQuestion: () => void;
  onComplete: () => void;
  isCompleted: boolean;
}

const QuizInterface = ({
  questions,
  currentQuestionIndex,
  userAnswers,
  onAnswerSubmit,
  onNextQuestion,
  onPreviousQuestion,
  onComplete,
  isCompleted,
}: QuizInterfaceProps) => {
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  
  const currentQuestion = questions[currentQuestionIndex];
  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;
  
  // Reset selected answer when question changes
  useEffect(() => {
    if (currentQuestion) {
      const savedAnswer = userAnswers[currentQuestion.id] || '';
      setSelectedAnswer(savedAnswer);
    }
  }, [currentQuestion, userAnswers]);
  
  if (!currentQuestion) {
    return (
      <div className="p-6 bg-white rounded-lg shadow-md">
        <p className="text-center text-gray-600">No questions available</p>
      </div>
    );
  }
  
  const handleAnswerSelect = (answer: string) => {
    setSelectedAnswer(answer);
  };
  
  const handleSubmitAnswer = () => {
    if (selectedAnswer) {
      // const responseTime = Date.now() - timeStarted;
      onAnswerSubmit(currentQuestion.id, selectedAnswer);
      
      if (currentQuestionIndex < questions.length - 1) {
        onNextQuestion();
      } else {
        onComplete();
      }
    }
  };
  
  const renderQuestionContent = () => {
    switch (currentQuestion.question_type) {
      case 'multiple_choice':
        return (
          <div className="space-y-3">
            {currentQuestion.options?.map((option, index) => (
              <div key={index} className="flex items-center">
                <input
                  type="radio"
                  id={`option-${index}`}
                  name="quiz-option"
                  value={option}
                  checked={selectedAnswer === option}
                  onChange={() => handleAnswerSelect(option)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                  disabled={isCompleted}
                />
                <label htmlFor={`option-${index}`} className="ml-2 block text-gray-700">
                  {option}
                </label>
              </div>
            ))}
          </div>
        );
        
      case 'true_false':
        return (
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="radio"
                id="option-true"
                name="quiz-option"
                value="True"
                checked={selectedAnswer === 'True'}
                onChange={() => handleAnswerSelect('True')}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                disabled={isCompleted}
              />
              <label htmlFor="option-true" className="ml-2 block text-gray-700">
                True
              </label>
            </div>
            <div className="flex items-center">
              <input
                type="radio"
                id="option-false"
                name="quiz-option"
                value="False"
                checked={selectedAnswer === 'False'}
                onChange={() => handleAnswerSelect('False')}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                disabled={isCompleted}
              />
              <label htmlFor="option-false" className="ml-2 block text-gray-700">
                False
              </label>
            </div>
          </div>
        );
        
      case 'short_answer':
      case 'fill_in_blank':
        return (
          <div>
            <textarea
              value={selectedAnswer}
              onChange={(e) => handleAnswerSelect(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Type your answer here..."
              disabled={isCompleted}
            />
          </div>
        );
        
      default:
        return (
          <div className="text-center text-gray-600">
            Unsupported question type
          </div>
        );
    }
  };
  
  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-6">
        <div 
          className="bg-blue-600 h-2.5 rounded-full" 
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      
      {/* Question counter */}
      <div className="flex justify-between items-center mb-4">
        <span className="text-sm font-medium text-gray-500">
          Question {currentQuestionIndex + 1} of {questions.length}
        </span>
        <span className="text-sm font-medium text-gray-500">
          {currentQuestion.question_type.replace('_', ' ')}
        </span>
      </div>
      
      {/* Question */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          {currentQuestion.question}
        </h3>
        
        {renderQuestionContent()}
      </div>
      
      {/* Navigation buttons */}
      <div className="flex justify-between mt-6">
        <button
          onClick={onPreviousQuestion}
          disabled={currentQuestionIndex === 0 || isCompleted}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed"
        >
          Previous
        </button>
        
        <button
          onClick={handleSubmitAnswer}
          disabled={!selectedAnswer || isCompleted}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {currentQuestionIndex < questions.length - 1 ? 'Next' : 'Finish Quiz'}
        </button>
      </div>
    </div>
  );
};

export default QuizInterface;