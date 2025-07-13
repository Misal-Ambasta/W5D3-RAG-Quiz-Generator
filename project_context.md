# Project Context: Automated Quiz Generator MVP

## 🎯 Project Overview
This is an MVP for an **Automated Quiz Generator** that helps instructors create personalized quizzes from educational documents. The system uses advanced RAG (Retrieval-Augmented Generation) techniques to understand content and generate relevant questions with explanations.

---

## 🏗️ Architecture Overview

### Core Components:
1. **Document Processing Pipeline** → Parse PDFs/DOCX, extract content
2. **Hybrid RAG System** → Dense + Sparse retrieval with reranking
3. **AI Question Generation** → LLM-powered quiz creation
4. **Caching Layer** → Redis for performance
5. **Persistent Storage** → SQLite for data persistence
6. **API Layer** → FastAPI for REST endpoints

### Technology Stack:
- **Backend**: FastAPI + Python
- **AI/LLM**: Google Gemini via LangChain 0.3.x
- **Vector DB**: Weaviate (primary) or Qdrant
- **Caching**: Redis (Docker)
- **Database**: SQLite
- **Search**: BM25 + Sentence Transformers + Cross-encoder reranking

---

## 📋 Key Features

### What the System Does:
✅ **Document Upload** → Instructors upload educational materials (PDF/DOCX)
✅ **Content Analysis** → Extract learning objectives and key concepts
✅ **Hybrid Search** → Combine dense embeddings + sparse retrieval
✅ **Smart Reranking** → Use cross-encoder models for better relevance
✅ **Question Generation** → Create MCQs, fill-blanks, true/false, short answers
✅ **Answer Validation** → Check answers and provide explanations
✅ **Session Management** → Anonymous sessions for quiz taking
✅ **Caching** → Cache frequently accessed content and generated quizzes

### What the System Does NOT Do:
❌ No user authentication/login system
❌ No user progress tracking across sessions
❌ No performance analytics or dashboards
❌ No manual scoring (system shows correct/incorrect only)
❌ No content validation pipeline
❌ No deployment configuration

---

## 🔧 Technical Implementation Details

### Data Flow:
1. **Upload** → Document → Parse → Extract metadata
2. **Process** → Chunk content → Generate embeddings → Store in vector DB
3. **Extract** → Learning objectives → Store in SQLite
4. **Generate** → User requests quiz → Hybrid search → Rerank → LLM generates questions
5. **Cache** → Store generated content in Redis
6. **Validate** → User answers → Check against stored answers → Provide feedback

### Key Technical Decisions:
- **SQLite**: Chosen for simplicity and persistence (no external DB needed)
- **Redis**: Caching layer with graceful degradation (system works without it)
- **Weaviate**: Preferred for built-in hybrid search capabilities
- **Anonymous Sessions**: UUID-based sessions stored in SQLite
- **Error Handling**: Comprehensive error handling with fallbacks

---

## 🎯 MVP Scope & Limitations

### MVP Focuses On:
- **Core RAG functionality** with hybrid search
- **Question generation** from educational content
- **Basic quiz taking** with immediate feedback
- **Caching optimization** for performance
- **Robust error handling** and graceful degradation

### MVP Limitations:
- **No user accounts** → Anonymous sessions only
- **No long-term tracking** → Sessions expire in 24 hours
- **Basic UI** → Simple demo interface
- **No advanced analytics** → Basic question quality validation only
- **Local deployment** → No cloud deployment setup

---

## 🚀 Development Approach

### Phase-by-Phase Development:
1. **Setup** → Environment, dependencies, Docker
2. **Core Pipeline** → Document processing, chunking, embeddings
3. **RAG System** → Hybrid search with reranking
4. **AI Integration** → LLM-powered question generation
5. **Validation** → Quality checks and error handling
6. **API Layer** → FastAPI endpoints with session management
7. **Testing** → Quality assurance and performance testing

### Key Design Patterns:
- **Graceful Degradation**: System works even if Redis fails
- **Fallback Strategies**: Multiple approaches for learning objectives and question quality
- **Modular Design**: Each component can be developed and tested independently
- **Error-First Approach**: Comprehensive error handling at every layer

---

## 📊 Success Metrics for MVP

### Technical Metrics:
- **Retrieval Quality**: Relevant content chunks retrieved for questions
- **Question Quality**: Generated questions make sense and are answerable
- **System Reliability**: Graceful handling of failures (Redis, LLM, etc.)
- **Performance**: Reasonable response times for quiz generation

### User Experience Metrics:
- **Content Processing**: Successfully parse and process educational documents
- **Quiz Generation**: Generate diverse question types with correct answers
- **Answer Validation**: Accurately check answers and provide explanations
- **Session Management**: Maintain quiz state throughout user session

---

## 🔍 Development Context

### Target Use Case:
An instructor uploads a PDF of lecture notes or textbook chapter. The system analyzes the content, identifies key learning objectives, and generates a quiz with multiple question types. Students take the quiz and get immediate feedback with explanations.

### Example Workflow:
1. Instructor uploads "Chapter 5: Photosynthesis.pdf"
2. System extracts learning objectives like "Understand light-dependent reactions"
3. System chunks content and creates embeddings
4. Student requests quiz on photosynthesis
5. System retrieves relevant chunks, generates 10 questions
6. Student answers questions, gets immediate feedback
7. System shows correct answers with explanations

### Key Challenges Addressed:
- **Content Understanding**: Using hybrid RAG to find relevant information
- **Question Quality**: Validation and fallback strategies
- **System Reliability**: Graceful degradation and error handling
- **Performance**: Caching and efficient retrieval
- **User Experience**: Simple session management without authentication

---

## 💡 Implementation Tips for Coding Agent

### Start With:
1. **Basic FastAPI setup** with health check endpoints
2. **SQLite schema** for documents, chunks, questions, sessions
3. **Document parsing** pipeline for PDF/DOCX
4. **Simple chunking** before moving to advanced techniques

### Key Integration Points:
- **LangChain 0.3.x** for LLM integration and tool calling
- **Weaviate** for vector storage and hybrid search
- **Redis** with try-catch blocks for graceful degradation
- **Structured outputs** from Gemini for consistent question formats

### Testing Strategy:
- Test each component independently
- Use sample educational documents for testing
- Validate question generation with different content types
- Test error scenarios (Redis down, LLM failures, etc.)

---

## 📁 Project Structure Suggestion:
```
quiz-generator/
├── app/
│   ├── api/           # FastAPI routes
│   ├── core/          # Configuration, database
│   ├── models/        # SQLite models
│   ├── services/      # Business logic
│   ├── utils/         # Helper functions
│   └── main.py        # FastAPI app
├── tests/             # Test files
├── docker-compose.yml # Redis setup
├── requirements.txt   # Dependencies
└── README.md          # Documentation
```

This context provides the coding agent with a complete understanding of the project scope, technical decisions, and implementation approach.