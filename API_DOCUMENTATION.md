# API Documentation - Automated Quiz Generator

## Overview

This document provides details about the API endpoints available in the Automated Quiz Generator application. The API is built using FastAPI and provides endpoints for document upload, quiz generation, session management, answer validation, and feedback collection.

## Base URL

```
http://localhost:8000
```

## Authentication

The API does not currently require authentication. All endpoints are publicly accessible.

## API Endpoints

### Document Management

#### Upload Document

```
POST /langchain/upload
```

Uploads an educational document for processing and indexing.

**Request:**
- Form data with a file field named `file`
- Supported formats: PDF, DOCX, TXT, HTML

**Response:**
```json
{
  "document_id": 123,
  "filename": "example.pdf",
  "content_length": 12345,
  "chunks_created": 42,
  "learning_objectives": ["Understand concept X", "Apply formula Y"],
  "vector_indexed": { "status": "success" },
  "status": "processed"
}
```

### Quiz Generation

#### Generate Quiz

```
POST /langchain/generate-quiz
```

Generates a quiz based on the specified topic and parameters.

**Request:**
```json
{
  "topic": "Photosynthesis",
  "question_count": 5,
  "difficulty": "medium"
}
```

**Response:**
```json
{
  "quiz_data": {
    "topic": "Photosynthesis",
    "difficulty": "medium",
    "questions": [
      {
        "id": 1,
        "question": "What is the primary pigment in photosynthesis?",
        "question_type": "multiple_choice",
        "options": ["Chlorophyll", "Carotene", "Xanthophyll", "Phycocyanin"],
        "correct_answer": "Chlorophyll",
        "explanation": "Chlorophyll is the primary pigment that absorbs light energy used in photosynthesis."
      }
    ]
  },
  "cached": false
}
```

### Session Management

#### Create Session

```
POST /sessions
```

Creates a new quiz session.

**Request:**
```json
{
  "document_id": 123,
  "topic": "Photosynthesis",
  "metadata": {}
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-04-01T12:00:00Z",
  "expires_at": "2023-04-02T12:00:00Z",
  "status": "active",
  "document_id": 123,
  "topic": "Photosynthesis",
  "metadata": {}
}
```

#### Get Session

```
GET /sessions/{session_id}
```

Retrieves information about a specific session.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-04-01T12:00:00Z",
  "expires_at": "2023-04-02T12:00:00Z",
  "status": "active",
  "document_id": 123,
  "topic": "Photosynthesis",
  "metadata": {}
}
```

#### Update Session

```
PATCH /sessions/{session_id}
```

Updates an existing session.

**Request:**
```json
{
  "status": "completed",
  "metadata": {"score": 85}
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2023-04-01T12:00:00Z",
  "expires_at": "2023-04-02T12:00:00Z",
  "status": "completed",
  "document_id": 123,
  "topic": "Photosynthesis",
  "metadata": {"score": 85}
}
```

### Answer Submission and Validation

#### Submit Answer

```
POST /sessions/{session_id}/answers
```

Submits an answer for a quiz question.

**Request:**
```json
{
  "question_id": 1,
  "user_answer": "Chlorophyll"
}
```

**Response:**
```json
{
  "question_id": 1,
  "is_correct": true,
  "correct_answer": "Chlorophyll",
  "explanation": "Chlorophyll is the primary pigment that absorbs light energy used in photosynthesis.",
  "response_time_ms": 5000
}
```

#### Get Quiz Results

```
GET /sessions/{session_id}/results
```

Retrieves the results of a completed quiz.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_questions": 5,
  "correct_answers": 4,
  "score_percentage": 80,
  "results": [
    {
      "question_id": 1,
      "user_answer": "Chlorophyll",
      "is_correct": true,
      "response_time_ms": 5000,
      "explanation": "Chlorophyll is the primary pigment that absorbs light energy used in photosynthesis."
    }
  ]
}
```

### Feedback

#### Submit Quiz Feedback

```
POST /feedback/quiz
```

Submits feedback for an entire quiz.

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": 4,
  "feedback": "Good quiz, but some questions were too easy."
}
```

**Response:**
```json
{
  "feedback_id": 123,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating": 4,
  "feedback": "Good quiz, but some questions were too easy.",
  "created_at": "2023-04-01T12:30:00Z"
}
```

#### Submit Question Feedback

```
POST /feedback/question
```

Submits feedback for a specific question.

**Request:**
```json
{
  "question_id": 1,
  "rating": 3,
  "feedback": "This question was too basic."
}
```

**Response:**
```json
{
  "feedback_id": 456,
  "question_id": 1,
  "rating": 3,
  "feedback": "This question was too basic.",
  "created_at": "2023-04-01T12:35:00Z"
}
```

## Error Handling

The API returns appropriate HTTP status codes for different error scenarios:

- `400 Bad Request`: Invalid input parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a detail message explaining the error:

```json
{
  "detail": "Session not found"
}
```

## Rate Limiting

There is currently no rate limiting implemented on the API.

## Caching

The API uses Redis for caching frequently accessed data, including:

- Generated quizzes
- Frequently accessed document chunks
- Learning objectives

Cached data has appropriate TTL (Time To Live) values set for expiration.

## Health Check

```
GET /health
```

Returns the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "vector_store": "connected"
}
```