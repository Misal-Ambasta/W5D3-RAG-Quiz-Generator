# Automated Quiz Generator

## Overview

The Automated Quiz Generator is an educational tool that automatically creates quizzes based on uploaded educational materials. It uses advanced Retrieval-Augmented Generation (RAG) techniques with LangChain tool calling and Google Gemini LLM integration to generate high-quality, contextually relevant quiz questions from educational documents.

## Key Features

- **Document Upload**: Support for PDF, DOCX, TXT, and HTML files
- **Hybrid RAG System**: Combines dense and sparse retrieval for better context understanding
- **Advanced Reranking**: Uses cross-encoder models to improve retrieval relevance
- **Contextual Compression**: Preserves semantic context during document chunking
- **Intelligent Caching**: Redis-based caching for improved performance
- **Educational API Integration**: Khan Academy API integration for enhanced content
- **LangChain Tool Calling**: 9 specialized tools for quiz dataset querying and educational content retrieval
- **JSON Dataset Support**: Query structured quiz datasets by topic, difficulty, keywords, and categories
- **Google Gemini Integration**: Advanced LLM capabilities for quiz generation, learning objectives, and explanations
- **Structured Output Generation**: Gemini-powered structured quiz formats with function calling
- **Multiple Question Types**: Supports multiple-choice, true/false, short answer, and fill-in-the-blank questions
- **Session Management**: Anonymous session system for quiz taking and result tracking
- **Feedback Collection**: Gathers user feedback on quiz and question quality

## Architecture

The application follows a client-server architecture:

- **Frontend**: React-based single-page application with TypeScript
- **Backend**: FastAPI-based RESTful API server
- **Database**: SQLite for data persistence
- **Cache**: Redis for performance optimization
- **LLM Integration**: Google Gemini Pro for question generation and answer validation
- **Tool System**: LangChain tools for educational APIs and dataset querying
- **Educational APIs**: Khan Academy integration for supplementary content

## New Features (Phase 9 & 10)

### Phase 9 - Tool Calling Integration
- **QuizDatasetService**: Advanced JSON dataset querying with filtering, statistics, and search capabilities
- **EducationalAPIService**: Khan Academy API integration with caching and fallback mechanisms
- **LangChain Tools**: 9 specialized tools including:
  - `search_quiz_by_topic`: Find quizzes by educational topic
  - `search_quiz_by_difficulty`: Filter by difficulty level
  - `search_quiz_by_keyword`: Semantic keyword search
  - `get_random_quiz_questions`: Random question selection
  - `filter_quiz_questions`: Multi-criteria filtering
  - `get_quiz_categories`: Available categories listing
  - `search_educational_content`: Khan Academy content search
  - `get_khan_academy_topics`: Topic hierarchy retrieval
  - `get_educational_api_status`: API health monitoring

### Phase 10 - Google Gemini Integration
- **GeminiService**: Complete Google Gemini Pro integration with:
  - Quiz question generation with customizable parameters
  - Learning objective extraction from documents
  - Answer explanation generation
  - Structured output formatting
  - Function calling capabilities
  - Safety settings and content filtering

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Redis server
- Google API key for Gemini access

### Installation

#### Backend Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/automated-quiz-generator.git
   cd automated-quiz-generator
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Set up environment variables
   ```bash
   # Create a .env file with the following variables
   GOOGLE_API_KEY=your_google_api_key
   REDIS_URL=redis://localhost:6379
   KHAN_ACADEMY_API_KEY=your_khan_academy_api_key  # Optional
   
   # For Weaviate Cloud (Optional - if not using local Weaviate)
   WEAVIATE_CLUSTER_URL=https://your-cluster-name.weaviate.network
   WEAVIATE_AUTH_CREDENTIALS=your-weaviate-cloud-api-key
   ```

5. Start required services (Redis + Weaviate)
   
   **🌩️ Weaviate Cloud Option (Recommended)**
   
   For easier setup, you can use Weaviate Cloud instead of local Weaviate:
   1. Sign up at [Weaviate Cloud](https://console.weaviate.cloud/)
   2. Create a cluster and get your credentials
   3. Set the `WEAVIATE_CLUSTER_URL` and `WEAVIATE_AUTH_CREDENTIALS` environment variables
   4. Run the test script: `python backend/test_weaviate_cloud.py`
   5. Only start Redis locally: `docker run -d -p 6379:6379 redis:alpine`
   
   See `backend/WEAVIATE_CLOUD_SETUP.md` for detailed instructions.
   
   **🏠 Local Setup Option**
   
   **Option 1: Automated Setup (Recommended)**
   ```bash
   # For Windows
   start_services.bat
   
   # For Linux/Mac
   chmod +x start_services.sh
   ./start_services.sh
   ```
   
   **Option 2: Manual Setup**
   ```bash
   # Start all services
   docker-compose up -d
   
   # Check status
   docker-compose ps
   ```
   
   **Option 3: Individual Services**
   ```bash
   # Redis only (basic caching)
   docker run -d -p 6379:6379 redis:alpine
   
   # Weaviate only (vector search)
   docker run -d -p 8080:8080 -p 50051:50051 semitechnologies/weaviate:1.25.0
   ```
   
   > 📋 **Note**: The system works with graceful degradation - it will function even if some services are unavailable. See `backend/DOCKER_SETUP.md` for detailed setup instructions.

6. Initialize the database
   ```bash
   python services/init_db.py
   ```

7. Run the backend server
   ```bash
   uvicorn app.main:app --reload
   cd backend && source venv/Scripts/activate && uvicorn app.main:app --reload
   ```
#### Frontend Setup

1. Install dependencies
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server
   ```bash
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:5173`

## API Endpoints

### Core Endpoints
- `POST /langchain/upload` - Upload educational documents
- `POST /langchain/generate-quiz` - Generate quiz questions
- `POST /sessions` - Create quiz session
- `GET /sessions/{session_id}` - Get session details
- `POST /sessions/{session_id}/answers` - Submit quiz answers
- `GET /sessions/{session_id}/results` - Get quiz results

### Phase 9 Endpoints (Tool Calling)
- `POST /langchain/search-quiz-topic` - Search quizzes by topic
- `POST /langchain/search-quiz-difficulty` - Filter by difficulty
- `POST /langchain/search-quiz-keyword` - Keyword-based search
- `GET /langchain/random-quiz-questions` - Get random questions
- `POST /langchain/filter-quiz-questions` - Multi-criteria filtering
- `GET /langchain/educational-content` - Khan Academy content search

### Phase 10 Endpoints (Gemini Integration)
- `POST /langchain/generate-quiz-gemini` - Gemini-powered quiz generation
- `POST /langchain/extract-learning-objectives` - Extract learning objectives
- `POST /langchain/generate-answer-explanations` - Generate explanations
- `POST /langchain/generate-structured-quiz` - Structured quiz output
- `GET /langchain/test-gemini-connection` - Test Gemini connectivity
- `GET /langchain/gemini-model-info` - Get model information

For complete API documentation, access the interactive Swagger UI at `http://localhost:8000/docs` when the backend server is running.

## Development

## Usage

1. **Upload Document**: Start by uploading an educational document (PDF, DOCX, TXT, or HTML)
2. **Generate Quiz**: Enter a topic or learning objective to generate relevant questions
3. **Take Quiz**: Answer the generated questions in the interactive interface
4. **View Results**: Review your performance with detailed explanations and correct answers
5. **Feedback**: Provide feedback to improve the system

## Development

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production
```bash
# Frontend build
cd frontend
npm run build

# Backend deployment
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Database models
│   │   └── utils/         # Utility functions
│   ├── services/          # Business logic services
│   │   ├── quiz_dataset_service.py      # JSON dataset querying
│   │   ├── educational_api_service.py   # Khan Academy integration
│   │   ├── langchain_tools.py           # LangChain tool definitions
│   │   ├── gemini_service.py            # Google Gemini integration
│   │   ├── langchain_rag_service.py     # Enhanced RAG with tools
│   │   ├── document_ingestion.py        # Document processing
│   │   ├── vector_indexing.py           # Vector database operations
│   │   └── learning_objectives.py       # Learning objective extraction
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── public/            # Static assets
│   └── src/               # Source code
│       ├── api/           # API client
│       ├── components/    # React components
│       ├── store/         # State management
│       └── types/         # TypeScript type definitions
├── database.db           # SQLite database
├── quiz_questions.json   # Educational quiz dataset
└── docs/                 # Documentation
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) for RAG implementation
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [React](https://reactjs.org/) for the frontend framework
- [Google Gemini](https://ai.google.dev/) for LLM capabilities