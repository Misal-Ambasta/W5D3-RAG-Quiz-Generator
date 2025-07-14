"""
LangChain RAG API Routes
FastAPI routes that use the LangChain v0.3 RAG service for phases 1-7
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Query
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the backend directory to the path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.dependencies import get_database_manager, get_settings
from app.core.database import DatabaseManager
from app.core.config import Settings
from services.langchain_rag_service import LangChainRAGService

router = APIRouter(prefix="/langchain", tags=["langchain-rag"])

# Global service instance (will be initialized per request)
_rag_service: Optional[LangChainRAGService] = None

def get_rag_service(
    db_manager: DatabaseManager = Depends(get_database_manager),
    settings: Settings = Depends(get_settings)
) -> LangChainRAGService:
    """Dependency to get RAG service instance"""
    global _rag_service
    
    if _rag_service is None:
        # Get Weaviate configuration from settings (handles both cloud and local)
        weaviate_config = settings.get_weaviate_config()
        
        # If no configuration is available, disable Weaviate
        if not weaviate_config.get("cluster_url") and not weaviate_config.get("url"):
            weaviate_config = None
        
        _rag_service = LangChainRAGService(
            db_manager=db_manager,
            google_api_key=settings.google_api_key,
            weaviate_config=weaviate_config,
            redis_config=settings.get_redis_config(),
            # embedding_model=settings.embedding_model,
            # reranker_model=settings.cross_encoder_model
        )
    
    return _rag_service

# Request/Response models
class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    content_length: int
    chunks_created: int
    learning_objectives: List[str]
    vector_indexed: Dict[str, Any]
    status: str

class SearchRequest(BaseModel):
    query: str
    k: int = 10
    search_type: str = "hybrid"  # "bm25", "vector", "hybrid", "rerank"
    weights: List[float] = [0.5, 0.5]  # For hybrid search

class SearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    search_type: str
    total_results: int
    retriever_status: Dict[str, bool]

class ServiceStatusResponse(BaseModel):
    document_count: int
    retriever_status: Dict[str, bool]
    service_ready: bool

class QuizGenerationRequest(BaseModel):
    topic: str
    question_count: int = 5
    difficulty: str = "medium"

class QuizResponse(BaseModel):
    quiz_data: Dict[str, Any]
    cached: bool

# Phase 1: Document Upload and Processing
@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_langchain(
    file: UploadFile = File(...),
    rag_service: LangChainRAGService = Depends(get_rag_service),
    settings: Settings = Depends(get_settings)
):
    """
    Upload and process document using LangChain RAG service
    Integrates phases 1-7: parsing, chunking, objectives, indexing, retrieval setup
    """
    try:
        # Validate file 
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        print("Received file:", file.filename)
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        supported_extensions = {'.pdf', '.docx', '.html', '.txt'}
        if file_ext not in supported_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: {', '.join(supported_extensions)}"
            )
        
        # Save uploaded file temporarily
        upload_dir = Path(settings.upload_directory)
        upload_dir.mkdir(exist_ok=True)
        
        temp_file_path = upload_dir / file.filename
        
        # Read and save file content
        content = await file.read()
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        print("temp_file_path:", temp_file_path)
        # Process document using LangChain service
        result = rag_service.process_document(temp_file_path, file.filename)
        print("Processing result:", result)
        # Clean up temporary file
        try:
            temp_file_path.unlink()
        except:
            pass  # Ignore cleanup errors
        
        return DocumentUploadResponse(**result)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

# Phase 5: BM25 Sparse Retrieval
@router.post("/search/bm25", response_model=SearchResponse)
async def search_bm25(
    search_request: SearchRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Search using BM25 sparse retrieval
    """
    try:
        results = rag_service.search_bm25(
            query=search_request.query,
            k=search_request.k
        )
        
        # Convert LangChain documents to response format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0.0)
            })
        
        return SearchResponse(
            query=search_request.query,
            results=formatted_results,
            search_type="bm25",
            total_results=len(formatted_results),
            retriever_status=rag_service.get_retriever_status()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BM25 search failed: {str(e)}")

# Phase 6: Hybrid Retrieval
@router.post("/search/hybrid", response_model=SearchResponse)
async def search_hybrid(
    search_request: SearchRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Search using hybrid retrieval (dense + sparse)
    """
    try:
        results = rag_service.search_hybrid(
            query=search_request.query,
            k=search_request.k,
            weights=search_request.weights
        )
        
        # Convert LangChain documents to response format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0.0)
            })
        
        return SearchResponse(
            query=search_request.query,
            results=formatted_results,
            search_type="hybrid",
            total_results=len(formatted_results),
            retriever_status=rag_service.get_retriever_status()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")

# Phase 7: Cross-Encoder Reranking
@router.post("/search/rerank", response_model=SearchResponse)
async def search_with_reranking(
    search_request: SearchRequest,
    rerank_top_k: int = Query(20, description="Number of results to rerank"),
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Search with cross-encoder reranking
    """
    try:
        results = rag_service.search_with_reranking(
            query=search_request.query,
            k=search_request.k,
            rerank_top_k=rerank_top_k
        )
        
        # Convert LangChain documents to response format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0.0),
                "rerank_score": doc.metadata.get("rerank_score", 0.0)
            })
        
        return SearchResponse(
            query=search_request.query,
            results=formatted_results,
            search_type="rerank",
            total_results=len(formatted_results),
            retriever_status=rag_service.get_retriever_status()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reranking search failed: {str(e)}")

# General search endpoint that supports all search types
@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    General search endpoint supporting all search types
    """
    try:
        if search_request.search_type == "bm25":
            results = rag_service.search_bm25(search_request.query, search_request.k)
        elif search_request.search_type == "hybrid":
            results = rag_service.search_hybrid(search_request.query, search_request.k, search_request.weights)
        elif search_request.search_type == "rerank":
            results = rag_service.search_with_reranking(search_request.query, search_request.k)
        else:
            raise HTTPException(status_code=400, detail="Invalid search type. Use: bm25, hybrid, or rerank")
        
        # Convert LangChain documents to response format
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": doc.metadata.get("score", 0.0),
                "rerank_score": doc.metadata.get("rerank_score", 0.0) if search_request.search_type == "rerank" else None
            })
        
        return SearchResponse(
            query=search_request.query,
            results=formatted_results,
            search_type=search_request.search_type,
            total_results=len(formatted_results),
            retriever_status=rag_service.get_retriever_status()
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Service status and health check
@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Get RAG service status and retriever readiness
    """
    try:
        retriever_status = rag_service.get_retriever_status()
        document_count = rag_service.get_document_count()
        
        # Service is ready if at least one retriever is available
        service_ready = any(retriever_status.values())
        
        return ServiceStatusResponse(
            document_count=document_count,
            retriever_status=retriever_status,
            service_ready=service_ready
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# Redis health check endpoint
@router.get("/redis/health")
async def redis_health_check(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Redis health check endpoint
    """
    try:
        if not rag_service.redis_service:
            return {
                "status": "disabled",
                "message": "Redis service not initialized"
            }
        
        health_status = rag_service.redis_service.health_check()
        return health_status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redis health check failed: {str(e)}")

# Cache management endpoints
@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: Optional[str] = None,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Invalidate cache entries
    """
    try:
        if not rag_service.redis_service:
            return {"message": "Redis service not available"}
        
        deleted_count = rag_service.redis_service.invalidate_cache(pattern)
        return {
            "message": f"Invalidated {deleted_count} cache entries",
            "pattern": pattern or "all",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache invalidation failed: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Get cache statistics
    """
    try:
        if not rag_service.redis_service:
            return {"message": "Redis service not available"}
        
        stats = rag_service.redis_service.get_cache_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

# Quiz generation endpoint (demonstrates quiz caching)
@router.post("/generate-quiz", response_model=QuizResponse)
async def generate_quiz(
    quiz_request: QuizGenerationRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Generate a quiz (demonstrates quiz caching functionality)
    """
    try:
        quiz_data = rag_service.generate_quiz(
            topic=quiz_request.topic,
            question_count=quiz_request.question_count,
            difficulty=quiz_request.difficulty
        )
        
        return QuizResponse(
            quiz_data=quiz_data,
            cached=quiz_data.get("cached", False)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

# Reset service (useful for testing)
@router.post("/reset")
async def reset_service(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """
    Reset RAG service retrievers (useful for testing)
    """
    try:
        rag_service.reset_retrievers()
        return {"message": "Service reset successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Service reset failed: {str(e)}")

# Learning objectives endpoint
@router.get("/documents/{document_id}/objectives")
async def get_learning_objectives(
    document_id: int,
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """
    Get learning objectives for a specific document
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT objective_text, confidence_score
            FROM learning_objectives
            WHERE document_id = ?
            ORDER BY confidence_score DESC
        """, (document_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        objectives = [
            {"text": row[0], "confidence": row[1]}
            for row in results
        ]
        
        return {
            "document_id": document_id,
            "objectives": objectives,
            "total_count": len(objectives)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get objectives: {str(e)}")


# Phase 9 - Tool Calling Integration Routes
@router.get("/tools")
async def get_phase9_tools(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Get available Phase 9 tools"""
    try:
        tools = rag_service.get_phase9_tools()
        tool_info = []
        for tool in tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description
            })
        return {"tools": tool_info, "count": len(tool_info)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")


@router.post("/execute_tool")
async def execute_phase9_tool(
    tool_name: str,
    tool_input: str,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Execute a specific Phase 9 tool"""
    try:
        result = rag_service.execute_tool(tool_name, tool_input)
        return {"result": result, "tool_name": tool_name, "input": tool_input}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute tool: {str(e)}")


@router.get("/quiz/search")
async def search_quiz_dataset(
    query: str,
    search_type: str = "keyword",
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Search quiz dataset using Phase 9 tools"""
    try:
        result = rag_service.search_quiz_dataset(query, search_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search quiz dataset: {str(e)}")


@router.get("/educational/content")
async def get_educational_content(
    topic: str,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Get educational content using Phase 9 APIs"""
    try:
        result = rag_service.get_educational_content(topic)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get educational content: {str(e)}")


@router.get("/quiz/categories")
async def get_quiz_categories(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Get quiz categories and statistics"""
    try:
        result = rag_service.execute_tool("get_quiz_categories", "")
        return {"categories": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get quiz categories: {str(e)}")


@router.get("/educational/status")
async def get_educational_api_status(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Get educational API status"""
    try:
        result = rag_service.execute_tool("get_educational_api_status", "")
        return {"status": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API status: {str(e)}")


# Phase 10 - Gemini Integration Routes
class GeminiQuizRequest(BaseModel):
    content: str
    num_questions: int = 5
    difficulty: str = "medium"
    question_types: Optional[List[str]] = None


class GeminiObjectivesRequest(BaseModel):
    content: str
    max_objectives: int = 5


class GeminiExplanationRequest(BaseModel):
    question: str
    correct_answer: str
    incorrect_answers: Optional[List[str]] = None
    context: Optional[str] = None


class GeminiStructuredQuizRequest(BaseModel):
    content: str
    quiz_config: Dict[str, Any]


@router.post("/quiz/generate")
async def generate_quiz_with_gemini(
    request: GeminiQuizRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Generate quiz questions using Gemini"""
    try:
        result = rag_service.generate_quiz_with_gemini(
            content=request.content,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_types=request.question_types
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.post("/objectives/extract")
async def extract_learning_objectives_with_gemini(
    request: GeminiObjectivesRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Extract learning objectives using Gemini"""
    try:
        result = rag_service.extract_learning_objectives_with_gemini(
            content=request.content,
            max_objectives=request.max_objectives
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract objectives: {str(e)}")


@router.post("/explanations/generate")
async def generate_answer_explanations_with_gemini(
    request: GeminiExplanationRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Generate answer explanations using Gemini"""
    try:
        result = rag_service.generate_answer_explanations_with_gemini(
            question=request.question,
            correct_answer=request.correct_answer,
            incorrect_answers=request.incorrect_answers,
            context=request.context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate explanations: {str(e)}")


@router.post("/quiz/structured")
async def generate_structured_quiz_with_gemini(
    request: GeminiStructuredQuizRequest,
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Generate structured quiz using Gemini"""
    try:
        result = rag_service.generate_structured_quiz_with_gemini(
            content=request.content,
            quiz_config=request.quiz_config
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate structured quiz: {str(e)}")


@router.get("/gemini/test")
async def test_gemini_connection(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Test Gemini API connection"""
    try:
        result = rag_service.test_gemini_connection()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test Gemini connection: {str(e)}")


@router.get("/gemini/models")
async def get_gemini_model_info(
    rag_service: LangChainRAGService = Depends(get_rag_service)
):
    """Get Gemini model information"""
    try:
        result = rag_service.get_gemini_model_info()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}") 