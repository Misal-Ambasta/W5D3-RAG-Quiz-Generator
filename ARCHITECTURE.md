# Architecture Documentation - Automated Quiz Generator

## System Architecture Overview

The Automated Quiz Generator is built using a modular architecture that separates concerns and allows for easy maintenance and extension. The system is composed of several key components that work together to provide the quiz generation functionality.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Layer (FastAPI)                       │
└───────┬───────────────┬────────────────┬──────────────┬─────────┘
        │               │                │              │
        ▼               ▼                ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
│  Document    │ │    Quiz     │ │   Session    │ │   Feedback   │
│  Processing  │ │ Generation  │ │  Management  │ │  Collection  │
└───────┬──────┘ └──────┬──────┘ └───────┬──────┘ └───────┬──────┘
        │               │                │               │
        └───────┬───────┴────────┬──────┴───────┬───────┘
                │                │              │
                ▼                ▼              ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │    Hybrid    │ │     LLM      │ │   Database   │
        │ RAG System   │ │ Integration  │ │   (SQLite)   │
        └───────┬──────┘ └──────────────┘ └──────────────┘
                │
                ▼
        ┌──────────────┐
        │    Redis     │
        │    Cache     │
        └──────────────┘
```

## Component Descriptions

### 1. Frontend (React)

The frontend is built using React and provides the user interface for the application. It includes:

- Document upload interface
- Quiz taking interface
- Results display
- Feedback collection forms

The frontend communicates with the backend through the API layer using fetch API calls.

### 2. API Layer (FastAPI)

The API layer is built using FastAPI and provides RESTful endpoints for the frontend to interact with. It includes routes for:

- Document upload and processing
- Quiz generation
- Session management
- Answer validation
- Feedback collection

### 3. Document Processing

This component handles the ingestion and processing of educational documents. It includes:

- File parsing (PDF, DOCX, TXT, HTML)
- Content extraction
- Chunking with context preservation
- Metadata extraction

### 4. Quiz Generation

This component is responsible for generating quizzes based on the processed documents. It includes:

- Learning objective identification
- Question generation using LLM
- Answer validation
- Explanation generation

### 5. Session Management

This component manages quiz sessions and user interactions. It includes:

- Session creation and tracking
- Answer submission and validation
- Results compilation
- Session cleanup

### 6. Feedback Collection

This component collects and stores user feedback on quizzes and questions. It includes:

- Quiz feedback collection
- Question feedback collection
- Feedback storage and retrieval

### 7. Hybrid RAG System

This component implements the Retrieval-Augmented Generation system. It includes:

- Dense retrieval using embeddings
- Sparse retrieval using BM25
- Hybrid search combining both approaches
- Cross-encoder reranking

### 8. LLM Integration

This component integrates with the Google Gemini LLM for various AI tasks. It includes:

- Question generation
- Learning objective extraction
- Answer explanation generation
- Tool calling for educational APIs

### 9. Database (SQLite)

The database stores all persistent data for the application. It includes tables for:

- Documents and chunks
- Learning objectives
- Quiz questions and answers
- Sessions
- User feedback

### 10. Redis Cache

The Redis cache improves performance by caching frequently accessed data. It caches:

- Generated quizzes
- Frequently accessed document chunks
- Learning objectives

## Data Flow

### Document Upload Flow

1. User uploads document through frontend
2. API receives document and passes to document processing
3. Document is parsed and chunked
4. Chunks are stored in SQLite
5. Embeddings are generated and stored in vector database
6. Learning objectives are extracted and stored
7. Confirmation is returned to frontend

### Quiz Generation Flow

1. User requests quiz on specific topic
2. API receives request and creates session
3. Hybrid RAG system retrieves relevant chunks
4. LLM generates questions based on chunks
5. Questions are validated and stored
6. Quiz is cached in Redis
7. Quiz is returned to frontend

### Quiz Taking Flow

1. User answers question in frontend
2. Answer is sent to API
3. Answer is validated and result stored
4. Feedback is generated if needed
5. Result is returned to frontend
6. Process repeats for each question
7. Final results are compiled and displayed

## Technology Stack Details

### Backend

- **Language**: Python 3.9+
- **Web Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Database**: SQLite
- **Cache**: Redis
- **Vector Database**: Weaviate or Qdrant
- **Embedding Models**: Sentence Transformers (all-MiniLM-L6-v2)
- **Reranking Models**: Cross-encoder (ms-marco-MiniLM-L-6-v2)
- **LLM**: Google Gemini

### Frontend

- **Framework**: React
- **Styling**: Tailwind CSS
- **State Management**: Custom hooks
- **HTTP Client**: Fetch API

## Scalability Considerations

The current architecture is designed for an MVP and has some limitations for scaling:

- SQLite is used for simplicity but would need to be replaced with a more robust database for production
- The system uses local file storage which would need to be replaced with cloud storage for production
- No authentication or user management is implemented
- The system is designed to run locally and would need additional configuration for deployment

## Future Extensions

The architecture is designed to allow for future extensions, including:

- User authentication and management
- Analytics dashboard for instructors
- More sophisticated question generation
- Integration with learning management systems
- Multi-modal content support (images, videos)
- Adaptive difficulty based on user performance