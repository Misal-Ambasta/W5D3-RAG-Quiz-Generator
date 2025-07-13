"""
FastAPI Dependencies
Dependency injection for database, settings, and other services
"""

from functools import lru_cache
from .config import Settings
from .database import DatabaseManager

# Global instances
_db_manager = None
_settings = None

@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_database_manager() -> DatabaseManager:
    """Get database manager instance"""
    global _db_manager
    if _db_manager is None:
        settings = get_settings()
        _db_manager = DatabaseManager(settings.database_url)
    return _db_manager

def get_cache_service():
    """Get cache service (Redis) - placeholder for now"""
    # TODO: Implement Redis cache service
    return None

def get_vector_store():
    """Get vector store (Weaviate) - placeholder for now"""
    # TODO: Implement Weaviate vector store
    return None

def get_llm_service():
    """Get LLM service (Gemini) - placeholder for now"""
    # TODO: Implement Gemini LLM service
    return None
