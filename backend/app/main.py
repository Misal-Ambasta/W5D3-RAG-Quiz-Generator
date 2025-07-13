"""
FastAPI Main Application - Quiz Generator MVP
Entry point for the Automated Quiz Generator with RAG system
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any
import os
from pathlib import Path
import sys

# Add the backend directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import Settings
from app.core.database import DatabaseManager
from app.core.dependencies import get_database_manager, get_settings
from app.api.langchain_routes import router as langchain_router
from app.api.session_routes import router as session_router
from app.api.feedback_routes import router as feedback_router

# Global variables for app state
db_manager = None
settings = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events - startup and shutdown
    """
    global db_manager, settings
    
    # Startup
    print("🚀 Starting Quiz Generator application...")
    
    # Load settings
    settings = Settings()
    
    # Initialize database
    db_manager = DatabaseManager(settings.database_url)
    db_manager.create_indexes()
    
    # Cleanup expired sessions
    expired_count = db_manager.cleanup_expired_sessions()
    if expired_count > 0:
        print(f"🧹 Cleaned up {expired_count} expired sessions")
    
    print("✅ Application startup complete!")
    yield
    
    # Shutdown
    print("📴 Shutting down Quiz Generator application...")
    print("✅ Application shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title="Automated Quiz Generator MVP",
    description="Advanced RAG-based quiz generation system with hybrid search and AI-powered question creation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(langchain_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Quiz Generator API is running",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to the Automated Quiz Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Database status endpoint
@app.get("/status")
async def get_status(
    db_manager: DatabaseManager = Depends(get_database_manager)
):
    """Get application and database status"""
    try:
        stats = db_manager.get_database_stats()
        return {
            "status": "operational",
            "database": "connected",
            "statistics": stats
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "database": "disconnected",
                "error": str(e)
            }
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
