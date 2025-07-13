"""
Core Configuration Settings
Handles environment variables and application settings
"""

import os
from typing import Optional, List, Dict, Any, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "Quiz Generator MVP"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database settings
    database_url: str = Field(default="quiz_generator.db", env="DATABASE_URL")
    
    # API Keys
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    redis_health_check_interval: int = Field(default=30, env="REDIS_HEALTH_CHECK_INTERVAL")
    
    # Cache TTL settings (in seconds)
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    cache_chunk_ttl: int = Field(default=3600, env="CACHE_CHUNK_TTL")  # 1 hour
    cache_quiz_ttl: int = Field(default=1800, env="CACHE_QUIZ_TTL")  # 30 minutes
    cache_objectives_ttl: int = Field(default=7200, env="CACHE_OBJECTIVES_TTL")  # 2 hours
    cache_search_ttl: int = Field(default=900, env="CACHE_SEARCH_TTL")  # 15 minutes
    
    # Weaviate settings
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # Weaviate Cloud settings
    weaviate_cluster_url: Optional[str] = Field(default=None, env="WEAVIATE_CLUSTER_URL")
    weaviate_auth_credentials: Optional[str] = Field(default=None, env="WEAVIATE_AUTH_CREDENTIALS")
    
    # File upload settings
    upload_directory: str = Field(default="uploads", env="UPLOAD_DIRECTORY")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: Union[List[str], str] = Field(
        default=[".pdf", ".docx", ".txt", ".html"], 
        env="ALLOWED_EXTENSIONS"
    )
    
    # Embeddings settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")
    
    # Quiz generation settings
    default_question_count: int = Field(default=10, env="DEFAULT_QUESTION_COUNT")
    max_question_count: int = Field(default=50, env="MAX_QUESTION_COUNT")
    
    # Cross-encoder settings
    cross_encoder_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", 
        env="CROSS_ENCODER_MODEL"
    )
    
    # Session settings
    session_timeout_hours: int = Field(default=24, env="SESSION_TIMEOUT_HOURS")
    
    # Hybrid search settings
    hybrid_search_alpha: float = Field(default=0.5, env="HYBRID_SEARCH_ALPHA")
    retrieval_k: int = Field(default=10, env="RETRIEVAL_K")
    rerank_k: int = Field(default=5, env="RERANK_K")
    
    # LLM settings
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1000, env="LLM_MAX_TOKENS")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # CORS settings
    allowed_origins: Union[List[str], str] = Field(
        default=["*"], 
        env="ALLOWED_ORIGINS"
    )
    
    @field_validator('allowed_extensions')
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            # Parse comma-separated string to list
            return [ext.strip() for ext in v.split(',') if ext.strip()]
        return v
    
    @field_validator('allowed_origins')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Parse comma-separated string to list
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create upload directory if it doesn't exist
        Path(self.upload_directory).mkdir(parents=True, exist_ok=True)
        
        # Validate required settings
        if not self.google_api_key:
            print("⚠️  Warning: GOOGLE_API_KEY not set. LLM features will be disabled.")
    
    @property
    def database_path(self) -> Path:
        """Get database file path"""
        return Path(self.database_url)
    
    @property
    def upload_path(self) -> Path:
        """Get upload directory path"""
        return Path(self.upload_directory)
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        config = {
            "host": self.redis_host,
            "port": self.redis_port,
            "db": self.redis_db,
            "socket_timeout": self.redis_socket_timeout,
            "health_check_interval": self.redis_health_check_interval,
            "chunk_ttl": self.cache_chunk_ttl,
            "quiz_ttl": self.cache_quiz_ttl,
            "objectives_ttl": self.cache_objectives_ttl,
            "search_results_ttl": self.cache_search_ttl,
            "default_ttl": self.cache_ttl
        }
        
        if self.redis_password:
            config["password"] = self.redis_password
            
        return config
    
    def get_weaviate_config(self) -> Dict[str, Any]:
        """Get Weaviate configuration - prioritizes cloud over local"""
        # Check for Weaviate Cloud configuration first
        if self.weaviate_cluster_url and self.weaviate_auth_credentials:
            # Use Weaviate Cloud
            config = {
                "cluster_url": self.weaviate_cluster_url,
                "auth_credentials": self.weaviate_auth_credentials,
                "timeout_config": (5, 15),  # (connect_timeout, read_timeout)
            }
        else:
            # Use local Weaviate (fallback)
            config = {
                "url": self.weaviate_url,
                "timeout_config": (5, 15),  # (connect_timeout, read_timeout)
            }
            
            if self.weaviate_api_key:
                config["auth_client_secret"] = self.weaviate_api_key
            
        return config
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.debug
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            "allow_origins": self.allowed_origins,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

# Global settings instance
settings = Settings()
